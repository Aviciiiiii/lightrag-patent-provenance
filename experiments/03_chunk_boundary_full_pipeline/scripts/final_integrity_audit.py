"""Read-only audit of existing outputs; no imports of runtime/API wrappers or secrets."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
import json, pathlib, hashlib, math, collections, datetime
ROOT=legacy_root('round4_full_20261030');BASE=ROOT/'round4_full_20261030'
load=lambda p:json.loads(pathlib.Path(p).read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
issues=[]
def check(ok,code,detail=None):
 if not ok: issues.append({'code':code,'detail':detail})
ledger=load(BASE/'results/cost_ledger.json');calls=ledger['calls'];reqs={};providers={};summary_rows=[];ids=[];extract_ids=[];system_hashes=collections.Counter();kindcounts=collections.Counter();stagecounts=collections.Counter();tokens=collections.defaultdict(lambda:collections.Counter());cachecost=0;uppercost=0
for c in calls:
 cid=c['id'];kind=c['kind'];kindcounts[(kind,c['state'])]+=1;stagecounts[c['stage']]+=1
 req=load(BASE/f'logs/api_{cid:04d}_request.json');raw=load(BASE/f'logs/api_{cid:04d}_provider_response.json');reqs[cid]=req;providers[cid]=raw
 check(req['id']==cid and req['stage']==c['stage'],'request_identity',cid)
 check(raw.get('usage')==c.get('usage'),'usage_ledger_raw_mismatch',cid)
 check(not any(k.lower() in ['authorization','headers','api_key','api-key'] for k in list(raw)+list(req)),'sensitive_header_key_in_logs',cid)
 u=raw.get('usage',{});p=u.get('prompt_tokens',0);o=u.get('completion_tokens',0);cache=u.get('prompt_cache_hit_tokens',(u.get('prompt_tokens_details') or {}).get('cached_tokens',0));reason=(u.get('completion_tokens_details') or {}).get('reasoning_tokens',0)
 check(u.get('total_tokens')==p+o,'usage_total_disagreement',cid)
 if 'prompt_cache_hit_tokens' in u and 'cached_tokens' in (u.get('prompt_tokens_details') or {}):check(cache==u['prompt_tokens_details']['cached_tokens'],'cached_usage_fields_disagree',cid)
 if 'prompt_cache_miss_tokens' in u:check(u['prompt_cache_miss_tokens']+cache==p,'cache_hit_miss_total',cid)
 tokens[kind].update(prompt=p,completion=o,cached=cache,reasoning=reason)
 known=(2*(p-cache)+.04*cache+8*o)/1e6 if kind=='llm' else 0
 upper=(2*p+8*(o+reason))/1e6 if kind=='llm' else 0
 cachecost+=known;uppercost+=upper
 check(abs(c.get('estimated_cost_upper_cny',0)-upper)<1e-12,'per_call_cost_disagreement',cid)
 row={'call_id':cid,'stage':c['stage'],'kind':kind,'state':c['state'],'prompt_tokens':p,'completion_tokens':o,'cached_input_tokens':cache,'reasoning_tokens':reason,'cache_aware_cny':known,'no_cache_cny':upper}
 if kind=='llm':
  check(req.get('model')=='deepseek-ai/DeepSeek-V4.1-Flash' and raw.get('model')==req['model'],'llm_model',cid)
  check(req.get('temperature')==0 and req.get('max_tokens')==3500 and req.get('stream') is False and req.get('extra_body')=={'enable_thinking':False},'llm_settings',cid)
  choice=raw['choices'][0];saved=load(BASE/f'logs/api_{cid:04d}_response.json');ids.append(raw['id']);row.update(provider_id=raw['id'],finish_reason=choice.get('finish_reason'))
  check(saved['content']==choice['message']['content'],'simplified_response_content',cid)
  check(saved.get('usage')==u and saved.get('finish_reason')==choice.get('finish_reason')==c.get('finish_reason'),'simplified_response_metadata',cid)
  check(reason==0 and not choice['message'].get('reasoning_content'),'reasoning_observed',cid)
  sys=req['messages'][0]['content'] if req['messages'][0]['role']=='system' else ''
  if 'Knowledge Graph Specialist' in sys:
   extract_ids.append(cid);system_hashes[sha(sys.encode())]+=1
 else:
  check(req.get('model')=='BAAI/bge-m3' and raw.get('model')==req['model'],'embedding_model',cid)
  rows=raw['data'];indices=[r['index'] for r in rows]
  check(sorted(indices)==list(range(len(req['input']))),'embedding_index_alignment',cid)
  check(all(len(r['embedding'])==1024 and all(isinstance(v,(int,float)) and math.isfinite(v) for v in r['embedding']) and any(v!=0 for v in r['embedding']) for r in rows),'embedding_values_shape',cid)
  row['embedding_texts']=len(req['input'])
 summary_rows.append(row)
check([c['id'] for c in calls]==list(range(1,len(calls)+1)),'noncontiguous_call_ids')
check(len(ids)==len(set(ids)),'duplicate_llm_provider_id')
check(len(system_hashes)==1 and len(extract_ids)==45,'extraction_prompt_identity_or_count')
check(abs(uppercost-ledger['estimated_observed_cost_cny'])<1e-10,'ledger_total_disagreement')
check(ledger['reserved_unknown_cny']==0 and all(c['state']=='success' for c in calls),'unknown_or_failed_calls')
check(all('M01' not in c['stage'] for c in calls),'M01_calls_present')
length=[c['id'] for c in calls if c.get('finish_reason')=='length'];check(length==[1,56],'unexpected_truncations',length)
frozen=load(BASE/'conditions/frozen_groups.json');groups={g['id']:g for g in frozen['groups']};runs=[];mapped=[];storages=[];allgraphrows=0
for gid in ['F01','F04','F05']:
 g=groups[gid]
 for condition in ['A','B']:
  for rep in range(1,4):
   rid=f'{gid}_{condition}_r{rep}';d=BASE/'results'/rid;status=load(d/'status.json');chunks=load(d/'chunks.json');actual=load(d/'actual_chunking.json');parsed=load(d/'parsed_extraction.json');graph=load(d/'merged_graph.json');naive=load(d/'natural_naive.json');mix=load(d/'natural_query.json');forced=load(d/'forced_diagnostic.json');storage=pathlib.Path(status['storage'])/status['workspace'];storages.append(str(storage));ordered=sorted(chunks.items(),key=lambda v:v[1]['chunk_order_index']);fc=g['conditions'][condition]['chunks']
   check(status['status']=='completed' and status['doc_counts']['processed']==1 and status['doc_counts'].get('failed',0)==0,'run_doc_status',rid)
   check(status['no_reused_extraction_or_answer_cache'] is True and status['embedding_cache_reused'] is False,'cache_flags',rid)
   check(len(ordered)==len(fc)==len(actual['chunks'])==len(parsed['records']),'chunk_record_count',rid)
   check(actual['source_sha256']==g['content_sha256']==sha(g['content'].encode()),'source_hash',rid)
   for i,((chunkid,c),expected,a) in enumerate(zip(ordered,fc,actual['chunks'])):
    check(c['content']==expected['content'] and sha(c['content'].encode())==expected['content_sha256']==a['content_sha256'],'frozen_actual_content',f'{rid}/{i}')
    check(c['file_path']==g['file_path'],'chunk_file_path',f'{rid}/{i}')
    check(a['actual_tokens']<=1200 and a['overlap_previous_global_tokens']==(100 if i else 0),'chunk_size_overlap',f'{rid}/{i}')
    cs=a['source_char_span'];check(g['content'][cs[0]:cs[1]]==c['content'],'chunk_source_slice',f'{rid}/{i}')
   anchor_groups=g['evidenceanchors'];anchorsA=[v['quote'] for v in anchor_groups['A']];anchorsB=[v['quote'] for v in anchor_groups['B']]
   joint=[cid for cid,c in ordered if any(q in c['content'] for q in anchorsA) and any(q in c['content'] for q in anchorsB)]
   check(bool(joint) if condition=='A' else not joint,'literal_target_cooccurrence',rid)
   for rec in parsed['records']:
    cid=rec['call_id'];mapped.append(cid);check(cid in extract_ids,'parser_call_not_extraction',cid)
    source=chunks[rec['chunk_id']];prompt=reqs[cid]['messages'][-1]['content'];check(('```\n'+source['content']+'\n```') in prompt,'parser_request_chunk_mapping',cid)
    check(rec['file_path']==source['file_path'] and rec['finish_reason']==providers[cid]['choices'][0]['finish_reason'],'parser_meta_mapping',cid)
    records=[x for vals in rec['nodes'].values() for x in vals]+[x for edge in rec['edges'] for x in edge['records']]
    check(all(x['source_id']==rec['chunk_id'] and x['file_path']==rec['file_path'] for x in records),'parsed_source_fields',cid)
   for gr in graph['nodes']+graph['edges']:
    allgraphrows+=1
    check(set(gr.get('source_id','').split('<SEP>'))<=set(chunks),'graph_source_ids',rid)
    check(set(gr.get('file_path','').split('<SEP>'))=={g['file_path']},'graph_file_paths',rid)
   check(status['graph_counts']=={'nodes':len(graph['nodes']),'edges':len(graph['edges'])},'graph_counts',rid)
   trunc=[r['call_id'] for r in parsed['records'] if r['finish_reason']=='length'];check(status['truncated_extraction_call_ids']==trunc and status['boundary_causal_eligible']==(not trunc),'truncation_eligibility',rid)
   retrieval={}
   for name,q,expected_calls in [('mix',mix,2),('naive',naive,1)]:
    check(q['query']==g['query'] and q['mode']==name and q['forced_evidence'] is False and q['result']['status']=='success' and q['result']['llm_response']['llm_generated'] is True,'natural_query_status',f'{rid}/{name}')
    first,last=q['call_id_range'];llmc=[c for c in calls[first-1:last] if c['kind']=='llm'];check(len(llmc)==expected_calls and all(c['stage']==rid+'_natural_'+name for c in calls[first-1:last]),'natural_call_provenance',f'{rid}/{name}')
    content=q['result']['llm_response']['content'];check(content==providers[llmc[-1]['id']]['choices'][0]['message']['content'],'answer_provider_mapping',f'{rid}/{name}')
    retrieval[name]={'actual_llm_calls':[c['id'] for c in llmc],'chunks':len(q['result']['data']['chunks']),'entities':len(q['result']['data']['entities']),'relationships':len(q['result']['data']['relationships']),'references':len(q['result']['data']['references']),'status':q['result']['status']}
   check({k:v for k,v in mix['params'].items() if k!='mode'}=={k:v for k,v in naive['params'].items() if k!='mode'},'naive_mix_parameters',rid)
   check(forced['forced_evidence'] is True and forced['not_natural_retrieval_score'] is True and forced['content']==providers[forced['call_id']]['choices'][0]['message']['content'],'forced_diagnostic_mapping',rid)
   before=naive['core_index_hashes_before'];after=naive['core_index_hashes_after'];current={n:sha((storage/n).read_bytes()) for n in before}
   check(before==after==current and naive['core_index_unchanged'] is True,'naive_core_index_mutation',rid)
   runs.append({'run_id':rid,'status':status['status'],'storage':str(storage),'chunk_count':len(chunks),'chunk_lengths':[x['actual_tokens'] for x in actual['chunks']],'frozen_content_matches':True,'literal_joint_target_chunks':joint,'parsed_extraction_call_ids':[r['call_id'] for r in parsed['records']],'truncated_extraction_call_ids':trunc,'boundary_causal_eligible':not trunc,'graph_counts':status['graph_counts'],'retrieval':retrieval,'forced_diagnostic_call_id':forced['call_id'],'naive_core_hashes_before_after_current_match':before==after==current})
check(len(set(storages))==18,'distinct_index_paths')
check(sorted(mapped)==sorted(extract_ids) and len(mapped)==45,'all_extractions_parsed_once')
old=[]
for name,expected in load(ROOT/'round3/evidence/index_before_hashes.json').items():
 current=sha((ROOT/name).read_bytes());old.append({'path':name,'expected_sha256':expected,'actual_sha256':current,'unchanged':current==expected});check(current==expected,'old_round2_index_modified',name)
source=[];manifest={x['path']:x for x in load(ROOT/'env_diagnostics_20261030/evidence/fresh_official_source_manifest.json')}
for name in ['lightrag/__init__.py','lightrag/_version.py','lightrag/lightrag.py','lightrag/operate.py','lightrag/utils.py','lightrag/prompt.py','lightrag/constants.py']:
 p=(legacy_root('round4_full_20261030')/'src/LightRAG-v1.5.7')/name;current=sha(p.read_bytes());entry={'path':name,'current_sha256':current,'manifest_sha256':manifest[name]['sha256'],'matches':current==manifest[name]['sha256']};source.append(entry);check(entry['matches'],'official_source_changed',name)
watchdogs=[]
for n in ['F01','F04','F05','naive']:
 w=load(BASE/f'results/{n}_watchdog.json');check(w['status']=='completed' and w['exit_code']==0 and w['child_alive'] is False,'watchdog_completion',n);watchdogs.append({'name':n,**w})
prior=[]
for relative in ['round4','env_diagnostics_20261030']:
 pl=load(ROOT/relative/'results/cost_ledger.json');pc=pu=0
 for c in pl['calls']:
  if c['kind']!='llm' or not c.get('usage'):continue
  u=c['usage'];p=u.get('prompt_tokens',0);o=u.get('completion_tokens',0);cache=u.get('prompt_cache_hit_tokens',(u.get('prompt_tokens_details') or {}).get('cached_tokens',0));r=(u.get('completion_tokens_details') or {}).get('reasoning_tokens',0);pc+=(2*(p-cache)+.04*cache+8*o)/1e6;pu+=(2*p+8*(o+r))/1e6
 prior.append({'directory':relative,'confirmed_usage_cache_aware_cny':round(pc,8),'confirmed_usage_no_cache_cny':round(pu,8),'unconfirmed_reservation_cny':pl['reserved_unknown_cny'],'not_invoice':True})
prior_cache=sum(x['confirmed_usage_cache_aware_cny'] for x in prior);prior_upper=sum(x['confirmed_usage_no_cache_cny'] for x in prior);unknown=sum(x['unconfirmed_reservation_cny'] for x in prior)
report={'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed_execution_integrity_with_truncation_and_parser_warnings' if not issues else 'issues_found','scope':'Existing full-group execution integrity only; no credential reads, APIs, environment imports or process actions. Old partial round4 and environment smoke are separate and never substitute full-group cells. Technical-gold scoring is reviewed by other agents.','issues':issues,'calls':{'attempts':len(calls),'counts_by_kind_and_state':{f'{k}/{s}':v for (k,s),v in kindcounts.items()},'tokens_by_kind':{k:dict(v) for k,v in tokens.items()},'llm_unique_provider_ids':len(set(ids)),'extraction_calls':len(extract_ids),'extraction_system_prompt_sha256_counts':dict(system_hashes),'all_llm_fixed_model_temperature0_max3500_thinking_disabled':not any(x['code'] in ['llm_model','llm_settings'] for x in issues),'length_finish_call_ids':length,'reasoning_tokens':sum(v['reasoning'] for v in tokens.values()),'unknown_reservations':ledger['reserved_unknown_cny'],'per_call_usage_and_cost':summary_rows},'cost':{'currency':'CNY','rates_per_million':{'input':2,'cached_input':.04,'output':8,'BAAI/bge-m3':0},'price_scope':'Previously verified provider prices; no new web/API calls in this audit. Estimates from returned usage, not invoice.','new_confirmed_usage_cache_aware_cny':round(cachecost,8),'new_confirmed_usage_no_cache_upper_cny':round(uppercost,8),'new_unknown_reservation_cny':ledger['reserved_unknown_cny'],'prior_components':prior,'combined_confirmed_usage_cache_aware_cny':round(cachecost+prior_cache,8),'combined_confirmed_usage_no_cache_cny':round(uppercost+prior_upper,8),'prior_unconfirmed_reservation_cny':unknown,'combined_budget_upper_including_unknown_reservation_cny':round(uppercost+prior_upper+unknown,8),'maximum_budget_bound_cny':4+prior_upper+unknown,'reservation_caveat':'The prior 0.315518 reservation is not confirmed spend. Failed calls with no returned usage are not proof of zero billing.'},'runs':runs,'parsed_mapping':{'records':len(mapped),'all_45_extraction_calls_mapped_once_to_real_persisted_chunks':sorted(mapped)==sorted(extract_ids),'graph_rows_checked':allgraphrows,'parser_reexecution_in_this_audit':False,'method':'Validate saved official parser records against raw request fenced chunk, response finish metadata and source fields; no model or official parser import in this audit.'},'cache_integrity':{'unique_index_directories':len(set(storages)),'application_response_reuse_observed':False,'evidence':'Fresh-directory runner refuses existing storage; each extraction and each mix/naive/forced answer has a distinct actual provider response and sequential ledger ID. Same request text may recur legitimately across repetitions. Query-only naive reopens its own index, never other repetitions. Provider cached input tokens are prefix-cache billing, not application answer reuse.','embedding_cache_reused':False,'seed_limitation':'No seed request recorded. Temperature 0 does not guarantee deterministic provider behavior.'},'scope_limits':['Full document means the original second-round indexed title+abstract+claims; no specification or 20-document background corpus in each independent index.','Frozen boundary matches and literal anchor noncooccurrence are checked; this does not prove exhaustive semantic-equivalent absence.','F01_A_r1 and F01_A_r2 are excluded from untruncated boundary-causal comparisons; successful transport and completed index do not remove truncation confounding.','M01 status not_run_by_scope_update, zero new M01 calls or indexes. Earlier partial AST experiment and environment diagnosis smoke are preserved separately.'],'official_source':{'version':'1.5.7','commit':'28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c','selected_current_files_vs_prior_materialization_manifest':source,'independently_rehashed_entire_repository':False},'old_round2_indices':old,'watchdogs':watchdogs,'audit_script':'scripts/final_integrity_audit.py'}
import xml.etree.ElementTree as ET
persisted=[]
for r in runs:
 storage=pathlib.Path(r['storage']);rid=r['run_id'];current_chunks=load(storage/'kv_store_text_chunks.json');snapshot=load(BASE/'results'/rid/'chunks.json');tree=ET.parse(storage/'graph_chunk_entity_relation.graphml');ns={'g':'http://graphml.graphdrawing.org/xmlns'};counts={'nodes':len(tree.findall('.//g:node',ns)),'edges':len(tree.findall('.//g:edge',ns))};persisted.append({'run_id':rid,'persisted_chunk_dictionary_matches_snapshot':current_chunks==snapshot,'persisted_graphml_counts':counts,'saved_graph_counts_match':counts==r['graph_counts']})
 check(current_chunks==snapshot and counts==r['graph_counts'],'persisted_storage_mismatch',rid)
report['persisted_storage_checks']=persisted
report['persisted_storage_checks_method']='Read current kv_store_text_chunks.json and standard-library XML graphml counts once per new run; compare exported snapshots. Core hashes separately verify naive did not change these stores.'
warnings=[]
for name in ['F01_pipeline.log','F04_pipeline.log','F05_pipeline.log','naive_followup.log']:
 for line_number,line in enumerate((BASE/'logs'/name).read_text().splitlines(),1):
  if line.startswith(('WARNING:','ERROR:')):warnings.append({'file':name,'line':line_number,'message':line})
report['completed_run_log_warnings']=warnings
report['parser_warnings_note']='Two F01 length responses have missing completion delimiters; call56 also has an incomplete relation. Separately F04_B_r2 call253 ends normally (stop) but three four-field relation records lack a target-entity field and are rejected by the official parser; warnings repeat during parser replay. No ERROR-level lines in completed-run logs. Earlier pre-index setup failure is separate. Full API success does not mean all extraction records parsed successfully. Other typo delimiters may be repaired by official parsing and are not automatically rejected edges.'
report['nontruncated_parser_failures']=[{'run_id':'F04_B_r2','call_id':253,'finish_reason':'stop','malformed_four_field_relations':['Short Message / generated by','Recipient Mobile Device / receives forwarded','Database / accessed by'],'unique_malformed_records':3,'warning_lines_in_F04_pipeline_log':[254,255,256,329,330,331],'warning_repetition':'Three during insertion, three during saved-parser replay; not six distinct malformed records.','causal_scope':'Extraction-output formatting/parser rejection. Target gold effect must be evaluated separately; cannot label this a pure boundary omission solely from warning presence.'}]
if issues:report['status']='issues_found'

(BASE/'evidence/final_integrity_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'status':report['status'],'issues':issues,'cost':report['cost'],'calls':{k:v for k,v in report['calls'].items() if k!='per_call_usage_and_cost'},'runs':len(runs),'old_indices_unchanged':all(x['unchanged'] for x in old)},ensure_ascii=False,indent=2))
