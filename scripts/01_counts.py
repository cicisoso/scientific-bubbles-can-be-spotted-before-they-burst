"""Topic x year counts 1980-2025 from the planck build (core corpus): research articles+reviews (main), all types (robustness),
with mean FWCI, low-impact and uncited shares, retraction share, and field/all totals. Output data/build/topic_year.parquet."""
import os, duckdb, time
P=os.path.expanduser('~/research/sos/planck/data/build'); ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B=os.path.join(ROOT,'data','build'); os.makedirs(B,exist_ok=True)
con=duckdb.connect(); con.execute("SET threads=10; SET memory_limit='40GB'")
t=time.time()
con.execute(f"""COPY (
  SELECT topic, subfield, field, domain, year, count(*) AS n_all,
    sum(CASE WHEN type IN ('article','review') THEN 1 ELSE 0 END) AS n, sum(CASE WHEN type='review' THEN 1 ELSE 0 END) AS n_review, sum(CASE WHEN type='preprint' THEN 1 ELSE 0 END) AS n_preprint,
    avg(CASE WHEN type IN ('article','review') THEN fwci END) AS fwci_mean, median(CASE WHEN type IN ('article','review') THEN fwci END) AS fwci_med,
    avg(CASE WHEN type IN ('article','review') THEN (fwci < 0.25)::INT END) AS low_fwci_share, avg(CASE WHEN type IN ('article','review') THEN (fwci >= 2)::INT END) AS high_fwci_share,
    avg(CASE WHEN type IN ('article','review') THEN (cited_by_count = 0)::INT END) AS uncited_share, avg(CASE WHEN type IN ('article','review') THEN is_retracted::INT END) AS retracted_share,
    sum(CASE WHEN type IN ('article','review') THEN is_retracted::INT END) AS n_retracted, avg(CASE WHEN type IN ('article','review') THEN n_auth END) AS team_mean,
    avg(CASE WHEN type IN ('article','review') THEN (language='en')::INT END) AS en_share, avg(CASE WHEN type IN ('article','review') THEN n_refs END) AS refs_mean
  FROM '{P}/works.parquet' WHERE year BETWEEN 1980 AND 2025 AND topic IS NOT NULL GROUP BY 1,2,3,4,5) TO '{B}/topic_year.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)""")
print(con.execute(f"SELECT count(*) AS n_rows, count(DISTINCT topic) AS n_topics FROM '{B}/topic_year.parquet'").fetchone(), f'{time.time()-t:.0f}s')
print(con.execute(f"SELECT year, sum(n) n_articles, sum(n_all) n_all, count(*) topics_active FROM '{B}/topic_year.parquet' GROUP BY 1 ORDER BY 1").df().to_string())
