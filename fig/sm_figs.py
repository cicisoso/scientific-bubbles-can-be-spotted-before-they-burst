"""Supplementary figures S1-S8."""
import os, sys, json, numpy as np, pandas as pd, matplotlib.pyplot as plt, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figstyle import *
warnings.filterwarnings('ignore')
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R=os.path.join(ROOT,'results'); A=os.path.join(R,'analysis'); B=os.path.join(ROOT,'data','build'); OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'out')
S=loadj(os.path.join(R,'summary.json')); ev=pd.read_parquet(os.path.join(R,'evaluable.parquet')); ev['crash']=ev.crash.astype(bool)
CR=PALETTE['red_strong']; SO=PALETTE['blue_main']; NU=PALETTE['neutral_mid']
names={int(t['id'].split('/')[-1].lstrip('T')):t['display_name'] for t in json.load(open(os.path.join(ROOT,'data','names','topics.json')))}
which=sys.argv[1:] or ['S1','S2','S3','S4','S5','S6','S7','S8']
# ---------------- S1 coverage artefacts: raw vs stable-core vs constant-source series
if 'S1' in which:
    ty=pd.read_parquet(os.path.join(B,'topic_year.parquet')); so=pd.read_parquet(os.path.join(B,'topic_year_sources.parquet')); cs=pd.read_parquet(os.path.join(B,'cs_series.parquet'))
    d=ty.merge(so[['topic','year','n_core']],on=['topic','year']); tot=d.groupby('year')[['n_all','n_core']].sum(); d=d.merge(tot,on='year',suffixes=('','_tot')); d['s_all']=d.n_all/d.n_all_tot; d['s_core']=d.n_core/d.n_core_tot
    EX=[(13497,'Hermeneutics and narrative identity',2000),(11405,'Geophysics and gravity measurements',2023),(10995,'Methane hydrates',2021),(10083,'Graphene',2014)]
    fig,axs=plt.subplots(1,4,figsize=(175*MM,52*MM),gridspec_kw=dict(left=0.06,right=0.99,top=0.86,bottom=0.3,wspace=0.4))
    from matplotlib.ticker import FuncFormatter, LogLocator
    plain=FuncFormatter(lambda v,_: f'{v:g}')
    for ax,(t,nm,py),pl in zip(axs,EX,'ABCD'):
        g=d[d.topic==t].set_index('year').sort_index().loc[1990:2025]
        ax.plot(g.index,1e4*g.s_all,color=NU,lw=1,label='All works'); ax.plot(g.index,1e4*g.s_core,color=PALETTE['neutral_black'],lw=1,label='Stable core')
        c=cs[(cs.topic==t)&(cs.t==cs[cs.topic==t].t.min())] if t!=10083 else cs[(cs.topic==t)&(cs.t==2014)]
        for tt,gg in cs[cs.topic==t].groupby('t'): ax.plot(gg.year,1e4*gg.share,color=SO,lw=1.2,label='Constant-source panel' if tt==cs[cs.topic==t].t.min() else None)
        ax.set_title(nm,fontsize=6,x=0.06,ha='left'); ax.set_yscale('log'); ax.set_xticks([1990,2000,2010,2020]); ax.yaxis.set_minor_formatter(plt.NullFormatter()); ax.yaxis.set_major_formatter(plain); ax.set_xlabel('Year')
        if pl=='A': ax.set_ylabel('Share of output (per 10,000)')
        add_panel_label(ax,pl)
    h,l=axs[0].get_legend_handles_labels(); fig.legend(h,l,loc='lower center',ncol=3,fontsize=6,frameon=False,bbox_to_anchor=(0.5,0.0),handlelength=1.6)
    finalize(fig,os.path.join(OUT,'figS1'))
# ---------------- S2 sensitivity of the crash rate
if 'S2' in which:
    sens=pd.DataFrame(S['sensitivity']); main=sens[(sens.definition.str.contains('main'))&(sens.crash_threshold==0.4)].rate.iloc[0]
    rows=[]
    for _,r in sens.iterrows():
        lab=r.definition.replace('constant-source, run-up>=1.5, >=200 papers (main)','Main definition').replace('constant-source, run-up>=2, >=300 papers','Run-up ≥ 2 and ≥ 300 papers').replace('stable-core share, run-up>=2 (no constant-source panel)','Stable-core series, no constant-source panel').replace('excluding topics with < 50% English papers','Topics with ≥ 50% English papers').replace('excluding top-source share > 30% at the peak','Top venue ≤ 30% of papers at the peak').replace('peaks 1990-2015 only','Peaks 1990–2015').replace('excluding booms led by conference-proceedings serials','Excluding booms led by proceedings serials').replace('diffuse booms only (top-3 venues < 50% of the run-up)','Diffuse booms (top-3 venues < 50% of run-up)').replace('venue-concentrated booms only (top-3 venues >= 50% of the run-up)','Concentrated booms (top-3 venues ≥ 50% of run-up)').replace('fixed source weights (booms that remain booms; crash measured on the fixed-weight index)','Fixed source weights')
        rows.append((f'{lab}, drawdown ≥ {int(100*r.crash_threshold)}%',r.rate,r.n))
    fig,ax=plt.subplots(figsize=(175*MM,80*MM),gridspec_kw=dict(left=0.45,right=0.98,top=0.97,bottom=0.12)); ys=np.arange(len(rows))
    def wil(k,n,z=1.96):
        p=k/n; d_=1+z*z/n; c=(p+z*z/(2*n))/d_; h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d_; return c-h,c+h
    for y,(lab,r,n) in zip(ys,rows):
        lo,hi=wil(round(r*n),n); ax.errorbar(100*r,y,xerr=[[100*(r-lo)],[100*(hi-r)]],fmt='o',ms=3,color=PALETTE['blue_main'] if 'Main' in lab else PALETTE['neutral_dark'],elinewidth=0.8,capsize=1.5); ax.text(118,y,f'n = {n}',fontsize=5.5,va='center',ha='right',color=NU)
    ax.axvline(100*main,color=PALETTE['neutral_light'],lw=0.8,zorder=0); ax.set_yticks(ys); ax.set_yticklabels([r[0] for r in rows],fontsize=6); ax.invert_yaxis(); ax.set_xlim(0,120); ax.set_xticks([0,25,50,75,100]); ax.set_xlabel('Crash rate (%)')
    finalize(fig,os.path.join(OUT,'figS2'),single_panel=True)
# ---------------- S3 null model: reversion and net loss
if 'S3' in which:
    null=pd.read_csv(os.path.join(R,'null_model.csv')); x=np.arange(len(null)); w=0.36
    fig,axs=plt.subplots(1,3,figsize=(175*MM,50*MM),gridspec_kw=dict(left=0.06,right=0.99,top=0.9,bottom=0.22,wspace=0.35))
    for ax,(o,nl,lab),pl in zip(axs,(('crash_obs','crash_null','Reversal ≥ 40% within 5 years (%)'),('revert_obs','revert_null','Back to the pre-boom trough (%)'),('netloss_obs','netloss_null','Share at t+5 below share at t−5 (%)')),'ABC'):
        ax.bar(x-w/2,100*null[o],w,color=PALETTE['neutral_black'],label='Observed'); ax.bar(x+w/2,100*null[nl],w,color=PALETTE['neutral_light'],label='Shuffled growth (null)')
        ax.set_xticks(x); ax.set_xticklabels(['1.2–1.5','1.5–2','2–3','≥ 3']); ax.set_xlabel('Run-up'); ax.set_ylabel(lab); ax.set_ylim(0,100); add_panel_label(ax,pl)
        if pl=='A': ax.legend(loc='upper left',fontsize=5.5,handlelength=1,borderaxespad=0.2)
    finalize(fig,os.path.join(OUT,'figS3'))
# ---------------- S4 additional event-time profiles
if 'S4' in which:
    et=pd.read_parquet(os.path.join(R,'eventtime.parquet')); et=et[et.evaluable].copy(); et['crash']=et.crash.astype(bool); rng=np.random.default_rng(0)
    def boot(x,Bn=1000):
        x=np.asarray(x,float); x=x[~np.isnan(x)]; m=rng.choice(x,(Bn,len(x))).mean(1); return x.mean(),np.percentile(m,2.5),np.percentile(m,97.5)
    panels=[('new_scientist_share','Authors new to science (%)',100),('high_fwci_share','Papers with FWCI ≥ 2 (%)',100),('top_country_share','Top-country share (%)',100),('china_share','Share of papers from China (%)',100),
            ('top_source_share','Top-venue share of papers (%)',100),('n_sources','Venues publishing the topic',1),('refs_mean','References per paper',1),('ref_age','Mean age of cited works (years)',1),('within_cites_share','Citations from within the topic (%)',100)]
    fig,axs=plt.subplots(3,3,figsize=(175*MM,125*MM),gridspec_kw=dict(left=0.07,right=0.99,top=0.96,bottom=0.08,wspace=0.42,hspace=0.6))
    for ax,(c,lab,sc),pl in zip(axs.ravel(),panels,'ABCDEFGHI'):
        ax.axvspan(-5.5,-0.5,color=PALETTE['neutral_light'],alpha=0.25,lw=0)
        for m,col,nm in ((True,CR,'Crash'),(False,SO,'Soft landing')):
            g=et[et.crash==m]; ks=range(-5,6); st=np.array([boot(g[g.k==k][c]) for k in ks])*sc; ax.fill_between(ks,st[:,1],st[:,2],color=col,alpha=0.2,lw=0); ax.plot(ks,st[:,0],color=col,lw=1.2,marker='o',ms=2,label=nm)
        ax.set_xlim(-5.5,5.5); ax.set_xticks([-5,0,5]); ax.set_ylabel(lab); ax.axvline(0,color=NU,lw=0.5,ls=':')
        if pl in 'GHI': ax.set_xlabel('Years from peak')
        if pl=='A': ax.legend(loc='upper right',fontsize=5.5,handlelength=1.4,borderaxespad=0.2)
        add_panel_label(ax,pl)
    finalize(fig,os.path.join(OUT,'figS4'))
# ---------------- S5 drawdown regression and predicted-probability distributions
if 'S5' in which:
    LAB={'accel':'Growth acceleration','runup':'Run-up (log)','low_fwci_share_pre':'Low-impact papers','awards_log':'Linked grants (log)','newcomer_share_pre':'Authors new to the topic','within_topic_share_pre':'References within the topic','review_share_pre':'Reviews','top_country_share_pre':'Top-country share','top3_share_inc':'Run-up carried by top-3 venues','log_npeak':'Papers at the peak (log)'}
    ols=S['ols_drawdown']; rows=[(LAB[k],v) for k,v in ols.items()]
    fig,axs=plt.subplots(1,2,figsize=(120*MM,66*MM),gridspec_kw=dict(left=0.3,right=0.98,top=0.93,bottom=0.24,wspace=0.5))
    ax=axs[0]; ys=np.arange(len(rows))
    for y,(lab,v) in zip(ys,rows): ax.errorbar(100*v['coef'],y,xerr=[[100*(v['coef']-v['lo'])],[100*(v['hi']-v['coef'])]],fmt='s',ms=2.6,color=PALETTE['blue_main'],elinewidth=0.8,capsize=1.2)
    ax.axvline(0,color=PALETTE['neutral_light'],lw=0.8,zorder=0); ax.set_yticks(ys); ax.set_yticklabels([r[0] for r in rows],fontsize=6); ax.invert_yaxis(); ax.set_xlabel('Change in drawdown per s.d. (pp)'); add_panel_label(ax,'A')
    ax=axs[1]; oos=pd.read_csv(os.path.join(A,'oos_predictions.csv')); bins=np.linspace(0,1,11)
    for m,col,nm in ((0,SO,'Soft landing'),(1,CR,'Crash')):
        x=oos[oos.crash==m].p; ax.hist(x,bins=bins,weights=np.ones(len(x))/len(x)*100,color=col,alpha=0.6,lw=0,label=f'{nm} (n = {len(x)})')
    ax.set_xlabel('Predicted crash probability'); ax.set_ylabel('Booms (%)'); ax.legend(loc='upper center',fontsize=5.5,handlelength=1,borderaxespad=0.2); add_panel_label(ax,'B')
    finalize(fig,os.path.join(OUT,'figS5'))
# ---------------- S6 raw retraction rates and by domain
if 'S6' in which:
    rt=S['retract']; fig,axs=plt.subplots(1,2,figsize=(120*MM,55*MM),gridspec_kw=dict(left=0.1,right=0.98,top=0.92,bottom=0.2,wspace=0.45))
    ax=axs[0]; x=np.arange(3); w=0.27
    for j,(g,col,nm) in enumerate((('all',PALETTE['neutral_black'],'All booms'),('crash',CR,'Crash'),('soft',SO,'Soft landing'))):
        vals=[rt[f'pre_{g}_per10k'] if g!='all' else rt['pre_per10k'],rt[f'boom_{g}_per10k'] if g!='all' else rt['boom_per10k'],rt[f'post_{g}_per10k'] if g!='all' else rt['post_per10k']]
        ax.bar(x+(j-1)*w,vals,w,color=col,label=nm)
    ax.set_xticks(x); ax.set_xticklabels(['Before\n(t−8 to t−6)','Boom\n(t−2 to t)','After\n(t+1 to t+3)']); ax.set_ylabel('Retracted papers per 10,000'); ax.legend(loc='upper left',fontsize=5.5,handlelength=1,borderaxespad=0.2); add_panel_label(ax,'A')
    ax=axs[1]; DN={1:'Life',2:'Social',3:'Physical',4:'Health'}; rows=[]
    for dcode,dn in DN.items():
        g=ev[ev.domain==dcode]; o,e=g.rw_obs_boom.sum(),g.rw_exp_boom.sum(); r=o/e if e>0 else np.nan; lo,hi=(np.exp(np.log(r)-1.96/np.sqrt(o)),np.exp(np.log(r)+1.96/np.sqrt(o))) if o>0 else (np.nan,np.nan); rows.append((dn,r,lo,hi,int(o)))
    for y,(dn,r,lo,hi,o) in enumerate(rows): ax.errorbar(r,y,xerr=[[r-lo],[hi-r]],fmt='o',ms=3,color=PALETTE['neutral_black'],elinewidth=0.8,capsize=1.5)
    ax.axvline(1,color=PALETTE['neutral_light'],lw=0.8,zorder=0); ax.set_yticks(range(4)); ax.set_yticklabels([f'{r[0]} ({r[4]})' for r in rows]); ax.invert_yaxis(); ax.set_xlim(0,12.5); ax.set_xlabel('Boom-era retractions, observed / expected\n(Retraction Watch-confirmed)'); add_panel_label(ax,'B')
    finalize(fig,os.path.join(OUT,'figS6'))
# ---------------- S7 crash rate by field
if 'S7' in which:
    fields={int(t['id'].split('/')[-1]):t['display_name'] for t in json.load(open(os.path.join(ROOT,'data','names','fields.json')))}
    g=ev.groupby('field').crash.agg(['sum','size']); g=g[g['size']>=5].sort_values('sum',ascending=False); g['rate']=g['sum']/g['size']; g=g.sort_values('rate')
    def wil(k,n,z=1.96):
        p=k/n; d_=1+z*z/n; c=(p+z*z/(2*n))/d_; h=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d_; return c-h,c+h
    fig,ax=plt.subplots(figsize=(120*MM,90*MM),gridspec_kw=dict(left=0.42,right=0.97,top=0.97,bottom=0.1)); ys=np.arange(len(g))
    for y,(f,r) in zip(ys,g.iterrows()):
        lo,hi=wil(r['sum'],r['size']); ax.errorbar(100*r.rate,y,xerr=[[100*(r.rate-lo)],[100*(hi-r.rate)]],fmt='o',ms=3,color=PALETTE['neutral_black'],elinewidth=0.8,capsize=1.5); ax.text(124,y,f'{int(r["sum"])}/{int(r["size"])}',fontsize=5.5,va='center',ha='right',color=NU)
    ax.axvline(100*S['crash_rate'],color=PALETTE['neutral_light'],lw=0.8,zorder=0); ax.set_yticks(ys); ax.set_yticklabels([fields.get(int(f),str(f)) for f in g.index],fontsize=6); ax.set_xlim(0,125); ax.set_xticks([0,25,50,75,100]); ax.set_xlabel('Crash rate (%)'); ax.set_ylim(len(g)-0.5,-1.6); ax.text(124,-1.3,'crashes/booms',fontsize=5.5,ha='right',va='center',color=NU)
    finalize(fig,os.path.join(OUT,'figS7'),single_panel=True)
# ---------------- S8 fixed-weight index vs main
if 'S8' in which:
    m=ev.copy()
    fig,axs=plt.subplots(1,2,figsize=(120*MM,58*MM),gridspec_kw=dict(left=0.1,right=0.98,top=0.92,bottom=0.18,wspace=0.4))
    ax=axs[0]; ax.scatter(m.runup,m.runup_fw,s=6,c=[CR if c else SO for c in m.crash],alpha=0.6,lw=0); ax.plot([1,300],[1,300],color=PALETTE['neutral_light'],lw=0.6); ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xlabel('Run-up, constant-source panel'); ax.set_ylabel('Run-up, fixed source weights'); ax.xaxis.set_minor_formatter(plt.NullFormatter()); ax.yaxis.set_minor_formatter(plt.NullFormatter())
    from matplotlib.ticker import FuncFormatter; ax.xaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:g}')); ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_: f'{v:g}'))
    ax.text(0.03,0.97,f'Spearman ρ = {S["fixed_weight"]["spearman_runup"]:.2f}',transform=ax.transAxes,fontsize=5.5,va='top'); add_panel_label(ax,'A')
    ax=axs[1]; ax.scatter(m.drawdown,m.drawdown_fw,s=6,c=[CR if c else SO for c in m.crash],alpha=0.6,lw=0); ax.plot([0,1],[0,1],color=PALETTE['neutral_light'],lw=0.6); ax.set_xlabel('Drawdown, constant-source panel'); ax.set_ylabel('Drawdown, fixed source weights'); ax.set_xlim(-0.05,1.02); ax.set_ylim(-0.08,1.02)
    ax.text(0.03,0.97,f'Spearman ρ = {S["fixed_weight"]["spearman_drawdown"]:.2f}',transform=ax.transAxes,fontsize=5.5,va='top'); ax.scatter([],[],s=6,c=CR,label='Crash'); ax.scatter([],[],s=6,c=SO,label='Soft landing'); ax.legend(loc='lower right',fontsize=5.5,handlelength=1,borderaxespad=0.2); add_panel_label(ax,'B')
    finalize(fig,os.path.join(OUT,'figS8'))
