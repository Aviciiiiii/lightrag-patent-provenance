"""Fill the local-only runs/ folder from dot's evidence package (the three LightRAG_NEW_A/B/C copies).

The package copies are only read. Which copy holds what (see docs/NAMING.md):
  original results : round2 in B (=C), round3 in A (=C), round4_full in A (=B)
  2026-11-05 rerun : round2 in A, round3 in B, round4_full in C

    python tools/setup_local_runs.py --a <path>/LightRAG_NEW_A --b <path>/LightRAG_NEW_B --c <path>/LightRAG_NEW_C
    python tools/setup_local_runs.py ... --check     # only report what is missing / differs, copy nothing
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
from pathlib import Path

RUNS = Path(__file__).resolve().parents[1] / 'runs'
IGN = shutil.ignore_patterns('.DS_Store', '__pycache__', '*.pyc')


def plan(a: Path, b: Path, c: Path):
    e1, e2, e3 = '01_baseline_index_qa', '02_provenance_ablation_and_chunk_control', '03_chunk_boundary_full_pipeline'
    out = []
    for sd in ['logs', 'storage_full', 'storage_smoke', 'report']:
        out.append((b / 'round2' / sd, f'{e1}/original/{sd}'))
    for sd in ['logs', 'storage_full', 'storage_smoke']:
        out.append((a / 'round2' / sd, f'{e1}/rerun_20261105/{sd}'))
    for sd in ['logs', 'report']:
        out.append((a / 'round3' / sd, f'{e2}/original/{sd}'))
    out.append((b / 'round3' / 'logs', f'{e2}/rerun_20261105/logs'))
    for sd in ['logs', 'storage', 'report']:
        out.append((a / 'round4_full_20261030' / sd, f'{e3}/original/{sd}'))
    for sd in ['logs', 'storage']:
        out.append((c / 'round4_full_20261030' / sd, f'{e3}/rerun_20261105/{sd}'))
    out += [
        (a / 'tiktoken_cache', 'tiktoken_cache'),
        (a / 'report', 'round1_report'),
        (a / 'round4', 'archive/round4'),
        (a / 'env_diagnostics_20261030', 'archive/env_diagnostics_20261030'),
        (a / 'data' / 'source_checks', 'archive/data_source_checks'),
        (a / 'data' / 'dis2pat_train_rows_0000.json', 'archive/dis2pat_train_rows_0000.json'),
        (a / 'evidence' / 'official_LightRAG_v1.5.7_source_sanitized.tar.gz', 'archive/official_LightRAG_v1.5.7_source_sanitized.tar.gz'),
        (b / 'round2' / 'evidence' / 'official_core_v1.5.7.tar.gz', 'archive/round2_official_core_v1.5.7.tar.gz'),
        (b / 'round2' / 'scripts', 'archive/dot_original_scripts/round2'),
        (a / 'round3' / 'scripts', 'archive/dot_original_scripts/round3'),
        (a / 'round4_full_20261030' / 'scripts', 'archive/dot_original_scripts/round4_full_20261030'),
    ]
    return out


def same(src: Path, dst: Path) -> bool:
    if src.is_file():
        return dst.is_file() and filecmp.cmp(src, dst, shallow=False)
    if not dst.is_dir():
        return False
    cmp = filecmp.dircmp(src, dst, ignore=['.DS_Store', '__pycache__'])
    stack = [cmp]
    while stack:
        d = stack.pop()
        if d.left_only or d.right_only or d.diff_files or d.funny_files:
            return False
        stack.extend(d.subdirs.values())
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--a', type=Path, required=True)
    ap.add_argument('--b', type=Path, required=True)
    ap.add_argument('--c', type=Path, required=True)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    bad = 0
    for src, rel in plan(args.a, args.b, args.c):
        dst = RUNS / rel
        if not src.exists():
            print(f'MISSING SOURCE {src}')
            bad += 1
            continue
        if same(src, dst):
            print(f'ok        runs/{rel}')
            continue
        if args.check:
            print(f'DIFFERS   runs/{rel}')
            bad += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, ignore=IGN, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        print(f'copied    runs/{rel}')
    raise SystemExit(1 if bad else 0)


if __name__ == '__main__':
    main()
