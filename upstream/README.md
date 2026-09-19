# Upstream extraction scripts

The topic-year tables in `data/build/` were computed from two extractions of the OpenAlex snapshot of 26 June 2026
(parquet files on the public OpenAlex S3 bucket, read over HTTPS with DuckDB's httpfs extension). The scripts that
made them live in two companion projects and are copied here unchanged so that the whole chain is documented:

| File | Companion project | What it produces |
|---|---|---|
| `planck_01_extract.py` | planck (`~/research/sos/planck`) | `data/oa/{core,refs,auth}`: one parquet part per snapshot part with the work-level columns (id, year, type, topic, authors, references, FWCI, retraction flag) |
| `planck_02_build.py` | planck | `data/build/works.parquet`, `refs/cyear=YYYY`, `auth/year=YYYY`, `author_first.parquet` and the topic/subfield/field/domain name tables (`data/names/` here) |
| `llmcite_01_extract.py` | llmcite (`~/research/sos/llmcite`) | `data/oa2/meta` (source id and type, DOI flag, language, citation counts by year) and `data/oa2/country` for every core work |

The scripts in `scripts/01_counts.py`, `01b_sources.py`, `02b_constant_source.py`, `02c_venues.py`, `02d_fixed_weight.py`,
`03_topic_measures.py`, `04_features.py` and `05_entrants.py` expect these builds at `~/research/sos/planck/data/build` and
`~/research/sos/llmcite/data/oa2` (paths set at the top of each script). The full extraction transfers roughly 230 GB and
takes about ten hours on a 10 MB/s link; the outputs occupy about 60 GB.
