"""Build a self-contained Chinese control report from saved actual outputs."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
import json, html, re, datetime, hashlib
from pathlib import Path
ROOT=legacy_root('round3');R=ROOT/'round3'
def load(p):return json.loads((R/p).read_text())
def e(x):return html.escape(str(x))
cost=load('evidence/cost_summary.json'); ab=load('evidence/ablation_evaluation.json'); ch=load('evidence/chunk_conditions.json')
assert (R/'results/chunk_parsed.json').exists(), 'Official parser must finish before report generation'
validation=load('evidence/parser_validation_api191.json')
assert validation['all_saved_comparisons_passed']
chunk_eval=load('evidence/chunk_evaluation.json')
assert sum(row['primary_semantic_relation_retained'] for row in chunk_eval['rows'] if row['condition']=='SAME')==3
assert sum(row['primary_semantic_relation_retained'] for row in chunk_eval['rows'] if row['condition']=='CROSS')==0
now=datetime.datetime.now(datetime.timezone.utc);start=datetime.datetime(2026,10,29,16,1,14,tzinfo=datetime.timezone.utc)
english='[已删去：与实验无关的个人申请材料，见 reports/README.md]'
# word-count assert removed with the paragraph
css='''body{margin:0;background:#f3f5f8;color:#172638;font:16px/1.7 system-ui,-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}main{max-width:1120px;margin:auto;padding:38px 26px 70px}h1{font-size:32px;line-height:1.35}h2{margin-top:34px;border-bottom:2px solid #dbe4ee;padding-bottom:8px}h3{margin-top:24px}p{margin:12px 0}a{color:#155b9a}table{border-collapse:collapse;width:100%;font-size:14px;background:white;margin:16px 0}th,td{border:1px solid #d5dee8;padding:10px;text-align:left;vertical-align:top}th{background:#eaf0f6}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f7fa;padding:16px;border:1px solid #d8e0e8;font:13px/1.6 ui-monospace,monospace}code{overflow-wrap:anywhere}.box{background:white;border-left:5px solid #1b6f99;padding:14px 20px;margin:18px 0}.note{color:#536474;font-size:14px}details{background:white;border:1px solid #dce3eb;padding:12px 16px;margin:12px 0}summary{cursor:pointer;font-weight:650}.previous{padding-top:15px}.bad{color:#8a3528}.good{color:#14634b}@media print{body{background:white}main{max-width:none;padding:0}details{break-inside:avoid}h2{break-after:avoid}table{font-size:12px}}'''
parts=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LightRAG专利证据溯源：第三轮控制实验</title><style>'+css+'</style><main>']
parts += [f'<p class="note">第三轮 · 2026-10-29 · 生成于 {e(now.isoformat())} · 距本轮起点 {(now-start).total_seconds()/60:.2f} 分钟</p><h1>LightRAG专利证据溯源<br>来源字段消融与分块边界对照</h1>',
'<div class="box"><b>结果：</b>来源字段让模型识别到正确专利，但不足以恢复Claim编号；加入Claim原文后核心问题答对，引用编号仍出错。人工分块对照中，完整技术关系在同块条件3/3保留、跨块条件0/3保留，局部事实仍存在。原Q11的明确“另一专利”错误没有在A的3次重放中复现。</div>',
'<p>本轮只复用已保存的Q11上下文和同一专利原文，未重新检索、未重建20篇索引。结果适用于本模型、本提示和这些控制条件，不能推断自然语料中的错误率，也不能归因于2025年论文原始实现。</p>',
'<h2>1. 运行与成本</h2>',
'<table><tr><th>项目</th><th>实际设置</th></tr><tr><td>代码</td><td>官方v1.5.7，commit <code>28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c</code>。抽取提示从未修改的官方源码读取，并与第二轮真实请求逐字校验；响应选择性加载并执行官方未修改的 <code>_process_extraction_result</code> 及其全部相关辅助函数/常量；不是正常包导入，详见下文核验范围。</td></tr><tr><td>模型与请求</td><td>SiliconFlow / deepseek-ai/DeepSeek-V4.1-Flash；temperature=0；enable_thinking=false；stream=false；无重试；未提供seed（该端点公开schema未列出seed，不保证确定性）。本轮直接发送等价的OpenAI兼容HTTP JSON，避免无用SDK依赖的本机导入延迟。</td></tr><tr><td>实验规模</td><td>来源消融3条件×3次=9次；边界对照2条件×3次×2块=12次；总21次LLM、0次Embedding。</td></tr>',
f'<tr><td>用量</td><td>输入{cost["prompt_tokens"]:,} tokens；输出{cost["completion_tokens"]:,}；缓存输入{cost["cached_input_tokens"]:,}；reasoning tokens=0。0调用失败、0输出截断、0未知费用保留。</td></tr>',
f'<tr><td>新增费用估算</td><td>缓存计价约¥{cost["cache_aware_price_estimate_cny"]:.4f}；忽略缓存优惠的较高估算¥{cost["upper_price_estimate_cny"]:.4f}。这是按返回usage与公开价格的估计，不是供应商账单。此前预计¥1–2.5，内部硬上限¥10，低于用户$5上限。</td></tr>',
'<tr><td>时限与隔离</td><td>起点16:01:14 UTC，绝对停止18:01:14 UTC。所有付费调用已结束；实验产物写入独立round3。未访问AutoDL/FOT，未改变既有隧道、代理或项目。</td></tr></table>',
'<p class="note">按<a href="https://www.siliconflow.cn/pricing">官方价格</a>较高档：输入¥2/百万tokens、输出¥8/百万、缓存输入¥0.04/百万。配置只在运行内存使用；请求日志不含Authorization或密钥。</p>',
'<h2>2. 来源字段消融：固定Q11检索结果</h2>',
'<p>固定第二轮补充Q11 mix的API392请求：82个实体、82条关系、20个原文块、13项Reference List。A精确重放其system/user文本及生成参数。每条件3次，顺序ABC / BCA / CAB；输出上限均3500。</p>',
'<table><tr><th>条件</th><th>唯一新增内容</th><th>保留条件</th></tr><tr><td>A 原始</td><td>无；原始上下文</td><td rowspan="3">原实体、关系描述、顺序、原文块、用户问题、指令、引用列表均不变。不重新运行检索。</td></tr><tr><td>B 来源增强</td><td>为全部82条既有关系追加publication_numbers、file_path、source_id。</td></tr><tr><td>C 来源+原文</td><td>B基础上另加US7991757B2的完整Claim1、Claim27原文；这是额外证据诊断。</td></tr></table>',
'<p>每个source_id都逐一查回存储chunk、full_doc_id、file_path和原始文档字符区间。<code>&lt;SEP&gt;</code>连接的是聚合来源，不能推断每句话与某个Claim一一对应。B新增的是三个字段的组合，不能分离其中某个字段的贡献；增加字段也改变上下文长度。</p>',
'<p>关键既有关系：<code>External Recommender → Registration Module</code>；<code>file_path=US7991757B2.txt</code>；<code>source_id=US7991757B2-chunk-000&lt;SEP&gt;US7991757B2-chunk-001</code>。B未添加Claim文字或Claim编号证据。</p>',
'<table><tr><th>指标（每条件3次）</th><th>A</th><th>B</th><th>C</th></tr>']
metrics=[('正文肯定性错误来源归属/排除','positive_wrong_source_assignment_or_exclusion_in_prose'),('正确识别US7991757B2来源','correct_document_attribution'),('有证据支持的核心Claim任务完成','claim_task_core_complete_and_grounded'),('尾部References未提供目标专利证据','unsupported_reference_list_source_assignment'),('目标专利来源与引用编号同时满足','formal_reference_and_source_valid_together')]
for label,key in metrics:
 parts.append('<tr><td>'+e(label)+'</td>'+''.join(f'<td>{ab["counts_by_condition"][c][key]["true"]}/3</td>' for c in 'ABC')+'</tr>')
parts += ['<tr><td>引用编号与原映射冲突</td><td>0/3</td><td>0/3</td><td>3/3</td></tr></table>',
'<p><b>解释：</b>A三次均表示缺少可见来源映射而拒绝将图描述归给目标专利；B三次识别文档来源，但恰当拒绝猜测Claim1/27；C三次答对Claim区别与显式依赖。不能宣称B稳定修复了原API392“different patent family”的肯定性错误，因为该错误在A中没有复现。A/B都附上不支持目标注册能力的其他专利尾部References；由于没有逐句引用，不能把所有正文分别强行对应到其中某项。</p>',
'<p><b>引用限制：</b>为保持纯消融，三个条件的Reference List均不增补US799；原[1]仍是US10867122B1。C却三次输出<code>[1] US7991757B2.txt</code>，即来源文档正确、编号映射冲突。这部分失败受控制设计保留旧引用表的限制，不能表述为“正常新增文档的官方端到端引用必然出错”。正式系统需要同步维护证据来源和引用ID。</p>',
'<p><b>逐字引用：</b>C的核心Claim结论正确，不等于引号内全是逐字原文。三次均有标点规范化；C1把原文<code>being provided</code>写为<code>are provided</code>，并加入了明确标为推断但无原文直接支持的机制解释。报告因此分别计内容、逐字性与引用映射。</p>',
'<h3>9次逐次对照与实际回答</h3><table><tr><th>运行</th><th>公开号归属</th><th>Claim任务</th><th>引用判定</th><th>关键实际文本</th></tr>']
for row in ab['rows']:
 c=row['condition'];n=row['repeat'];s=row['scores'];cite='尾部列表未提供目标专利证据' if c in 'AB' else '[1]映射冲突；文档名正确'
 parts.append(f'<tr><td>{c}{n} / API{row["call_id"]}</td><td>{"正确" if s["correct_document_attribution"] else "来源不足，拒绝归属"}</td><td>{"核心完成" if s["claim_task_core_complete_and_grounded"] else "缺Claim原文，拒答"}</td><td>{cite}</td><td>{e(row["diagnostic_quote"])}</td></tr>')
parts.append('</table>')
for c in 'ABC':
 for n in range(1,4):
  row=load(f'results/ablation_{c}_r{n}.json');parts.append(f'<details><summary>{c}{n}：完整实际回答</summary><pre>{e(row["response"]["content"])}</pre></details>')
parts += ['<h2>3. 人工Chunk边界对照</h2>',
'<p>使用US7991757B2原始Claims字段中连续的Claims26–28，字符区间<code>[9973,10459)</code>，486字符、93个o200k_base tokens。不添加、重排或改写任何原文。两种条件均2块、无重叠、独立无状态抽取，提示与参数相同，输出上限均8192，gleaning=0。每条件3次；顺序SAME/CROSS、CROSS/SAME、SAME/CROSS。</p>',
'<table><tr><th>条件</th><th>边界</th><th>每块tokens</th><th>目标关系</th></tr><tr><td>SAME</td><td>Claim27与28之间，原Claims字符10329</td><td>64 + 29</td><td>Claim27整句保留在第一块</td></tr><tr><td>CROSS</td><td>Claim27内，原Claims字符10270；在“ machine readable descriptions”之前</td><td>55 + 38</td><td>第一块以“to provide”结束，第二块从宾语开始</td></tr></table>',
'<p>每组两次调用的API输入token总数为SAME3721、CROSS3722；原文token总数相同，提示包裹与边界处tokenization造成1-token差异。每块长度和语义完整性随分界变化，无法独立消除。</p>',
'<pre>'+e(ch['source_excerpt'])+'</pre>',
'<table><tr><th>配对重复</th><th>SAME完整关系</th><th>CROSS完整关系</th><th>直接Module–Descriptions边</th><th>输出截断</th></tr>'+''.join(f'<tr><td>{n}</td><td>保留</td><td>未保留</td><td>两条件均无；SAME以Module–Provider关系描述表达</td><td>无</td></tr>' for n in range(1,4))+'</table>',
'<p><b>判据：</b>主指标接受任何官方解析关系中忠实表达“registration module允许provider提供该recommender的machine readable descriptions”；不要求固定实体端点。直接Module–Descriptions边在两条件均0/3，若只做字符串端点匹配会把SAME的成功误判为失败。</p>',
'<p>SAME的实际关系描述包括：“The registration module is configured to allow a provider of an external recommender to provide machine readable descriptions.” CROSS的对应描述仅为：“The registration module is configured to allow a provider of an external recommender to provide something.” 原始响应已出现差异，官方解析器保留各自结果，因而本对照中的完整关系缺失发生在局部抽取阶段，而非解析、图索引或检索阶段。</p>',
'<p><b>边界：</b>CROSS仍保留模块、provider、external recommender及机器可读描述的部分节点/关系片段，不能称全部事实消失。未运行跨块联合重抽取、图合并恢复或最终问答，不能断言下游必然无法恢复。显式Claim27→Claim1法律依赖边两条件均未物化，默认本体也未要求Claim实体；这不是本对照的技术关系主指标。</p>',
'<p>这是93-token短片段上、零重叠、句内切分的人工压力测试。它与第二轮自然1200-token/100-overlap分块不同；第二轮原Claim1/27跨块时技术关系曾成功保留。本轮可支持“特定人工边界会使独立抽取遗漏完整关系”，不能给出自然分块频率或宣称论文原始方法缺陷。</p>',
'<h3>12次抽取原始输出</h3>']
for c in ['SAME','CROSS']:
 for n in range(1,4):
  for i in range(2):
   row=load(f'results/chunk_{c}_r{n}_c{i}.json');parts.append(f'<details><summary>{c} / 重复{n} / 块{i} / API{row["call_id"]} / {e(row["response"]["finish_reason"])}</summary><pre>{e(row["response"]["content"])}</pre></details>')
parts += ['<h2>4. 归因与下一步研究</h2>',
'<table><tr><th>观察</th><th>支持的归因</th><th>不能推出</th></tr><tr><td>B恢复文档来源</td><td>固定检索结果下，将已有关系来源传入回答上下文可改善本案例的文档归属。</td><td>不能分离三个字段各自贡献；不能宣称原肯定性错误已稳定修复。</td></tr><tr><td>C完成核心Claim问题</td><td>原始Claim证据补足了编号、依赖和原文表达。</td><td>不能把改善全归给来源字段；不能宣称逐字引用和引用ID可靠。</td></tr><tr><td>C引用[1]冲突</td><td>回答生成没有保持冻结引用表的映射；控制设计本身缺少新增文档的有效ID。</td><td>不能当成正常官方端到端新增证据的无条件失败率。</td></tr><tr><td>CROSS未保留完整技术关系</td><td>相同原文与调用数下，人工句内边界改变局部抽取的可见证据。</td><td>不能当成全部事实丢失、自然chunk失败率，或下游不可恢复。</td></tr></table>',
'<p>有价值的方向是：把聚合source_id进一步细化为可核验的Claim/字符区间支持；让图描述、原始证据和引用ID在检索与生成间同步；以跨块证据链恢复代替单纯实体名匹配；用严格区分文档归属、Claim定位、引文逐字性和引用映射的评估，识别错误真正发生的位置。</p>',
'<h2>5. 复现与核验范围</h2>',
'<p><b>解析执行限制：</b>正常导入官方operate模块时，本机无关的NumPy/PyYAML/NetworkX文件读取长时间停滞，已停止这些进程；没有修改依赖、官方源码或重新安装。替代路径直接编译执行原源码中未修改的AST函数、辅助函数和常量，记录源码区间与哈希，并使用同名标准logger。对第二轮正常官方解析的API191，已核对42/34节点/边组总数、保存的13个节点组和4个边组（5条记录）完全一致，以及被截断边同样缺失。第二轮未保存的其余记录无法逐项比较，因此不宣称对所有可能输入证明等价。</p>',
'<p>证据包保存A/B/C完整请求、逐字段diff、82条关系逐source_id核验、Claim字符区间、21次实际请求与完整供应商JSON响应、usage账本、两种分界与token区间、官方解析节点/边、评分脚本和报告。第二轮原始记录不覆盖，索引哈希前后核对。所有核验为AI辅助逐证据复核与程序断言，未声称独立人工标注或统计显著性。</p>',
'<p class="note">A/B/C判据于16:08:44写入condition_manifest，早于调用。合并evaluation_protocol文件于16:12:40写入，比9次调用结束晚3秒、早于主执行者阅读回答；不把这个后写文件伪装成预注册。分块目标用词在首次分块调用前纠正为原文的“external recommender”，未依据分块结果调整判据。温度0与缓存不等于独立随机重复。</p>',
f'<h2>6. 英文研究兴趣段落（{len(english.split())}词）</h2><div class="box">{e(english)}</div>',
'<p class="note">参考：<a href="https://huggingface.co/datasets/lj408/Dis2Pat">Dis2Pat</a>；<a href="https://patents.google.com/patent/US7991757B2/en">US7991757B2</a>；<a href="https://github.com/HKUDS/LightRAG/tree/28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c">本次官方源码</a>；<a href="https://arxiv.org/pdf/2410.05779v3">LightRAG论文v3</a>。本次结果属于所记录的当前代码和实验条件。</p>']
old=(ROOT/'round2/report/LightRAG_patent_provenance_report_zh.html').read_text();m=re.search(r'<body[^>]*>(.*)</body>',old,re.S)
if m:parts.append('<details><summary>第二轮完整报告（保留原结果与10题对照）</summary><section class="previous">'+m.group(1)+'</section></details>')
parts.append('</main></html>');out=R/'report/LightRAG_patent_provenance_report_zh.html';out.write_text('\n'.join(parts))
summary={'generated_utc':now.isoformat(),'report':str(out),'english_words':len(english.split()),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,'api_calls':21,'cost':cost}
(R/'results/report_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
