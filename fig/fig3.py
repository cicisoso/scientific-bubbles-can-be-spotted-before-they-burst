"""Fig. 3 | Crashes are predictable before the peak. (A) Odds ratios per s.d. for a crash, univariate (grey) and in a joint model (blue), with
decade and domain fixed effects. (B) Out-of-sample ROC: models fitted to booms peaking up to 2008, tested on 2009-2020. (C) Calibration in the test
set by tercile of predicted probability. (D) Crash rate by venue concentration and by the pre-peak share of low-impact papers."""
import os, sys, json, numpy as np, pandas as pd, matplotlib.pyplot as plt, warnings
import statsmodels.formula.api as smf
from sklearn.metrics import roc_curve, roc_auc_score
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figstyle import *
warnings.filterwarnings('ignore')
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R=os.path.join(ROOT,'results'); A=os.path.join(R,'analysis')
S=loadj(os.path.join(R,'summary.json')); lg=pd.read_csv(os.path.join(A,'logit.csv')); ev=pd.read_parquet(os.path.join(R,'evaluable.parquet')); ev['crash']=ev.crash.astype(bool)
LAB={'accel':'Growth acceleration','runup':'Run-up (log)','low_fwci_share_pre':'Low-impact papers (FWCI < 0.25)','fwci_log':'Mean FWCI (log)','uncited_share_pre':'Never-cited papers','newcomer_share_pre':'Authors new to the topic',
     'new_scientist_share_pre':'Authors new to science','within_topic_share_pre':'References within the topic','awards_log':'Linked grants (log)','review_share_pre':'Reviews','top_country_share_pre':'Top-country share',
     'top_source_share_pre':'Top-venue share of papers','top3_share_inc':'Run-up carried by top-3 venues','team_mean_pre':'Authors per paper','en_share_pre':'Papers in English','log_npeak':'Papers at the peak (log)'}
main=['top3_share_inc','runup','accel','low_fwci_share_pre','newcomer_share_pre','top_country_share_pre','awards_log','within_topic_share_pre','review_share_pre','log_npeak']
others=['fwci_log','uncited_share_pre','new_scientist_share_pre','top_source_share_pre','team_mean_pre','en_share_pre']
def get(spec,v):
    r=lg[(lg.spec==spec)&(lg['var']==v)]; return (r.or_per_sd.iloc[0],r.lo.iloc[0],r.hi.iloc[0]) if len(r) else (np.nan,np.nan,np.nan)
fig=plt.figure(figsize=(175*MM,105*MM)); gs=fig.add_gridspec(2,3,width_ratios=[1.45,1,1],left=0.2,right=0.99,top=0.95,bottom=0.12,wspace=0.45,hspace=0.55)
# ---- A forest
ax=fig.add_subplot(gs[:,0]); rows=main+others; ys=np.arange(len(rows),dtype=float); ys[len(main):]+=0.8
for y,v in zip(ys,rows):
    e,lo,hi=get('univariate',v); hic=min(hi,55)
    ax.errorbar(e,y+0.18,xerr=[[e-lo],[hic-e]],fmt='o',ms=2.6,color=PALETTE['neutral_mid'],ecolor=PALETTE['neutral_mid'],elinewidth=0.7,capsize=1.2 if hi<=55 else 0)
    if hi>55: ax.annotate('',xy=(62,y+0.18),xytext=(50,y+0.18),arrowprops=dict(arrowstyle='->',color=PALETTE['neutral_mid'],lw=0.7,shrinkA=0,shrinkB=0)); ax.text(27,y+0.95,f'{e:.0f} ({lo:.1f}–{hi:.0f})',fontsize=5,ha='center',va='top',color=PALETTE['neutral_mid'])
    if v in main:
        e,lo,hi=get('multivariate',v); ax.errorbar(e,y-0.18,xerr=[[e-lo],[hi-e]],fmt='s',ms=2.6,color=PALETTE['blue_main'],ecolor=PALETTE['blue_main'],elinewidth=0.9,capsize=1.2)
ax.axvline(1,color=PALETTE['neutral_light'],lw=0.8,zorder=0); ax.set_xscale('log'); ax.set_xlim(0.25,64); ax.set_xticks([0.25,0.5,1,2,4,8,16,32]); ax.set_xticklabels(['0.25','0.5','1','2','4','8','16','32'])
ax.xaxis.set_minor_formatter(plt.NullFormatter()); ax.set_yticks(ys); ax.set_yticklabels([LAB[v] for v in rows],fontsize=6); ax.invert_yaxis(); ax.set_ylim(ys[-1]+0.7,-0.7); ax.set_xlabel('Odds ratio for a crash, per s.d.')
ax.axhline(len(main)-0.5+0.4,color=PALETTE['neutral_light'],lw=0.5,ls=':')
ax.errorbar([],[],fmt='o',ms=2.6,color=PALETTE['neutral_mid'],label='One variable at a time'); ax.errorbar([],[],fmt='s',ms=2.6,color=PALETTE['blue_main'],label='Joint model')
ax.legend(loc='lower right',fontsize=5.5,handlelength=1,borderaxespad=0.2); add_panel_label(ax,'A')
# ---- B ROC out of sample (refit as in the statistics script)
SIG=['accel','runup','low_fwci_share_pre','fwci_log','uncited_share_pre','newcomer_share_pre','new_scientist_share_pre','within_topic_share_pre','awards_log','review_share_pre','top_country_share_pre','top_source_share_pre','top3_share_inc','team_mean_pre','en_share_pre','log_npeak']
ev['fwci_log']=np.log(ev.fwci_mean_pre.clip(lower=0.01)); ev['awards_log']=np.log1p(ev.awards_per_100_pre.fillna(0)); ev['log_npeak']=np.log(ev.n_peak_cs)
X=ev[SIG].copy(); X=X.fillna(X.median()); Z=(X-X.mean())/X.std(); Z['crash']=ev.crash.astype(int).values; Z['peak_year']=ev.peak_year.values
tr=Z[Z.peak_year<=2008]; te=Z[Z.peak_year>2008]
mv=['accel','runup','low_fwci_share_pre','awards_log','newcomer_share_pre','within_topic_share_pre','review_share_pre','top_country_share_pre','top3_share_inc','log_npeak']
models=[('All predictors',mv,PALETTE['blue_main'],1.4),('Without venue concentration',[v for v in mv if v!='top3_share_inc'],PALETTE['teal'],1.0),('Paper quality only',['accel','low_fwci_share_pre','awards_log','review_share_pre'],PALETTE['gold'],1.0),('Run-up only',['runup'],PALETTE['neutral_mid'],1.0)]
ax=fig.add_subplot(gs[0,1:]); pfull=None
for nm,vs,col,lw in models:
    m=smf.logit('crash ~ '+' + '.join(vs),data=tr).fit(disp=0); p=m.predict(te); fpr,tpr,_=roc_curve(te.crash,p); auc=roc_auc_score(te.crash,p)
    ax.plot(fpr,tpr,color=col,lw=lw,label=f'{nm} (AUC {auc:.2f})')
    if pfull is None: pfull=p
ax.plot([0,1],[0,1],color=PALETTE['neutral_light'],lw=0.6,ls='--'); ax.set_xlabel('False-positive rate'); ax.set_ylabel('True-positive rate'); ax.set_xlim(0,1); ax.set_ylim(0,1.02); ax.set_xticks([0,0.5,1]); ax.set_yticks([0,0.5,1])
ax.legend(loc='lower right',fontsize=5.5,handlelength=1.4,borderaxespad=0.2); ax.text(0.99,0.42,f'{len(tr)} training booms (peaks ≤ 2008)\n{len(te)} test booms (peaks 2009–2020)',transform=ax.transAxes,fontsize=5.5,va='bottom',ha='right',color=PALETTE['neutral_dark']); add_panel_label(ax,'B')
# ---- C calibration by tercile
ax=fig.add_subplot(gs[1,1]); cal=S['oos_calibration']; ks=['low','mid','high']; x=np.arange(3)
pred=[cal[k]['pred'] for k in ks]; obs=[cal[k]['obs'] for k in ks]; n=[cal[k]['n'] for k in ks]
w=0.36; ax.bar(x-w/2,[100*v for v in pred],w,color=PALETTE['neutral_light'],label='Predicted'); ax.bar(x+w/2,[100*v for v in obs],w,color=PALETTE['blue_main'],label='Observed')
from scipy.stats import beta
for xi,o,nn in zip(x,obs,n):
    k=round(o*nn); lo,hi=beta.ppf(0.025,k+0.5,nn-k+0.5),beta.ppf(0.975,k+0.5,nn-k+0.5); ax.errorbar(xi+w/2,100*o,yerr=[[100*(o-lo)],[100*(hi-o)]],fmt='none',ecolor=PALETTE['neutral_dark'],elinewidth=0.7,capsize=1.5)
ax.set_xticks(x); ax.set_xticklabels(['Low','Middle','High']); ax.set_xlabel('Predicted-risk tercile (test set)'); ax.set_ylabel('Crash rate (%)'); ax.set_ylim(0,100); ax.legend(loc='upper left',fontsize=5.5,handlelength=1,borderaxespad=0.2); add_panel_label(ax,'C')
# ---- D crash rate by venue concentration x low-impact share (quartiles)
ax=fig.add_subplot(gs[1,2]); ev['vq']=pd.qcut(ev.top3_share_inc,3,labels=['Diffuse','Middle','Concentrated']); ev['lq']=pd.qcut(ev.low_fwci_share_pre,2,labels=['low','high'])
def wil(k,n,z=1.96):
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return c-h,c+h
for j,(lab,col) in enumerate((('low','Fewer low-impact papers'),('high','More low-impact papers'))):
    col=[PALETTE['blue_secondary'],PALETTE['red_strong']][j]; g=ev[ev.lq==lab].groupby('vq',observed=True).crash.agg(['sum','size'])
    r=g['sum']/g['size']; ci=np.array([wil(k,n) for k,n in zip(g['sum'],g['size'])])
    xs=np.arange(3)+(j-0.5)*0.36; ax.bar(xs,100*r,0.34,color=col,label=['Fewer low-impact papers','More low-impact papers'][j]); ax.errorbar(xs,100*r,yerr=[100*(r-ci[:,0]),100*(ci[:,1]-r)],fmt='none',ecolor=PALETTE['neutral_dark'],elinewidth=0.7,capsize=1.5)
ax.set_xticks(range(3)); ax.set_xticklabels(['Diffuse','Middle','Concen-\ntrated']); ax.set_xlabel('Venue concentration (terciles)'); ax.set_ylabel('Crash rate (%)'); ax.set_ylim(0,100); ax.legend(loc='upper left',fontsize=5.5,handlelength=1,borderaxespad=0.2); add_panel_label(ax,'D')
finalize(fig,os.path.join(os.path.dirname(os.path.abspath(__file__)),'out','fig3'),exemptions=[{'panels':['a'],'checks':['row','column','vertical-gutter','horizontal-gutter','panel-label','panel-width'],'reason':'forest panel spans both rows beside a two-row grid'}])
