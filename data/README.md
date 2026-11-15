# data/ — the 20 patents used in the experiments

## Source and licence

- Dataset: [lj408/Dis2Pat](https://huggingface.co/datasets/lj408/Dis2Pat) (Hugging Face), split `train`, revision `eda4a497291e9e8b898639881c34f158524732fc` (the `x-revision` response header at fetch time, see `dis2pat_train_rows_0000.source.json`), fetched 2026-10-29 13:12 UTC.
- Licence: the dataset card states **CC-BY-SA-4.0** (checked through the Hugging Face API on 2026-11-12). This directory redistributes only the 20 records actually used and the files derived from them, shared alike under CC-BY-SA-4.0 and attributed to the Dis2Pat dataset authors (see [LICENSE.md](LICENSE.md)). The patent texts themselves are US patent publications.
- Not in git: the raw response of the first 100 rows downloaded at fetch time (6.4 MB, including 80 unused records) and 20 Google Patents pages used for checking (about 8 MB). Both can be fetched again with the scripts below.

## How the 20 were chosen (round 1, 2026-10-29, no LLM call)

1. `round1/scripts/data_fetch.py`: fetches the first 100 rows of `train` through the Hugging Face Dataset Viewer (one request).
2. A **purposive selection** by dot (the AI assistant) after reading the titles, not a random sample: 20 patents on related topics (information retrieval, recommendation, contextual ranking, data/relation indexing) were picked from these 100 rows, so that same-name entities across patents and comparison questions had a chance to occur. One publication number appeared twice in the batch and was taken once. The selected row numbers are fixed in `round1/scripts/data_validate.py` (`selected=[8,10,21,…,88]`).
3. `round1/scripts/data_validate.py` checks every patent: publication number of the form `US…B1/B2`; title, abstract and claims non-empty and not truncated by the Viewer; claims numbered consecutively from 1. It then writes:
   - `documents/<number>.txt`: the text inserted into LightRAG, with the four sections `Publication number` / `Title` / `ABSTRACT` / `CLAIMS`; **the text is not rewritten**, only section labels are added;
   - `claims/<number>.json`: the claims split by number (with their character spans in the original claims field), used for writing and checking questions;
   - `selected_raw/<number>.json`: the 20 original Dis2Pat records (including the specification, which was not indexed);
   - `manifest.json` / `manifest.csv`: list, row numbers, lengths, document SHA256; `selected_patents.json`: the 20 original records in one file (read by experiment 01's scripts).
4. **Only title, abstract and all claims were indexed**; neither the full specification nor the dataset's generated disclosure was indexed (to limit time and cost, see `exclusion_reason` in `manifest.json`). The 20 patents have 438 claims; chunking gives 42,087 tokens → 48 chunks (source: `round1/results/chunk_probe.json`).
5. `round1/scripts/data_verify_sources.py` fetches the Google Patents page of every patent for comparison. Result in `source_verification.json`: abstracts agree 20/20, claims agree 19/20 after whitespace normalisation.
6. Known data issues (`data_quality_flags.json`; the text was not changed; questions avoid them):
   - US8509827B2: the parent claim numbers of claims 2/3 are already missing on the source page;
   - US9218390B2: claims 10/11 contain garbled formula symbols.

`round1/` also contains the questions and the pre-check: `round1/results/questions.json` (Q01–Q10 with their evidence passages), `question_chunk_mapping.json` (which chunk holds each question's evidence), `natural_cross_chunk_candidates.json` (candidate claim dependencies that cross chunks), `round1/evidence/question_ground_truth.txt` (the passages per question). The round-1 report: [`../reports/translated/00_data_and_chunk_probe_report_en.md`](../reports/translated/00_data_and_chunk_probe_report_en.md) (English translation; the Chinese original is in `reports/original/`).

## Fetching the raw data again (optional; no LLM call, public web pages only)

```bash
python data/round1/scripts/data_fetch.py          # downloads the first 100 rows again → data/dis2pat_train_rows_0000.json (ignored by git)
python data/round1/scripts/data_validate.py       # regenerates documents/ claims/ selected_raw/ manifest.* from the raw rows
git diff --stat data/                             # expected: no change (unless the dataset's revision has changed upstream)
python data/round1/scripts/data_verify_sources.py # fetches the Google Patents pages again → data/source_checks/ (ignored by git)
```

Compared with dot's originals, the scripts in `round1/` only changed paths, see [`round1/PATH_CHANGES.diff`](round1/PATH_CHANGES.diff). They contain Chinese comments and a Chinese report template; they are kept as they were.

## The 20 patents

| Publication number | Title | Dis2Pat row | Claims |
|---|---|---|---|
| US9298709B2 | Computer system to visualize data from an IP rights database | 8 | 17 |
| US8509827B2 | Methods and apparatus of context-data acquisition and ranking | 10 | 26 |
| US9514753B2 | Speaker identification using hash-based indexing | 21 | 20 |
| US9304738B1 | Systems and methods for selecting content using weighted terms | 22 | 19 |
| US9118735B1 | Finding people using social networks | 25 | 21 |
| US8095432B1 | Recommendation engine for social networks | 28 | 24 |
| US8880423B2 | Inventory estimation for search retargeting | 29 | 17 |
| US8917913B2 | Searching with face recognition and social networking profiles | 37 | 17 |
| US9514120B1 | Classification of a string as a typographical error based on feedback | 49 | 20 |
| US7991757B2 | System for obtaining recommendations from multiple recommenders | 50 | 28 |
| US8069128B2 | Real-time ad-hoc spam filtering of email | 52 | 20 |
| US9374411B1 | Content recommendations using deep data | 54 | 25 |
| US9218390B2 | Query parser derivation computing device and method for making a query parser for parsing unstructured search queries | 60 | 18 |
| US7756837B2 | Methods and apparatus for searching backup data based on content and attributes | 69 | 49 |
| US8719408B2 | Automated digital media content filtration based on relationship monitoring | 72 | 24 |
| US8655901B1 | Translation-based query pattern mining | 73 | 15 |
| US10867122B1 | Contextually relevant knowledge panels in an application environment | 77 | 15 |
| US11423041B2 | Maintaining data lineage to detect data events | 84 | 20 |
| US10778629B2 | Systems and methods for collation, translation, and analysis of passively created digital interaction and relationship data | 85 | 21 |
| US9589231B2 | Social medical network for diagnosis assistance | 88 | 22 |
