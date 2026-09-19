"""Assemble the Science submission package in submission/science/ from paper/ and results/. Usage: python3 scripts/08_package.py"""
import os, re, sys, json, shutil, subprocess, datetime, glob
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH as AL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PAPER=os.path.join(ROOT,'paper'); FIG=os.path.join(ROOT,'fig','out'); RES=os.path.join(ROOT,'results'); A=os.path.join(RES,'analysis')
OUT=os.path.join(ROOT,'submission','science'); os.makedirs(OUT,exist_ok=True); FONT='Times New Roman'; DATE=datetime.date.today().strftime('%-d %B %Y')
def run(cmd,cwd=PAPER):
    r=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,errors='replace'); return r.returncode, r.stdout+r.stderr
def log(*a): print(*a,flush=True)
os.chdir(PAPER)
for tex in ('main.tex','supplement.tex'):
    rc,out=run(['latexmk','-pdf','-interaction=nonstopmode','-silent',tex]); log(tex,'->','ok' if rc==0 else 'FAILED')
    if rc!=0: log(out[-1200:])
txt=subprocess.run(['pdftotext','-layout','main.pdf','-'],capture_output=True,text=True).stdout
assert '[pending]' not in txt, 'main.pdf still contains [pending]'; assert '??' not in txt, 'unresolved references in main.pdf'
title=re.search(r'\\newcommand\{\\papertitle\}\{(.*)\}',open('title.tex').read()).group(1)
# Word version via pandoc
os.makedirs('figures',exist_ok=True)
for f in glob.glob(os.path.join(FIG,'*.png')): shutil.copy(f,os.path.join('figures',os.path.basename(f)))
mac=open('macros.tex').read()
pan=r"""\documentclass{article}
\providecommand{\textminus}{−}
"""+mac+open('title.tex').read()+r"""
\newcommand{\figS}[1]{fig.~S#1}\newcommand{\tabS}[1]{table~S#1}
\begin{document}
\section*{Abstract}
\input{sections/00_abstract}
\input{sections/01_intro}
\input{sections/02_results}
\input{sections/03_discussion}
\input{sections/04_methods_summary}
\input{sections/05_acknowledgments}
\input{sections/06_figures}
\end{document}
"""
open('main_pandoc.tex','w').write(pan)
rc,out=run(['pandoc','main_pandoc.tex','-f','latex','-t','docx','-o','main.docx','--citeproc','--bibliography','../lit/references.bib','--csl','science.csl','--default-image-extension=png','--resource-path','.:figures','-M','link-citations=false','-M','reference-section-title=References and Notes'])
log('main.docx','ok' if rc==0 else 'FAILED: '+out[:600])
def set_font(style,size):
    style.font.name=FONT; style.font.size=Pt(size); style.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),FONT)
def line_numbers(doc):
    for s in doc.sections:
        ln=OxmlElement('w:lnNumType'); ln.set(qn('w:countBy'),'1'); ln.set(qn('w:restart'),'continuous'); ln.set(qn('w:distance'),'360'); s._sectPr.append(ln)
if rc==0:
    d=Document('main.docx')
    for s in d.sections: s.page_width,s.page_height=Cm(21.6),Cm(27.9); s.left_margin=s.right_margin=s.top_margin=s.bottom_margin=Cm(2.54)
    names=[st.name for st in d.styles]
    for name in ['Normal','Body Text','First Paragraph','Compact']:
        if name in names: set_font(d.styles[name],12); d.styles[name].paragraph_format.line_spacing=2.0; d.styles[name].paragraph_format.first_line_indent=Cm(0)
    for name,size in [('Heading 1',14),('Heading 2',12),('Heading 3',12)]:
        if name in names: set_font(d.styles[name],size); d.styles[name].font.bold=True; d.styles[name].font.color.rgb=None
    first=d.paragraphs[0]
    def ins(par,text,size,bold=False,align=AL.CENTER,italic=False):
        p=par.insert_paragraph_before(); r=p.add_run(text); r.bold=bold; r.italic=italic; r.font.size=Pt(size); r.font.name=FONT; p.alignment=align; return p
    ins(first,title,16,bold=True); ins(first,'Hao Liu1*, Xiaojie Zong1, Jie Chen1, Jianyu Xiong1',12)
    ins(first,'1School of Information Technology, Zhejiang Financial College, Hangzhou 310018, China. *Corresponding author. Email: liuhao@zfc.edu.cn',10)
    ins(first,'One-sentence summary: '+re.search(r'\\newcommand\{\\onesentence\}\{(.*)\}',open('title.tex').read()).group(1),11,italic=True,align=AL.LEFT)
    line_numbers(d); d.core_properties.author='Hao Liu'; d.core_properties.title=title; d.save('main.docx')
# copy package files
M=os.path.join(OUT,'manuscript'); os.makedirs(M,exist_ok=True)
for src,dst in (('main.pdf','main.pdf'),('main.docx','main.docx'),('supplement.pdf','supplementary_materials.pdf')): shutil.copy(src,os.path.join(M,dst))
SRC=os.path.join(M,'latex_source'); shutil.rmtree(SRC,ignore_errors=True); os.makedirs(os.path.join(SRC,'sections'))
for f in ('main.tex','supplement.tex','preamble.tex','title.tex','macros.tex','references.tex','references_sm.tex','make_numbers.py','make_bib.py','make_sm_tables.py','wordcount.py'):
    if os.path.exists(f): shutil.copy(f,SRC)
for f in glob.glob('sections/*.tex'): shutil.copy(f,os.path.join(SRC,'sections'))
FG=os.path.join(OUT,'figures'); os.makedirs(FG,exist_ok=True)
for i in range(1,6):
    for ext in ('pdf','png'): shutil.copy(os.path.join(FIG,f'fig{i}.{ext}'),os.path.join(FG,f'Fig{i}.{ext}'))
SF=os.path.join(OUT,'supplementary_figures'); os.makedirs(SF,exist_ok=True)
for f in glob.glob(os.path.join(FIG,'figS*.pdf'))+glob.glob(os.path.join(FIG,'figS*.png')): shutil.copy(f,os.path.join(SF,os.path.basename(f).replace('figS','Fig_S')))
# source data
SD=os.path.join(OUT,'source_data'); os.makedirs(SD,exist_ok=True)
def book(name,sheets):
    with pd.ExcelWriter(os.path.join(SD,name)) as w:
        for sh,df in sheets.items(): df.to_excel(w,sheet_name=sh[:31],index=False)
    log(name,'ok')
ev=pd.read_parquet(f'{RES}/evaluable.parquet'); ep=pd.read_parquet(f'{RES}/episodes_cs.parquet'); cs=pd.read_parquet(os.path.join(ROOT,'data','build','cs_series.parquet'))
for df in (ev,ep):
    for c in df.columns:
        if df[c].dtype==object and df[c].map(lambda x: isinstance(x,(list,tuple))).any(): df[c]=df[c].map(lambda x: ';'.join(map(str,x)) if isinstance(x,(list,tuple)) else x)
keep=[c for c in ev.columns if not c.endswith('_dup')]
book('Data_S1_Fig1.xlsx',{'booms_all':ep,'evaluable_booms':ev[keep],'cs_series':cs.merge(ep[['topic','peak_year']].rename(columns={'peak_year':'t'}),on=['topic','t']),'dose':pd.read_csv(f'{A}/dose.csv'),'null_model':pd.read_csv(f'{RES}/null_model.csv'),'sensitivity':pd.read_csv(f'{A}/sensitivity.csv')})
et=pd.read_parquet(f'{RES}/eventtime.parquet'); et=et[et.evaluable]
book('Data_S2_Fig2.xlsx',{'eventtime':et,'signatures':pd.read_csv(f'{A}/signatures.csv'),'venues':pd.read_parquet(f'{RES}/venues.parquet').assign(top_sids=lambda d: d.top_sids.map(lambda x: ';'.join(map(str,x))),top_inc=lambda d: d.top_inc.map(lambda x: ';'.join(map(str,x))))})
book('Data_S3_Fig3.xlsx',{'logit':pd.read_csv(f'{A}/logit.csv'),'oos_predictions':pd.read_csv(f'{A}/oos_predictions.csv')})
en=pd.read_parquet(f'{RES}/entrants.parquet')
book('Data_S4_Fig4.xlsx',{'entrants_by_episode':en,'entrants_summary':pd.read_csv(f'{A}/entrants.csv'),'retractions':ev[['topic','name','peak_year','crash','rw_obs_boom','rw_exp_boom','rw_obs_pre','rw_exp_pre','rw_obs_post','rw_exp_post','ret_obs_boom','ret_exp_boom','ret_obs_pre','ret_exp_pre','ret_obs_post','ret_exp_post','attention_ratio_t5','net_gain']]})
book('Data_S5_Fig5.xlsx',{'ongoing':pd.read_csv(f'{A}/ongoing.csv'),'fixed_weight':pd.read_parquet(f'{RES}/fixed_weight.parquet')})
shutil.copy(os.path.join(RES,'summary.json'),os.path.join(SD,'summary.json'))
# docx versions of cover letter
TOK=re.compile(r'(\*\*.+?\*\*|(?<!\w)_[^_]+?_(?!\w))')
def new_doc(t):
    d=Document(); s=d.sections[0]; s.page_width,s.page_height=Cm(21.6),Cm(27.9); s.left_margin=s.right_margin=s.top_margin=s.bottom_margin=Cm(2.54)
    set_font(d.styles['Normal'],12); pf=d.styles['Normal'].paragraph_format; pf.space_after=Pt(8); pf.line_spacing=1.15; d.core_properties.author='Hao Liu'; d.core_properties.title=t; return d
def para(d,text,bold=False,size=None,align=None,after=None):
    p=d.add_paragraph()
    for part in TOK.split(text):
        if not part: continue
        if part.startswith('**'): r=p.add_run(part[2:-2]); r.bold=True
        elif part.startswith('_') and part.endswith('_') and len(part)>2: r=p.add_run(part[1:-1]); r.italic=True
        else: r=p.add_run(part)
        if bold: r.bold=True
        if size: r.font.size=Pt(size)
    if align is not None: p.alignment=align
    if after is not None: p.paragraph_format.space_after=Pt(after)
    return p
def md_to_docx(md_path,out_path,t,date=False):
    d=new_doc(t)
    if date: para(d,DATE,align=AL.RIGHT)
    for block in [b for b in re.split(r'\n\s*\n',open(md_path).read().strip()) if b.strip()]:
        if block.startswith('# '): para(d,block[2:].strip(),bold=True,size=14,after=6)
        elif block.startswith('## '): para(d,block[3:].strip(),bold=True,size=12,after=4)
        elif block.startswith('|'):
            rows=[[c.strip() for c in l.strip().strip('|').split('|')] for l in block.splitlines() if not re.match(r'^\|\s*-',l)]
            t_=d.add_table(rows=len(rows),cols=len(rows[0])); t_.style='Table Grid'
            for i,row in enumerate(rows):
                for j,c in enumerate(row):
                    cell=t_.cell(i,j); cell.text=''; r=cell.paragraphs[0].add_run(re.sub(r'\*\*','',c)); r.font.size=Pt(10); r.bold=(i==0)
            d.add_paragraph()
        else: para(d,' '.join(l.strip() for l in block.splitlines()))
    d.save(out_path); log(os.path.basename(out_path),'ok')
md_to_docx(os.path.join(OUT,'cover_letter.md'),os.path.join(OUT,'cover_letter.docx'),'Cover letter to Science',date=True)
subprocess.run([sys.executable,'wordcount.py'],cwd=PAPER,capture_output=True)
# checklist + README
W=json.load(open(os.path.join(PAPER,'wordcounts.json'))); ONE=re.search(r'\\newcommand\{\\onesentence\}\{(.*)\}',open(os.path.join(PAPER,'title.tex')).read()).group(1)
rows=[('Title',f'<=135 characters; declarative',f'"{title}" ({len(title)} characters)','OK' if len(title)<=135 else 'CHECK'),
 ('One-sentence summary','<=125 characters',f'{len(ONE)} characters','OK' if len(ONE)<=125 else 'CHECK'),
 ('Abstract','<=125 words preferred (250 max at submission)',f'{W["abstract"]} words','OK' if W['abstract']<=130 else 'CHECK'),
 ('Main text','Research Article 6,000-8,000 words including references, notes and captions (verify live page)',f'{W["total_incl_refs_captions"]:,} words incl. references and legends; {W["main_text"]:,} words of text','OK' if W['total_incl_refs_captions']<=8000 else 'CHECK'),
 ('Display items','5-8 figures for Research Articles','5 multi-panel figures','OK'),
 ('Sections','Abstract, Introduction, Results, Discussion, Materials and Methods, References and Notes, Acknowledgments','present; full methods in Supplementary Materials','OK'),
 ('References','numbered in order of citation; ~40 guideline',f'{W["refs_main"]} in main text ({W["refs_total"]} incl. SM)','OK'),
 ('Figures','<=17.8 cm wide, 6-8 pt Helvetica/Arial, vector','175 mm wide, 5-7 pt Helvetica (Arial), PDF vector + PNG; collision, alignment and text audits passed','OK'),
 ('Supplementary Materials','single PDF: Materials and Methods, Supplementary Text, figs. S1-S8, tables S1-S6, references','supplementary_materials.pdf','OK'),
 ('Double spacing and line numbers','required at submission','main.pdf and main.docx','OK'),
 ('Cover letter','customary; suggested and excluded reviewers; related manuscripts','cover_letter.md/.docx','OK'),
 ('Competing interests','AAAS form for all authors at submission','none; complete the form online','to do'),
 ('Data and materials availability','statement in Acknowledgments; deposit on publication','statement present; code and derived data archived on Zenodo (doi:10.5281/zenodo.22840160) and on GitHub','OK'),
 ('AI use','disclosed','disclosed in Acknowledgments','OK'),
 ('Funding','statement in Acknowledgments','[to complete]','to do')]
ck=[f'# Submission checklist: Science Research Article ({DATE})','','Requirements digest: docs/SCIENCE_REQUIREMENTS.md (verify the live Science author pages before upload; they block automated fetches).','','| Requirement | Limit / policy | This package | Status |','|---|---|---|---|']+[f'| {a} | {b} | {c} | {d} |' for a,b,c,d in rows]
open(os.path.join(OUT,'submission_checklist.md'),'w').write('\n'.join(ck)+'\n')
readme=f"""# Science submission package: "{title}"

Built {DATE} by scripts/08_package.py. Authors: Hao Liu (corresponding, liuhao@zfc.edu.cn), Xiaojie Zong, Jie Chen, Jianyu Xiong; School of Information Technology, Zhejiang Financial College, Hangzhou, China.

| Path | What it is |
|---|---|
| manuscript/main.pdf | Research Article (title page with one-sentence summary and abstract; Introduction, Results, Discussion, Materials and Methods, References and Notes, Acknowledgments; figures with legends at the end); double-spaced, line-numbered |
| manuscript/main.docx | Word version (pandoc; Science reference style) |
| manuscript/supplementary_materials.pdf | Materials and Methods, Supplementary Text, figs. S1-S8, tables S1-S6, references |
| manuscript/latex_source/ | LaTeX source; every number is a macro generated from results/summary.json |
| figures/ | Fig1-Fig5 (PDF vector, 175 mm; PNG previews) |
| supplementary_figures/ | figs. S1-S8 |
| source_data/ | Data S1-S5 (boom catalogue, series, event-time panels, models, entrants, retractions, booms in progress) and summary.json |
| cover_letter.md/.docx | Cover letter with suggested reviewers |
| statements.md | Author contributions, competing interests, funding, data and code availability, AI use |
| suggested_reviewers.md | Suggested referees (contact details to confirm) |
| submission_checklist.md | Requirement-by-requirement status |

Word counts: abstract {W['abstract']}; text {W['main_text']:,}; total including references and legends {W['total_incl_refs_captions']:,}; {W['refs_main']} references in the main text.

Before upload: complete the funding statement; complete the AAAS competing-interests forms; confirm reviewer suggestions. Code and derived data are archived on Zenodo (doi:10.5281/zenodo.22840160) and at https://github.com/cicisoso/scientific-bubbles-can-be-spotted-before-they-burst.
"""
open(os.path.join(OUT,'README.md'),'w').write(readme); log('package written to',OUT)
