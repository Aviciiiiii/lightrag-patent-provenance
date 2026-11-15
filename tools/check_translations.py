"""Check that a translated Markdown file carries the same numbers as its English source. No API calls.

Numbers are compared per section (## headings, matched by position) as multisets of numeric tokens
(digits with . , / – - kept together, e.g. 242/242, 0.65, 2026-11-15, US7991757B2's digits are ignored
because identifiers are dropped). Prints differences; exit code 1 if any.

    python tools/check_translations.py README.md README_zh.md
    python tools/check_translations.py --pairs        # all known en/zh pairs (zh copies may be local-only)
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PAIRS = [
    ('README.md', 'README_zh.md'),
    ('docs/SETUP.md', 'local/zh/SETUP.md'),
    ('experiments/01_baseline_index_qa/README.md', 'local/zh/experiments/01_baseline_index_qa/README.md'),
    ('experiments/02_provenance_ablation_and_chunk_control/README.md', 'local/zh/experiments/02_provenance_ablation_and_chunk_control/README.md'),
    ('experiments/03_chunk_boundary_full_pipeline/README.md', 'local/zh/experiments/03_chunk_boundary_full_pipeline/README.md'),
    ('experiments/04_merged_node_audit/README.md', 'local/zh/experiments/04_merged_node_audit/README.md'),
]
ID = re.compile(r'(US\d+[AB]\d|[0-9a-f]{7,40}|api_\d+|#L\d+(-L\d+)?|L\d+(–L\d+)?|\]\([^)]*\)|`[^`]*`)')
NUM = re.compile(r'(?<![\w.])\d[\d,.]*(?:/\d[\d,.]*)?(?:[–-]\d[\d,.]*)?')


def sections(text: str) -> list[tuple[str, Counter]]:
    out, title, buf = [], '(top)', []
    for line in text.splitlines() + ['## (end)']:
        if line.startswith('## '):
            out.append((title, Counter(n.rstrip('.,') for n in NUM.findall(ID.sub(' ', '\n'.join(buf))))))
            title, buf = line[3:].strip(), []
        else:
            buf.append(line)
    return out


def compare(a: Path, b: Path) -> int:
    sa, sb = sections(a.read_text()), sections(b.read_text())
    bad = 0
    if len(sa) != len(sb):
        print(f'{b}: {len(sb)} sections vs {len(sa)} in {a}')
        bad += 1
    for (ta, ca), (tb, cb) in zip(sa, sb):
        if ca != cb:
            bad += 1
            print(f'{a} [{ta}] vs {b} [{tb}]: only en {dict(ca - cb)}  only zh {dict(cb - ca)}')
    return bad


def main():
    if sys.argv[1:] == ['--pairs']:
        pairs = [(REPO / x, REPO / y) for x, y in PAIRS if (REPO / x).exists() and (REPO / y).exists()]
    else:
        pairs = [(Path(sys.argv[1]), Path(sys.argv[2]))]
    bad = sum(compare(a, b) for a, b in pairs)
    print(f'{len(pairs)} pairs checked, {bad} differences')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
