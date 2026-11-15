"""No-LLM smoke test for one experiment (or all). Never calls an API and never prints secrets.

Checks: Python / LightRAG version; LightRAG source files byte-identical to commit 28ff1b05;
paths.py mapping of every input the experiment reads; all scripts compile; the experiment's
session module loads (without creating a session); .env keys present (values not printed);
tokenizer works offline; experiment-specific deterministic checks (03: dot's custom chunker
reproduces the saved chunk hashes; 01: saved index readable, 612 nodes / 994 edges).

    python tools/smoke_check.py [01_baseline_index_qa ...]    # default: all four
Exit code 0 = no FAIL (WARN lines are informational).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
import paths  # noqa: E402

os.environ.setdefault('TIKTOKEN_CACHE_DIR', str(paths.RUNS / 'tiktoken_cache'))

# sha256 at upstream commit 28ff1b05 (v1.5.7), recorded from the pinned checkout
UPSTREAM_SHA256 = {
    'lightrag/_version.py': '6dd9edee78ddd7c0c7822a79214d9db424cb2cc18ca3b61136cc84a71868840a',
    'lightrag/constants.py': '295f3e46121b111ead3e164231ff363a4a6b0231c9bd530c370b88346157b3b7',
    'lightrag/utils.py': '70fe8389a462a3ada44df7d2dd7c49ed85a5c959ca32422f78ac8fdb2dafd5fc',
    'lightrag/operate.py': 'fecb70d27b860efacb57d7b1bc16a706d7d68bd18de9ac80571fcd4628305047',
    'lightrag/prompt.py': 'db0cf2d0f5d420a8372fac2b33043d8b4f14c84ec0a60653862e4e53a27047e1',
    'lightrag/lightrag.py': 'ff118d8d197b7f5ab899a2190157fa88782dc6be897c59ab47a42cab52ac45b9',
    'lightrag/base.py': '53a1628afb3e2b440aa03eb5a0590c365a04ae4974b432ae79914e8927f92a96',
}
ENV_KEYS = ['LLM_BINDING_HOST', 'LLM_MODEL', 'LLM_BINDING_API_KEY', 'EMBEDDING_BINDING_HOST',
            'EMBEDDING_MODEL', 'EMBEDDING_BINDING_API_KEY']
LEGACY = {v: k for k, v in paths.EXPERIMENTS.items()}
# inputs read through the legacy ROOT (committed unless marked local-only)
INPUTS = {
    '01_baseline_index_qa': ['data/selected_patents.json', 'data/documents', 'results/questions.json',
                             'round2/evidence/optional_question11.json',
                             'round2/storage_full/patent_r2_full/graph_chunk_entity_relation.graphml'],
    '02_provenance_ablation_and_chunk_control': ['round3/conditions/condition_manifest.json',
                                                 'round3/evidence/chunk_conditions.json',
                                                 'round2/evidence/extraction_truncation_parser_replay.json'],
    '03_chunk_boundary_full_pipeline': ['round4_full_20261030/conditions/frozen_groups.json'],
    '04_merged_node_audit': ['round2/results/full_graph.json', 'round2_multisource_audit/reviews',
                             'round2/storage_full/patent_r2_full/kv_store_llm_response_cache.json'],
}
LOCAL = {
    '01_baseline_index_qa': ['round2/logs'],
    '02_provenance_ablation_and_chunk_control': ['round2/logs/api_0392_request.json', 'round2/logs/api_0191_response.json'],
    '03_chunk_boundary_full_pipeline': ['round4_full_20261030/storage', 'round4_full_20261030/logs'],
    '04_merged_node_audit': [],
}

results: list[tuple[str, str, str]] = []


def rec(level, name, detail=''):
    results.append((level, name, detail))
    print(f'{level:5} {name}' + (f' — {detail}' if detail else ''))


def common():
    v = sys.version_info
    rec('OK' if (v.major, v.minor) == (3, 10) else 'WARN', 'python', f'{v.major}.{v.minor}.{v.micro} (original runs: 3.10.6)')
    try:
        site = paths.lightrag_site()
        from lightrag._version import __version__
        rec('OK' if __version__ == '1.5.7' else 'FAIL', 'lightrag version', __version__)
        bad = [f for f, h in UPSTREAM_SHA256.items() if hashlib.sha256((site / f).read_bytes()).hexdigest() != h]
        rec('FAIL' if bad else 'OK', 'lightrag source == upstream 28ff1b05', ', '.join(bad) or f'{len(UPSTREAM_SHA256)} files match')
    except Exception as e:  # noqa: BLE001
        rec('FAIL', 'lightrag import', repr(e))
    try:
        import tiktoken
        enc = tiktoken.get_encoding('o200k_base')
        rec('OK', 'tokenizer o200k_base', f'{len(enc.encode("Publication number: US7991757B2"))} tokens for a sample line')
    except Exception as e:  # noqa: BLE001
        rec('WARN', 'tokenizer o200k_base', f'{e!r} (needs runs/tiktoken_cache or network)')
    env = paths.ENV_FILE
    if not env.exists():
        rec('WARN', '.env', 'not present — only needed for live reruns (copy .env.example)')
    else:
        from dotenv import dotenv_values
        cfg = dotenv_values(env)
        missing = [k for k in ENV_KEYS if not cfg.get(k)]
        rec('FAIL' if missing else 'OK', '.env keys', ('missing: ' + ', '.join(missing)) if missing else 'all present (values not shown)')


def check_experiment(name):
    legacy = LEGACY[name]
    exp = paths.REPO / 'experiments' / name
    root = paths.legacy_root(legacy)
    for p in INPUTS[name]:
        q = root / p
        rec('OK' if Path(q).exists() else 'FAIL', f'[{name[:2]}] input {p}', str(Path(q).relative_to(paths.REPO)) if str(q).startswith(str(paths.REPO)) else str(q))
    for p in LOCAL[name]:
        q = root / p
        rec('OK' if Path(q).exists() else 'WARN', f'[{name[:2]}] local-only {p}', 'present' if Path(q).exists() else 'missing (offline replay needs it; see runs/README.md)')
    bad = []
    scripts = sorted(exp.rglob('*.py'))
    for f in scripts:
        try:
            compile(f.read_text(), str(f), 'exec')
        except SyntaxError as e:
            bad.append(f'{f.name}: {e}')
    rec('FAIL' if bad else 'OK', f'[{name[:2]}] scripts compile', '; '.join(bad) or f'{len(scripts)} files')
    rr = exp / 'scripts' / 'repro_runtime.py'
    if rr.exists():
        spec = importlib.util.spec_from_file_location(f'repro_runtime_{name[:2]}', rr)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        ok = Path(mod.SESSION_PATH).is_relative_to(exp) and Path(mod.DEFAULT_CONFIG) == paths.ENV_FILE
        state = 'session exists' if Path(mod.SESSION_PATH).exists() else 'no session (not started)'
        rec('OK' if ok else 'FAIL', f'[{name[:2]}] session module', f'group {mod.GROUP}, {state}, config -> .env')
    if name == '03_chunk_boundary_full_pipeline':
        check_chunker(exp)
    if name == '01_baseline_index_qa':
        check_index(root)


def check_chunker(exp):
    try:
        sys.path.insert(0, str(exp / 'scripts'))
        from custom_chunker import make_precomputed_chunker
        from lightrag.utils import TiktokenTokenizer
        tok = TiktokenTokenizer('gpt-4o-mini')
        groups = {g['id']: g for g in json.loads((exp / 'conditions/frozen_groups.json').read_text())['groups']}
        n = 0
        for gid in ['F01', 'F05', 'F04']:
            for cond in 'AB':
                ranges = [c['token_span'] for c in groups[gid]['conditions'][cond]['chunks']]
                chunks = make_precomputed_chunker(groups[gid]['content'], ranges)(tok, groups[gid]['content'])
                got = [hashlib.sha256(c['content'].encode()).hexdigest() for c in chunks]
                saved = json.loads((exp / f'results/{gid}_{cond}_r1/actual_chunking.json').read_text())
                want = [c['content_sha256'] for c in saved['chunks']]
                if got != want:
                    rec('FAIL', f'[03] chunker {gid}/{cond}', 'chunk hashes differ from saved actual_chunking.json')
                    return
                n += len(got)
        rec('OK', '[03] custom chunker reproduces saved chunks', f'6 conditions, {n} chunks, sha256 identical')
    except Exception as e:  # noqa: BLE001
        rec('FAIL', '[03] custom chunker', repr(e))


def check_index(root):
    g = Path(root / 'round2/storage_full/patent_r2_full/graph_chunk_entity_relation.graphml')
    if not g.exists():
        return
    import networkx as nx
    G = nx.read_graphml(g)
    rec('OK' if (G.number_of_nodes(), G.number_of_edges()) == (612, 994) else 'FAIL', '[01] saved index graph',
        f'{G.number_of_nodes()} nodes / {G.number_of_edges()} edges (report: 612 / 994)')
    sums = paths.ORIGINAL_INDEX / 'SHA256SUMS.txt'
    if sums.exists():
        import hashlib
        rows = [l.split(None, 1) for l in sums.read_text().splitlines() if l.strip()]
        bad = [f for h, f in rows if hashlib.sha256((paths.ORIGINAL_INDEX / f.strip()).read_bytes()).hexdigest() != h]
        rec('FAIL' if bad else 'OK', '[01] committed index SHA256', f'{len(rows) - len(bad)}/{len(rows)} files match SHA256SUMS.txt' + (f'; differ: {bad}' if bad else ''))


if __name__ == '__main__':
    names = sys.argv[1:] or list(LEGACY)
    for n in names:
        if n not in LEGACY:
            sys.exit(f'unknown experiment {n}; choose from {list(LEGACY)}')
    common()
    for n in names:
        check_experiment(n)
    fails = [r for r in results if r[0] == 'FAIL']
    print(f'\n{len(results)} checks, {len(fails)} FAIL, {sum(1 for r in results if r[0] == "WARN")} WARN')
    sys.exit(1 if fails else 0)
