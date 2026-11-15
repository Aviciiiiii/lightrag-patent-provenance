"""Score one run (original / 20261105 / a later rerun) with docs/SCORING_RUBRIC.md. No API calls.

Every judgment is first made by a written rule (S1-S13 in the rubric). Two kinds of review can
override it, with this priority:
  docs/scoring/human_review_<label>.json   review by the repository author (human review; done in Chinese,
                                           note_zh is the original, note_en a translation)
  docs/scoring/claude_review_<label>.json  review by Claude Code reading the answers
Each row records the rule value, both reviews if present, the final value, its status and where the evidence is.
For the original run, dot's own labels are attached so agreement can be measured.

    python tools/score_runs.py original
    python tools/score_runs.py 20261105
    python tools/score_runs.py 20261115      # any rerun imported as experiments/*/results_rerun_<label>/
Writes docs/scoring/scores_<label>.json and prints a summary.
"""
from __future__ import annotations

import json
from collections import Counter
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
E1 = REPO / 'experiments/01_baseline_index_qa'
E2 = REPO / 'experiments/02_provenance_ablation_and_chunk_control'
E3 = REPO / 'experiments/03_chunk_boundary_full_pipeline'
OUT = REPO / 'docs/scoring'
REVIEWER = {'human review': 'reviewed by the author',
            'Claude Code review': 'reviewed by Claude Code, pending human review',
            'rule': 'rule only, not reviewed item by item'}
TARGET = 'US7991757B2'

ABSTAIN = re.compile(r'do not have enough information|not have sufficient information|cannot (?:compare|answer|quote)|'
                     r'insufficient (?:information|evidence) to', re.I)
MISATTRIB = re.compile(r'different patent family|belongs? to (?:a )?(?:different|another) patent|'
                       r'in (?:a )?(?:different|another|separate) patent(?! publication number)', re.I)


def j(p: Path):
    return json.loads(p.read_text())


def norm(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()


def lex(s: str) -> str:
    return ' '.join(re.findall(r'\w+', s.lower()))


def answer_of(obj) -> str:
    if not obj:
        return ''
    if isinstance(obj.get('result'), dict):
        return ((obj['result'].get('llm_response') or {}).get('content')) or ''
    if isinstance(obj.get('response'), dict):
        return obj['response'].get('content') or ''
    return obj.get('content') or obj.get('answer') or ''


def claim_mentioned(text: str, n: int) -> bool:
    # "Claim 6", "claims 1 and 27", "Claims 4, 5, 8", "Claim1"
    for m in re.finditer(r'[Cc]laims?\s*((?:\d+\s*(?:,|and|&|or|–|-|/)?\s*)+)', text):
        if n in [int(x) for x in re.findall(r'\d+', m.group(1))]:
            return True
    return False


def claim_near_pub(text: str, pub: str, n: int, others=(), window: int = 700) -> bool:
    """Claim n named after a mention of pub, before the next mention of another required patent."""
    for m in re.finditer(pub, text):
        end = m.start() + window
        for o in others:
            k = text.find(o, m.end())
            if k != -1:
                end = min(end, k)
        if claim_mentioned(text[m.start():end], n):
            return True
    return False


def opening_abstains(text: str) -> bool:
    return bool(ABSTAIN.search(text[:260]))


def references(text: str) -> list[tuple[str, str]]:
    tail = text.split('### References')[-1] if '### References' in text else ''
    return re.findall(r'\[(\d+)\]\s*([\w.]+)', tail)


class Run:
    def __init__(self, label: str):
        self.label = label
        sub = 'results' if label == 'original' else f'results_rerun_{label}/results'
        self.r1, self.r2, self.r3 = E1 / sub, E2 / sub, E3 / sub
        self.cond2 = E2 / 'conditions' if label == 'original' else E2 / f'results_rerun_{label}/conditions'


# ----------------------------------------------------------------------------- rules
def s1_core(ans: str, q: dict) -> tuple[bool, str]:
    pairs = sorted({(e['publication_number'], e['claim_number']) for e in q['evidence']})
    pubs = q['correct_publication_numbers']
    if opening_abstains(ans):
        return False, 'opening abstains'
    miss_pub = [p for p in pubs if p not in ans]
    if miss_pub:
        return False, f'missing publication {miss_pub}'
    if len(pubs) > 1:
        # cross-document: each patent's own passage must cite at least one of its claims (dot accepted
        # equivalent claims, e.g. Claims 4/17 instead of 1 for US7991757B2 in the supplementary Q06 answer)
        miss = [p for p in pubs if not any(claim_near_pub(ans, p, n, [o for o in pubs if o != p]) for n in range(1, 60))]
    else:
        miss = [(p, n) for p, n in pairs if not claim_mentioned(ans, n)]
    if miss:
        return False, f'required claim not named {miss}'
    return True, 'all publications named with claims in their own passages, no opening abstention'


def s2_evidence(res: dict, q: dict) -> tuple[bool, str]:
    chunks = norm(' '.join(c.get('content', '') for c in res['result']['data'].get('chunks', [])))
    quotes = [e['quote'] for e in q['evidence']]
    miss = [x[:40] for x in quotes if norm(x) not in chunks]
    return not miss, ('all required quotes in same-call chunks' if not miss else f'missing {len(miss)}/{len(quotes)}: {miss}')


def s3_misattribution(ans: str) -> tuple[bool, str]:
    m = MISATTRIB.search(ans)
    return bool(m), (f'phrase: {m.group(0)!r}' if m else 'no misattribution phrase')


def q11_as_question() -> dict:
    o = j(E1 / 'evidence/optional_question11.json')
    return {'id': 'Q11', 'correct_publication_numbers': o['correct_publication_numbers'],
            'evidence': [{'publication_number': TARGET, 'claim_number': e['claim_number'],
                          'quote': e['full_claim']} for e in o['evidence']]}


def q11_claim_clauses() -> list[str]:
    a = j(E1 / 'evidence/supplement_budget_audit.json')['concrete_attribution_failure']
    return [a['claim1_exact_source_clause'], a['claim27_exact_source_clause']]


NEG_ATTR = re.compile(r'not (?:linked|tied)\** [^.]{0,60}?US7991757B2|does not (?:contain|include) any [^.]*(?:entity|document)[^.]*US7991757B2|'
                      r'no [^.]*(?:entity|chunk|document)[^.]*for \**US7991757B2', re.I)
POS_ATTR = re.compile(r'US7991757B2\** (?:is referenced|appears) only|referencing \**US7991757B2|evidence (?:relating|related) to that patent|'
                      r'[Cc]laim 1 of US7991757B2|US7991757B2\**\s*[—-]|In US7991757B2', re.I)


def s5_doc_attribution(ans: str) -> tuple[bool, str]:
    if NEG_ATTR.search(ans):
        return False, f'negated link: {NEG_ATTR.search(ans).group(0)[:80]!r}'
    if POS_ATTR.search(ans):
        return True, f'positive link: {POS_ATTR.search(ans).group(0)[:80]!r}'
    return False, 'no explicit link of the registration evidence to US7991757B2'


def s6_claim_task(ans: str) -> tuple[bool, str]:
    c1, c27 = (lex(x) for x in q11_claim_clauses())
    la = lex(ans)
    has = [c1[:60] in la, c27[:60] in la]
    dep = bool(re.search(r'claim 27[^.]{0,80}(?:depend|of claim 1)|depends? (?:on|from) claim 1|the system of claim 1', ans, re.I))
    ok = all(has) and dep and not opening_abstains(ans)
    return ok, f'claim1 clause {has[0]}, claim27 clause {has[1]}, dependency stated {dep}'


def s7_ref_conflict(ans: str, refmap: dict) -> tuple[bool, str]:
    bad = [(i, f) for i, f in references(ans) if refmap.get(i) not in (None, f)]
    return bool(bad), (f'remapped ids {bad}' if bad else 'all reference ids match the frozen list')


def s8_chunk_relation(parsed_nodes_edges: list) -> tuple[bool, str]:
    hits = [e for e in parsed_nodes_edges
            if 'Registration Module' in (e.get('src_id', '') + e.get('tgt_id', ''))
            and 'machine readable descriptions' in e.get('description', '').lower()]
    return bool(hits), (hits[0]['description'][:120] if hits else 'no Registration Module relation with "machine readable descriptions"')


# --- experiment 03 graph predicates: dot's own matchers, copied verbatim in meaning
def _n1(x):
    return re.sub(r'\s+', ' ', str(x).lower().replace('-', ' '))


def f01_pred(text, key):
    s = _n1(text)
    onto = 'ontology' in s
    if key == 'R_umls':
        return onto and ('unified medical language system' in s or 'umls' in s) and any(v in s for v in ['based', 'basis', 'underl'])
    role = bool(re.search(r'existing(?: medical)? cases?', s)) if key == 'R_case' else 'expert' in s
    return onto and role and any(v in s for v in ['embed', 'represent']) and any(v in s for v in ['based', 'basis', 'used', 'using', 'compute'])


def _n5(s):
    return re.sub(r'[\W_]+', ' ', s.lower()).strip()


def f05_match(e, p):
    a, b = e.get('source', e.get('src_id', '')), e.get('target', e.get('tgt_id', ''))
    end, d = _n5(a + ' ' + b), _n5(e.get('description', ''))
    if p == 'P1':
        return 'naive bayes' in end and 'filter' in d and ('employ' in d or 'uses' in d)
    if p == 'P2':
        return 'second classification data' in end and 'filter' in end and 'generat' in d and 'second classification data' in d
    return 'second classification data' in end and 'non persistent memory' in end and ('resid' in d or 'stored' in d)


def f04_witness(e, p):
    d = e.get('description', '').lower()
    cost = bool(re.search(r'cost|pecuniary|monetary', d))
    if p == 'P1':
        return cost and (bool(re.search(r'rank|select', d)) or ('parameter' in d and 'pecuniary' in d) or ('metric' in d and 'monetary' in d))
    return cost and (('allowed to provide' in d) or ('provide a cost' in d) or ('cost value' in d and 'provided by the context-data source' in d)
                     or ('cost value' in d and 'as provided by the context-data source' in d))


def s9_merged(group: str, graph: dict) -> tuple[bool, str]:
    edges = graph['edges']
    if group == 'F01':
        got = {k: any(f01_pred(json.dumps(e, ensure_ascii=False), k) for e in edges) for k in ['R_case', 'R_expert', 'R_umls']}
    elif group == 'F05':
        got = {k: any(f05_match(e, k) for e in edges) for k in ['P1', 'P2', 'P3']}
    else:
        got = {k: any(f04_witness(e, k) for e in edges) for k in ['P1', 'P2']}
    return all(got.values()), json.dumps(got)


KEYTERMS = {
    'F01': ([4, 8], [r'unified medical language system|umls', r'expert', r'existing (?:medical )?cases?', r'ontology']),
    'F05': ([6, 10], [r'naive bayes', r'non-?\s?persistent', r'second classification data']),
    'F04': ([], [r'pecuniary|monetary|cost', r'provid']),
}


def s12_core_answer(group: str, ans: str, pub: str) -> tuple[bool, str]:
    claims, terms = KEYTERMS[group]
    if not ans or opening_abstains(ans):
        return False, 'empty or abstains'
    miss_c = [n for n in claims if not claim_mentioned(ans, n)]
    if group == 'F04':
        miss_c = [] if (any(claim_mentioned(ans, n) for n in (1, 18, 22)) and any(claim_mentioned(ans, n) for n in (14, 25))) else ['1/18/22 and 14/25']
    miss_t = [t for t in terms if not re.search(t, ans, re.I)]
    ok = not miss_c and not miss_t and pub in ans
    return ok, f'claims missing {miss_c}, terms missing {miss_t}, publication named {pub in ans}'


def s13_dependency_error(ans: str, claims: dict) -> tuple[bool, str]:
    """A stated claim-dependency chain that contradicts the claims text."""
    parent = {int(c['claim_number']): (int(m.group(1)) if (m := re.search(r'\bof claim (\d+)', c['text'][:120], re.I)) else None)
              for c in claims}
    errs = []
    for m in re.finditer(r'[Cc]laim (\d+)\s+(?:depends|is dependent)\s+(?:on|from|upon)\s+[Cc]laim (\d+)', ans):
        a, b = int(m.group(1)), int(m.group(2))
        if parent.get(a) is not None and parent.get(a) != b:
            errs.append(f'claim {a} said to depend on {b}, actually {parent.get(a)}')
    for para in re.split(r'\n\s*\n', ans):
        if 'depend' not in para.lower():
            continue
        for chain in re.findall(r'[Cc]laim \d+(?:\s*(?:\([^)]*\))?\s*(?:→|->)\s*[Cc]laim \d+)+', para):
            nums = [int(x) for x in re.findall(r'\d+', re.sub(r'\([^)]*\)', '', chain))]
            for a, b in zip(nums, nums[1:]):
                if parent.get(b) is not None and parent.get(b) != a:
                    errs.append(f'chain {a}→{b}: claim {b} depends on {parent.get(b)}')
    return bool(errs), ('; '.join(errs) or 'no contradicted dependency statement')


# ----------------------------------------------------------------------------- dot labels (original run only)
def dot_labels() -> dict:
    lab = {}
    a = j(E1 / 'evidence/full_audit_q01_q05.json')['audits']
    for x in a:
        lab[('S1', f"{x['question_id']}/{x['mode']}")] = x['core_required_fact_correct']
        lab[('S2', f"{x['question_id']}/{x['mode']}")] = x['all_required_quotes_retrieved']
    for x in j(E1 / 'evidence/full_audit_q06_q11.json')['rows']:
        qid = x['question_id'].replace('_supplementary', '')
        sc = x['scores_by_dimension']
        lab[('S1', f"{qid}/{x['mode']}")] = sc['core_question_completed']
        lab[('S2', f"{qid}/{x['mode']}")] = sc['patent_retrieval'] == 'all_required_present'
    for x in j(E1 / 'evidence/supplement_budget_audit.json')['rows']:
        qid = x['question_id'].replace('_supplementary', '')
        lab[('S1', f"supplement/{qid}/{x['mode']}")] = x['verdict']['core_question_completed']
    for k in list(lab):
        if k[0] == 'S1':
            lab[('S3', k[1])] = k[1] == 'supplement/Q11/mix'
    for x in j(E2 / 'evidence/ablation_evaluation.json')['rows']:
        key = f"{x['condition']}{x['repeat']}"
        s = x['scores']
        lab[('S5', key)] = s['correct_document_attribution']
        lab[('S6', key)] = s['claim_task_core_complete_and_grounded']
        lab[('S7', key)] = not s['reference_ids_match_original_context']
        lab[('S4', key)] = s['positive_wrong_source_assignment_or_exclusion_in_prose']
    for x in j(E2 / 'evidence/chunk_evaluation.json')['rows']:
        lab[('S8', f"{x['condition']}_r{x['repeat']}")] = x['primary_semantic_relation_retained'] in (True, 'True')
    f01 = {r['run_id']: r for r in j(E3 / 'evidence/F01_evaluation.json')['runs']}
    for rid, r in f01.items():
        lab[('S9', rid)] = r['all_three_merged_predicates']
        lab[('S10', rid)] = bool(r['truncated_extraction_ids'])
        lab[('S11', rid)] = r['natural']['both_original_target_quotes_retrieved']
        lab[('S12', rid + '/mix')] = r['manual_answer_review']['natural_core_predicates_correct']
        lab[('S12', rid + '/forced')] = r['manual_answer_review']['forced_core_predicates_correct']
        lab[('S12', rid + '/naive')] = r['naive']['core_answer_correct']
        lab[('S13', rid + '/naive')] = rid == 'F01_B_r2'
    for r in j(E3 / 'evidence/F05_evaluation.json')['runs']:
        rid = r['run_id']
        lab[('S9', rid)] = all(r['predicates'][p]['merged_relation_present'] for p in ['P1', 'P2', 'P3'])
        lab[('S10', rid)] = not r['valid_untruncated_extraction_run']
        lab[('S11', rid)] = r['natural_retrieval']['both_target_claims_available']
        na = r['natural_answer']
        lab[('S12', rid + '/mix')] = all(na[k] for k in ['core_classifier_correct', 'second_data_memory_and_exclusivity_correct', 'supporting_claim6_and10_correct'])
        lab[('S12', rid + '/forced')] = r['forced_diagnostic']['core_answer_and_claims_correct']
        lab[('S12', rid + '/naive')] = r['naive']['core_answer_correct']
        lab[('S13', rid + '/naive')] = False
    for r in j(E3 / 'evidence/F04_evaluation.json')['runs']:
        rid, s = r['run_id'], r['summary']
        lab[('S9', rid)] = s['merged_P1'] and s['merged_P2']
        lab[('S10', rid)] = not s['untruncated']
        lab[('S11', rid)] = s['natural_evidence']
        lab[('S12', rid + '/mix')] = s['core_answer']
        lab[('S12', rid + '/forced')] = s['forced_core_answer']
        lab[('S12', rid + '/naive')] = s['naive_core_answer']
        lab[('S13', rid + '/naive')] = False
    return lab


# ----------------------------------------------------------------------------- scoring
def score(label: str) -> list[dict]:
    run = Run(label)
    rows = []

    def add(code, item, value, why, evidence):
        rows.append({'rubric': code, 'item': item, 'rule_value': value, 'rule_reason': why, 'evidence': evidence})

    rel = lambda p: str(p.relative_to(REPO))  # noqa: E731
    questions = {q['id']: q for q in j(REPO / 'data/round1/results/questions.json')['questions']}
    questions['Q11'] = q11_as_question()
    for qid, q in questions.items():
        for mode in ('naive', 'mix'):
            f = run.r1 / f"full_{qid if qid != 'Q11' else 'Q11_supplementary'}_{mode}.json"
            if not f.exists():
                continue
            res, ans = j(f), answer_of(j(f))
            add('S1', f'{qid}/{mode}', *s1_core(ans, q), rel(f) + ' → result.llm_response.content')
            add('S2', f'{qid}/{mode}', *s2_evidence(res, q), rel(f) + ' → result.data.chunks')
            add('S3', f'{qid}/{mode}', *s3_misattribution(ans), rel(f) + ' → result.llm_response.content')
    for qid in ('Q06', 'Q11'):
        for mode in ('naive', 'mix'):
            f = run.r1 / f"supplement_budget_{qid if qid != 'Q11' else 'Q11_supplementary'}_{mode}.json"
            if f.exists():
                ans = answer_of(j(f))
                add('S1', f'supplement/{qid}/{mode}', *s1_core(ans, questions[qid]), rel(f))
                add('S3', f'supplement/{qid}/{mode}', *s3_misattribution(ans), rel(f))
    refmap = {x['reference_id']: x['file_path'] for x in j(E1 / 'results/supplement_budget_Q11_supplementary_mix.json')['result']['data']['references']}
    for cond in 'ABC':
        for rep in (1, 2, 3):
            f = run.r2 / f'ablation_{cond}_r{rep}.json'
            if not f.exists():
                continue
            ans = answer_of(j(f))
            key = f'{cond}{rep}'
            add('S4', key, *s3_misattribution(ans), rel(f) + ' → response.content')
            add('S5', key, *s5_doc_attribution(ans), rel(f) + ' → response.content')
            add('S6', key, *s6_claim_task(ans), rel(f) + ' → response.content')
            add('S7', key, *s7_ref_conflict(ans, refmap), rel(f) + ' → References')
    parsed = run.r2 / 'chunk_parsed.json'
    if parsed.exists():
        pj = j(parsed)
        recs = pj['parsed_chunks']
        for cond in ('SAME', 'CROSS'):
            for rep in (1, 2, 3):
                edges = [e for r in recs if r['condition'] == cond and int(r['repeat']) == rep for e in r['edges']]
                add('S8', f'{cond}_r{rep}', *s8_chunk_relation(edges), rel(parsed) + ' → parsed_chunks[].edges')
    groups = {g['id']: g for g in j(E3 / 'conditions/frozen_groups.json')['groups']}
    claims_cache = {}
    for gid in ('F01', 'F05', 'F04'):
        g = groups[gid]
        pub = g['publication_number']
        claims_cache[pub] = j(REPO / f'data/claims/{pub}.json')
        for cond in 'AB':
            for rep in (1, 2, 3):
                rid = f'{gid}_{cond}_r{rep}'
                d = run.r3 / rid
                if not (d / 'merged_graph.json').exists():
                    continue
                add('S9', rid, *s9_merged(gid, j(d / 'merged_graph.json')), rel(d / 'merged_graph.json'))
                trunc = [x['call_id'] for x in j(d / 'parsed_extraction.json')['records'] if x['finish_reason'] == 'length']
                add('S10', rid, bool(trunc), f'finish_reason=length calls {trunc}', rel(d / 'parsed_extraction.json'))
                nq = j(d / 'natural_query.json')
                ctx = norm(' '.join(c.get('content', '') for c in nq['result']['data'].get('chunks', [])))
                fam = {k: any(norm(a['quote']) in ctx for a in v) for k, v in g['evidenceanchors'].items()}
                add('S11', rid, all(fam.values()), f'anchor families retrieved {fam}', rel(d / 'natural_query.json'))
                for kind, fname in (('mix', 'natural_query.json'), ('naive', 'natural_naive.json'), ('forced', 'forced_diagnostic.json')):
                    if (d / fname).exists():
                        ans = answer_of(j(d / fname))
                        add('S12', f'{rid}/{kind}', *s12_core_answer(gid, ans, pub), rel(d / fname))
                        if kind == 'naive':
                            add('S13', f'{rid}/{kind}', *s13_dependency_error(ans, claims_cache[pub]), rel(d / fname))
    return rows


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else 'original'
    rows = score(label)
    load = lambda f: j(f) if f.exists() else {}  # noqa: E731
    claude, human = load(OUT / f'claude_review_{label}.json'), load(OUT / f'human_review_{label}.json')
    dot = dot_labels() if label == 'original' else {}
    for r in rows:
        key = f"{r['rubric']}:{r['item']}"
        c, h = claude.get(key), human.get(key)
        if c:
            r['claude_code_review'] = {'value': c['value'], 'note': c['note']}
        if h:
            r['human_review'] = {k: h[k] for k in ('value', 'note_zh', 'note_en', 'review_language', 'date') if k in h}
        r['value'] = h['value'] if h else (c['value'] if c else r['rule_value'])
        r['status'] = 'human review' if h else ('Claude Code review' if c else 'rule')
        r['reviewer'] = REVIEWER[r['status']]
        if dot:
            dl = dot.get((r['rubric'], r['item']))
            r['dot_label'] = None if dl is None else bool(dl)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'scores_{label}.json').write_text(json.dumps({'label': label, 'rubric': 'docs/SCORING_RUBRIC.md', 'review_counts': dict(Counter(r['reviewer'] for r in rows)),
                                                          'rows': rows}, ensure_ascii=False, indent=1) + '\n')
    by = {}
    for r in rows:
        by.setdefault(r['rubric'], []).append(r)
    print(f'{label}: {len(rows)} judgments')
    for code in sorted(by, key=lambda c: int(c[1:])):
        rs = by[code]
        line = f'  {code}: true {sum(x["value"] for x in rs)}/{len(rs)}'
        if dot:
            cmp = [x for x in rs if x.get('dot_label') is not None]
            line += f' | agree with dot {sum(x["value"] == x["dot_label"] for x in cmp)}/{len(cmp)}'
        print(line)
    if dot:
        dis = [r for r in rows if r.get('dot_label') is not None and r['value'] != r['dot_label']]
        for r in dis:
            print('  DISAGREE', r['rubric'], r['item'], 'rule', r['rule_value'], 'dot', r['dot_label'], '|', r['rule_reason'][:120])
    elif (OUT / 'scores_original.json').exists():
        # review checklist: every rule judgment that differs from the original run should be read
        orig = {(x['rubric'], x['item']): x['value'] for x in j(OUT / 'scores_original.json')['rows']}
        # S10 (finish_reason == length) is a logged fact, not a judgment, so it is left out
        diff = [r for r in rows if r['rubric'] != 'S10' and (r['rubric'], r['item']) in orig
                and r['rule_value'] != orig[(r['rubric'], r['item'])]]
        print(f'  rule value differs from the original run: {len(diff)} (read each; record the result in '
              f'claude_review_{label}.json or human_review_{label}.json)')
        for r in diff:
            print(f"    {r['rubric']}:{r['item']}  rule {r['rule_value']}  original {orig[(r['rubric'], r['item'])]}"
                  f"  now {r['value']} [{r['status']}]")


if __name__ == '__main__':
    main()
