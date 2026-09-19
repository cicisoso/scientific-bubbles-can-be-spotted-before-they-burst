# Scientific bubbles: do research booms end in crashes? (research plan, 2026-09-19)

## Question
Financial manias have a recognisable shape: faster-than-exponential growth fed by newcomers, then a crash. Research topics also boom (graphene, blockchain, Zika, COVID-19, large language models). Nobody has measured, across all of science, how many booms end in crashes, what distinguishes a bubble from a boom that lasts, whether crashes can be anticipated, and what happens afterwards to the literature and to the people who joined. We treat the 4,516 OpenAlex topics as 4,516 assets and their annual output 1980-2025 as prices.

## Data (all on disk; awards downloaded 2026-09-19)
OpenAlex snapshot 2026-06-26 core corpus: topic x year counts (planck build); FWCI, retraction flag, team size; authorships with career start (new scientists, newcomers to a topic); references (within-topic citation share, citations received by year); second-pass metadata (source/journal, DOI, OA, country); awards entity (19 M awards with topic, funder, amount, start year, funded outputs).

## Units and series
Topic x year, 1980-2025. Primary series: annual number of research articles and reviews in the 'stable core' (DOI-bearing works in journal sources), expressed as the topic's share of all such works in the year (removes index-wide growth and coverage waves). Robustness: raw counts; all work types; distinct authors instead of papers; citations received.

## Coverage artefacts (the main threat)
OpenAlex coverage grows in waves (publisher backfiles, proceedings, non-English journals); junk topics collect misclassified records. Rules: (i) a boom requires at least 300 stable-core papers at the peak, at least 20 distinct sources in the peak year, and a top-source share of at most 25%; (ii) a crash must be visible in papers and in distinct authors; (iii) topics whose peak coincides with an index-wide jump in their field are checked against the field's coverage series; (iv) results are repeated on DOI-bearing journal articles only and on citations received.

## Episodes
Boom peak: year t with s_t maximal within +-5 years and run-up R = s_t / min(s_{t-5..t-1}) >= 2 (share doubled within five years). Outcome over the five years after the peak: drawdown D = 1 - min(s_{t+1..t+5})/s_t; crash if D >= 0.4 (sensitivity 0.3, 0.5; seven-year window); soft landing otherwise. Peaks after 2020 are censored (ongoing booms). Severity as continuous drawdown; time to trough.

## Ex-ante signatures (measured in the three years before the peak)
Growth acceleration (convexity of log share; faster-than-exponential growth); newcomer share (authors publishing in the topic for the first time; authors in their first two years of career); quality dilution (share of papers with FWCI < 0.25; mean FWCI; share uncited); insularity (share of references within the topic; share of citations received from within the topic); entry of new sources and new countries (top-country share, China share); funding inflow (awards starting in the year with the topic; funded papers); review share; team size. Log-periodic power-law (LPPL) fits as a secondary early-warning test with fixed parameter ranges.

## Analyses
1. Bubble chronicle: all booms 1985-2020, crash rate with CI, by decade and domain; largest examples (COVID-19, Zika, Ebola, H1N1, SARS, high-Tc superconductors, fullerenes, graphene, blockchain, deep learning ...).
2. Anatomy: event-time profiles (peak-relative years -5..+5) of each signature for crash vs soft-landing booms.
3. Prediction: logistic models of crash on ex-ante signatures (standardised; field and decade fixed effects); out-of-sample AUC (train on peaks <= 2008, test 2009-2020); LPPL early warning two years before the peak.
4. Aftermath: citations received after the crash (does knowledge persist?), retraction rates of boom-era papers vs baseline (do bubbles attract fraud?), what happens to boom-era entrants (exit from science, migration to other topics) relative to matched entrants into soft-landing topics.
5. Ongoing booms (2021-2025): where they stand on the signatures (LLMs, AI in health, ...).

## Hypotheses (before results)
H1 a substantial minority of booms end in crashes; H2 crash booms show faster-than-exponential growth, higher newcomer shares and stronger quality dilution before the peak; H3 boom-era papers in crash topics are retracted more often; H4 citations to crash topics persist longer than production; H5 boom-era entrants to crash topics leave science more often.

## Figures
F1 chronicle (examples, spaghetti of post-peak paths, crash rate by decade/domain); F2 anatomy (event-time signatures); F3 prediction (odds ratios, ROC, LPPL); F4 aftermath (citations, retractions, people); F5 ongoing booms.
