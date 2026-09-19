"""Topic x year measures for the boom anatomy: newcomers to the topic (authors' first year in the topic), new scientists, within-topic reference share
(insularity), citations received per year (attention), first-author country concentration and China share, review share. Outputs in data/build/."""
import os, duckdb, time
P=os.path.expanduser('~/research/sos/planck/data/build'); O=os.path.expanduser('~/research/sos/llmcite/data/oa2'); L=os.path.expanduser('~/research/sos/llmcite/data/build'); ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B=os.path.join(ROOT,'data','build')
con=duckdb.connect(); con.execute(f"SET threads=12; SET memory_limit='60GB'; SET temp_directory='{P}/tmp/duck_bub'; SET preserve_insertion_order=false;")
def log(*a): print(time.strftime('%H:%M:%S'),*a,flush=True)
# 1. newcomers to the topic, in 10 topic buckets
if not os.path.exists(f'{B}/topic_year_newcomers.parquet'):
    parts=[]
    for k in range(10):
        con.execute(f"""CREATE OR REPLACE TABLE ft AS SELECT a.aid, w.topic, min(a.year) AS first_year
                        FROM read_parquet('{P}/auth/year=*/*.parquet', hive_partitioning=true) a JOIN '{P}/works.parquet' w USING (wid)
                        WHERE w.topic IS NOT NULL AND w.topic % 10 = {k} AND a.type IN ('article','review') AND a.year BETWEEN 1960 AND 2025 GROUP BY 1,2""")
        con.execute(f"""CREATE OR REPLACE TABLE nk AS
            SELECT w.topic, a.year, count(DISTINCT a.aid) AS n_authors, count(DISTINCT CASE WHEN f.first_year = a.year THEN a.aid END) AS n_newcomers,
                   count(DISTINCT CASE WHEN f.first_year = a.year AND a.y0 = a.year THEN a.aid END) AS n_new_scientists_newcomers
            FROM read_parquet('{P}/auth/year=*/*.parquet', hive_partitioning=true) a JOIN '{P}/works.parquet' w USING (wid) JOIN ft f ON f.aid = a.aid AND f.topic = w.topic
            WHERE w.topic IS NOT NULL AND w.topic % 10 = {k} AND a.type IN ('article','review') AND a.year BETWEEN 1980 AND 2025 GROUP BY 1,2""")
        parts.append(con.execute("SELECT * FROM nk").df()); log('newcomers bucket',k,len(parts[-1]))
    import pandas as pd; pd.concat(parts).to_parquet(f'{B}/topic_year_newcomers.parquet',index=False)
# 2. insularity: share of references within the same topic, per citing topic-year; and citations received per topic-year (attention)
if not os.path.exists(f'{B}/topic_year_refs.parquet'):
    con.execute(f"""COPY (SELECT w.topic, r.cyear AS year, count(*) AS n_refs, avg(CASE WHEN r.rtopic = w.topic THEN 1 ELSE 0 END) AS within_topic_share,
                           avg(CASE WHEN cw.subfield = w.subfield THEN 1 ELSE 0 END) AS within_subfield_share, avg(r.cyear - r.ryear) AS ref_age
                    FROM read_parquet('{P}/refs/cyear=*/*.parquet', hive_partitioning=true) r JOIN '{P}/works.parquet' w ON w.wid = r.wid LEFT JOIN '{P}/works.parquet' cw ON cw.wid = r.cited
                    WHERE r.cyear BETWEEN 1980 AND 2025 AND w.topic IS NOT NULL AND w.type IN ('article','review') GROUP BY 1,2) TO '{B}/topic_year_refs.parquet' (FORMAT PARQUET)""")
    log('refs done')
if not os.path.exists(f'{B}/topic_year_cites.parquet'):
    con.execute(f"""COPY (SELECT cw.topic, c.cyear AS year, sum(c.n) AS cites_received, sum(CASE WHEN w.topic = cw.topic THEN c.n ELSE 0 END) AS cites_from_within,
                           sum(CASE WHEN cw.year >= c.cyear - 5 THEN c.n ELSE 0 END) AS cites_to_recent
                    FROM (SELECT r.cited, r.cyear, r.wid, count(*) AS n FROM read_parquet('{P}/refs/cyear=*/*.parquet', hive_partitioning=true) r WHERE r.cyear BETWEEN 1980 AND 2025 GROUP BY 1,2,3) c
                    JOIN '{P}/works.parquet' cw ON cw.wid = c.cited JOIN '{P}/works.parquet' w ON w.wid = c.wid WHERE cw.topic IS NOT NULL GROUP BY 1,2) TO '{B}/topic_year_cites.parquet' (FORMAT PARQUET)""")
    log('cites done')
# 3. countries (first author) and China share
if not os.path.exists(f'{B}/topic_year_countries.parquet'):
    con.execute(f"""COPY (SELECT w.topic, w.year, count(*) AS n_with_country, max(cnt)/count(*) AS top_country_share, sum(CASE WHEN country='CN' THEN 1 ELSE 0 END)/count(*) AS china_share,
                           sum(CASE WHEN country='US' THEN 1 ELSE 0 END)/count(*) AS us_share, count(DISTINCT country) AS n_countries
                    FROM (SELECT w.wid, w.topic, w.year, c.country, count(*) OVER (PARTITION BY w.topic, w.year, c.country) AS cnt
                          FROM '{P}/works.parquet' w JOIN (SELECT wid, min(country) AS country FROM read_parquet('{O}/country/*.parquet') WHERE position='first' GROUP BY 1) c USING (wid)
                          WHERE w.year BETWEEN 1980 AND 2025 AND w.topic IS NOT NULL AND w.type IN ('article','review')) w GROUP BY 1,2) TO '{B}/topic_year_countries.parquet' (FORMAT PARQUET)""")
    log('countries done')
log('all done')
