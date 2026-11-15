"""Run record + rough phenomenon check for a rerun of experiments 01-03. Not scoring. No API calls.

Each experiment is given as one or more directories laid out like dot's round folders
(results/, evidence/, logs/, conditions/, config/ ...). A file is looked up in the
directories in the order given, so a split rerun (committed results + local logs) works:

    # a fresh rerun made with run.sh live new
    python tools/summarize_rerun.py --exp01 runs/rerun_01_baseline_index_qa_<UTC> --exp02 ... --out docs/x.md
    # the 2026-11-05 second run (results in git, logs local)
    python tools/summarize_rerun.py --label 20261105 \
        --exp01 experiments/01_baseline_index_qa/results_rerun_20261105 runs/01_baseline_index_qa/rerun_20261105 \
        --exp02 experiments/02_provenance_ablation_and_chunk_control/results_rerun_20261105 runs/02_provenance_ablation_and_chunk_control/rerun_20261105 \
        --exp03 experiments/03_chunk_boundary_full_pipeline/results_rerun_20261105 runs/03_chunk_boundary_full_pipeline/rerun_20261105 \
        --operator "the author, on their own machine, with dot's 11-05 adapted scripts" --out docs/RERUN_20261105_CHECK.md
    # Chinese version for local reading
    python tools/summarize_rerun.py ... --lang zh --out local/zh/RERUN_20261105_CHECK.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'tools'))
from extract_key_evidence import answer, f01_edges, first, refs_in_answer, rel_desc  # noqa: E402

TARGET = 'US7991757B2'
LANG = 'en'


def L(zh: str, en: str) -> str:
    return zh if LANG == 'zh' else en

ORIGINAL = {  # original run (dot, 2026-10-29/30), from the original reports / ledgers
    '01': {'llm': 95, 'embedding': 297, 'cost': 'CNY 1.56–1.77'},
    '02': {'llm': 21, 'embedding': 0, 'cost': 'CNY 0.15–0.65'},
    '03': {'llm': 117, 'embedding': 247, 'cost': 'CNY 1.08–1.33'},
}
STEPS = {
    '01': [('preflight', 'results/preflight.json'), ('smoke', 'results/smoke_run_status.json'),
           ('full', 'results/full_run_status.json'), ('probe', 'evidence/retrieval_rank_probe.json'),
           ('budget', 'results/supplement_budget_Q11_supplementary_mix.json')],
    '02': [('prepare-ablation', 'conditions/condition_manifest.json'), ('prepare-chunks', 'evidence/chunk_conditions.json'),
           ('ablation', 'results/ablation_run_status.json'), ('chunks', 'results/chunk_run_status.json'),
           ('parse', 'results/chunk_parsed.json')],
    '03': [('F01', 'results/run_status_F01.json'), ('F05', 'results/run_status_F05.json'),
           ('F04', 'results/run_status_F04.json'), ('naive', 'results/naive_followup_status.json')],
}


class Run:
    def __init__(self, dirs):
        self.dirs = [Path(d).resolve() for d in dirs]

    def path(self, rel) -> Path | None:
        for d in self.dirs:
            if (d / rel).exists():
                return d / rel
        return None

    def json(self, rel):
        p = self.path(rel)
        return json.loads(p.read_text()) if p else None

    def results_dir(self) -> Path | None:
        return self.path('results')


def step_status(run: Run, rel: str) -> str:
    d = run.json(rel)
    if d is None:
        return L('缺失（未找到输出文件）', 'missing (no output file found)')
    if isinstance(d, dict) and 'status' in d:
        bad = [r.get('run_id') for r in d.get('runs', []) if r.get('status') != 'completed']
        return d['status'] + ((L('（未完成：', ' (not completed: ') + ', '.join(bad) + L('）', ')')) if bad else '')
    if isinstance(d, dict) and 'llm' in d and 'embedding' in d:  # preflight
        ok = d['llm'].get('success') and d['embedding'].get('success')
        return 'completed' if ok else 'failed'
    return L('有输出', 'output present')


def record(exp: str, run: Run) -> list[str]:
    out = [L(f'### 实验 {exp}', f'### Experiment {exp}'), '', L('目录：', 'Directories: ') + ', '.join(f'`{rel(d)}`' for d in run.dirs), '']
    ledger = run.json('results/cost_ledger.json')
    cfg = run.json('evidence/public_runtime_config.json') or {}
    out += [L('| 步骤 | 状态 |', '| step | status |'), '|---|---|']
    out += [f'| {name} | {step_status(run, f)} |' for name, f in STEPS[exp]]
    out.append('')
    if not ledger:
        return out + [L('（没有费用账本 `results/cost_ledger.json`，无法统计调用与费用）', '(no cost ledger `results/cost_ledger.json`; calls and cost not counted)'), '']
    calls = ledger['calls']
    kinds = Counter(c['kind'] for c in calls)
    states = Counter(c['state'] for c in calls)
    starts = sorted(c['started_utc'] for c in calls if c.get('started_utc'))
    ends = sorted(c['finished_utc'] for c in calls if c.get('finished_utc'))
    models = Counter(c.get('model_returned') for c in calls)
    length = [c for c in calls if c.get('finish_reason') == 'length']
    total = ledger.get('estimated_observed_cost_cny', 0) + ledger.get('reserved_unknown_cny', 0)
    o = ORIGINAL[exp]
    out += [
        L('| 项 | 本次 | 原始运行 |', '| item | this run | original run |'), '|---|---|---|',
        f"| {L('会话起点（UTC）', 'session start (UTC)')} | {ledger.get('run_start_utc')} | — |",
        f"| {L('第一次 / 最后一次 API 调用', 'first / last API call')} | {starts[0] if starts else '—'} / {ends[-1] if ends else '—'} | — |",
        f"| {L('LLM 调用', 'LLM calls')} | {kinds.get('llm', 0)} | {o['llm']} |",
        f"| {L('Embedding 调用', 'embedding calls')} | {kinds.get('embedding', 0)} | {o['embedding']} |",
        f"| {L('调用状态', 'call states')} | {', '.join(f'{k}: {v}' for k, v in states.items())} | — |",
        f"| {L('返回的模型名', 'model names returned')} | {', '.join(f'{k}: {v}' for k, v in models.items())} | — |",
        f"| {L('配置的模型', 'configured models')} | LLM `{cfg.get('llm_model')}`, embedding `{cfg.get('embedding_model')}` ({cfg.get('embedding_dim')} dim), thinking={cfg.get('enable_thinking')}, retries={cfg.get('client_max_retries')} | `deepseek-ai/DeepSeek-V4.1-Flash` / `BAAI/bge-m3` |",
        f"| {L('账本合计（估算，非账单）', 'ledger total (estimate, not an invoice)')} | CNY {total:.4f} ({L('硬上限', 'hard cap')} CNY {ledger.get('hard_cap_cny')}) | {o['cost']} |",
        '| finish_reason=length | %d: %s | — |' % (len(length), ', '.join('#%s (%s)' % (c['id'], c['stage']) for c in length) or L('无', 'none')),
        '',
    ]
    if exp == '01':
        s = run.json('evidence/full_settings.json') or {}
        keys = ['chunk_size', 'overlap', 'entity_extract_max_gleaning', 'query_top_k', 'query_chunk_top_k',
                'query_max_entity_tokens', 'query_max_relation_tokens', 'query_max_total_tokens', 'rerank']
        if s:
            out += [L('参数：', 'Parameters: ') + ', '.join(f'{k}={s.get(k)}' for k in keys), '']
        st = run.json('results/full_run_status.json') or {}
        if st.get('index'):
            out += [L(f"索引：{st['index'].get('nodes')} 节点 / {st['index'].get('edges')} 边（原始 612 / 994）", f"Index: {st['index'].get('nodes')} nodes / {st['index'].get('edges')} edges (original 612 / 994)"), '']
    if exp == '03':
        fs = (run.json('conditions/frozen_groups.json') or {}).get('fixed_settings')
        if fs:
            out += [L('冻结设置：', 'Frozen settings: ') + json.dumps(fs, ensure_ascii=False)[:400], '']
    return out


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(REPO))
    except ValueError:
        return str(p)


def checks(r1: Run | None, r2: Run | None, r3: Run | None) -> list[tuple[str, str, str]]:
    lines = []
    again, absent = L('再次出现', 'reappeared'), L('未出现', 'not observed')
    if r1:
        sup = r1.json('results/supplement_budget_Q11_supplementary_mix.json')
        if sup:
            ids = sup.get('api_call_id_range') or []
            req = r1.json(f'logs/api_{ids[-1]:04d}_request.json') if ids else None
            d = sup['result']['data']
            name = L('P1 拼上下文时去掉来源（结构性）', 'P1 sources removed when the context is assembled (structural)')
            if req:
                sp = req['messages'][0]['content']
                ok = sp.count('file_path') == 0 and sp.count('source_id') == 0
                ne = sum(1 for e in d['entities'] if TARGET in (e.get('file_path') or ''))
                nc = sum(1 for c in d['chunks'] if TARGET in c['file_path'])
                lines.append((name, again if ok else absent, L(
                    f"同一题的提示（API {ids[-1]}）：`file_path` 出现 {sp.count('file_path')} 次、`source_id` {sp.count('source_id')} 次；结构化返回里来自 {TARGET} 的实体 {ne} 个、chunk {nc} 个。",
                    f"prompt of the same question (API {ids[-1]}): `file_path` {sp.count('file_path')} times, `source_id` {sp.count('source_id')} times; structured result: {ne} entities and {nc} chunks from {TARGET}.")))
            else:
                lines.append((name, L('未检查', 'not checked'), L('没有找到请求日志', 'request log not found')))
            a11 = answer(sup)
            refs = ', '.join(f'[{a}] {b}' for a, b in refs_in_answer(a11))
            lines.append((L('P1′ Q11 错误归属为“另一专利族”（行为性）', 'P1′ Q11 misattribution to “a different patent family” (behavioural)'),
                          again if 'different patent family' in a11 else L('未再出现', 'did not reappear'),
                          L(f"回答开头：{first(a11, 200)}；引用：{refs}", f"start of answer: {first(a11, 200)}; references: {refs}")))
        b6, s6, b6n = (r1.json(f'results/{f}.json') for f in ('full_Q06_mix', 'supplement_budget_Q06_mix', 'full_Q06_naive'))
        if b6 and s6 and b6n:
            n_base = sum(1 for c in b6['result']['data']['chunks'] if TARGET in c['file_path'])
            n_base_naive = sum(1 for c in b6n['result']['data']['chunks'] if TARGET in c['file_path'])
            n_sup = sum(1 for c in s6['result']['data']['chunks'] if TARGET in c['file_path'])
            refused = 'do not have enough information' in answer(b6).lower()
            label = (again if refused else L('部分再现', 'partly reappeared')) if (n_base == 0 and n_base_naive == 0) else absent
            refs = ', '.join(f'[{a}] {b}' for a, b in refs_in_answer(answer(b6)))
            lines.append((L('P2 Q06 基线预算下缺目标原文', 'P2 Q06 lacks the target text at the baseline budget'), label, L(
                f"基线上下文中 {TARGET} chunk 数：naive {n_base_naive}、mix {n_base}；mix 回答开头：{first(answer(b6), 90)}；mix 引用：{refs}；扩展预算后 mix 中 {TARGET} chunk 数 {n_sup}。",
                f"{TARGET} chunks in the baseline context: naive {n_base_naive}, mix {n_base}; start of mix answer: {first(answer(b6), 90)}; mix references: {refs}; {TARGET} chunks in mix with the extended budget: {n_sup}.")))
        ledger = r1.json('results/cost_ledger.json')
        if ledger:
            ln = [c for c in ledger['calls'] if c.get('finish_reason') == 'length']
            lines.append((L('P4 抽取输出达 3500 上限被截断', 'P4 extraction output cut off at the 3500 limit'),
                          (L(f'再次出现（{len(ln)} 次）', f'reappeared ({len(ln)} times)') if ln else absent),
                          L('账本中 finish_reason=length 的调用：', 'calls with finish_reason=length in the ledger: ') + (', '.join(f"#{c['id']}" for c in ln) or L('无', 'none'))))
    if r2 and r2.path('results/chunk_SAME_r1_c0.json'):
        rd = r2.results_dir()
        cross = [rel_desc(json.loads((rd / f'chunk_CROSS_r{r}_c0.json').read_text())['response']['content'] + '\n' +
                          json.loads((rd / f'chunk_CROSS_r{r}_c1.json').read_text())['response']['content'], 'Registration Module') for r in [1, 2, 3]]
        same = [rel_desc(json.loads((rd / f'chunk_SAME_r{r}_c0.json').read_text())['response']['content'], 'Registration Module') for r in [1, 2, 3]]
        full = lambda ds: any('machine readable' in d.lower() for d in ds)  # noqa: E731
        lines.append((L('P5 人为句内切分丢失完整关系', 'P5 artificial mid-sentence split loses the complete relation'),
                      L(f"SAME {sum(map(full, same))}/3、CROSS {sum(map(full, cross))}/3 含“machine readable”",
                        f"SAME {sum(map(full, same))}/3, CROSS {sum(map(full, cross))}/3 contain “machine readable”"),
                      L('字符串粗查 Registration Module 关系描述；CROSS 例：', 'string check of Registration Module relation descriptions; CROSS example: ')
                      + (cross[0][0] if cross[0] else L('（无）', '(none)'))))
        abl_c = [refs_in_answer(json.loads((rd / f'ablation_C_r{r}.json').read_text())['response']['content']) for r in [1, 2, 3]]
        n = sum(1 for x in abl_c if ('1', 'US7991757B2.txt') in x)
        lines.append((L('P9 消融 C 条件引用编号冲突（实验设计）', 'P9 citation-number conflict in ablation condition C (experiment design)'),
                      L(f"{n}/3 次把 [1] 写成 US7991757B2.txt", f"{n}/3 cite [1] as US7991757B2.txt"),
                      L('冻结引用表中 [1] 是 US10867122B1.txt', 'in the frozen reference list [1] is US10867122B1.txt')))
    if r3 and r3.path('results/F01_A_r1'):
        rd = r3.results_dir()
        marks, kept, trunc = {}, {}, {}
        for cond in 'AB':
            m = []
            for r in [1, 2, 3]:
                pe = rd / f'F01_{cond}_r{r}' / 'parsed_extraction.json'
                if not pe.exists():
                    m.append('?')
                    continue
                es = ' '.join(f01_edges(f'F01_{cond}_r{r}', rd)).lower()
                kept[(cond, r)] = 'case' in es and 'expert' in es
                trunc[(cond, r)] = any(x['finish_reason'] == 'length' for x in json.loads(pe.read_text())['records'])
                m.append(('✓' if kept[(cond, r)] else '✗') + (L('(截断)', '(truncated)') if trunc[(cond, r)] else ''))
            marks[cond] = ' '.join(m)
        pairs = [r for r in (1, 2, 3) if ('A', r) in trunc and ('B', r) in trunc and not trunc[('A', r)] and not trunc[('B', r)]]
        same_dir = [r for r in pairs if kept[('A', r)] and not kept[('B', r)]]
        b_kept = any(kept.get(('B', r)) for r in (1, 2, 3))
        label = L(f'干净配对 {len(pairs)} 对，其中 {len(same_dir)} 对为“同块保留、跨块丢失”' + ('；但跨块条件并非每次都丢失' if b_kept else ''),
                  f'{len(pairs)} clean pairs, {len(same_dir)} of them “kept same-chunk, lost cross-chunk”' + ('; but the cross-chunk condition did not always lose it' if b_kept else ''))
        lines.append((L('P5′ F01 同块/跨块谓词保留差异', 'P5′ F01 predicate kept same-chunk vs cross-chunk'), label + f" (A {marks['A']}; B {marks['B']})",
                      L('字符串粗查（解析后关系描述同时含 ontology+cases+experts）；该规则在原始运行上与原报告一致（A 3/3、B 0/3，干净配对 1 对）',
                        'string check (parsed relation descriptions containing ontology + cases + experts); on the original run this rule agrees with the original report (A 3/3, B 0/3, 1 clean pair)')))
        nb_p = rd / 'F01_B_r2' / 'natural_naive.json'
        if nb_p.exists():
            nb = answer(json.loads(nb_p.read_text()))
            lines.append((L('P8 F01_B_r2 naive 编造 Claim 依赖链（行为性）', 'P8 F01_B_r2 naive invents a claim-dependency chain (behavioural)'),
                          L('再次出现同样的表述', 'the same wording reappeared') if 'sequence of dependencies' in nb else L('未再出现同样的表述', 'the same wording did not reappear'),
                          L('自动规则：回答中是否出现 “sequence of dependencies”（原错误把 4→5→6→8 称为依赖顺序）；需复核',
                            'automatic rule: does the answer contain “sequence of dependencies” (the original error called 4→5→6→8 a dependency order); needs review')))
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--exp01', nargs='+')
    ap.add_argument('--exp02', nargs='+')
    ap.add_argument('--exp03', nargs='+')
    ap.add_argument('--label', default='')
    ap.add_argument('--out', type=Path)
    ap.add_argument('--operator', default='', help='who ran it (printed in the header)')
    ap.add_argument('--lang', choices=['en', 'zh'], default='en')
    a = ap.parse_args()
    global LANG
    LANG = a.lang
    runs = {k: Run(v) for k, v in (('01', a.exp01), ('02', a.exp02), ('03', a.exp03)) if v}
    when = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lab = (' — ' + a.label) if a.label else ''
    md = [L(f'# 复跑运行记录与粗查{lab}', f'# Rerun record and rough check{lab}'), '',
          L('> **这是运行记录和粗查，不是评分。** 由 `tools/summarize_rerun.py` 从运行目录里的状态文件、费用账本和日志自动生成；'
            f'“粗查”是对 README 所展示现象的字符串级检查。评分见 `docs/REPRODUCIBILITY.md`。生成时间 {when}。',
            '> **This is a run record and a rough check, not scoring.** Generated by `tools/summarize_rerun.py` from the status files, '
            'cost ledger and logs in the run directories; the “rough check” is a string-level check of the phenomena shown in the README. '
            f'Scoring: `docs/REPRODUCIBILITY.md`. Generated {when}.'), '']
    if a.operator:
        md += [L(f'运行者：{a.operator}。', f'Run by: {a.operator}.'), '']
    md += [L('## 运行记录', '## Run record'), '']
    for exp, run in runs.items():
        md += record(exp, run)
    md += [L('## 现象粗查', '## Rough check of phenomena'), '', L('| 现象 | 本次 | 依据 |', '| phenomenon | this run | basis |'), '|---|---|---|']
    md += [f'| {x} | {y} | {z} |' for x, y, z in checks(runs.get('01'), runs.get('02'), runs.get('03'))]
    text = '\n'.join(md) + '\n'
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text, encoding='utf-8')
    print(text)


if __name__ == '__main__':
    main()
