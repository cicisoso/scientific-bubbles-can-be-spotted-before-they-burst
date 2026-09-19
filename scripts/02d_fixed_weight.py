"""Fixed-source-weight variant of the constant-source series. For each boom (topic, peak t) and the same set of active sources, the topic's share is
the weighted mean over sources of the topic's share within each source, with weights equal to the source's mean annual output over [t-5, t+5].
A source that multiplies its total output cannot raise the index unless the topic's share within that source rises. Output results/fixed_weight.parquet."""
import os, numpy as np, pandas as pd, duckdb, time
P=os.path.expanduser('~/research/sos/planck/data/build'); O=os.path.expanduser('~/research/sos/llmcite/data/oa2'); ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R=os.path.join(ROOT,'results')
W=5; KMIN=20; CRASH=0.4
con=duckdb.connect(); con.execute(f"SET threads=12; SET memory_limit='60GB'; SET temp_directory='{P}/tmp/duck_bub'; SET preserve_insertion_order=false;")
E=pd.read_parquet(os.path.join(R,'episodes_cs.parquet')); con.register('ep',E[['topic','peak_year']]); t0=time.time()
con.execute(f"""CREATE TABLE ts AS SELECT w.topic, w.year, m.sid, count(*) AS n FROM '{P}/works.parquet' w JOIN read_parquet('{O}/meta/*.parquet') m USING (wid)
                WHERE w.year BETWEEN 1980 AND 2025 AND w.topic IS NOT NULL AND w.type IN ('article','review') AND m.has_doi AND m.stype='journal' AND m.sid IS NOT NULL GROUP BY 1,2,3""")
con.execute("CREATE TABLE sy AS SELECT sid, year, sum(n) AS n_total FROM ts GROUP BY 1,2")
con.execute(f"""CREATE TABLE act AS SELECT c.topic, c.peak_year AS t, s1.sid FROM ep c
  JOIN sy s1 ON s1.year = c.peak_year - {W} AND s1.n_total >= {KMIN}
  JOIN sy s2 ON s2.sid = s1.sid AND s2.year = LEAST(c.peak_year + {W}, 2025) AND s2.n_total >= {KMIN}""")
# weights: mean annual output of each active source over the window; index = sum_s w_s * (n_topic,s,y / n_total,s,y) / sum_s w_s (over sources present in year y)
con.execute(f"""CREATE TABLE wgt AS SELECT a.topic, a.t, a.sid, avg(sy.n_total) AS w FROM act a JOIN sy ON sy.sid=a.sid AND sy.year BETWEEN a.t-{W} AND a.t+{W} GROUP BY 1,2,3""")
d=con.execute(f"""SELECT g.topic, g.t, sy.year, sum(g.w * coalesce(ts.n,0)/sy.n_total)/sum(g.w) AS share_fw, sum(coalesce(ts.n,0)) AS n_cs
  FROM wgt g JOIN sy ON sy.sid=g.sid AND sy.year BETWEEN g.t-{W} AND g.t+{W}
  LEFT JOIN ts ON ts.sid=g.sid AND ts.topic=g.topic AND ts.year=sy.year GROUP BY 1,2,3 ORDER BY 1,2,3""").df(); print('series', len(d), f'{time.time()-t0:.0f}s')
rows=[]
for (topic,t),g in d.groupby(['topic','t']):
    g=g.set_index('year').reindex(range(t-W,t+W+1)); v=g.share_fw.values; full=t<=2020
    if np.isnan(v[W]) or v[W]<=0: continue
    pre=v[:W]; post=v[W+1:]; run=v[W]/np.nanmin(pre) if np.nanmin(pre)>0 else np.inf
    ismax=v[W]>=np.nanmax(v) if full else v[W]>=np.nanmax(v[:W+1]); dd=1-np.nanmin(post)/v[W] if full else np.nan
    rows.append(dict(topic=topic,peak_year=t,runup_fw=float(run),is_peak_fw=bool(ismax),drawdown_fw=float(dd) if full else np.nan,crash_fw=(bool(dd>=CRASH) if full else None),
                     boom_fw=bool(run>=1.5 and ismax),net_gain_fw=float(v[-1]/v[0]) if full and v[0]>0 else np.nan))
F=pd.DataFrame(rows); F.to_parquet(os.path.join(R,'fixed_weight.parquet'),index=False)
M=E.merge(F,on=['topic','peak_year'],how='left'); ev=M[M.evaluable]
print('evaluable',len(ev),'still a boom under fixed weights (run-up>=1.5, local max):',int(ev.boom_fw.sum()))
b=ev[ev.boom_fw]; print(f'crash rate among those: {b.crash_fw.mean():.3f} (n={len(b)}); crash by main definition among them {b.crash.mean():.3f}')
print('agreement main vs fw crash among fw booms:', pd.crosstab(b.crash,b.crash_fw))
print('Spearman run-up main vs fw:', ev[['runup','runup_fw']].corr('spearman').iloc[0,1].round(3), ' drawdown:', ev[['drawdown','drawdown_fw']].corr('spearman').iloc[0,1].round(3))
