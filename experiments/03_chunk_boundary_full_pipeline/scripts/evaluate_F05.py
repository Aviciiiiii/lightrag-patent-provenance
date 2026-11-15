"""Frozen-predicate, evidence-grounded F05 evaluation; no model/self-judging calls.
Candidate matches were manually reviewed in raw/merged/context/answers on2026-10-30.
"""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import json,re,datetime,hashlib
ROOT=legacy_root('round4_full_20261030');R=ROOT/'round4_full_20261030'
def load(p):return json.loads(p.read_text())
g=next(x for x in load(R/'conditions/frozen_groups.json')['groups'] if x['id']=='F05');src=g['content']
def ids(e):return [e.get('source',e.get('src_id','')),e.get('target',e.get('tgt_id',''))]
def norm(s):return re.sub(r'[\W_]+',' ',s.lower()).strip()
def match(e,p):
 a,b=ids(e);end=norm(a+' '+b);d=norm(e.get('description',''))
 if p=='P1':return 'naive bayes' in end and 'filter' in d and ('employ' in d or 'uses' in d)
 if p=='P2':return 'second classification data' in end and 'filter' in end and 'generat' in d and 'second classification data' in d
 if p=='P3':return 'second classification data' in end and 'non persistent memory' in end and ('resid' in d or 'stored' in d)
def quoted(s,evidence):
 q=[m.group(1) or m.group(2) for m in re.finditer(r'“([^”]+)”|"([^"\n]+)"',s)]
 return [{'quote':x,'byte_exact_substring':x in evidence,'word_sequence_supported_after_punctuation_whitespace_normalization':norm(x) in norm(evidence)} for x in q]
rows=[]
for c,n in [('A',1),('B',1),('B',2),('A',2),('A',3),('B',3)]:
 rid=f'F05_{c}_r{n}';b=R/'results'/rid;status=load(b/'status.json');assert status['status']=='completed'
 p=load(b/'parsed_extraction.json');graph=load(b/'merged_graph.json');nat=load(b/'natural_query.json');forced=load(b/'forced_diagnostic.json');d=nat['result']['data'];chunks=d['chunks'];ans=nat['result']['llm_response']['content']
 pred={};raw_records=[]
 for rec in p['records']:
  response=load(R/'logs'/f"api_{rec['call_id']:04d}_response.json")
  lines=response['content'].splitlines()
  for grouping in rec['edges']:
   for edge in grouping['records']:
    raw_records.append({'call_id':rec['call_id'],'chunk_id':rec['chunk_id'],'finish_reason':rec['finish_reason'],'edge':edge,'raw_tuple_lines':[{'line':i+1,'text':line} for i,line in enumerate(lines) if line.startswith('relation') and edge['description'] in line]})
 for key in ['P1','P2','P3']:
  raw=[x for x in raw_records if match(x['edge'],key)];merged=[dict(record_index=i,**e) for i,e in enumerate(graph['edges']) if match(e,key)];retr=[e for e in d['relationships'] if match(e,key)]
  nodes={v for e in merged for v in ids(e)};node_evidence=[v for v in graph['nodes'] if v.get('id',v.get('entity_id')) in nodes]
  pred[key]={'raw_relation_present':bool(raw),'raw_target_rows_located_verbatim':bool(raw) and all(x['raw_tuple_lines'] for x in raw),'raw_relation_records':raw,'merged_relation_present':bool(merged),'merged_relation_records':merged,'merged_endpoint_nodes_present':len(node_evidence)==len(nodes),'merged_endpoint_nodes':node_evidence,'natural_graph_relation_present':bool(retr),'natural_graph_relation_records':retr}
  if key=='P3':pred[key]['exclusive_qualifier_in_merged_relation']=any(re.search(r'\b(exclusively|only)\b',x['description'],re.I) for x in merged)
 # These exact-edge identity checks are secondary, not a requirement that semantically equivalent names are one canonical entity.
 e1=pred['P1']['merged_relation_records'][0];e2=pred['P2']['merged_relation_records'][0];e3=pred['P3']['merged_relation_records'][0]
 filter1=next(v for v in ids(e1) if 'bayes' not in v.lower());filter2=next(v for v in ids(e2) if v!='Second Classification Data')
 exact_identity=filter1==filter2 and 'Second Classification Data' in ids(e3)
 alternate=[dict(record_index=i,**e) for i,e in enumerate(graph['edges']) if (set(ids(e))=={filter1,'Classification Model'} and 'generat' in e['description'].lower()) or ('Classification Model' in ids(e) and any('Non-Persistent' in z for z in ids(e)) and 'exclusively' in e['description'].lower())]
 cq={str(cl['claim_number']):[i for i,ch in enumerate(chunks) if cl['text'] in ch['content']] for cl in g['claims']}
 qa=quoted(ans,src);fq=quoted(forced['content'],forced['supplied_evidence']);claimnodes=[x for x in graph['nodes'] if re.search(r'\bclaim\s*(6|10)\b',x.get('id',''),re.I)]
 assert all(pred[k]['raw_relation_present'] and pred[k]['merged_relation_present'] and pred[k]['natural_graph_relation_present'] for k in pred)
 assert pred['P3']['exclusive_qualifier_in_merged_relation'] and all(cq.values())
 findings=[]
 if not exact_identity:findings.append({'kind':'entity_naming_variation_carried_through_merge','stage':'raw entity naming plus graph identity representation','evidence':{'P1_filter_id':filter1,'P2_filter_id':filter2},'interpretation':'These are distinct stored identities. Component facts survive, and an alternative ClassificationModel path exists. Do not label this alone a deduplication bug or technical relation loss.'})
 if any(not x['byte_exact_substring'] for x in qa):findings.append({'kind':'natural_answer_non_verbatim_quotation','stage':'generation/quotation fidelity','interpretation':'Supported original evidence was retrieved. Most differences are punctuation; A2/A3 additionally change occurs to occur in a Claim8 quote. Core technical answers remain correct.','non_word_exact':[x for x in qa if not x['word_sequence_supported_after_punctuation_whitespace_normalization']]})
 rows.append({'run_id':rid,'condition':c,'repeat':n,'status':status['status'],'valid_untruncated_extraction_run':not status['truncated_extraction_call_ids'],'extraction_calls':[{'call_id':x['call_id'],'chunk_id':x['chunk_id'],'finish_reason':x['finish_reason'],'completion_tokens':x['completion_tokens']} for x in p['records']],'actual_chunking':load(b/'actual_chunking.json'),'graph_counts':status['graph_counts'],'predicates':pred,'all_three_component_predicates_retained_raw_graph_and_natural_graph_context':True,'P3_exclusive_qualifier_retained':True,'shared_identity_secondary':{'P1_filter_id':filter1,'P2_filter_id':filter2,'exact_filter_id_shared_with_SecondClassificationData_path':exact_identity,'alternate_ClassificationModel_chain_edges':alternate,'alternate_model_chain_present':len(alternate)>=2,'not_a_semantic_merge_equivalence_proof':True},'claim_structure_secondary':{'claim6_or_claim10_graph_nodes':claimnodes,'explicit_claim10_to6_edge':False,'interpretation':'No Claim nodes/dependency edges represented by this default extraction. Supporting-Claim accuracy is evaluated separately. Natural query did not explicitly request the legal dependency.'},'natural_retrieval':{'status':nat['result']['status'],'chunks':len(chunks),'entities':len(d['entities']),'relationships':len(d['relationships']),'full_original_claim_chunks':cq,'both_target_claims_available':all(cq.values()),'references':d['references']},'natural_answer':{'core_classifier_correct':True,'second_data_memory_and_exclusivity_correct':True,'first_vs_second_data_not_conflated':True,'supporting_claim6_and10_correct':True,'publication_and_reference_mapping_correct':True,'explicit_claim_dependency_assertion_present':bool(re.search(r'depend\w*\s+(?:on\s+)?claim\s*6',ans,re.I)),'material_unsupported_technical_conclusion_found':False,'quotes':qa,'content':ans},'forced_diagnostic':{'supplied_only_original_claim6_and10':forced['supplied_evidence']==g['diagnostic_text'],'not_natural_retrieval_score':True,'core_answer_and_claims_correct':True,'publication_and_reference_mapping_correct':True,'quotes':fq,'content':forced['content']},'findings':findings,'failure_attribution':'No target-component extraction, graph retention or retrieval loss observed; quotation fidelity deviations occur after correct original evidence retrieval. Identity naming variation is separately reported, not assigned as a chunk-loss mechanism.'})
summary={}
for c in ['A','B']:
 rr=[r for r in rows if r['condition']==c]
 summary[c]={'runs_completed':len(rr),'untruncated_runs':sum(r['valid_untruncated_extraction_run'] for r in rr),'raw_all_three_component_predicates':3,'merged_all_three_component_predicates':3,'natural_graph_all_three_component_predicates':3,'explicit_exclusivity_retained':3,'natural_both_target_claims_retrieved':3,'natural_core_answer_claims_source_correct':3,'forced_core_answer_claims_source_correct':3,'exact_target_filter_id_chain':sum(r['shared_identity_secondary']['exact_filter_id_shared_with_SecondClassificationData_path'] for r in rr),'all_natural_quotes_byte_exact':sum(all(q['byte_exact_substring'] for q in r['natural_answer']['quotes']) for r in rr),'all_natural_quote_word_sequences_supported_after_punctuation':sum(all(q['word_sequence_supported_after_punctuation_whitespace_normalization'] for q in r['natural_answer']['quotes']) for r in rr),'claim10_to6_graph_edge':0}
res={'evaluated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'group':'F05','publication_number':g['publication_number'],'original_claims':g['claims'],'rubric':'evidence/F05_frozen_evaluation_rubric.json','method':'Read-only original-text and raw-response/official-parser/actual-graph/retrieval-context/answer review; deterministic matching collects manually reviewed specific predicates. No LLM self-grading or API calls. Source quotation audit is exact substring plus separately labeled punctuation/whitespace normalization.','summary':summary,'paired_valid_repeats':3,'runs':rows,'conclusion_zh':'三个无截断配对重复中，A/B均保留所有三个显式技术组件关系及exclusivity，并检索到Claim6/10，核心回答与来源均正确；未观察到目标跨块技术关系损失。A条件存在filter/model命名分裂，但同时有原文支持的ClassificationModel路径，不能仅按名称差异判关系丢失或dedup缺陷。','limits':['Single patent and three repeats per condition; B has3chunks versusA2, so extraction-call count/repeated source budget differ.','The tested target is explicit component co-retention, not an irreducible two-fragment relation. Deletion/dependency clues and repeated residency statements remain.','All queries index only this target document; context budget retrieves every chunk, making document retrieval easy.','Entity naming equivalence was not enforced through external ontology; no new alias links were added.','Quoted answers are not uniformly verbatim: A2/A3 change occurs to occur in a peripheral Claim8 quote; this does not change the target technical conclusion.','Default absence of legal Claim edges is different from technical relation loss.'],'api_calls':0,'secrets_read':False}
(R/'evidence/F05_evaluation.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2))
