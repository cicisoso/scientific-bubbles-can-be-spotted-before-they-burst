# Scientific bubbles can be spotted before they burst

Code, derived data and figures for the study of booms and crashes in the share of the scientific literature held by
research topics, 1980–2025, built on the OpenAlex snapshot of 26 June 2026 (318 million works, 4,516 topics).

Hao Liu (corresponding author, liuhao@zfc.edu.cn), Xiaojie Zong, Jie Chen, Jianyu Xiong.
School of Information Technology, Zhejiang Financial College, Hangzhou, China.

## What the study does

* A **boom** is a year in which a topic's share of the papers published in a *constant panel of journals* (journals with at
  least 20 papers both five years before and five years after that year) reaches a local maximum after rising at least
  1.5-fold from its minimum of the preceding five years, with at least 200 panel papers. A **crash** is a fall of at least
  40% from the peak share within the following five years. The constant-source panel is the "same-store" measure of
  retailing applied to science: a boom can arise only from the allocation of pages within journals that were already
  there, not from journals entering or leaving the index.
* 878 booms in 832 topics; 350 peaked in 2020 or earlier and can be followed for five years; 145 of them (41%) crashed.
* A **null model** shuffles each topic's annual log growth rates in time and reapplies the detection rules; observed
  reversal rates are below the null at every run-up.
* **Pre-peak signatures** (three years before the peak) separate booms that crashed from booms that did not: share of
  low-impact and never-cited papers, linked grants, reviews, team size, newcomers, growth acceleration, and the share
  of the run-up carried by the three largest venues. A logistic model fitted to booms peaking up to 2008 forecasts the
  crashes of 2009–2020 with an out-of-sample AUC of 0.87.
* **Costs**: retractions relative to the field-year expectation (OpenAlex flags and Retraction Watch-confirmed),
  citations after the peak, and the fate of the scientists who entered a topic during the run-up.
* **Booms in progress** (peaks 2021–2025) are scored with the fitted model.

## Repository layout

| Path | Contents |
|---|---|
| `scripts/` | The pipeline, numbered in running order (see below) |
| `upstream/` | The OpenAlex extraction and build scripts of the two companion projects that produce the work-level inputs |
| `data/build/` | Topic × year tables (207,288 topic-years) and the constant-source series: the inputs of steps 04–07 (38 MB, included) |
| `data/names/` | OpenAlex topic, subfield, field and domain names |
| `results/` | Boom catalogues (`episodes_cs.parquet`, `evaluable.parquet`, `features.parquet`), event-time panels, entrants, null model, venue concentration, fixed-weight index, `summary.json`, and `analysis/*.csv` (every number in the paper) |
| `fig/` | Figure scripts (`fig1.py`–`fig5.py`, `sm_figs.py`, shared style `figstyle.py`) and their outputs in `fig/out/` (PDF, PNG, SVG, alignment and collision audit JSON) |
| `paper/` | LaTeX skeleton (`preamble.tex`, `main.tex`, `supplement.tex`) and the builders that turn `results/` into the manuscript's numbers (`make_numbers.py` → `macros.tex`), reference list (`make_bib.py`) and supplementary tables (`make_sm_tables.py`); `wordcount.py` |
| `lit/` | `refs.py` (Crossref-verified reference builder), `references.bib`, `verified.json` |
| `submission/science/source_data/` | Data S1–S5: source data for every figure (xlsx) and `summary.json` |
| `submission/science/figures/`, `supplementary_figures/` | Fig. 1–5 and figs. S1–S8 |
| `docs/` | Research plan, status notes, format requirements |

The manuscript text (`paper/sections/`), the compiled manuscript and the cover letter are not in this repository; they
will be added when the authors post a preprint.

## Pipeline

Steps 00–03 need the work-level extractions described in `upstream/README.md` (about 230 GB transferred from the public
OpenAlex bucket; roughly ten hours). Steps 04–08 run from the files included here in minutes.

| Step | Script | Input | Output |
|---|---|---|---|
| 00 | `00_awards.py` | OpenAlex awards entity (S3 over HTTPS, DuckDB httpfs) | `data/awards/*.parquet` (409 MB, not included; re-downloadable) |
| 01 | `01_counts.py`, `01b_sources.py` | planck build, llmcite metadata | `data/build/topic_year.parquet`, `topic_year_sources.parquet`, `topic_year_authors.parquet` |
| 02 | `02b_constant_source.py` (main), `02_episodes.py` (raw and stable-core detection, robustness) | work-level tables | `results/episodes_cs.parquet`, `data/build/cs_series.parquet`; `results/episodes_*.parquet` |
| 02c | `02c_venues.py` | work-level tables + OpenAlex API for source names | `results/venues.parquet`, `results/venue_names.csv` |
| 02d | `02d_fixed_weight.py` | work-level tables | `results/fixed_weight.parquet` |
| 03 | `03_topic_measures.py` | planck build, llmcite metadata | `data/build/topic_year_{newcomers,refs,cites,countries}.parquet` |
| 04 | `04_features.py` | `data/build/*`, `data/awards/*`, `results/episodes_cs.parquet` | `results/features.parquet`, `results/eventtime.parquet` |
| 05 | `05_entrants.py` | planck authorship tables | `results/entrants.parquet` |
| 06 | `06_null.py` | `data/build/topic_year*.parquet` | `results/null_model.csv` |
| 07 | `07_stats.py` | `results/*` | `results/summary.json`, `results/analysis/*.csv` |
| figures | `fig/fig1.py` … `fig/fig5.py`, `fig/sm_figs.py` | `results/*`, `data/build/cs_series.parquet` | `fig/out/*` |
| paper | `paper/make_numbers.py`, `make_bib.py`, `make_sm_tables.py`; `latexmk -pdf main.tex supplement.tex` | `results/*`, `lit/*` | `paper/macros.tex`, `references*.tex`, `sections/sm_tables.tex` |
| 08 | `08_package.py` | `paper/`, `fig/out/`, `results/` | `submission/science/` |

Retraction Watch-confirmed retractions (`data/build/retracted_flags.parquet`, `topic_year_rw.parquet`) were matched by DOI
against the Retraction Watch database distributed by Crossref (https://api.labs.crossref.org/data/retractionwatch).

To reproduce the statistics and figures from the included files:

```bash
pip install -r requirements.txt
python3 scripts/07_stats.py          # results/summary.json and results/analysis/
cd fig && for f in fig1 fig2 fig3 fig4 fig5 sm_figs; do python3 $f.py; done
```

`fig/figstyle.py` runs a render-time panel-alignment gate when the `audit_panel_alignment` module of the nature-figure QA
scripts is importable and skips it with a warning otherwise; the exported figures are identical either way.

## Data sources

* OpenAlex snapshot of 26 June 2026 (CC0), https://openalex.org — works, sources, topics, awards.
* The Retraction Watch Database (The Center for Scientific Integrity), distributed by Crossref.

## License

Code: MIT. Derived data: CC0 1.0 (see `LICENSE`).
