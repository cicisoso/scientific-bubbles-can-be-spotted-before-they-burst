"""Download the OpenAlex awards entity (parquet on public S3 over HTTPS), keeping the columns needed: award id, funder, amount, currency,
type/scheme, years, funded outputs, primary topic, awarded institution country. Output data/awards/part_*.parquet (resumable)."""
import json, os, time, duckdb, concurrent.futures as cf, random
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D=os.path.join(ROOT,'data','awards'); os.makedirs(D,exist_ok=True)
m=json.load(open(os.path.join(ROOT,'data','awards_manifest.json'))); files=[f['url'] for f in m['files']]
def key(u): return u.split('updated_date=')[1].replace('/','_').replace('.parquet','')
Q="""SELECT CAST(regexp_extract(id,'(\\d+)$') AS BIGINT) AS award_id, CAST(regexp_extract(funder.id,'(\\d+)$') AS BIGINT) AS funder_id, funder.display_name AS funder_name, amount, currency, funding_type, funder_scheme, provenance,
  start_year, end_year, funded_outputs_count, list_transform(funded_outputs, x -> CAST(regexp_extract(x,'(\\d+)$') AS BIGINT)) AS funded_wids,
  CAST(regexp_extract(primary_topic.id,'(\\d+)$') AS INTEGER) AS topic, primary_topic.score AS topic_score, CAST(regexp_extract(primary_topic.subfield.id,'(\\d+)$') AS INTEGER) AS subfield,
  institution_awarded[1].country_code AS country, institution_awarded[1].id AS inst_id
FROM src"""
def work(u):
    url=u.replace('s3://openalex/','https://openalex.s3.amazonaws.com/'); k=key(u); out=os.path.join(D,k+'.parquet')
    if os.path.exists(out): return (k,0,'skip')
    for attempt in range(6):
        try:
            con=duckdb.connect(); con.execute("LOAD httpfs; SET threads=4; SET http_retries=6; SET http_retry_wait_ms=3000; SET http_timeout=900000; SET memory_limit='4GB';")
            con.execute(f"CREATE VIEW src AS SELECT * FROM read_parquet('{url}')"); t=time.time()
            con.execute(f"COPY ({Q}) TO '{out}.tmp' (FORMAT PARQUET, COMPRESSION ZSTD)"); os.replace(out+'.tmp',out)
            n=con.execute(f"SELECT count(*) FROM '{out}'").fetchone()[0]; con.close(); return (k,n,f'{time.time()-t:.0f}s')
        except Exception as e:
            err=str(e)[:150]; time.sleep(5+10*attempt)
            try: con.close()
            except: pass
    return (k,-1,err)
random.shuffle(files); t0=time.time()
with cf.ThreadPoolExecutor(8) as ex:
    for i,(k,n,info) in enumerate(ex.map(work,files),1): print(f'{i}/{len(files)} {k} rows={n} {info} elapsed={time.time()-t0:.0f}s',flush=True)
print('finished')
