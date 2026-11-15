#!/usr/bin/env python3
"""Prepare credential-free Q11 A/B/C replay inputs from saved round-2 evidence.

No API, credential, index mutation, or third-party dependency is used.
"""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import copy
import datetime
import difflib
import hashlib
import json
import re

ROOT = legacy_root('round3')
OUT = ROOT / "round3" / "conditions"


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path):
    return json.loads((ROOT / path).read_text())


def write_json(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    original_path = ROOT / "round2/logs/api_0392_request.json"
    logged = json.loads(original_path.read_text())
    result = read_json("round2/results/supplement_budget_Q11_supplementary_mix.json")["result"]
    chunks = read_json("round2/storage_full/patent_r2_full/kv_store_text_chunks.json")
    docs = read_json("round2/storage_full/patent_r2_full/kv_store_full_docs.json")
    spans = {x["chunk_id"]: x for x in read_json("round2/evidence/actual_chunk_source_mapping.json")["mapping"]}
    question = read_json("round2/evidence/optional_question11.json")
    payload_keys = ["model", "messages", "max_tokens", "temperature", "stream", "extra_body"]
    a = {k: copy.deepcopy(logged[k]) for k in payload_keys}
    assert a["messages"][1]["content"] == question["question"]
    original_system = a["messages"][0]["content"]
    relation_pattern = re.compile(r"(Knowledge Graph Data \(Relationship\):\s*```json\n)(.*?)(\n```)", re.S)
    match = relation_pattern.search(original_system)
    assert match is not None
    original_lines = match.group(2).splitlines()
    records = result["data"]["relationships"]
    assert len(original_lines) == len(records) == 82

    enhanced_lines = []
    field_diffs = []
    verified_sources = []
    local_docs = {}
    for ordinal, (line, record) in enumerate(zip(original_lines, records)):
        item = json.loads(line)
        assert item == {
            "entity1": record["src_id"],
            "entity2": record["tgt_id"],
            "description": record["description"],
        }
        assert line.endswith("}")
        source_ids = record["source_id"].split("<SEP>")
        file_paths = record["file_path"].split("<SEP>")
        mappings = []
        for source_id in source_ids:
            chunk = chunks[source_id]
            pub = chunk["full_doc_id"]
            assert chunk["file_path"] in file_paths
            assert pub in docs
            if chunk["file_path"] not in local_docs:
                local_docs[chunk["file_path"]] = (ROOT / "data/documents" / chunk["file_path"]).read_text()
            local_doc = local_docs[chunk["file_path"]]
            # Official insertion stripped the single terminal newline. Do not
            # normalize inner whitespace or permit any other text difference.
            assert docs[pub]["content"] == local_doc.removesuffix("\n")
            assert local_doc.startswith("Publication number: " + pub + "\n")
            span = spans[source_id]["source_span"]
            assert spans[source_id]["publication_number"] == pub
            assert local_doc[span["start"]:span["end"]] == chunk["content"]
            mappings.append({
                "source_id": source_id,
                "publication_number": pub,
                "file_path": chunk["file_path"],
                "source_span": span,
                "chunk_content_sha256": sha(chunk["content"]),
            })
        assert set(file_paths) == {x["file_path"] for x in mappings}
        publications = list(dict.fromkeys(x["publication_number"] for x in mappings))
        additions = {
            "publication_numbers": publications,
            "file_path": record["file_path"],
            "source_id": record["source_id"],
        }
        # Preserve every byte of each original JSON object except its final
        # closing brace, adding only verified metadata before that same brace.
        line_b = line[:-1] + ", " + json.dumps(additions, ensure_ascii=False)[1:]
        parsed_b = json.loads(line_b)
        assert {k: parsed_b[k] for k in item} == item
        assert set(parsed_b) - set(item) == set(additions)
        enhanced_lines.append(line_b)
        field_diffs.append({"relationship_ordinal_zero_based": ordinal,
                            "entity1": item["entity1"], "entity2": item["entity2"],
                            "changed_existing_fields": [], "added_fields": additions})
        verified_sources.append({"relationship_ordinal_zero_based": ordinal,
                                 "source_mappings": mappings})

    b = copy.deepcopy(a)
    b["messages"][0]["content"] = original_system[:match.start(2)] + "\n".join(enhanced_lines) + original_system[match.end(2):]
    # Reversing precisely the 82 metadata insertions must recover A byte-for-byte.
    reversed_b = b["messages"][0]["content"]
    for old, new in zip(original_lines, enhanced_lines):
        assert reversed_b.count(new) == 1
        reversed_b = reversed_b.replace(new, old, 1)
    assert reversed_b == original_system

    publication = "US7991757B2"
    original_doc = docs[publication]["content"]
    original_claims = []
    claim_audits = []
    for evidence in question["evidence"]:
        claim = evidence["full_claim"]
        start, end = evidence["source_span"]
        assert original_doc[start:end] == claim
        containing_ids = [key for key, val in chunks.items()
                          if val["full_doc_id"] == publication and claim in val["content"]]
        assert len(containing_ids) == 1
        original_claims.append({
            "publication_number": publication,
            "file_path": publication + ".txt",
            "source_id": containing_ids[0],
            "claim_number": evidence["claim_number"],
            "content": claim,
        })
        claim_audits.append({"claim_number": evidence["claim_number"],
                             "source_span": [start, end],
                             "source_id": containing_ids[0],
                             "exact_original_match": True,
                             "content_sha256": sha(claim)})
    c = copy.deepcopy(b)
    original_section = "Original Claim Evidence:\n\n```json\n" + "\n".join(json.dumps(x, ensure_ascii=False) for x in original_claims) + "\n```\n\n"
    anchor = "Reference Document List (Each entry starts with a [reference_id] that corresponds to entries in the Document Chunks):"
    assert c["messages"][0]["content"].count(anchor) == 1
    c["messages"][0]["content"] = c["messages"][0]["content"].replace(anchor, original_section + anchor, 1)
    assert c["messages"][0]["content"].replace(original_section, "", 1) == b["messages"][0]["content"]

    statistics = {}
    for label, payload in [("A", a), ("B", b), ("C", c)]:
        write_json(f"{label}_request.json", payload)
        system = payload["messages"][0]["content"]
        (OUT / f"{label}_system.txt").write_text(system)
        (OUT / f"{label}_user.txt").write_text(payload["messages"][1]["content"])
        assert payload["messages"][1:] == a["messages"][1:]
        assert system.split("---Context---", 1)[0] == original_system.split("---Context---", 1)[0]
        assert system[system.index(anchor):] == original_system[original_system.index(anchor):]
        statistics[label] = {
            "system_characters": len(system),
            "system_utf8_bytes": len(system.encode("utf-8")),
            "system_sha256": sha(system),
            "user_sha256": sha(payload["messages"][1]["content"]),
            "token_count": None,
            "token_count_note": "Not guessed; runner/API usage will provide exact charged prompt-token count.",
        }
    (OUT / "A_original_logged_request.json").write_bytes(original_path.read_bytes())
    for first, second, left, right in [("A", "B", a, b), ("B", "C", b, c)]:
        diff = difflib.unified_diff(left["messages"][0]["content"].splitlines(keepends=True),
                                    right["messages"][0]["content"].splitlines(keepends=True),
                                    fromfile=first, tofile=second)
        (OUT / f"{first}_to_{second}.diff").write_text("".join(diff))
    write_json("B_field_diffs.json", field_diffs)
    write_json("source_mapping_verification.json", verified_sources)
    write_json("C_claim_verification.json", claim_audits)
    metadata = {
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "original_api_call_id": 392,
        "original_request": "round2/logs/api_0392_request.json",
        "retrieved_result": "round2/results/supplement_budget_Q11_supplementary_mix.json",
        "A": "Exact replay of original API392 payload, excluding only log-envelope id/stage fields.",
        "B": "Add only publication_numbers, original file_path, and original source_id to each of all 82 pre-existing relationship JSON records. Entity records, descriptions, order, retrieved chunks, reference list, user query and system instructions unchanged.",
        "C": "B plus exact original Claim1 and Claim27 in a separate Original Claim Evidence section. Diagnostic adds semantic evidence, not a pure provenance-field ablation.",
        "relationship_count": 82,
        "entity_count_unchanged": 82,
        "document_chunk_count_unchanged": 20,
        "reference_count_unchanged": 13,
        "new_reference_ids": [],
        "citation_limitation": "US7991757B2 is absent from the unchanged reference-ID list in all conditions. Correct prose attribution and formal reference-list ID compliance must be assessed separately. C's supplied Claim source labels have no new reference ID.",
        "source_id_meaning": "IDs of persisted text chunks, joined by <SEP> for merged provenance. Each ID was independently looked up and verified against full_doc_id, file_path and an exact original-document character span. No source_id/file_path lists were arbitrarily zipped; aggregation does not establish one-to-one attribution of description sentences or Claim numbers.",
        "source_document_normalization": "Persisted full_docs equals each original local document with its single terminal newline removed; no inner text normalization accepted. Chunk and Claim character spans match the original local document exactly.",
        "checks": {"A_payload_values_exact": True, "B_reversible_to_A": True,
                   "existing_relationship_fields_unchanged": True,
                   "all_relationship_sources_validated": True,
                   "C_reversible_to_B": True, "C_claims_exact_original_matches": True,
                   "user_query_identical": True, "system_instructions_identical": True,
                   "reference_list_identical": True},
        "statistics": statistics,
        "evaluation_recommendation": {
            "primary": "Wrong positive source attribution/exclusion: says retrieved registration capabilities belong to another patent/family, do not belong to US7991757B2, or cites another patent as their actual support. Neutral lack-of-source abstention is distinct, not this error.",
            "document_attribution": "Recognizes US7991757B2 as provenance of the registration relationship. B can establish document attribution but cannot establish Claim1/27 assignment from source_id alone.",
            "claim_dependency": "Correct Claim27 depends on Claim1, registration vs machine-readable-description capability, supported by provided claim text. A/B have no explicit Claim evidence for this attribution; guesses remain unsupported even when true externally.",
            "quotes": "Exact supporting claim wording only in C; a graph paraphrase must not be labeled a direct original-Claim quotation.",
            "repeat_design": "3 matched repeats per condition, interleaved/rotated order, same parameters. Record no seed if unsupported and report observed counts without population/sole-cause claims.",
        },
    }
    write_json("condition_manifest.json", metadata)
    evidence_dir = ROOT / "round3/evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "ablation_design_review.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": "prepared", "conditions_directory": str(OUT),
                      "relationship_records_verified": 82, "statistics": statistics}, indent=2))


if __name__ == "__main__":
    main()
