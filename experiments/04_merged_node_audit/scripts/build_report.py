"""Build a standalone Chinese report and machine-readable audit tables, offline."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
from collections import Counter
import csv, datetime, hashlib, html, json
O=legacy_root('round2_multisource_audit')/'round2_multisource_audit';ROOT=legacy_root('round2_multisource_audit');P=O/'report';P.mkdir(exist_ok=True)
load=lambda p:json.loads(p.read_text())
inv=load(O/'evidence/multisource_nodes_inventory.json');summary=load(O/'evidence/inventory_summary.json');validation=load(O/'evidence/review_validation.json');adj=load(O/'evidence/root_adjudications.json');quality=load(O/'evidence/review_quality_audit.json');source_audit=load(O/'source_mapping_audit.json')
assert validation['reviewed_nodes']==38 and not validation['pending_nodes'] and not validation['errors'] and not validation['original_inputs_changed']
labels={'shared_specific_concept':'较具体的共享技术概念','shared_broad_class':'合理共享的宽泛类别','contextual_conflation':'异义／文档局部角色并置','insufficient_evidence':'证据不足'}
short={'shared_specific_concept':'共享技术概念','shared_broad_class':'共享宽类','contextual_conflation':'异义／角色并置','insufficient_evidence':'证据不足'}
conf={'high':'高','medium':'中','low':'低'}
quote_checks={(x['audit_id'],x['publication_number']):x for x in validation['quote_checks']}
def rename_offsets(x):
 if isinstance(x,list):return [rename_offsets(v) for v in x]
 if isinstance(x,dict):return {('first_occurrence_in_full_doc_char_start' if k=='exact_full_doc_char_start' else k):rename_offsets(v) for k,v in x.items()}
 return x
records=[]
for item in inv:
 aid=item['audit_id'];r=load(O/'reviews'/f'{aid}.json');d=load(O/'dossiers'/f'{aid}.json');override=adj['category_overrides'].get(aid);final=override['final_category'] if override else r['category']
 sources=[]
 for s in r['source_assessments']:
  p=s['publication_number'];dsource=next(x for x in d['source_documents'] if x['publication_number']==p)
  keep={k:s.get(k) for k in ['publication_number','evidence_quote','claim_or_section','source_chunk_ids','role_zh','extraction_description_support','relevant_actual_edges']}
  keep['file_paths']=dsource['file_paths'];keep['all_node_source_chunks_for_publication']=dsource['source_chunks'];keep['verified_quote_locations']=quote_checks[(aid,p)]
  keep['raw_entity_records']=[{'chunk_id':c['chunk_id'],'raw_entity_rows':c['raw_entity_rows']} for c in dsource['sources']]
  sources.append(keep)
 record={**item,'initial_category':r['category'],'category':final,'category_zh':labels[final],'confidence':r['confidence'],'reason_zh':override['reason_zh'] if override else r['reason_zh'],'initial_reason_zh':r['reason_zh'],'class_instance_interpretation_zh':r['class_instance_interpretation_zh'],'source_assessments':sources,'actual_incident_edges':d['all_incident_edges'],'neighbor_audit':rename_offsets(r['neighbor_audit']) if aid in ['N024','N025','N026'] else r['neighbor_audit'],'limitations_zh':r['limitations_zh'],'adjudication':override,'ontology_sensitive':aid in adj['ontology_sensitive_contextual_nodes'],'review_file':f'reviews/{aid}.json','dossier_file':f'dossiers/{aid}.json'}
 if aid=='N030':
  record['neighbor_audit']=dict(record['neighbor_audit'])
  record['neighbor_audit']['initial_details_zh']=record['neighbor_audit'].get('details_zh','')
  record['neighbor_audit']['details_zh']='已逐条检查全部实际邻边及其source_id/file_path。除495/502/517这3条主语粒度警示外，其余关系按所属来源有支持；未确认跨专利不支持边。3条警示均来自US9514120B1-chunk-002：完整Claim18的server computing machine在原抽取及图中被概括为Apparatus，最早已出现在单专利抽取。共同节点仍可形成潜在无作用域路径，但没有本次查询或传播证据，不能把这些源内警示归因于跨专利节点合并。'
 records.append(record)
counts=Counter(r['category'] for r in records);initial=Counter(r['initial_category'] for r in records);byid={r['audit_id']:r for r in records}
result={'schema_version':1,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'audit_start_utc':'2026-10-30T07:58:00Z','deadline_utc':'2026-10-30T09:58:00Z','scope':'Read-only existing round2 baseline,20indexed title/abstract/claims documents,not specification; no new indexing/retrieval/generation.','official_version':'1.5.7','source_commit':'28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c','counts':{**summary,'category_counts':{k:counts[k] for k in labels},'initial_category_counts':dict(initial),'source_quotes_verified':98,'unique_incident_edges_reviewed':266,'incident_edge_visits':307,'confirmed_cross_publication_wrong_edge_propagation':0,'local_role_attribution_warnings':3},'method':'AI-assisted source review of every multi-publication node, plus targeted second AI review; not independent human gold. Category counts are not benchmark error rates.','adjudications':adj,'nodes':records,'original_inputs_changed':[],'external_model_api_calls':0,'embedding_api_calls':0,'new_api_cost_usd':0,'credentials_read':False}
(P/'round2_multisource_nodes.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
headers=['audit_id','node_id','entity_type','publication_count','publication_numbers','file_paths','source_chunk_ids','category','category_zh','initial_category','confidence','reason_zh','class_instance_interpretation_zh','source_evidence','incident_edge_count','actual_edge_indices','neighbor_audit_zh','ontology_sensitive','limitations_zh']
with (P/'round2_multisource_nodes.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=headers);w.writeheader()
 for r in records:
  compact_sources=[{k:s[k] for k in ['publication_number','claim_or_section','evidence_quote','source_chunk_ids','role_zh']} for s in r['source_assessments']]
  w.writerow({'audit_id':r['audit_id'],'node_id':r['node_id'],'entity_type':r['entity_type'],'publication_count':r['publication_count'],'publication_numbers':' | '.join(r['canonical_publications']),'file_paths':' | '.join(r['actual_chunk_file_paths']),'source_chunk_ids':' | '.join(r['all_source_chunks']),'category':r['category'],'category_zh':r['category_zh'],'initial_category':r['initial_category'],'confidence':r['confidence'],'reason_zh':r['reason_zh'],'class_instance_interpretation_zh':r['class_instance_interpretation_zh'],'source_evidence':json.dumps(compact_sources,ensure_ascii=False),'incident_edge_count':r['incident_edge_count'],'actual_edge_indices':' | '.join(str(e['edge_index']) for e in r['actual_incident_edges']),'neighbor_audit_zh':r['neighbor_audit'].get('details_zh',''),'ontology_sensitive':r['ontology_sensitive'],'limitations_zh':json.dumps(r['limitations_zh'],ensure_ascii=False) if not isinstance(r['limitations_zh'],str) else r['limitations_zh']})
with (P/'round2_multisource_sources.csv').open('w',encoding='utf-8-sig',newline='') as f:
 h=['audit_id','node_id','publication_number','file_paths','claim_or_section','exact_quote','source_chunk_ids','role_zh','extraction_description_support','verified_quote_locations'];w=csv.DictWriter(f,fieldnames=h);w.writeheader()
 for r in records:
  for s in r['source_assessments']:w.writerow({'audit_id':r['audit_id'],'node_id':r['node_id'],'publication_number':s['publication_number'],'file_paths':' | '.join(s['file_paths']),'claim_or_section':s['claim_or_section'],'exact_quote':s['evidence_quote'],'source_chunk_ids':' | '.join(s['source_chunk_ids']),'role_zh':s['role_zh'],'extraction_description_support':s['extraction_description_support'],'verified_quote_locations':json.dumps(s['verified_quote_locations'],ensure_ascii=False)})
E=lambda x:html.escape(str(x))
def quote(s):return f'<p class="source"><b>{E(s["publication_number"])} · {E(s["claim_or_section"])}</b><br><q>{E(s["evidence_quote"])}</q><br><span class="muted">{E(s["role_zh"])}<br>来源 Chunk：{E(", ".join(s["source_chunk_ids"]))}</span></p>'
category_rows=''.join(f'<tr><td>{E(labels[k])}</td><td>{counts[k]}</td><td>{counts[k]/38:.1%}</td></tr>' for k in labels)
table=''.join(f'<tr><td><a href="#node-{r["audit_id"]}">{r["audit_id"]}</a></td><td>{E(r["node_id"])}</td><td>{E(r["entity_type"])}</td><td>{r["publication_count"]}</td><td>{E(short[r["category"]])}</td><td>{conf[r["confidence"]]}</td></tr>' for r in records)
details=[]
for r in records:
 edges=''.join(f'<tr><td>{e["edge_index"]}</td><td>{E(e["source"])} — {E(e["target"])}</td><td>{E(e["description"])}</td><td>{E(", ".join(e["canonical_publications"]))}<br><code>{E(e["source_id"])}</code></td></tr>' for e in r['actual_incident_edges'])
 details.append(f'<details id="node-{r["audit_id"]}"><summary>{r["audit_id"]} · {E(r["node_id"])} · {E(short[r["category"]])} · {r["publication_count"]} 篇</summary><p><b>判定：</b>{E(r["reason_zh"])}</p><p><b>类与实例：</b>{E(r["class_instance_interpretation_zh"])}</p><p><b>原图类型：</b>{E(r["entity_type"])}；<b>置信度：</b>{conf[r["confidence"]]}；<b>文件：</b>{E(", ".join(r["actual_chunk_file_paths"]))}</p>'+''.join(quote(s) for s in r['source_assessments'])+f'<p><b>邻边审阅：</b>{E(r["neighbor_audit"].get("details_zh",""))}</p><p class="muted"><b>局限：</b>{E(r["limitations_zh"])}</p><details><summary>实际邻边端点、描述与来源（{r["incident_edge_count"]} 条）</summary><div class="scroll"><table><tr><th>边索引</th><th>真实端点（无向图）</th><th>保存描述</th><th>公开号与 source_id</th></tr>{edges}</table></div></details></details>')
token=byid['N017'];tokens=byid['N032'];processor=byid['N019']
token_quotes=''.join(quote(s) for s in token['source_assessments'])
tokens_quotes=''.join(quote(s) for s in tokens['source_assessments'])
processor_quotes=''.join(quote(s) for s in processor['source_assessments'][:2])
css='''body{max-width:1100px;margin:36px auto;padding:0 24px;font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif;color:#17252c;background:#fff}h1{font-size:30px;line-height:1.3}h2{margin-top:36px;font-size:23px}h3{font-size:19px}table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid #ced9dd;text-align:left;vertical-align:top;padding:9px}th{background:#eef4f5}code{font-size:12px;overflow-wrap:anywhere}.muted{color:#52646d;font-size:14px}.lead{font-size:18px}.box{padding:15px 20px;background:#eef6f4;border-left:4px solid #22806e}.warn{background:#fff7e8;border-left-color:#a57515}details{border:1px solid #d6e0e3;border-radius:6px;padding:12px;margin:14px 0}summary{font-weight:600;cursor:pointer}.source{border-left:3px solid #bdcfd3;padding-left:13px}q{font-family:Georgia,serif;color:#263d46}.scroll{overflow:auto}a{color:#1c6c91}footer{border-top:1px solid #ccd;margin-top:35px;padding-top:15px}@media print{body{max-width:none;font-size:11pt}details{break-inside:avoid}table{font-size:9pt}a{color:inherit}}'''
body=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LightRAG 第二轮跨专利节点审计</title><style>{css}</style><body>
<h1>LightRAG 第二轮：跨专利节点来源与语义审计</h1><p class="muted">2026-10-30 · 既有 v1.5.7 快照 · 只读审计 · 新增 API 成本 $0</p>
<p class="lead">612 个节点中，<b>38 个节点（6.21%）</b>来自两篇或以上专利。逐项审阅后，<b>32 个支持合理的类／概念共享</b>；另外 <b>6 个表现为异义或文档局部角色在同一 ID 中并置</b>。后者不是“6 个已证实错误合并”：其中 5 个对本体粒度和角色作用域的解释较敏感。</p>
<div class="box"><b>完成范围：</b>38/38 节点、98/98 个节点—专利来源、307 次逐节点邻边审阅（266 条不同实际边）。98 条代表性引文均核对到具体原文、Claim／摘要及实际来源 Chunk。原图、原索引和旧报告未改动；没有重建索引、运行新查询或调用 LLM／Embedding。</div>
<h2>统计与判定边界</h2><table><tr><th>最终类别</th><th>节点数</th><th>占38个多源节点</th></tr>{category_rows}</table>
<p>“共享宽类”包括 Processor、Memory、Server、System 等通用类别。不同专利内的具体实例不能互换，但可以共享同一个上位类；泛化名称本身不是错误。较具体的共享概念为查询语境中的 Tokens、Labels、Label。两类共 32 个，均未因名称通用而判错。</p>
<div class="box warn"><b>本体敏感性：</b>6 个并置节点为 First User、Second User、Third User、Event、Token、Network。Token 的“匿名替代值／查询词元”差异最清楚；其余5项保留合法宽类解释。若采用该解释，计数可变为共享技术概念3、共享宽类34、异义并置1。两种计数都不能作为代码缺陷率或实体解析准确率。</div>
<p>这是 AI 辅助逐项内容审阅，另对7个重点节点进行第二次 AI 审阅，<b>不是独立人工 gold</b>。高／中置信度是定性判断。初评把2种存储载体列为较具体概念；为与其他存储介质、Processor／Memory保持同一粒度，最终统一为共享宽类。初评与裁决均保留，这不改变合理共享总数或并置节点数。</p>
<h2>来源统计如何复现</h2><p>复用 <code>lj408/Dis2Pat</code> 数据集首100行中有目的选取的20篇信息检索、推荐、上下文排序等专利；不是随机代表性样本。本次未重新下载。实际快照为20篇专利、48个Chunk、612节点、994边。以节点 <code>source_id</code> 与完整 <code>entity_chunks.chunk_ids</code> 的并集为起点，按 <code>text_chunks.full_doc_id → full_docs 的 publication header</code> 归并公开号；同专利的多个Chunk和路径别名只计一次。随后交叉核对节点 <code>file_path</code>，不按分隔后的列表位置配对。</p>
<p><code>&lt;SEP&gt;</code> 是保存字段的分隔符。38节点中，28个来自2篇、6个来自3篇、3个来自5篇、1个来自9篇。节点最多14个Chunk；缺失映射、文档冲突、来源KV与图字段差异、路径对应差异均为0。48个实际Chunk都能在所属完整索引文本中逐字定位。本快照未出现来源列表截断；这不表示所有规模下都不会截断。</p>
<p>47条抽取响应由原缓存读取；US9218390B2-chunk-000曾因输出上限截断、未入缓存，使用保存的调用191请求与原始响应补齐审阅，并保留 <code>finish_reason=length</code> 限定。没有补调模型。98个节点—专利来源均找到该名字的原始实体抽取行。审计范围是当时实际索引的标题、完整摘要及Claims，不含未索引的完整说明书。</p>
<h2>三个代表案例</h2>
<h3>1. 真正共享：Tokens（N032，2篇）</h3><p>两篇专利都把查询分成词元并赋予标注：一个服务于跨语言查询模式，另一个服务于地理搜索查询解析。它们共享查询词元这一技术概念，不表示两个查询或算法实例相同。</p>{tokens_quotes}<p>实际边704为 <code>Tokens — Labels</code>，保留两篇来源；相应单数节点边251 <code>Token — Label</code> 也有两篇查询专利的支持。现图的单数与复数是不同ID；本任务不评价应合而未合的同义节点。</p>
<h3>2. 合理但宽泛：Processor（N019，9篇）</h3><p>9篇原文都提供处理器／执行指令的硬件角色，因此共享 Processor 类合理；各专利中的处理器实例及其职责不可据此对齐。其25条实际邻边按各自来源审阅，没有把跨文档邻接自动认作错误。</p>{processor_quotes}<p class="muted">其余7篇的原文、Claim、source_id和邻边详见N019展开项及逐来源CSV。</p>
<h3>3. 清楚的异义并置：Token（N017，3篇）</h3>{token_quotes}<p>同一 <code>Token</code> 节点合入匿名化替代值与NLP查询词元两种含义。实际边193为 <code>Second User — Token</code>（仅US9118735B1），边251为 <code>Token — Label</code>（仅US8655901B1、US9218390B2）。共享节点因此允许形成跨语义路径；两条边在各自来源中仍有支持。</p><p><b>没有新增或观察到一条“匿名用户必须具备查询标签”的直接边，也没有在本次运行查询证明错误答案传播。</b>这是一项可复核的词义区分／来源作用域风险，不能直接归为LightRAG代码bug。</p>
<h2>邻边检查：语义混并与错误传播分开</h2><p>266条相关实际边中，本次未确认由跨专利合并造成的不支持边或答案传播。实际跨专利来源的边只有4条：Weight—Characteristic、Token—Label、Processor—Memory、Tokens—Labels；来源子句需逐一解释，不能把任一合并描述都归给每一篇专利。</p>
<p><b>另有3条源内角色警示：</b>US9514120B1 Claim18明确由 <code>server computing machine</code> 执行combine、sort、update；chunk002从句中间开始，保存的原抽取及图边495、502、517则使用 <code>Apparatus</code> 作动作主体。这是已观察的角色粒度不一致，最早出现在单专利原始抽取中。整体装置功能概括的解释仍需限定；不能归因于跨专利合并，也没有本次边界控制或新问答来证明因果传播。Apparatus节点本身仍归共享宽类。</p>
<h2>逐节点总表</h2><p class="muted">完整38项，非抽样。点击编号或向下展开可查所有来源、短引文与真实边端点。类型为保存原图中的entity_type，不把它当人工本体金标准。</p><table><tr><th>编号</th><th>原节点 ID／label</th><th>原图类型</th><th>专利数</th><th>最终类别</th><th>置信度</th></tr>{table}</table>
<h2>完整证据展开</h2>{''.join(details)}
<h2>复现与局限</h2><p>证据包保留原始图快照、GraphML、来源KV、20篇索引文本与Claims、47条缓存抽取和调用191原始记录；同时提供逐节点／逐来源CSV、完整JSON、所有初审、裁决、核验结果及文件SHA256清单。统计脚本只用Python标准库，运行 <code>python3 round2_multisource_audit/scripts/build_inventory.py</code>，随后运行 <code>python3 round2_multisource_audit/scripts/validate_reviews.py --require-complete</code>。语义分类是保留的AI审阅结论，统计重跑不会自动生成新的人工判断。</p>
<p>本次是单个20专利图的穷尽多源节点审计，不是泛化性能评测；没有独立人工复标、查询干预或instance/sameAs金标准。泛化类与具体概念的边界、Event／Network及局部序号角色的本体选择均可能影响分类。来源完整不等于逐Claim结构已被建模，也不等于每条合并摘要有子句级出处。</p>
<footer class="muted">官方版本v1.5.7 · commit 28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c<br>仅审计第二轮基线；不混用后续边界实验数据。新增模型与Embedding API调用0，新增API费用$0，未读取密钥；未访问或修改FOT、AutoDL、SSH隧道或代理。原始输入哈希复核未变。</footer></body></html>'''
(P/'LightRAG_round2_multisource_node_audit_zh.html').write_text(body)
stats={'created_utc':result['created_utc'],'category_counts':dict(counts),'records':len(records),'source_records':sum(len(r['source_assessments']) for r in records),'report_files':[]}
for p in sorted(P.iterdir()):
 if p.is_file():stats['report_files'].append({'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(O/'evidence/report_build_checks.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n');print(json.dumps(stats,ensure_ascii=False,indent=2))
