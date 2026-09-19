"""Null model for the run-up -> drawdown relation: within each topic, the annual log changes of the constant-source-like share (here the stable-core share)
are permuted in time, the series rebuilt, and booms/crashes detected with the same rules; repeated 20 times. Reports the crash rate by run-up class under
the null. Output results/null_model.csv."""
import os, numpy as np, pandas as pd
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B=os.path.join(ROOT,'data','build'); R=os.path.join(ROOT,'results'); W=5
ty=pd.read_parquet(os.path.join(B,'topic_year.parquet')).merge(pd.read_parquet(os.path.join(B,'topic_year_sources.parquet')),on=['topic','year'],how='left')
ty['n_core']=ty.n_core.fillna(0); tot=ty.groupby('year').n_core.sum(); wide=ty.pivot(index='topic',columns='year',values='n_core').reindex(columns=range(1980,2025)).fillna(0)
share=wide.div(tot,axis=1); logs=np.log(share.where(share>0)); years=np.array(share.columns)
def detect(S,N):
    rows=[]
    for topic in S.index:
        v=S.loc[topic].values; n=N.loc[topic].values
        for i in range(W,len(v)-W):
            lo=i-W; hi=i+W+1
            if not (v[i]>0) or v[i]<np.nanmax(v[lo:hi]) or (v[lo:i]==v[i]).any(): continue
            pre=v[lo:i]; post=v[i+1:hi]
            if np.nanmin(pre)<=0 or n[i]<200: continue
            run=v[i]/np.nanmin(pre); dd=1-np.nanmin(post)/v[i]; net=v[i+W]/v[lo] if v[lo]>0 else np.nan; revert=(np.nanmin(post)<=np.nanmin(pre))
            if run>=1.2: rows.append((run,dd,net,revert))
    return pd.DataFrame(rows,columns=['run','dd','net','revert'])
def classes(d):
    out={}
    for lo,hi,lab in ((1.2,1.5,'1.2-1.5'),(1.5,2,'1.5-2'),(2,3,'2-3'),(3,1e9,'>=3')):
        g=d[(d.run>=lo)&(d.run<hi)]; out[lab]=(len(g),g.dd.ge(0.4).mean() if len(g) else np.nan, g.dd.median() if len(g) else np.nan, g.revert.mean() if len(g) else np.nan, (g.net<1).mean() if len(g) else np.nan)
    return out
obs=classes(detect(share,wide)); print('observed',obs)
rng=np.random.default_rng(1); res=[]; res_rev=[]; res_net=[]
for rep in range(20):
    L=logs.values.copy(); S=np.full_like(L,np.nan)
    for r in range(L.shape[0]):
        row=L[r]; ok=~np.isnan(row)
        if ok.sum()<10: continue
        idx=np.where(ok)[0]; d=np.diff(row[idx]); rng.shuffle(d); rebuilt=np.concatenate([[row[idx[0]]],row[idx[0]]+np.cumsum(d)]); S[r,idx]=rebuilt
    Sh=pd.DataFrame(np.exp(S),index=share.index,columns=share.columns); Nh=Sh.mul(tot,axis=1).fillna(0)
    c=classes(detect(Sh,Nh)); res.append({lab:c[lab][1] for lab in c}); res_rev.append({lab:c[lab][3] for lab in c}); res_net.append({lab:c[lab][4] for lab in c}); print('rep',rep,{k:round(v,3) if v==v else None for k,v in res[-1].items()},flush=True)
nul=pd.DataFrame(res).mean(); nrev=pd.DataFrame(res_rev).mean(); nnet=pd.DataFrame(res_net).mean(); sd=pd.DataFrame(res).std()
out=pd.DataFrame({'class':list(obs),'n_obs':[obs[k][0] for k in obs],'crash_obs':[obs[k][1] for k in obs],'dd_med_obs':[obs[k][2] for k in obs],'revert_obs':[obs[k][3] for k in obs],'netloss_obs':[obs[k][4] for k in obs],'crash_null':[nul[k] for k in obs],'crash_null_sd':[sd[k] for k in obs],'revert_null':[nrev[k] for k in obs],'netloss_null':[nnet[k] for k in obs]}); out.to_csv(os.path.join(R,'null_model.csv'),index=False); print(out.round(3).to_string())
