"""Count graph nodes whose sources span two or more patents (experiment 04's first statistic). No API calls.

A node's patents = the publication numbers in its own `file_path` field (split at <SEP>), cross-checked
with `source_id` chunk ids (<publication>-chunk-NNN). Experiment 04 built the same count from
source_id ∪ entity_chunks → full_doc_id and reported 38 / 612 with 0 path/KV discrepancies.
Semantic review (reasonable sharing vs homonym) is NOT done here.

    python tools/count_multisource_nodes.py <graph_chunk_entity_relation.graphml> [...]
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

import networkx as nx

SEP = '<SEP>'


def count(graphml: Path) -> dict:
    g = nx.read_graphml(graphml)
    multi, mismatch = {}, 0
    for n, d in g.nodes(data=True):
        by_path = {p.removesuffix('.txt') for p in (d.get('file_path') or '').split(SEP) if p}
        by_src = {re.sub(r'-chunk-\d+$', '', s) for s in (d.get('source_id') or '').split(SEP) if s}
        if by_src and by_path != by_src:
            mismatch += 1
        if len(by_path | by_src) >= 2:
            multi[n] = sorted(by_path | by_src)
    dist = Counter(len(v) for v in multi.values())
    return {'graph': str(graphml), 'nodes': g.number_of_nodes(), 'edges': g.number_of_edges(),
            'multi_source_nodes': len(multi), 'share': round(len(multi) / g.number_of_nodes(), 4),
            'by_patent_count': dict(sorted(dist.items())), 'file_path_vs_source_id_mismatches': mismatch,
            'nodes_list': multi}


if __name__ == '__main__':
    for f in sys.argv[1:]:
        r = count(Path(f))
        print(json.dumps({k: v for k, v in r.items() if k != 'nodes_list'}, ensure_ascii=False))
