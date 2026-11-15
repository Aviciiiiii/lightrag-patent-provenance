"""Build a transparent partial-result report; no model calls or synthetic answers."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import html
import json
import re

ROOT = legacy_root()
load = lambda p: json.loads((ROOT / p).read_text())
esc = html.escape
questions = load('results/questions.json')['questions']
chunks = load('results/chunk_probe.json')
mapping = load('results/question_chunk_mapping.json')
natural = load('results/natural_cross_chunk_candidates.json')
manifest = load('data/manifest.json')
start = datetime.fromisoformat('2026-10-29T13:08:42+00:00')
now = datetime.now(timezone.utc)
minutes = (now-start).total_seconds()/60
status = {
    'start_utc':start.isoformat(),'report_generated_utc':now.isoformat(),
    'elapsed_minutes_to_report':round(minutes,2),
    'disposition':'early_stop_missing_authorized_model_service',
    'data_milestone_passed':True,
    'official_stable_code_executed':'deterministic chunker only',
    'official_index_completed':False,'official_query_completed':False,
    'llm_model':None,'embedding_model':None,'model_calls':0,'cost_usd':0,
    'queries_prepared':10,'queries_executed':0,
    'naive_mix_comparison_completed':False,'incremental_test_completed':False,
    'autodl_used':False,'fot_touched':False,
    'blocker':{'action':'ainsert followed by aquery_llm for patent corpus',
               'target':'local official LightRAG v1.5.7',
               'reason':'No configured authorized LLM and embedding service found in this execution environment; common local service ports refused connections.',
               'state':'blocked; no query attempted; not an approval denial; no uncertain paid call'},
    'review':'AI-assisted source review, exact-string checks; not independent human adjudication',
}
(ROOT/'results/run_status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2))

paragraph = '[已删去：与实验无关的个人申请材料，见 reports/README.md]'
word_count=len(paragraph.split())
# word-count assert removed with the paragraph
(ROOT/'report/research_interest.txt').write_text(paragraph+'\n')

rows=[]
for q in questions:
    proof='; '.join(f"{e['publication_number']} Claim {e['claim_number']}" for e in q['evidence'])
    proof='; '.join(dict.fromkeys(proof.split('; ')))
    rows.append(f"<tr><td>{q['id']}<br><span class='muted'>{esc(q['category'][0])}</span></td><td>{esc(q['question_zh'])}</td><td><b>{esc(proof)}</b><br>{esc(q['expected_answer_zh'])}</td><td>naive：未运行<br>mix：未运行<br>无回答、引用或检索结果</td><td>未测，不能判错或归因</td></tr>")

details=[]
for q in questions:
    quotes=''.join(f"<p><b>{esc(e['publication_number'])} / Claim {e['claim_number']}</b><br><q>{esc(e['quote'])}</q> <a href='{esc(e['source_url'])}'>原始页面</a></p>" for e in q['evidence'])
    details.append(f"<details><summary>{q['id']} 原文证据</summary>{quotes}</details>")

source_rows=''.join(f"<tr><td>{esc(r['publication_number'])}</td><td>{esc(r['title'])}</td><td>{r['claim_count']}</td></tr>" for r in manifest['records'])
body=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>LightRAG 专利证据溯源：限时验证记录</title><style>
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.65;color:#172b3a;background:#f3f6f8;margin:0}}main{{max-width:1180px;margin:auto;padding:42px 28px 80px;background:white}}h1{{font-size:30px;line-height:1.3}}h2{{font-size:21px;margin-top:36px;border-top:1px solid #dce5eb;padding-top:22px}}h3{{font-size:17px}}a{{color:#005f91}}.meta,.muted{{color:#607080;font-size:13px}}.notice{{border-left:5px solid #b77216;background:#fff7e9;padding:16px 20px}}.stats{{display:flex;gap:14px;flex-wrap:wrap;margin:22px 0}}.stat{{background:#edf5f8;border-radius:7px;padding:14px 20px;min-width:145px}}.stat b{{display:block;font-size:24px}}table{{border-collapse:collapse;width:100%;font-size:13px;margin:16px 0}}th,td{{border:1px solid #dbe3e8;padding:10px;vertical-align:top;text-align:left}}th{{background:#edf2f6}}.tablewrap{{overflow-x:auto}}code{{overflow-wrap:anywhere;background:#f0f3f5;padding:2px 4px}}blockquote{{border-left:3px solid #90b8c9;padding:6px 18px;margin:12px 0;background:#f5f9fb}}details{{border-top:1px solid #e3e9ec;padding:12px 0}}summary{{cursor:pointer;font-weight:600}}.small{{font-size:13px}}@media print{{body,main{{background:white}}main{{padding:0}}h2{{break-after:avoid}}tr{{break-inside:avoid}}details{{display:block}}.tablewrap{{overflow:visible}}}}
</style></head><body><main>
<p class="meta">实验开始：2026-10-29 13:08:42 UTC · 报告生成：{now.strftime('%H:%M:%S')} UTC · 已用 {minutes:.1f} 分钟</p>
<h1>LightRAG 专利证据溯源<br>限时验证记录与未完成说明</h1>
<div class="notice"><b>核心结果：未完成官方 LightRAG 的真实索引与问答，不能声称实验跑通。</b><br>
已取得并核验真实数据、固定官方发布版，并实际运行其确定性分块器。当前执行环境未发现已配置且可用的获授权 LLM/Embedding 服务；已询问现有服务位置，未取得配置。按“环境问题不持续耗时”的约束提前结束模型阶段，不等待或突破 60/120 分钟上限。没有用本助手的回答代替模型调用，没有使用 mock 模型，也没有开通收费服务。</div>
<div class="stats"><div class="stat"><b>20</b>真实英文专利</div><div class="stat"><b>438</b>编号 Claims</div><div class="stat"><b>48</b>实际官方分块</div><div class="stat"><b>0 / $0</b>模型调用 / 新增费用</div></div>

<h2>A. 实际完成情况</h2>
<p>在本 Mac 的独立目录执行；未访问 AutoDL，未修改 FOT、已有进程、模型权重、隧道或代理。数据于 13:14:56 UTC 前满足规模和字段要求，早于 13:38:42 数据门槛。官方查询门槛为 14:08:42、总截止为 15:08:42；本次因模型服务缺失提前停止，不是等到截止后继续尝试。</p>
<p>数据来源为 <a href="https://huggingface.co/datasets/lj408/Dis2Pat">Dis2Pat</a>，仅通过 Dataset Viewer 下载 train 前 100 行（约 6.75 MB），按公开号去重后目的性选取信息检索、推荐、上下文排序、数据索引方向 20 篇。数据集记录 revision 为 <code>eda4a497291e9e8b898639881c34f158524732fc</code>；原始 API 响应及 SHA256 已保留。抽样不是随机样本，不能推断总体错误率。</p>
<p>每篇输入包含完整原始公开号、标题、摘要和 Claims；文件名为公开号。specification 保存在原始文件中，本次未加入分块输入；生成的 disclosure 完全排除。20 篇均无 Viewer 截断，摘要全部与 Google Patents 完整匹配；19/20 篇 Claims 在仅规范空白后完整匹配。异常：US8509827B2 Claims 2/3 的父 Claim 号码在来源页面本就缺失；US9218390B2 Claims 10/11 的公式有编码乱码。未改写原文，测试证据避开受影响内容。</p>
<table><tr><th>项目</th><th>实际状态 / 设置</th></tr>
<tr><td>官方代码</td><td>最新正式发布 v1.5.7，API 0344；commit <code>28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c</code>。分块从该源码目录直接导入；源码无修改。</td></tr>
<tr><td>版本隔离</td><td>先安装了官方 main 声明 1.5.8 的包及依赖，随后改用固定 v1.5.7 源码。发布包安装切换遇构建/超时问题而停止修复，installed distribution 元数据仍为 1.5.8；实际分块的导入路径和声明版本 1.5.7 已记录。不能把该环境称为完成了稳定版端到端部署。</td></tr>
<tr><td>实际分块</td><td>官方 chunking_by_token_size；size=1200、overlap=100；Tiktoken gpt-4o-mini/o200k_base 仅作为 tokenizer 标识，不代表调用过该 LLM。输入 42,087 tokens，48 块。开启 _emit_source_span 仅用于输出诊断坐标，逐块校验来源文本精确一致。</td></tr>
<tr><td>LLM / Embedding</td><td>均未配置、未调用。常见模型环境变量未设置；本机 11434、1234 端口拒绝连接。没有读取或展示任何 API Key。</td></tr>
<tr><td>查询与预算</td><td>实体抽取、图索引、naive/mix、生成、增量更新均未执行；检索上下文预算不适用。此前示例的 top_k/预算仅是未执行参考，绝非实际设置。实际成本 $0；未产生待结算调用。</td></tr></table>

<h2>B. 逐问题记录</h2>
<p>以下 10 题基于真实 Claims。20 段精确引文均通过原始文本子串及所属 Claim 校验；审阅为 <b>AI 辅助逐条原文审阅</b>，不是独立人工金标准。缺失回答不计为检索失败，未计算准确率、引用正确率或 naive/mix 差异。</p>
<div class="tablewrap"><table><tr><th>ID / 类别</th><th>问题</th><th>已核验正确证据</th><th>系统回答与引用</th><th>错误分类</th></tr>{''.join(rows)}</table></div>
<p>A=实体；B=Claim 证据；C=跨文档比较；D=自然跨块候选。实际分块后 Q08、Q09 的依赖链各自完整共处一块，因此这两题不能用于声称跨块缺失。另已找到下节所示的真实自然分离样本。</p>
{''.join(details)}

<h2>C. 两个最有价值的已观察案例</h2>
<p><b>没有可提交的 RAG 问答成功或失败案例。</b>以下是实际数据/分块观察，不是检索结果，也不是模型回答。</p>
<h3>案例 1：跨块假设被实际边界否定</h3>
<p><a href="https://patents.google.com/patent/US9514753B2/en">US9514753B2</a>：Claim 11→10→9→1 的完整依赖链全部处于同一实际 chunk 0（块编号从 0 开始）。Claim 1 涉及哈希表候选说话人；Claim 10 出现 <q>cosine distance</q>；Claim 11 要求 <q>smallest cosine distance</q> 与 <q>maximum distance threshold</q>。在本配置下，不能说这条关系因跨块而丢失。边界预检成功，抽取/检索/引用正确性仍未测。</p>
<h3>案例 2：真实依赖证据自然分散，但尚未证明信息丢失</h3>
<p><a href="https://patents.google.com/patent/US7991757B2/en">US7991757B2</a>：Claim 1 的完整文本位于 chunk 0，文档字符区间 [494,2433)；Claim 27 的完整文本位于 chunk 1，区间 [10570,10823)。Claim 1 定义外部推荐器注册模块；Claim 27 明确依赖 Claim 1，并增加 <q>machine readable descriptions of the external recommender</q> 的限定。没有任何一个块包含两条完整 Claim，且没有人为调整分块边界。</p>
<p>Claim 27 自身重复了实体名称和部分关系，因此仅凭完整 Claims 不同块，仍不能证明抽取失败。需要实际核查抽取输出、图节点/边、检索上下文和回答才能归因。结构筛查共识别 364 个明确单父引用，其中 54 对完整 Claim 文本不共处一块；这是启发式候选数量，<b>不是 54 个关系丢失，更不是错误率</b>。</p>
<p>本次可明确定位的问题属于输入数据：父 Claim 号码缺失与公式编码乱码。未证实 LightRAG 的 Extraction、Indexing、Retrieval、Generation 或 Citation 缺陷。</p>

<h2>D. 研究判断与版本边界</h2>
<table><tr><th>研究问题</th><th>本次可以支持的判断</th></tr>
<tr><td>文档级溯源？</td><td>当前正式版源码提供 file_paths→reference_id 的文档映射；naive 为文本块检索，mix 结合实体、关系和文本块。尚无运行证据可判断回答引用的实际正确率。</td></tr>
<tr><td>可靠的 Claim 级溯源？</td><td>尚未验证。当前格式化查询结果含 chunk_id/content/file_path/reference_id，没有显式 Claim ID 或字符偏移；内部 chunker/pipeline 已有 source-span 支持，不能说系统完全没有 span provenance。文档引用存在也不等于回答被某条 Claim 蕴涵。</td></tr>
<tr><td>复现跨块关系丢失？</td><td>没有。已复现自然的 Claim 证据分离，并否定两项最初的跨块候选；没有抽取/图/检索/生成中间结果，无法归因任何关系丢失。</td></tr>
<tr><td>缺陷还是实验限制？</td><td>已确认的是数据质量问题、返回 schema 的粒度和本次模型服务缺失；没有证实当前代码缺陷。未执行增量插入，不能判断合并一致性。</td></tr>
<tr><td>值得继续的问题？</td><td>Claim 依赖感知的证据组织；让实体/关系/回答保留可核验原文区间；分阶段测量事实保留率；跨文档比较中显式区分事实与推断；增量实体合并后的来源一致性。它们是待验证研究方向，不是本次已证明的缺陷。</td></tr></table>
<p>接口核对：<code>aquery_llm</code> 可在同一次调用保存回答与 entities/relationships/chunks/references；<code>/query/data</code> 调用 <code>aquery_data</code>，无答案生成但仍可能需要关键词模型和 embedding。核心 <code>QueryParam.include_references</code> 默认 false，REST 默认 true；<code>include_chunk_content</code> 是 REST 参数，不可误传给 QueryParam。</p>
<p>论文 <a href="https://arxiv.org/pdf/2410.05779v3">v3</a> 日期为 2025-04-28，Figure 1 已展示原始 chunk IDs；当前 README 将 citations 记录在 2025-03。不能声称论文时代完全没有引用功能。本次采用 2026 年正式发布代码，不是复现论文时期固定 artifact，也不把当前行为倒推给论文。</p>
<p class="small">源码依据：<a href="https://github.com/HKUDS/LightRAG/blob/28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c/lightrag/utils.py#L6936">格式化 chunks 与文档引用</a>；<a href="https://github.com/HKUDS/LightRAG/blob/28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c/lightrag/api/routers/query_routes.py#L144">REST 参数</a>；<a href="https://github.com/HKUDS/LightRAG/blob/28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c/lightrag/chunker/token_size.py#L133">官方分块器</a>；<a href="https://github.com/HKUDS/LightRAG/releases/tag/v1.5.7">正式发布记录</a>。逐项行号、源码摘录和哈希见 evidence/official_stable_audit.json。</p>

<h2>E. 研究兴趣段落（已删去）（{word_count} words）</h2>
<blockquote lang="en">{esc(paragraph)}</blockquote>
<p>该段只说“准备评估”，没有暗示已经跑通问答或发现 LightRAG 缺陷。若以后取得真实索引/查询结果，应依据结果再改写。</p>

<h2>复核与文件清单</h2>
<p>打开 evidence/question_ground_truth.txt 可逐题核对原文；results/questions.json 中 naive/mix 均为 null；results/chunk_probe.json 保留全部实际块；results/question_chunk_mapping.json 和 natural_cross_chunk_candidates.json 记录边界映射；data/manifest.json、source_verification.json 与 data_quality_flags.json 记录抽样和源页比对。</p>
<p>源码归档为 evidence/official_LightRAG_v1.5.7_source.tar.gz，依赖清单为 evidence/requirements_installed.json。脚本 scripts/data_*.py 可复现数据过程；scripts/chunk_probe.py 直接导入固定正式版源码、30 秒运行上限；scripts/build_questions.py 与 map_question_chunks.py 可复核证据。所有模型过程均未运行，没有后台模型/训练任务。没有遗留待支付或结果不确定的 API 请求。</p>
<details><summary>20 篇抽样清单</summary><table><tr><th>Publication</th><th>Title</th><th>Claims</th></tr>{source_rows}</table></details>
<p class="meta">本报告为提前停止的探索性验证记录。它保留可复查证据，同时明确未完成部分。</p>
</main></body></html>'''
(ROOT/'report/LightRAG_patent_provenance_report_zh.html').write_text(body)
(ROOT/'report/research_interest_metadata.json').write_text(json.dumps({'word_count':word_count,'text':paragraph},indent=2))
print(json.dumps({'report':str(ROOT/'report/LightRAG_patent_provenance_report_zh.html'),'elapsed_minutes':round(minutes,2),'interest_words':word_count},ensure_ascii=False))
