# S6 "Does science have bubbles" — status (19 September 2026)

Submission package: `submission/science/` (Science Research Article). Title: "Scientific bubbles can be spotted before they burst".

Pipeline (all scripts in `scripts/`, run in order): 00_awards (OpenAlex awards download) → 01_counts, 01b_sources, 03_topic_measures (topic-year tables in data/build) → 02b_constant_source (booms in the constant-source panel; main) → 02c_venues (venue concentration of the run-up; names via the OpenAlex API) → 02d_fixed_weight (fixed-source-weight index) → 04_features (per-boom signatures, event-time panels, standardized retractions) → 05_entrants → 06_null → 07_stats (summary.json, analysis/*.csv) → fig/fig1-5.py, fig/sm_figs.py → paper/make_numbers.py, make_bib.py, make_sm_tables.py → 08_package.

Headline numbers: 878 booms in 832 topics (1980-2025); 350 evaluable (peak <= 2020); 145 crashes (41%, CI 36-47%); median drawdown 36%; only 23% fall below the pre-boom level; null model (shuffled growth) gives more reversals than observed at every run-up; pre-peak signatures (low-FWCI share 70 vs 53%, uncited 52 vs 38%, grants 0.20 vs 0.69 per 100, reviews 0.4 vs 1.6%, team 2.8 vs 3.4, venue concentration 61 vs 34%); joint logit OR/SD venue 2.75, low-FWCI 1.71, accel 1.61, run-up 5.5; out-of-sample AUC 0.87 (train <= 2008 n=219, test 2009-2020 n=131), calibration 14/35/91%; retractions RW-confirmed 4.3x expected in boom-era papers (crash 6.2x, soft 2.2x); attention still rising at t+5 in 83% of crashed booms; entrants to crashed booms 66.6% still publishing at t+5 vs 74.3%; 528 booms in progress, median p 18%, COVID topics 0.8-1.0, AI in healthcare 0.26.

Known caveats: 29 booms of 2011-2014 are carried by Trans Tech Publications proceedings serials (66% crash); results hold excluding all 58 proceedings-led booms (crash 40%, AUC 0.83). Venue concentration is treated as a feature. Awards coverage is uneven across decades.

Before upload: funding statement; AAAS competing-interests forms; Zenodo deposit; confirm reviewer suggestions.
