"""Word counts for the Science manuscript: abstract; text (intro+results+discussion+methods summary); references; figure legends; total."""
import re, os, json
P=os.path.dirname(os.path.abspath(__file__))
mac={m.group(1):m.group(2) for l in open(os.path.join(P,'macros.tex')) for m in [re.match(r'\\newcommand\{\\(\w+)\}\{(.*)\}',l.strip())] if m}
def strip(t):
    t=t.replace('\\%','PCT'); t=re.sub(r'(?<!\\)%.*','',t); t=t.replace('PCT','%'); t=re.sub(r'\\cite[pt]?\{[^}]*\}','(0)',t)
    t=re.sub(r'\\(textbf|emph|textit|figS|tabS|url)\{([^}]*)\}',r'\2',t); t=re.sub(r'\\(sub)?section\*?\{[^}]*\}','',t)
    t=re.sub(r'\\begin\{equation\*?\}.*?\\end\{equation\*?\}',' EQUATION ',t,flags=re.S); t=re.sub(r'\$[^$]*\$','X',t)
    t=re.sub(r'\\(\w+)(\{\})?',lambda m: mac.get(m.group(1),'N'),t); t=t.replace('--','-').replace('~',' ')
    return t
def count(t): return len([w for w in strip(t).split() if re.search(r'[A-Za-z0-9]',w)])
out={}
out['abstract']=count(open(os.path.join(P,'sections/00_abstract.tex')).read())
body=''.join(open(os.path.join(P,f'sections/{f}.tex')).read() for f in ('01_intro','02_results','03_discussion','04_methods_summary'))
out['main_text']=count(body)
figs=open(os.path.join(P,'sections/06_figures.tex')).read(); caps=re.findall(r'\\caption\{(.*)\}',figs); out['legends']=sum(count(c) for c in caps); out['legend_each']=[count(c) for c in caps]
refs=open(os.path.join(P,'references.tex')).read() if os.path.exists(os.path.join(P,'references.tex')) else ''; out['references']=count(refs)
ack=count(open(os.path.join(P,'sections/05_acknowledgments.tex')).read()); out['acknowledgments']=ack
out['total_incl_refs_captions']=out['abstract']+out['main_text']+out['legends']+out['references']+ack
rk=json.load(open(os.path.join(P,'refkeys.json'))) if os.path.exists(os.path.join(P,'refkeys.json')) else {'n_main':0,'all':[]}
out['refs_main']=rk['n_main']; out['refs_total']=len(rk['all'])
sm=''.join(open(os.path.join(P,f'sections/{f}.tex')).read() for f in ('sm_methods','sm_text')); out['sm_text']=count(sm)
json.dump(out,open(os.path.join(P,'wordcounts.json'),'w'),indent=1); print(json.dumps(out,indent=1))
