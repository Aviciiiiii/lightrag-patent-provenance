"""One pinned official Git source for both B-group offline parser wrappers."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root, PINNED_SOURCE  # path mapping only, see paths.py
import hashlib
import os
from pathlib import Path
import subprocess

ROOT = legacy_root('round3')
EXPECTED_COMMIT = '28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c'
SOURCE = Path(os.environ.get('LIGHTRAG_REPRO_SOURCE',
                            str(PINNED_SOURCE))).expanduser().resolve()
OFFICIAL_ORIGINS = {'https://github.com/HKUDS/LightRAG.git',
                    'https://github.com/HKUDS/LightRAG',
                    'git@github.com:HKUDS/LightRAG.git'}


def git_read(*args):
    # Ignore caller repository overrides; do not refresh the index or run fsmonitor.
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update(GIT_OPTIONAL_LOCKS='0', GIT_NO_REPLACE_OBJECTS='1')
    result = subprocess.run(
        ['git', '--no-optional-locks', '-c', 'core.fsmonitor=false',
         '-c', 'core.untrackedCache=false', '-C', str(SOURCE), *args],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if result.returncode:
        raise RuntimeError('Pinned official Git checkout check failed: ' + args[0])
    return result.stdout


def verify_source(selected_files):
    if not SOURCE.is_dir():
        raise RuntimeError('Pinned official source directory is missing')
    top = Path(git_read('rev-parse', '--show-toplevel').decode().strip()).resolve()
    if top != SOURCE:
        raise RuntimeError('SOURCE must be the Git checkout root, not an unpacked subdirectory')
    commit = git_read('rev-parse', '--verify', 'HEAD^{commit}').decode().strip()
    if commit != EXPECTED_COMMIT:
        raise RuntimeError('Official parser requires the exact pinned commit')
    if git_read('remote', 'get-url', 'origin').decode().strip() not in OFFICIAL_ORIGINS:
        raise RuntimeError('Source origin must be the official HKUDS/LightRAG repository')
    if git_read('status', '--porcelain=v1', '-z', '--untracked-files=all'):
        raise RuntimeError('Official checkout has staged, unstaged or untracked changes')
    hashes = {}
    for relative in selected_files:
        path = SOURCE / relative
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(SOURCE):
            raise RuntimeError('Official parser source must be a regular in-checkout file: ' + relative)
        data = path.read_bytes()
        if data != git_read('show', EXPECTED_COMMIT + ':' + relative):
            raise RuntimeError('Official parser source differs from the pinned Git blob: ' + relative)
        hashes[relative] = hashlib.sha256(data).hexdigest()
    return {'official_source_root': str(SOURCE), 'official_commit': commit,
            'git_worktree_clean': True, 'official_origin_verified': True,
            'selected_files_equal_pinned_git_blobs': True,
            'selected_file_sha256': hashes}
