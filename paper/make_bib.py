"""Science-style numbered reference list. Reads the citation keys in order of first appearance from the section files (main text first, then
Supplementary Materials), looks up metadata in ../lit/verified.json and ../lit/references.bib (books/arXiv), and writes references.tex
(a thebibliography environment; numbers = order of first citation) plus refkeys.json. Journal abbreviations are mapped explicitly."""
import os, re, json
P=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(os.path.dirname(P),'lit')
ORDER=['sections/00_abstract.tex','sections/01_intro.tex','sections/02_results.tex','sections/03_discussion.tex','sections/04_methods_summary.tex','sections/05_acknowledgments.tex','sections/06_figures.tex','sections/sm_methods.tex','sections/sm_text.tex','sections/sm_figures.tex','sections/sm_tables.tex']
ver=json.load(open(os.path.join(L,'verified.json'))); bib=open(os.path.join(L,'references.bib')).read()
ABBR={'Science':'Science','Science Advances':'Sci. Adv.','Nature':'Nature','Nature Human Behaviour':'Nat. Hum. Behav.','Nature Communications':'Nat. Commun.','Proceedings of the National Academy of Sciences':'Proc. Natl. Acad. Sci. U.S.A.',
      'Journal of the American Society for Information Science':'J. Am. Soc. Inf. Sci.','Journal of the American Society for Information Science and Technology':'J. Am. Soc. Inf. Sci. Technol.',
      'Journal of the Association for Information Science and Technology':'J. Assoc. Inf. Sci. Technol.','Scientometrics':'Scientometrics','Management Science':'Manage. Sci.','Research Policy':'Res. Policy',
      'Accountability in Research':'Account. Res.','American Economic Review':'Am. Econ. Rev.','American Sociological Review':'Am. Sociol. Rev.','Canadian Journal of Philosophy':'Can. J. Philos.',
      'International Journal of Theoretical and Applied Finance':'Int. J. Theor. Appl. Finance','Journal of Political Economy':'J. Polit. Econ.','Philosophy \\& Technology':'Philos. Technol.','Social Problems':'Soc. Probl.',
      'Technological Forecasting and Social Change':'Technol. Forecast. Soc. Change','The Academy of Management Review':'Acad. Manage. Rev.','The Quarterly Journal of Economics':'Q. J. Econ.'}
def initials(given): return ' '.join(p[0]+'.' for p in re.split(r'[\s\-]+',given) if p) if given else ''
def fmt_authors(auths):
    out=[]
    for a in auths:
        fam,giv=a
        out.append(f"{initials(giv)} {fam}".strip())
    if len(out)>6: return ', '.join(out[:1])+' et al.'
    return ', '.join(out)
def parse_bib_entry(key):
    m=re.search(r'@(\w+)\{'+re.escape(key)+r',(.*?)\n\}',bib,flags=re.S)
    if not m: return None
    typ=m.group(1); body=m.group(2); f={}
    for fm in re.finditer(r'(\w+)=\{(.*?)\}(?=,\n|\n|$)',body,flags=re.S): f[fm.group(1)]=fm.group(2)
    auths=[]
    for a in f.get('author','').split(' and '):
        a=a.strip()
        if a.startswith('{'): fam,giv=a.strip('{}'),''
        elif ',' in a: fam,giv=[x.strip() for x in a.split(',',1)]
        else: parts=a.split(); fam,giv=parts[-1],' '.join(parts[:-1])
        auths.append((fam,giv))
    title=f.get('title','').strip('{}'); return typ,f,auths,title
def entry(key):
    r=parse_bib_entry(key); assert r, key
    typ,f,auths,title=r; au=fmt_authors(auths); yr=f.get('year','')
    if typ=='book': return f"{au}, \\textit{{{title}}} ({f.get('publisher','')}, {yr})."
    if typ=='misc':
        how=f.get('howpublished',''); 
        if 'arXiv' in how: return f"{au}, {title}. {how.replace('arXiv:','arXiv:')} (preprint, {yr}); \\url{{https://doi.org/{f.get('doi','')}}}."
        if f.get('doi'): return f"{au}, {title}. {how} ({yr}); doi:{f['doi']}."
        return f"{au}, {title}. {how} ({yr})."
    if typ=='inproceedings': return f"{au}, {title}. In \\textit{{{ABBR.get(f.get('booktitle',''),f.get('booktitle',''))}}} (2025), pp. {f.get('pages','')}; doi:{f.get('doi','')}."
    jr=ABBR.get(f.get('journal',''),f.get('journal','')); vol=f.get('volume',''); pg=re.sub(r'(\d)-+(\d)',r'\1–\2',f.get('pages',''))
    s=f"{au}, {title}. \\textit{{{jr}}}"
    if vol: s+=f" \\textbf{{{vol}}}"
    if pg: s+=f", {pg}"
    s+=f" ({yr})."
    if f.get('doi'): s+=f" doi:{f['doi']}"
    return s
keys=[]; nmain=None
for fn in ORDER:
    if fn.startswith('sections/sm_') and nmain is None: nmain=len(keys)
    p=os.path.join(P,fn)
    if not os.path.exists(p): continue
    for m in re.finditer(r'\\cite[pt]?\{([^}]*)\}',open(p).read()):
        for k in m.group(1).split(','):
            k=k.strip()
            if k and k not in keys: keys.append(k)
if nmain is None: nmain=len(keys)
def write(path,ks):
    with open(path,'w') as f:
        f.write('\\begin{thebibliography}{%d}\n'%len(ks))
        for k in ks: f.write(f"\\bibitem{{{k}}} {entry(k)}\n")
        f.write('\\end{thebibliography}\n')
write(os.path.join(P,'references.tex'),keys[:nmain]); write(os.path.join(P,'references_sm.tex'),keys)
json.dump(dict(all=keys,n_main=nmain),open(os.path.join(P,'refkeys.json'),'w'),indent=1); print(nmain,'main references,',len(keys),'in total')
