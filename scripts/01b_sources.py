"""Topic x year source structure from the llmcite second-pass metadata (all core works): counts on the 'stable core' (article/review with a DOI in a
journal source), number of distinct sources, top-source share, DOI share, OA share; and distinct-author counts from the planck authorship tables."""
import os, duckdb, time
P=os.path.expanduser('~/research/sos/planck/data/build'); O=os.path.expanduser('~/research/sos/llmcite/data/oa2'); ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B=os.path.join(ROOT,'data','build')
con=duckdb.connect(); con.execute(f"SET threads=12; SET memory_limit='60GB'; SET temp_directory='{P}/tmp/duck_bub'; SET preserve_insertion_order=false;")
t=time.time()
con.execute(f"""CREATE TABLE ts AS
  SELECT w.topic, w.year, m.sid, count(*) AS n, sum(CASE WHEN m.has_doi AND m.stype='journal' THEN 1 ELSE 0 END) AS n_core, sum(m.has_doi::INT) AS n_doi, sum(m.is_oa::INT) AS n_oa
  FROM '{P}/works.parquet' w JOIN read_parquet('{O}/meta/*.parquet') m USING (wid)
  WHERE w.year BETWEEN 1980 AND 2025 AND w.topic IS NOT NULL AND w.type IN ('article','review') GROUP BY 1,2,3""")
print('topic-year-source rows', con.execute("SELECT count(*) FROM ts").fetchone(), f'{time.time()-t:.0f}s')
con.execute(f"""COPY (SELECT topic, year, sum(n) AS n_art, sum(n_core) AS n_core, sum(n_doi)/sum(n) AS doi_share, sum(n_oa)/sum(n) AS oa_share,
                       count(DISTINCT sid) AS n_sources, max(n)/sum(n) AS top_source_share, sum(CASE WHEN sid IS NULL THEN n ELSE 0 END)/sum(n) AS nosource_share,
                       arg_max(sid, n) AS top_sid
                FROM ts GROUP BY 1,2) TO '{B}/topic_year_sources.parquet' (FORMAT PARQUET)""")
print('sources done', f'{time.time()-t:.0f}s')
con.execute(f"""COPY (SELECT w.topic, a.year, count(DISTINCT a.aid) AS n_authors, count(*) AS n_authorships,
                       count(DISTINCT CASE WHEN a.y0 = a.year THEN a.aid END) AS n_new_scientists, count(DISTINCT CASE WHEN a.year - a.y0 <= 2 THEN a.aid END) AS n_junior
                FROM read_parquet('{P}/auth/year=*/*.parquet', hive_partitioning=true) a JOIN '{P}/works.parquet' w USING (wid)
                WHERE a.year BETWEEN 1980 AND 2025 AND w.topic IS NOT NULL AND a.type IN ('article','review') GROUP BY 1,2) TO '{B}/topic_year_authors.parquet' (FORMAT PARQUET)""")
print('authors done', f'{time.time()-t:.0f}s')
