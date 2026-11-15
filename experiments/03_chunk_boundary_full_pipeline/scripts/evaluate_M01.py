"""Inventory new official M01 runs only, with manual semantic review added after completion."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import json,re,datetime,sys
ROOT=legacy_root('round4_full_20261030');R=ROOT/'round4_full_20261030';G=next(g for g in json.loads((R/'conditions/frozen_groups.json').read_text())['groups'] if g['id']=='M01')
if (R/'evidence/M01_scope_update.json').exists():
 print(json.dumps({'status':'not_run_by_scope_update','note':'Existing M01_evaluation.json intentionally remains unscored; do not mix older experiments.'}));sys.exit(0)

def norm(s):return re.sub(r'\s+',' ',str(s).lower().replace('-',' '))
def pred(record,k):
 s=norm(json.dumps(record,ensure_ascii=False));module='registration module' in s
 if k=='R1':return module and 'external recommender' in s and ('recommendation service' in s or 'recommendations service' in s) and ('register' in s or 'registration' in s)
 return module and 'provider' in s and 'external recommender' in s and 'machine readable description' in s and any(q in s for q in ['allow','permit','enable'])
KEYS=['R1','R2']
def pick(records):return {k:[x for x in records if pred(x,k)] for k in KEYS}
def small(r):return {k:r[k] for k in ['id','entity_id','entity_name','entity_type','source','target','src_id','tgt_id','description','keywords','source_id','file_path','call_id'] if k in r}
def module_id(n):return 'registration module' in norm(n.get('id',n.get('entity_id',n.get('entity_name',''))))
def dep_answer(s):return bool(re.search(r'claim\s*27.{0,100}(depend|incorporat|refers|adds|further|limits).{0,100}claim\s*1\b',norm(s)) or re.search(r'claim\s*27.{0,70}system of claim\s*1',norm(s)) or re.search(r'depend.{0,60}claim\s*1.{0,100}claim\s*27',norm(s)))
rows=[]
for cond,n in [('A',1),('B',1),('B',2),('A',2),('A',3),('B',3)]:
 rid=f'M01_{cond}_r{n}';B=R/'results'/rid
 if not(B/'status.json').exists():rows.append({'run_id':rid,'condition':cond,'repeat':n,'status':'not_started','eligible':False});continue
 status=json.loads((B/'status.json').read_text());row={'run_id':rid,'condition':cond,'repeat':n,'status':status['status'],'eligible':False}
 if status['status']!='completed':rows.append(row);continue
 p=json.loads((B/'parsed_extraction.json').read_text());graph=json.loads((B/'merged_graph.json').read_text());natural=json.loads((B/'natural_query.json').read_text());forced=json.loads((B/'forced_diagnostic.json').read_text());out=natural['result'];data=out.get('data',{});ans=out.get('llm_response',{}).get('content','')
 rawr=[];rawe=[];pe=[];pn=[];pc=[]
 for rec in p['records']:
  cid=rec['call_id'];rr=json.loads((R/'logs'/f'api_{cid:04d}_response.json').read_text());rawlines=rr['content'].splitlines();rl=[v for v in rawlines if v.startswith('relation<|#|>')];el=[v for v in rawlines if v.startswith('entity<|#|>')]
  rawr += [{'call_id':cid,'chunk_id':rec['chunk_id'],'row':v} for v in rl];rawe += [{'call_id':cid,'chunk_id':rec['chunk_id'],'row':v} for v in el]
  pe += [dict(v,call_id=cid) for group in rec['edges'] for v in group['records']];pn += [dict(v,call_id=cid) for records in rec['nodes'].values() for v in records]
  pc.append({'call_id':cid,'chunk_id':rec['chunk_id'],'finish_reason':rr['finish_reason'],'completion_tokens':rr.get('usage',{}).get('completion_tokens'),'completion_delimiter_present':rec['completion_delimiter_present'],'raw_relation_rows':len(rl),'parsed_relation_records':sum(len(z['records']) for z in rec['edges']),'raw_entity_rows':len(el),'parsed_entity_records':sum(len(v) for v in rec['nodes'].values())})
 rp=pick(rawr);ep=pick(rawe);pp=pick(pe);mp=pick(graph['edges']);np=pick(graph['nodes']);tp=pick(data.get('relationships',[]));tn=pick(data.get('entities',[]));truncated=[x['call_id'] for x in pc if x['finish_reason']=='length']
 modules=[small(x) for x in graph['nodes'] if module_id(x)];module_ids={x.get('id',x.get('entity_id',x.get('entity_name'))) for x in modules};support_ids={k:sorted({v for e in mp[k] for v in [e.get('source'),e.get('target')] if v in module_ids}) for k in KEYS};common=set(support_ids['R1'])&set(support_ids['R2'])
 raw_module_nodes=[small(x) for x in pn if module_id(x)];chunks=data.get('chunks',[]);anchors={x['id']:x['quote'] for x in G['evidenceanchors']};anchor_hits={k:[c['chunk_id'] for c in chunks if norm(v) in norm(c['content'])] for k,v in anchors.items()};claim_hits={k:[c['chunk_id'] for c in chunks if norm(v['content']) in norm(c['content'])] for k,v in G['claims'].items()};graph_claim_nodes=[small(x) for x in graph['nodes'] if re.search(r'claim\s*(1|27)\b',str(x.get('id','')),re.I)];graph_claim_edges=[small(x) for x in graph['edges'] if re.search(r'claim\s*1\b',str(x),re.I) and re.search(r'claim\s*27\b',str(x),re.I)]
 row.update(eligible=not truncated,truncated_extraction_ids=truncated,parser_checks=pc,raw_relation_retention={k:bool(v) for k,v in rp.items()},raw_entity_description_retention={k:bool(v) for k,v in ep.items()},parsed_relation_retention={k:bool(v) for k,v in pp.items()},merged_relation_retention={k:bool(v) for k,v in mp.items()},merged_entity_description_retention={k:bool(v) for k,v in np.items()},graph_counts={'nodes':len(graph['nodes']),'edges':len(graph['edges'])},raw_support=rp,raw_entity_support=ep,parsed_support={k:[small(v) for v in x] for k,x in pp.items()},merged_support={k:[small(v) for v in x] for k,x in mp.items()},merged_node_support={k:[small(v) for v in x] for k,x in np.items()},registration_module_identity={'raw_chunk_nodes':raw_module_nodes,'actual_merged_nodes':modules,'actual_ids_supporting_each_relation':support_ids,'shared_actual_ids':sorted(common),'joint_actual_endpoint_identity_retained':bool(common),'semantic_aliases_not_silently_merged':True},claim_structure={'nodes':graph_claim_nodes,'edges':graph_claim_edges,'explicit_claim27_to_claim1_edge':bool(graph_claim_edges)},natural={'status':out.get('status'),'llm_generated':out.get('llm_response',{}).get('llm_generated'),'chunk_ids':[c['chunk_id'] for c in chunks],'exact_target_anchor_chunks':anchor_hits,'full_claim_chunks':claim_hits,'both_original_target_clauses_retrieved':all(bool(v) for v in anchor_hits.values()),'both_full_original_claims_retrieved':all(bool(v) for v in claim_hits.values()),'explicit_original_dependency_words_retrieved':any('the system of claim 1' in norm(c['content']) for c in chunks),'retrieved_relation_retention':{k:bool(v) for k,v in tp.items()},'retrieved_node_description_retention':{k:bool(v) for k,v in tn.items()},'references':data.get('references',[]),'answer':ans,'publication_present':'US7991757B2' in ans,'claim1_and27_present':bool(re.search(r'claim\s*1\b',ans,re.I) and re.search(r'claim\s*27\b',ans,re.I)),'dependency_statement_candidate':dep_answer(ans)},forced={'call_id':forced['call_id'],'content':forced['content'],'not_natural_score':True,'dependency_statement_candidate':dep_answer(forced['content'])},source={'publication_number':G['publication_number'],'scope':G['scope'],'content_sha256':G['content_sha256'],'claim1':G['claims']['1']['content'],'claim27':G['claims']['27']['content']})
 row['attribution_candidates']=[]
 for k in KEYS:
  if not rp[k]:row['attribution_candidates'].append({'predicate':k,'stage':'raw_explicit_relation_omission','qualification':'Check actual semantic records manually; entitydescription may retain predicate; absence is not necessarily totalfactloss.'})
  elif not pp[k]:row['attribution_candidates'].append({'predicate':k,'stage':'parser_candidate_loss'})
  elif not mp[k]:row['attribution_candidates'].append({'predicate':k,'stage':'merge_candidate_loss'})
  elif not tp[k]:row['attribution_candidates'].append({'predicate':k,'stage':'relation_not_returned_in_retrieved_relationships','qualification':'Original chunk evidence may still recover it.'})
 if truncated:row['attribution_candidates'].append({'stage':'truncation_confound','exclude_clean_boundary_pair':True})
 rows.append(row)
summary={}
for c in ['A','B']:
 rr=[x for x in rows if x['condition']==c and x['status']=='completed'];vv=[x for x in rr if x['eligible']]
 summary[c]={'completed':len(rr),'nontruncated':len(vv),'raw_relation_counts':{k:sum(x['raw_relation_retention'][k] for x in rr) for k in KEYS},'raw_entity_description_counts':{k:sum(x['raw_entity_description_retention'][k] for x in rr) for k in KEYS},'merged_relation_counts':{k:sum(x['merged_relation_retention'][k] for x in rr) for k in KEYS},'shared_actual_module_endpoint_identity':sum(x['registration_module_identity']['joint_actual_endpoint_identity_retained'] for x in rr),'both_target_clauses_naturally_retrieved':sum(x['natural']['both_original_target_clauses_retrieved'] for x in rr)}
result={'evaluated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'group':'M01','publication_number':'US7991757B2','scope':'NEW official full pipeline on clipped Claims1/27 only; excludes earlier partial AST/diagnostic smoke','method':'Deterministic candidate inventory; manual review required. No judge-model API; explicit source gold frozen before outputs.','complete_six_runs':all(x['status']=='completed' for x in rows),'summary':summary,'runs':rows,'manual_review_status':'pending','causal_limit':'R2self-contained inClaim27; B2chunks/462processedsource tokens vsA1chunk/362, so not fullpatent or irreducible joint-evidence experiment.'}
(R/'evidence/M01_evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'complete':result['complete_six_runs'],'summary':summary},indent=2))
