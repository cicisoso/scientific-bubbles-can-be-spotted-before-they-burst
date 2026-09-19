"""paper/macros.tex from results/summary.json, results/*.parquet and data/build. Digit-free macro names; missing values -> [pending]."""
import json, os, re, numpy as np, pandas as pd
P=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(P); R=os.path.join(ROOT,'results'); A=os.path.join(R,'analysis'); B=os.path.join(ROOT,'data','build')
S=json.load(open(os.path.join(R,'summary.json'))); m={}
def fx(v,d=1):
    s=f'{v:.{d}f}'
    if s.startswith('-') and s.lstrip('-').strip('0.')=='': s=s[1:]
    return s.replace('-','\\textminus ',1) if s.startswith('-') else s
def pct(v,d=0): return fx(100*v,d)
def big(x): return f'{int(round(float(x))):,}'
ev=pd.read_parquet(os.path.join(R,'evaluable.parquet')); ev['crash']=ev.crash.astype(bool); E=pd.read_parquet(os.path.join(R,'episodes_cs.parquet'))
# corpus
m['nWorksCoreM']='318 million'; m['nTopics']='4,516'
so=pd.read_parquet(os.path.join(B,'topic_year_sources.parquet')); so=so[(so.year>=1980)&(so.year<=2025)]
m['nCoreM']=f"{so.n_core.sum()/1e6:.0f} million"; m['nArtM']=f"{so.n_art.sum()/1e6:.0f} million"
rf=pd.read_parquet(os.path.join(B,'retracted_flags.parquet')); m['nRetractedOA']=big(len(rf)); m['nRetractedRW']=big(rf.rw.sum()); m['nAwards']='1.1 million'
# booms
m['nBooms']=str(S['n_booms']); m['nBoomTopics']=str(S['n_topics']); m['nEvaluable']=str(S['n_evaluable']); m['nOngoing']=str(S['n_ongoing']); m['nCrash']=str(S['n_crash']); m['nSoft']=str(S['n_evaluable']-S['n_crash'])
m['crashRate']=pct(S['crash_rate']); m['crashLo']=pct(S['crash_ci'][0]); m['crashHi']=pct(S['crash_ci'][1])
m['ddMedian']=pct(S['drawdown_median']); m['ddQLo']=pct(ev.drawdown.quantile(.25)); m['ddQHi']=pct(ev.drawdown.quantile(.75)); m['shareDdFifty']=pct(S['share_dd50']); m['shareDdTwenty']=pct(S['share_dd20'])
m['shareRevert']=pct(S['share_revert']); m['netGainMedian']=fx(S['net_gain_median'],2); m['netGainCrash']=fx(S['net_gain_median_crash'],2); m['netGainSoft']=fx(S['net_gain_median_soft'],2)
m['yearsToMin']=str(int(S['years_to_min_median'])); m['runupMedian']=fx(ev.runup.median(),1); m['shareRunupTwo']=pct((ev.runup>=2).mean()); m['shareRunupThree']=pct((ev.runup>=3).mean())
m['nPeakMedian']=big(ev.n_peak_cs.median()); m['nSourcesMedian']=big(ev.n_sources_cs.median()); m['nCandidates']='2,102'
for d,k in (('1980','Eighties'),('1990','Nineties'),('2000','Noughties'),('2010','Tens'),('2020','Twenties')):
    b=S['by_decade'][d]; m['crash'+k]=pct(b['rate']); m['n'+k]=str(b['n'])
for d in ('Life','Social','Physical','Health'):
    b=S['by_domain'][d]; m['crash'+d]=pct(b['rate']); m['n'+d]=str(b['n']); m['crash'+d+'Lo']=pct(b['ci'][0]); m['crash'+d+'Hi']=pct(b['ci'][1])
for c,k in (('1.5-2','One'),('2-3','Two'),('>=3','Three')):
    r=[x for x in S['dose'] if x['cls']==c][0]; m['dose'+k]=pct(r['rate']); m['dose'+k+'N']=str(r['n']); m['dose'+k+'Lo']=pct(r['lo']); m['dose'+k+'Hi']=pct(r['hi']); m['dose'+k+'Revert']=pct(r['revert'])
m['rhoRunupDd']=fx(S['spearman_runup_drawdown'],2)
for r in S['null']:
    k={'1.2-1.5':'Weak','1.5-2':'One','2-3':'Two','>=3':'Three'}[r['class']]
    m['nullObs'+k]=pct(r['crash_obs']); m['nullNull'+k]=pct(r['crash_null']); m['nullN'+k]=big(r['n_obs']); m['nullRevObs'+k]=pct(r['revert_obs']); m['nullRevNull'+k]=pct(r['revert_null']); m['nullLossObs'+k]=pct(r['netloss_obs']); m['nullLossNull'+k]=pct(r['netloss_null'])
# sensitivity
for r in S['sensitivity']:
    d=r['definition']; thr=r['crash_threshold']
    key={('constant-source, run-up>=1.5, >=200 papers (main)',0.3):'sensMainThirty',('constant-source, run-up>=1.5, >=200 papers (main)',0.5):'sensMainFifty',('constant-source, run-up>=2, >=300 papers',0.4):'sensStrict',
         ('stable-core share, run-up>=2 (no constant-source panel)',0.4):'sensStable',('excluding topics with < 50% English papers',0.4):'sensEnglish',('excluding top-source share > 30% at the peak',0.4):'sensTopSource',('peaks 1990-2015 only',0.4):'sensMid',
         ('excluding booms led by conference-proceedings serials',0.4):'sensNoProc',('diffuse booms only (top-3 venues < 50% of the run-up)',0.4):'sensDiffuse',('venue-concentrated booms only (top-3 venues >= 50% of the run-up)',0.4):'sensConc',
         ('fixed source weights (booms that remain booms; crash measured on the fixed-weight index)',0.4):'sensFixed'}.get((d,thr))
    if key: m[key]=pct(r['rate']); m[key+'N']=str(r['n'])
fw=S['fixed_weight']; m['fwN']=str(fw['n_boom_fw']); m['fwCrash']=pct(fw['crash_rate_fw']); m['fwCrashMain']=pct(fw['crash_rate_main_among']); m['fwRhoRunup']=fx(fw['spearman_runup'],2); m['fwRhoDd']=fx(fw['spearman_drawdown'],2)
pl=S['proc_led']; m['procN']=str(pl['n']); m['procCrash']=pct(pl['crash']); m['ttpN']=str(pl['n_ttp']); m['ttpCrash']=pct(pl['crash_ttp'])
vc=S['venue_conc']; m['concN']=str(vc['n_conc']); m['concCrash']=pct(vc['crash_conc']); m['concLo']=pct(vc['ci_conc'][0]); m['concHi']=pct(vc['ci_conc'][1]); m['diffN']=str(vc['n_diff']); m['diffCrash']=pct(vc['crash_diff']); m['diffLo']=pct(vc['ci_diff'][0]); m['diffHi']=pct(vc['ci_diff'][1])
# signatures (medians)
sig={s['var']:s for s in S['signatures']}
def med(v,fmt,cr=True): return fmt(sig[v]['median_crash'] if cr else sig[v]['median_soft'])
m['sigLowFwciCrash']=pct(sig['low_fwci_share_pre']['median_crash']); m['sigLowFwciSoft']=pct(sig['low_fwci_share_pre']['median_soft'])
m['sigUncitedCrash']=pct(sig['uncited_share_pre']['median_crash']); m['sigUncitedSoft']=pct(sig['uncited_share_pre']['median_soft'])
m['sigFwciCrash']=fx(np.exp(sig['fwci_log']['median_crash']),2); m['sigFwciSoft']=fx(np.exp(sig['fwci_log']['median_soft']),2)
m['sigAwardsCrash']=fx(ev[ev.crash].awards_per_100_pre.median(),2); m['sigAwardsSoft']=fx(ev[~ev.crash].awards_per_100_pre.median(),2); m['sigAnyAwardCrash']=pct((ev[ev.crash].awards_per_100_pre>0).mean()); m['sigAnyAwardSoft']=pct((ev[~ev.crash].awards_per_100_pre>0).mean())
m['sigReviewCrash']=pct(sig['review_share_pre']['median_crash'],1); m['sigReviewSoft']=pct(sig['review_share_pre']['median_soft'],1)
m['sigWithinCrash']=pct(sig['within_topic_share_pre']['median_crash']); m['sigWithinSoft']=pct(sig['within_topic_share_pre']['median_soft'])
m['sigTeamCrash']=fx(sig['team_mean_pre']['median_crash'],1); m['sigTeamSoft']=fx(sig['team_mean_pre']['median_soft'],1)
m['sigNewcomerCrash']=pct(sig['newcomer_share_pre']['median_crash']); m['sigNewcomerSoft']=pct(sig['newcomer_share_pre']['median_soft'])
m['sigNewSciCrash']=pct(sig['new_scientist_share_pre']['median_crash']); m['sigNewSciSoft']=pct(sig['new_scientist_share_pre']['median_soft'])
m['sigAccelCrash']=fx(sig['accel']['median_crash'],3); m['sigAccelSoft']=fx(sig['accel']['median_soft'],3); m['sigRunupCrash']=fx(sig['runup']['median_crash'],1); m['sigRunupSoft']=fx(sig['runup']['median_soft'],1)
m['sigVenueCrash']=pct(sig['top3_share_inc']['median_crash']); m['sigVenueSoft']=pct(sig['top3_share_inc']['median_soft']); m['sigVenueAuc']=fx(sig['top3_share_inc']['auc'],2)
m['sigTopCountryCrash']=pct(sig['top_country_share_pre']['median_crash']); m['sigTopCountrySoft']=pct(sig['top_country_share_pre']['median_soft'])
m['sigLowFwciAuc']=fx(sig['low_fwci_share_pre']['auc'],2); m['sigRunupAuc']=fx(sig['runup']['auc'],2); m['sigAccelAuc']=fx(sig['accel']['auc'],2)
# logit
lg=pd.DataFrame(S['logit'])
def orr(spec,v,k):
    r=lg[(lg.spec==spec)&(lg['var']==v)]
    if len(r):
        d=1 if v=='runup' else 2; m[k]=fx(r.or_per_sd.iloc[0],d); m[k+'Lo']=fx(r.lo.iloc[0],d); m[k+'Hi']=fx(r.hi.iloc[0],d); m[k+'P']=('$<$0.001' if r.p.iloc[0]<0.001 else fx(r.p.iloc[0],3))
for v,k in (('top3_share_inc','orVenue'),('accel','orAccel'),('runup','orRunup'),('low_fwci_share_pre','orLowFwci'),('awards_log','orAwards'),('newcomer_share_pre','orNewcomer'),('within_topic_share_pre','orWithin'),('review_share_pre','orReview'),('top_country_share_pre','orTopCountry'),('log_npeak','orSize')):
    orr('multivariate',v,k); orr('univariate',v,'u'+k[0].upper()+k[1:])
for v,k in (('fwci_log','uOrFwci'),('uncited_share_pre','uOrUncited'),('team_mean_pre','uOrTeam'),('new_scientist_share_pre','uOrNewSci'),('en_share_pre','uOrEnglish'),('top_source_share_pre','uOrTopSource')): orr('univariate',v,k)
m['insampleAuc']=fx(S['multivariate_auc_insample'],2); m['pseudoR']=fx(S['multivariate_pseudo_r2'],2)
m['oosAuc']=fx(S['oos_auc'],2); m['oosAucRunup']=fx(S['oos_auc_runup_only'],2); m['oosAucQuality']=fx(S['oos_auc_quality'],2); m['oosAucVenue']=fx(S['oos_auc_venue_only'],2); m['oosAucNoVenue']=fx(S['oos_auc_no_venue'],2); m['oosAucNoProc']=fx(S['oos_auc_excl_proc'],2)
m['oosTrain']=str(S['oos_n_train']); m['oosTest']=str(S['oos_n_test']); m['oosTrainNoProc']=str(S['oos_n_excl_proc'][0]); m['oosTestNoProc']=str(S['oos_n_excl_proc'][1])
cal=S['oos_calibration']
for k,kk in (('low','Low'),('mid','Mid'),('high','High')): m['cal'+kk+'Obs']=pct(cal[k]['obs']); m['cal'+kk+'Pred']=pct(cal[k]['pred']); m['cal'+kk+'N']=str(cal[k]['n'])
ols=S['ols_drawdown']
for v,k in (('top3_share_inc','olsVenue'),('low_fwci_share_pre','olsLowFwci'),('accel','olsAccel'),('top_country_share_pre','olsTopCountry'),('runup','olsRunup')):
    if v in ols: m[k]=fx(100*ols[v]['coef'],1); m[k+'Lo']=fx(100*ols[v]['lo'],1); m[k+'Hi']=fx(100*ols[v]['hi'],1)
# quadrant crash rates (venue concentration terciles x low-impact halves), as in Fig. 3D
ev['vq']=pd.qcut(ev.top3_share_inc,3,labels=['d','m','c']); ev['lq']=pd.qcut(ev.low_fwci_share_pre,2,labels=['lo','hi'])
q=ev.groupby(['vq','lq'],observed=True).crash.mean(); m['quadDiffuseGood']=pct(q[('d','lo')]); m['quadConcBad']=pct(q[('c','hi')]); m['quadDiffuseBad']=pct(q[('d','hi')]); m['quadConcGood']=pct(q[('c','lo')])
# retractions
for src,pre in (('sir','sir'),('sir_rw','rw')):
    for w in ('boom_all','pre_all','post_all','boom_crash','boom_soft','pre_crash','pre_soft','post_crash','post_soft'):
        r=S[src].get(w)
        if r is None: continue
        k=pre+''.join(x.capitalize() for x in w.split('_')); m[k]=fx(r[0],1); m[k+'Lo']=fx(r[1],1); m[k+'Hi']=fx(r[2],1); m[k+'Obs']=big(r[3]); m[k+'Exp']=big(r[4])
rt=S['retract']; m['rawPre']=fx(rt['pre_per10k'],1); m['rawBoom']=fx(rt['boom_per10k'],1); m['rawPost']=fx(rt['post_per10k'],1); m['rawBoomCrash']=fx(rt['boom_crash_per10k'],1); m['rawBoomSoft']=fx(rt['boom_soft_per10k'],1)
m['rrBoomPre']=fx(rt['rr_boom_vs_pre'][0],1); m['rrCrashSoft']=fx(rt['rr_crash_vs_soft'][0],1); m['rrCrashSoftLo']=fx(rt['rr_crash_vs_soft'][1],1); m['rrCrashSoftHi']=fx(rt['rr_crash_vs_soft'][2],1)
# aftermath
m['attCrash']=fx(S['attention_ratio_median_crash'],2); m['attSoft']=fx(S['attention_ratio_median_soft'],2); m['attUpCrash']=pct(S['attention_share_up_crash']); m['attUpSoft']=pct((ev[~ev.crash].attention_ratio_t5>1).mean())
m['aboveCrash']=pct(S['level_above_pre_crash']); m['aboveSoft']=pct(S['level_above_pre_soft'])
en={(r['grp'],bool(r['crash'])):r for r in S['entrants']}
for (g,c),r in en.items():
    k=('ent' if g=='entrant' else 'inc')+('Crash' if c else 'Soft'); m[k+'Pub']=pct(r['still_publishing_t5'],1); m[k+'Topic']=pct(r['still_in_topic_t5'],1); m[k+'Moved']=pct(r['moved_t5'],1); m[k+'NewSci']=pct(r['share_new_scientists'])
enp=pd.read_parquet(os.path.join(R,'entrants.parquet')); enp=enp[enp.evaluable]; m['nEntrantsM']=f"{enp[enp.grp=='entrant'].n.sum()/1e6:.1f} million"; m['nIncumbentsK']=big(enp[enp.grp=='incumbent'].n.sum()); m['nIncumbentsM']=f"{enp[enp.grp=='incumbent'].n.sum()/1e6:.1f} million"
# ongoing
og=pd.read_csv(os.path.join(A,'ongoing.csv')); m['ongoingMedianP']=pct(og.p_crash.median()); m['ongoingAboveHalf']=pct((og.p_crash>=0.5).mean()); m['ongoingBelowFifth']=pct((og.p_crash<0.2).mean()); m['ongoingCovidN']=str(int(og.name.str.contains('COVID|SARS',case=False).sum()))
def op(nm,k):
    r=og[og.name==nm]
    if len(r): m[k]=pct(r.p_crash.iloc[0]); m[k+'Runup']=fx(r.runup.iloc[0],0 if r.runup.iloc[0]>=10 else 1); m[k+'N']=big(r.n_peak_cs.iloc[0]); m[k+'Year']=str(int(r.peak_year.iloc[0]))
for nm,k in (('SARS-CoV-2 and COVID-19 Research','ogCovid'),('COVID-19 and Mental Health','ogCovidMental'),('Long-Term Effects of COVID-19','ogLongCovid'),('Artificial Intelligence in Healthcare and Education','ogAI'),('Microplastics and Plastic Pollution','ogMicroplastics'),('Advanced Battery Technologies Research','ogBattery'),('CAR-T cell therapy research','ogCart'),('Ferroptosis and cancer prognosis','ogFerroptosis'),('Blockchain Technology Applications and Security','ogBlockchain'),('Quantum Computing Algorithms and Architecture','ogQuantum'),('Educational Reforms and Innovations','ogEducation'),('COVID-19 epidemiological studies','ogCovidEpi')): op(nm,k)
# examples for Fig. 1 / text
def ex(nm,y,k):
    r=E[(E.name==nm)&(E.peak_year==y)]
    if len(r): r=r.iloc[0]; m[k+'Runup']=fx(r.runup,0 if r.runup>=10 else 1); m[k+'Dd']=pct(r.drawdown) if not pd.isna(r.drawdown) else '[pending]'; m[k+'N']=big(r.n_peak_cs)
for nm,y,k in (('COVID-19 Clinical Research Studies',2020,'exCovid'),('Cold Fusion and Nuclear Reactions',1990,'exColdFusion'),('Fullerene Chemistry and Applications',1993,'exFullerene'),('Graphene research and applications',2014,'exGraphene'),('SARS-CoV-2 and COVID-19 Research',2004,'exSars'),('Iron-based superconductors research',2009,'exIron'),('Superconductivity in MgB2 and Alloys',2003,'exMgb'),('Helicobacter pylori-related gastroenterology studies',1998,'exHelico')): ex(nm,y,k)
m['nTwoBoomTopics']=str(int((E.groupby('topic').size()>=2).sum()))
# SM counts
m['smFigCount']='8'; m['smTabCount']='6'
with open(os.path.join(P,'macros.tex'),'w') as f:
    for k,v in m.items():
        assert re.fullmatch(r'[A-Za-z]+',k), k
        f.write(f'\\newcommand{{\\{k}}}{{{v}}}\n')
print(len(m),'macros;', [k for k,v in m.items() if v=='[pending]'])
