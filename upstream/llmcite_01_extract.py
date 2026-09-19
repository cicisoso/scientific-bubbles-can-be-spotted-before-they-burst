"""Second pass over the OpenAlex works snapshot (parquet on public S3 over HTTPS) for the LLM-citation study.
For every part file writes three parquet files under data/oa2/{meta,country,abs}/ (skips parts already done; safe to re-run):
  meta:    one row per core work: wid, year, type, source id/type, is_oa, has_doi, title length, citation_normalized_percentile,
           counts_by_year (years[], counts[]), cited_by_count, referenced_works_count, has_abstract, language
  country: one row per authorship x country: wid, pos, position, is_corresponding, country
  abs:     abstract_inverted_index (raw JSON string) for core articles/reviews published 2019-2025
Usage: python 01_extract.py [n_workers] [max_files]"""
import json, os, sys, time, duckdb, concurrent.futures as cf, random
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D=os.path.join(ROOT,'data','oa2')
NW=int(sys.argv[1]) if len(sys.argv)>1 else 6; MAXF=int(sys.argv[2]) if len(sys.argv)>2 else None
m=json.load(open(os.path.join(D,'works_manifest.json'))); files=[f['url'] for f in m['files']]
def key(u): return u.split('updated_date=')[1].replace('/','_').replace('.parquet','')
TABLES=('meta','country','abs')
def done(u): return all(os.path.exists(os.path.join(D,t,key(u)+'.parquet')) for t in TABLES)
FILT=os.environ.get('PART_FILTER'); todo=[u for u in files if not done(u) and (FILT is None or FILT in u)]
random.Random(int(os.environ.get('SEED','20260919'))).shuffle(todo)
if MAXF: todo=todo[:MAXF]
print(f'{len(files)} parts, {len(todo)} to do', flush=True)
Q_META="""SELECT CAST(regexp_extract(id,'(\\d+)$') AS BIGINT) AS wid, publication_year AS year, type,
  CAST(regexp_extract(primary_location."source".id,'(\\d+)$') AS BIGINT) AS sid, primary_location."source"."type" AS stype,
  open_access.is_oa AS is_oa, (ids['doi'] IS NOT NULL) AS has_doi, length(title) AS title_chars, len(string_split(title,' ')) AS title_words,
  citation_normalized_percentile."value" AS cnp, citation_normalized_percentile.is_in_top_1_percent AS top1, citation_normalized_percentile.is_in_top_10_percent AS top10,
  list_transform(counts_by_year, x -> x."year") AS cby_years, list_transform(counts_by_year, x -> x.cited_by_count) AS cby_counts,
  cited_by_count, referenced_works_count AS n_refs, (abstract_inverted_index IS NOT NULL) AS has_abstract, language
FROM src WHERE NOT is_xpac"""
Q_COUNTRY="""SELECT CAST(regexp_extract(id,'(\\d+)$') AS BIGINT) AS wid, CAST(pos AS SMALLINT) AS pos, a.author_position AS position, a.is_corresponding, c AS country
FROM (SELECT id, unnest(authorships) AS a, unnest(generate_series(1, len(authorships))) AS pos FROM src WHERE NOT is_xpac AND authors_count > 0), unnest(a.countries) AS t(c)"""
Q_ABS="""SELECT CAST(regexp_extract(id,'(\\d+)$') AS BIGINT) AS wid, publication_year AS year, abstract_inverted_index AS abs
FROM src WHERE NOT is_xpac AND publication_year BETWEEN 2019 AND 2025 AND type IN ('article','review') AND abstract_inverted_index IS NOT NULL"""
def work(u):
    url=u.replace('s3://openalex/','https://openalex.s3.amazonaws.com/'); k=key(u)
    if done(u): return (k,0,0,'skip')
    err='?'
    for attempt in range(6):
        try:
            con=duckdb.connect(); con.execute("LOAD httpfs; SET threads=4; SET http_retries=6; SET http_retry_wait_ms=3000; SET http_timeout=900000; SET memory_limit='5GB';")
            con.execute(f"CREATE VIEW src AS SELECT * FROM read_parquet('{url}')")
            t=time.time()
            for tbl,q in (('meta',Q_META),('country',Q_COUNTRY),('abs',Q_ABS)):
                out=os.path.join(D,tbl,k+'.parquet')
                if os.path.exists(out): continue
                tmp=out+'.tmp'; con.execute(f"COPY ({q}) TO '{tmp}' (FORMAT PARQUET, COMPRESSION ZSTD)"); os.replace(tmp,out)
            n=con.execute(f"SELECT count(*) FROM read_parquet('{os.path.join(D,'meta',k+'.parquet')}')").fetchone()[0]
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
