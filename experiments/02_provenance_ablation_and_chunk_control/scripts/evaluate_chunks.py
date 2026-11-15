"""Materialize the source-grounded semantic review of all12 saved outputs.

The review was performed on the raw records. This script validates the reviewed
target rows against the unchanged official parser output and saves traceable
judgments; it does not ask an LLM to grade itself.
"""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import datetime as dt
import json

ROOT = legacy_root('round3')
ROUND = ROOT / "round3"


def main():
    parsed = json.loads((ROUND/'results/chunk_parsed.json').read_text())
    rows = []
    total_prompt = total_completion = total_cache = 0
    for name in ('SAME','CROSS'):
        for rep in range(1,4):
            chunks=[x for x in parsed['parsed_chunks'] if x['condition']==name and x['repeat']==rep]
            assert len(chunks)==2
            assert all(c['finish_reason']=='stop' and c['completion_delimiter_present'] for c in chunks)
            edges=[e for c in chunks for e in c['edges']]
            nodes=[n for c in chunks for n in c['nodes']]
            target=[e for e in edges if {e['src_id'],e['tgt_id']}=={'Registration Module','Provider'}]
            assert len(target)==1
            faithful='machine readable descriptions' in target[0]['description'].lower()
            partial='provide something' in target[0]['description'].lower()
            assert faithful if name=='SAME' else partial
            condition=next(x for x in parsed['condition_repeats'] if x['condition']==name and x['repeat']==rep)
            flags=condition['candidate_flags']
            assert not flags['strict_module_description_edge_candidates']
            assert not flags['claim27_claim1_dependency_candidates']
            complete_entity=bool(flags['entity_complete_proposition_candidates'])
            assert complete_entity==(name=='SAME')
            retained_fragment=[n for n in nodes if 'machine readable descriptions' in n['description'].lower()]
            assert retained_fragment, 'Do not claim total fact disappearance'
            prompt=sum(c['usage']['prompt_tokens'] for c in chunks)
            completion=sum(c['usage']['completion_tokens'] for c in chunks)
            cache=sum(c['usage'].get('prompt_cache_hit_tokens',0) for c in chunks)
            total_prompt+=prompt; total_completion+=completion; total_cache+=cache
            rows.append({
                'condition':name,'repeat':rep,'primary_semantic_relation_retained':faithful,
                'primary_evidence':target[0],
                'primary_reason':'The parsed Registration Module--Provider relation explicitly states the Claim27 machine-readable-description function.' if faithful else 'The parsed Registration Module--Provider relation ends with provide something; no parsed relation or entity description retains the complete target proposition.',
                'strict_module_descriptions_direct_edge':False,
                'complete_target_in_entity_description':complete_entity,
                'legal_claim27_claim1_edge':False,
                'local_machine_description_entity_fragments_retained':retained_fragment,
                'local_machine_description_edges':[e for e in edges if 'machine readable description' in (e['src_id']+' '+e['tgt_id']+' '+e['description']).lower()],
                'finish_reasons':[c['finish_reason'] for c in chunks],
                'truncated':False,'all_completion_delimiters':True,
                'prompt_tokens':prompt,'completion_tokens':completion,'cache_hit_tokens':cache,
                'records_before_graph_merge':{'nodes':len(nodes),'edges':len(edges)},
                'raw_output_files':[c['input_file'] for c in chunks],
            })
    result={
        'reviewed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'review_method':'AI-assisted direct semantic review of all12 raw responses, exact Claim27 wording and official parser records; not independent human annotation and no new grading API calls.',
        'source_publication_number':'US7991757B2','target_claim':27,
        'ground_truth_quote':'27. The system of claim 1 , wherein the registration module is further configured to allow a provider of an external recommender associated with the plurality of external recommenders to provide machine readable descriptions of the external recommender.',
        'prepared_evidence':'round3/evidence/chunk_conditions.json',
        'official_parse_evidence':'round3/results/chunk_parsed.json',
        'rows':rows,
        'summary':{'SAME':{'primary_semantic_relation_retained':3,'repeats':3,'strict_direct_edge':0,'complete_target_entity_description':3,'legal_dependency_edge':0},'CROSS':{'primary_semantic_relation_retained':0,'repeats':3,'strict_direct_edge':0,'complete_target_entity_description':0,'legal_dependency_edge':0},'truncated_calls':0,'all12_calls_finish_stop':True,'completion_token_range_per_call':[min(c['usage']['completion_tokens'] for c in parsed['parsed_chunks']),max(c['usage']['completion_tokens'] for c in parsed['parsed_chunks'])],'max_tokens_per_call':8192},
        'tokens':{'prompt':total_prompt,'completion':total_completion,'cache_hit':total_cache,'api_prompt_tokens_per_two_chunk_repeat':{'SAME':3721,'CROSS':3722},'source_tokens_per_condition_o200k_base':93},
        'attribution':'In this imposed boundary control, the complete technical proposition is present in the original source and parsed same-chunk outputs, but absent from each cross-chunk extraction and their concatenated parsed relation records. The difference is localized to independent chunk extraction under the changed boundary. Output truncation and record-limit exhaustion are not explanations for these12 responses. Graph indexing, graph merges, retrieval and answer generation were not rerun in this control.',
        'important_limits':[
            'This is an artificial split inside Claim27, not a natural-corpus failure of the original1200-token/100-overlap chunking.',
            'Both conditions contain exactly the same contiguous source bytes in the same order and use two stateless calls. Chunk lengths and whether the subject/object are jointly visible necessarily change. API prompt tokenization differs by one token per condition pair despite the same93 source tokens under the recorded tokenizer.',
            'Fragments survive in CROSS: the module allows a provider to provide something, and descriptions of the external recommender remain in at least an entity description. This is not complete factual information loss.',
            'No exact Module--Machine Readable Descriptions edge appears even in SAME; the correct predicate is represented through Module--Provider. An endpoint-only metric would falsely classify both conditions as failures.',
            'No explicit Claim27--Claim1 dependency edge appears in either condition. That is separate from the technical relation result; the default extractor does not require a legal claim ontology.',
            'Three paired repeats on one patent and one imposed boundary do not establish corpus-wide rates. Temperature0 hosted responses varied; no seed was requested.',
            'The result supports a limitation of independent local extraction under this boundary; it does not by itself establish an implementation bug, prove failure after all possible graph merges, or demonstrate downstream answer failure.'
        ]
    }
    out=ROUND/'evidence/chunk_evaluation.json'
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'output':str(out),'summary':result['summary'],'tokens':result['tokens']},indent=2))


if __name__=='__main__': main()
