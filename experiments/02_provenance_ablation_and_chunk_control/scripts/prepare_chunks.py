"""Prepare a boundary-only control; no credentials, network, model calls or index writes."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import hashlib
import json
import os
import ast
import bisect
import sys

ROOT = legacy_root('round3')
ROUND = ROOT / "round3"
SOURCE = ROOT / "src" / "LightRAG-v1.5.7"
os.environ["TIKTOKEN_CACHE_DIR"] = str(ROOT / "tiktoken_cache")
sys.path.insert(0, str(SOURCE))
import tiktoken

# Read unchanged official literals without importing its unrelated YAML/data stack.
# The system prompt is replayed byte for byte from the real round2 extractor call.
def literal_assignment(path, name, key=None):
    for node in ast.parse(path.read_text()).body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if key is None and isinstance(target, ast.Name) and target.id == name:
                return ast.literal_eval(node.value)
            if key is not None and isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == name and ast.literal_eval(target.slice) == key:
                return ast.literal_eval(node.value)
    raise KeyError((path, name, key))

PROMPTS = {key:literal_assignment(SOURCE/'lightrag/prompt.py','PROMPTS',key) for key in ['DEFAULT_TUPLE_DELIMITER','DEFAULT_COMPLETION_DELIMITER','entity_extraction_system_prompt','entity_extraction_user_prompt']}
DEFAULT_MAX_EXTRACTION_RECORDS = literal_assignment(SOURCE/'lightrag/constants.py','DEFAULT_MAX_EXTRACTION_RECORDS')
DEFAULT_MAX_EXTRACTION_ENTITIES = literal_assignment(SOURCE/'lightrag/constants.py','DEFAULT_MAX_EXTRACTION_ENTITIES')
__version__ = literal_assignment(SOURCE/'lightrag/_version.py','__version__')


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    assert __version__ == "1.5.7"
    raw_path = ROOT / "data/selected_raw/US7991757B2.json"
    raw = json.loads(raw_path.read_text())["claims"]
    claims = json.loads((ROOT / "data/claims/US7991757B2.json").read_text())
    by_number = {c["claim_number"]: c for c in claims}
    start = by_number[26]["start_char_in_raw_claims"]
    end = by_number[28]["end_char_in_raw_claims"]
    text = raw[start:end]
    assert text.startswith("26.") and text.endswith("recommenders.")
    full_path = ROOT / "data/documents/US7991757B2.txt"
    full = full_path.read_text()
    full_offset = full.index(raw)
    assert full.count(raw) == 1
    enc = tiktoken.get_encoding("o200k_base")
    raw_tokens = enc.encode(raw)
    full_tokens = enc.encode(full)
    text_tokens = enc.encode(text)

    # Boundaries fall immediately before the source's existing leading spaces.
    # Thus neither chunk strips, inserts, deletes, repeats or changes source bytes.
    same = by_number[28]["start_char_in_raw_claims"] - 1
    cross = raw.index(" machine readable descriptions", by_number[27]["start_char_in_raw_claims"])
    assert raw[same:same+4] == " 28."
    assert raw[cross-7:cross] == "provide"

    old_request = json.loads((ROOT / "round2/logs/api_0003_request.json").read_text())
    old_system = next(m["content"] for m in old_request["messages"] if m["role"] == "system")
    entity_types_guidance = old_system.split('\n---Entity Types---\n', 1)[1].split('\n\n---Output Format Template---\n', 1)[0]
    examples = old_system.split('The following content is an output format template only. It is not source text and must never be used as extraction content.\n\n',1)[1]
    delimiters = {
        "tuple_delimiter": PROMPTS["DEFAULT_TUPLE_DELIMITER"],
        "completion_delimiter": PROMPTS["DEFAULT_COMPLETION_DELIMITER"],
        "entity_types_guidance": entity_types_guidance,
        "language": "English",
    }
    context = {
        **delimiters,
        "examples": examples,
        "max_total_records": DEFAULT_MAX_EXTRACTION_RECORDS,
        "max_entity_records": DEFAULT_MAX_EXTRACTION_ENTITIES,
    }
    system = PROMPTS["entity_extraction_system_prompt"].format(**context).strip()
    assert system == old_system, "Official settings differ from round2 extraction"

    def aligned_span(source, source_tokens, a, b):
        left = enc.encode(source[:a])
        mid = enc.encode(source[a:b])
        right = enc.encode(source[b:])
        aligned = left + mid + right == source_tokens
        byte_a, byte_b = len(source[:a].encode()), len(source[:b].encode())
        byte_boundaries = [0]
        for token in source_tokens:
            byte_boundaries.append(byte_boundaries[-1]+len(enc.decode_single_token_bytes(token)))
        ia = bisect.bisect_left(byte_boundaries, byte_a)
        ib = bisect.bisect_left(byte_boundaries, byte_b)
        return {
            "start": len(left), "end": len(left)+len(mid),
            "aligned_to_whole_sequence": aligned,
            "utf8_byte_span": [byte_a, byte_b],
            "whole_sequence_exact_start_token_boundary": ia if byte_boundaries[ia] == byte_a else None,
            "whole_sequence_exact_end_token_boundary": ib if byte_boundaries[ib] == byte_b else None,
            "whole_sequence_enclosing_token_span": [bisect.bisect_right(byte_boundaries, byte_a)-1, ib],
            "end_byte_offset_inside_final_enclosing_token": 0 if byte_boundaries[ib] == byte_b else byte_b-byte_boundaries[ib-1],
        }

    conditions = {}
    for name, boundary in [("SAME", same), ("CROSS", cross)]:
        chunks = []
        offsets = [(start, boundary), (boundary, end)]
        for n, (a, b) in enumerate(offsets):
            content = raw[a:b]
            user = PROMPTS["entity_extraction_user_prompt"].format(
                **context, input_text=content, heading_context_block=""
            )
            chunks.append({
                "chunk_id": f"controlled-US7991757B2-{name.lower()}-{n:03d}",
                "chunk_order_index": n,
                "file_path": "US7991757B2.txt",
                "content": content,
                "sha256": sha(content),
                "utf8_bytes": len(content.encode()),
                "tokens": len(enc.encode(content)),
                "excerpt_char_span": [a-start, b-start],
                "raw_claims_char_span": [a, b],
                "full_document_char_span": [full_offset+a, full_offset+b],
                "excerpt_token_span": aligned_span(text, text_tokens, a-start, b-start),
                "raw_claims_token_span": aligned_span(raw, raw_tokens, a, b),
                "full_document_token_span": aligned_span(full, full_tokens, full_offset+a, full_offset+b),
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "user_prompt_sha256": sha(user),
            })
        assert "".join(c["content"] for c in chunks) == text
        conditions[name] = {
            "boundary_in_raw_claims": boundary,
            "boundary_in_excerpt": boundary-start,
            "boundary_label": "between Claim27 and Claim28" if name == "SAME" else "inside Claim27, immediately before machine-readable descriptions object",
            "chunks": chunks,
            "joined_text_sha256": sha("".join(c["content"] for c in chunks)),
            "total_chunk_tokens": sum(c["tokens"] for c in chunks),
        }

    result = {
        "experiment": "artificial boundary-only extraction control; not the natural 1200/100 corpus chunking",
        "publication_number": "US7991757B2",
        "source_path": str(raw_path.relative_to(ROOT)),
        "source_field": "claims",
        "source_claims": [26, 27, 28],
        "source_excerpt": text,
        "source_excerpt_sha256": sha(text),
        "raw_claims_char_span": [start, end],
        "full_document_char_span": [full_offset+start, full_offset+end],
        "full_document_claims_offset": full_offset,
        "source_excerpt_tokens": len(text_tokens),
        "tokenizer": "o200k_base; also used by round2 gpt-4o-mini tokenizer setting",
        "span_semantics": "Zero-based half-open Unicode character, UTF-8 byte and tokenizer-token spans. Token start/end index the whole named source sequence only when aligned_to_whole_sequence is true; otherwise they denote independently encoded prefix length plus chunk length and must not be treated as whole-sequence slices. Exact global token boundaries and enclosing token spans are also computed from the official tokenizer's per-token bytes. The last full-document endpoint falls within a token that also includes a trailing newline; the original raw-claims and excerpt ranges align exactly.",
        "official_version": __version__,
        "official_commit": "28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c",
        "prompt_api": "Unmodified lightrag.prompt.PROMPTS entity_extraction_system_prompt / entity_extraction_user_prompt read as AST literals. Entity type guidance and examples reused verbatim from real round2 API0003; reconstructed official system prompt asserted byte-identical. This avoids importing unrelated YAML/data dependencies during preparation.",
        "parser_api": "await lightrag.operate._process_extraction_result(response, chunk_id, timestamp, file_path, tuple_delimiter='<|#|>', completion_delimiter='<|COMPLETE|>')",
        "system_prompt_sha256": sha(system),
        "system_prompt_byte_exact_round2_api_0003": True,
        "generation_settings": {"model": old_request["model"], "temperature": 0, "max_tokens": 8192, "stream": False, "enable_thinking": False, "gleaning": 0, "seed": None},
        "quantity_limits": {"total_records": DEFAULT_MAX_EXTRACTION_RECORDS, "entities": DEFAULT_MAX_EXTRACTION_ENTITIES},
        "controls": {"calls_per_condition_per_repeat": 2, "overlap": 0, "input_text_order_identical": True, "total_original_source_bytes_identical": True, "same_system_prompt": True, "same_user_prompt_template": True, "heading_context": "", "joint_cross_chunk_reextraction": False, "index_rebuild": False},
        "conditions": conditions,
        "preregistered_evaluation": {
            "primary_technical_proposition": "The registration module allows a provider of an external recommender to provide machine readable descriptions of that recommender.",
            "primary_edge_evidence": "Count a condition successful if at least one officially parsed relation in either chunk explicitly supports the primary proposition through its endpoint labels and/or relation description. Registration Module--External Recommender/Provider edges whose description expressly states the machine-readable-description function qualify; exact endpoint equality is not required.",
            "strict_edge_secondary": "Record whether a parsed direct edge joins Registration Module and Machine Readable Descriptions (case, hyphen and plural normalization allowed; inspect description to reject merely co-occurring labels). This is secondary, because the official extractor may use another faithful binary decomposition.",
            "entity_description_secondary": "Separately record whether an entity description retains the complete primary proposition. Entity-only retention is not a parsed relation success but prevents overstating total factual loss.",
            "local_fragment_secondary": "Record surviving fragments such as module--provider and descriptions--external recommender. A union path alone is not an explicit cross-chunk proposition; do not claim all information disappeared when fragments survive.",
            "legal_dependency_exploratory": "Claim27 explicitly says The system of claim1. Record a parsed Claim27--Claim1 dependency only if those claim entities and dependency relation actually occur. The default entity-type guidance does not require a patent claim ontology. Do not infer technical relation loss from absent legal dependency edges; full Claim1 text is outside this controlled excerpt in both conditions.",
            "truncation_rule": "Check raw finish_reason, completion usage and completion delimiter for every response. If output-length truncation affects a condition, mark its boundary-only comparison inconclusive; do not attribute a cut-off row to chunking. Keep same 8192 output cap in every call.",
            "comparison_rule": "Three paired repeats, interleaved condition order. Compare each matched repeat and all raw outputs. No seed is requested; temperature0 does not ensure deterministic hosted outputs. Do not generalize one patent/one imposed boundary to corpus-wide failure rates."
        },
        "limitations": [
            "Only the original boundary placement changes; lengths and semantic completeness of individual chunks necessarily change.",
            "Both conditions make two separate stateless extraction calls and repeat the same prompt overhead, controlling call count and total source text. No cross-chunk LLM merge or full-graph reconstruction is performed.",
            "This tests an artificial split inside one Claim27 sentence, not the natural separation of complete Claim1 and Claim27. Claim27 names the module and external recommender explicitly, so simply separating whole Claims1/27 is not a clean test of this technical relation.",
            "The excerpt excludes Claims1-25 by the same rule in both conditions; nothing is inserted, paraphrased or shuffled inside the retained contiguous source span."
        ],
    }
    out = ROUND / "evidence/chunk_conditions.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    (ROUND / "evidence/chunk_source_excerpt.txt").write_text(text)
    print(json.dumps({"output":str(out),"chars":len(text),"tokens":len(text_tokens),"boundaries":{k:v["boundary_in_raw_claims"] for k,v in conditions.items()},"chunk_tokens":{k:[c['tokens'] for c in v['chunks']] for k,v in conditions.items()},"token_spans_aligned":{k:all(c['excerpt_token_span']['aligned_to_whole_sequence'] and c['raw_claims_token_span']['aligned_to_whole_sequence'] and c['full_document_token_span']['aligned_to_whole_sequence'] for c in v['chunks']) for k,v in conditions.items()}},indent=2))


if __name__ == "__main__":
    main()
