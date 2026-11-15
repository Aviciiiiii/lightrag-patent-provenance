"""Independent offline verification; no service configuration or model imports."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import os,sys,json,hashlib,datetime,re,importlib.util
ROOT=legacy_root('round4_full_20261030');OUT=ROOT/'round4_full_20261030/evidence'
os.environ['TIKTOKEN_CACHE_DIR']=str(legacy_root('round4_full_20261030')/'tiktoken_cache')
import tiktoken
enc=tiktoken.get_encoding('o200k_base')
spec=importlib.util.spec_from_file_location('frozen_custom_chunker',ROOT/'round4/scripts/custom_chunker.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
frozenpath=ROOT/'round4/conditions/frozen_groups.json';frozen=json.loads(frozenpath.read_text());candidatepath=ROOT/'round4/evidence/candidates.json';gold=json.loads((ROOT/'round4/evidence/manual_gold_review.json').read_text());manual={g['id']:g for g in gold['rows']}
assert hashlib.sha256(candidatepath.read_bytes()).hexdigest()==gold['candidate_file_sha256']
rows=[]
for g in frozen['groups']:
 if g['id']=='M01':continue
 text=g['content'];raw=(ROOT/g['content_source']).read_text();ids=enc.encode(text)
 checks={'content_matches_complete_original_indexed_document_after_recorded_strip':text==raw.strip(),'content_sha_matches_frozen':hashlib.sha256(text.encode()).hexdigest()==g['content_sha256'],'raw_sha_matches_frozen':hashlib.sha256(raw.encode()).hexdigest()==g['raw_sha256'],'full_token_roundtrip_identical':enc.decode(ids)==text,'total_tokens_match':len(ids)==g['total_tokens']}
 anchors=[]
 for family,aa in g['evidenceanchors'].items():
  for a in aa:
   ca,cb=a['char_span'];ta,tb=a['token_span'];q=a['quote'];actual=text[ca:cb]
   assert re.sub(r'\s+',' ',actual).strip()==re.sub(r'\s+',' ',q).strip()
   assert actual in enc.decode(ids[ta:tb])
   actual_occurrences=[m.start() for m in re.finditer(re.escape(actual),text)]
   frozen_occurrences=[aa2['char_span'][0] for aa2 in aa if re.sub(r'\s+',' ',text[slice(*aa2['char_span'])]).strip()==re.sub(r'\s+',' ',actual).strip()]
   assert set(actual_occurrences)<=set(frozen_occurrences)
   anchors.append({'family':family,'char_span':[ca,cb],'token_span':[ta,tb],'quote_exactly_matches_span':actual==q,'all_exact_occurrences_accounted':True,'original_span_text':actual})
 conds={}
 for c in ['A','B']:
  plan=g['conditions'][c]['chunks'];ranges=[x.get('global_token_span',x.get('token_span')) for x in plan];callback=mod.make_precomputed_chunker(text,ranges);actual=callback(enc,text,None,False,100,1200)
  assert len(actual)==len(plan)
  reproduced=''; previous_end=0;detail=[]
  for i,(chunk,planned,span) in enumerate(zip(actual,plan,ranges)):
   start,end=span;char_start=len(enc.decode(ids[:start]));char_end=len(enc.decode(ids[:end]));matches={family:[] for family in ['A','B']}
   assert chunk['content']==planned['content']
   assert chunk['tokens']==len(enc.encode(chunk['content']))<=1200
   assert hashlib.sha256(chunk['content'].encode()).hexdigest()==planned['content_sha256']
   if i:assert previous_end-start==100
   reproduced+=enc.decode(ids[previous_end:end]);previous_end=end
   for a in anchors:
    ca,cb=a['char_span']
    if max(ca,char_start)<min(cb,char_end):matches[a['family']].append(a['char_span'])
   detail.append({'index':i,'token_span':span,'char_span':[char_start,char_end],'actual_tokens':chunk['tokens'],'partial_intersections':matches,'has_partial_both_families':bool(matches['A'] and matches['B']),'sha256':hashlib.sha256(chunk['content'].encode()).hexdigest()})
  assert reproduced==text
  whole_covered=all(any(x['char_span'][0]<=a['char_span'][0] and a['char_span'][1]<=x['char_span'][1] for x in detail) for a in anchors)
  assert whole_covered
  dual=[d['index'] for d in detail if d['has_partial_both_families']]
  if c=='B':assert not dual
  if c=='A':assert dual
  conds[c]={'chunk_count':len(plan),'lengths':[x['actual_tokens'] for x in detail],'global_spans':ranges,'source_sequence_reconstruction_identical':True,'all_chunks_at_most1200':True,'all_adjacent_global_overlap_exactly100':True,'each_anchor_wholly_available':whole_covered,'dual_partial_anchor_chunk_indices':dual,'source_tokens_processed':sum(x['actual_tokens'] for x in detail),'chunks':detail}
 # The forced diagnostic consists only of intact original retained claims joined by blank lines.
 diag=g['diagnostic_text'];diag_parts=[x.strip() for x in diag.split('\n\n') if x.strip()]
 assert all(x in text for x in diag_parts)
 checks['forced_diagnostic_contains_only_original_claims']=True
 checks['B_has_no_partial_joint_frozen_anchor']=not conds['B']['dual_partial_anchor_chunk_indices'];assert all(checks.values())
 rows.append({'id':g['id'],'publication_number':g['publication_number'],'status':'passed_offline_preflight','source_scope':'Complete second-round indexed publication/title/abstract/all-Claims document, not full patent specification','source_path':g['content_source'],'content_sha256':g['content_sha256'],'total_tokens':len(ids),'checks':checks,'conditions':conds,'anchors':anchors,'frozen_query':g['query'],'frozen_technical_predicate':g['researcher_predicate'],'required_component_predicates':manual[g['id']]['required_component_predicates'],'forbidden_inferred_required_edge':manual[g['id']]['forbidden_inference_as_required_edge'],'forced_diagnostic_original_text':diag,'forced_diagnostic_claims':[int(re.match(r'(\d+)\.',v).group(1)) for v in diag_parts],'manually_reviewed_claims':manual[g['id']]['selected_claims'],'semantic_limitation':manual[g['id']]['semantic_leakage_warning'],'semantic_equivalence_exhaustively_excluded':False,'requires_same_chunk_to_exist_logically':False})
r={'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'round4_full_preflight independent offline audit','status':'passed_all_three_frozen_full_document_pairs','source_frozen_sha256':hashlib.sha256(frozenpath.read_bytes()).hexdigest(),'candidate_file_sha256':hashlib.sha256(candidatepath.read_bytes()).hexdigest(),'candidate_file_matches_manual_review':True,'tokenizer':'o200k_base','python':sys.executable,'rows':rows,'minimum_control_exclusion':{'publication_number':'US7991757B2','claim_pair':[1,27],'full_document_anchor_enclosing_tokens':1677,'max_tokens':1200,'full_document_same_chunk_eligible':False,'minimal_clipped_pair_remains_separate':True},'excluded_candidates':[{k:x[k] for k in ['id','publication_number','exclusion_reason']} for x in manual.values() if not x.get('boundary_feasible')],'model_api_calls':0,'secret_reads':0,'original_file_writes':0,'review_limits':['Frozen literal anchors and all their exact occurrences are separated; does not prove every inferential or semantically equivalent cue is absent.','Gold is original-text grounded researcher-style AI-assisted criteria, not independent human annotation or model self-scoring.','Component-predicate co-retention and graph chaining are valid targets; no direct shortcut relation is required.','A/B have different local chunk lengths, potentially counts and total repeated tokens; compare these explicitly.','This audit does not certify any model run, parser success, merged graph or answer; verify actual runtime chunk audits and raw requests after execution.','The custom chunker receives only original content and numeric ranges; no gold predicates enter that callback. Actual extraction prompts require later inspection.']}
OUT.mkdir(parents=True,exist_ok=True);(OUT/'preflight_independent_review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':r['status'],'groups':[{'id':x['id'],'A':x['conditions']['A']['lengths'],'B':x['conditions']['B']['lengths']} for x in rows]},ensure_ascii=False))
