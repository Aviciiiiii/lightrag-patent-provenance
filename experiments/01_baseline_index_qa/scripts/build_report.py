"""Second-round Chinese report from saved real runs and reviewed evidence."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
from datetime import datetime,timezone
import json,html,re
ROOT=legacy_root('round2');R=ROOT/'round2';E=html.escape
load=lambda p:json.loads((ROOT/p).read_text())
questions=load('results/questions.json')['questions']
cost=load('round2/evidence/cost_summary.json')
ledger=load('round2/results/cost_ledger.json')
gate=load('round2/results/official_query_gate.json')
full=load('round2/results/full_run_status.json')
extra=load('round2/evidence/optional_question11.json')
now=datetime.now(timezone.utc);start=datetime.fromisoformat('2026-10-29T14:13:44+00:00')
minutes=(now-start).total_seconds()/60
last_api=max(c['finished_utc'] for c in ledger['calls'])
first_api=min(c['started_utc'] for c in ledger['calls'])
style=re.search(r'<style>(.*?)</style>',(ROOT/'report/LightRAG_patent_provenance_report_zh.html').read_text(),re.S).group(1)
style+='pre.answer{white-space:pre-wrap;font-family:inherit;font-size:13px;line-height:1.55;background:#f6f8fa;padding:14px;border-radius:6px}td{overflow-wrap:anywhere}.ok{color:#21613f}.warn{color:#8a4c04}.notice{border-color:#31815c;background:#eff8f3}.pill{background:#eef3f6;padding:2px 7px;border-radius:6px;white-space:nowrap}summary{line-height:1.5}'

paragraph='[已删去：与实验无关的个人申请材料，见 reports/README.md]'
words=len(paragraph.split())  # word-count assert removed with the paragraph
(R/'report/research_interest.txt').write_text(paragraph+'\n')

def answer_cell(qid,mode):
 d=load(f'round2/results/full_{qid}_{mode}.json');r=d['result'];a=r['llm_response']['content'];data=r.get('data',{})
 if qid=='Q06':verdict='未完成比较；明确说明证据不足'
 elif qid=='Q01' and mode=='mix':verdict='核心事实正确；“集合中唯一”推断超出检索范围'
 else:verdict='核心事实、专利及 Claim 正确'
 cited='；'.join(f"[{x['reference_id']}] {x['file_path']}" for x in data.get('references',[]) if x['file_path'].split('.')[0] in set(re.findall(r'US\d+[AB]\d',a)))
 cnt=f"E {len(data.get('entities',[]))} / R {len(data.get('relationships',[]))} / C {len(data.get('chunks',[]))}"
 return f"<b>{E(verdict)}</b><br><span class='muted'>{cnt}</span><details><summary>实际回答及引用</summary><pre class='answer'>{E(a)}</pre><p class='small'>同次返回来源（与答案所提专利相交）：{E(cited)}</p></details>"

table=[]
for q in questions:
 evidence='；'.join(dict.fromkeys(f"{e['publication_number']} / Claim {e['claim_number']}" for e in q['evidence']))
 kind='检索/上下文覆盖不足；非抽取或索引丢失' if q['id']=='Q06' else ('mix：生成阶段范围扩大；未证明断言为假' if q['id']=='Q01' else '未发现核心事实错误；引文有格式精度备注')
 table.append(f"<tr><td>{q['id']}<br>{q['category'][0]}</td><td>{E(q['question_zh'])}</td><td><b>{E(evidence)}</b><br>{E(q['expected_answer_zh'])}</td><td>{answer_cell(q['id'],'naive')}</td><td>{answer_cell(q['id'],'mix')}</td><td>{E(kind)}</td></tr>")

q4=load('round2/results/full_Q04_mix.json')['result']
q4answer=q4['llm_response']['content']
q4e=next(q for q in questions if q['id']=='Q04')['evidence'][0]
q11mix=load(f"round2/results/supplement_budget_{extra['id']}_mix.json")['result']
reg=next(x for x in q11mix['data']['entities'] if x['entity_name']=='Registration Module')
supp=[]
for qid,label in [('Q06','原 Q06 跨文档比较'),(extra['id'],'补充 Q11 自然跨块依赖')]:
 for mode in ['naive','mix']:
  result=load(f'round2/results/supplement_budget_{qid}_{mode}.json')['result'];data=result['data'];a=result['llm_response']['content']
  outcome='找回目标原文，完成比较' if qid=='Q06' else ('仍未取回目标原文；来源判断错误' if mode=='mix' else '仍未取回目标原文；拒答')
  supp.append(f"<tr><td>{E(label)} / {mode}</td><td>{len(data.get('chunks',[]))}</td><td>{E(outcome)}<details><summary>实际补充回答</summary><pre class='answer'>{E(a)}</pre></details></td></tr>")

doclist=load('data/manifest.json')['records']
data_rows=''.join(f"<tr><td><a href='https://patents.google.com/patent/{E(x['publication_number'])}/en'>{E(x['publication_number'])}</a></td><td>{E(x['title'])}</td><td>{x['claim_count']}</td></tr>" for x in doclist)

body=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LightRAG 专利证据溯源：第二轮实际实验报告</title><style>{style}</style></head><body><main>
<p class="meta">第二轮 · 起点 2026-10-29 14:13:44 UTC · 报告生成 {now.strftime('%H:%M:%S')} UTC · 截至报告用时 {minutes:.1f} 分钟 · 硬停止 16:13:44 UTC</p>
<h1>LightRAG 专利证据溯源<br>第二轮实际实验报告</h1>
<div class="notice"><b>官方 v1.5.7 已实际完成 20 篇专利索引和真实问答。</b><br>基线 10 题 × naive/mix 共 20 条回答，两模式各完成 9/10 项核心任务；Q06 因证据未进入上下文而未完成比较。另保留一项自然跨块补充题及检索预算敏感性检查。发现可核验的来源呈现/归属问题与一次配置导致的抽取截断，<b>没有证明跨 Chunk 导致关系丢失</b>，也不据此宣称某模式普遍更优。</div>
<div class="stats"><div class="stat"><b>20 / 48</b>专利 / 实际块</div><div class="stat"><b>612 / 994</b>图节点 / 图边</div><div class="stat"><b>20 + 2 + 4</b>基线 / 补充 / 敏感性回答</div><div class="stat"><b>¥1.56–1.77</b>估算新增费用，非账单</div></div>

<h2>A. 实验完成情况、配置与成本</h2>
<p>本轮复用第一轮全部数据和已取得的官方源码，没有重新下载专利或部署新模型。先分别调用 Completion 和 Embedding：实际返回 OK 与有效 1×1024 向量；随后 2 篇冒烟索引达到 processed，得到 71 节点/90 边，并完成 naive/mix 真实问答。官方查询门槛最晚于 <b>{gate['passed_utc'][11:19]} UTC</b> 满足，早于 15:13:44。20 篇基线运行从 {full['started_utc'][11:19]} 至 {full['finished_utc'][11:19]} UTC；所有 API 调用区间为 {first_api[11:19]}–{last_api[11:19]} UTC。</p>
<p>第一轮于 13:45:45 UTC 因没有模型服务提前停止；其原始记录和本地报告完整保留，本轮不覆盖原证据。本轮从用户指定安全配置文件临时读取服务设置，密钥未写入报告、代码、日志或持久环境。全程未访问 AutoDL，未触碰 FOT、既有进程、权重、SSH 隧道或代理。</p>
<table><tr><th>项目</th><th>实际设置 / 完成证据</th></tr>
<tr><td>官方版本</td><td>v1.5.7，API 0344；commit <code>28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c</code>。直接导入该固定源码；索引与基线阶段显式断言版本 1.5.7，补充阶段复用同一固定源码路径，官方源码未修改。已安装分发包元数据仍为第一轮 1.5.8，但运行导入路径明确指向 v1.5.7；不混称两个版本。</td></tr>
<tr><td>数据</td><td><a href="https://huggingface.co/datasets/lj408/Dis2Pat">Dis2Pat</a>，20 个去重英文公开号，信息检索/推荐/上下文排序/数据索引方向，438 条编号 Claims。完整标题、摘要、Claims 独立写入，file_paths 为公开号.txt。specification 仅原始保存；生成的 disclosure 未入索引。</td></tr>
<tr><td>数据核验范围</td><td>全部摘要与 Google Patents 匹配；19/20 Claims 全文在仅规范空白后匹配。US8509827B2 Claims 2/3 原始来源缺父 Claim 编号；US9218390B2 Claims 10/11 公式存在编码乱码。均未补写，主问题避开这些内容；后述截断案例位于不受该乱码影响的 Claim 2。</td></tr>
<tr><td>LLM / Embedding</td><td>SiliconFlow OpenAI-compatible 接口；<code>deepseek-ai/DeepSeek-V4.1-Flash</code>，<code>BAAI/bge-m3</code>，Embedding 为 1024 维，每项输入限制为 8192 tokens。记录请求和返回模型别名；供应商公告称别名指向 1017 版本，但没有独立验证服务内部构建。</td></tr>
<tr><td>实际分块与索引</td><td>固定 1200 tokens、overlap 100；tokenizer 为 o200k_base（gpt-4o-mini 仅 tokenizer 标识）。42,087 输入 tokens→48 个实际块；48/48 与原文区间精确一致。JSON KV、NanoVectorDB、NetworkX；20 processed、0 failed；612 节点、994 边，来源块 ID 无悬空引用。</td></tr>
<tr><td>抽取与生成</td><td>官方默认抽取提示；额外 gleaning=0（源码默认为 1，属于本次限制）。temperature=0，最大输出 3500 tokens，thinking=false；SDK 自动重试=0，全局调用并发=2。出现 1 次输出截断，未当作无损抽取。</td></tr>
<tr><td>基线查询</td><td>naive/mix 使用相同模型、问题、提示和总预算。top_k=12，chunk_top_k=8，实体/关系预算各 2000，总上下文 8000；rerank=false。采用官方 <code>aquery_llm</code> 保存同次回答和结构化证据，不把另一次检索冒充原回答上下文。</td></tr>
<tr><td>成本与停止保护</td><td>{cost['llm_calls']} 次 LLM、{cost['embedding_calls']} 次 Embedding；实际返回 LLM 输入 {cost['llm_prompt_tokens']:,}、输出 {cost['llm_completion_tokens']:,} tokens，缓存命中输入 {cost['prompt_cache_hit_tokens']:,}，reasoning=0；服务失败=0、缺 usage=0。人民币10元累计预算、独立硬截止、关闭自动重试；不存在不确定待结算请求。</td></tr></table>
<p>按 <a href="https://www.siliconflow.cn/pricing">官方峰时价格</a>，LLM 输入 ¥2/M、输出 ¥8/M、缓存命中 ¥0.04/M，bge-m3 免费。考虑返回缓存量的估算为 ¥{cost['cache_aware_price_estimate_cny']:.4f}；完全不计缓存优惠的保守估算为 ¥{cost['upper_price_estimate_cny']:.4f}。按 <a href="https://www.chinamoney.com.cn/chinese/">当日参考中间价 6.7147 CNY/USD</a>，约 ${cost['estimated_usd_cache_aware']:.2f}–${cost['estimated_usd_upper']:.2f}；不是实际结算账单。最初预估 ¥2–6，实际估算更低，低于 $5 上限。</p>

<h2>B. 逐问题对照</h2>
<p>审阅为 AI 辅助逐条原文检查，加上精确子串、Claim 归属、引用映射和中间结果核对；不是独立人工金标准。表内“核心正确”不表示每个额外句子或每个标点都逐字正确。点击各格可查看真实完整回答。E/R/C 分别是同次返回的实体、关系、原文块数量。</p>
<div class="tablewrap"><table><tr><th>ID / 类别</th><th>原问题</th><th>正确证据与期望</th><th>naive 实际结果</th><th>mix 实际结果</th><th>归因</th></tr>{''.join(table)}</table></div>
<p>按“完成所问核心任务”计，两模式均为 9/10；Q06 的部分事实正确，但完整比较未完成。Q01 mix 另有超范围的“集合中唯一”推断，虽然标为 inference，也没有对整个 20 篇集合的证据支持，且没有证明该断言实际为假。因此不能将 9/10 解读为整答完全有据。部分回答引文改动句末标点或显式使用省略号/[s]，技术含义未变，但不应报告为全数逐字一致。末尾 References 是官方提示格式，未强制逐句脚注，不能仅因缺少行内脚注判错。</p>

<h3>单独的检索预算敏感性检查</h3>
<p>为定位失败，保持原问题、模型、提示和索引不变，将 top_k/chunk_top_k 改为 40/20，实体/关系/总上下文预算改为 6000/8000/30000（源码默认量级；rerank 仍关闭）。多个参数同时变化，不是单因素消融，也不混入主对照成绩。前后索引哈希一致。</p>
<table><tr><th>问题 / 模式</th><th>返回块</th><th>结果</th></tr>{''.join(supp)}</table>
<p>同一 Embedding 模型的候选排名复查：Q06 的 US7991757B2 两块位于第 9、11，低于基线 top-8；补充 Q11 两块位于第 29、30，仍低于扩展 top-20。索引中两条向量记录完整存在，不能归为索引写入丢失。mix 可能额外通过图路径取得事实，因此向量名次不是对全部 mix 行为的唯一解释。</p>

<h2>C. 两个最有价值的实际案例</h2>
<h3>成功：具体 Claim 与原文块可以对应</h3>
<p><a href="https://patents.google.com/patent/US9514753B2/en">US9514753B2</a>，Q04 询问 locality-sensitive hash functions 位于哪一 Claim。真实证据为 <b>Claim 6</b>：<q>{E(q4e['quote'])}</q>。naive 与 mix 均指出 Claim 6；同次检索包含 <code>US9514753B2-chunk-000</code>，文件来源与公开号一致。</p>
<details><summary>mix 的真实完整回答</summary><pre class="answer">{E(q4answer)}</pre></details>
<p>这证明本次样本在原文块成功进入上下文时，可以完成正确的文档与 Claim 定位。它不证明系统为每项断言生成了可机器校验的 Claim-span 证据对象。</p>

<h3>失败：图事实已经取回，却产生错误来源排除</h3>
<p><a href="https://patents.google.com/patent/US7991757B2/en">US7991757B2</a> 的 Claim 1 定义注册外部推荐器的模块，Claim 27 明确从属于 Claim 1 并增加机器可读描述能力。必要原文：</p>
<blockquote><b>Claim 1:</b> “a registration module configured to provide functionality for registering an external recommender with a recommendations service”<br><b>Claim 27:</b> “The system of claim 1 … provide machine readable descriptions of the external recommender.”</blockquote>
<p>两条完整 Claim 位于不同实际块：000 与 001。技术能力均成功抽取和合并；扩展预算的 Q11 mix 同次返回 Registration Module 记录，<code>file_path={E(reg['file_path'])}</code>，<code>source_id={E(reg['source_id'])}</code>。但回答提示 API 392 保留描述、没有这些来源字段，目标公开号仅出现在用户问题而未出现在系统证据/引用列表。模型将这些注册能力称为 <b>“in a different patent family”</b>，并最终引用 [1] US10867122B1.txt。</p>
<p>该来源排除与已记录的来源相矛盾。这里不是在推断实际专利族谱系，也没有把技术关系缺失误判为抽取错误：<b>技术事实已抽取、已入图、已被图检索取回；错误发生在来源呈现/最终归属这一链条。</b>来源字段被省略是可观察到的条件，未经单独来源恢复消融，不能说它是生成错误的唯一原因。模型仍未取得原始 Claim 文本，Claim 级回答没有完成。</p>
<details><summary>完整失败回答</summary><pre class="answer">{E(q11mix['llm_response']['content'])}</pre></details>

<h3>另一个定位明确但受实验条件影响的遗漏</h3>
<p><a href="https://patents.google.com/patent/US9218390B2/en">US9218390B2 Claim 2</a> 完整位于一个块内。抽取调用 API 191 达到本实验 3500-token 输出上限，<code>finish_reason=length</code>，正在输出的 <code>Class-Based Language Model Features → GEO_TRI_FIRST</code> 关系行未写完。实际官方解析器重放拒绝该行，最终图也缺这条显式成员边；其他块没有恢复它。</p>
<p><b>GEO_TRI_FIRST 节点及其含义仍保留，原文也完整存在。</b>这是本次输出上限导致的特定抽取关系遗漏，不能称为整项事实完全消失、跨块丢失或已证明回答失败。未把其他未显式建边项目都算作同因果错误，未修改基线索引或提高上限重跑后覆盖原结果。</p>

<h2>D. 研究判断</h2>
<table><tr><th>问题</th><th>本轮证据支持的结论</th></tr>
<tr><td>当前官方版本能做专利文档级溯源吗？</td><td>可以，多个真实答案的文件引用正确对应公开号；但并不保证所有图来源都进入回答上下文。补充 Q11 显示，结构化返回保留来源而回答仍错误归属。因此要分别评价“来源数据存在”和“回答正确绑定来源”。</td></tr>
<tr><td>能可靠回溯具体 Claim 吗？</td><td>在所需原文块被检索到时，本轮多数题正确定位 Claim；目前没有自动 Claim-span 保证。格式化查询输出没有显式 Claim ID，内部 source-span 和外部核验不能等同为模型每项结论的证明。未取回原文时出现拒答，不能称普遍可靠。</td></tr>
<tr><td>复现了跨 Chunk 关系丢失吗？</td><td>没有证明。原 Q08/Q09 的依赖链实际同块；真正跨块的 US7991757B2 技术关系成功抽取并合并，保留两个来源 ID。Q11 失败发生在原文检索/上下文来源与归属层；显式 Claim 从属关系未被图化，也没有同文不同边界的因果实验支持归因给分块。</td></tr>
<tr><td>是代码缺陷、设计限制还是本次条件？</td><td>Q06 对较低 top-k/上下文预算敏感，扩展后恢复；截断遗漏由本次 3500 输出限制引发；Claim 结构和图来源呈现粒度属于当前系统表示/接口设计范围；错误来源判断还涉及生成行为。没有确认普适软件缺陷，也没有复现论文基准。</td></tr>
<tr><td>值得 PhD 深入探索的方向？</td><td>把 Claim、从属约束和原文区间作为明确证据对象；使实体/关系摘要在上下文构建中保留来源身份；结合公开号约束与语义/图检索；逐阶段衡量事实与出处的保留；在证据缺失时区分安全拒答与错误归属。增量一致性本轮未测试，仍是后续问题。</td></tr></table>
<p>当前核心 <code>aquery_llm</code> 已真实使用，输出含 entities/relationships/chunks/references。<code>include_references</code> 在核心 QueryParam 默认 false，本轮显式 true；<code>include_chunk_content</code> 是 REST 参数，核心结果直接保留 chunks 内容；<code>/query/data</code> 对应 aquery_data，无最终答案生成但仍可调用关键词/Embedding。HTTP 路由本轮仅源码核对，没有部署 HTTP 服务，不冒称 REST 测试。</p>
<p>版本界限：论文 <a href="https://arxiv.org/pdf/2410.05779v3">v3（2025-04-28）</a> Figure 1 已示原始块 ID，当前 README 将 citations 功能记于 2025-03；不能声称论文时期完全没有引用机制。这里测试的是 2026 年 <a href="https://github.com/HKUDS/LightRAG/releases/tag/v1.5.7">正式发布 v1.5.7</a>、指定商业服务和本轮配置，不将新代码行为倒推成论文原始方法结论。</p>

<h2>E. 研究兴趣段落（已删去）（{words} words）</h2>
<blockquote lang="en">{E(paragraph)}</blockquote>
<p>这段依据实际成功和失败现象提出研究问题，没有声称 LightRAG 普遍失效，也没有虚构已有研究贡献。</p>

<h2>复现与证据</h2>
<p>主记录：<code>round2/results/full_Q*_naive.json</code>、<code>full_Q*_mix.json</code>；补充结果：<code>supplement_budget_*.json</code>。每份保留原问题、真实答案、同次实体/关系/块/引用、调用编号与时间。索引、图、原始抽取缓存、LLM 的无密钥请求和完整生成响应，以及 Embedding 的输入/返回元数据和已持久化索引向量均保留；输出截断响应没有被官方正常缓存，因此 API 191 原始记录尤其重要。</p>
<p>审阅与定位：<code>full_audit_q01_q05.json</code>、<code>full_audit_q06_q11.json</code>、<code>supplement_budget_audit.json</code>、<code>retrieval_rank_probe.json</code>、<code>full_provenance_trace.json</code>、<code>extraction_truncation_parser_replay.json</code>、<code>actual_chunk_source_mapping.json</code>。成本账本在 <code>cost_ledger.json</code>。角色脚本、依赖版本和原始选择清单随小型证据包提供。</p>
<p class="small">方法限制：20 篇目的性样本；单次模型输出，temperature=0 也不保证完全确定性；没有独立人工双盲标注；基线预算低于源码默认值；额外 gleaning=0、rerank 关闭；敏感性检查同时改变多个预算参数；未测试增量插入。所有模式的成功、未完成和来源错误都保留，不按偏好挑选赢家。</p>
<details><summary>20 篇专利清单</summary><table><tr><th>Publication</th><th>Title</th><th>Claims</th></tr>{data_rows}</table></details>
<p class="meta">报告生成 {now.isoformat()}。第一轮无模型服务的记录保留；第二轮实测结果单独归档。</p>
</main></body></html>'''
path=R/'report/LightRAG_patent_provenance_report_zh.html';path.write_text(body)
summary={'generated_utc':now.isoformat(),'elapsed_minutes_to_report':round(minutes,2),'main_questions':10,'main_answers':20,
 'core_completed_naive':9,'core_completed_mix':9,'supplement_natural_answers':2,'budget_sensitivity_answers':4,
 'actual_api_first_utc':first_api,'actual_api_last_utc':last_api,'english_words':words,'cost':cost,
 'official_query_succeeded':True,'cross_chunk_causal_loss_established':False,'review':'AI-assisted, not independent human gold standard'}
(R/'results/report_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps({'report':str(path),'bytes':path.stat().st_size,'english_words':words,'minutes':round(minutes,2)},ensure_ascii=False))
