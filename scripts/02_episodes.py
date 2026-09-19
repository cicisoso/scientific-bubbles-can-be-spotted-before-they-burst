"""Boom-bust episode detection on topic shares. For each topic, share s_t = n_t / N_t (articles+reviews) 1980-2025. A boom peak is a year t such that
s_t is the maximum of s over [t-5, t+5] (or to the end of the series), the run-up R = s_t / min(s[t-5..t-1]) >= RUN and n_t >= NMIN.
Post-peak outcome: drawdown D = 1 - min(s[t+1..t+5]) / s_t (needs t <= 2020 for a full window); crash if D >= CRASH. Ongoing booms (peak in the last
window) are censored. Output results/episodes.parquet with one row per boom peak and the ex-ante/ex-post statistics computed later."""
import os, sys, json, numpy as np, pandas as pd
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B=os.path.join(ROOT,'data','build'); R=os.path.join(ROOT,'results'); os.makedirs(R,exist_ok=True)
RUN=float(os.environ.get('RUN','2.0')); CRASH=float(os.environ.get('CRASH','0.4')); NMIN=int(os.environ.get('NMIN','300')); W=int(os.environ.get('W','5')); COL=os.environ.get('COL','n_core'); Y1=int(os.environ.get('Y1','2025'))
ty=pd.read_parquet(os.path.join(B,'topic_year.parquet'))
src=pd.read_parquet(os.path.join(B,'topic_year_sources.parquet')); au=pd.read_parquet(os.path.join(B,'topic_year_authors.parquet'))
ty=ty.merge(src,on=['topic','year'],how='left').merge(au,on=['topic','year'],how='left'); ty=ty[ty.year<=Y1]
for c in ('n_core','n_sources','n_authors'): ty[c]=ty[c].fillna(0)
NSRC=int(os.environ.get('NSRC','20')); TOPSRC=float(os.environ.get('TOPSRC','0.25'))
wide_src=ty.pivot(index='topic',columns='year',values='n_sources').reindex(columns=range(1980,Y1+1)).fillna(0); wide_top=ty.pivot(index='topic',columns='year',values='top_source_share').reindex(columns=range(1980,Y1+1)).fillna(1)
wide_au=ty.pivot(index='topic',columns='year',values='n_authors').reindex(columns=range(1980,Y1+1)).fillna(0)
tot=ty.groupby('year')[COL].sum(); wide=ty.pivot(index='topic',columns='year',values=COL).reindex(columns=range(1980,Y1+1)).fillna(0)
share=wide.div(tot,axis=1)
names={int(t['id'].split('/')[-1].lstrip('T')):t['display_name'] for t in json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'data','names','topics.json')))}
meta=ty.groupby('topic')[['subfield','field','domain']].first()
rows=[]
years=np.array(share.columns)
for topic,s in share.iterrows():
    v=s.values; n=wide.loc[topic].values
    for i in range(W,len(v)):
        t=years[i]
        lo=max(0,i-W); hi=min(len(v),i+W+1)
        if v[i]<=0 or v[i]<v[lo:hi].max(): continue        # local max over +-W (ties resolved by the first)
        if i>lo and v[i]==v[lo:i].max() and (v[lo:i]==v[i]).any(): continue
        pre=v[lo:i]; run=v[i]/pre.min() if pre.min()>0 else np.inf
        if run<RUN or n[i]<NMIN: continue
        nsrc=wide_src.loc[topic].values[i]; topsh=wide_top.loc[topic].values[i]; nau=wide_au.loc[topic].values
        if nsrc<NSRC or topsh>TOPSRC: continue
        full=(i+W)<len(v)
        post=v[i+1:i+W+1]; dd=1-post.min()/v[i] if len(post) else np.nan
        post_n=n[i+1:i+W+1]; dd_n=1-post_n.min()/n[i] if len(post_n) else np.nan
        years_to_min=int(years[i+1+int(np.argmin(post))]-t) if len(post) else None
        post_au=nau[i+1:i+W+1]; dd_au=(1-post_au.min()/nau[i]) if (len(post_au) and nau[i]>0) else np.nan
        rows.append(dict(topic=topic,name=names.get(topic,''),subfield=meta.loc[topic,'subfield'],field=meta.loc[topic,'field'],domain=meta.loc[topic,'domain'],peak_year=int(t),n_peak=int(n[i]),share_peak=float(v[i]),
                         runup=float(run),trough_year=int(years[lo+int(np.argmin(pre))]),drawdown=float(dd) if full else np.nan,drawdown_n=float(dd_n) if full else np.nan,drawdown_authors=float(dd_au) if full else np.nan,n_sources=int(nsrc),top_source_share=float(topsh),evaluable=bool(full),years_to_min=years_to_min,
                         crash=(bool(dd>=CRASH) if full else None),share_last=float(v[-1]),n_last=int(n[-1]),
                         growth_accel=float(np.mean(np.diff(np.log(np.maximum(v[i-3:i+1],1e-12)),2))) if i>=3 else np.nan))
ep=pd.DataFrame(rows)
# separate episodes of the same topic by >= 2W years (keep the larger peak)
ep=ep.sort_values(['topic','share_peak'],ascending=[True,False]); keep=[]
for topic,g in ep.groupby('topic'):
    taken=[]
    for _,r in g.iterrows():
        if all(abs(r.peak_year-y)>=2*W for y in taken): keep.append(r); taken.append(r.peak_year)
ep=pd.DataFrame(keep).sort_values(['peak_year','topic']).reset_index(drop=True)
ep.to_parquet(os.path.join(R,f'episodes_{COL}_R{RUN}_C{CRASH}_N{NMIN}_W{W}.parquet'),index=False)
if COL=='n_core' and RUN==2.0 and CRASH==0.4 and NMIN==300 and W==5: ep.to_parquet(os.path.join(R,'episodes.parquet'),index=False)
ev=ep[ep.evaluable]
print(f'topics with booms: {ep.topic.nunique()}, boom episodes: {len(ep)}, evaluable (peak<= {Y1-W}): {len(ev)}, crashes: {int(ev.crash.sum())} ({100*ev.crash.mean():.1f}%), ongoing/censored: {(~ep.evaluable).sum()}')
print(ev.groupby(ev.peak_year//10*10).crash.agg(['size','mean']).round(3))
print(ev.groupby('domain').crash.agg(['size','mean']).round(3))
print('median drawdown', ev.drawdown.median().round(3), 'share crash>=0.5', (ev.drawdown>=0.5).mean().round(3), 'share drawdown<0.2', (ev.drawdown<0.2).mean().round(3))
pd.set_option('display.width',250)
print(ev.sort_values('n_peak',ascending=False).head(25)[['name','peak_year','n_peak','runup','drawdown','crash','years_to_min']].to_string())
print(ep[~ep.evaluable].sort_values('n_peak',ascending=False).head(12)[['name','peak_year','n_peak','runup']].to_string())
