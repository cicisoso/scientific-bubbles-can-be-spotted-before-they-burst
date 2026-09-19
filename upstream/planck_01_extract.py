"""Stream the OpenAlex works snapshot (parquet, public S3 over HTTPS) and keep only the columns this study needs.
For every part file writes three parquet files under data/oa/{core,refs,auth}/ (skips parts already done; safe to re-run).
Usage: python 01_extract.py [n_workers] [max_files]  (workers default 6)."""
import json, os, sys, time, duckdb, concurrent.futures as cf, random
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D=os.path.join(ROOT,'data','oa')
NW=int(sys.argv[1]) if len(sys.argv)>1 else 6; MAXF=int(sys.argv[2]) if len(sys.argv)>2 else None
m=json.load(open(os.path.join(D,'works_manifest.json')))
files=[f['url'] for f in m['files']]
def key(u): return u.split('updated_date=')[1].replace('/','_').replace('.parquet','')
def done(u): return all(os.path.exists(os.path.join(D,t,key(u)+'.parquet')) for t in ('core','refs','auth'))
FILT=os.environ.get('PART_FILTER'); todo=[u for u in files if not done(u) and (FILT is None or FILT in u)]
random.Random(int(os.environ.get('SEED','20260918'))).shuffle(todo)
if MAXF: todo=todo[:MAXF]
print(f'{len(files)} parts, {len(todo)} to do', flush=True)
Q_CORE="""SELECT CAST(regexp_extract(id,'(\\d+)$') AS BIGINT) AS wid, publication_year AS year, type,
  CAST(regexp_extract(primary_topic.id,'(\\d+)$') AS INTEGER) AS topic,
  CAST(regexp_extract(primary_topic.subfield.id,'(\\d+)$') AS INTEGER) AS subfield,
  CAST(regexp_extract(primary_topic.field.id,'(\\d+)$') AS INTEGER) AS field,
  CAST(regexp_extract(primary_topic."domain".id,'(\\d+)$') AS INTEGER) AS "domain",
  authors_count AS n_auth, referenced_works_count AS n_refs, cited_by_count, is_retracted, fwci,
  cited_by_percentile_year.min AS pct_min, language, (ids['pmid'] IS NOT NULL) AS has_pmid
FROM src WHERE NOT is_xpac"""
Q_REFS="""SELECT CAST(regexp_extract(id,'(\\d+)$') AS BIGINT) AS wid, CAST(regexp_extract(r,'(\\d+)$') AS BIGINT) AS cited
FROM (SELECT id, unnest(referenced_works) AS r FROM src WHERE NOT is_xpac AND referenced_works_count > 0)"""
Q_AUTH="""SELECT CAST(regexp_extract(id,'(\\d+)$') AS BIGINT) AS wid, CAST(regexp_extract(a.author.id,'(\\d+)$') AS BIGINT) AS aid,
  CAST(pos AS SMALLINT) AS pos, a.author_position AS position, (a.author.orcid IS NOT NULL) AS has_orcid
FROM (SELECT id, unnest(authorships) AS a, unnest(generate_series(1, len(authorships))) AS pos FROM src WHERE NOT is_xpac AND authors_count > 0)"""
def work(u):
    url=u.replace('s3://openalex/','https://openalex.s3.amazonaws.com/'); k=key(u)
    if done(u) or any(os.path.exists(os.path.join(D,t,k+'.parquet.tmp')) for t in ('core','refs','auth')): return (k,0,0,'skip')
    for attempt in range(6):
        try:
            con=duckdb.connect(); con.execute("LOAD httpfs; SET threads=6; SET http_retries=6; SET http_retry_wait_ms=3000; SET http_timeout=900000; SET memory_limit='6GB';")
            con.execute(f"CREATE VIEW src AS SELECT * FROM read_parquet('{url}')")
            t=time.time()
            for tbl,q in (('core',Q_CORE),('refs',Q_REFS),('auth',Q_AUTH)):
                out=os.path.join(D,tbl,k+'.parquet'); tmp=out+'.tmp'
                con.execute(f"COPY ({q}) TO '{tmp}' (FORMAT PARQUET, COMPRESSION ZSTD)")
                os.replace(tmp,out)
            n=con.execute(f"SELECT count(*) FROM read_parquet('{os.path.join(D,'core',k+'.parquet')}')").fetchone()[0]
            con.close(); return (k, n, time.time()-t, attempt)
        except Exception as e:
            err=str(e)[:200]; time.sleep(5+10*attempt+random.random()*5)
            try: con.close()
            except: pass
    return (k, -1, 0, err)
t0=time.time(); ndone=0; nrec=0
with cf.ThreadPoolExecutor(NW) as ex:
    for k,n,dt,info in ex.map(work, todo):
        ndone+=1; nrec+=max(n,0)
        line=f'{ndone}/{len(todo)} {k} rows={n} {dt:.0f}s {info} elapsed={time.time()-t0:.0f}s'
        print(line, flush=True)
        with open(os.path.join(D,'logs','extract.log'),'a') as f: f.write(line+'\n')
print('finished', ndone, 'records', nrec, time.time()-t0)
