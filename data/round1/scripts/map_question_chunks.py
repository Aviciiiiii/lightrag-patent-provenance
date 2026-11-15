"""Map verified quotations and full claims onto actual official chunks; no inference calls."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
import json,re,itertools
from pathlib import Path
BASE=legacy_root()
probe=json.loads((BASE/'results/chunk_probe.json').read_text())
questions=json.loads((BASE/'results/questions.json').read_text())['questions']
patents={r['publication_number']:r for r in json.loads((BASE/'data/selected_patents.json').read_text())}
docs={r['publication_number']:r for r in probe['documents']}

def coverage(chunks,a,b):
    containing=[];overlap=[]
    for ch in chunks:
        s,e=ch['_source_span']['start'],ch['_source_span']['end']
        if s<=a and b<=e: containing.append(ch['chunk_order_index'])
        ov=max(0,min(e,b)-max(s,a))
        if ov: overlap.append({'chunk_index':ch['chunk_order_index'],'diagnostic_chunk_id':ch['diagnostic_chunk_id'],'covered_char_count':ov,'total_char_count':b-a,'coverage_fraction':round(ov/(b-a),6)})
    return {'fully_containing_chunk_indices':containing,'overlapping_chunks':overlap}

out=[]
for q in questions:
    per=[]
    for e in q['evidence']:
        pub=e['publication_number'];d=docs[pub]
        text=(BASE/'data/documents'/d['file_path']).read_text()
        raw=patents[pub]['claims']; offset=text.index(raw)
        for ch in d['chunks']:
            s,t=ch['_source_span']['start'],ch['_source_span']['end']
            assert text[s:t]==ch['content'], (pub,ch['chunk_order_index'])
        a=offset+e['quote_char_start_in_raw_claims'];b=offset+e['quote_char_end_in_raw_claims']
        assert text[a:b]==e['quote']
        ca=text.index(e['full_claim'],offset);cb=ca+len(e['full_claim'])
        per.append({'publication_number':pub,'claim_number':e['claim_number'],'quote':e['quote'],'quote_doc_span':[a,b],'full_claim_doc_span':[ca,cb],'quote_coverage':coverage(d['chunks'],a,b),'full_claim_coverage':coverage(d['chunks'],ca,cb)})
    bydoc=[]
    for pub in q['correct_publication_numbers']:
        es=[x for x in per if x['publication_number']==pub]
        quote_common=set.intersection(*(set(e['quote_coverage']['fully_containing_chunk_indices']) for e in es))
        claim_common=set.intersection(*(set(e['full_claim_coverage']['fully_containing_chunk_indices']) for e in es))
        bydoc.append({'publication_number':pub,'chunk_indices_containing_all_required_quotes':sorted(quote_common),'chunk_indices_containing_all_required_full_claims':sorted(claim_common),'all_quotes_co_resident':bool(quote_common),'all_full_claims_co_resident':bool(claim_common)})
    dstatus='not_applicable'
    if q['category'].startswith('D_'):
        dstatus='co_resident_full_dependency_chain_in_at_least_one_chunk' if all(x['all_full_claims_co_resident'] for x in bydoc) else ('all_selected_quotes_co_resident_but_full_claim_chain_split' if all(x['all_quotes_co_resident'] for x in bydoc) else 'selected_chain_evidence_split_across_chunks')
    out.append({'question_id':q['id'],'category':q['category'],'evidence':per,'per_document_summary':bydoc,'natural_cross_chunk_assessment':dstatus,'query_status':'not_run','extraction_or_retrieval_loss_established':False})
result={'source':'results/chunk_probe.json','official_version':probe['lightrag_version'],'source_commit':probe['source_commit'],'chunk_size':probe['chunk_size'],'overlap':probe['overlap'],'index_convention':'zero-based within each patent; diagnostic_chunk_id is local SHA256, not a persisted LightRAG graph chunk ID','source_spans_exact_match_verified':True,'questions':out,'limitation':'This measures source co-location only. No embedding, entity/relation extraction, graph indexing, retrieval, generation, or citation fidelity was executed. It cannot establish a relation-loss failure.'}
(BASE/'results/question_chunk_mapping.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps([{'id':q['question_id'],'assessment':q['natural_cross_chunk_assessment'],'summary':q['per_document_summary']} for q in out],ensure_ascii=False,indent=2))
