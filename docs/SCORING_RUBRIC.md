# Scoring rubric (so that the three runs can be compared directly)

**Scope**: only the judgments that the behavioural conclusions of the README rely on. Structural conclusions (P1 sources removed, and so on) are determined by code and need no scoring.
**Implementation**: [`tools/score_runs.py`](../tools/score_runs.py). Each judgment is first made mechanically by the rule written below; judgments where the rule is uncertain or differs from what is expected are then reviewed. Reviews are stored in `docs/scoring/claude_review_<run>.json` (review by Claude Code) and `docs/scoring/human_review_<run>.json` (human review, i.e. by the author). Output: `docs/scoring/scores_<run>.json`; each row records the rule value, the final value, the review status (`human review` / `Claude Code review` / `rule`), and the evidence file and field.
**Origin**: each rule follows dot's criteria as closely as possible. dot's scoring has two kinds of labels:
- in experiments 01 and 03, “is the answer correct” is a fixed label that dot wrote after reading the answer;
- in experiment 02, the ablation labels are fixed per condition (`evaluate_ablation.py` asserts that a certain sentence occurs in the answer and then assigns the label by condition A/B/C).

Reruns therefore need rules of their own. For the graph predicates of experiment 03, dot used deterministic lexical matching, which is copied here unchanged.

## Agreement with dot's original labels (original run)

Scoring dot's original run with this rubric and comparing item by item with dot's labels: **242 / 242 agree** (2026-11-14, `python tools/score_runs.py original`).

Caveat: the rules were written after reading the original answers, so their agreement on the original run does **not** show that they are as reliable on new answers. After they were written, Claude Code fixed two defects found on the 11-05 run (see “Revision history”); after the fixes the original run still scores 242/242. Therefore every rerun judgment whose rule value differs from the original run (except S10, which is the logged `finish_reason`, not a judgment) was read and reviewed by Claude Code and recorded in `claude_review_<run>.json`; `python tools/score_runs.py <run>` lists these items. A few items where the rule agrees with the original run but Claude Code found the rule wrong after reading the answer are recorded in the same file. The author's review is recorded in `human_review_<run>.json`; it takes precedence over the Claude Code review and the item is marked “reviewed by the author”. The author's review was written in Chinese; the files keep the original (`note_zh`) and an English translation (`note_en`). Record: [`scoring/HUMAN_REVIEW.md`](scoring/HUMAN_REVIEW.md).

## Judgments

| ID | Judgment (boolean) | Rule | Origin (dot's criterion) | README conclusion it supports |
|---|---|---|---|---|
| **S1** | Experiment 01: the answer completes the core task of the question (Q01–Q10, Q11, naive/mix; and the extended-budget Q06, Q11) | (1) no refusal phrase (“do not have enough information” etc.) in the first 260 characters; (2) names every publication number the question asks for; (3) single-patent questions: names every claim number in the question's evidence; cross-document questions: names at least one claim number **within each publication number's own paragraph** (from where the number appears to where another publication number appears, at most 700 characters) | `core_question_completed` / `core_required_fact_correct` in `evaluation_criteria.json`; `full_audit_q01_q05.json`, `full_audit_q06_q11.json`, `supplement_budget_audit.json` | “9/10 in both modes”; P2 (recovers with the larger budget) |
| **S2** | Experiment 01: every required evidence passage of the question appears in the context chunks of the same call | every evidence passage (whitespace-normalised) is a substring of `result.data.chunks[].content` of the same call | `all_required_quotes_retrieved` / `patent_retrieval == all_required_present` | P2, P3 |
| **S3** | Experiment 01: the answer **affirmatively** attributes the target technical facts to another patent | phrases such as “different patent family”, “belongs to another patent” (a match is checked by reading) | `concrete_attribution_failure` in `supplement_budget_audit.json`; `wrong_patent_or_claim_attribution_observed` | P1′ / Q11 misattribution (limitations) |
| **S4** | Experiment 02 ablation: the answer text contains an affirmative misattribution | same as S3 | `positive_wrong_source_assignment_or_exclusion_in_prose` in `ablation_evaluation.json` | P1′ |
| **S5** | Experiment 02 ablation: the registration evidence is correctly attributed to US7991757B2 | a negative statement (US7991757B2 within 60 characters after “not linked / not tied”, or “does not contain any … entity … for US7991757B2”) gives no; otherwise an affirmative statement (“US7991757B2 is referenced only through…”, “referencing US7991757B2”, “evidence relating to that patent”, “Claim 1 of US7991757B2” etc.) gives yes | `correct_document_attribution` | P1′ (0/3 → 3/3) |
| **S6** | Experiment 02 ablation: the claim task is completed with evidence | no opening refusal; the answer (after word-form normalisation) contains the first 60 characters of the key clauses of Claim 1 and Claim 27; and states that 27 depends on 1 | `claim_task_core_complete_and_grounded` | P1′ (the claim text is needed) |
| **S7** | Experiment 02 ablation: citation numbers conflict with the frozen reference list | any `[n] file` in the References differs from `[n]` in the frozen reference list | `reference_ids_match_original_context` (negated) | P9 |
| **S8** | Experiment 02 artificial chunking: the complete relation is kept | after the official parser, there is a relation with Registration Module as an endpoint whose description contains “machine readable descriptions” | `primary_semantic_relation_retained` in `chunk_evaluation.json` (dot's criterion is exactly this phrase) | P5 |
| **S9** | Experiment 03: all target predicates reach the relation records of the merged graph | dot's lexical matchers copied unchanged: F01 `pred()` (case/expert/UMLS), F05 `match()` (P1–P3), F04 `p1_witness/p2_witness` | `evaluate_F01.py`, `evaluate_F05.py`, `evaluate_F04.py` | P5′ |
| **S10** | Experiment 03: an extraction output of the run was truncated | any `finish_reason == length` in the parsed records | `truncated_extraction_ids` / `valid_untruncated_extraction_run` / `untruncated` | P4, P5′ (clean pairs) |
| **S11** | Experiment 03: natural `mix` retrieval returns every kind of target text | for each evidence family of the frozen anchors at least one passage (whitespace-normalised) appears in the chunks of the same call | `both_original_target_quotes_retrieved` / `both_target_claims_available` / `natural_evidence` | “text retrieval compensates for what the graph lacks” |
| **S12** | Experiment 03: the mix / naive / forced answer is correct at its core | no opening refusal; names the publication number; names the target claims (F01: 4, 8; F05: 6, 10; F04: one of 1/18/22 and one of 14/25); contains the key terms (F01: UMLS, expert, existing cases, ontology; F05: Naive Bayes, non-persistent, second classification data; F04: cost/pecuniary/monetary, provide) | `manual_answer_review.natural_core_predicates_correct`, `forced_core_predicates_correct`, `naive.core_answer_correct`; F05 `natural_answer`, `forced_diagnostic`; F04 `core_answer`, `forced_core_answer`, `naive_core_answer` | “all mix answers correct” |
| **S13** | Experiment 03 naive: states a claim dependency that contradicts the original | “Claim A depends on/from Claim B” not as in the original; or, in a paragraph containing “depend”, an arrow chain `Claim a → Claim b` where b's parent claim in the original is not a | `incorrect_claim_dependency_chain` in F01 `extra` (only F01_B_r2) | P8 |

“Target text” and “target claims” of F01/F05/F04 come from `experiments/03_chunk_boundary_full_pipeline/conditions/frozen_groups.json`; the evidence of the experiment-01 questions comes from `data/round1/results/questions.json` and `experiments/01_baseline_index_qa/evidence/optional_question11.json`.

## Not scored

- Whether quoted text is strictly verbatim: every report already states that not all quotes are verbatim; this does not affect the README's conclusions.
- Whether additional, non-target explanations in an answer are supported (for example the explanatory warning in 03 F04_A1): this needs sentence-level semantic judgment and is outside this rubric.
- The semantic review of experiment 04: here only the number of multi-source nodes is counted automatically.

## Revision history

| Date | Change | Reason |
|---|---|---|
| 2026-11-14 | S1: for cross-document questions the claim check is limited to each patent's own paragraph and accepts any claim of that patent | 11-05's Q06 mix says “No specific claim number … for US7991757B2”, but the old rule counted the other patent's “Claim 1”; in the original run the supplementary Q06 mix cites claims 17/4 for US7991757B2, which dot counted as completed |
| 2026-11-14 | S5: added the affirmative phrase “referencing US7991757B2” | 11-05's B1 and B3 attribute correctly with this phrase; the old rule missed it |
| 2026-11-15 | S5: the negative pattern narrowed to “not linked/not tied … US7991757B2” (within 60 characters) | in the 11-15 rerun B1 writes “these are not tied to Claim 1 or Claim 27” after attributing correctly; the old rule misread it as a negative attribution |
