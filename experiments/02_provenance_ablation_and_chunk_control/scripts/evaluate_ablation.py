#!/usr/bin/env python3
"""Evidence-based review labels plus deterministic quote/reference checks."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import datetime
import hashlib
import json
import re

ROOT = legacy_root('round3')
R3 = ROOT / "round3"


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lex(text):
    return " ".join(re.findall(r"\w+", text))


def main():
    protocol = read(R3 / "evidence/evaluation_protocol.json")
    manifest = read(R3 / "conditions/condition_manifest.json")
    run = read(R3 / "results/ablation_run_status.json")
    claims = read(ROOT / "round2/evidence/optional_question11.json")["evidence"]
    retrieval = read(ROOT / "round2/results/supplement_budget_Q11_supplementary_mix.json")["result"]["data"]
    refmap = {x["reference_id"]: x["file_path"] for x in retrieval["references"]}
    diagnostics = {
        "A1": "These are associated with registration-related concepts, but the graph does not link them to US7991757B2.",
        "A2": "However, these entities are **not linked** in the provided relationships to US7991757B2 (or to any patent number in the reference list).",
        "A3": "However, these are not tied to US7991757B2 in the supplied evidence.",
        "B1": "US7991757B2 is referenced only through Knowledge Graph relationships, not through any Document Chunk.",
        "B2": "US7991757B2 appears only in the Knowledge Graph relationships, not in the Document Chunks.",
        "B3": "The only evidence relating to that patent is Knowledge Graph relationship data,",
        "C1": 'Claim 27 depends from Claim 1 ("The system of claim 1") and adds a further configuration of the same module:',
        "C2": 'Claim 27 explicitly depends on Claim 1 ("The system of claim 1"), so it narrows the Claim 1 system rather than defining a separate one.',
        "C3": "The dependency is express — Claim 27 incorporates all limitations of Claim 1 and narrows the registration module.",
    }
    rows = []
    for condition in "ABC":
        for repeat in (1, 2, 3):
            path = R3 / f"results/ablation_{condition}_r{repeat}.json"
            record = read(path)
            response = record["response"]
            text = response["content"]
            key = condition + str(repeat)
            assert diagnostics[key] in text
            citations = []
            for ref_id, label in re.findall(r"^- \[(\d+)\] (.+)$", text, re.M):
                citations.append({
                    "reference_id": ref_id,
                    "displayed_file_path": label,
                    "original_mapping": refmap.get(ref_id),
                    "matches_original_id_mapping": refmap.get(ref_id) == label,
                    "supports_target_registration_facts": label == "US7991757B2.txt",
                    "assessment": ("Correct target document label, but remaps the original reference ID."
                                   if condition == "C" else "Existing ID/title, but document does not support the target registration facts."),
                })
            quote_audit = []
            if condition == "C":
                for quote in re.findall(r'"([^"\n]+)"', text):
                    exact = [c["claim_number"] for c in claims if quote in c["full_claim"]]
                    normalized = [c["claim_number"] for c in claims if lex(quote) in lex(c["full_claim"])]
                    quote_audit.append({
                        "quote": quote,
                        "exact_original_claim_matches": exact,
                        "word_sequence_matches_after_punctuation_and_whitespace_normalization": normalized,
                        "lexical_substitution": not bool(normalized),
                    })
            scores = {
                "positive_wrong_source_assignment_or_exclusion_in_prose": False,
                "unsupported_reference_list_source_assignment": condition in "AB",
                "primary_wrong_source_error_including_reference_list": condition in "AB",
                "correct_document_attribution": condition in "BC",
                "neutral_source_attribution_abstention": condition == "A",
                "claim_task_abstention": condition in "AB",
                "claim_abstention_appropriate_to_supplied_evidence": condition in "AB",
                "claim_task_core_complete_and_grounded": condition == "C",
                "claim_dependency_correct_and_supported": condition == "C",
                "unsupported_claim_number_assignment": False,
                "claim_quotations_present": condition == "C",
                "all_claim_quotes_byte_exact": all(x["exact_original_claim_matches"] for x in quote_audit) if quote_audit else None,
                "all_claim_quotes_word_faithful_with_punctuation_normalization": all(x["word_sequence_matches_after_punctuation_and_whitespace_normalization"] for x in quote_audit) if quote_audit else None,
                "reference_ids_match_original_context": all(x["matches_original_id_mapping"] for x in citations),
                "reference_sources_support_target_facts": condition == "C",
                "formal_reference_and_source_valid_together": False,
            }
            row = {
                "condition": condition,
                "repeat": repeat,
                "call_id": record["call_id"],
                "response_file": str(path.relative_to(ROOT)),
                "response_file_sha256": digest(path),
                "request_exact_match": record["request_exact_match"],
                "finish_reason": response["finish_reason"],
                "scores": scores,
                "diagnostic_quote": diagnostics[key],
                "references": citations,
                "claim_quote_audit": quote_audit,
                "reasoning_note": (
                    "No positive alternative-patent assertion; source uncertainty is appropriate for A. Irrelevant references are a separate citation-attribution error."
                    if condition == "A" else
                    "Identifies source from relationship provenance, correctly declines claim-level attribution/quotes because no Claim text or number-to-fact mapping was added."
                    if condition == "B" else
                    "Correct source and core Claim distinction/dependency. Citation [1] conflicts with the original reference list. Quotation changes are assessed separately."
                ),
                "extra_inference_note": None,
                "usage": response["usage"],
            }
            if key == "C1":
                inference = "It can reasonably be inferred that Claim 27's machine-readable descriptions are the mechanism by which an external recommender is registered and made accessible via Claim 1's data interface; however, the claims do not expressly state that link, so this is inference rather than quoted fact."
                assert inference in text
                row["extra_inference_note"] = {
                    "quote": inference,
                    "assessment": "Explicitly labeled but unsupported mechanism inference; do not count it as grounded fact. Core requested Claim comparison remains correct.",
                }
                row["quotation_note"] = 'One quotation changes original "being provided" to "are provided", beyond punctuation normalization. Other core target wording is faithful.'
            elif key == "C2":
                row["quotation_note"] = "Claim1 excerpt-final semicolon becomes period; Claim27 space before comma removed. No substantive word change."
            elif key == "C3":
                row["quotation_note"] = "Some excerpt-final semicolons become periods. No substantive word change."
            rows.append(row)

    counts = {}
    for condition in "ABC":
        selected = [x for x in rows if x["condition"] == condition]
        counts[condition] = {"n": len(selected)}
        for metric in selected[0]["scores"]:
            values = [x["scores"][metric] for x in selected]
            counts[condition][metric] = {
                "true": sum(v is True for v in values),
                "false": sum(v is False for v in values),
                "not_applicable": sum(v is None for v in values),
            }
    summary = {
        "reviewed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "method": "AI-assisted direct reading of all nine complete responses, with deterministic original-claim quotation/reference-map checks. No additional API calls; no independent human annotation claimed.",
        "protocol_file": "round3/evidence/evaluation_protocol.json",
        "protocol_sha256": digest(R3 / "evidence/evaluation_protocol.json"),
        "criteria_timing": {
            "condition_manifest_generated_utc": manifest["generated_utc"],
            "run_started_utc": run["started_utc"],
            "run_finished_utc": run["finished_utc"],
            "protocol_written_utc": protocol.get("written_utc", protocol.get("frozen_utc")),
            "note": "Evaluation recommendations in condition_manifest predate the calls. The consolidated protocol file was written three seconds after the calls ended; do not claim independent prior preregistration of that file.",
        },
        "primary_metric_interpretation": "The agreed primary definition includes wrong support citations. The combined field counts irrelevant end-reference entries in A/B as citation-attribution errors under the original prompt contract that each reference directly support facts. The prose-only metric is zero in all conditions. No inline citation assigns each reference to an individual sentence, so unsupported end references must not be described as an explicit prose claim that the registration module belongs to another patent. C displays the correct document label but invalid reference-ID mapping; that is classified separately.",
        "rows": rows,
        "counts_by_condition": counts,
        "conclusions": [
            'The original API392 positive "different patent family" wording did not recur in any new A run. A abstained from document attribution; B correctly identified US7991757B2 in all three runs.',
            "B appropriately abstained from unsupported Claim1/Claim27 completion in all three runs. Source IDs identify chunks, not legal Claim dependencies.",
            "C completed the core Claim distinction/dependency in all three runs after receiving original Claim evidence. This is an additional-evidence diagnostic, not proof of Claim-level grounding from provenance fields alone.",
            "A/B appended irrelevant patent references in all six responses. C displayed the correct target title but renumbered it as [1], contradicting the unchanged reference map in all three responses. No condition satisfied both source-support and formal-ID validity.",
            'Every C response altered punctuation in at least one quote; C1 additionally changed "being provided" to "are provided". Core technical facts remain correct, but byte-exact quotation fidelity is not achieved.',
            "B bundles publication_numbers/file_path/source_id across all 82 relationship records, with changed token length/attention. Three unseeded temp0 repeats do not identify a single-field effect or population-level guarantee.",
            "C1 adds an explicitly labeled but unsupported mechanism inference; it is not direct Claim evidence.",
        ],
        "no_truncated_responses": all(x["finish_reason"] == "stop" for x in rows),
    }
    destination = R3 / "evidence/ablation_evaluation.json"
    destination.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"saved": str(destination), "rows": len(rows), "no_truncation": summary["no_truncated_responses"]}, indent=2))


if __name__ == "__main__":
    main()
