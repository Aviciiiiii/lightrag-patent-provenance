"""Mechanical evidence annotations; these are not automatic correctness grades."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import json,re,hashlib,datetime
R=legacy_root('round2');D=R/'round2'
norm=lambda s:' '.join(str(s).split())
questions=json.loads((R/'results/questions.json').read_text())['questions']
extra=json.loads((D/'evidence/optional_question11.json').read_text())
questions.append(extra)
ledger=json.loads((D/'results/cost_ledger.json').read_text())
rows=[]
for q in questions:
 for mode in ['naive','mix']:
  p=D/'results'/f"full_{q['id']}_{mode}.json"
  if not p.exists():continue
  entry=json.loads(p.read_text());res=entry.get('result') or {};data=res.get('data') or {};llm=res.get('llm_response') or {}
  answer=llm.get('content') or '';chunks=data.get('chunks') or [];refs=data.get('references') or []
  evidence=[]
  for e in q['evidence']:
   quote=e.get('quote',e.get('full_claim',''))
   pub=e.get('publication_number',(q.get('correct_publication_numbers') or [''])[0])
   exact=[c.get('chunk_id') for c in chunks if norm(quote) in norm(c.get('content','')) and pub in c.get('file_path','')]
   evidence.append({'patent':pub,'claim':e.get('claim_number'),'quote':quote,'matching_retrieved_chunk_ids':exact})
  cited_ids=sorted(set(re.findall(r'\[(\d+)\]',answer)))
  refmap={str(x.get('reference_id')):x.get('file_path') for x in refs}
  lo,hi=entry.get('api_call_id_range',[0,-1])
  calls=[c for c in ledger['calls'] if lo<=c['id']<=hi]
  rows.append({'question_id':q['id'],'mode':mode,'system_status':res.get('status'),'llm_generated':llm.get('llm_generated'),
   'answer':answer,'answer_patent_ids':sorted(set(re.findall(r'US\d+[AB]\d',answer))),
   'answer_claim_numbers':sorted(set(map(int,re.findall(r'\bclaims?\s*(\d+)',answer,re.I)))),
   'retrieved_entities':len(data.get('entities') or []),'retrieved_relationships':len(data.get('relationships') or []),
   'retrieved_chunks':len(chunks),'references':refs,'cited_reference_ids':cited_ids,
   'unresolved_cited_reference_ids':[i for i in cited_ids if i not in refmap],
   'evidence_quote_coverage':evidence,'api_calls':len(calls),
   'estimated_query_cost_upper_cny':sum(c.get('estimated_cost_upper_cny',0) for c in calls),
   'api_prompt_tokens':sum(c.get('usage',{}).get('prompt_tokens',0) or 0 for c in calls if c['kind']=='llm'),
   'api_completion_tokens':sum(c.get('usage',{}).get('completion_tokens',0) or 0 for c in calls if c['kind']=='llm'),
   'source_result_file':str(p.relative_to(R))})
out={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'note':'Mechanical annotations only. Evidence absence alone is not an extraction error; quotations and entailment require review.','rows':rows}
(D/'evidence/query_evidence_annotations.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({'query_results_annotated':len(rows),'status_success':sum(r['system_status']=='success' for r in rows)},indent=2))
