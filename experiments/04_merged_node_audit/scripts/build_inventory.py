"""Read-only inventory/dossiers for existing round2; standard library only; no API."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
from collections import defaultdict, Counter
import datetime, hashlib, html, json, re, xml.etree.ElementTree as ET

OUT=legacy_root('round2_multisource_audit')/'round2_multisource_audit'
ROOT=legacy_root('round2_multisource_audit')
R=ROOT/'round2'
S=R/'storage_full/patent_r2_full'
inputs={}
def read(p):
 b=p.read_bytes();inputs[str(p.relative_to(ROOT))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return json.loads(b)
def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
graph=read(R/'results/full_graph.json');chunks=read(S/'kv_store_text_chunks.json');ec=read(S/'kv_store_entity_chunks.json');rc=read(S/'kv_store_relation_chunks.json');docs=read(S/'kv_store_full_docs.json');cache=read(S/'kv_store_llm_response_cache.json')
sp=lambda s:[x.strip() for x in (s or '').split('<SEP>') if x.strip()]
pubrx=re.compile(r'\b(?:US|EP|WO|GB|CN|JP)\d+[A-Z]\d?\b')
docmap={};conflicts=[]
for did,doc in docs.items():
 content=doc.get('content','');m=re.search(r'^Publication number:\s*(\S+)',content,re.M)
 pub=m.group(1) if m else None
 docmap[did]={'publication_number':pub,'file_path':doc.get('file_path'), 'content_sha256':hashlib.sha256(content.encode()).hexdigest(),'content':content}
 if pub!=did:conflicts.append({'doc_id':did,'publication_header':pub})
chunkmap={};missing_docs=[]
for cid,c in chunks.items():
 did=c.get('full_doc_id');dm=docmap.get(did);p=dm.get('publication_number') if dm else None
 path=c.get('file_path');pm=pubrx.search(path or '')
 if pm and p and pm.group(0)!=p:conflicts.append({'chunk':cid,'publication_header':p,'file_path_publication':pm.group(0)})
 if not dm:missing_docs.append(cid)
 content=c.get('content','');full=dm['content'] if dm else '';start=full.find(content)
 chunkmap[cid]={'publication_number':p,'full_doc_id':did,'file_path':path,'chunk_order_index':c.get('chunk_order_index'),'tokens':c.get('tokens'),'content_sha256':hashlib.sha256(content.encode()).hexdigest(),'exact_doc_char_start':start,'exact_doc_char_end':start+len(content) if start>=0 else None,'content':content,'llm_cache_list':c.get('llm_cache_list',[])}
node_lookup={n['id'].casefold():n['id'] for n in graph['nodes']}
raw_records=list(cache.items())
# The one truncated response was parsed into the graph but not cached by LightRAG.
# Attribute it through the saved request's exact input text, not a guessed name.
truncated_request=read(R/'logs/api_0191_request.json')
truncated_response=read(R/'logs/api_0191_response.json')
truncated_cid='US9218390B2-chunk-000'
assert chunks[truncated_cid]['content'] in '\n'.join(m.get('content','') for m in truncated_request['messages'])
assert truncated_response['finish_reason']=='length'
raw_records.append(('raw_log:round2/logs/api_0191_response.json',{'return':truncated_response['content'],'cache_type':'extract','chunk_id':truncated_cid,'finish_reason':'length','source_origin':'saved_raw_response','response_file':'round2/logs/api_0191_response.json','request_file':'round2/logs/api_0191_request.json'}))
raw_entities=defaultdict(lambda:defaultdict(list));raw_relations=defaultdict(lambda:defaultdict(list));cache_by_chunk=defaultdict(list)
raw_record_registry={}
for key,c in raw_records:
 if c.get('cache_type')!='extract':continue
 cid=c.get('chunk_id');cache_by_chunk[cid].append(key)
 raw_record_registry[key]={'chunk_id':cid,'origin':c.get('source_origin','official_llm_response_cache'),'finish_reason':c.get('finish_reason','not recorded in cache'),'response_file':c.get('response_file'),'request_file':c.get('request_file'),'content_sha256':hashlib.sha256(c.get('return','').encode()).hexdigest()}
 for line_no,line in enumerate(c.get('return','').splitlines(),1):
  fields=line.strip().split('<|#|>')
  kind=fields[0].strip().lower()
  if kind not in ['entity','relation','relationship'] or len(fields)<3:continue
  positions=[1] if kind=='entity' else [1,2]
  for pos in positions:
   name=html.unescape(fields[pos].strip().strip('"'));nid=node_lookup.get(name.casefold())
   if nid:
    target=raw_entities if kind=='entity' else raw_relations
    target[nid][cid].append({'raw_record_id':key,'cache_key':key if key.startswith('default:') else None,'response_file':c.get('response_file'),'finish_reason':c.get('finish_reason','not recorded in cache'),'line_number':line_no,'raw_line':line,'fields':fields})
adj=defaultdict(list)
for i,e in enumerate(graph['edges']):
 row=dict(e);row['edge_index']=i;row['source_chunks']=sp(e.get('source_id'));row['canonical_publications']=sorted({chunkmap[s]['publication_number'] for s in row['source_chunks'] if s in chunkmap and chunkmap[s]['publication_number']})
 row['unmapped_source_chunks']=[s for s in row['source_chunks'] if s not in chunkmap]
 for nid in {e['source'],e['target']}:adj[nid].append(row)
allnodes=[];multi=[];missing_sources=[];source_diffs=[];path_diffs=[]
for node in graph['nodes']:
 nid=node['id'];gs=set(sp(node.get('source_id')));ks=set(ec.get(nid,{}).get('chunk_ids',[]));sids=sorted(gs|ks);pubs=sorted({chunkmap[s]['publication_number'] for s in sids if s in chunkmap and chunkmap[s]['publication_number']});missing=[s for s in sids if s not in chunkmap]
 paths=sorted({chunkmap[s]['file_path'] for s in sids if s in chunkmap and chunkmap[s]['file_path']});fp=sp(node.get('file_path'));fp_pubs=sorted({m.group(0) for path in fp if (m:=pubrx.search(path))})
 r={'node_id':nid,'entity_type':node.get('entity_type'),'graph_source_chunks':sorted(gs),'entity_chunk_store_sources':sorted(ks),'all_source_chunks':sids,'canonical_publications':pubs,'publication_count':len(pubs),'actual_chunk_file_paths':paths,'graph_file_paths':fp,'graph_file_path_publications':fp_pubs,'missing_source_chunks':missing,'graph_source_matches_entity_chunk_store':gs==ks,'raw_entity_source_chunks':sorted(raw_entities[nid]),'raw_relation_endpoint_source_chunks':sorted(raw_relations[nid]),'graph_node':node,'incident_edge_count':len(adj[nid])}
 if missing:missing_sources.append({'node_id':nid,'chunks':missing})
 if gs!=ks:source_diffs.append({'node_id':nid,'graph_only':sorted(gs-ks),'store_only':sorted(ks-gs)})
 if set(fp_pubs)!=set(pubs):path_diffs.append({'node_id':nid,'path_publications':fp_pubs,'chunk_publications':pubs})
 allnodes.append(r)
 if len(pubs)<2:continue
 aid=f'N{len(multi)+1:03d}';r['audit_id']=aid
 source_documents=[]
 for p in pubs:
  cids=[s for s in sids if s in chunkmap and chunkmap[s]['publication_number']==p]
  sources=[]
  for cid in cids:
   c=chunkmap[cid];text=c['content'];matches=[]
   for mt in re.finditer(re.escape(nid),text,re.I):
    lo=max(0,mt.start()-180);hi=min(len(text),mt.end()+240);matches.append({'chunk_char_start':lo,'chunk_char_end':hi,'text':text[lo:hi]})
   sources.append({**c,'chunk_id':cid,'extraction_records':[raw_record_registry[k] for k in cache_by_chunk.get(cid,[])],'raw_entity_rows':raw_entities[nid].get(cid,[]),'raw_relation_endpoint_rows':raw_relations[nid].get(cid,[]),'lexical_context_windows':matches[:12],'lexical_occurrence_count':len(matches)})
  source_documents.append({'publication_number':p,'file_paths':sorted({chunkmap[c]['file_path'] for c in cids if chunkmap[c]['file_path']}),'source_chunks':cids,'sources':sources,'incident_edges_from_publication':[e for e in adj[nid] if p in e['canonical_publications']]})
 dossier={**r,'scope':'round2 original 20-patent baseline only','source_documents':source_documents,'all_incident_edges':adj[nid],'review_status':'unreviewed'}
 write(OUT/'dossiers'/f'{aid}.json',dossier);multi.append(r)
write(OUT/'evidence/all_nodes_source_inventory.json',allnodes)
write(OUT/'evidence/multisource_nodes_inventory.json',multi)
write(OUT/'evidence/chunk_to_document_mapping.json',chunkmap)
write(OUT/'evidence/document_registry.json',docmap)
write(OUT/'evidence/raw_extraction_source_index.json',{'extraction_records_by_chunk':dict(cache_by_chunk),'raw_record_registry':raw_record_registry,'raw_entities':dict(raw_entities),'raw_relations':dict(raw_relations),'note':'Raw-row inventory uses delimiter/name lookup; not a replay of the official parser. It does not add sources to the graph membership count. 47 official cached responses plus saved truncated raw response191 cover48chunks; the latter is explicitly marked as a log, not a cache entry.'})
summary={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'round2 baseline','nodes':len(graph['nodes']),'edges':len(graph['edges']),'documents':len(docs),'chunks':len(chunks),'multisource_nodes':len(multi),'multisource_fraction':len(multi)/len(graph['nodes']),'multi_node_source_memberships':sum(len(n['canonical_publications']) for n in multi),'max_publication_count':max(n['publication_count'] for n in multi),'publication_count_histogram':dict(sorted(Counter(n['publication_count'] for n in multi).items())),'missing_doc_mappings':missing_docs,'mapping_conflicts':conflicts,'unmapped_node_source_ids':missing_sources,'graph_vs_entity_store_source_differences':source_diffs,'node_filepath_vs_chunk_publication_differences':path_diffs,'graph_field_only_multi_node_count':sum(len(n['graph_file_path_publications'])>1 for n in allnodes),'exact_chunk_in_doc_matches':sum(c['exact_doc_char_start']>=0 for c in chunkmap.values()),'new_model_calls':0,'new_embedding_calls':0,'credentials_read':False}
write(OUT/'evidence/inventory_summary.json',summary)
write(OUT/'evidence/original_input_hashes.json',inputs)
print(json.dumps(summary,ensure_ascii=False,indent=2))
