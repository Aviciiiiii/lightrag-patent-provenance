"""Convert dot's report HTML into readable Markdown (headings, paragraphs, lists, tables, code).

Content embedded in attributes (e.g. collapsed historical snapshots in iframe srcdoc)
is not converted; the HTML copy remains the complete version.
Usage: python tools/html_to_md.py IN.html OUT.md
"""
import re
import sys
from html.parser import HTMLParser


class _MD(HTMLParser):
    BLOCK = {'p', 'div', 'section', 'blockquote', 'pre', 'ul', 'ol', 'table', 'details', 'summary', 'figure'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.row, self.cell, self.in_table = [], 0, None, None, False
        self.list_stack, self.pre, self.header_done = [], False, False

    def _emit(self, text):
        if self.cell is not None:
            self.cell.append(text)
        else:
            self.out.append(text)

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'head', 'iframe', 'svg'):
            self.skip += 1
            return
        if self.skip:
            return
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.out.append('\n\n' + '#' * int(tag[1]) + ' ')
        elif tag == 'table':
            self.in_table, self.rows = True, []
        elif tag == 'tr':
            self.row = []
        elif tag in ('td', 'th'):
            self.cell = []
        elif tag in ('ul', 'ol'):
            self.list_stack.append(tag)
        elif tag == 'li':
            self._emit('\n' + '  ' * (len(self.list_stack) - 1) + '- ')
        elif tag == 'br':
            self._emit('<br>' if self.cell is not None else '\n')
        elif tag == 'pre':
            self.pre = True
            self.out.append('\n\n```\n')
        elif tag == 'code' and not self.pre:
            self._emit('`')
        elif tag in ('strong', 'b'):
            self._emit('**')
        elif tag == 'blockquote':
            self.out.append('\n\n> ')
        elif tag == 'a':
            href = dict(attrs).get('href')
            self._href = href if href and href.startswith('http') else None
            self._emit('[')
        elif tag in self.BLOCK:
            self.out.append('\n\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'head', 'iframe', 'svg'):
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag in ('td', 'th') and self.cell is not None and self.row is not None:
            self.row.append(re.sub(r'\s+', ' ', ''.join(self.cell)).strip().replace('|', '\\|'))
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        elif tag == 'table':
            if self.rows:
                width = max(len(r) for r in self.rows)
                rows = [r + [''] * (width - len(r)) for r in self.rows]
                lines = ['| ' + ' | '.join(rows[0]) + ' |', '|' + '---|' * width]
                lines += ['| ' + ' | '.join(r) + ' |' for r in rows[1:]]
                self.out.append('\n\n' + '\n'.join(lines) + '\n\n')
            self.in_table = False
        elif tag in ('ul', 'ol') and self.list_stack:
            self.list_stack.pop()
            self.out.append('\n')
        elif tag == 'pre':
            self.pre = False
            self.out.append('\n```\n\n')
        elif tag == 'code' and not self.pre:
            self._emit('`')
        elif tag in ('strong', 'b'):
            self._emit('**')
        elif tag == 'a':
            href = getattr(self, '_href', None)
            self._emit(f']({href})' if href else ']')
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6') or tag in self.BLOCK:
            self.out.append('\n\n')

    def handle_data(self, data):
        if self.skip:
            return
        if self.pre:
            self.out.append(data)
        else:
            # keep literal <SEP>, <TMP> etc. visible on GitHub (bare <...> would be read as HTML)
            self._emit(re.sub(r'\s+', ' ', data).replace('<', '&lt;').replace('>', '&gt;'))


def convert(html_text: str) -> str:
    p = _MD()
    p.feed(html_text)
    md = ''.join(p.out)
    md = re.sub(r'\[\]\([^)]*\)|\[\]', '', md)
    md = re.sub(r'[ \t]+\n', '\n', md)
    md = re.sub(r'\n{3,}', '\n\n', md)
    return md.strip() + '\n'


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding='utf-8') as f:
        text = convert(f.read())
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(text)
