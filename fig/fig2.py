"""Fig. 2 | The anatomy of booms that crash and booms that do not: mean characteristics of the papers published in each year around the peak
(k = 0), crash vs soft landing, with 95% bootstrap confidence intervals of the mean; last panel: venue concentration of the run-up."""
import os, sys, numpy as np, pandas as pd, matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figstyle import *
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R=os.path.join(ROOT,'results')
ev=pd.read_parquet(os.path.join(R,'eventtime.parquet')); ev=ev[ev.evaluable].copy(); ev['crash']=ev.crash.astype(bool)
F=pd.read_parquet(os.path.join(R,'evaluable.parquet')); F['crash']=F.crash.astype(bool)
CR=PALETTE['red_strong']; SO=PALETTE['blue_main']; rng=np.random.default_rng(0)
def boot(x,B=1000):
    x=np.asarray(x,float); x=x[~np.isnan(x)]
    if len(x)==0: return np.nan,np.nan,np.nan
    m=rng.choice(x,(B,len(x))).mean(1); return x.mean(),np.percentile(m,2.5),np.percentile(m,97.5)
panels=[('low_fwci_share','Papers with FWCI < 0.25 (%)',100),('uncited_share','Papers never cited (%)',100),('fwci_mean','Mean FWCI',1),('newcomer_share','Authors new to the topic (%)',100),
        ('review_share','Reviews (%)',100),('awards_per_100','Linked grants per 100 papers',1),('within_topic_share','References within the topic (%)',100),('team_mean','Authors per paper',1)]
fig,axs=plt.subplots(3,3,figsize=(175*MM,132*MM),gridspec_kw=dict(left=0.07,right=0.99,top=0.96,bottom=0.1,wspace=0.42,hspace=0.6))
for ax,(c,lab,sc),pl in zip(axs.ravel()[:8],panels,'ABCDEFGH'):
    ax.axvspan(-5.5,-0.5,color=PALETTE['neutral_light'],alpha=0.25,lw=0)
    for m,col,nm in ((True,CR,'Crash'),(False,SO,'Soft landing')):
        g=ev[ev.crash==m]; ks=range(-5,6); st=np.array([boot(g[g.k==k][c]) for k in ks])*sc
        ax.fill_between(ks,st[:,1],st[:,2],color=col,alpha=0.2,lw=0); ax.plot(ks,st[:,0],color=col,lw=1.2,marker='o',ms=2,label=nm)
    ax.set_xlim(-5.5,5.5); ax.set_xticks([-5,0,5]); ax.set_ylabel(lab); ax.axvline(0,color=PALETTE['neutral_mid'],lw=0.5,ls=':')
    if pl in 'FGH': ax.set_xlabel('Years from peak')
    if pl=='A': ax.legend(loc='center left',fontsize=5.5,handlelength=1.4,borderaxespad=0.2)
    add_panel_label(ax,pl)
# I: venue concentration of the run-up
ax=axs.ravel()[8]; bins=np.linspace(0,1,21)
for m,col,nm in ((False,SO,'Soft landing'),(True,CR,'Crash')):
    x=F[F.crash==m].top3_share_inc; ax.hist(x,bins=bins,weights=np.ones(len(x))/len(x)*100,color=col,alpha=0.55,lw=0,label=nm)
    ax.axvline(x.median(),color=col,lw=0.8,ls='--')
ax.set_xlabel('Run-up carried by the\nthree largest venues (%)'); ax.set_ylabel('Booms (%)'); ax.set_xticks([0,0.5,1]); ax.set_xticklabels(['0','50%','100%'])
ax.text(0.98,0.97,f'medians\n{100*F[~F.crash].top3_share_inc.median():.0f}% vs {100*F[F.crash].top3_share_inc.median():.0f}%',transform=ax.transAxes,fontsize=5.5,ha='right',va='top',color=PALETTE['neutral_dark']); add_panel_label(ax,'I')
finalize(fig,os.path.join(os.path.dirname(os.path.abspath(__file__)),'out','fig2'))
