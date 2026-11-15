"""Offline verification of persisted actual chunks, request accounting and run isolation."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import json,hashlib,datetime
ROOT=legacy_root('round4_full_20261030');R=ROOT/'round4_full_20261030'
groups={g['id']:g for g in json.loads((R/'conditions/frozen_groups.json').read_text())['groups']};ledger=json.loads((R/'results/cost_ledger.json').read_text());runs=[]
for p in sorted((R/'results').glob('*/status.json')):
 s=json.loads(p.read_text());g=groups[s['group']];row={'run_id':s['run_id'],'status':s['status'],'condition':s['condition'],'repeat':s['repeat'],'scope':s['scope'],'graph_counts':s.get('graph_counts'),'truncated_extraction_call_ids':s.get('truncated_extraction_call_ids',[]),'boundary_causal_eligible':s.get('boundary_causal_eligible',False)}
 a=p.parent/'actual_chunking.json';c=p.parent/'chunks.json'
 if a.exists() and c.exists():
  audit=json.loads(a.read_text());chunks=json.loads(c.read_text());expected=g['conditions'][s['condition']]['chunks'];actual=sorted(chunks.items(),key=lambda kv:kv[1]['chunk_order_index']);assert len(actual)==len(expected)==len(audit['chunks']);assert audit['source_sha256']==hashlib.sha256(g['content'].encode()).hexdigest()
  for ((cid,chunk),planned,span) in zip(actual,expected,audit['chunks']):
   assert chunk['content']==planned['content'];assert hashlib.sha256(chunk['content'].encode()).hexdigest()==span['content_sha256'];assert span['actual_tokens']<=1200;assert chunk['file_path']==g['file_path']
  row.update(actual_chunk_content_matches_frozen=True,source_sha256=audit['source_sha256'],chunk_count=len(actual),chunk_lengths=[x['actual_tokens'] for x in audit['chunks']],file_paths=sorted(set(x['file_path'] for _,x in actual)),chunk_ids=[k for k,_ in actual],workspace=s['workspace'])
 runs.append(row)
ll=[c for c in ledger['calls'] if c['kind']=='llm' and c['state']=='success'];ee=[c for c in ledger['calls'] if c['kind']=='embedding' and c['state']=='success'];inp=sum(c['usage']['prompt_tokens'] for c in ll);out=sum(c['usage']['completion_tokens'] for c in ll);cache=sum((c['usage'].get('prompt_tokens_details') or {}).get('cached_tokens',0) for c in ll);reason=sum((c['usage'].get('completion_tokens_details') or {}).get('reasoning_tokens',0) for c in ll)
cost={'successful_llm_calls':len(ll),'successful_embedding_calls':len(ee),'all_attempts':len(ledger['calls']),'llm_prompt_tokens':inp,'llm_completion_tokens':out,'cached_input_tokens':cache,'reasoning_tokens':reason,'cache_aware_cny':((inp-cache)*2+cache*.04+(out+reason)*8)/1e6,'no_cache_cny':(inp*2+(out+reason)*8)/1e6,'unknown_reserved_cny':ledger['reserved_unknown_cny'],'states_not_success':[{'id':c['id'],'state':c['state'],'kind':c['kind']} for c in ledger['calls'] if c['state']!='success'],'length_finish_call_ids':[c['id'] for c in ll if c.get('finish_reason')=='length'],'not_invoice':True}
r={'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runs':runs,'completed_runs':sum(x['status']=='completed' for x in runs),'actual_chunk_hashes_and_frozen_content_verified':all(x.get('actual_chunk_content_matches_frozen',False) for x in runs if x['status']=='completed'),'cost':cost,'scope_note':'Uses only new full-pipeline records; original partial AST control and envdiag smoke are separate.'}
(R/'evidence/completed_runs_audit.json').write_text(json.dumps(r,indent=2)+'\n');(R/'evidence/cost_summary.json').write_text(json.dumps(cost,indent=2)+'\n');print(json.dumps({'runs':len(runs),'completed_runs':r['completed_runs'],'all_actual_chunk_hashes_verified':r['actual_chunk_hashes_and_frozen_content_verified'],'cost':cost},indent=2))
