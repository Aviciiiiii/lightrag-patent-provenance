"""Deterministic evidence inventory for manual F01 review, no model calls."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import json,re,datetime,hashlib
ROOT=legacy_root('round4_full_20261030');R=ROOT/'round4_full_20261030';G=next(g for g in json.loads((R/'conditions/frozen_groups.json').read_text())['groups'] if g['id']=='F01')
def norm(x):return re.sub(r'\s+',' ',str(x).lower().replace('-',' '))
def pred(text,key):
 s=norm(text);onto='ontology' in s
 if key=='R_umls':return onto and ('unified medical language system' in s or 'umls' in s) and any(v in s for v in ['based','basis','underl'])
 role=bool(re.search(r'existing(?: medical)? cases?',s)) if key=='R_case' else 'expert' in s
 return onto and role and any(v in s for v in ['embed','represent']) and any(v in s for v in ['based','basis','used','using','compute'])
KEYS=['R_case','R_expert','R_umls']
def pick(records):return {k:[x for x in records if pred(json.dumps(x,ensure_ascii=False),k)] for k in KEYS}
def small(x):return {k:x[k] for k in ['entity_id','entity_name','id','source','target','src_id','tgt_id','description','source_id','file_path','keywords','call_id'] if k in x}
def allp(d):return all(bool(d[k]) for k in KEYS)
def roles(records):
 text=' '.join(str(x.get('entity_id',x.get('entity_name',x.get('id','')))) for x in records);return {'existing_case_entity':bool(re.search(r'existing(?: medical)? cases?',norm(text))),'expert_entity':'expert' in norm(text),'medical_ontology_entity':'medical ontology' in norm(text),'umls_entity':'unified medical language system' in norm(text)}
runs=[]
for cond,n in [('A',1),('B',1),('B',2),('A',2),('A',3),('B',3)]:
 rid=f'F01_{cond}_r{n}';B=R/'results'/rid
 if not(B/'status.json').exists():runs.append({'run_id':rid,'status':'not_started','eligible':False});continue
 status=json.loads((B/'status.json').read_text());row={'run_id':rid,'status':status['status'],'condition':cond,'repeat':n,'eligible':False}
 if status['status']!='completed':runs.append(row);continue
 parsed=json.loads((B/'parsed_extraction.json').read_text());graph=json.loads((B/'merged_graph.json').read_text());natural=json.loads((B/'natural_query.json').read_text());forced=json.loads((B/'forced_diagnostic.json').read_text());out=natural['result'];data=out.get('data') or {};ans=(out.get('llm_response') or {}).get('content','')
 rawrels=[];rawents=[];pedges=[];pnodes=[];parsers=[]
 for rec in parsed['records']:
  cid=rec['call_id'];resp=json.loads((R/'logs'/f'api_{cid:04d}_response.json').read_text());lines=resp['content'].splitlines();rr=[l for l in lines if l.startswith('relation<|#|>')];ee=[l for l in lines if l.startswith('entity<|#|>')]
  rawrels += [{'call_id':cid,'chunk_id':rec['chunk_id'],'row':l} for l in rr];rawents += [{'call_id':cid,'chunk_id':rec['chunk_id'],'row':l} for l in ee]
  for z in rec['edges']:
   pedges += [dict(x,call_id=cid) for x in z['records']]
  for name,records in rec['nodes'].items():pnodes += [dict(x,call_id=cid) for x in records]
  parsers.append({'call_id':cid,'chunk_id':rec['chunk_id'],'finish_reason':resp['finish_reason'],'completion_tokens':(resp.get('usage') or {}).get('completion_tokens'),'completion_delimiter_present':rec['completion_delimiter_present'],'raw_entity_rows':len(ee),'raw_relation_rows':len(rr),'parsed_entity_records':sum(len(v) for v in rec['nodes'].values()),'parsed_relation_records':sum(len(z['records']) for z in rec['edges'])})
 rawp=pick(rawrels);parp=pick(pedges);gp=pick(graph['edges']);np=pick(graph['nodes']);rnp=pick(rawents);retp=pick(data.get('relationships',[]));reten=pick(data.get('entities',[]))
 chunks=data.get('chunks',[]);quotes={k:G['evidence'][k][0]['quote'] for k in ['A','B']};quote_hits={k:[c['chunk_id'] for c in chunks if norm(v) in norm(c.get('content',''))] for k,v in quotes.items()}
 common=None
 for key in KEYS:
  ids=set()
  for e in gp[key]:ids.update(e.get(k) for k in ['source','target'] if e.get(k) and norm(e[k])=='medical ontology')
  common=ids if common is None else common&ids
 claim_nodes=[small(v) for v in graph['nodes'] if re.search(r'\bclaim\s*[48]\b',str(v.get('id','')),re.I)];claim_edges=[small(v) for v in graph['edges'] if re.search(r'claim\s*4',str(v),re.I) and re.search(r'claim\s*8',str(v),re.I)]
 trunc=[p['call_id'] for p in parsers if p['finish_reason']=='length'];row.update(eligible=not trunc,truncated_extraction_ids=trunc,graph_counts={'nodes':len(graph['nodes']),'edges':len(graph['edges'])},parser_checks=parsers,raw_relation_retention={k:bool(v) for k,v in rawp.items()},raw_entity_description_retention={k:bool(v) for k,v in rnp.items()},parsed_relation_retention={k:bool(v) for k,v in parp.items()},merged_relation_retention={k:bool(v) for k,v in gp.items()},merged_entity_description_retention={k:bool(v) for k,v in np.items()},merged_target_entity_presence=roles(graph['nodes']),all_three_merged_predicates=allp(gp),shared_ontology_actual_graph_ids=sorted(common or []),shared_ontology_chain_retained=allp(gp) and bool(common),explicit_claim8_to_claim4_graph_dependency=bool(claim_edges),claim_structure_evidence={'nodes':claim_nodes,'edges':claim_edges},raw_support=rawp,parsed_support={k:[small(x) for x in v] for k,v in parp.items()},merged_support={k:[small(x) for x in v] for k,v in gp.items()},entity_description_support={k:[small(x) for x in v] for k,v in np.items()},natural={'status':out.get('status'),'llm_generated':(out.get('llm_response') or {}).get('llm_generated'),'retrieved_chunk_ids':[c['chunk_id'] for c in chunks],'original_target_quote_chunks':quote_hits,'both_original_target_quotes_retrieved':all(bool(v) for v in quote_hits.values()),'retrieved_relationship_retention':{k:bool(v) for k,v in retp.items()},'retrieved_entity_description_retention':{k:bool(v) for k,v in reten.items()},'references':data.get('references',[]),'answer':ans,'answer_mentions_both_supporting_claims':bool(re.search(r'claim\s*4',ans,re.I) and re.search(r'claim\s*8',ans,re.I)),'answer_publication_correct':'US9589231B2' in ans,'answer_names_umls':'unified medical language system' in norm(ans),'answer_existing_cases_and_experts':bool(re.search(r'existing(?: medical)? cases?',norm(ans)) and 'expert' in norm(ans))},forced={'call_id':forced['call_id'],'not_natural_score':True,'answer':forced['content'],'both_claims_mentioned':bool(re.search(r'claim\s*4',forced['content'],re.I) and re.search(r'claim\s*8',forced['content'],re.I))},source_evidence={'query':G['query'],'claims':G['claims'],'input_sha256':G['content_sha256']})
 row['attribution_preliminary']=[]
 for k in KEYS:
  if not rawp[k]:row['attribution_preliminary'].append({'predicate':k,'stage':'raw_extraction_explicit_relation_omission','qualification':'Not necessarily total fact loss; inspect node descriptions and generic/multi-edge alternatives. Boundary cause not established merely by this omission.'})
  elif not parp[k]:row['attribution_preliminary'].append({'predicate':k,'stage':'parser_candidate_loss_requires_manual_review'})
  elif not gp[k]:row['attribution_preliminary'].append({'predicate':k,'stage':'merge_candidate_loss_requires_manual_review'})
  elif not retp[k]:row['attribution_preliminary'].append({'predicate':k,'stage':'graph_relation_not_in_retrieved_relation_list','qualification':'Original chunks may still retrieve the complete evidence, so do not conflate with answer evidence loss.'})
 if trunc:row['attribution_preliminary'].append({'stage':'output_truncation_confounded','qualification':'Exclude this run from clean boundary comparison even if target predicates survive.'})
 runs.append(row)
summary={}
for c in ['A','B']:
 rows=[x for x in runs if x.get('condition')==c and x['status']=='completed'];valid=[x for x in rows if x['eligible']]
 summary[c]={'completed':len(rows),'nontruncated':len(valid),'truncated':len(rows)-len(valid),'observed_all_three_merged_predicates':sum(x['all_three_merged_predicates'] for x in rows),'nontruncated_all_three_merged_predicates':sum(x['all_three_merged_predicates'] for x in valid),'observed_both_original_target_quotes_retrieved':sum(x['natural']['both_original_target_quotes_retrieved'] for x in rows),'raw_relation_counts':{k:sum(x['raw_relation_retention'][k] for x in rows) for k in KEYS}}
result={'evaluated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'group':'F01','publication_number':'US9589231B2','method':'Deterministic evidence inventory followed by AI-assisted researcher manual reading of matched raw/parsed/graph records and all answers; no judge-model API; not independent human annotation. Strict existing-case predicate requires explicit existing-case role; generic medical-case representation alone is flagged as partial/ambiguous, not automatically sufficient.','scoring_protocol':'evidence/F01_scoring_protocol.json','complete_six_runs':all(x['status']=='completed' for x in runs),'summary':summary,'runs':runs,'manual_review_status':'pending final six-run review','causal_conclusion':'Pending; extraction omission must be separated from truncation and later retrieval recovery.'}
if result['complete_six_runs']:
 result['manual_review_status']='complete: all6 raw/parsed/merged target records and all6 natural+forced answers read against frozen original claims'
 for row in result['runs']:
  row['manual_answer_review']={'natural_core_predicates_correct':True,'natural_supporting_claim4_and8_correct':True,'natural_publication_and_reference_mapping_correct':True,'natural_distinguishes_explicit_chain_from_inferred_shortcut':True,'forced_core_predicates_correct':True,'forced_claim_and_source_correct':True,'forced_not_counted_as_natural':True,'unsupported_target_conclusion_found':False,'explicit_claim8_depends_claim4_statement_in_natural_answer':False,'absence_of_explicit_dependency_answer_is_not_scored_wrong':'The frozen query asks supporting claims, not an explicit legal-dependency sentence. All raw retrievedtext contains Claim8 ofClaim4.','non_target_extra_answer_review':'Additional Claims5–7 technical details are supported in naturally retrieved source. B1 says exact phrase common embedding space is outside claims; exact phrase occurs only inabstract.','quote_caution':'Core source wording is supported; punctuation, ellipsis or bracket inflection may differ. No blanket byte-exact quote claim.'}
  row['node_description_metric_caution']='Boolean matcher fields are lexical candidate inventory, not standalone semantic gold. Generic medical-case wording does not establish explicit existing-case role. Primary outcome is manually checked explicit relation records plus target entity identity presence.'
  row['direct_subject_endpoint_edges']={}
  for key in ['R_case','R_expert']:
   found=False
   for edge in row['merged_support'][key]:
    endpoints=[norm(edge.get('source','')),norm(edge.get('target',''))]
    role=bool(re.search(r'existing(?: medical)? cases?', ' '.join(endpoints))) if key=='R_case' else 'expert' in ' '.join(endpoints)
    if 'medical ontology' in endpoints and role:found=True
   row['direct_subject_endpoint_edges'][key]=found
  row['primary_metric_endpoint_limit']='Primary semantic predicate-retention counts explicit subject roles in relationship descriptions; it is not identical to direct subject→ontology endpoint topology. Report direct_subject_endpoint_edges separately.'
  if row['condition']=='B':
   row['manual_relation_failure']={'missing':['R_case','R_expert'],'first_observed_stage':'raw relation generation','parser_loss_of_target_relation':False,'merge_loss_of_target_relation':False,'all_original_target_evidence_retrieved':True,'generation_core_error':False,'fact_not_totally_lost':'Medical Ontology entitydescription still mentions medical cases and experts; naturalchunks retain exact Claim4/8. Generic medical cases does not explicitly distinguish existing vsnew cases.','boundary_attribution_limit':'The omitted Claim4 predicates are intact within B chunk0; they do not require Claim8 to be in the same chunk. This is boundary/context-sensitive explicit relation representation under the chosen settings, not proof of necessary cross-chunk joint-reasoning failure.'}
  if row['run_id']=='F01_A_r2':row['parser_truncation_detail']={'raw_relation_rows_in_first_chunk':41,'parsed_relation_records':40,'last_raw_row':'relation<|#|>US9589231B2<','reason':'Incomplete last row at3500-token output cutoff; target predicates survived before cutoff; exclude run from clean causal pair.'}
  if row['run_id']=='F01_A_r3':row['combined_predicate_relation_note']='The actual edge is Diagnosis Assistance Method→Medical Ontology; its description explicitly states the ontology basis for newcase/existingcases/experts together. This satisfies frozen combined-role semantic criterion, but does not create direct ExistingCases→Ontology or Experts→Ontology endpoint edges.'
  if row['run_id']=='F01_A_r3':row['entity_semantic_shortcut_note']={'source':'raw extraction call77, preserved inmerged Unified Medical Language System node','description':'A medical ontology on which the embedding of medical cases and experts is based.','classification':'compressed/inferred chain presented inentitydescription without qualification; not used as explicit ontology-to-UMLS predicate evidence.','explicit_relation_and_answer':'The actual MedicalOntology→UMLS relation is correct; naturalanswer expressly preserves the intermediate ontology.'}
 result['paired_comparison']=[{'repeat':n,'A_nontruncated':next(x for x in runs if x['run_id']==f'F01_A_r{n}')['eligible'],'B_nontruncated':next(x for x in runs if x['run_id']==f'F01_B_r{n}')['eligible'],'clean_pair':n==3,'A_observed_three_predicates':True,'B_observed_three_predicates':False,'notes':'r1/r2 A truncated, descriptive observations only' if n<3 else 'One clean pair: A retains3predicates, B retainsonlyontology→UMLS; alloriginalevidence naturally retrieved inboth'} for n in [1,2,3]]
 result['summary']['paired_nontruncated_comparisons']=1
 result['summary']['natural_core_answer_correct']=6
 result['summary']['forced_core_answer_correct']=6
 result['summary']['natural_evidence_both_quotes']=6
 result['summary']['default_graph_claim_dependency_edges']=0
 result['boundary_control_notes']={'A_global_token_spans':[[0,1200],[1100,1719]],'B_global_token_spans':[[0,636],[536,1719]],'both_chunk_count':2,'both_total_processed_source_tokens':1819,'overlap_tokens':100,'same_full_input_hash':G['content_sha256'],'unavoidable_difference':'Per-chunk length/context distribution changes while full text, order, chunk count and source-token sum are identical.','anchor_status':'B nochunkcontains bothliteralanchor families; semantic-inference alternatives not exhaustivelyexcluded.'}
 result['causal_conclusion']='In this frozen F01 control, explicit case/expert ontology-basis predicates within relationship records are present in all3 Aoutputs and absent in all3 Boutputs, with omission already inraw relations. Two A runs are truncated; onlyr3 is a clean paired comparison. ExactClaim4/8 evidence is retrieved and coreanswers correct inall6, so graph representation loss is not equivalent to end-to-end factual loss. The omitted predicates are self-contained inBchunk0, and no general cross-chunk knowledge-loss claim is justified.'
for row in result['runs']:
 naive_path=R/'results'/row['run_id']/'natural_naive.json'
 if not naive_path.exists():continue
 nq=json.loads(naive_path.read_text());nr=nq.get('result') or {};nd=nr.get('data') or {};na=(nr.get('llm_response') or {}).get('content','');nc=nd.get('chunks',[])
 qhits={k:[c['chunk_id'] for c in nc if norm(G['evidence'][k][0]['quote']) in norm(c.get('content',''))] for k in ['A','B']}
 qa=[]
 for pair in re.findall(r'"([^"]+)"|“([^”]+)”',na):
  q=pair[0] or pair[1];qa.append({'quote':q,'byte_exact_original_substring':q in G['content'],'contains_marked_ellipsis_or_brackets':bool(re.search(r'\.\.\.|…|\[',q))})
 extra=[]
 if row['run_id']=='F01_B_r2':extra.append({'stage':'generation','type':'incorrect_claim_dependency_chain','answer_excerpt':'Claim 4 → Claim 5 (concepts as dimensions) → Claim 6 (proximity matrix for similarity) → Claim 8 (UMLS basis). This is the stated sequence of dependencies.','original_counterevidence':'8. The method of claim 4 , wherein the medical ontology is based on the Unified Medical Language System.','finding':'Claim8 directly depends onClaim4, notClaim6. The stated sequence is wrong if presented as claim dependency; the technical feature list itself remains supported.','retrieval_complete':True,'attribution':'Generation/claim-structure attribution error, not retrieval or extraction failure.'})
 if row['run_id']=='F01_B_r1':extra.append({'stage':'generation_quotation','type':'unmarked_omission_inside_quote','finding':'The Claim4 quotation drops in the embedding space between new medical case and comprises without an ellipsis. Core technical proposition remains supported, but this is not a byte-exact quotation.','original_omitted_words':'in the embedding space'})
 row['naive']={'status':nq.get('status'),'mode':'naive','core_answer_correct':True,'core_definition':'Only frozen existing-case/expert ontology-basis and ontology-UMLS predicates, not all ancillary claims or quotation exactness.','source_publication_correct':True,'supporting_claim4_claim8_correct':True,'claim_dependency_extra_correct':row['run_id']!='F01_B_r2','all_conclusions_supported':row['run_id']!='F01_B_r2','distinguishes_explicit_chain_and_inference':True,'original_target_quote_chunks':qhits,'both_original_target_quotes_retrieved':all(bool(v) for v in qhits.values()),'chunk_ids':[c['chunk_id'] for c in nc],'references':nd.get('references',[]),'entities_count':len(nd.get('entities',[])),'relationships_count':len(nd.get('relationships',[])),'answer':na,'actual_new_answer_call':nq.get('actual_new_answer_call'),'core_index_unchanged':nq.get('core_index_unchanged'),'call_id_range':nq.get('call_id_range'),'quote_audit':qa,'extras_and_support':extra,'manual_review':'All6actualnaiveanswers manually read against the full original Claims and matching retrievalchunks; no judge API. Added Claims5–7 andClaim9 descriptions supported; A1 markedellipsis accepted as abbreviated quote; B2 terminalpunctuation normalization separate fromits dependency error.','not_forced':True}
naives=[x['naive'] for x in result['runs'] if 'naive' in x]
result['summary']['naive_completed']=len(naives)
result['summary']['naive_core_answer_correct']=sum(x['core_answer_correct'] for x in naives)
result['summary']['naive_source_quotes']=sum(x['both_original_target_quotes_retrieved'] for x in naives)
result['summary']['naive_all_conclusions_supported']=sum(x['all_conclusions_supported'] for x in naives)
result['summary']['naive_incorrect_claim_dependency_extra']=sum(not x['claim_dependency_extra_correct'] for x in naives)
result['summary']['naive_unmarked_quote_omission']=sum(any(e['type']=='unmarked_omission_inside_quote' for e in x['extras_and_support']) for x in naives)
(R/'evidence/F01_evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'complete':result['complete_six_runs'],'summary':summary,'manual_review_status':result['manual_review_status']},indent=2))
