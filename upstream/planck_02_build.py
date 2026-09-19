"""Build the analysis tables from the extracted OpenAlex parts (run after 01_extract.py has finished).
Outputs (data/build/):
  works.parquet          one row per core work: wid, year, type, topic, subfield, field, domain, n_auth, n_refs, cited_by_count, fwci, pct_min, language, has_pmid, is_retracted
  author_first.parquet   aid, y0 (first publication year anywhere), ylast, n_works, n_orcid
  refs/cyear=YYYY/       citing wid, cited wid, cited year, cited subfield, cited topic (only citing works with a year)
  auth/year=YYYY/        wid, aid, pos, position, has_orcid, n_auth, subfield, field, type, y0
  subfields.csv / fields.csv  names (from the topics entity)
Usage: python 02_build.py [step]   steps: works, first, refs, auth, names, all (default all)."""
import os, sys, time, duckdb, json, urllib.request
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OA=os.path.join(ROOT,'data','oa'); B=os.environ.get('PLANCK_BUILD') or os.path.join(ROOT,'data','build'); OA=os.environ.get('PLANCK_OA') or OA
os.makedirs(B,exist_ok=True)
step=sys.argv[1] if len(sys.argv)>1 else 'all'
con=duckdb.connect(); con.execute(f"SET threads=16; SET memory_limit='100GB'; SET temp_directory='{os.path.join(B,'tmp','duck_'+str(os.getpid()))}'; SET preserve_insertion_order=false;")
def log(*a): print(time.strftime('%H:%M:%S'),*a,flush=True)
t0=time.time()
if step in ('works','all'):
    log('works'); con.execute(f"""COPY (SELECT * FROM read_parquet('{OA}/core/*.parquet')) TO '{B}/works.parquet' (FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 1000000)""")
    log(con.execute(f"SELECT count(*), count(year), min(year), max(year) FROM '{B}/works.parquet'").fetchall(), f'{time.time()-t0:.0f}s')
if step in ('first','all'):
    log('author_first')
    con.execute(f"""COPY (
      SELECT a.aid, min(w.year) AS y0, max(w.year) AS ylast, count(*) AS n_works, sum(CASE WHEN a.has_orcid THEN 1 ELSE 0 END) AS n_orcid
      FROM read_parquet('{OA}/auth/*.parquet') a JOIN '{B}/works.parquet' w USING (wid)
      WHERE w.year IS NOT NULL AND a.aid <> 9999999999 AND a.aid <> 5317838346
      GROUP BY a.aid) TO '{B}/author_first.parquet' (FORMAT PARQUET, COMPRESSION ZSTD)""")
    log(con.execute(f"SELECT count(*), avg(n_works), quantile_cont(y0,[0.1,0.5,0.9]) FROM '{B}/author_first.parquet'").fetchall(), f'{time.time()-t0:.0f}s')
if step in ('refs','all'):
    log('refs (partitioned by citing year)')
    con.execute(f"""COPY (
      SELECT r.wid, r.cited, w.year AS cyear, c.year AS ryear, c.subfield AS rsub, c.topic AS rtopic
      FROM read_parquet('{OA}/refs/*.parquet') r
      JOIN '{B}/works.parquet' w ON w.wid = r.wid
      LEFT JOIN '{B}/works.parquet' c ON c.wid = r.cited
      WHERE w.year IS NOT NULL) TO '{B}/refs' (FORMAT PARQUET, COMPRESSION ZSTD, PARTITION_BY (cyear), OVERWRITE_OR_IGNORE, ROW_GROUP_SIZE 2000000)""")
    log('refs done', f'{time.time()-t0:.0f}s')
if step in ('auth','all'):
    log('auth (partitioned by year)')
    con.execute(f"""COPY (
      SELECT a.wid, a.aid, a.pos, a.position, a.has_orcid, w.n_auth, w.subfield, w.field, w.type, w.year, f.y0
      FROM read_parquet('{OA}/auth/*.parquet') a
      JOIN '{B}/works.parquet' w USING (wid)
      LEFT JOIN '{B}/author_first.parquet' f USING (aid)
      WHERE w.year IS NOT NULL) TO '{B}/auth' (FORMAT PARQUET, COMPRESSION ZSTD, PARTITION_BY (year), OVERWRITE_OR_IGNORE, ROW_GROUP_SIZE 2000000)""")
    log('auth done', f'{time.time()-t0:.0f}s')
if step in ('names','all'):
    log('names')
    rows=[]
    for ent in ('subfields','fields','domains','topics'):
        url=f'https://api.openalex.org/{ent}?per-page=200&select=id,display_name'
        if ent=='topics':
            # topics: 4,516 -> paginate with cursor
            cur='*'; out=[]
            while cur:
                d=json.load(urllib.request.urlopen(f'https://api.openalex.org/topics?per-page=200&cursor={cur}&select=id,display_name,subfield,field,domain'))
                out+=d['results']; cur=d['meta'].get('next_cursor')
            with open(os.path.join(B,'topics.json'),'w') as f: json.dump(out,f)
        else:
            cur="*"; out=[]
            while cur:
                d=json.load(urllib.request.urlopen(f"https://api.openalex.org/{ent}?per-page=200&cursor={cur}&select=id,display_name")); out+=d["results"]; cur=d["meta"].get("next_cursor")
            with open(os.path.join(B,f'{ent}.json'),'w') as f: json.dump(out,f)
        log(ent, len(out))
log('finished', f'{time.time()-t0:.0f}s')
