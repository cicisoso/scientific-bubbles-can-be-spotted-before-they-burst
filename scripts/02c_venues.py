"""Venue concentration of each boom: which sources carried the run-up in the constant-source panel, and how concentrated the increase was.
For every evaluable episode (peak t): within the constant-source panel, the share of the constant-source peak count and of the increase (peak minus t-5)
contributed by the top 1 and top 3 sources, plus the top-3 source ids. Output results/venues.parquet and results/venue_names.csv (names via OpenAlex API)."""
import os, json, time, numpy as np, pandas as pd, duckdb, urllib.request
P=os.path.expanduser('~/research/sos/planck/data/build'); O=os.path.expanduser('~/research/sos/llmcite/data/oa2'); ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B=os.path.join(ROOT,'data','build'); R=os.path.join(ROOT,'results')
W=5; KMIN=20
con=duckdb.connect(); con.execute(f"SET threads=12; SET memory_limit='60GB'; SET temp_directory='{P}/tmp/duck_bub'; SET preserve_insertion_order=false;")
E=pd.read_parquet(os.path.join(R,'episodes_cs.parquet')); con.register('ep',E[['topic','peak_year']])
t0=time.time()
con.execute(f"""CREATE TABLE ts AS SELECT w.topic, w.year, m.sid, count(*) AS n FROM '{P}/works.parquet' w JOIN read_parquet('{O}/meta/*.parquet') m USING (wid)
                WHERE w.year BETWEEN 1980 AND 2025 AND w.topic IS NOT NULL AND w.type IN ('article','review') AND m.has_doi AND m.stype='journal' AND m.sid IS NOT NULL GROUP BY 1,2,3""")
con.execute("CREATE TABLE sy AS SELECT sid, year, sum(n) AS n_total FROM ts GROUP BY 1,2"); print('ts built', f'{time.time()-t0:.0f}s')
con.execute(f"""CREATE TABLE act AS SELECT c.topic, c.peak_year AS t, s1.sid FROM ep c
  JOIN sy s1 ON s1.year = c.peak_year - {W} AND s1.n_total >= {KMIN}
  JOIN sy s2 ON s2.sid = s1.sid AND s2.year = LEAST(c.peak_year + {W}, 2025) AND s2.n_total >= {KMIN}""")
d=con.execute(f"""SELECT a.topic, a.t, a.sid, coalesce(p.n,0) AS n_peak, coalesce(q.n,0) AS n_pre
  FROM act a LEFT JOIN ts p ON p.sid=a.sid AND p.topic=a.topic AND p.year=a.t LEFT JOIN ts q ON q.sid=a.sid AND q.topic=a.topic AND q.year=a.t-{W}
  WHERE coalesce(p.n,0)>0 OR coalesce(q.n,0)>0""").df()
rows=[]
for (topic,t),g in d.groupby(['topic','t']):
    g=g.assign(inc=(g.n_peak-g.n_pre).clip(lower=0)).sort_values('n_peak',ascending=False)
    tot=g.n_peak.sum(); inc=g.inc.sum(); gi=g.sort_values('inc',ascending=False)
    rows.append(dict(topic=topic,peak_year=t,n_sources_active=len(g),top1_share_peak=g.n_peak.iloc[0]/tot if tot else np.nan,top3_share_peak=g.n_peak.iloc[:3].sum()/tot if tot else np.nan,
                     top1_share_inc=gi.inc.iloc[0]/inc if inc else np.nan,top3_share_inc=gi.inc.iloc[:3].sum()/inc if inc else np.nan,top10_share_inc=gi.inc.iloc[:10].sum()/inc if inc else np.nan,
                     top_sids=list(gi.sid.iloc[:3].astype(int)),top_inc=list(gi.inc.iloc[:3].astype(int))))
V=pd.DataFrame(rows); V.to_parquet(os.path.join(R,'venues.parquet'),index=False); print('episodes',len(V), f'{time.time()-t0:.0f}s')
# names of the sources that lead the increase in at least one episode
sids=sorted({s for l in V.top_sids for s in l}); names={}
cache=os.path.join(R,'venue_names.csv')
if os.path.exists(cache): names={int(k):v for k,v in pd.read_csv(cache).set_index('sid').display_name.items()}
for i in range(0,len(sids),50):
    chunk=[s for s in sids[i:i+50] if s not in names]
    if not chunk: continue
    url='https://api.openalex.org/sources?filter=ids.openalex:'+'|'.join(f'S{s}' for s in chunk)+'&per-page=50&select=id,display_name,host_organization_name,type&mailto=liuhao@zfc.edu.cn'
    try:
        js=json.load(urllib.request.urlopen(url,timeout=60))
        for r in js['results']: names[int(r['id'].split('/S')[-1])]=r['display_name']+' | '+str(r.get('host_organization_name'))
    except Exception as e: print('api error',e)
    time.sleep(0.2)
pd.DataFrame({'sid':list(names),'display_name':list(names.values())}).to_csv(cache,index=False); print('names',len(names))
