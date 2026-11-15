"""Read-only check of assigned content-review evidence, no external calls."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
import json, re, hashlib
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
ROOT=legacy_root('round2_multisource_audit')
OUT=ROOT/'round2_multisource_audit'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
errors=[];records=[];edges=set();chunks=set()
for i in range(14,27):
 aid=f'N{i:03d}'
 rp=OUT/'reviews'/f'{aid}.json';dp=OUT/'dossiers'/f'{aid}.json'
 r=json.loads(rp.read_text());d=json.loads(dp.read_text())
 if {s['publication_number'] for s in r['source_assessments']}!=set(d['canonical_publications']):errors.append([aid,'publication coverage'])
 for s in r['source_assessments']:
  p=s['publication_number'];ds=next(v for v in d['source_documents'] if v['publication_number']==p)
  if set(s['source_chunk_ids'])!=set(ds['source_chunks']):errors.append([aid,p,'source chunk coverage'])
  q=s['evidence_quote'];matches=[c['chunk_id'] for c in ds['sources'] if q in c['content']]
  if not matches:errors.append([aid,p,'quote not in actual source'])
  claim_match=re.fullmatch(r'Claim (\d+)',s['claim_or_section'])
  if claim_match:
   cs=json.loads((ROOT/'data'/'claims'/f'{p}.json').read_text())
   c=next((v for v in cs if v['claim_number']==int(claim_match.group(1))),None)
   if c is None or q not in c['text']:errors.append([aid,p,'quote not in named claim'])
  elif s['claim_or_section']!='Abstract':errors.append([aid,p,'unexpected section'])
  original_edges={e['edge_index'] for e in ds['incident_edges_from_publication']}
  review_edges={e if isinstance(e,int) else e['edge_index'] for e in s['relevant_actual_edges']}
  if original_edges!=review_edges:errors.append([aid,p,'source edge coverage'])
 nb=r['neighbor_audit'];count=nb.get('reviewed_incident_edge_count',nb.get('incident_edge_count'))
 ids=nb.get('edge_indices',nb.get('all_incident_edge_indices'))
 if count!=d['incident_edge_count'] or set(ids)!={e['edge_index'] for e in d['all_incident_edges']}:errors.append([aid,'neighbor edge coverage'])
 edges.update(ids);chunks.update(d['all_source_chunks'])
 records.append({'audit_id':aid,'node_id':r['node_id'],'category':r['category'],'confidence':r['confidence'],
  'publications_reviewed':len(r['source_assessments']),'incident_edges_reviewed':count,
  'review_file_sha256':sha(rp),'dossier_sha256':sha(dp)})
result={'validated_utc':datetime.now(timezone.utc).isoformat(),'scope':'N014–N026',
 'review_kind':'AI-assisted source review, not independent human gold',
 'semantic_decisions_validated_by_script':False,
 'checks':'publication/chunk/edge membership and exact source/Claim quotation checks only',
 'errors':errors,'records':records,'categories':dict(Counter(r['category'] for r in records)),
 'source_node_pairs':sum(r['publications_reviewed'] for r in records),
 'incident_edge_reviews_with_duplicates':sum(r['incident_edges_reviewed'] for r in records),
 'unique_incident_edges':len(edges),'unique_source_chunks':len(chunks),
 'external_model_api_calls':0,'credentials_read':False}
(OUT/'evidence'/'N014_N026_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='records'},ensure_ascii=False))
raise SystemExit(bool(errors))
