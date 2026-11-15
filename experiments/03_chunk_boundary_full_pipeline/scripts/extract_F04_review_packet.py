"""Read-only evidence extraction for manual F04 audit; not a model judge."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import json,re,datetime
ROOT=legacy_root('round4_full_20261030');R=ROOT/'round4_full_20261030';g=next(g for g in json.loads((R/'conditions/frozen_groups.json').read_text())['groups'] if g['id']=='F04')
pattern=re.compile(r'cost|pecuniary|monetary|price',re.I)
def relevant(x):return bool(pattern.search(json.dumps(x,ensure_ascii=False)))
rows=[]
for condition,repeat in [('A',1),('B',1),('B',2),('A',2),('A',3),('B',3)]:
 rid=f'F04_{condition}_r{repeat}';d=R/'results'/rid
 row={'run_id':rid,'condition':condition,'repeat':repeat,'status':'unrun'}
 if not (d/'status.json').exists():rows.append(row);continue
 row['status']=json.loads((d/'status.json').read_text());row['raw'] = []
 if (d/'parsed_extraction.json').exists():
  parsed=json.loads((d/'parsed_extraction.json').read_text())
  for c in parsed['records']:
   response=json.loads((R/'logs'/f"api_{c['call_id']:04d}_response.json").read_text())
   row['raw'].append({'call_id':c['call_id'],'chunk_id':c['chunk_id'],'finish_reason':c['finish_reason'],'completion_tokens':c['completion_tokens'],'delimiter_present':c['completion_delimiter_present'],'raw_relevant_lines':[line for line in response['content'].splitlines() if pattern.search(line)],'parsed_entities':[x for values in c['nodes'].values() for x in values if relevant(x)],'parsed_edges':[x for group in c['edges'] for x in group['records'] if relevant(x)]})
 if (d/'merged_graph.json').exists():
  graph=json.loads((d/'merged_graph.json').read_text());row['graph']={'counts':{'nodes':len(graph['nodes']),'edges':len(graph['edges'])},'entities':[x for x in graph['nodes'] if relevant(x)],'edges':[x for x in graph['edges'] if relevant(x)]}
 if (d/'natural_query.json').exists():
  q=json.loads((d/'natural_query.json').read_text())['result'];data=q.get('data',{});row['natural']={'status':q.get('status'),'entities':[x for x in data.get('entities',[]) if relevant(x)],'edges':[x for x in data.get('relationships',[]) if relevant(x)],'references':data.get('references'),'answer':q.get('llm_response',{}).get('content'),'chunks':[]}
  for c in data.get('chunks',[]):
   txt=c['content'];row['natural']['chunks'].append({'chunk_id':c.get('chunk_id'),'file_path':c.get('file_path'),'reference_id':c.get('reference_id'),'anchor_matches':{k:[a['quote'] for a in vals if a['quote'] in txt] for k,vals in g['evidence'].items()},'content':txt})
 if (d/'forced_diagnostic.json').exists():row['forced']=json.loads((d/'forced_diagnostic.json').read_text())
 rows.append(row)
result={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'Deterministic cost-keyword candidate extraction only; requires subsequent manual semantic adjudication. Unrun/running is not a failure score.','group':'F04','publication_number':'US8509827B2','runs':rows}
(R/'evidence/F04_review_packet.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps([{'run_id':x['run_id'],'status':x['status'] if isinstance(x['status'],str) else x['status'].get('status')} for x in rows]))
