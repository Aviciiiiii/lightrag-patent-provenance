"""Read-only source-schema audit of the existing round2 snapshot. No runtime imports/API calls."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[2]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
import pathlib,json,hashlib,collections,xml.etree.ElementTree as ET,tarfile,datetime,re
OUT=legacy_root('round2_multisource_audit')/'round2_multisource_audit'
ROOT=legacy_root('round2_multisource_audit')/'round2';STORE=ROOT/'storage_full/patent_r2_full';SEP='<SEP>'
sha=lambda b:hashlib.sha256(b).hexdigest()
file_hashes={}
def read(name):
 p=STORE/name;b=p.read_bytes();file_hashes[name]={'bytes':len(b),'sha256':sha(b)};return json.loads(b)
chunks=read('kv_store_text_chunks.json');entity_chunks=read('kv_store_entity_chunks.json');relation_chunks=read('kv_store_relation_chunks.json');docs=read('kv_store_full_docs.json');full_entities=read('kv_store_full_entities.json');full_relations=read('kv_store_full_relations.json');statuses=read('kv_store_doc_status.json')
b=(STORE/'graph_chunk_entity_relation.graphml').read_bytes();file_hashes['graph_chunk_entity_relation.graphml']={'bytes':len(b),'sha256':sha(b)};xml=ET.fromstring(b);ns={'g':'http://graphml.graphdrawing.org/xmlns'};keys={x.attrib['id']:x.attrib['attr.name'] for x in xml.findall('g:key',ns)}
def attrs(el):return {keys[x.attrib['key']]:x.text or '' for x in el.findall('g:data',ns)}
nodes={x.attrib['id']:attrs(x) for x in xml.findall('.//g:node',ns)}
edges={SEP.join(sorted([x.attrib['source'],x.attrib['target']])):{**attrs(x),'endpoints':sorted([x.attrib['source'],x.attrib['target']])} for x in xml.findall('.//g:edge',ns)}
findings=collections.defaultdict(list)
def bad(condition,code,obj):
 if condition:findings[code].append(obj)
def split(v):return [x.strip() for x in (v or '').split(SEP) if x.strip()]
def docset(ids):return set(chunks[x]['full_doc_id'] for x in ids if x in chunks)
def paths(ids):return set(chunks[x]['file_path'] for x in ids if x in chunks)
bydoc=collections.defaultdict(list)
for cid,c in chunks.items():
 did=c.get('full_doc_id');bydoc[did].append(cid)
 bad(did not in docs,'chunk_missing_full_document',{'chunk_id':cid,'full_doc_id':did})
 if did in docs:
  bad(c.get('file_path')!=docs[did].get('file_path'),'chunk_doc_filepath_mismatch',cid)
  bad(c.get('content','') not in docs[did].get('content',''),'chunk_not_literal_substring_of_document',cid)
 bad(c.get('_id')!=cid,'chunk_internal_id_mismatch',cid)
 bad(not re.fullmatch(re.escape(str(did))+r'-chunk-\d+',cid),'chunk_id_naming_inconsistent',cid)
for did,d in docs.items():
 bad(d.get('_id')!=did,'document_internal_id_mismatch',did)
 bad(d.get('file_path')!=did+'.txt','document_publication_filepath_mismatch',did)
 bad(not d.get('content','').startswith('Publication number: '+did+'\n'),'document_publication_header_mismatch',did)
 bad(did not in statuses,'document_missing_status',did)
 if did in statuses:
  st=statuses[did];bad(st.get('status')!='processed','document_not_processed',did);bad(set(st.get('chunks_list',[]))!=set(bydoc[did]),'document_status_chunk_mapping_mismatch',did);bad(st.get('chunks_count')!=len(bydoc[did]),'document_status_chunk_count_mismatch',did)
 bad(not bydoc[did],'document_has_no_chunks',did)
for did in bydoc:bad(did not in docs,'chunk_only_document_id',did)
per_kind={};multi_doc_examples={};ownership={};all_tracking_used=set()
for kind,graph,tracking in [('node',nodes,entity_chunks),('edge',edges,relation_chunks)]:
 source_counts=collections.Counter();file_counts=collections.Counter();doc_counts=collections.Counter();rows=[];trunc=[];placeholder=[];graph_incidences=0;tracking_incidences=0
 for ident,g in graph.items():
  source=split(g.get('source_id'));fp=split(g.get('file_path'));track=tracking.get(ident);bad(track is None,f'{kind}_missing_tracking_row',ident)
  tids=track.get('chunk_ids',[]) if isinstance(track,dict) else []
  bad(not isinstance(tids,list),f'{kind}_invalid_tracking_schema',ident)
  if not isinstance(tids,list):tids=[]
  bad(not source,f'{kind}_empty_graph_source_id',ident);bad(not tids,f'{kind}_empty_tracking_source_ids',ident)
  bad(len(source)!=len(set(source)),f'{kind}_duplicate_graph_source_ids',ident);bad(len(tids)!=len(set(tids)),f'{kind}_duplicate_tracking_source_ids',ident)
  if track is not None:bad(track.get('count')!=len(tids),f'{kind}_tracking_count_mismatch',ident)
  bad(any(SEP in x for x in tids),f'{kind}_unsplit_joined_tracking_id',ident)
  missing_source=[x for x in source if x not in chunks];missing_tracking=[x for x in tids if x not in chunks]
  bad(bool(missing_source),f'{kind}_missing_graph_source_chunks',{'id':ident,'chunk_ids':missing_source});bad(bool(missing_tracking),f'{kind}_missing_tracking_chunks',{'id':ident,'chunk_ids':missing_tracking})
  bad(set(source)!=set(tids),f'{kind}_graph_source_vs_full_tracking_mismatch',{'id':ident,'graph_only':sorted(set(source)-set(tids)),'tracking_only':sorted(set(tids)-set(source))})
  expected_paths=paths(tids);bad(set(fp)!=expected_paths,f'{kind}_filepath_vs_chunk_mapping_mismatch',{'id':ident,'graph_file_paths':fp,'tracking_chunk_file_paths':sorted(expected_paths)})
  bad(len(fp)!=len(set(fp)),f'{kind}_duplicate_graph_file_paths',ident)
  if g.get('truncate'):trunc.append({'id':ident,'truncate':g['truncate']})
  if any(x.startswith('...truncated') for x in fp):placeholder.append({'id':ident,'file_path':fp})
  ds=docset(tids);source_counts[len(source)]+=1;file_counts[len(fp)]+=1;doc_counts[len(ds)]+=1;graph_incidences+=len(source);tracking_incidences+=len(tids);all_tracking_used.update(tids)
  row={'id':ident,'chunk_ids':tids,'publication_numbers':sorted(ds),'file_paths':sorted(expected_paths)};rows.append(row)
  ownership[(kind,ident)]=ds
  if kind=='edge':bad(any(x not in nodes for x in g['endpoints']),'edge_missing_endpoint',ident)
  if kind=='node':bad(g.get('entity_id')!=ident,'node_entity_id_mismatch',ident)
 for ident in tracking:bad(ident not in graph,f'{kind}_orphan_tracking_row',ident)
 per_kind[kind]={'graph_count':len(graph),'tracking_rows':len(tracking),'graph_source_chunk_incidences':graph_incidences,'tracking_chunk_incidences':tracking_incidences,'max_source_chunks':max(source_counts,default=0),'max_file_paths':max(file_counts,default=0),'max_resolved_documents':max(doc_counts,default=0),'source_chunk_count_histogram':dict(sorted(source_counts.items())),'file_path_count_histogram':dict(sorted(file_counts.items())),'resolved_document_count_histogram':dict(sorted(doc_counts.items())),'source_truncate_fields':trunc,'filepath_truncation_placeholders':placeholder}
 multi_doc_examples[kind]=sorted([r for r in rows if len(r['publication_numbers'])>1],key=lambda x:(-len(x['publication_numbers']),x['id']))[:10]
# Recovery indexes contain candidates, not a universal proof of successfully merged objects.
for kind,table,field in [('node',full_entities,'entity_names'),('edge',full_relations,'relation_pairs')]:
 candidate_docs=collections.defaultdict(set)
 for did,row in table.items():
  bad(did not in docs,f'{kind}_recovery_unknown_document',did);values=row.get(field,[]);bad(row.get('count')!=len(values),f'{kind}_recovery_count_mismatch',did)
  for v in values:
   ident=v if kind=='node' else SEP.join(sorted(v));candidate_docs[ident].add(did)
   bad((kind,ident) not in ownership,f'{kind}_recovery_candidate_absent_from_graph',{'document':did,'id':ident})
 for (k,ident),ds in ownership.items():
  if k!=kind:continue
  cd=candidate_docs.get(ident,set())
  bad(ds!=cd,f'{kind}_tracking_document_vs_recovery_mismatch',{'id':ident,'tracking_only_documents':sorted(ds-cd),'recovery_only_documents':sorted(cd-ds)})
 for did in docs:bad(did not in table,f'{kind}_document_missing_recovery_row',did)
# Read the preserved official source archive, never import application code.
source={};archive=ROOT/'evidence/official_core_v1.5.7.tar.gz'
with tarfile.open(archive) as t:
 for name in ['lightrag/constants.py','lightrag/operate.py','lightrag/utils.py','lightrag/lightrag.py','lightrag/_version.py']:
  raw=t.extractfile(name).read();source[name]={'sha256':sha(raw),'bytes':len(raw)}
settings=json.loads((ROOT/'evidence/full_settings.json').read_text())
allcodes=['chunk_missing_full_document','chunk_doc_filepath_mismatch','chunk_not_literal_substring_of_document','chunk_internal_id_mismatch','chunk_id_naming_inconsistent','document_internal_id_mismatch','document_publication_filepath_mismatch','document_publication_header_mismatch','document_missing_status','document_not_processed','document_status_chunk_mapping_mismatch','document_status_chunk_count_mismatch','document_has_no_chunks','chunk_only_document_id','node_entity_id_mismatch','edge_missing_endpoint']
for kind in ['node','edge']:
 allcodes += [kind+'_'+n for n in ['missing_tracking_row','invalid_tracking_schema','empty_graph_source_id','empty_tracking_source_ids','duplicate_graph_source_ids','duplicate_tracking_source_ids','tracking_count_mismatch','unsplit_joined_tracking_id','missing_graph_source_chunks','missing_tracking_chunks','graph_source_vs_full_tracking_mismatch','filepath_vs_chunk_mapping_mismatch','duplicate_graph_file_paths','orphan_tracking_row','recovery_unknown_document','recovery_count_mismatch','recovery_candidate_absent_from_graph','tracking_document_vs_recovery_mismatch','document_missing_recovery_row']]
counts={k:len(findings.get(k,[])) for k in allcodes}
report={'audit_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Read-only schema/source integrity audit of existing round2 20-patent storage; no new classification, API calls, model executions or index mutation.','inputs_root':str(ROOT),'official_version':settings['official_version'],'source_commit':settings['source_commit'],'input_hashes':file_hashes,'source_archive':'round2/evidence/official_core_v1.5.7.tar.gz','archived_code_hashes':source,'counts':{'documents':len(docs),'text_chunks':len(chunks),'graph_nodes':len(nodes),'graph_edges':len(edges),'entity_tracking_rows':len(entity_chunks),'relation_tracking_rows':len(relation_chunks),'document_entity_recovery_rows':len(full_entities),'document_relation_recovery_rows':len(full_relations),'chunks_with_any_entity_or_relation_tracking':len(all_tracking_used),'chunks_without_any_tracking':sorted(set(chunks)-all_tracking_used)},'field_schema':{'graph.source_id':'String of chunk IDs joined by literal <SEP>; identifiers resolve via kv_store_text_chunks keys.','graph.file_path':'Deduplicated file paths joined by <SEP>, for display. Not a positional array aligned with source IDs; several chunks may share a document path.','kv_store_entity_chunks':'Key is exact entity name; chunk_ids list is full tracked source set, count is list length.','kv_store_relation_chunks':'Key is <SEP>.join(sorted((src,tgt))); undirected endpoints, not a directed predicate identifier.','kv_store_text_chunks':'Key is chunk ID, full_doc_id links to full_docs key, file_path records original filename, content is persisted chunk text.','kv_store_full_docs':'Key is original publication_number here; file_path and header independently preserve it.','kv_store_full_entities_and_full_relations':'Document-keyed write-ahead candidate/recovery indexes; cross-check ownership with source tracking and graph. They are candidate supersets in general.'},'per_kind':per_kind,'mapping_problem_counts':counts,'mapping_problems':dict(findings),'multidocument_mapping_examples_for_schema_only':multi_doc_examples,'code_mechanisms':[{'source':'lightrag/constants.py','line':49,'finding':'GRAPH_FIELD_SEP is <SEP>; source IDs, descriptions and relation keys share this delimiter.'},{'source':'lightrag/utils.py','line':6423,'finding':'merge_source_ids splits joined strings, trims whitespace, deduplicates by first-seen order. Joining is not a lossless per-description attribution structure.'},{'source':'lightrag/operate.py','line':2489,'finding':'Entity merge prefers structurally valid entity_chunks tracking, writes full merged chunk IDs before limiting graph.source_id. An empty but present chunk_ids list is authoritative; graph fallback only when tracking schema is absent.'},{'source':'lightrag/operate.py','line':2855,'finding':'Relation merge uses the same full-tracking-before-limit pattern; excludes historical UNKNOWN/manual_creation placeholders as non-evidence.'},{'source':'lightrag/utils.py','line':6484,'finding':'source_id cap keeps oldest first-N in KEEP mode or newest last-N in FIFO mode. Defaults are 200 per entity and 200 per relation; graph/VDB can therefore omit sources while full KV tracking retains them.'},{'source':'lightrag/operate.py','line':2633,'finding':'Entity file_path unions old/new paths, deduplicates, drops old placeholder while rebuilding; applies count cap (default75). KEEP keeps earliest paths; FIFO newest, adds ...truncated...(KEEP Old/FIFO). Stored path union is separate from source-id order.'},{'source':'lightrag/operate.py','line':2698,'finding':'Node truncate records source-ID limiting (KEEP Old or FIFO kept/total). This field differs from generation finish_reason=length.'},{'source':'lightrag/operate.py','line':3160,'finding':'Absent relation endpoints may be created as UNKNOWN nodes and inherit relation evidence; source membership is not proof that the entity was separately explicitly extracted.'},{'source':'lightrag/operate.py','line':3665,'finding':'full_entities/full_relations write candidate supersets before graph mutation; candidates alone do not prove a final graph object or supported relation.'},{'source':'lightrag/utils.py','line':6623,'finding':'make_relation_chunk_key sorts endpoints then joins with <SEP>; it loses direction by design because graph stores undirected entity-pair relations.'}],'configuration_caveat':'Saved full_settings does not record resolved max_source_ids/max_file_paths/limit_method, and run_experiment.py supplies no explicit override. Values200/200/75/KEEP above are official defaults, not a reconstructed secret/environment configuration. Actual completeness is established by persisted-set comparisons, independently of assumed defaults.','authoritative_mapping_recommendation':['For a node, use exact entity name -> kv_store_entity_chunks.chunk_ids -> kv_store_text_chunks[chunk_id].full_doc_id -> kv_store_full_docs[full_doc_id], and verify file_path/header.','For an edge, use sorted endpoint pair -> kv_store_relation_chunks.chunk_ids -> text_chunks -> full_docs. Track full source sets even when graph.source_id or file_path is truncated.','Use document recovery indexes as corroboration, not sole authoritative evidence. Never zip source_id tokens with file_path tokens positionally.','Read original chunk/document content to assign individual descriptive statements, predicates or Claim numbers. Membership only records that a graph object was sourced from those chunks, not that every merged description clause is supported by every source.'],'limits':['This audit checks mapping integrity, not semantic correctness of entity resolution or merged descriptions.','A complete mapping does not establish explicit Claim structure; source_id identifies chunks, not Claim numbers or exact evidence spans.','Current node/edge summaries can combine multiple descriptions without a clause-to-source linkage; text-level manual verification remains necessary.','Truncation risks described are code mechanisms; empirical truncation presence/absence is reported separately from hypothetical future scale.'],'snapshot_preservation':'Original files opened read-only; output and script are confined to round2_multisource_audit. No secret file, API, FOT, AutoDL or process action.'}
report['status']='mapping_complete_with_no_detected_schema_mismatches' if not any(counts.values()) else 'mapping_findings_require_interpretation'
(OUT/'source_mapping_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'status':report['status'],'counts':report['counts'],'nonzero_mapping_problems':{k:v for k,v in counts.items() if v},'per_kind':per_kind},ensure_ascii=False,indent=2))
