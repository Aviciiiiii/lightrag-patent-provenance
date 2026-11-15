"""Import a finished rerun into experiments/<exp>/results_rerun_<label>/ (sanitized). Full logs stay in runs/.

Copied: results/, evidence/, conditions/ (if present) and a RUN_RECORD.md made by summarize_rerun.py.
Not copied: logs/, storage*/, config/ (session), report/.
Every text file gets local paths replaced by placeholders (repo root -> <REPO>, see tools/sanitize_paths.py).
The import is refused if any API key value from the .env file appears in the copied files.

    python tools/import_rerun.py 01_baseline_index_qa runs/rerun_01_baseline_index_qa_<UTC> [--label 20261114]
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / 'tools'))
import paths  # noqa: E402
import sanitize_paths  # noqa: E402

KEEP = ['results', 'evidence', 'conditions']
TEXT = {'.json', '.txt', '.md', '.csv', '.log', '.py', '.diff', '.jsonl', '.html'}


def secret_values() -> list[str]:
    if not paths.ENV_FILE.exists():
        return []
    from dotenv import dotenv_values
    return [v for k, v in dotenv_values(paths.ENV_FILE).items() if v and ('KEY' in k or 'TOKEN' in k) and len(v) >= 8]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('experiment', choices=list(paths.EXPERIMENTS.values())[:3])
    ap.add_argument('run_dir', type=Path)
    ap.add_argument('--label', help='date label, default: from the run directory name')
    ap.add_argument('--operator', default='', help='who ran it; passed to summarize_rerun.py for RUN_RECORD.md')
    a = ap.parse_args()
    src = a.run_dir.resolve()
    if not src.is_dir():
        sys.exit(f'not a directory: {src}')
    label = a.label or src.name.rsplit('_', 1)[-1][:8]
    dst = REPO / 'experiments' / a.experiment / f'results_rerun_{label}'
    if dst.exists():
        sys.exit(f'already exists, refusing to overwrite: {dst.relative_to(REPO)}')
    for d in KEEP:
        if (src / d).is_dir():
            shutil.copytree(src / d, dst / d, ignore=shutil.ignore_patterns('.DS_Store', '__pycache__'))
    flag = {'01_baseline_index_qa': '--exp01', '02_provenance_ablation_and_chunk_control': '--exp02',
            '03_chunk_boundary_full_pipeline': '--exp03'}[a.experiment]
    dst.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, str(REPO / 'tools/summarize_rerun.py'), '--label', label, flag, str(src),
                        '--out', str(dst / 'RUN_RECORD.md'), '--operator', a.operator], stdout=subprocess.DEVNULL)
    if r.returncode:
        shutil.rmtree(dst)
        sys.exit('summarize_rerun.py failed; nothing imported')
    secrets = secret_values()
    n_paths = n_files = 0
    for f in dst.rglob('*'):
        if not f.is_file() or f.suffix not in TEXT:
            continue
        t = f.read_text(encoding='utf-8', errors='replace')
        if any(s in t for s in secrets):
            shutil.rmtree(dst)
            sys.exit(f'ABORTED: an API key value was found in {f.name}; nothing imported')
        new = t.replace(str(REPO), '<REPO>')
        new, n = sanitize_paths.sanitize_text(new)
        n += t.count(str(REPO))
        if new != t:
            f.write_text(new, encoding='utf-8')
            n_paths += n
        n_files += 1
    print(f'imported {n_files} files into {dst.relative_to(REPO)} ({n_paths} local paths replaced, '
          f'{len(secrets)} key values checked, 0 found). Logs and indexes stay in {src.relative_to(REPO) if src.is_relative_to(REPO) else src}.')
    if not secrets:
        print(f'WARNING: no key file at {paths.ENV_FILE}, so the key-value scan was skipped; '
              'set LRP_ENV_FILE and re-import (delete the imported folder first).')


if __name__ == '__main__':
    main()
