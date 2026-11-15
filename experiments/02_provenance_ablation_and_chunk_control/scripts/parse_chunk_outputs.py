"""Replay the unchanged official v1.5.7 parser over saved boundary-control outputs.

No model calls, no credentials, no LightRAG index creation or mutation.
Semantic decisions require reviewing the retained parsed records; substring flags
below are candidate selectors, not the final human/agent review verdict.
"""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import asyncio
import datetime as dt
import hashlib
import json
import os
import re
import signal
import sys
import time

ROOT = legacy_root('round3')
ROUND = ROOT / "round3"
from parser_source import SOURCE, EXPECTED_COMMIT
os.environ["TIKTOKEN_CACHE_DIR"] = str(ROOT / "tiktoken_cache")
sys.path.insert(0, str(SOURCE))


def norm(value):
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def flat(groups):
    return [record for records in groups.values() for record in records]


def candidate_flags(nodes, edges):
    relation_candidates = []
    strict_candidates = []
    entity_candidates = []
    legal_candidates = []
    fragment_candidates = []
    for edge in edges:
        terms = norm(" ".join(str(edge.get(k, "")) for k in ("src_id", "tgt_id", "description")))
        endpoints = [norm(str(edge.get(k, ""))) for k in ("src_id", "tgt_id")]
        if "registration module" in terms and "machine readable description" in terms:
            relation_candidates.append(edge)
        if any("registration module" in e for e in endpoints) and any("machine readable description" in e for e in endpoints):
            strict_candidates.append(edge)
        if "claim 27" in terms and "claim 1" in terms:
            legal_candidates.append(edge)
        if "registration module" in terms or "machine readable description" in terms:
            fragment_candidates.append(edge)
    for entity in nodes:
        terms = norm(" ".join(str(entity.get(k, "")) for k in ("entity_name", "description")))
        if "registration module" in terms and "machine readable description" in terms:
            entity_candidates.append(entity)
    return {
        "primary_relation_candidates_needing_semantic_review": relation_candidates,
        "strict_module_description_edge_candidates": strict_candidates,
        "entity_complete_proposition_candidates": entity_candidates,
        "claim27_claim1_dependency_candidates": legal_candidates,
        "local_relation_fragment_candidates": fragment_candidates,
    }


async def main():
    conditions = json.loads((ROUND / "evidence/chunk_conditions.json").read_text())
    if conditions.get("official_commit") != EXPECTED_COMMIT:
        raise RuntimeError("Frozen chunk conditions require a different official commit")
    expected = [(name, rep, chunk, ROUND / "results" / f"chunk_{name}_r{rep}_c{chunk}.json")
                for name in ("SAME", "CROSS") for rep in range(1, 4) for chunk in (0, 1)]
    missing = [str(path) for _, _, _, path in expected if not path.exists()]
    if missing:
        raise FileNotFoundError("Saved outputs incomplete; parser makes no calls: " + ", ".join(missing))

    # A normal official import stalled in unrelated GraphML/networkx startup.
    # Execute the unchanged official function/helper nodes selectively instead,
    # then validate against a real normal-package parser replay from round2.
    from official_parser_selective import load
    namespace, load_metadata = load()
    __version__ = namespace['__version__']
    _process_extraction_result = namespace['_process_extraction_result']
    old_response=json.loads((ROOT/'round2/logs/api_0191_response.json').read_text())
    expected_validation=json.loads((ROOT/'round2/evidence/extraction_truncation_parser_replay.json').read_text())
    vnodes,vedges=await _process_extraction_result(namespace['TruncatedResponse'](old_response['content']),'US9218390B2-chunk-000',0,'US9218390B2.txt',tuple_delimiter='<|#|>',completion_delimiter='<|COMPLETE|>')
    validation={
        'source':'round2/evidence/extraction_truncation_parser_replay.json',
        'raw_response':'round2/logs/api_0191_response.json',
        'input_type':'official unchanged TruncatedResponse class',
        'chunk_id':'US9218390B2-chunk-000','timestamp':0,'file_path':'US9218390B2.txt',
        'node_group_count_equal':len(vnodes)==expected_validation['nodes'],
        'edge_group_count_equal':len(vedges)==expected_validation['edges'],
        'feature_node_records_equal':all(vnodes.get(k)==v for k,v in expected_validation['feature_nodes'].items()),
        'feature_edge_records_equal':all(vedges.get(tuple(v['endpoints']))==v['records'] for v in expected_validation['feature_edges']),
        'partial_edge_absence_equal':(('Class-Based Language Model Features','GEO_TRI_FIRST') in vedges)==expected_validation['geo_tri_first_membership_edge_present'],
        'scope':'Exact equality of saved13 feature-node groups and4 feature-edge groups including5 edge records, both total group counts42/34, and absent truncated membership edge. Round2 did not retain every parsed record in this replay artifact, so full-record equality across all42/34 groups is not claimed.',
        'parsed_nodes':vnodes,
        'parsed_edges':[{'endpoints':list(k),'records':v} for k,v in vedges.items()],
    }
    checks=[v for k,v in validation.items() if k.endswith('_equal')]
    validation['all_saved_comparisons_passed']=all(checks)
    assert validation['all_saved_comparisons_passed'], 'Selective official parser failed saved normal-import replay validation'
    (ROUND/'evidence/parser_validation_api191.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
    (ROUND/'evidence/parser_selective_source_manifest.json').write_text(json.dumps(load_metadata,ensure_ascii=False,indent=2)+'\n')

    parsed = []
    for name, rep, chunk_no, path in expected:
        saved = json.loads(path.read_text())
        response = saved["response"]
        content = response["content"]
        source_chunk = conditions["conditions"][name]["chunks"][chunk_no]
        parsed_at = int(time.time())
        nodes, edges = await _process_extraction_result(
            content, source_chunk["chunk_id"], parsed_at, source_chunk["file_path"],
            tuple_delimiter="<|#|>", completion_delimiter="<|COMPLETE|>",
        )
        node_rows, edge_rows = flat(nodes), flat(edges)
        entry = {
            "condition": name, "repeat": rep, "chunk": chunk_no,
            "input_file": str(path.relative_to(ROOT)),
            "chunk_id": source_chunk["chunk_id"],
            "raw_response_sha256": hashlib.sha256(content.encode()).hexdigest(),
            "finish_reason": response.get("finish_reason"),
            "usage": response.get("usage"),
            "completion_delimiter_present": "<|COMPLETE|>" in content,
            "parser_timestamp": parsed_at,
            "nodes": node_rows, "edges": edge_rows,
            "node_groups": [{"key": key, "records": records} for key, records in nodes.items()],
            "edge_groups": [{"key": list(key), "records": records} for key, records in edges.items()],
            "candidate_flags": candidate_flags(node_rows, edge_rows),
        }
        parsed.append(entry)

    paired_rows = []
    for name in ("SAME", "CROSS"):
        for rep in range(1, 4):
            pair = [p for p in parsed if p["condition"] == name and p["repeat"] == rep]
            nodes = [n for p in pair for n in p["nodes"]]
            edges = [e for p in pair for e in p["edges"]]
            paired_rows.append({
                "condition": name, "repeat": rep, "chunk_count": len(pair),
                "node_records_before_any_merge": len(nodes),
                "edge_records_before_any_merge": len(edges),
                "finish_reasons": [p["finish_reason"] for p in pair],
                "truncated": any(p["finish_reason"] == "length" for p in pair),
                "all_completion_delimiters_present": all(p["completion_delimiter_present"] for p in pair),
                "candidate_flags": candidate_flags(nodes, edges),
                "aggregation": "Concatenate records from the two independent official extraction parses; no new LLM inference or graph insertion/merge.",
            })

    output = {
        "parsed_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "official_version": __version__,
        "official_commit": conditions["official_commit"],
        "official_parser_module": str(SOURCE/'lightrag/operate.py'),
        "official_parser_function": "_process_extraction_result",
        "parser_load_mode":load_metadata['load_mode'],
        "normal_import_replay_validation":"round3/evidence/parser_validation_api191.json",
        "source_dependency_manifest":"round3/evidence/parser_selective_source_manifest.json",
        "source_unchanged": True,
        "calls_made_by_parser": 0,
        "parsed_chunks": parsed,
        "condition_repeats": paired_rows,
        "evaluation_note": "Candidate flags select records for semantic review under chunk_conditions.json preregistered_evaluation. They are not conclusive causal or semantic verdicts.",
    }
    out = ROUND / "results/chunk_parsed.json"
    out.write_text(json.dumps(output, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"output": str(out), "parsed_chunks":len(parsed), "rows":[{
        "condition":r["condition"],"repeat":r["repeat"],"edge_records":r["edge_records_before_any_merge"],
        "primary_candidates":len(r["candidate_flags"]["primary_relation_candidates_needing_semantic_review"]),
        "strict_candidates":len(r["candidate_flags"]["strict_module_description_edge_candidates"]),
        "truncated":r["truncated"],"completion_signals":r["all_completion_delimiters_present"]
    } for r in paired_rows]}, indent=2))


if __name__ == "__main__":
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("Parser local execution exceeded240 seconds")))
    signal.alarm(240)
    asyncio.run(main())
    signal.alarm(0)
