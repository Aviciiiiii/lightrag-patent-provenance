"""Check every relative link and anchor in the repository's Markdown files (no network).
    python tools/check_links.py            # public files (everything except runs/ and local/)
    python tools/check_links.py --local    # also the maintained local copies in local/ (not local/zh_snapshot_*)
"""
import re, sys, unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LINK = re.compile(r'(?<!!)\[[^\]]*\]\(([^)\s]+)\)|!\[[^\]]*\]\(([^)\s]+)\)')


def slug(h: str) -> str:  # GitHub-style heading anchor
    h = re.sub(r'<[^>]+>', '', h).strip().lower()
    h = ''.join(c for c in h if c.isalnum() or c in ' -_' or unicodedata.category(c).startswith('L'))
    return h.replace(' ', '-')


def anchors(md: Path):
    out = set()
    for line in md.read_text(encoding='utf-8').splitlines():
        m = re.match(r'#{1,6}\s+(.*)', line)
        if m:
            out.add(slug(m.group(1)))
    return out


bad = []
def wanted(p):
    parts = p.relative_to(REPO).parts
    if parts[0] in ('runs', '.git'):
        return False
    if parts[0] == 'local':
        return '--local' in sys.argv and not parts[1].startswith('zh_snapshot')
    return True


files = [p for p in REPO.rglob('*.md') if wanted(p)]
for md in files:
    text = md.read_text(encoding='utf-8')
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    for m in LINK.finditer(text):
        target = m.group(1) or m.group(2)
        if re.match(r'^[a-z]+:', target):
            continue
        path, _, frag = target.partition('#')
        dest = (md.parent / path).resolve() if path else md
        if not dest.exists():
            bad.append(f'{md.relative_to(REPO)}: missing {target}')
        elif frag and dest.suffix == '.md' and slug(frag) not in anchors(dest) and frag not in anchors(dest):
            bad.append(f'{md.relative_to(REPO)}: missing anchor {target}')
print('\n'.join(bad) or f'all links ok ({len(files)} Markdown files)')
sys.exit(1 if bad else 0)
