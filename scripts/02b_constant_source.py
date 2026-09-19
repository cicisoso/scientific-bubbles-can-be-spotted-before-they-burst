"""Constant-source ('same-store') booms and crashes. Candidates: local maxima of the stable-core share with run-up >= 1.5 and >= 200 papers.
For each candidate peak t, the topic's series over [t-5, t+5] is recomputed within the set of sources active in both t-5 and t+5 (>= 20 article/review
papers of any topic in each of those years), as a share of all papers in those sources. Run-up and drawdown are then measured in this constant-source
panel. Output results/episodes_cs.parquet (one row per candidate) and data/build/cs_series.parquet (the series)."""
import os, json, numpy as np, pandas as pd, duckdb, time
P=os.path.expanduser('~/research/sos/planck/data/build'); O=os.path.expanduser('~/research/sos/llmcite/data/oa2'); ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B=os.path.join(ROOT,'data','build'); R=os.path.join(ROOT,'results')
W=5; KMIN=20; RUN=float(os.environ.get('RUN','2.0')); CRASH=float(os.environ.get('CRASH','0.4')); NMIN=int(os.environ.get('NMIN','300'))
con=duckdb.connect(); con.execute(f"SET threads=12; SET memory_limit='60GB'; SET temp_directory='{P}/tmp/duck_bub'; SET preserve_insertion_order=false;")
t0=time.time()
# topic-year-source counts (stable core: article/review with DOI in a journal source) and source-year totals
con.execute(f"""CREATE TABLE ts AS SELECT w.topic, w.year, m.sid, count(*) AS n FROM '{P}/works.parquet' w JOIN read_parquet('{O}/meta/*.parquet') m USING (wid)
                WHERE w.year BETWEEN 1980 AND 2025 AND w.topic IS NOT NULL AND w.type IN ('article','review') AND m.has_doi AND m.stype='journal' AND m.sid IS NOT NULL GROUP BY 1,2,3""")
con.execute("CREATE TABLE sy AS SELECT sid, year, sum(n) AS n_total FROM ts GROUP BY 1,2")
print('ts rows',con.execute("SELECT count(*) FROM ts").fetchone(),'sources',con.execute("SELECT count(DISTINCT sid) FROM sy").fetchone(), f'{time.time()-t0:.0f}s')
# candidate peaks from the stable-core share series (broad net)
ty=con.execute("SELECT topic, year, sum(n) AS n FROM ts GROUP BY 1,2").df(); tot=ty.groupby('year').n.sum()
wide=ty.pivot(index='topic',columns='year',values='n').reindex(columns=range(1980,2026)).fillna(0); share=wide.div(tot,axis=1); years=np.array(share.columns)
cands=[]
for topic,s in share.iterrows():
    v=s.values; n=wide.loc[topic].values
    for i in range(W,len(v)):
        lo=max(0,i-W); hi=min(len(v),i+W+1)
        if v[i]<=0 or v[i]<v[lo:hi].max() or (v[lo:i]==v[i]).any(): continue
        pre=v[lo:i]; run=v[i]/pre.min() if pre.min()>0 else np.inf
        if run<1.5 or n[i]<200: continue
        cands.append((int(topic),int(years[i])))
cd=pd.DataFrame(cands,columns=['topic','t']); print('candidates',len(cd)); con.register('cd',cd)
# active sources per candidate peak year: >= KMIN papers in t-5 and in t+5 (t+5 capped at 2025 for censored peaks -> use t and 2025?)
con.execute(f"""CREATE TABLE act AS
  SELECT c.topic, c.t, s1.sid FROM (SELECT DISTINCT t, topic FROM cd) c
  JOIN sy s1 ON s1.year = c.t - {W} AND s1.n_total >= {KMIN}
  JOIN sy s2 ON s2.sid = s1.sid AND s2.year = LEAST(c.t + {W}, 2025) AND s2.n_total >= {KMIN}""")
con.execute(f"""CREATE TABLE cs AS
  SELECT a.topic, a.t, ts.year, sum(ts.n) AS n_cs FROM act a JOIN ts ON ts.sid = a.sid AND ts.topic = a.topic AND ts.year BETWEEN a.t - {W} AND a.t + {W} GROUP BY 1,2,3""")
con.execute(f"""CREATE TABLE cstot AS
  SELECT a.topic, a.t, sy.year, sum(sy.n_total) AS n_tot, count(*) AS n_sources FROM act a JOIN sy ON sy.sid = a.sid AND sy.year BETWEEN a.t - {W} AND a.t + {W} GROUP BY 1,2,3""")
ser=con.execute("SELECT c.topic, c.t, c.year, coalesce(cs.n_cs,0) AS n_cs, c.n_tot, c.n_sources FROM cstot c LEFT JOIN cs USING (topic, t, year) ORDER BY 1,2,3").df()
ser['share']=ser.n_cs/ser.n_tot; ser.to_parquet(os.path.join(B,'cs_series.parquet'),index=False); print('series rows',len(ser), f'{time.time()-t0:.0f}s')
names={int(t['id'].split('/')[-1].lstrip('T')):t['display_name'] for t in json.load(open(os.path.join(ROOT,'data','names','topics.json')))}
meta=pd.read_parquet(os.path.join(B,'topic_year.parquet')).groupby('topic')[['subfield','field','domain']].first()
rows=[]
for (topic,t),g in ser.groupby(['topic','t']):
    g=g.set_index('year').reindex(range(t-W,t+W+1)); v=g.share.values; n=g.n_cs.values
    if np.isnan(v[W]) or v[W]<=0: continue
    pre=v[:W]; post=v[W+1:]; full=t<=2020
    run=v[W]/np.nanmin(pre) if np.nanmin(pre)>0 else np.inf
    ismax=v[W]>=np.nanmax(v) if full else v[W]>=np.nanmax(v[:W+1])
    dd=1-np.nanmin(post)/v[W] if full else np.nan
    rows.append(dict(topic=topic,name=names.get(topic,''),subfield=meta.loc[topic,'subfield'] if topic in meta.index else None,field=meta.loc[topic,'field'] if topic in meta.index else None,domain=meta.loc[topic,'domain'] if topic in meta.index else None,
                     peak_year=t,n_peak_cs=int(n[W]),n_sources_cs=int(g.n_sources.iloc[W]) if not np.isnan(g.n_sources.iloc[W]) else 0,share_peak=float(v[W]),runup=float(run),is_peak=bool(ismax),
                     drawdown=float(dd) if full else np.nan,evaluable=full,crash=(bool(dd>=CRASH) if full else None),years_to_min=int(np.nanargmin(post)+1) if full else None,
                     growth_accel=float(np.nanmean(np.diff(np.log(np.maximum(v[W-3:W+1],1e-12)),2)))))
ep=pd.DataFrame(rows); ep=ep[(ep.runup>=RUN)&(ep.n_peak_cs>=NMIN)&ep.is_peak].copy()
ep=ep.sort_values(['topic','share_peak'],ascending=[True,False]); keep=[]
for topic,g in ep.groupby('topic'):
    taken=[]
    for _,r in g.iterrows():
        if all(abs(r.peak_year-y)>=2*W for y in taken): keep.append(r); taken.append(r.peak_year)
ep=pd.DataFrame(keep).sort_values(['peak_year','topic']).reset_index(drop=True); ep.to_parquet(os.path.join(R,'episodes_cs.parquet'),index=False)
ev=ep[ep.evaluable]; pd.set_option('display.width',250)
print(f'booms: {len(ep)} in {ep.topic.nunique()} topics; evaluable: {len(ev)}; crashes: {int(ev.crash.sum())} ({100*ev.crash.mean():.1f}%); ongoing: {(~ep.evaluable).sum()}')
print(ev.groupby(ev.peak_year//10*10).crash.agg(['size','mean']).round(3)); print(ev.groupby('domain').crash.agg(['size','mean']).round(3))
print(ev.sort_values('n_peak_cs',ascending=False).head(30)[['name','peak_year','n_peak_cs','n_sources_cs','runup','drawdown','crash']].to_string())
print(ep[~ep.evaluable].sort_values('n_peak_cs',ascending=False).head(15)[['name','peak_year','n_peak_cs','runup']].to_string())
