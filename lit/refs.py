"""Verify references against Crossref and write references.bib (+ verified.json). Keys fixed here; DOIs fetched/verified; titles printed for semantic check."""
import json, re, sys, time, urllib.request, urllib.parse
UA={'User-Agent':'bubbles-study/0.1 (mailto:liuhao@zfc.edu.cn)'}
def get(url):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=60) as r: return json.load(r)
        except Exception as e:
            err=e; time.sleep(2+2*i)
    return None
REFS={ # key: (doi or None, fallback bibliographic query)
 'johansen2000crashes':('10.1142/S0219024900000115',None),
 'sornette2003stock':(None,None),
 'kindleberger2005manias':(None,None),
 'shiller2000exuberance':(None,None),
 'dedehayir2016hype':('10.1016/j.techfore.2016.04.005',None),
 'crane1969fashion':('10.2307/799952',None),
 'fujimura1988bandwagon':('10.2307/800622',None),
 'abrahamson1996fashion':('10.5465/amr.1996.9602161572',None),
 'bikhchandani1992fads':('10.1086/261849',None),
 'banerjee1992herd':('10.2307/2118364',None),
 'lorenzspreen2019attention':('10.1038/s41467-019-09311-w',None),
 'wu2007novelty':('10.1073/pnas.0704916104',None),
 'candia2019memory':('10.1038/s41562-018-0474-5',None),
 'fortunato2018science':('10.1126/science.aao0185',None),
 'jin2021prizes':('10.1038/s41467-021-25712-2',None),
 'small2006growth':('10.1007/s11192-006-0132-y',None),
 'rzhetsky2015choosing':('10.1073/pnas.1509757112',None),
 'foster2015tradition':('10.1177/0003122415601618',None),
 'uzzi2013atypical':('10.1126/science.1240474',None),
 'jia2017interest':('10.1038/s41562-017-0078',None),
 'zeng2019switch':('10.1038/s41467-019-11401-8',None),
 'hill2025pivot':(None,'The pivot penalty in research Hill Yin Stein Wang Jones Nature 2025'),
 'azoulay2019funeral':('10.1257/aer.20161574',None),
 'chu2021canonical':('10.1073/pnas.2021636118',None),
 'park2023disruptive':('10.1038/s41586-022-05543-x',None),
 'ioannidis2022covidization':('10.1073/pnas.2204074119',None),
 'fang2012misconduct':('10.1073/pnas.1212247109',None),
 'yeoteh2021covid':('10.1080/08989621.2020.1782203',None),
 'intemann2022hype':(None,'Intemann Understanding the problem of hype exaggeration values and trust in science Canadian Journal of Philosophy 2022'),
 'milojevic2018temporary':('10.1073/pnas.1800478115',None),
 'priem2022openalex':(None,None),
 'waltman2012classification':('10.1002/asi.22748',None),
 'bornmann2015growth':('10.1002/asi.23329',None),
 'wang2021science':('10.1017/9781108610834',None),
 'sinatra2016impact':('10.1126/science.aaf5239',None),
 'evans2008narrowing':('10.1126/science.1150473',None),
 'petersen2019methods':(None,'Petersen Pan Pammolli Fortunato Methods to account for citation inflation in research evaluation Research Policy 2019'),
 'salganik2006experimental':('10.1126/science.1121066',None),
 'merton1968matthew':('10.1126/science.159.3810.56',None),
 'kuhn2012structure':(None,None),
 'pedersen2014bubbles':('10.1007/s13347-013-0142-7',None),
 'brainard2018retractions':('10.1126/science.aav8384',None),
 'ke2015sleeping':('10.1073/pnas.1424329112',None),
 'wang2013quantifying':('10.1126/science.1237825',None),
 'retractionwatch2023':(None,None),
}
BOOKS={
 'sornette2003stock':"@book{sornette2003stock,\n  title={{Why Stock Markets Crash: Critical Events in Complex Financial Systems}},\n  author={Sornette, Didier},\n  year={2003},\n  publisher={Princeton University Press},\n  address={Princeton}\n}",
 'kindleberger2005manias':"@book{kindleberger2005manias,\n  title={{Manias, Panics and Crashes: A History of Financial Crises}},\n  author={Kindleberger, Charles P. and Aliber, Robert Z.},\n  year={2005},\n  edition={5},\n  publisher={Palgrave Macmillan},\n  address={Basingstoke}\n}",
 'shiller2000exuberance':"@book{shiller2000exuberance,\n  title={{Irrational Exuberance}},\n  author={Shiller, Robert J.},\n  year={2000},\n  publisher={Princeton University Press},\n  address={Princeton}\n}",
 'kuhn2012structure':"@book{kuhn2012structure,\n  title={{The Structure of Scientific Revolutions}},\n  author={Kuhn, Thomas S.},\n  year={1962},\n  publisher={University of Chicago Press},\n  address={Chicago}\n}",
 'brainard2018retractions':"@misc{brainard2018retractions,\n  title={{What a massive database of retracted papers reveals about science publishing's `death penalty'}},\n  author={Brainard, Jeffrey and You, Jia},\n  year={2018},\n  howpublished={Science, News, 25 October 2018},\n  doi={10.1126/science.aav8384}\n}",
 'johansen2000crashes':"@article{johansen2000crashes,\n  title={{Crashes as critical points}},\n  author={Johansen, Anders and Ledoit, Olivier and Sornette, Didier},\n  journal={International Journal of Theoretical and Applied Finance},\n  volume={3},\n  pages={219--255},\n  year={2000},\n  doi={10.1142/S0219024900000115}\n}",
 'retractionwatch2023':"@misc{retractionwatch2023,\n  title={{The Retraction Watch Database}},\n  author={{The Center for Scientific Integrity}},\n  year={2026},\n  howpublished={Crossref and Retraction Watch, https://api.labs.crossref.org/data/retractionwatch (accessed September 2026)}\n}",
 'priem2022openalex':"@misc{priem2022openalex,\n  title={{OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts}},\n  author={Priem, Jason and Piwowar, Heather and Orr, Richard},\n  year={2022},\n  howpublished={arXiv:2205.01833},\n  doi={10.48550/arXiv.2205.01833}\n}",
}
import html
def esc(s): return html.unescape(s).replace('&','\\&').replace('%','\\%')
def entry(key,m):
    au=' and '.join(f"{a.get('family','')}, {a.get('given','')}".strip(', ') if 'family' in a else a.get('name','') for a in m.get('author',[]))
    title=esc(re.sub(r'<[^>]+>','',m.get('title',[''])[0])); jr=esc((m.get('container-title') or [''])[0])
    yr=(m.get('issued',{}).get('date-parts') or [[None]])[0][0]; vol=m.get('volume',''); pg=m.get('page','') or m.get('article-number','')
    typ=m.get('type','')
    if typ in ('posted-content',):
        return f"@misc{{{key},\n  title={{{{{title}}}}},\n  author={{{au}}},\n  year={{{yr}}},\n  howpublished={{arXiv}},\n  doi={{{m['DOI']}}}\n}}"
    if typ in ('proceedings-article',):
        return f"@inproceedings{{{key},\n  title={{{{{title}}}}},\n  author={{{au}}},\n  booktitle={{{jr}}},\n  pages={{{pg}}},\n  year={{{yr}}},\n  doi={{{m['DOI']}}}\n}}"
    if typ=='book' or typ=='monograph':
        return f"@book{{{key},\n  title={{{{{title}}}}},\n  author={{{au}}},\n  year={{{yr}}},\n  publisher={{{esc(m.get('publisher',''))}}},\n  doi={{{m['DOI']}}}\n}}"
    return f"@article{{{key},\n  title={{{{{title}}}}},\n  author={{{au}}},\n  journal={{{jr}}},\n  volume={{{vol}}},\n  pages={{{pg}}},\n  year={{{yr}}},\n  doi={{{m['DOI']}}}\n}}"
out=[]; ver={}
for key,(doi,q) in REFS.items():
    if key in BOOKS: out.append(BOOKS[key]); ver[key]={'status':'book'}; continue
    m=None
    if doi:
        d=get(f'https://api.crossref.org/works/{urllib.parse.quote(doi)}'); m=d['message'] if d else None
    if m is None and q:
        d=get(f'https://api.crossref.org/works?query.bibliographic={urllib.parse.quote(q)}&rows=3'); items=d['message']['items'] if d else []
        m=items[0] if items else None
    if m is None: print('MISSING',key,doi,q); ver[key]={'status':'missing'}; continue
    out.append(entry(key,m)); ver[key]={'status':'ok','doi':m['DOI'],'title':re.sub(r'<[^>]+>','',m.get('title',[''])[0]),'year':(m.get('issued',{}).get('date-parts') or [[None]])[0][0],'container':(m.get('container-title') or [''])[0],'type':m.get('type')}
    print(key,'|',ver[key]['doi'],'|',ver[key]['title'][:80],'|',ver[key]['year'],'|',ver[key]['container'][:40])
open('references.bib','w').write('\n\n'.join(out)+'\n'); json.dump(ver,open('verified.json','w'),indent=1)
print('wrote',len(out))
