"""Read-only output collection for manual, frozen-predicate F05 evaluation; no API."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import json,re,datetime
ROOT=legacy_root('round4_full_20261030');R=ROOT/'round4_full_20261030'
g=next(x for x in json.loads((R/'conditions/frozen_groups.json').read_text())['groups'] if x['id']=='F05')
rx=re.compile(r'na[iï]ve|bayes|filter|classifi|memory|persistent',re.I)
def load(p):return json.loads(p.read_text()) if p.exists() else None
def relevant(x):return bool(rx.search(json.dumps(x,ensure_ascii=False)))
rows=[]
for c,n in [('A',1),('B',1),('B',2),('A',2),('A',3),('B',3)]:
 rid=f'F05_{c}_r{n}';base=R/'results'/rid;status=load(base/'status.json')
 out={'run_id':rid,'status':status,'actual_chunking':load(base/'actual_chunking.json')}
 if status is None:out['execution']='not_run_or_no_status_yet';rows.append(out);continue
 out['parsed_extraction']=load(base/'parsed_extraction.json');out['raw_extraction_candidates']=[]
 if out['parsed_extraction']:
  for a in out['parsed_extraction']['records']:
   resp=load(R/'logs'/f"api_{a['call_id']:04d}_response.json")
   out['raw_extraction_candidates'].append({'call_id':a['call_id'],'chunk_id':a['chunk_id'],'finish_reason':a['finish_reason'],'completion_tokens':a['completion_tokens'],'content_lines':[{'line':i+1,'text':l} for i,l in enumerate(resp['content'].splitlines()) if relevant(l)]})
 graph=load(base/'merged_graph.json');out['graph_candidates']=None
 if graph:out['graph_candidates']={'nodes':[dict(record_index=i,**x) for i,x in enumerate(graph['nodes']) if relevant(x)],'edges':[dict(record_index=i,**x) for i,x in enumerate(graph['edges']) if relevant(x)],'total_nodes':len(graph['nodes']),'total_edges':len(graph['edges'])}
 nat=load(base/'natural_query.json');out['natural']=None
 if nat:
  d=nat['result'].get('data') or {};chunks=d.get('chunks',[])
  out['natural']={'status':nat['result'].get('status'),'entities':[x for x in d.get('entities',[]) if relevant(x)],'relationships':[x for x in d.get('relationships',[]) if relevant(x)],'chunks':chunks,'references':d.get('references',[]),'answer':nat['result'].get('llm_response',{}),'literal_anchors_in_retrieved_chunks':{fam:[{'quote':a['quote'],'retrieved_chunk_indices':[i for i,c in enumerate(chunks) if a['quote'] in c['content']]} for a in anchors] for fam,anchors in g['evidenceanchors'].items()},'full_diagnostic_claims_in_retrieved_chunks':{str(a['claim_number']):[i for i,c in enumerate(chunks) if a['text'] in c['content']] for a in g['claims']}}
 out['forced']=load(base/'forced_diagnostic.json');rows.append(out)
x={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Candidate excerpts for manual researcher review; lexical search is not final gold scoring','publication_number':g['publication_number'],'predicates':g['researcher_predicate'],'runs':rows}
(R/'evidence/F05_candidate_evidence.json').write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'runs':[{ 'id':r['run_id'],'status':(r['status'] or {}).get('status','not_run')} for r in rows]},indent=2))
