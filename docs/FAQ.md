# FAQ

Short answers to common questions about this repository. Numbers refer to the original run unless a rerun is named; the three-run comparison is in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Is removing the source fields intentional in LightRAG? Why is it a problem for patents?

It is intentional. Upstream commit [`d3fde609`](https://github.com/HKUDS/LightRAG/commit/d3fde60938c7e14f5e5dff07d4fbd4196e86cbce) (2025-08-18) is titled “refactor: remove file_path and created_at from context, improve token truncation”; before it, `file_path` was part of the context. This repository therefore classes P1 as a design trade-off, not a bug.

The commit does not state a reason. The code comment “Remove file_path and created_at for token calculation” ([v1.5.7 operate.py L5462–L5494](https://github.com/HKUDS/LightRAG/blob/28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c/lightrag/operate.py#L5462-L5494)) suggests token saving, but that is an inference. Citations are designed at chunk level.

Upstream was checked again on 2026-11-15: the newest release `v1.5.8rc1` and `main` at [`c9ef958`](https://github.com/HKUDS/LightRAG/commit/c9ef958b3af62e5bb155cee395089a341342bfac) have the same `operate.py`, and both still remove the two fields ([main L5765–L5797](https://github.com/HKUDS/LightRAG/blob/c9ef958b3af62e5bb155cee395089a341342bfac/lightrag/operate.py#L5765-L5797)). The newest version on PyPI is still 1.5.7.

Patent work needs to know which patent and which claim a statement comes from. Graph retrieval is useful precisely because it returns facts that the retrieved chunks do not cover; when such a fact comes only from the graph and no chunk of its document is in the context, the prompt contains nothing it can be cited to. In Q11, five entities came from the target patent and none of its chunks reached the context. Chunk-level citation itself works: with the text in context, both modes located the claims in 9 of 10 questions.

## Would it still happen with LightRAG's default parameters?

- P1: yes. The code that removes the fields reads no parameter, and the live reproduction uses default-level budgets (40/20/6000/8000/30000); none of its 82 entity lines and 82 relation lines carries `file_path`.
- P2 (Q06 missing one patent's text): not in the same way; Q06 recovered at default-level budgets.
- P4 (truncated extraction) depends on the output cap, which is not set by default; not tested.
- Default gleaning (1), reranking and running without dot's strict `user_prompt` were not tested.

## Would a stronger model do better?

Not tested; only `deepseek-ai/DeepSeek-V4.1-Flash` was used. For P1 the source is absent from the prompt, so no model can read it there. Whether a model then refuses, uses the facts without a source, or attributes them to the wrong patent may well depend on the model; the same holds for P8.

## Can the Q11 misattribution be reproduced?

No. It occurred once, in the original run. In experiment 02 the same frozen context was replayed 9 times (three runs × 3); in the original-context condition the model declined to attribute every time. The full reruns on 2026-11-05 and 2026-11-15 did not repeat it either. It is therefore listed as a limitation, not a main result. Its precondition, a prompt without sources, appeared in every run.

## Could the experiment's own code have failed to pass the sources?

No. Documents were inserted with `ids` = publication number and `file_paths` = `<number>.txt`, and the first line of every document states the number. Every entity and relation in storage and in the `aquery_data` result carries `file_path` and `source_id`. LightRAG was not modified: the installed package's `.py` files are byte-identical to the upstream commit, and the smoke test checks their SHA256.

## What can a sample of 20 patents support?

The mechanism, not a rate. The 20 patents were chosen purposively and share related topics; experiment 03 used 3 patents. The repository makes no error-rate claims; frequencies are stated as “observed n times”.

## Does chunking lose knowledge?

An artificial mid-sentence split does: the complete relation was extracted 3/3 times from the same chunk and 0/3 times from the split, in all three runs. Under the natural 1200/100-token chunking of experiment 01, the genuinely cross-chunk claim 1/27 relation was kept. In experiment 03, F01's difference is not caused by a cut sentence, and the runs disagree (cross-chunk kept the predicate 0/3, 1/3 and 3/3 times), so there is no evidence that crossing a chunk boundary generally loses knowledge.

## The demo calls no embedding API. Where do the query vectors come from, and is the retrieval the same as in the original run?

In v1.5.7 a `mix` query passes three texts to the embedding function in one call: the question, the low-level keywords and the high-level keywords ([operate.py L5198–L5225](https://github.com/HKUDS/LightRAG/blob/28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c/lightrag/operate.py#L5198-L5225)). These three texts of the original Q11 call were embedded once with bge-m3 on 2026-11-15 (one API call; the input is identical to the original log of API call 391, also 99 tokens) and saved in [`q11_query_vectors_bge-m3.json`](../experiments/01_baseline_index_qa/evidence/q11_query_vectors_bge-m3.json). During the demo the embedding function only looks texts up in that file and raises for any other text, so the demo makes no API call. Keywords come from the index's own LLM cache; budgets and `user_prompt` are those of the original call.

Retrieval is identical: 82/82 entities, 82/82 relations and 20/20 chunks overlap. The context has the same 198 lines as the original request, 33 of them in a different order (next question).

With `--replay-answer` the script also calls `aquery_llm` with the original parameters while the LLM function is a stub that raises. The answer returned from the cache is identical to the original API 392 answer. This shows that question, parameters and keywords were the same and that no LLM was called. It does not show that the model would answer the same today (the answer is retrieved, not regenerated), nor that the context is the same (the context is not part of the cache key).

The older stand-in mode `--proxy-vector` uses one entity's stored vector as the query vector; its retrieval overlaps the original Q11 in only 8 of 82 entities, so it shows the mechanism only.

Saved output: [`context_provenance_demo.md`](../experiments/01_baseline_index_qa/results/key_evidence/context_provenance_demo.md).

## Why are 33 context lines in a different order?

The cause cannot be determined from the saved data.

What is established (no API call was made for these checks):

- The difference lies in the relation path: relations retrieved with the high-level keyword vector, and the entities derived from them. In the original run, some relations that are adjacent in similarity rank appear in swapped order (ranks 5/6, 16/17 and 36/37), with similarity gaps of up to 7×10⁻⁴. Because the entity and relation lists are interleaved when they are merged, these swaps move other lines as well.
- LightRAG v1.5.7 keeps relations in vector-search order (“Relations maintain vector search order (sorted by similarity)”, `_get_edge_data` in `operate.py`), so the swaps mean that the original similarity order differed.
- Ruled out: different line content (the sets are identical); reordering while the text is assembled (the structured result is already ordered differently); reversed relation direction (all 82 match); the float16 and float32 copies of the stored vectors; a later change of the relation vectors (every relation record was written between 14:28 and 14:39 UTC on 2026-10-29, before the Q11 call at 14:52); small numerical differences in the question vector (the recomputed question vector reproduces the chunk similarities recorded in the original run to within 2×10⁻⁵, and random perturbations of that size leave the 33-line difference unchanged).

What cannot be checked: the original run did not save its query vectors, and the high-level keyword vector, which ranks the relations, left no trace that could be compared. A different vector at the time of the original call would explain the swaps, but it would have to differ from the recomputed one by far more than the question vector does (similarity changes of up to about 7×10⁻⁴ instead of 2×10⁻⁵). This remains a possibility, not a finding.

## Who ran what?

- The original experiments (2026-10-29/30), including scripts and reports, were designed and run by an AI assistant referred to as dot.
- The second full run (2026-11-05) was run by the repository author on their own machine with dot's adapted scripts.
- The third full run (2026-11-15) was run by Claude Code with the author's authorisation, using this repository's `run.sh live`.
- Curation, the audit ([AUDIT.md](AUDIT.md)), the scoring rubric and the rule-based scores were prepared by Claude Code. Of the 242 judgments per run, 15 were reviewed by Claude Code and then by the author ([HUMAN_REVIEW.md](scoring/HUMAN_REVIEW.md)); the rest are rule-based.

## What would be worth researching next?

See [Research questions](../README.md#research-questions-this-leads-to) in the README: assertion-level provenance that survives context assembly, claims and their dependencies as explicit evidence objects, source-scoped entity merging, and stage-wise error metrics.
