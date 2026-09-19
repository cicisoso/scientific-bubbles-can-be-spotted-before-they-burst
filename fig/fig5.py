"""Fig. 5 | Booms in progress. (A) The 24 largest booms whose peak year is 2021 or later (not yet evaluable), with the crash probability predicted
by the joint model of Fig. 3 fitted to all 350 evaluable booms. (B) All 528 booms in progress: predicted crash probability against run-up; point
size is the number of papers at the peak; the largest COVID-19 topics are labelled."""
import os, sys, numpy as np, pandas as pd, matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figstyle import *
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R=os.path.join(ROOT,'results'); A=os.path.join(R,'analysis')
og=pd.read_csv(os.path.join(A,'ongoing.csv')); S=loadj(os.path.join(R,'summary.json'))
SHORT={'SARS-CoV-2 and COVID-19 Research':'SARS-CoV-2 and COVID-19','COVID-19 and Mental Health':'COVID-19 and mental health','Artificial Intelligence in Healthcare and Education':'AI in healthcare and education',
       'Microplastics and Plastic Pollution':'Microplastics','Energy, Environment, Economic Growth':'Energy, environment and growth','Advanced Sensor and Energy Harvesting Materials':'Energy-harvesting materials',
       'Advanced Battery Technologies Research':'Battery technologies','CAR-T cell therapy research':'CAR-T cell therapy','COVID-19 epidemiological studies':'COVID-19 epidemiology','Smart Agriculture and AI':'Smart agriculture and AI',
       'Ferroptosis and cancer prognosis':'Ferroptosis and cancer','Radiomics and Machine Learning in Medical Imaging':'Radiomics and machine learning','Additive Manufacturing and 3D Printing Technologies':'Additive manufacturing',
       'Advanced battery technologies research':'Battery technologies (II)','Extraction and Separation Processes':'Extraction and separation','Educational Reforms and Innovations':'Educational reforms','Network Security and Intrusion Detection':'Network security',
       'Vaccine Coverage and Hesitancy':'Vaccine coverage and hesitancy','Land Use and Ecosystem Services':'Land use and ecosystem services','Long-Term Effects of COVID-19':'Long COVID','Environmental Sustainability in Business':'Sustainability in business',
       'High Entropy Alloys Studies':'High-entropy alloys','Blockchain Technology Applications and Security':'Blockchain','Diet and metabolism studies':'Diet and metabolism'}
top=og.sort_values('n_peak_cs',ascending=False).head(24).reset_index(drop=True)
fig=plt.figure(figsize=(175*MM,92*MM)); gs=fig.add_gridspec(1,2,width_ratios=[1.15,1],left=0.235,right=0.99,top=0.93,bottom=0.13,wspace=0.38)
cmap=plt.get_cmap('RdBu_r')
def pc(p): return PALETTE['red_strong'] if p>=0.5 else (PALETTE['gold'] if p>=0.2 else PALETTE['blue_main'])
# A
ax=fig.add_subplot(gs[0,0]); ys=np.arange(len(top))
ax.barh(ys,100*top.p_crash,color=[pc(p) for p in top.p_crash],height=0.7)
for y,r in top.iterrows(): ax.text(100*r.p_crash+1.5,y,f'×{r.runup:.0f}' if r.runup>=10 else f'×{r.runup:.1f}',fontsize=5,va='center',ha='left',color=PALETTE['neutral_dark'])
ax.set_yticks(ys); ax.set_yticklabels([f'{SHORT.get(n,n)}, {y}' for n,y in zip(top.name,top.peak_year)],fontsize=5.8); ax.invert_yaxis(); ax.set_ylim(len(top)-0.4,-0.6); ax.set_xlim(0,115); ax.set_xticks([0,25,50,75,100])
ax.set_xlabel('Predicted probability of a crash (%)'); ax.text(114,-0.55,'run-up',fontsize=5,ha='right',va='bottom',color=PALETTE['neutral_dark'])
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=PALETTE['blue_main'],label='< 20%'),Patch(color=PALETTE['gold'],label='20–50%'),Patch(color=PALETTE['red_strong'],label='≥ 50%')],loc='center right',fontsize=5.5,handlelength=1,borderaxespad=0.2,title='predicted risk',title_fontsize=5.5); add_panel_label(ax,'A')
# B
ax=fig.add_subplot(gs[0,1]); sz=np.sqrt(og.n_peak_cs)/4
ax.scatter(og.runup,100*og.p_crash,s=sz,c=[pc(p) for p in og.p_crash],alpha=0.55,lw=0)
ax.set_xscale('log'); ax.set_xlim(1.3,150); ax.set_xticks([1.5,2,4,8,16,32,64]); ax.set_xticklabels(['1.5','2','4','8','16','32','64']); ax.xaxis.set_minor_formatter(plt.NullFormatter())
ax.set_xlabel('Run-up (peak share / trough share)'); ax.set_ylabel('Predicted probability of a crash (%)'); ax.set_ylim(-3,103); ax.axhline(50,color=PALETTE['neutral_light'],lw=0.8,zorder=0)
lab=[('COVID-19 and Mental Health','COVID-19 and\nmental health',(-58,-12)),('SARS-CoV-2 and COVID-19 Research','SARS-CoV-2 and\nCOVID-19',(-62,-4)),('Artificial Intelligence in Healthcare and Education','AI in healthcare',(4,4)),('Microplastics and Plastic Pollution','Microplastics',(4,-8))]
for nm,txt,off in lab:
    r=og[og.name==nm].iloc[0]; ax.annotate(txt,xy=(r.runup,100*r.p_crash),xytext=off,textcoords='offset points',fontsize=5.5,ha='left',va='center',color=PALETTE['neutral_dark'],arrowprops=dict(arrowstyle='-',color=PALETTE['neutral_mid'],lw=0.5,shrinkA=0,shrinkB=2))
ax.text(0.98,0.60,f'{len(og)} booms in progress\nmedian probability {100*og.p_crash.median():.0f}%\n{100*(og.p_crash>=0.5).mean():.0f}% above 50%',transform=ax.transAxes,fontsize=5.5,va='center',ha='right',color=PALETTE['neutral_dark'])
for n,lab_ in ((500,'500 papers'),(5000,'5,000')):
    ax.scatter([],[],s=np.sqrt(n)/4,c=PALETTE['neutral_mid'],alpha=0.55,lw=0,label=lab_)
ax.legend(loc='lower right',fontsize=5.5,handlelength=1,borderaxespad=0.2,labelspacing=0.8,title='papers at peak',title_fontsize=5.5); add_panel_label(ax,'B')
finalize(fig,os.path.join(os.path.dirname(os.path.abspath(__file__)),'out','fig5'),exemptions=[{'panels':['a','b'],'checks':['panel-width'],'reason':'ranked bar chart is wider than the scatter by design'}])
