"""Replace local absolute paths with placeholders. Used for every copied text file.

Placeholders (documented in docs/NAMING.md):
  <DOT_WORKDIR>   dot's original working directory (<HOME>/Documents/Codex/2026-10-29/task/lightrag_patent_20261029)
  <ORIG_COPY>     the user's local copies of dot's package (<HOME>/Downloads/LightRAG_NEW_{A,B,C}, LightRAG_OFFLINE, ...)
  <HOME>          the user's home directory
  <EXTERNAL_DISK> external disk that held the private .env
  <TMP>           macOS system temp dir (private tmp)
  <VAR_FOLDERS>   macOS per-user temp dir
Usage: python tools/sanitize_paths.py FILE... (in place; prints replacement counts)
"""
import re, sys
from pathlib import Path

U, V, PT = '/' + 'Users/', '/' + 'Volumes/', '/' + 'private/'
RULES = [
    (re.compile(U + r'[^/\s"\'<>]+/Documents/Codex/2026-10-29/task/lightrag_patent_20261029'), '<DOT_WORKDIR>'),
    (re.compile(U + r'[^/\s"\'<>]+/Downloads/(LightRAG_[A-Za-z0-9_]+)'), r'<ORIG_COPY>/\1'),
    (re.compile(U + r'[^/\s"\'<>]+'), '<HOME>'),
    (re.compile(V + r'[^/\s"\'<>]+'), '<EXTERNAL_DISK>'),
    (re.compile(PT + r'var/folders/[^\s"\'<>]*|/var/folders/[^\s"\'<>]*'), '<VAR_FOLDERS>'),
    (re.compile(PT + 'tmp'), '<TMP>'),
    (re.compile(r'(?<![\w.<])/tmp/'), '<TMP>/'),
]

def sanitize_text(text):
    total = 0
    for rx, rep in RULES:
        text, n = rx.subn(rep, text)
        total += n
    return text, total

def main(paths):
    grand = 0
    for p in map(Path, paths):
        try:
            raw = p.read_text(encoding='utf-8')
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        new, n = sanitize_text(raw)
        if n:
            p.write_text(new, encoding='utf-8')
            print(f'{n}\t{p}')
            grand += n
    print(f'TOTAL\t{grand}')

if __name__ == '__main__':
    main(sys.argv[1:])
