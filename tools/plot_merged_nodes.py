"""Draw the 1-hop neighbourhood of merged (multi-patent) nodes from experiment 01's original graph.

Input : experiments/01_baseline_index_qa/results/full_graph.json (committed snapshot of the
        original 612-node / 994-edge graph; same content as the local GraphML)
Output: figures/merged_nodes.png and figures/merged_nodes_table.md (English, default);
        with --lang zh: local/zh/figures/merged_nodes.png and merged_nodes_table.md (not committed)
Edges and neighbour nodes are coloured by the patent(s) in their own file_path field.
No API calls.  Requires: pip install -r requirements-figures.txt
    python tools/plot_merged_nodes.py [--nodes Token Tokens] [--lang zh]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402
from matplotlib import font_manager  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
GRAPH = REPO / 'experiments/01_baseline_index_qa/results/full_graph.json'
SEP = '<SEP>'
PALETTE = ['#1f77b4', '#d62728', '#2ca02c', '#9467bd', '#ff7f0e', '#8c564b', '#e377c2', '#17becf', '#bcbd22']
MULTI = '#7f7f7f'
CJK = ['PingFang SC', 'Hiragino Sans GB', 'STHeiti', 'Heiti SC', 'Songti SC', 'Arial Unicode MS', 'Noto Sans CJK SC']


def set_cjk_font():
    names = {f.name for f in font_manager.fontManager.ttflist}
    for n in CJK:
        if n in names:
            plt.rcParams['font.family'] = [n, 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            return n
    return None


def docs(rec) -> list[str]:
    return [p.removesuffix('.txt') for p in (rec.get('file_path') or '').split(SEP) if p]


def load_graph():
    raw = json.loads(GRAPH.read_text())
    g = nx.Graph()
    for n in raw['nodes']:
        g.add_node(n['id'], **n)
    for e in raw['edges']:
        g.add_edge(e['source'], e['target'], **e)
    return g


def draw(ax, g, center, colours, used):
    nbrs = list(g.neighbors(center))
    sub = g.subgraph([center] + nbrs)
    pos = nx.spring_layout(sub, seed=7, k=1.1)
    pos[center] = (0.0, 0.0)
    for u, v, d in sub.edges(data=True):
        ds = docs(d)
        c = colours[ds[0]] if len(ds) == 1 else MULTI
        used.update(ds[:1] if len(ds) == 1 else [])
        ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]], color=c, lw=1.6 if len(ds) == 1 else 2.6,
                ls='-' if len(ds) == 1 else '--', alpha=.85, zorder=1)
    for n in sub.nodes:
        ds = docs(g.nodes[n])
        c = colours[ds[0]] if len(ds) == 1 else MULTI
        used.update(ds[:1] if len(ds) == 1 else [])
        size = 900 if n == center else 260
        ax.scatter(*pos[n], s=size, c=c, edgecolors='black' if n == center else 'white', linewidths=1.5, zorder=2)
        ax.annotate(n, pos[n], fontsize=9 if n == center else 7, ha='center', va='bottom',
                    xytext=(0, 14 if n == center else 6), textcoords='offset points',
                    fontweight='bold' if n == center else 'normal', zorder=3)
    ax.set_axis_off()


TEXT = {
    'zh': {'title': lambda n, k, ps: f'"{n}"：合并自 {k} 篇专利（{ps}）', 'multi': '多篇专利（合并）',
           'sup': '实验 01 原始图谱中的同名合并节点（1 跳邻居；颜色 = 该节点/边自身 file_path 中的专利）', 'suffix': ''},
    'en': {'title': lambda n, k, ps: f'"{n}": merged from {k} patents ({ps})', 'multi': 'several patents (merged)',
           'sup': "Same-name merged nodes in experiment 01's original graph (1-hop neighbours; colour = patent in the node's/edge's own file_path)",
           'suffix': '_en'},
}


def main(nodes, lang='zh'):
    T = TEXT[lang]
    font = set_cjk_font()
    g = load_graph()
    patents = sorted({p for n in nodes for p in docs(g.nodes[n])} |
                     {p for n in nodes for nb in g.neighbors(n) for p in docs(g.nodes[nb])} |
                     {p for n in nodes for _, _, d in g.edges(n, data=True) for p in docs(d)})
    colours = {p: PALETTE[i % len(PALETTE)] for i, p in enumerate(patents)}
    fig, axes = plt.subplots(1, len(nodes), figsize=(7.2 * len(nodes), 6.4))
    axes = [axes] if len(nodes) == 1 else axes
    used = set()
    for ax, n in zip(axes, nodes):
        draw(ax, g, n, colours, used)
        ax.set_title(T['title'](n, len(docs(g.nodes[n])), ', '.join(docs(g.nodes[n]))), fontsize=10)
    handles = [plt.Line2D([], [], color=c, lw=3, label=p) for p, c in colours.items() if p in used]
    handles.append(plt.Line2D([], [], color=MULTI, lw=3, ls='--', label=T['multi']))
    fig.legend(handles=handles, loc='lower center', ncol=min(6, len(handles)), fontsize=8, frameon=False)
    fig.suptitle(T['sup'], fontsize=11)
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    fig_dir = REPO / 'figures' if lang == 'en' else REPO / 'local/zh/figures'
    out = fig_dir / 'merged_nodes.png'
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)

    rows = []
    for n in nodes:
        d = g.nodes[n]
        segs = [s.strip() for s in d['description'].split(SEP)]
        rows.append(f"| {n} | {', '.join(docs(d))} | " + '<br>'.join(f'({i+1}) {s}' for i, s in enumerate(segs)) + ' |')
    head = ('| 节点名 | 来自哪些专利（file_path） | 合并后的描述（按 `<SEP>` 拆开，原样） |' if lang == 'zh'
            else '| Node | from patents (file_path) | merged description (split at `<SEP>`, verbatim) |')
    (fig_dir / 'merged_nodes_table.md').write_text(head + '\n|---|---|---|\n' + '\n'.join(rows) + '\n', encoding='utf-8')
    print(out, 'font:', font)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--nodes', nargs='+', default=['Token', 'Tokens'])
    ap.add_argument('--lang', choices=['en', 'zh'], default='en')
    a = ap.parse_args()
    main(a.nodes, a.lang)
