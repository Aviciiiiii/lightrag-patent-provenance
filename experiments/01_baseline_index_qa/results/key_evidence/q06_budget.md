# Q06 (cross-document comparison): baseline budget vs. extended budget

| | baseline `full_Q06_mix.json` | extended budget `supplement_budget_Q06_mix.json` |
|---|---|---|
| parameters | top_k=12, chunk_top_k=8, entity/relation 2000/2000, total 8000 | top_k=40, chunk_top_k=20, entity/relation 6000/8000, total 30000 (the order of LightRAG's defaults) |
| context chunks from US7991757B2 | 0 | 2 |
| start of answer | I do not have enough information to compare US7991757B2 with US8095432B1, because the provided context contains no document chunks or knowledge-graph facts about US7991757B2. Its selection or ranking approach, claims, an… | ## How Each Patent Selects or Ranks Recommendations **US7991757B2** ranks/selects by combining scores from multiple external recommenders. Claim 17 recites: "normalizing scores provided by the recommenders to produce nor… |

Vector ranks of the two US7991757B2 chunks under the same embedding (`evidence/retrieval_rank_probe.json`): Q06 [(9, 'US7991757B2-chunk-001'), (11, 'US7991757B2-chunk-000')]; Q11 [(29, 'US7991757B2-chunk-000'), (30, 'US7991757B2-chunk-001')]. Baseline chunk_top_k=8, extended 20.
