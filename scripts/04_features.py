"""Per-episode features: pre-peak signatures (t-3..t-1 averages and t-5 -> t-1 changes), post-peak outcomes, awards, retractions; event-time panels
(peak-relative years -5..+5) for the anatomy figure. Inputs: results/episodes_cs.parquet + data/build/topic_year_*.parquet + awards. Output results/features.parquet,
results/eventtime.parquet."""
import os, json, numpy as np, pandas as pd, duckdb
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B=os.path.join(ROOT,'data','build'); R=os.path.join(ROOT,'results'); P=os.path.expanduser('~/research/sos/planck/data/build')
ep=pd.read_parquet(os.path.join(R,'episodes_cs.parquet'))
ty=pd.read_parquet(os.path.join(B,'topic_year.parquet'))
for f in ('topic_year_sources','topic_year_authors','topic_year_newcomers','topic_year_refs','topic_year_cites','topic_year_countries','topic_year_rw'):
    p=os.path.join(B,f+'.parquet')
    if os.path.exists(p):
        d=pd.read_parquet(p); d=d.loc[:,~d.columns.duplicated()]
        ty=ty.merge(d,on=['topic','year'],how='left',suffixes=('','_dup'))
ty=ty.loc[:,~ty.columns.str.endswith('_dup')]
# awards by topic and start year
con=duckdb.connect()
aw=con.execute(f"""SELECT topic, start_year AS year, count(*) AS n_awards, sum(CASE WHEN currency='USD' THEN amount END) AS usd_amount, sum(funded_outputs_count) AS n_funded_outputs
                   FROM read_parquet('{ROOT}/data/awards/*.parquet') WHERE topic IS NOT NULL AND start_year BETWEEN 1980 AND 2025 GROUP BY 1,2""").df()
ty=ty.merge(aw,on=['topic','year'],how='left'); ty['n_awards']=ty.n_awards.fillna(0)
# derived rates
ty['newcomer_share']=ty.n_newcomers/ty.n_authors_x if 'n_authors_x' in ty else ty.n_newcomers/ty.n_authors
if 'n_authors_x' in ty: ty['n_authors']=ty.n_authors_x
ty['new_scientist_share']=ty.n_new_scientists/ty.n_authors; ty['review_share']=ty.n_review/ty.n; ty['attention']=ty.cites_received; ty['within_cites_share']=ty.cites_from_within/ty.cites_received
ty['awards_per_100']=100*ty.n_awards/ty.n_core.replace(0,np.nan)
tot=ty.groupby('year').n_core.sum(); ty['share_core']=ty.n_core/ty.year.map(tot)
fy=ty.groupby(['field','year']).agg(fn=('n','sum'),fr=('n_retracted','sum')).reset_index(); ty=ty.merge(fy,on=['field','year'],how='left')
ty['exp_retracted']=ty.n*((ty.fr-ty.n_retracted.fillna(0))/(ty.fn-ty.n).replace(0,np.nan))   # expected retractions at the field-year rate (excluding the topic)
ty['n_retracted_rw']=ty.n_retracted_rw.fillna(0); fy2=ty.groupby(['field','year']).agg(frw=('n_retracted_rw','sum')).reset_index(); ty=ty.merge(fy2,on=['field','year'],how='left')
ty['exp_retracted_rw']=ty.n*((ty.frw-ty.n_retracted_rw)/(ty.fn-ty.n).replace(0,np.nan))
ty=ty.sort_values(['topic','year'])
FEATS=['newcomer_share','new_scientist_share','low_fwci_share','high_fwci_share','fwci_mean','uncited_share','within_topic_share','within_subfield_share','within_cites_share','top_country_share','china_share','us_share','n_countries','top_source_share','n_sources','review_share','team_mean','refs_mean','ref_age','awards_per_100','n_awards','attention','retracted_share','en_share','share_core','n_core','n_authors']
tyi=ty.set_index(['topic','year'])
rows=[]; et=[]
for _,e in ep.iterrows():
    t=int(e.peak_year); tp=int(e.topic)
    def val(y,c):
        try: return tyi.loc[(tp,y),c]
        except KeyError: return np.nan
    rec=dict(e)
    for c in FEATS:
        pre=[val(y,c) for y in range(t-3,t)]; rec[f'{c}_pre']=np.nanmean(pre) if not all(pd.isna(pre)) else np.nan
        rec[f'{c}_peak']=val(t,c); rec[f'{c}_m5']=val(t-5,c); rec[f'{c}_change']=(rec[f'{c}_pre']-val(t-5,c)) if not pd.isna(val(t-5,c)) else np.nan
        post=[val(y,c) for y in range(t+1,t+6)]; rec[f'{c}_post']=np.nanmean(post) if not all(pd.isna(post)) else np.nan
    # growth measures from the core share
    s=[val(y,'share_core') for y in range(t-5,t+6)]; s=np.array(s,dtype=float)
    lg=np.log(np.where(s>0,s,np.nan)); g=np.diff(lg)
    rec['g_pre_mean']=np.nanmean(g[:5]); rec['g_last']=g[4] if len(g)>4 else np.nan; rec['accel']=np.nanmean(np.diff(g[:5])) ; rec['convexity']=(lg[5]-2*lg[3]+lg[1]) if len(lg)>5 else np.nan
    rec['net_gain']=(s[10]/s[0]) if (len(s)>10 and s[0]>0 and not np.isnan(s[10])) else np.nan; rec['level_t5']=s[10] if len(s)>10 else np.nan
    # retractions: boom-era papers (t-2..t) vs pre-boom (t-8..t-6)
    def rate(ys):
        n=sum(val(y,'n') for y in ys if not pd.isna(val(y,'n'))); r=sum(val(y,'n_retracted') for y in ys if not pd.isna(val(y,'n_retracted'))); return (r/n if n else np.nan), n
    rec['retract_boom'],rec['n_boom']=rate(range(t-2,t+1)); rec['retract_pre'],rec['n_preboom']=rate(range(t-8,t-5)); rec['retract_post'],rec['n_postboom']=rate(range(t+1,t+4))
    def sir(ys):
        o=sum(val(y,'n_retracted') for y in ys if not pd.isna(val(y,'n_retracted'))); e=sum(val(y,'exp_retracted') for y in ys if not pd.isna(val(y,'exp_retracted'))); return o,e
    rec['ret_obs_boom'],rec['ret_exp_boom']=sir(range(t-2,t+1)); rec['ret_obs_pre'],rec['ret_exp_pre']=sir(range(t-8,t-5)); rec['ret_obs_post'],rec['ret_exp_post']=sir(range(t+1,t+4))
    def sir_rw(ys):
        o=sum(val(y,'n_retracted_rw') for y in ys if not pd.isna(val(y,'n_retracted_rw'))); e=sum(val(y,'exp_retracted_rw') for y in ys if not pd.isna(val(y,'exp_retracted_rw'))); return o,e
    rec['rw_obs_boom'],rec['rw_exp_boom']=sir_rw(range(t-2,t+1)); rec['rw_obs_pre'],rec['rw_exp_pre']=sir_rw(range(t-8,t-5)); rec['rw_obs_post'],rec['rw_exp_post']=sir_rw(range(t+1,t+4))
    # attention after the peak: citations received in t+1..t+5 relative to t
    a=[val(y,'attention') for y in range(t-5,t+6)]; rec['attention_ratio_t5']=(a[10]/a[5]) if (len(a)>10 and a[5] and not pd.isna(a[10])) else np.nan
    rows.append(rec)
    for k in range(-5,6):
        et.append(dict(topic=tp,peak_year=t,k=k,crash=e.crash,evaluable=e.evaluable,runup=e.runup,**{c:val(t+k,c) for c in FEATS}))
F=pd.DataFrame(rows); F.to_parquet(os.path.join(R,'features.parquet'),index=False); E=pd.DataFrame(et); E.to_parquet(os.path.join(R,'eventtime.parquet'),index=False)
ev=F[F.evaluable]
pd.set_option('display.width',250)
for c in ['newcomer_share_pre','new_scientist_share_pre','low_fwci_share_pre','fwci_mean_pre','within_topic_share_pre','top_country_share_pre','china_share_pre','awards_per_100_pre','review_share_pre','accel','convexity','g_pre_mean','top_source_share_pre','newcomer_share_change','low_fwci_share_change']:
    if c in ev: print(f'{c:28s} crash {ev[ev.crash==True][c].median():.4f}  soft {ev[ev.crash==False][c].median():.4f}  n={ev[c].notna().sum()}')
print('retraction: boom-era crash/soft', ev[ev.crash==True].retract_boom.mean(), ev[ev.crash==False].retract_boom.mean(), 'pre-boom', ev.retract_pre.mean())
print('net gain median crash/soft', ev[ev.crash==True].net_gain.median(), ev[ev.crash==False].net_gain.median(), '; attention ratio', ev[ev.crash==True].attention_ratio_t5.median(), ev[ev.crash==False].attention_ratio_t5.median())
