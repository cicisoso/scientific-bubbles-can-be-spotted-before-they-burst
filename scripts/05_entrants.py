"""Fate of boom-era entrants. For each episode (topic, peak t), entrants are authors whose first paper in the topic appeared in t-2..t. Outcomes at t+5:
still publishing anywhere (last year in the corpus >= t+5), still publishing in the topic (a paper in the topic in t+3..t+5), moved (publishing elsewhere
but not in the topic). Compared with incumbents (first paper in the topic before t-5) and with career-age-matched entrants to soft-landing booms.
Output results/entrants.parquet (per episode x group)."""
import os, numpy as np, pandas as pd, duckdb, time
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B=os.path.join(ROOT,'data','build'); R=os.path.join(ROOT,'results'); P=os.path.expanduser('~/research/sos/planck/data/build')
con=duckdb.connect(); con.execute(f"SET threads=12; SET memory_limit='60GB'; SET temp_directory='{P}/tmp/duck_bub'; SET preserve_insertion_order=false;")
ep=pd.read_parquet(os.path.join(R,'episodes_cs.parquet')); topics=sorted(set(int(x) for x in ep.topic)); con.register('ep',ep[['topic','peak_year','crash','evaluable']])
t0=time.time()
con.execute(f"""CREATE TABLE atop AS SELECT a.aid, w.topic, min(a.year) AS first_year, max(a.year) AS last_year_topic, count(*) AS n_in_topic
                FROM read_parquet('{P}/auth/year=*/*.parquet', hive_partitioning=true) a JOIN '{P}/works.parquet' w USING (wid)
                WHERE w.topic IN (SELECT DISTINCT topic FROM ep) AND a.type IN ('article','review') AND a.year BETWEEN 1960 AND 2025 GROUP BY 1,2""")
print("author-topic rows", con.execute("SELECT count(*) FROM atop").fetchone(), f'{time.time()-t0:.0f}s')
con.execute(f"CREATE TABLE af AS SELECT aid, y0, ylast, n_works FROM '{P}/author_first.parquet'")
out=con.execute("""
  SELECT e.topic, e.peak_year, e.crash, e.evaluable,
         CASE WHEN x.first_year BETWEEN e.peak_year-2 AND e.peak_year THEN 'entrant' WHEN x.first_year < e.peak_year-5 AND x.last_year_topic >= e.peak_year-2 THEN 'incumbent' END AS grp,
         count(*) AS n, avg(CASE WHEN af.y0 >= e.peak_year-2 THEN 1 ELSE 0 END) AS share_new_scientists,
         avg(CASE WHEN af.ylast >= e.peak_year+5 THEN 1 ELSE 0 END) AS still_publishing_t5, avg(CASE WHEN x.last_year_topic >= e.peak_year+3 THEN 1 ELSE 0 END) AS still_in_topic_t5,
         avg(CASE WHEN af.ylast >= e.peak_year+5 AND x.last_year_topic < e.peak_year+3 THEN 1 ELSE 0 END) AS moved_t5, avg(x.n_in_topic) AS papers_in_topic
  FROM ep e JOIN atop x ON x.topic = e.topic JOIN af ON af.aid = x.aid
  WHERE e.peak_year <= 2020 GROUP BY 1,2,3,4,5 HAVING grp IS NOT NULL""").df()
out.to_parquet(os.path.join(R,'entrants.parquet'),index=False); print(f'{time.time()-t0:.0f}s')
ev=out[out.evaluable]
print(ev.groupby(['grp','crash'])[['still_publishing_t5','still_in_topic_t5','moved_t5','share_new_scientists']].mean().round(3))
