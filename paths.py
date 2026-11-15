"""Central path mapping for dot's experiment scripts.

dot's scripts were written for one package directory laid out like this:

    <package>/data/...                       input patents
    <package>/results/, evidence/, logs/      round1 (data preparation, no LLM)
    <package>/round2/                         experiment 01
    <package>/round3/                         experiment 02
    <package>/round4_full_20261030/           experiment 03
    <package>/round2_multisource_audit/       experiment 04
    <package>/round4/, env_diagnostics_*/     pilot / diagnostics (local only here)
    <package>/src/LightRAG-v1.5.7/            vendored LightRAG source
    <package>/tiktoken_cache/                 tokenizer cache
    <package>/config/repro_session.json       run session

Each script computed that root with ``Path(__file__).resolve().parents[N]`` and
joined legacy relative paths onto it (``ROOT/'round2/results'``). The only code
change made to those scripts is to obtain ROOT from :func:`legacy_root` instead.
``legacy_root(owner)`` returns a path-like object that keeps the legacy relative
path and resolves it through :data:`EXPERIMENTS` / :func:`resolve_legacy` when it
is used. No experimental logic, parameter or prompt is touched.

Rules
-----
* ``roundX/...``            -> ``experiments/<NN_name>/...``
* ``round2/storage_full/...`` (experiment 01's original index) -> the committed copy in
  ``experiments/01_baseline_index_qa/index/...``; ``runs/01_baseline_index_qa/original/storage_full/...``
  only if the committed copy is absent
* other local-only sub-folders of an experiment (full API logs, LightRAG working
  dirs, regenerated report HTML) -> ``runs/<NN_name>/original/...``
* ``src/LightRAG-v1.5.7/...`` -> the pip-installed ``lightrag-hku==1.5.7``
  (its ``.py`` files are byte-identical to commit 28ff1b05, see docs/AUDIT.md)
* round1 folders (``results``, ``evidence``, ``logs``, ``scripts``) -> ``data/round1/...``
* ``tiktoken_cache`` -> ``runs/tiktoken_cache``; ``round4``/``env_diagnostics_20261030`` -> ``runs/archive/...``
* ``config/...`` -> ``<experiment dir>/config/...`` (one session per experiment)
* ``roundX/scripts/...`` -> always the committed ``experiments/<NN_name>/scripts/`` (also during reruns)

Fresh live reruns: ``experiments/*/run.sh`` sets ``LRP_RUN_FOR=<legacy name>`` and
``LRP_RUN_DIR=runs/rerun_<exp>_<timestamp>``. That experiment's legacy folder then
maps to the fresh run directory (outputs never overwrite the committed results);
every other experiment keeps pointing at its frozen original files.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parent
RUNS = REPO / 'runs'
ENV_FILE = Path(os.environ.get('LRP_ENV_FILE') or (REPO / '.env')).expanduser()
PINNED_SOURCE = Path(os.environ.get('LIGHTRAG_REPRO_SOURCE') or (RUNS / 'LightRAG_PINNED_28ff1b05')).expanduser()

EXPERIMENTS = {
    'round2': '01_baseline_index_qa',
    'round3': '02_provenance_ablation_and_chunk_control',
    'round4_full_20261030': '03_chunk_boundary_full_pipeline',
    'round2_multisource_audit': '04_merged_node_audit',
}
# sub-folders that stay out of git (see .gitignore / runs/README.md)
LOCAL_ONLY = {
    'round2': {'logs', 'storage_full', 'storage_smoke', 'report'},
    'round3': {'logs', 'report'},
    'round4_full_20261030': {'logs', 'storage', 'report'},
    'round2_multisource_audit': set(),
}
ROUND1_DIRS = {'results', 'evidence', 'logs', 'scripts'}
# single files moved out of git (LightRAG source archives, deduplicated -> runs/archive/)
MOVED_FILES = {
    'round2/evidence/official_core_v1.5.7.tar.gz': 'archive/round2_official_core_v1.5.7.tar.gz',
    'evidence/official_LightRAG_v1.5.7_source_sanitized.tar.gz': 'archive/official_LightRAG_v1.5.7_source_sanitized.tar.gz',
}
ARCHIVED = {'round4', 'env_diagnostics_20261030'}
# experiment 01's original LightRAG index (workspace patent_r2_full), committed; runs/ is the fallback
ORIGINAL_INDEX = REPO / 'experiments' / '01_baseline_index_qa' / 'index'
ORIGINAL_INDEX_WORKSPACE = 'patent_r2_full'


def original_index_dir() -> Path:
    """Folder that contains the workspace ``patent_r2_full`` of experiment 01's original run."""
    if (ORIGINAL_INDEX / ORIGINAL_INDEX_WORKSPACE).is_dir():
        return ORIGINAL_INDEX
    return RUNS / '01_baseline_index_qa' / 'original' / 'storage_full'


def lightrag_site() -> Path:
    """Directory that contains the installed ``lightrag`` package."""
    spec = importlib.util.find_spec('lightrag')
    if spec is None or not spec.origin:
        raise RuntimeError('LightRAG is not installed; run: pip install -r requirements.txt')
    return Path(spec.origin).resolve().parent.parent


def experiment_dir(legacy_name: str) -> tuple[Path, bool]:
    """(directory, is_committed_original) for a legacy experiment folder name."""
    if os.environ.get('LRP_RUN_FOR') == legacy_name and os.environ.get('LRP_RUN_DIR'):
        return Path(os.environ['LRP_RUN_DIR']).expanduser().resolve(), False
    return REPO / 'experiments' / EXPERIMENTS[legacy_name], True


def resolve_legacy(rel: str, owner: str | None = None) -> Path:
    parts = [p for p in PurePosixPath(rel.replace('\\', '/')).parts if p not in ('.', '/')]
    if not parts:
        return REPO
    head, rest = parts[0], parts[1:]
    if '/'.join(parts) in MOVED_FILES:
        return RUNS / MOVED_FILES['/'.join(parts)]
    if head in EXPERIMENTS:
        if rest and rest[0] == 'scripts':  # code always comes from the repository, also during reruns
            return REPO.joinpath('experiments', EXPERIMENTS[head], *rest)
        base, original = experiment_dir(head)
        if head == 'round2' and original and rest and rest[0] == 'storage_full':
            return original_index_dir().joinpath(*rest[1:])
        if rest and original and rest[0] in LOCAL_ONLY[head]:
            return RUNS / EXPERIMENTS[head] / 'original' / Path(*rest)
        return base.joinpath(*rest)
    if head == 'src' and len(parts) >= 2 and parts[1] == 'LightRAG-v1.5.7':
        return lightrag_site().joinpath(*parts[2:])
    if head == 'tiktoken_cache':
        return RUNS.joinpath('tiktoken_cache', *rest)
    if head == 'config':
        if owner in EXPERIMENTS:
            return experiment_dir(owner)[0].joinpath('config', *rest)
        return RUNS.joinpath('config', *rest)
    if head in ROUND1_DIRS:
        return REPO.joinpath('data', 'round1', head, *rest)
    if head == 'report':  # round1 report output; the committed copy is in reports/original/
        return RUNS.joinpath('round1_report', *rest)
    if head in ARCHIVED:
        return RUNS.joinpath('archive', head, *rest)
    return REPO.joinpath(*parts)


class LegacyPath(os.PathLike):
    """Path-like stand-in for dot's package ROOT; resolves lazily via resolve_legacy()."""

    __slots__ = ('_rel', '_owner')

    def __init__(self, rel: str = '', owner: str | None = None):
        self._rel = rel.strip('/')
        self._owner = owner

    def _path(self) -> Path:
        return resolve_legacy(self._rel, self._owner)

    def __truediv__(self, other) -> 'LegacyPath':
        other = os.fspath(other) if isinstance(other, os.PathLike) else str(other)
        if os.path.isabs(other):
            return Path(other)  # type: ignore[return-value]
        return LegacyPath(f'{self._rel}/{other}' if self._rel else other, self._owner)

    def joinpath(self, *others) -> 'LegacyPath':
        out = self
        for o in others:
            out = out / o
        return out

    def __fspath__(self) -> str:
        return str(self._path())

    def __str__(self) -> str:
        return str(self._path())

    def __repr__(self) -> str:
        return f'LegacyPath({self._rel!r} -> {self._path()})'

    def __eq__(self, other) -> bool:
        try:
            return self._path() == Path(os.fspath(other))
        except TypeError:
            return NotImplemented

    def __hash__(self) -> int:
        return hash(self._path())

    def __getattr__(self, name):
        return getattr(self._path(), name)


def legacy_root(owner: str | None = None) -> LegacyPath:
    """Replacement for dot's ``Path(__file__).resolve().parents[N]`` package root."""
    return LegacyPath('', owner)
