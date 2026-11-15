"""Verify exhaustive source membership, exact quotes and real edge IDs; no APIs."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import datetime, hashlib, json, re, sys
OUT=legacy_root('round2_multisource_audit')/'round2_multisource_audit';ROOT=legacy_root('round2_multisource_audit')
inventory=json.loads((OUT/'evidence/multisource_nodes_inventory.json').read_text())
docs=json.loads((OUT/'evidence/document_registry.json').read_text())
doc_by_pub={x['publication_number']:x['content'] for x in docs.values()}
chunks=json.loads((OUT/'evidence/chunk_to_document_mapping.json').read_text())
errors=[];pending=[];checks=[];reviewed_nodes=[];all_edge_ids=set();source_memberships=0
categories={'shared_specific_concept','shared_broad_class','contextual_conflation','insufficient_evidence'}
for n in inventory:
 aid=n['audit_id'];p=OUT/'reviews'/f'{aid}.json'
 if not p.exists():pending.append(aid);continue
 a=json.loads(p.read_text());d=json.loads((OUT/'dossiers'/f'{aid}.json').read_text())
 def fail(kind,detail):errors.append({'audit_id':aid,'kind':kind,'detail':detail})
 if a.get('audit_id')!=aid or a.get('node_id')!=n['node_id']:fail('node_id_mismatch',a.get('node_id'))
 if a.get('category') not in categories:fail('invalid_category',a.get('category'))
 if a.get('confidence') not in ['high','medium','low']:fail('invalid_confidence',a.get('confidence'))
 for k in ['reason_zh','class_instance_interpretation_zh','limitations_zh']:
  if not a.get(k):fail('missing_required_field',k)
 sources=a.get('source_assessments',[]);pubs=[s.get('publication_number') for s in sources]
 if sorted(pubs)!=sorted(n['canonical_publications']):fail('source_coverage_mismatch',pubs)
 valid_edges={e['edge_index']:e for e in d['all_incident_edges']}
 na=a.get('neighbor_audit',{});review_edges=na.get('edge_indices',[])
 if na.get('reviewed_incident_edge_count')!=len(valid_edges):fail('incident_edge_count_mismatch',na.get('reviewed_incident_edge_count'))
 if set(review_edges)!=set(valid_edges):fail('incident_edge_set_mismatch',{'missing':sorted(set(valid_edges)-set(review_edges)),'unexpected':sorted(set(review_edges)-set(valid_edges))})
 all_edge_ids.update(valid_edges)
 for s in sources:
  source_memberships+=1;pub=s.get('publication_number');quote=s.get('evidence_quote','');cids=s.get('source_chunk_ids',[]);section=s.get('claim_or_section','');actual_sources=next(x['source_chunks'] for x in d['source_documents'] if x['publication_number']==pub)
  if not quote or not isinstance(quote,str):fail('missing_quote',pub);continue
  if not cids or not set(cids)<=set(actual_sources):fail('quote_source_ids_not_node_sources',{'publication':pub,'ids':cids})
  matches=[]
  for cid in cids:
   if cid not in chunks:continue
   for m in re.finditer(re.escape(quote),chunks[cid]['content']):
    docstart=chunks[cid]['exact_doc_char_start']+m.start()
    matches.append({'chunk_id':cid,'chunk_char_start':m.start(),'full_doc_char_start':docstart,'full_doc_char_end':docstart+len(quote)})
  if not matches:fail('quote_not_contiguous_in_source_chunk',{'publication':pub,'quote':quote})
  pos=doc_by_pub.get(pub,'').find(quote)
  if pos<0:fail('quote_not_contiguous_in_full_doc',{'publication':pub,'quote':quote})
  claims_path=ROOT/'data/claims'/f'{pub}.json';claims=json.loads(claims_path.read_text())
  claim_hits=[c['claim_number'] for c in claims if quote in c['text']]
  requested=[];claim_locations=[]
  if isinstance(section,str) and re.search(r'claim',section,re.I):
   requested=[int(x) for x in re.findall(r'\d+',section)]
   if requested and not set(requested)&set(claim_hits):fail('claim_quote_mismatch',{'publication':pub,'requested':requested,'actual_claim_hits':claim_hits})
   for claim in claims:
    if claim['claim_number'] not in requested:continue
    cs=doc_by_pub[pub].find(claim['text'])
    for m in re.finditer(re.escape(quote),claim['text']):
     start=cs+m.start();end=start+len(quote)
     source_matches=[x['chunk_id'] for x in matches if x['full_doc_char_start']==start]
     claim_locations.append({'claim_number':claim['claim_number'],'full_doc_char_start':start,'full_doc_char_end':end,'exact_source_chunks_containing_this_claim_occurrence':source_matches})
   if requested and not any(x['exact_source_chunks_containing_this_claim_occurrence'] for x in claim_locations):fail('claim_occurrence_outside_listed_source_chunks',{'publication':pub,'requested':requested,'quote':quote})
  if isinstance(section,str) and 'abstract' in section.lower():
   full=doc_by_pub[pub];abstract=full.split('\nABSTRACT\n',1)[-1].split('\nCLAIMS\n',1)[0]
   if quote not in abstract:fail('abstract_quote_mismatch',pub)
  for er in s.get('relevant_actual_edges',[]):
   eid=er if isinstance(er,int) else er.get('edge_index') if isinstance(er,dict) else None
   if eid not in valid_edges:fail('invalid_relevant_edge',{'publication':pub,'value':er});continue
   if pub not in valid_edges[eid]['canonical_publications']:fail('edge_wrong_publication',{'publication':pub,'edge_index':eid})
  checks.append({'audit_id':aid,'node_id':n['node_id'],'publication_number':pub,'evidence_quote':quote,'claim_or_section':section,'matching_claim_numbers':claim_hits,'first_occurrence_in_full_doc_char_start':pos,'first_occurrence_in_full_doc_char_end':pos+len(quote) if pos>=0 else None,'claim_anchored_quote_locations':claim_locations,'matching_source_chunks':matches,'source_chunk_ids':cids})
 reviewed_nodes.append({'audit_id':aid,'review_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'dossier_sha256':hashlib.sha256((OUT/'dossiers'/f'{aid}.json').read_bytes()).hexdigest()})
input_hashes=json.loads((OUT/'evidence/original_input_hashes.json').read_text());changed=[]
for rel,x in input_hashes.items():
 p=ROOT/rel
 if hashlib.sha256(p.read_bytes()).hexdigest()!=x['sha256']:changed.append(rel)
result={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'expected_nodes':len(inventory),'reviewed_nodes':len(reviewed_nodes),'pending_nodes':pending,'reviewed_source_memberships':source_memberships,'unique_incident_edges':len(all_edge_ids),'incident_edge_visits':sum(len(json.loads((OUT/'dossiers'/f"{n['audit_id']}.json").read_text())['all_incident_edges']) for n in inventory if (OUT/'reviews'/f"{n['audit_id']}.json").exists()),'errors':errors,'original_inputs_changed':changed,'quote_checks':checks,'review_hashes':reviewed_nodes,'structural_quote_validation_only':'Passing verifies coverage, exact source quotes and graph endpoint identifiers, not truth of semantic judgements.'}
(OUT/'evidence/review_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['quote_checks','review_hashes']},ensure_ascii=False,indent=2))
if errors or changed or ('--require-complete' in sys.argv and pending):raise SystemExit(1)
