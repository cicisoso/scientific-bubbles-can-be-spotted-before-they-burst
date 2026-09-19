"""Supplementary tables (LaTeX) -> sections/sm_tables.tex: S1 corpus and design; S2 largest evaluable booms; S3 pre-peak signatures;
S4 logistic models; S5 sensitivity; S6 largest booms in progress."""
import os, re, json, numpy as np, pandas as pd
P=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(P); R=os.path.join(ROOT,'results'); A=os.path.join(R,'analysis')
S=json.load(open(os.path.join(R,'summary.json'))); mac={m.group(1):m.group(2) for l in open(os.path.join(P,'macros.tex')) for m in [re.match(r'\\newcommand\{\\(\w+)\}\{(.*)\}',l.strip())] if m}
def esc(s): return str(s).replace('&','\\&').replace('%','\\%').replace('_','\\_')
def num(v,d=2):
    if v is None or (isinstance(v,float) and np.isnan(v)): return '--'
    s=f'{v:.{d}f}'
    if s.startswith('-') and s.lstrip('-').strip('0.')=='': s=s[1:]
    return s.replace('-','\\textminus ',1) if s.startswith('-') else s
def pct(v,d=0): return num(100*v,d)
out=[]
# S1 corpus and design
rows=[('OpenAlex snapshot','26 June 2026 (core corpus)'),('Works in the core corpus',mac['nWorksCoreM']),('Topics (OpenAlex classification)',mac['nTopics']),('Stable core (journal articles and reviews with a DOI), 1980--2025',mac['nCoreM']),
      ('Awards with a start year and a primary topic',mac['nAwards']),('Works flagged as retracted in OpenAlex',mac['nRetractedOA']),('Of which confirmed in the Retraction Watch database',mac['nRetractedRW']),
      ('Candidate peaks (stable-core series)',mac['nCandidates']),('Constant-source panel: minimum papers per journal in $t-5$ and $t+5$','20'),('Boom: run-up threshold and minimum panel papers at the peak','1.5; 200'),
      ('Crash: drawdown within five years of the peak','$\\ge 40\\%$'),('Booms (all)',mac['nBooms']),('Booms with five post-peak years (peaks $\\le 2020$)',mac['nEvaluable']),('Booms in progress (peaks $\\ge 2021$)',mac['nOngoing']),
      ('Median journals in a panel; median papers at the peak',f"{mac['nSourcesMedian']}; {mac['nPeakMedian']}"),('Null model replicates','20'),('Out-of-sample split','peaks $\\le 2008$ (training) vs 2009--2020 (test)')]
out.append("\\begin{table}[h]\\small\\centering\\caption{\\textbf{Corpus and design.}}\\begin{tabular}{lr}\\toprule Quantity & Value\\\\\\midrule\n"+"\n".join(f"{a} & {b}\\\\" for a,b in rows)+"\n\\bottomrule\\end{tabular}\\end{table}")
# S2 largest evaluable booms
ev=pd.read_parquet(os.path.join(R,'evaluable.parquet')); ev['crash']=ev.crash.astype(bool); DN={1:'Life',2:'Social',3:'Physical',4:'Health'}
t=ev.sort_values('n_peak_cs',ascending=False).head(40)
lines=[f"{esc(r['name'])[:52]} & {DN.get(int(r.domain),'')} & {int(r.peak_year)} & {int(r.n_peak_cs):,} & {num(r.runup,1)} & {pct(r.drawdown)} & {'yes' if r.crash else 'no'} & {pct(r.top3_share_inc)} & {pct(r.low_fwci_share_pre)}\\\\" for _,r in t.iterrows()]
out.append("\\begin{table}[h]\\scriptsize\\centering\\caption{\\textbf{The 40 largest evaluable booms.} Booms peaking in 2020 or earlier, by the number of papers in the constant-source panel at the peak. Run-up, peak share divided by the minimum of the preceding five years; drawdown, largest fall within five years; venue, share of the run-up carried by the three journals that added the most papers; low impact, pre-peak share of papers with FWCI below 0.25. The full catalogue of "+mac['nBooms']+" booms is provided as source data.}\\begin{tabular}{llrrrrrrr}\\toprule Topic & Domain & Peak & Papers & Run-up & Drawdown (\\%) & Crash & Venue (\\%) & Low impact (\\%)\\\\\\midrule\n"+"\n".join(lines)+"\n\\bottomrule\\end{tabular}\\end{table}")
# S3 signatures
sig=pd.DataFrame(S['signatures']); LAB={'accel':'Growth acceleration','runup':'Run-up','low_fwci_share_pre':'Share of papers with FWCI $<$ 0.25','fwci_log':'log mean FWCI','uncited_share_pre':'Share of papers never cited','newcomer_share_pre':'Share of authors new to the topic','new_scientist_share_pre':'Share of authors new to science',
     'within_topic_share_pre':'Share of references within the topic','awards_log':'log(1 + grants per 100 papers)','review_share_pre':'Share of reviews','top_country_share_pre':'Share of the largest country','top_source_share_pre':'Share of the largest journal','top3_share_inc':'Run-up carried by the three largest venues','team_mean_pre':'Authors per paper','en_share_pre':'Share of papers in English','log_npeak':'log papers at the peak'}
def pf(p): return '$<$0.001' if p<0.001 else num(p,3)
lines=[f"{LAB.get(r['var'],r['var'])} & {num(r.median_crash,3)} & {num(r.median_soft,3)} & {num(r.mean_crash,3)} & {num(r.mean_soft,3)} & {pf(r.p)} & {num(r.auc,2)}\\\\" for _,r in sig.iterrows()]
out.append("\\begin{table}[h]\\small\\centering\\caption{\\textbf{Pre-peak signatures of booms that crashed and booms that did not.} Averages over the three years before the peak ("+mac['nCrash']+" crash and "+mac['nSoft']+" soft-landing booms); $p$ from Mann--Whitney tests; AUC, area under the receiver operating characteristic curve for the crash.}\\begin{tabular}{lrrrrrr}\\toprule Signature & \\multicolumn{2}{c}{Median} & \\multicolumn{2}{c}{Mean} & $p$ & AUC\\\\ & Crash & Soft & Crash & Soft & & \\\\\\midrule\n"+"\n".join(lines)+"\n\\bottomrule\\end{tabular}\\end{table}")
# S4 logistic models
lg=pd.DataFrame(S['logit']); order=[v for v in LAB if v in set(lg['var'])]
def cell(spec,v):
    r=lg[(lg.spec==spec)&(lg['var']==v)]
    return f"{num(r.or_per_sd.iloc[0],2)} [{num(r.lo.iloc[0],2)}, {num(r.hi.iloc[0],2)}]" if len(r) else '--'
lines=[f"{LAB[v]} & {cell('univariate',v)} & {cell('multivariate',v)} & {cell('multivariate_all',v)}\\\\" for v in order]
out.append("\\begin{table}[h]\\small\\centering\\caption{\\textbf{Logistic models of the crash.} Odds ratios per standard deviation with 95\\% confidence intervals; all models include decade and domain fixed effects. Univariate: one signature at a time. Joint: the main model (in-sample AUC "+mac['insampleAuc']+", pseudo-$R^2$ "+mac['pseudoR']+"). All: every signature.}\\begin{tabular}{lrrr}\\toprule Signature & Univariate & Joint & All\\\\\\midrule\n"+"\n".join(lines)+"\n\\bottomrule\\end{tabular}\\end{table}")
# S5 sensitivity
sens=pd.DataFrame(S['sensitivity']); REN={'constant-source, run-up>=1.5, >=200 papers (main)':'Main definition (constant-source panel, run-up $\\ge$ 1.5, $\\ge$ 200 papers)','constant-source, run-up>=2, >=300 papers':'Run-up $\\ge$ 2 and $\\ge$ 300 papers','stable-core share, run-up>=2 (no constant-source panel)':'Stable-core series without the constant-source panel, run-up $\\ge$ 2',
     'excluding topics with < 50% English papers':'Excluding topics with fewer than 50\\% English papers','excluding top-source share > 30% at the peak':'Excluding booms whose largest journal had more than 30\\% of papers at the peak','peaks 1990-2015 only':'Peaks between 1990 and 2015','excluding booms led by conference-proceedings serials':'Excluding booms led by conference-proceedings serials',
     'diffuse booms only (top-3 venues < 50% of the run-up)':'Diffuse booms only (three largest venues carried less than 50\\% of the run-up)','venue-concentrated booms only (top-3 venues >= 50% of the run-up)':'Concentrated booms only (three largest venues carried at least 50\\% of the run-up)','fixed source weights (booms that remain booms; crash measured on the fixed-weight index)':'Fixed-weight index (booms that remain booms; crash on the same index)'}
lines=[f"{REN.get(r.definition,esc(r.definition))} & {int(100*r.crash_threshold)}\\% & {int(r.n)} & {pct(r.rate,1)}\\\\" for _,r in sens.iterrows()]
out.append("\\begin{table}[h]\\small\\centering\\caption{\\textbf{Sensitivity of the crash rate.} Crash rate under alternative definitions and restrictions.}\\begin{tabular}{p{9.5cm}rrr}\\toprule Definition & Threshold & Booms & Crash rate (\\%)\\\\\\midrule\n"+"\n".join(lines)+"\n\\bottomrule\\end{tabular}\\end{table}")
# S6 booms in progress
og=pd.read_csv(os.path.join(A,'ongoing.csv')).sort_values('n_peak_cs',ascending=False).head(30)
lines=[f"{esc(r['name'])[:52]} & {int(r.peak_year)} & {int(r.n_peak_cs):,} & {num(r.runup,1)} & {pct(r.top3_share_inc)} & {pct(r.low_fwci_share_pre)} & {pct(r.p_crash)}\\\\" for _,r in og.iterrows()]
out.append("\\begin{table}[h]\\scriptsize\\centering\\caption{\\textbf{The 30 largest booms in progress.} Booms peaking in 2021 or later, by papers in the constant-source panel at the peak, with the crash probability predicted by the joint model fitted to all evaluable booms. Columns as in \\tabS{2}.}\\begin{tabular}{lrrrrrr}\\toprule Topic & Peak & Papers & Run-up & Venue (\\%) & Low impact (\\%) & Predicted crash (\\%)\\\\\\midrule\n"+"\n".join(lines)+"\n\\bottomrule\\end{tabular}\\end{table}")
open(os.path.join(P,'sections','sm_tables.tex'),'w').write("\\section*{Supplementary Tables}\n\n"+"\n\n\\clearpage\n".join(out)+"\n"); print('wrote',len(out),'tables')
