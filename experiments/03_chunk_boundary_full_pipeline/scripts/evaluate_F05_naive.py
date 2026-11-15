"""Add independently read naive-query observations; no new API and no core-gold changes."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import json,re,datetime,hashlib,shutil
ROOT=legacy_root('round4_full_20261030');R=ROOT/'round4_full_20261030'
p=R/'evidence/F05_evaluation.json';ev=json.loads(p.read_text());g=next(x for x in json.loads((R/'conditions/frozen_groups.json').read_text())['groups'] if x['id']=='F05');source=g['content']
snapshot=p.with_name('F05_evaluation_mix_only.json')
if not snapshot.exists():shutil.copyfile(p,snapshot)
def norm(s):return re.sub(r'[\W_]+',' ',s.lower()).strip()
def quotes(s):
 qq=[m.group(1) or m.group(2) for m in re.finditer(r'“([^”]+)”|"([^"\n]+)"',s)]
 return [{'quote':q,'byte_exact_substring':q in source,'word_sequence_supported_after_punctuation_whitespace_normalization':norm(q) in norm(source)} for q in qq]
# Additional cited facts below were read against all original claims, not inferred by regex scoring.
claims={'F05_A_r1':[1,6,7,8,9,10,12,13],'F05_A_r2':[1,6,7,10,12,13,17],'F05_A_r3':[1,6,7,10,12,13],'F05_B_r1':[6,7,10],'F05_B_r2':[1,6,7,10],'F05_B_r3':[1,6,7,10,12]}
for row in ev['runs']:
 rid=row['run_id'];f=R/'results'/rid/'natural_naive.json';x=json.loads(f.read_text());d=x['result']['data'];ans=x['result']['llm_response']['content'];assert x['status']=='completed' and x['result']['status']=='success' and x['actual_new_answer_call'] and x['core_index_unchanged']
 q=quotes(ans);full={str(c['claim_number']):[i for i,ch in enumerate(d['chunks']) if c['text'] in ch['content']] for c in g['claims']};assert all(full.values())
 assert d['references']==[{'reference_id':'1','file_path':'US8069128B2.txt'}]
 wrong_word=[z for z in q if not z['word_sequence_supported_after_punctuation_whitespace_normalization']]
 row['naive']={'mode':'naive','record_file':str(f.relative_to(R)),'status':'completed','actual_new_answer_call':x['actual_new_answer_call'],'core_index_unchanged':x['core_index_unchanged'],'started_utc':x['started_utc'],'ended_utc':x['ended_utc'],'call_id_range':x['call_id_range'],'core_answer_correct':True,'source_claims':{'classifier_claim10_correct':True,'nonpersistent_exclusive_second_data_claim6_correct':True,'first_filter_persistent_data_claim6_correct':True,'other_cited_claim_numbers_manually_checked':claims[rid],'other_cited_claim_facts_supported':True,'publication_correct':True,'reference_mapping_correct':True,'legal_claim10_to6_dependency_not_required_by_query':True},'retrieval':{'chunks':len(d['chunks']),'entities':len(d['entities']),'relationships':len(d['relationships']),'full_original_claim_chunks':full,'both_target_claims_available':True,'references':d['references']},'quote_fidelity':{'quotes':q,'count':len(q),'byte_exact_count':sum(a['byte_exact_substring'] for a in q),'all_quotes_byte_exact':all(a['byte_exact_substring'] for a in q),'all_word_sequences_supported_after_punctuation':not wrong_word,'word_changes':wrong_word,'interpretation':'A1 quotes Claim8 as occur instead of original occurs; other non-exact cases are punctuation/whitespace. These are generation quotation-fidelity differences, not unsupported target technical conclusions.' if wrong_word else 'Any non-exact quotations differ only in punctuation/whitespace under this deterministic audit; core Claim attribution manually checked.'},'unsupported_extra':[],'material_unsupported_extra_found':False,'first_and_second_filter_data_not_conflated':True,'answer':ans,'comparison_to_mix':'Same stored isolated index and original query/model/context budget; graph files unchanged. Query-only new answer. Target facts/Claims/source correct in both modes; naive does not expose graph retrieval context.'}
for c in ['A','B']:
 rr=[r['naive'] for r in ev['runs'] if r['condition']==c];s=ev['summary'][c]
 s.update(naive_runs_completed=len(rr),naive_core_answer_correct=sum(r['core_answer_correct'] for r in rr),naive_source_claims_correct=sum(r['source_claims']['classifier_claim10_correct'] and r['source_claims']['nonpersistent_exclusive_second_data_claim6_correct'] and r['source_claims']['reference_mapping_correct'] for r in rr),naive_both_target_claims_retrieved=sum(r['retrieval']['both_target_claims_available'] for r in rr),naive_all_quotes_byte_exact=sum(r['quote_fidelity']['all_quotes_byte_exact'] for r in rr),naive_all_quote_word_sequences_supported_after_punctuation=sum(r['quote_fidelity']['all_word_sequences_supported_after_punctuation'] for r in rr),naive_material_unsupported_extra_count=sum(r['material_unsupported_extra_found'] for r in rr))
ev['naive_evaluated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();ev['naive_review_method']='Six real naive outputs, retrieved original Claim6/10 and additional cited Claims were read against frozen full source. Exact quote audit is separate from core factual correctness. No API or model self-judging used.'
ev['conclusion_naive_zh']='新增naive自然查询A/B各3次，核心技术答案、Claim6/10及来源均3/3正确，均检索到目标原文；没有实质不受原文支持的额外技术结论。A1的Claim8引文将occurs改为occur，其他非逐字差异仅标点/空格；不能把核心正确写成引文全部逐字正确。'
tmp=p.with_suffix('.json.tmp');tmp.write_text(json.dumps(ev,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
print(json.dumps({c:{k:v for k,v in ev['summary'][c].items() if k.startswith('naive')} for c in ['A','B']},indent=2))
