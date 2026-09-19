"""Fig. 1 | Research booms and what follows them. (A) Eight booms in the constant-source panel, share of output normalized to the peak year.
(B) All 350 evaluable booms: median and interquartile range of the normalized share, crash vs soft landing. (C) Drawdown distribution.
(D) Reversal rate by run-up class, observed vs a time-shuffled growth null (stable-core series). (E) Crash rate by decade and domain."""
import os, sys, json, numpy as np, pandas as pd, matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figstyle import *
from matplotlib.transforms import ScaledTranslation
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R=os.path.join(ROOT,'results')
S=loadj(os.path.join(R,'summary.json')); E=pd.read_parquet(os.path.join(R,'episodes_cs.parquet')); cs=pd.read_parquet(os.path.join(ROOT,'data','build','cs_series.parquet'))
ev=pd.read_parquet(os.path.join(R,'evaluable.parquet')); null=pd.read_csv(os.path.join(R,'null_model.csv'))
CR=PALETTE['red_strong']; SO=PALETTE['blue_main']; NU=PALETTE['neutral_mid']
EX=[('Cold Fusion and Nuclear Reactions',1990,'Cold fusion'),('Fullerene Chemistry and Applications',1993,'Fullerenes'),('Helicobacter pylori-related gastroenterology studies',1998,'Helicobacter pylori'),
    ('Superconductivity in MgB2 and Alloys',2003,'Magnesium diboride'),('SARS-CoV-2 and COVID-19 Research',2004,'SARS coronavirus'),('Iron-based superconductors research',2009,'Fe-based superconductors'),
    ('Graphene research and applications',2014,'Graphene'),('COVID-19 Clinical Research Studies',2020,'COVID-19 clinical')]
fig=plt.figure(figsize=(175*MM,112*MM))
gs=fig.add_gridspec(3,4,height_ratios=[1,1,1.35],left=0.075,right=0.99,top=0.93,bottom=0.085,hspace=0.7,wspace=0.45)
# ---- A: examples
for i,(nm,t,short) in enumerate(EX):
    ax=fig.add_subplot(gs[i//4,i%4]); r=E[(E.name==nm)&(E.peak_year==t)].iloc[0]; s=cs[(cs.topic==r.topic)&(cs.t==t)].sort_values('year')
    y=s.share/s.share.max(); k=s.year-t; col=CR if r.crash else SO
    ax.axhspan(0,0.6,color=PALETTE['neutral_light'],alpha=0.25,lw=0); ax.axvline(0,color=PALETTE['neutral_light'],lw=0.6)
    ax.plot(k,y,color=col,lw=1.1,marker='o',ms=2); ax.set_xlim(-5.4,5.4); ax.set_ylim(0,1.08); ax.set_xticks([-5,0,5]); ax.set_yticks([0,0.5,1])
    off=lambda dy: ScaledTranslation(2/72,dy/72,fig.dpi_scale_trans)
    ax.text(0,1,f'{short}, {t}',transform=ax.transAxes+off(10),fontsize=6,va='bottom',ha='left')
    ax.text(0,1,(f'run-up ×{r.runup:.0f}' if r.runup>=10 else f'run-up ×{r.runup:.1f}')+f', drawdown {100*r.drawdown:.0f}%',transform=ax.transAxes+off(2.5),fontsize=5.5,va='bottom',ha='left',color=PALETTE['neutral_dark'])
    if i%4==0: ax.set_ylabel('Share of output\n(peak = 1)')
    if i>=4: ax.set_xlabel('Years from peak')
    if i==0: add_panel_label(ax,'A')
    else: anchor_only(ax)
# ---- B: all evaluable booms, normalized paths
ax=fig.add_subplot(gs[2,0]); W=5
paths={}
for _,r in ev.iterrows():
    s=cs[(cs.topic==r.topic)&(cs.t==r.peak_year)].set_index('year').reindex(range(r.peak_year-W,r.peak_year+W+1)); paths[(r.topic,r.peak_year)]=(s.share/s.share.iloc[W]).values
Pm=np.array(list(paths.values())); k=np.arange(-W,W+1); crash=ev.crash.values.astype(bool)
ax.axhspan(0,0.6,color=PALETTE['neutral_light'],alpha=0.25,lw=0)
for m,col,lab in ((crash,CR,f'Crash (n = {crash.sum()})'),(~crash,SO,f'Soft landing (n = {(~crash).sum()})')):
    q=np.nanpercentile(Pm[m],[25,50,75],axis=0); ax.fill_between(k,q[0],q[2],color=col,alpha=0.18,lw=0); ax.plot(k,q[1],color=col,lw=1.3,label=lab)
ax.set_xlim(-5.4,5.4); ax.set_ylim(0,1.32); ax.set_xticks([-5,0,5]); ax.set_yticks([0,0.5,1]); ax.set_xlabel('Years from peak'); ax.set_ylabel('Share of output (peak = 1)')
ax.legend(loc='upper left',fontsize=5.5,handlelength=1.4,borderaxespad=0.1,ncol=1,labelspacing=0.3); ax.text(-5.1,0.04,'≥ 40% drawdown',fontsize=5.5,ha='left',va='bottom',color=PALETTE['neutral_dark']); add_panel_label(ax,'B')
# ---- C: drawdown distribution
ax=fig.add_subplot(gs[2,1]); bins=np.arange(0,1.0001,0.05); dd=ev.drawdown.clip(upper=0.9999)
ax.hist(dd[~crash],bins=bins,color=SO,alpha=0.9,lw=0); ax.hist(dd[crash],bins=bins,color=CR,alpha=0.9,lw=0)
ax.axvline(0.4,color=PALETTE['neutral_dark'],lw=0.6,ls='--'); ax.set_xlabel('Drawdown within 5 years'); ax.set_ylabel('Booms'); ax.set_xticks([0,0.2,0.4,0.6,0.8,1]); ax.set_xticklabels(['0','20%','40%','60%','80%','100%'])
ax.set_ylim(0,60); ax.text(0.99,59,f'crash: {100*S["crash_rate"]:.0f}%\n(95% CI {100*S["crash_ci"][0]:.0f}–{100*S["crash_ci"][1]:.0f}%)\nmedian: {100*S["drawdown_median"]:.0f}%',fontsize=5.5,va='top',ha='right',color=PALETTE['neutral_dark']); add_panel_label(ax,'C')
# ---- D: reversal rate by run-up class, observed vs null (stable-core series)
ax=fig.add_subplot(gs[2,2]); x=np.arange(len(null)); w=0.36
ax.bar(x-w/2,100*null.crash_obs,w,color=PALETTE['neutral_black'],label='Observed'); ax.bar(x+w/2,100*null.crash_null,w,yerr=100*2*null.crash_null_sd,color=PALETTE['neutral_light'],ecolor=NU,error_kw=dict(lw=0.6),label='Shuffled growth (null)')
ax.set_xticks(x); ax.set_xticklabels(['1.2–1.5','1.5–2','2–3','≥ 3']); ax.set_xlabel('Run-up (peak share / trough share)'); ax.set_ylabel('Reversal ≥ 40% (%)'); ax.set_ylim(0,100)
ax.legend(loc='upper left',fontsize=5.5,handlelength=1,borderaxespad=0.2); add_panel_label(ax,'D')
# ---- E: crash rate by decade and domain (constant-source booms)
ax=fig.add_subplot(gs[2,3]); rows=[]
for d in ['1980','1990','2000','2010','2020']:
    b=S['by_decade'][d]; rows.append((f'{d}s' if d!='2020' else '2020',b['rate'],b['ci'],b['n'],PALETTE['neutral_black']))
for d,c in (('Physical',PALETTE['blue_main']),('Life',PALETTE['teal']),('Health',PALETTE['red_strong']),('Social',PALETTE['gold'])):
    b=S['by_domain'][d]; rows.append((d,b['rate'],b['ci'],b['n'],c))
ys=np.arange(len(rows)); ys=np.where(ys>=5,ys+0.8,ys)
for y,(lab,r,ci,n,c) in zip(ys,rows):
    ax.errorbar(100*r,y,xerr=[[100*(r-ci[0])],[100*(ci[1]-r)]],fmt='o',ms=3,color=c,ecolor=c,elinewidth=0.8,capsize=1.5)
ax.axvline(100*S['crash_rate'],color=PALETTE['neutral_light'],lw=0.8,zorder=0)
for y,(lab,r,ci,n,c) in zip(ys,rows): ax.text(100,y,f'{n}',fontsize=5,ha='right',va='center',color=NU)
ax.set_yticks(ys); ax.set_yticklabels([r[0] for r in rows],fontsize=6); ax.invert_yaxis(); ax.set_xlim(0,100); ax.set_xlabel('Crash rate (%)'); ax.text(100,-1.1,'n',fontsize=5,ha='right',va='bottom',color=NU); add_panel_label(ax,'E')
finalize(fig,os.path.join(os.path.dirname(os.path.abspath(__file__)),'out','fig1'))
