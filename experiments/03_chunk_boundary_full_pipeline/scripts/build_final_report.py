"""Build the evidence-grounded continuation report from saved runs; no service calls."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import json,html,datetime,hashlib,csv,io
ROOT=legacy_root('round4_full_20261030');R=ROOT/'round4_full_20261030'
def load(p,default=None):
 p=R/p
 return json.loads(p.read_text()) if p.exists() else default

def esc(x):return html.escape(str(x))
def pre(x):return '<pre>'+esc(x)+'</pre>'
def table(head,rows):return '<table><thead><tr>'+''.join('<th>'+esc(x)+'</th>' for x in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table>'
def yn(x):return '是' if x is True else ('否' if x is False else '待核验')
def frac(n,d):return f'{n}/{d}' if d else '未运行'
def runtime_query(gid,c,n,mode):
 name='natural_query.json' if mode=='mix' else 'natural_naive.json';x=load(f'results/{gid}_{c}_r{n}/{name}')
 if not x:return None
 q=x.get('result',x);d=q.get('data') or {};a=q.get('llm_response') or {}
 return {'status':q.get('status'),'generated':a.get('llm_generated'),'chunks':len(d.get('chunks',[])),'entities':len(d.get('entities',[])),'relations':len(d.get('relationships',[])),'answer':a.get('content',''),'refs':d.get('references',[])}

def score(gid,row):
 if not row:return {'raw':'待核验','merged':'待核验','retrieved':None,'answer':None,'forced':None,'note':'待核验'}
 if gid=='F01':
  raw=row.get('raw_relation_retention',{});m=row.get('merged_relation_retention',{});a=row.get('manual_answer_review',{})
  return {'raw':f"{sum(bool(x) for x in raw.values())}/3",'merged':f"{sum(bool(x) for x in m.values())}/3",'retrieved':row.get('natural',{}).get('both_original_target_quotes_retrieved'),'answer':a.get('natural_core_predicates_correct'),'forced':a.get('forced_core_predicates_correct'),'note':'截断单列' if not row.get('eligible') else ('关系记录缺病例/专家谓词；原文仍检索到' if not row.get('all_three_merged_predicates') else '谓词共存；不要求三个直接端点边')}
 if gid=='F05':
  ps=row.get('predicates',{});a=row.get('natural_answer',{})
  return {'raw':f"{sum(bool(p.get('raw_relation_present')) for p in ps.values())}/3",'merged':f"{sum(bool(p.get('merged_relation_present')) for p in ps.values())}/3",'retrieved':row.get('natural_retrieval',{}).get('both_target_claims_available'),'answer':all(a.get(k,False) for k in ['core_classifier_correct','second_data_memory_and_exclusivity_correct','first_vs_second_data_not_conflated','supporting_claim6_and10_correct','publication_and_reference_mapping_correct']),'forced':row.get('forced_diagnostic',{}).get('core_answer_and_claims_correct'),'note':'组件谓词+exclusively保留；实体名称路径另计'}
 if gid=='F04':
  z=row.get('summary',{})
  return {'raw':f"{int(bool(z.get('raw_P1')))+int(bool(z.get('raw_P2')))}/2" if z else '待核验','merged':f"{int(bool(z.get('merged_P1')))+int(bool(z.get('merged_P2')))}/2" if z else '待核验','retrieved':z.get('natural_evidence'),'answer':z.get('core_answer'),'forced':z.get('forced_core_answer'),'note':'额外alternative解释性warning，归因不唯一' if z.get('unsupported_extra_flag') else ('非目标格式行被解析器拒绝；目标保留' if row.get('run_id')=='F04_B_r2' else '成本使用与来源提供分开评价')}
 return {}

def naive_score(gid,row):
 n=(row or {}).get('naive',{})
 if not n:return {'core':None,'evidence':None,'note':'待核验'}
 if gid=='F01':return {'core':n.get('core_answer_correct'),'evidence':n.get('both_original_target_quotes_retrieved'),'note':'额外Claim依赖错误' if n.get('claim_dependency_extra_correct') is False else ('引号内无标记删词' if (row or {}).get('run_id')=='F01_B_r1' else '核心正确不保证逐字引用')}
 if gid=='F05':return {'core':n.get('core_answer_correct'),'evidence':n.get('retrieval',{}).get('both_target_claims_available'),'note':'引文需核对；核心技术与来源正确'}
 return {'core':n.get('core_answer_correct'),'evidence':n.get('natural_evidence'),'note':'核心技术正确；标点/空格有规范化'}

def main():
 now=datetime.datetime.now(datetime.timezone.utc);groups={g['id']:g for g in load('conditions/frozen_groups.json')['groups']};evaluations={g:load(f'evidence/{g}_evaluation.json',{}) for g in ['F01','F05','F04']}
 erows={g:{x['run_id']:x for x in e.get('runs',[])} for g,e in evaluations.items()};statuses=[];rows=[];detail=[];naive_count=mix_count=forced_count=0
 for gid in ['F01','F05','F04']:
  for n in [1,2,3]:
   for c in ['A','B']:
    rid=f'{gid}_{c}_r{n}';s=load(f'results/{rid}/status.json',{});statuses.append(s);qmix=runtime_query(gid,c,n,'mix');qnaive=runtime_query(gid,c,n,'naive');z=score(gid,erows[gid].get(rid));nz=naive_score(gid,erows[gid].get(rid));gr=s.get('graph_counts',{});tr=s.get('truncated_extraction_call_ids',[]);f=load(f'results/{rid}/forced_diagnostic.json')
    naive_count+=bool(qnaive and qnaive['status']=='success' and qnaive['generated']);mix_count+=bool(qmix and qmix['status']=='success' and qmix['generated']);forced_count+=bool(f)
    counts=lambda q:'未运行' if not q else f"{q['chunks']} / {q['status']}"
    rows.append([rid,s.get('status','未运行'),str(gr.get('nodes','—'))+'/'+str(gr.get('edges','—')),'是：'+','.join(map(str,tr)) if tr else ('否' if s.get('status')=='completed' else '—'),z['raw'],z['merged'],counts(qnaive),counts(qmix),yn(nz['evidence']),yn(z['retrieved']),yn(nz['core']),yn(z['answer']),yn(z['forced']),z['note']+'；naive：'+nz['note']])
    detail.append({'run_id':rid,'status':s,'score':z,'naive':qnaive,'mix':qmix,'forced':f})
 completed=sum(s.get('status')=='completed' for s in statuses);truncated=sum(bool(s.get('truncated_extraction_call_ids')) for s in statuses if s.get('status')=='completed');cleanpairs=sum(all(load(f'results/{gid}_{c}_r{n}/status.json',{}).get('boundary_causal_eligible') for c in ['A','B']) for gid in ['F01','F05','F04'] for n in [1,2,3])
 cost=load('evidence/cost_summary.json');ledger=load('results/cost_ledger.json',{});fullcost=cost.get('no_cache_cny') if cost else ledger.get('estimated_observed_cost_cny');fullcache=cost.get('cache_aware_cny') if cost else None;reserved=cost.get('unknown_reserved_cny') if cost else ledger.get('reserved_unknown_cny');all_success=bool(completed==18 and naive_count==18 and mix_count==18 and forced_count==18)
 english='[已删去：与实验无关的个人申请材料，见 reports/README.md]'
 # word-count assert removed with the paragraph
 css='body{font:16px/1.7 system-ui,-apple-system,sans-serif;max-width:1180px;margin:32px auto;padding:0 24px;color:#152238}h1,h2,h3{line-height:1.35}h2{margin-top:36px}table{border-collapse:collapse;width:100%;font-size:13px}th,td{border:1px solid #d6dce5;padding:8px;vertical-align:top;overflow-wrap:anywhere}th{background:#edf3f8;text-align:left}pre{background:#f3f5f7;padding:12px;white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}.note{padding:16px;background:#fff4da;border-left:5px solid #b87811}.good{padding:18px;background:#eaf5ee;border-left:5px solid #28734b}.wide{overflow:auto}code{overflow-wrap:anywhere}summary{cursor:pointer;font-weight:650}small{color:#536177}a{color:#1558a0}'
 out=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>第三轮 Chunk Boundary Ablation 完整管线补充报告</title><style>'+css+'</style>',
 '<h1>第三轮 Chunk Boundary Ablation 完整管线补充报告</h1>',
 f'<p><small>按用户命名；内部执行目录仍为round4/round4_full_20261030，避免更名破坏证据。报告生成：{esc(now.isoformat())}。原始限时窗口02:11:08—04:11:08 UTC，未因环境诊断或续跑重置。</small></p>',
 f'<div class="good"><b>实际新增：{completed}/18个独立索引；mix自然查询{mix_count}/18，naive自然查询{naive_count}/18，强制原文诊断{forced_count}/18。</b><br>3组完整原索引文档，各同块A/跨块B×3次。旧Claim1/27最小抽取控制保留，未重复；独立环境恢复smoke不计入这些消融成绩。</div>',
 '<p>36次自然回答的预先冻结技术核心均通过原文核对，但不能称所有回答完全正确：F01_B_r2的naive回答编造了Claim依赖链，多次回答的引号内文字也并非严格逐字。主要发现：F01出现边界敏感的<b>显式关系记录谓词遗漏</b>，最早可见于原始抽取，且原文检索与核心回答仍成功。F05、F04的目标组件谓词在已核验A/B结果中保留。不能把这解释为跨Chunk普遍造成知识丢失；F01只有一对无截断配对，其他组还存在块数与重复token量差异。</p>',
 '<h2>A. 完成范围、版本与可复现配置</h2>',
 table(['项目','实际配置或证据'],[
 ['实际运行','新增完整流程API：2026-10-30 03:27:30.983—03:46:29.242 UTC，约18分58秒；18索引及mix/forced于03:43:28完成，随后只追加naive。原限时窗口仍从02:11:08起，实际交付结束见完成记录。'],
 ['数据','复用原20篇英文Dis2Pat专利中的3篇完整原索引文档；各包含title、完整abstract、全部Claims，不含完整specification。没有重新下载数据库。'],
 ['官方代码','LightRAG v1.5.7；commit 28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c。保存归档SHA256 0872ab23fb2bde3cc83ad59bcca910f8117e936fc2b104c84ac8ab3dd8f2c9ee；官方源码未修改。'],
 ['执行环境','<TMP>/lightrag-envdiag-20261030/venv/bin/python；Python3.10.6；独立安装与源码完整性证据在环境诊断报告。临时目录可能被系统清理，固定依赖与重建命令已保存。'],
 ['LLM / Embedding','deepseek-ai/DeepSeek-V4.1-Flash / BAAI/bge-m3（1024维，8192 token上限）；同授权SiliconFlow服务；temperature=0、thinking=false、无应用重试。'],
 ['抽取','官方默认提示与解析器；gleaning=0；输出上限3500；默认最多40实体/100行。记录finish_reason及不完整tuple，截断运行从干净边界比较剔除/单列。'],
 ['Chunk','官方六参数custom chunking_func扩展，源码不改；o200k_base；真实重新tokenize后每块≤1200、相邻精确100-token overlap；完整内容顺序不变，字符/token区间与hash保存。'],
 ['检索','naive与mix；top_k=12、chunk_top_k=8；实体/关系预算各2000、总预算8000；rerank=false。每个索引只有目标专利，原文全部块通常可进入上下文。'],
 ['实际调用','117次LLM（45次chunk抽取、18次关键词、18次mix回答、18次forced、18次naive回答）及247次Embedding；364次均返回成功，抽取中2次length，其他无截断；无新未决请求。'],
 ['重复与隔离','A1/B1/B2/A2/A3/B3交错顺序；每个条件/重复全新workspace和索引，不复用抽取或回答缓存，也未复用embedding缓存；服务端输入prefix cache单独记录。无可验证seed或确定性承诺。'],
 ['核验','预先冻结原文判据；助手逐条核对原始/解析/图/检索记录和答案，无judge-model API，未经独立人类标注。指标不把节点描述、关系记录、实际端点拓扑混成一项。'],
 ['范围边界','当前v1.5.7行为，不是论文v3的原样复现；不能未经验证归因于2025年论文方法。原论文与当前代码功能可能不同。']]),
 '<p>首次续跑包装脚本遗漏父目录创建，在任何API调用前退出；失败日志与脚本快照保留，只修正包装脚本mkdir(parents=True)。这不是LightRAG抽取失败。原始最小实验、第二轮索引、环境诊断smoke均独立保存。</p>',
 '<h2>B. 真实边界与冻结技术判据</h2>',
 table(['组/专利','目标Claims与技术判据','A块token长度','B块token长度','边界以外差异'],[
 ['F01 / US9589231B2','Claim4：existing cases与experts基于MedicalOntology嵌入；Claim8：ontology基于UMLS。主指标是3个谓词出现在显式关系记录，允许一条记录描述合并两个谓词，不要求3条直接端点边。','1200、619','636、1183','两条件均2块、处理1819源tokens；长度分配/边界不同。'],
 ['F05 / US8069128B2','Claim10：multi-pass filter采用NaiveBayes；Claim6：filter生成second classification data，该数据exclusively存于nonpersistent memory；不能混同first-filter持久数据。','1200、545','886、239、720','B多1块、多100重复源tokens；语义组件与同一实体ID拓扑分开计。'],
 ['F04 / US8509827B2','Claims1/18/22：排名/选择采用货币成本；Claims14/25：context-data source/provider提供成本值。无需推断provider→ranking shortcut。','1200、226','712、315、456、143','B多2块、多200重复源tokens；Claim14已自含specified-parameter语义。'],
 ['保留的M01 / US7991757B2','Claim1+27原文剪裁控制，共362tokens。原完整文档双证据跨度1677tokens，不能伪装为1200内同块。','旧最小A：362','旧最小B：318、144','仅旧抽取层控制；本次按用户要求不重复。']]),
 '<p>保留的旧M01抽取层结果：R1注册功能A/B均3/3；R2机器可读描述关系A2/3、B3/3。A的一次结果把R2保留于实体描述而未输出关系。9次新抽取均无截断，另3次强制原文诊断核心正确；没有把这些选择性官方解析结果当作合并图或自然检索成绩，本次也未重复它们。</p>',
 '<p>三个完整组的实际内容/顺序、全部目标anchor可用性、无任一B块同时包含两类冻结证据、精确overlap与1200上限均已离线复核；运行后的persisted chunk/hash再次核对。语义同义或间接线索并未穷尽排除，因此这些是组件关系共同保留控制，不能假定目标必须依赖不可分的跨片段推理。</p>',
 '<p>冻结问题与必要原文证据如下；完整Claims和抽样来源保存在证据包。</p>']
 for gid in ['F01','F05','F04']:
  g=groups[gid];out+=['<details open><summary>'+esc(gid+' — '+g['publication_number'])+'</summary><p>'+esc(g['query'])+'</p>'+pre(g['diagnostic_text'])+'</details>']
 out+=['<h2>C. 三层指标与逐次结果</h2>',f'<p>目前{completed}个新完整运行中，{truncated}个有抽取截断；无截断成对比较为{cleanpairs}/9。以下“谓词保留”计关系记录的描述语义，不自动等于具有指定端点的直接边。自然检索成功不替代图谱保真，强制诊断不计入自然成绩。</p>']
 summaries=[]
 for gid in ['F01','F05','F04']:
  e=evaluations[gid];summ=e.get('summary',{});arr=[score(gid,v) for v in e.get('runs',[]) if v.get('status')=='completed'];n=len(arr)
  for c in ['A','B']:
   if gid=='F04':
    z=e.get('summary_by_condition',{}).get(c,{})
    n=z.get('runs',0)
    summaries.append([gid,c,n,frac(min(z.get('merged_P1',0),z.get('merged_P2',0)),n),frac(z.get('natural_evidence',0),n),frac(z.get('core_answer',0),n),frac(z.get('forced_core_answer',0),n),z.get('untruncated',0)])
    continue
   er=[v for v in e.get('runs',[]) if v.get('condition')==c and v.get('status')=='completed'];sc=[score(gid,v) for v in er];n=len(er);target='3/3' if gid!='F04' else '2/2'
   summaries.append([gid,c,n,frac(sum(x['merged']==target for x in sc),n),frac(sum(x['retrieved'] is True for x in sc),n),frac(sum(x['answer'] is True for x in sc),n),frac(sum(x['forced'] is True for x in sc),n),sum(load(f'results/{gid}_{c}_r{k}/status.json',{}).get('boundary_causal_eligible') is True for k in [1,2,3])])
 out += [table(['组','条件','核验完成','目标谓词均在合并关系记录','mix原文目标证据均返回','mix核心事实/Claims正确','强制诊断核心正确','无截断运行'],summaries),'<p>naive在同18个新索引上追加运行，未重建/重提取；每次均为实际新答案调用，查询前后3个核心索引文件hash一致。18/18都取回目标原文且技术核心正确；F01只有5/6 naive的全部附加结论受支持，B2另有明确Claim依赖错误。mix的18次技术核心与目标Claim定位也正确，但F04_A1有解释性warning。强制诊断18次技术核心正确，独立于自然成绩。</p>',
 '<p>naive的实际回答/证据另存natural_naive.json，核验记录在各组evaluation.json的naive字段。下表“技术核心”只含冻结目标命题，不能掩盖依赖错误或引文改写；引用标点、空格、词形变化与不加省略标记的删词另行记录。</p>',
 '<div class="wide">'+table(['运行','状态','节点/边','抽取截断','raw谓词','合并谓词','naive块数/状态','mix块数/状态','naive原文齐全','mix原文齐全','naive技术核心','mix技术核心','forced技术核心','备注'],rows)+'</div>',
 '<h2>D. 两个最有价值的案例</h2>',
 '<h3>成功：US8069128B2，Claim6与Claim10</h3>',
 '<p>Claim10原文：“wherein the multi-pass message filter employs a Naive Bayes classifier.” Claim6原文：“the second classification data is configured to reside exclusively in a non-persistent memory store”。A/B各3次无截断；分类器使用、数据生成、非持久内存及exclusively限定均进入原始关系记录与合并图，mix自然检索也返回Claim6/10并正确区分第一过滤器持久数据。</p>',
 '<p>例如F05_B_r1的实际关系与source_id可在merged_graph.json核验。A条件中NaiveBayes连接到“Multi-Pass Ad-Hoc Spam Message Filter”，而SecondClassificationData连接到“Multi-Pass Message Filter”；同时存在原文支持的ClassificationModel替代路径。报告将实际同一ID链与语义事实保留分开，没有仅凭命名差异判dedup缺陷，也没有人为添加别名边。</p>',
 '<h3>可定位遗漏：US9589231B2，F01_A_r3 / F01_B_r3</h3>',
 '<p>Claim4明确包含“the embedding of the existing medical cases and the set of experts being also based on the medical ontology”；Claim8明确“the medical ontology is based on the Unified Medical Language System”。两次均无截断，相同全文、相同2次chunk抽取、相同1819处理源tokens，只有边界与长度分配不同。</p>',
 '<p>A3原始关系输出包含以下两条记录，其中第一条的描述同时保存cases和experts两个谓词。<b>它不是三条直接端点边</b>：</p>',
 pre('relation<|#|>Diagnosis Assistance Method<|#|>Medical Ontology<|#|>embeds based on<|#|>The embedding of the new medical case, existing medical cases, and experts is based on a medical ontology.\nrelation<|#|>Medical Ontology<|#|>Unified Medical Language System<|#|>based on<|#|>The medical ontology is based on the Unified Medical Language System.'),
 '<p>B3原始关系输出没有明确existing-case或expert的ontology-basis谓词；UMLS谓词保留。解析与合并并未造成这些目标的额外损失，故最早可见阶段是<b>抽取的关系表示</b>。B实体描述还保留部分通用medical-case/expert语义，因此不能说全部知识消失。</p>',
 '<p>A1/A2也观察到谓词保留，但均触及3500输出上限；三次B均没有上述谓词且无截断。总体观察A3/3、B0/3必须连同截断信息展示；干净配对只有r3。尤其Claim4关系句在B首块内部完整存在，不能据此证明“一个必须联合两块才能理解的关系被切断”。更准确的是：在本组边界与上下文重组下，显式关系表示不稳定。</p>',
 '<p>所有F01的mix查询都找回两段原文并正确回答Claim4/8与UMLS，强制原文诊断也成功。因此“答案正确”与“图中谓词完整”在此分离；原文检索能够补偿图表示遗漏。证据路径：results/F01_A_r3及F01_B_r3中的parsed_extraction.json、merged_graph.json、chunks.json、natural_query.json，及对应logs/api_*请求响应。</p>',
 '<h3>另一个明确生成错误：F01_B_r2 naive的Claim依赖</h3>',
 '<p>naive回答把Claim4→Claim5→Claim6→Claim8写成“the stated sequence of dependencies”。实际Claim8开头是“The method of claim 4”，直接依赖Claim4；自然检索已返回完整原文。因此该额外依赖链错误可定位到生成阶段，不能归咎于原文缺失或检索遗漏。技术核心仍正确，所以仅看技术问答得分会漏掉这一错误。</p>',
 '<h3>单列异常：格式与解释忠实性</h3>',
 '<p>F01_A_r2的最后关系行因输出截断不完整；F04_B_r2有3条非目标relation缺少字段，原始20行只得到17条解析关系。这是实际schema拒绝，目标成本谓词仍保留，不能由此断言解析器算法错误。</p>',
 '<p>F04_A_r1自然回答额外把Claims12/13说成alternative parameters、成本只是one option。原Claims未明确作此可替代陈述；原始SpecifiedParameter实体摘要已出现“or”式概括，答案又进一步解释。将它标为解释性忠实性warning，确切传播因果无法唯一归因，不把它作为已证实的Chunk失败或法律结论。</p>',
 '<h2>E. 研究判断</h2>',
 table(['问题','本实验支持的判断'],[
 ['文档级溯源','当前v1.5.7能返回实际file_path和references；本小语料的正确公开号可回溯。不能据单目标文档索引推断多专利竞争检索可靠率。'],
 ['Claim级溯源','原始Claims保留编号且被检索时，核心Claim定位表现良好，但F01_B2 naive在证据齐全时仍生成错误依赖链；默认图没有保证显式Claim依赖结构，引用多为文档映射，逐字引文并非都严格匹配。需把claim-span证据和图断言关联单独验证。'],
 ['跨Chunk关系损失','观察到F01边界敏感的关系记录谓词遗漏；只有1对干净配对，且遗漏谓词本身未被切断。F05/F04未观察到目标组件谓词损失。不能声称跨Chunk普遍导致知识丢失。'],
 ['失败阶段','F01_B2 naive额外Claim依赖错误最早在生成阶段；F01目标遗漏最早在raw抽取关系输出，可排除目标的额外parser/merge丢失；原文检索仍成功。截断是本次输出预算条件。非目标schema拒绝、引文改写和解释性warning另列，无法唯一归因的不强指定阶段。'],
 ['代码缺陷还是设计限制','没有由本实验确认的LightRAG核心代码缺陷。结果更支持LLM抽取表示/上下文敏感、默认ontology不强制Claim结构、实体命名粒度和生成引用约束的研究议题；当前配置及小样本限制同时存在。'],
 ['值得深入的方向','Assertion-level provenance：每个技术谓词链接原Claim/字符span；抽取稳定性与不确定性；图表示与原文检索一致性；别名与实际图连通的可审计合并；用过程指标诊断答案正确但图不完整。']]),
 '<p>所有source_id都需结合run_id/workspace和chunk hash解释：不同独立索引可产生相同“专利号-chunk-000”，而其边界/内容不同。单独复制source_id会丢失实验作用域。没有把源ID字符串当作跨索引全局证据标识。</p>',
 '<h2>F. 费用、限时与保留状态</h2>']
 if fullcost is not None:
  out += [table(['费用项','CNY（估计，非账单）'],[['本次新完整流程，已返回usage',('缓存计价¥'+format(fullcache,'.8f')+'；' if fullcache is not None else '')+'无缓存优惠¥'+format(fullcost,'.6f')],['本次新流程未决预留','¥'+format(reserved or 0,'.6f')],['此前最小抽取控制','¥0.12982048—0.155912'],['环境诊断成功usage','¥0.02665392—0.030668'],['环境诊断失败请求未决预留','¥0.315518，不能称为已支出'],['本轮加诊断的已确认usage估计','¥'+format((fullcache or 0)+0.12982048+0.02665392,'.8f')+'—'+format(fullcost+0.155912+0.030668,'.6f')],['含前述预留的保守合计','¥'+format(fullcost+(reserved or 0)+0.502098,'.6f')],['续跑硬预算','新流程¥4，连同此前保守上限≤¥4.502098，低于原$5上限']])]
 else:out+=['<p>最终费用审计尚未写入；当前不填造金额。见results/cost_ledger.json。</p>']
 out+=['<p>费用按同日核验的SiliconFlow输入¥2/M、输出¥8/M、缓存输入¥0.04/M与免费bge-m3计算；请求和响应usage均保存。抽取/生成finish_reason、服务端输入缓存、重试数、预算预留均可核验。<a href="https://www.siliconflow.cn/pricing">官方价格页</a>。</p>',
 '<p>全部任务遵守原04:11:08 UTC硬截止；单组外部watchdog、03:53停止启动新重复、03:56计算截止为核验留时间。未重建原20篇索引，未改FOT、AutoDL、SSH、代理或模型。最终进程清理、旧索引hash与实际结束时间以根线程交付的审计/完成记录为准，报告生成时不预先声称未完成的检查。</p>',
 '<h2>G. 英文研究兴趣段落</h2>','<p>'+esc(english)+'</p>',f'<p><small>{len(english.split())} words；依据本次观察提出研究问题，不声称发现普遍缺陷。</small></p>',
 '<h2>H. 证据索引与历史</h2>',
 '<p>conditions/frozen_groups.json：原文、问题、预先冻结判据及边界；evidence/preflight_independent_review.json：完整性与边界复核；results/每run：实际chunk、raw解析、merged graph、自然naive/mix及forced；logs/api_*：真实请求/响应/usage；evidence/各组_evaluation.json：逐谓词支持记录、答案与归因；evidence/completed_runs_audit.json及cost_summary.json：运行后hash/费用核验。版本、参数和独立索引路径均已保存。</p>',
 '<p><a href="https://github.com/HKUDS/LightRAG/tree/28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c">固定官方源码</a>；<a href="https://arxiv.org/pdf/2410.05779v3">论文v3</a>；<a href="https://huggingface.co/datasets/lj408/Dis2Pat">Dis2Pat来源</a>。本报告中的功能与结果只归属于实际运行版本和本次条件。</p>']
 # Preserve earlier partial record exactly as a self-contained historical view.
 prior=(ROOT/'round4/report/LightRAG_patent_provenance_report_zh.html').read_text()
 out+=['<details><summary>展开此前部分完成报告（历史快照，当时完整管线尚未运行）</summary><p>本次新结果仅补充实际完成的完整文档指标；历史原始证据未覆盖。该快照包含此前轮次记录。</p><iframe sandbox title="此前部分报告" style="width:100%;height:800px;border:1px solid #ddd" srcdoc="'+html.escape(prior,quote=True)+'"></iframe></details></html>']
 p=R/'report/LightRAG_patent_provenance_report_zh.html';p.parent.mkdir(exist_ok=True);p.write_text('\n'.join(out))
 csvbuf=io.StringIO();w=csv.writer(csvbuf);w.writerow(['run_id','status','nodes_edges','truncation','raw_predicates','merged_predicates','naive_chunks_status','mix_chunks_status','naive_target_evidence','mix_target_evidence','naive_core_correct','mix_core_correct','forced_core_correct','note']);w.writerows(rows);(R/'report/paired_run_table.csv').write_text(csvbuf.getvalue())
 summary={'generated_utc':now.isoformat(),'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'completed_indexes':completed,'mix_queries':mix_count,'naive_queries':naive_count,'forced_diagnostics':forced_count,'expected_indexes':18,'all_runtime_components_completed':all_success,'truncated_runs':truncated,'clean_paired_comparisons':cleanpairs,'english_words':len(english.split()),'new_M01_runs':0,'historical_M01_not_repeated':True}
 (R/'results/report_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
