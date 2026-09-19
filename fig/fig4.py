"""Fig. 4 | The aftermath of a boom. (A) Retractions among papers published before, during and after the boom, relative to the field-year expectation
(observed/expected with 95% Poisson CI), OpenAlex flags and Retraction Watch-confirmed. (B) Citations to the topic's papers five years after the peak
relative to the peak year. (C) Output share five years after the peak relative to five years before. (D) Fate of the scientists who entered the topic
during the boom versus the incumbents: still publishing at t+5 and still publishing in the topic at t+5 (episode-weighted means, 95% bootstrap CI)."""
import os, sys, numpy as np, pandas as pd, matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figstyle import *
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R=os.path.join(ROOT,'results')
S=loadj(os.path.join(R,'summary.json')); ev=pd.read_parquet(os.path.join(R,'evaluable.parquet')); ev['crash']=ev.crash.astype(bool); en=pd.read_parquet(os.path.join(R,'entrants.parquet')); en=en[en.evaluable].copy(); en['crash']=en.crash.astype(bool)
CR=PALETTE['red_strong']; SO=PALETTE['blue_main']; AL=PALETTE['neutral_black']; rng=np.random.default_rng(1)
fig,axs=plt.subplots(2,2,figsize=(120*MM,98*MM),gridspec_kw=dict(left=0.1,right=0.99,top=0.95,bottom=0.1,wspace=0.4,hspace=0.55))
# ---- A standardized retraction ratios
ax=axs[0,0]; groups=[('all','All booms',AL),('crash','Crash',CR),('soft','Soft landing',SO)]; wins=[('pre','Before\n(t−8 to t−6)'),('boom','Boom\n(t−2 to t)'),('post','After\n(t+1 to t+3)')]
for gi,(g,gl,col) in enumerate(groups):
    for wi,(w,wl) in enumerate(wins):
        x=wi+(gi-1)*0.27
        for src,mk,dx in (('sir','o',-0.05),('sir_rw','s',0.05)):
            r=S[src].get(f'{w}_{g}')
            if r is None: continue
            ax.errorbar(x+dx,r[0],yerr=[[r[0]-r[1]],[r[2]-r[0]]],fmt=mk,ms=2.8,color=col,ecolor=col,elinewidth=0.8,capsize=1.2,mfc=col if src=='sir' else 'white',mew=0.8)
ax.axhline(1,color=PALETTE['neutral_light'],lw=0.8,zorder=0); ax.set_xticks(range(3)); ax.set_xticklabels([w[1] for w in wins],fontsize=6); ax.set_ylabel('Retractions, observed / expected'); ax.set_yscale('log'); ax.set_ylim(0.5,24); ax.set_yticks([0.5,1,2,4,8,16]); ax.set_yticklabels(['0.5','1','2','4','8','16']); ax.yaxis.set_minor_formatter(plt.NullFormatter())
for g,gl,col in groups: ax.plot([],[],'o',ms=2.8,color=col,label=gl)
ax.plot([],[],'o',ms=2.8,color=PALETTE['neutral_mid'],mfc=PALETTE['neutral_mid'],label='OpenAlex flag'); ax.plot([],[],'s',ms=2.8,color=PALETTE['neutral_mid'],mfc='white',label='Retraction Watch')
ax.legend(loc='upper left',fontsize=5.2,handlelength=1,borderaxespad=0.2,ncol=2,columnspacing=0.8,labelspacing=0.3); add_panel_label(ax,'A')
# ---- B attention ratio ECDF
ax=axs[0,1]
for m,col,nm in ((False,SO,'Soft landing'),(True,CR,'Crash')):
    x=np.sort(ev[ev.crash==m].attention_ratio_t5.dropna()); ax.step(x,np.arange(1,len(x)+1)/len(x)*100,where='post',color=col,lw=1.2,label=nm)
ax.axvline(1,color=PALETTE['neutral_light'],lw=0.8,zorder=0); ax.set_xscale('log'); ax.set_xlim(0.25,6); ax.set_xticks([0.25,0.5,1,2,4]); ax.set_xticklabels(['0.25','0.5','1','2','4']); ax.xaxis.set_minor_formatter(plt.NullFormatter())
ax.set_xlabel('Citations at t+5 / citations at the peak'); ax.set_ylabel('Booms (cumulative %)'); ax.set_ylim(0,100)
up_c=100*(ev[ev.crash].attention_ratio_t5>1).mean(); up_s=100*(ev[~ev.crash].attention_ratio_t5>1).mean()
ax.text(0.03,0.97,f'still rising at t+5:\ncrash {up_c:.0f}%, soft {up_s:.0f}%',transform=ax.transAxes,fontsize=5.5,va='top',ha='left',color=PALETTE['neutral_dark']); ax.legend(loc='lower right',fontsize=5.5,handlelength=1.4,borderaxespad=0.2); add_panel_label(ax,'B')
# ---- C net gain ECDF
ax=axs[1,0]
for m,col,nm in ((False,SO,'Soft landing'),(True,CR,'Crash')):
    x=np.sort(ev[ev.crash==m].net_gain.dropna().clip(upper=30)); ax.step(x,np.arange(1,len(x)+1)/len(x)*100,where='post',color=col,lw=1.2,label=nm)
ax.axvline(1,color=PALETTE['neutral_light'],lw=0.8,zorder=0); ax.set_xscale('log'); ax.set_xlim(0.25,32); ax.set_xticks([0.25,0.5,1,2,4,8,16]); ax.set_xticklabels(['0.25','0.5','1','2','4','8','16']); ax.xaxis.set_minor_formatter(plt.NullFormatter())
ax.set_xlabel('Share of output at t+5, relative to t−5'); ax.set_ylabel('Booms (cumulative %)'); ax.set_ylim(0,100)
ax.text(0.97,0.06,f'above the pre-boom level:\ncrash {100*S["level_above_pre_crash"]:.0f}%, soft {100*S["level_above_pre_soft"]:.0f}%',transform=ax.transAxes,fontsize=5.5,va='bottom',ha='right',color=PALETTE['neutral_dark']); add_panel_label(ax,'C')
# ---- D entrants vs incumbents
ax=axs[1,1]; from matplotlib.patches import Patch
def wmean_ci(g,c,B=1000):
    v=g[c].values; w=g.n.values; m=np.average(v,weights=w); idx=rng.integers(0,len(v),(B,len(v))); bs=(v[idx]*w[idx]).sum(1)/w[idx].sum(1); return m,np.percentile(bs,2.5),np.percentile(bs,97.5)
cats=[('still_publishing_t5','Still publishing\nat t+5'),('still_in_topic_t5','Still publishing\nin the topic at t+5')]
GS=1.4; CS=3.4
for ci,(c,cl) in enumerate(cats):
    for gi,grp in enumerate(['incumbent','entrant']):
        for mi,(m,col) in enumerate(((False,SO),(True,CR))):
            g=en[(en.grp==grp)&(en.crash==m)]; mean,lo,hi=wmean_ci(g,c); x=ci*CS+gi*GS+mi*0.36
            ax.bar(x,100*mean,0.34,color=col,alpha=1 if grp=='entrant' else 0.45); ax.errorbar(x,100*mean,yerr=[[100*(mean-lo)],[100*(hi-mean)]],fmt='none',ecolor=PALETTE['neutral_dark'],elinewidth=0.7,capsize=1.2)
        ax.text(ci*CS+gi*GS+0.18,-3,'Incumbents' if grp=='incumbent' else 'Entrants',fontsize=5.5,ha='center',va='top')
    ax.text(ci*CS+GS/2+0.18,-13,cl,fontsize=6,ha='center',va='top')
ax.set_xticks([]); ax.set_ylim(0,100); ax.set_ylabel('Scientists (%)'); ax.set_xlim(-0.4,CS+GS+0.8)
ax.legend(handles=[Patch(color=SO,label='Soft landing'),Patch(color=CR,label='Crash')],loc='upper right',fontsize=5.5,handlelength=1,borderaxespad=0.2); add_panel_label(ax,'D')
finalize(fig,os.path.join(os.path.dirname(os.path.abspath(__file__)),'out','fig4'))
