"""Statistics for the bubbles paper -> results/summary.json and results/analysis/*.csv.
crash rates and sensitivity; dose-response vs null; logistic models and out-of-sample prediction; retractions; aftermath; entrants; ongoing booms."""
import os, json, numpy as np, pandas as pd, warnings
from scipy import stats
import statsmodels.api as sm, statsmodels.formula.api as smf
from sklearn.metrics import roc_auc_score
warnings.filterwarnings('ignore')
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R=os.path.join(ROOT,'results'); A=os.path.join(R,'analysis'); os.makedirs(A,exist_ok=True)
F=pd.read_parquet(os.path.join(R,'features.parquet')); S={}
# venue concentration of the run-up (02c) and the fixed-source-weight variant (02d)
import re
V=pd.read_parquet(os.path.join(R,'venues.parquet')); VN=pd.read_csv(os.path.join(R,'venue_names.csv')).set_index('sid').display_name; FW=pd.read_parquet(os.path.join(R,'fixed_weight.parquet'))
PROC=re.compile(r'proceedings|conference|trans tech|wit transactions|acta horticulturae|materials science forum|key engineering materials|symposium|advanced materials research|applied mechanics and materials|lecture notes',re.I)
V['top1_name']=V.top_sids.apply(lambda l: VN.get(int(l[0]),'') if len(l) else ''); V['proc_led']=V.top1_name.apply(lambda x: bool(PROC.search(x)))
F=F.merge(V[['topic','peak_year','top1_share_inc','top3_share_inc','top10_share_inc','top1_name','proc_led']],on=['topic','peak_year'],how='left').merge(FW,on=['topic','peak_year'],how='left')
def wilson(k,n,z=1.96):
    if n==0: return (np.nan,np.nan)
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return (c-h,c+h)
ev=F[F.evaluable].copy(); ev['crash']=ev.crash.astype(bool)
S['n_booms']=int(len(F)); S['n_topics']=int(F.topic.nunique()); S['n_evaluable']=int(len(ev)); S['n_ongoing']=int((~F.evaluable).sum())
S['crash_rate']=float(ev.crash.mean()); S['crash_ci']=wilson(int(ev.crash.sum()),len(ev)); S['n_crash']=int(ev.crash.sum())
S['drawdown_median']=float(ev.drawdown.median()); S['share_dd50']=float((ev.drawdown>=0.5).mean()); S['share_dd20']=float((ev.drawdown<0.2).mean())
S['share_revert']=float((ev.net_gain<1).mean()); S['net_gain_median']=float(ev.net_gain.median()); S['net_gain_median_crash']=float(ev[ev.crash].net_gain.median()); S['net_gain_median_soft']=float(ev[~ev.crash].net_gain.median())
S['years_to_min_median']=float(ev[ev.crash].years_to_min.median())
S['by_decade']={int(d):dict(n=int(len(g)),rate=float(g.crash.mean()),ci=wilson(int(g.crash.sum()),len(g))) for d,g in ev.groupby(ev.peak_year//10*10)}
DN={1:'Life',2:'Social',3:'Physical',4:'Health'}; S['by_domain']={DN.get(int(d),str(d)):dict(n=int(len(g)),rate=float(g.crash.mean()),ci=wilson(int(g.crash.sum()),len(g))) for d,g in ev.groupby('domain')}
# dose-response by run-up class (constant-source)
cls=[]
for lo,hi,lab in ((1.5,2,'1.5-2'),(2,3,'2-3'),(3,1e9,'>=3')):
    g=ev[(ev.runup>=lo)&(ev.runup<hi)]; cls.append(dict(cls=lab,n=len(g),rate=g.crash.mean(),lo=wilson(int(g.crash.sum()),len(g))[0],hi=wilson(int(g.crash.sum()),len(g))[1],dd_med=g.drawdown.median(),revert=(g.net_gain<1).mean()))
S['dose']=cls; pd.DataFrame(cls).to_csv(f'{A}/dose.csv',index=False)
S['spearman_runup_drawdown']=float(ev.runup.corr(ev.drawdown,method='spearman'))
if os.path.exists(os.path.join(R,'null_model.csv')): S['null']=pd.read_csv(os.path.join(R,'null_model.csv')).to_dict(orient='records')
# sensitivity: alternative definitions
sens=[]
for f,lab in (('episodes_cs_R1.5_N200.parquet','constant-source, run-up>=1.5, >=200 papers (main)'),('episodes_cs_R2.0_N300.parquet','constant-source, run-up>=2, >=300 papers')):
    p=os.path.join(R,f)
    if os.path.exists(p):
        d=pd.read_parquet(p); d=d[d.evaluable]
        for thr in (0.3,0.4,0.5): sens.append(dict(definition=lab,crash_threshold=thr,n=len(d),rate=float((d.drawdown>=thr).mean())))
for f,lab in (('episodes_n_R2.0_C0.4_N300_W5.parquet','stable-core share, run-up>=2 (no constant-source panel)'),):
    p=os.path.join(R,f)
    if os.path.exists(p):
        d=pd.read_parquet(p); d=d[d.evaluable]
        for thr in (0.3,0.4,0.5): sens.append(dict(definition=lab,crash_threshold=thr,n=len(d),rate=float((d.drawdown>=thr).mean())))
for lab,mask in (('excluding topics with < 50% English papers',ev.en_share_pre>=0.5),('excluding top-source share > 30% at the peak',ev.top_source_share_pre<=0.3),('peaks 1990-2015 only',(ev.peak_year>=1990)&(ev.peak_year<=2015)),
                 ('excluding booms led by conference-proceedings serials',~ev.proc_led),('diffuse booms only (top-3 venues < 50% of the run-up)',ev.top3_share_inc<0.5),('venue-concentrated booms only (top-3 venues >= 50% of the run-up)',ev.top3_share_inc>=0.5)):
    g=ev[mask]; sens.append(dict(definition=lab,crash_threshold=0.4,n=len(g),rate=float(g.crash.mean())))
fw=ev[ev.boom_fw==True]; sens.append(dict(definition='fixed source weights (booms that remain booms; crash measured on the fixed-weight index)',crash_threshold=0.4,n=len(fw),rate=float(fw.crash_fw.astype(float).mean())))
S['fixed_weight']=dict(n_boom_fw=int(len(fw)),crash_rate_fw=float(fw.crash_fw.astype(float).mean()),crash_rate_main_among=float(fw.crash.mean()),spearman_runup=float(ev.runup.corr(ev.runup_fw,method='spearman')),spearman_drawdown=float(ev.drawdown.corr(ev.drawdown_fw,method='spearman')))
S['proc_led']=dict(n=int(ev.proc_led.sum()),crash=float(ev[ev.proc_led].crash.mean()),n_ttp=int(ev.top1_name.str.contains('Trans Tech').sum()),crash_ttp=float(ev[ev.top1_name.str.contains('Trans Tech')].crash.mean()))
S['venue_conc']=dict(n_conc=int((ev.top3_share_inc>=0.5).sum()),crash_conc=float(ev[ev.top3_share_inc>=0.5].crash.mean()),ci_conc=wilson(int(ev[ev.top3_share_inc>=0.5].crash.sum()),int((ev.top3_share_inc>=0.5).sum())),n_diff=int((ev.top3_share_inc<0.5).sum()),crash_diff=float(ev[ev.top3_share_inc<0.5].crash.mean()),ci_diff=wilson(int(ev[ev.top3_share_inc<0.5].crash.sum()),int((ev.top3_share_inc<0.5).sum())))
S['sensitivity']=sens; pd.DataFrame(sens).to_csv(f'{A}/sensitivity.csv',index=False)
# ---------------- ex-ante signatures: group comparisons and logistic models
SIG=[('accel','Growth acceleration (log share, 2nd difference)'),('runup','Run-up (peak share / trough share)'),('low_fwci_share_pre','Share of papers with FWCI < 0.25'),('fwci_log','log mean FWCI'),('uncited_share_pre','Share of papers never cited'),
     ('newcomer_share_pre','Share of authors new to the topic'),('new_scientist_share_pre','Share of authors new to science'),('within_topic_share_pre','Within-topic reference share'),('awards_log','log(1 + awards per 100 papers)'),
     ('review_share_pre','Share of reviews'),('top_country_share_pre','Top-country share'),('top_source_share_pre','Top-source share'),('top3_share_inc','Share of the run-up carried by the three largest venues'),('team_mean_pre','Mean team size'),('en_share_pre','Share of papers in English'),('log_npeak','log papers at peak')]
ev['fwci_log']=np.log(ev.fwci_mean_pre.clip(lower=0.01)); ev['awards_log']=np.log1p(ev.awards_per_100_pre.fillna(0)); ev['log_npeak']=np.log(ev.n_peak_cs); ev['decade']=(ev.peak_year//10*10).astype(str); ev['dom']=ev.domain.map(DN)
comp=[]
for c,lab in SIG:
    a=ev[ev.crash][c].dropna(); b=ev[~ev.crash][c].dropna()
    if len(a)<5 or len(b)<5: continue
    u=stats.mannwhitneyu(a,b); comp.append(dict(var=c,label=lab,median_crash=a.median(),median_soft=b.median(),mean_crash=a.mean(),mean_soft=b.mean(),p=u.pvalue,n_crash=len(a),n_soft=len(b),auc=roc_auc_score(np.r_[np.ones(len(a)),np.zeros(len(b))],np.r_[a,b])))
comp=pd.DataFrame(comp); comp.to_csv(f'{A}/signatures.csv',index=False); S['signatures']=comp.round(5).to_dict(orient='records')
X=ev[[c for c,_ in SIG]].copy(); X=X.fillna(X.median()); Z=(X-X.mean())/X.std(); Z['crash']=ev.crash.astype(int).values; Z['decade']=ev.decade.values; Z['dom']=ev.dom.values; Z['peak_year']=ev.peak_year.values; Z['drawdown']=ev.drawdown.values; Z['proc_led']=ev.proc_led.values
main_vars=['accel','runup','low_fwci_share_pre','awards_log','newcomer_share_pre','within_topic_share_pre','review_share_pre','top_country_share_pre','top3_share_inc','log_npeak']
rows=[]
for spec,vars_ in (('univariate',None),('multivariate',main_vars),('multivariate_all',[c for c,_ in SIG])):
    if spec=='univariate':
        for c in [c for c,_ in SIG]:
            m=smf.logit(f'crash ~ {c} + C(decade) + C(dom)',data=Z).fit(disp=0); rows.append(dict(spec=spec,var=c,or_per_sd=np.exp(m.params[c]),lo=np.exp(m.conf_int().loc[c,0]),hi=np.exp(m.conf_int().loc[c,1]),p=m.pvalues[c]))
    else:
        m=smf.logit('crash ~ '+' + '.join(vars_)+' + C(decade) + C(dom)',data=Z).fit(disp=0)
        for c in vars_: rows.append(dict(spec=spec,var=c,or_per_sd=np.exp(m.params[c]),lo=np.exp(m.conf_int().loc[c,0]),hi=np.exp(m.conf_int().loc[c,1]),p=m.pvalues[c]))
        S[f'{spec}_pseudo_r2']=float(m.prsquared); S[f'{spec}_auc_insample']=float(roc_auc_score(Z.crash,m.predict(Z)))
lg=pd.DataFrame(rows); lg.to_csv(f'{A}/logit.csv',index=False); S['logit']=lg.round(5).to_dict(orient='records')
# out-of-sample: train on peaks <= 2008, test 2009-2020; and leave-one-decade-out
tr=Z[Z.peak_year<=2008]; te=Z[Z.peak_year>2008]
m=smf.logit('crash ~ '+' + '.join(main_vars),data=tr).fit(disp=0); S['oos_auc']=float(roc_auc_score(te.crash,m.predict(te))); S['oos_n_train']=int(len(tr)); S['oos_n_test']=int(len(te))
m1=smf.logit('crash ~ runup',data=tr).fit(disp=0); S['oos_auc_runup_only']=float(roc_auc_score(te.crash,m1.predict(te)))
m2=smf.logit('crash ~ accel + low_fwci_share_pre + awards_log + review_share_pre',data=tr).fit(disp=0); S['oos_auc_quality']=float(roc_auc_score(te.crash,m2.predict(te)))
m3=smf.logit('crash ~ top3_share_inc',data=tr).fit(disp=0); S['oos_auc_venue_only']=float(roc_auc_score(te.crash,m3.predict(te)))
m4=smf.logit('crash ~ '+' + '.join([v for v in main_vars if v!='top3_share_inc']),data=tr).fit(disp=0); S['oos_auc_no_venue']=float(roc_auc_score(te.crash,m4.predict(te)))
trx=tr[~Z.loc[tr.index,'proc_led']] if 'proc_led' in Z else tr; tex=te[~Z.loc[te.index,'proc_led']] if 'proc_led' in Z else te
m5=smf.logit('crash ~ '+' + '.join(main_vars),data=trx).fit(disp=0); S['oos_auc_excl_proc']=float(roc_auc_score(tex.crash,m5.predict(tex))); S['oos_n_excl_proc']=[int(len(trx)),int(len(tex))]
# calibration by tercile of predicted probability in the test set
te=te.assign(p=m.predict(te)); te['tercile']=pd.qcut(te.p,3,labels=['low','mid','high']); S['oos_calibration']={str(k):dict(n=int(len(g)),pred=float(g.p.mean()),obs=float(g.crash.mean())) for k,g in te.groupby('tercile')}
te[['peak_year','crash','p','tercile']].to_csv(f'{A}/oos_predictions.csv',index=False)
# drawdown OLS
mo=smf.ols('drawdown ~ '+' + '.join(main_vars)+' + C(decade) + C(dom)',data=Z).fit(cov_type='HC1'); S['ols_drawdown']={c:dict(coef=float(mo.params[c]),lo=float(mo.conf_int().loc[c,0]),hi=float(mo.conf_int().loc[c,1]),p=float(mo.pvalues[c])) for c in main_vars}
# ---------------- retractions (rates per 10,000 papers)
def pois_rate(num,den): return 1e4*num.sum()/den.sum()
ev['r_boom']=ev.retract_boom*ev.n_boom; ev['r_pre']=ev.retract_pre*ev.n_preboom; ev['r_post']=ev.retract_post*ev.n_postboom
S['retract']={'pre_per10k':pois_rate(ev.r_pre,ev.n_preboom),'boom_per10k':pois_rate(ev.r_boom,ev.n_boom),'post_per10k':pois_rate(ev.r_post,ev.n_postboom),
              'boom_crash_per10k':pois_rate(ev[ev.crash].r_boom,ev[ev.crash].n_boom),'boom_soft_per10k':pois_rate(ev[~ev.crash].r_boom,ev[~ev.crash].n_boom),
              'pre_crash_per10k':pois_rate(ev[ev.crash].r_pre,ev[ev.crash].n_preboom),'pre_soft_per10k':pois_rate(ev[~ev.crash].r_pre,ev[~ev.crash].n_preboom),
              'post_crash_per10k':pois_rate(ev[ev.crash].r_post,ev[ev.crash].n_postboom),'post_soft_per10k':pois_rate(ev[~ev.crash].r_post,ev[~ev.crash].n_postboom)}
# standardized retraction ratios (observed / expected at field-year rates)
def sirci(o,e):
    o=float(o); e=float(e); r=o/e if e else np.nan; lo,hi=(stats.chi2.ppf(0.025,2*o)/2/e if o>0 else 0.0, stats.chi2.ppf(0.975,2*o+2)/2/e) if e else (np.nan,np.nan); return [r,lo,hi,o,e]
S['sir']={'boom_all':sirci(ev.ret_obs_boom.sum(),ev.ret_exp_boom.sum()),'pre_all':sirci(ev.ret_obs_pre.sum(),ev.ret_exp_pre.sum()),'post_all':sirci(ev.ret_obs_post.sum(),ev.ret_exp_post.sum()),
          'boom_crash':sirci(ev[ev.crash].ret_obs_boom.sum(),ev[ev.crash].ret_exp_boom.sum()),'boom_soft':sirci(ev[~ev.crash].ret_obs_boom.sum(),ev[~ev.crash].ret_exp_boom.sum()),
          'pre_crash':sirci(ev[ev.crash].ret_obs_pre.sum(),ev[ev.crash].ret_exp_pre.sum()),'pre_soft':sirci(ev[~ev.crash].ret_obs_pre.sum(),ev[~ev.crash].ret_exp_pre.sum()),
          'post_crash':sirci(ev[ev.crash].ret_obs_post.sum(),ev[ev.crash].ret_exp_post.sum()),'post_soft':sirci(ev[~ev.crash].ret_obs_post.sum(),ev[~ev.crash].ret_exp_post.sum())}
S['sir_rw']={'boom_all':sirci(ev.rw_obs_boom.sum(),ev.rw_exp_boom.sum()),'pre_all':sirci(ev.rw_obs_pre.sum(),ev.rw_exp_pre.sum()),'post_all':sirci(ev.rw_obs_post.sum(),ev.rw_exp_post.sum()),
             'boom_crash':sirci(ev[ev.crash].rw_obs_boom.sum(),ev[ev.crash].rw_exp_boom.sum()),'boom_soft':sirci(ev[~ev.crash].rw_obs_boom.sum(),ev[~ev.crash].rw_exp_boom.sum())}
# rate ratio boom vs pre with Poisson CI
rr=(ev.r_boom.sum()/ev.n_boom.sum())/(ev.r_pre.sum()/ev.n_preboom.sum()); se=np.sqrt(1/ev.r_boom.sum()+1/ev.r_pre.sum()); S['retract']['rr_boom_vs_pre']=[float(rr),float(rr*np.exp(-1.96*se)),float(rr*np.exp(1.96*se))]
rr2=(ev[ev.crash].r_boom.sum()/ev[ev.crash].n_boom.sum())/(ev[~ev.crash].r_boom.sum()/ev[~ev.crash].n_boom.sum()); se2=np.sqrt(1/ev[ev.crash].r_boom.sum()+1/ev[~ev.crash].r_boom.sum()); S['retract']['rr_crash_vs_soft']=[float(rr2),float(rr2*np.exp(-1.96*se2)),float(rr2*np.exp(1.96*se2))]
# ---------------- aftermath: attention and level
S['attention_ratio_median_crash']=float(ev[ev.crash].attention_ratio_t5.median()); S['attention_ratio_median_soft']=float(ev[~ev.crash].attention_ratio_t5.median()); S['attention_share_up_crash']=float((ev[ev.crash].attention_ratio_t5>1).mean())
S['level_above_pre_crash']=float((ev[ev.crash].net_gain>1).mean()); S['level_above_pre_soft']=float((ev[~ev.crash].net_gain>1).mean())
# ---------------- entrants
if os.path.exists(os.path.join(R,'entrants.parquet')):
    en=pd.read_parquet(os.path.join(R,'entrants.parquet')); en=en[en.evaluable]
    agg=en.groupby(['grp','crash']).apply(lambda g: pd.Series({c:np.average(g[c],weights=g.n) for c in ['still_publishing_t5','still_in_topic_t5','moved_t5','share_new_scientists']})).reset_index()
    agg.to_csv(f'{A}/entrants.csv',index=False); S['entrants']=agg.round(4).to_dict(orient='records')
    # paired within-episode differences entrant vs incumbent by crash status
    w=en.pivot_table(index=['topic','peak_year','crash'],columns='grp',values=['still_publishing_t5','still_in_topic_t5']).dropna()
    S['entrants_paired']={str(k):dict(n=int(len(g)),exit_gap=float((g[('still_publishing_t5','incumbent')]-g[('still_publishing_t5','entrant')]).mean()),topic_gap=float((g[('still_in_topic_t5','incumbent')]-g[('still_in_topic_t5','entrant')]).mean())) for k,g in w.groupby(level='crash')}
# ---------------- ongoing booms: predicted crash probability from the multivariate model (fitted on all evaluable booms)
mfull=smf.logit('crash ~ '+' + '.join(main_vars),data=Z).fit(disp=0)
og=F[~F.evaluable].copy(); og['fwci_log']=np.log(og.fwci_mean_pre.clip(lower=0.01)); og['awards_log']=np.log1p(og.awards_per_100_pre.fillna(0)); og['log_npeak']=np.log(og.n_peak_cs)
Xo=og[[c for c,_ in SIG]].fillna(X.median()); Zo=(Xo-X.mean())/X.std(); og['p_crash']=mfull.predict(Zo)
og[['topic','name','peak_year','n_peak_cs','runup','p_crash','accel','low_fwci_share_pre','fwci_mean_pre','awards_per_100_pre','review_share_pre','newcomer_share_pre','top3_share_inc','top1_name']].sort_values('n_peak_cs',ascending=False).to_csv(f'{A}/ongoing.csv',index=False)
S['ongoing_top']=og.sort_values('n_peak_cs',ascending=False).head(15)[['name','peak_year','n_peak_cs','runup','p_crash']].round(3).to_dict(orient='records'); S['ongoing_p_median']=float(og.p_crash.median()); S['ongoing_share_p50']=float((og.p_crash>0.5).mean())
ev.to_parquet(os.path.join(R,'evaluable.parquet'),index=False)
json.dump(S,open(os.path.join(R,'summary.json'),'w'),indent=1,default=float)
print(json.dumps({k:v for k,v in S.items() if k in ('n_booms','n_evaluable','n_ongoing','crash_rate','crash_ci','share_revert','net_gain_median','oos_auc','oos_auc_runup_only','oos_auc_quality','multivariate_auc_insample','retract','attention_ratio_median_crash','attention_ratio_median_soft','entrants_paired','oos_calibration')},indent=1,default=str))
print(lg[lg.spec=='multivariate'].round(3).to_string())
