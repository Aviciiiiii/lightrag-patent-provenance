"""AI-assisted, source-grounded semantic review; no model/API calls.
The prose judgments below were authored after reading all assigned dossiers.
The script validates every selected contiguous quote against its claims JSON,
indexed full document and at least one actual mapped source chunk. It does not
infer semantic correctness programmatically or create a human gold standard.
"""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
import json, pathlib, hashlib, datetime
ROOT=legacy_root('round2_multisource_audit')
OUT=ROOT/'round2_multisource_audit'

def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
S={
'N027': dict(category='shared_broad_class', confidence='high',
 reason='两来源都指用户显式提供的反馈数据；一处判断用户是否偏好虚构角色，另一处判断疑似拼写错误是否为作者有意写法。不同反馈对象和字段不改变“用户反馈”这一共同上位数据类。合并描述保留两种任务，不能据此认定两个反馈实例相同或词义冲突。',
 instance='共同类为用户提供的意见/判定；US9374411B1的角色偏好反馈与US9514120B1的文本校验反馈是不同文档局部数据实例，字段及取值不应跨文档移植。',
 sources={
 'US9374411B1':(23,'obtain explicit user feedback expressing that the user favors the first fictional character via a user interface.','用户经界面表达对第一个虚构角色的偏好。','chunk002实体行与Claim23一致；三条关系分别保留指令获取、界面渠道和所偏好角色。'),
 'US9514120B1':(1,'feedback comprising an indicator that specifies that the potential typographical error is an author-intended string for the work','用户反馈是判断疑似排版/拼写错误是否为作者意图的输入，并与其他作品反馈组合。','chunk000实体描述的核心判定与Claim1一致，列举字段来自Claim7；原文“at least one of”是可选字段，抽取描述未明说全字段必需。')},
 edge_claims={440:'US9374411B1 Claim23',450:'US9514120B1 Abstract/Claim1',461:'US9514120B1 Claim1',480:'US9514120B1 Claim1',490:'US9514120B1 Claim1',491:'US9374411B1 Claim23',492:'US9374411B1 Claim23'}),
'N028': dict(category='shared_broad_class',confidence='high',
 reason='两篇都使用非暂态计算机可读介质承载可执行指令的共同存储载体类；指令分别完成内容推荐和排版错误反馈处理。应用功能不同不足以证明介质概念异义。',
 instance='介质是共同类；各独立权利要求中的具体指令集和介质实施例具有各自专利作用域，不能断言同一实际介质同时执行全部功能。',
 sources={
 'US9374411B1':(1,'A non-transitory computer-readable medium having a plurality of computer instructions executable by at least one computing device','承载内容呈现、角色偏好及推荐流程的指令介质。','chunk000/001对应独立Claim1/21；chunk002引用Claim21的从属Claim22–25，其存储指令含义需继承母项，不是独立新增介质实例。'),
 'US9514120B1':(10,'A non-transitory computer-readable medium having instructions stored thereon which, when executed by a processing device, cause the processing device to perform operations comprising:','承载判别作者意图字符串、反馈组合及参考更新操作的指令介质。','chunk000包含Claim10开头，chunk001续接其操作及从属项；抽取均与同一介质权利要求一致。')},
 edge_claims={452:'US9374411B1 Claims1,21',463:'US9514120B1 Claim10',512:'US9374411B1 Claim23继承Claim21'},
 limits=['介质—计算设备边是“介质上指令由设备执行”的简写，不能将其读为物理介质本体被执行。']),
'N029': dict(category='shared_broad_class',confidence='high',
 reason='两来源均是系统的人类用户群体：推荐结果受众与疑似文字错误反馈参与者。共同人类使用者角色成立，场景和具体人员集合不同不是实体语义错误。',
 instance='Users为用户类/集合角色，不是跨专利可唯一识别的一批人；不能从共享节点推出两篇用户身份或行为相同。',
 sources={
 'US7991757B2':(22,'A system for enabling site operators to obtain item recommendations for presentation to users','内容站点展示项目推荐的最终用户。','chunk001实体和Site Operators邻边直接对应Claim22首句。'),
 'US9514120B1':(1,'sending, by the processing device, data indicative of presence of the potential typographical error in the work to a plurality of users','收到潜在文字错误提示并提供作者意图反馈的用户群体。','chunk000实体与Claim1及摘要收集反馈操作一致。')},
 edge_claims={451:'US9514120B1 Abstract/Claim1',513:'US7991757B2 Claim22'}),
'N030': dict(category='shared_broad_class',confidence='medium',
 reason='Apparatus在两来源中均是由硬件/功能模块构成的装置类：备份数据管理装置与收集文字校验反馈的装置。原文没有表示同一个装置；泛化名称本身不足以判跨专利语义混并。US9514120B1另有同专利内的操作主体粗化候选，须与跨来源类合并分开。',
 instance='共同类为装置/设备；Claim31/47/48的备份流装置与另一专利Claim18的处理器/内存装置是局部实施例。把全部邻边无作用域地合成为同一机器能力会超出原文，但本审计未运行该种推理。',
 sources={
 'US7756837B2':(31,'An apparatus, comprising: means for receiving at least one data-stream intended for archiving on a backup storage device;','透明接收备份流、提取管理数据并存储到数据库的装置；Claim47/48分别含存储路由/服务器功能。','chunk001/002/003实体及关系分别对应Claim31/47/48，保留具体功能差异；未发现从另一本专利移入的关系陈述。'),
 'US9514120B1':(18,'An apparatus comprising: a memory; a processing device operatively coupled to the memory','含内存和处理设备的装置，向用户显示疑似文字错误并向服务器提交反馈；服务器随后组合、排序及更新参考。','chunk001实体与Claim18前段对应；chunk002实体描述及行17–19把组合/排序/更新的主语概括为Apparatus。Claim18明确这些后续操作属于server computing machine，存在局部主体细节丢失候选，不能直接归因跨专利合并。')},
 edge_claims={102:'US7756837B2 Claims31,48',324:'US9514120B1 Claim18',468:'US9514120B1 Claim18',477:'US9514120B1 Claims19,20',495:'US9514120B1 Claim18',502:'US9514120B1 Claim18',514:'US9514120B1 Claim18',515:'US9514120B1 Claim18',516:'US9514120B1 Claim18',517:'US9514120B1 Claim18',518:'US9514120B1 Claim19',519:'US9514120B1 Claim19',520:'US9514120B1 Claim19',521:'US9514120B1 Claim19',522:'US7756837B2 Claims31,47',523:'US7756837B2 Claims31,47,48',524:'US7756837B2 Claim47',525:'US7756837B2 Claim48'},
 limits=['是否可把server操作作为整机功能间接概括存在粒度解释空间；目前将三个显式主语不一致的边列为qualified_role_attribution_candidate，不计为已证明跨专利错误边。']),
'N031': dict(category='shared_broad_class',confidence='high',
 reason='两来源的Score均为算法评估值，但一处评估推荐项目并加权归一化，另一处评估消息是否误放文件夹。可共同解释为评估分数类；量纲、算法与数值实例不可互换不等于Score一词的异义误并。',
 instance='共享量化评估值类；推荐分数及消息分类分数的取值域、阈值和计算过程属于各自文档，图中未声明同一数值变量。',
 sources={
 'US7991757B2':(4,'receiving recommendations and corresponding scores from the recommenders; applying weights to each of the recommenders; combining the scores with the weights to produce overall scores;','推荐器返回的项目评分，归一化及加权后生成总分。','chunk000描述由Claim1的归一化和Claim4的加权组合共同支持，未把消息分类语义加入其原始抽取。'),
 'US8069128B2':(17,'using the second classification data, executing a second pass of the multi-pass message filter on the sorted plurality of messages to score each message;','多遍消息过滤器第二遍对消息打分，用以发现错误文件夹中的消息。','chunk001实体及Score–Message关系直接对应Claim17。')},
 edge_claims={177:'US7991757B2 Claim4',556:'US7991757B2 Claim1',558:'US7991757B2 Claim4',559:'US8069128B2 Claim17'}),
'N032': dict(category='shared_specific_concept',confidence='high',
 reason='两来源都明确把搜索query表示/分割为tokens，并给tokens赋予语义标签；因此是查询语言处理中的词/词组单元这一共同技术概念，不是名称巧合。第一来源允许token含多个terms，第二来源的具体分词方式未完全定义，不能推定分词粒度相同。',
 instance='共同概念为查询中的token单元；翻译模式挖掘和地理查询解析中的具体token序列、词表及标签方案是各自局部实例。',
 sources={
 'US8655901B1':(15,'segmenting a given query among the collection into one or more tokens in the first language, wherein each token includes one or more terms from the given query;','第一语言query的词/词组分段，绑定查询模式组件标签，翻译顺序用于恢复目标语言模式。','chunk001实体与Claim15的token定义一致，四条端点关系分别对应分段、模式组件绑定、标注及翻译顺序。'),
 'US9218390B2':(1,'receiving an input query, wherein the input query comprises a series of tokens; assigning a label to each of a plurality of the tokens;','输入地理网页搜索query的token序列，标签用于条件随机场解析。','原api_0191_response.json虽finish_reason=length，但已保存的实体行15及关系行56/57完整，且实际图保留这些条目。只能评价这些已观察到的记录，不能用截断输出判断全部关系召回。')},
 edge_claims={701:'US9218390B2 Claim1',704:'US9218390B2 Claim1; US8655901B1 Claim15',705:'US8655901B1 Claim15',706:'US8655901B1 Claim15',707:'US8655901B1 Claim15'},
 limits=['US9218390B2-chunk-000的原抽取响应因length截断，补证来自原API日志而非成功提取cache；当前完整可见行与图存在性可核验，抽取完整性不能据此确认。']),
'N033': dict(category='shared_specific_concept',confidence='medium',
 reason='两来源都将Labels作为query token/片段的语义标注：一处表示查询模式组件，一处表示搜索词、地理表达等查询解析类别。作为查询token语义标签概念可共享；各自完整标签集合和学习机制不相同，不能把一个来源的具体枚举强加给另一来源。',
 instance='共享查询token语义标签概念；不同专利标签schema及每个token上的标签赋值是局部对象。共同节点不能证明相同label ID或枚举。',
 sources={
 'US8655901B1':(15,'annotating the one or more tokens with labels for the corresponding components of the first query pattern;','查询模式组件的标注，用其对应次序抽取翻译后query pattern。','chunk001实体、查询标注、token标注和翻译模式次序关系均有Claim13/15支持。'),
 'US9218390B2':(12,'the respective sentence identifies the respective label as corresponding to one or more of a search term, a geographic expression, a geographic expression relation indication, and/or uninteresting information;','地理查询解析的语义类别标签；句子被关联到标签以标识其意义。','chunk000完整可见实体及关系来自length截断的原api_0191日志；chunk001独立保存的实体/关系由Claim12支持。标签与sentence在原文明说不同，图亦分别建节点。')},
 edge_claims={673:'US9218390B2 Claim12',704:'US9218390B2 Claim1; US8655901B1 Claim15',708:'US9218390B2 Claims1,12',709:'US8655901B1 Claims13,15',710:'US8655901B1 Claim15'},
 limits=['shared_specific_concept的粒度限定为查询token语义标签，不包括两个具体标签集等价。','US9218390B2-chunk-000的原抽取响应finish_reason=length，已见完整条目可核验，但不能作无遗漏保证。']),
'N034': dict(category='shared_specific_concept',confidence='medium',
 reason='Label单数节点同样表示query token的语义类别标注，一处对应模式组件，另一处对应地理解析类别；技术角色相容。各标签集合不同不是已证明多义混并，且本节点与Labels复数节点是图中两个真实ID，不能在审计中人为合并。',
 instance='共享查询token语义标签概念，具体标签赋值和标签集按文档限定；Label/Labels命名变体的存在另属归一化粒度问题，本轮不改图。',
 sources={
 'US8655901B1':(1,'annotating the one or more tokens with labels for the corresponding components of the first query pattern;','绑定到第一查询模式组件的token标注。','chunk000实体与Claim1的标注步骤相符，Token–Label边保留该角色。'),
 'US9218390B2':(18,'the respective sentence identifies the respective label as corresponding to one or more of a search term, a geographic expression, a geographic expression relation indication, and/or uninteresting information;','机器可读介质权利要求中，token上的地理/搜索语义类别标注，参与建立CRF模型。','chunk002完整实体与三条端点关系由Claim18支持；sentence与label不同对象的区分在原文与图中均存在。')},
 edge_claims={251:'US9218390B2 Claim18; US8655901B1 Claim1',732:'US9218390B2 Claim18',736:'US9218390B2 Claim18'},
 limits=['不同标签schema不能等同；技术概念共享的判断不意味着单复数ID已被正确归一。']),
'N035': dict(category='shared_broad_class',confidence='high',
 reason='两来源均指为获取信息而提出的查询请求：备份数据管理查询与用于模式挖掘/翻译的搜索query。前者未限定自然语言格式，后者明确token/语言结构；共同信息查询类仍成立，不能仅因处理流程不同判异义。',
 instance='共同类为信息检索查询请求；备份管理查询实例不应被默认分词或翻译，语言模式挖掘query也不能默认访问备份数据库。原始边的source_id可区分这些条件。',
 sources={
 'US7756837B2':(13,'receiving at least one query from a party concerning the archived data-stream; formulating one or more responses to the query based on an analysis of the management data stored in the database;','来自请求方、关于已归档数据流的查询；通过分析管理数据库形成响应，并可经网络收发。','chunk000/001/002抽取分别由Claim13/28/44及网络从属Claim14/29/45支持，均是相同文档局部信息查询角色。'),
 'US8655901B1':(1,'segmenting a given query among the collection into one or more tokens in the first language, wherein each token includes one or more terms from the given query;','从query log识别、切分、标注、翻译的搜索query，也包括用翻译模式解释的新query。','chunk000/001描述合并了训练集合query与接收query的角色；这些都在Claim1–15中明确出现，不能据此认定同一查询实例。')},
 edge_claims={112:'US7756837B2 Claims29,45',253:'US8655901B1 Claim1',313:'US7756837B2 Claim28',706:'US8655901B1 Claim15',709:'US8655901B1 Claims13,15',758:'US7756837B2 Claims13,44',769:'US7756837B2 Claims13,28',770:'US8655901B1 Claim1',771:'US8655901B1 Claim1',772:'US8655901B1 Claims1,15',773:'US8655901B1 Claims2,3,9,10',774:'US8655901B1 Claims12,15',775:'US8655901B1 Claim15',776:'US8655901B1 Claim15'}),
'N036': dict(category='shared_broad_class',confidence='high',
 reason='两来源明确描述非暂态计算机存储介质编码程序指令，分别用于知识面板内容处理和query pattern翻译。相同的存储载体类可共享，应用程序功能差异不是媒介词义混并。',
 instance='共同存储介质类；两篇中的程序和实际存储实例分别限定，不应解释成同一载体上必然安装两套程序。',
 sources={
 'US10867122B1':(6,'A non-transitory computer storage medium encoded with computer program instructions that, when executed by one or more processors, cause a computer device to perform operations comprising:','编码用于内容接收、事实实体识别和知识面板/界面呈现操作的指令。','chunk000为Claim6开头；chunk001的Claim7–10继承该介质，描述对应同一类的应用程序。'),
 'US8655901B1':(15,'A non-transitory computer storage medium encoded with a computer program, the program comprising instructions that when executed by data processing apparatus cause the data processing apparatus to perform operations comprising:','编码执行查询模式标注与翻译操作的程序。','chunk001实体及与Data Processing Apparatus的关系直接由Claim15支持。')},
 edge_claims={844:'US8655901B1 Claim15',845:'US10867122B1 Claim6及从属Claims7–10'}),
'N037': dict(category='shared_broad_class',confidence='high',
 reason='两来源的Data Processing Apparatus都是执行数据处理方法的计算装置，分别承担内容相关知识面板和查询模式翻译流程。通用执行设备类相容；没有原文身份等同声明。',
 instance='共同可执行数据处理的装置类；两篇文档内装置是独立实施例。US10867122B1中Claim1的apparatus与Claim6的computer device可以有类级近义解释，但不能据此证明实际个体相同。',
 sources={
 'US10867122B1':(1,'A method performed by a data processing apparatus, the method comprising:','接收用户输入内容、确定事实实体、请求相关界面内容并提供显示指令的方法执行者。','chunk000实体和确定实体/请求内容关系由Claim1支持。Computer Program Instructions邻边描述来自Claim6的computer device；将其绑定到Data Processing Apparatus是类级名称归并，未证明两个权利要求个体相同。'),
 'US8655901B1':(15,'instructions that when executed by data processing apparatus cause the data processing apparatus to perform operations comprising:','执行存储介质中程序、完成query pattern翻译的方法执行装置。','chunk001实体及存储介质邻边直接对应Claim15的程序执行关系。')},
 edge_claims={844:'US8655901B1 Claim15',846:'US10867122B1 Claim1',847:'US10867122B1 Claim1/Abstract',848:'US10867122B1 Claim6（computer device）'},
 limits=['edge848的端点名称是抽取时把computer device用Data Processing Apparatus概括；作为共同计算设备类可解释，作为同一个体等同则缺乏证明。']),
'N038': dict(category='shared_broad_class',confidence='high',
 reason='两来源均指执行计算/程序操作的一台或多台设备；ETL历史事件触发与查询翻译属于不同应用，不能据此判设备概念误并。',
 instance='共同计算设备类；ETL服务中的设备集合与query翻译系统中的设备集合是各自文档局部实例，不表示同一部署或同一机器。',
 sources={
 'US11423041B2':(15,'storing program instructions that when executed on or across one or more computing devices, cause the one or more computing devices to implement:','执行数据目录记录、条件评估及ETL事件触发指令的一台或多台设备。','chunk001实体和存储介质边直接对应Claim15，并由Claim16/17延续。'),
 'US8655901B1':(15,'translating, with a system comprising one or more computing devices, the collection of annotated queries in the first language into a translated collection of queries in a second language;','构成系统来翻译已标注query集合的计算设备。','chunk001实体和Query关系直接对应Claim15。')},
 edge_claims={776:'US8655901B1 Claim15',849:'US11423041B2 Claims15–17'})
}

COMMON_LIMITS=[
 '本结果为AI辅助逐来源语义审阅，不是独立人工金标准；分类依赖所声明的类/实例粒度。',
 '只审计第二轮既有20篇索引中的可见原chunk、原抽取与实际图邻边；原文范围为已索引的标题、摘要及Claims，未额外读取完整说明书或新语料，未调用模型API，也未进行新的检索/生成传播测试。',
 '共享节点产生跨专利邻接不等于已观察到错误跨文档推理；边的source_id和file_path应保持作用域。'
]
outputs=[]
for aid, a in S.items():
 dp=OUT/'dossiers'/f'{aid}.json';d=json.loads(dp.read_text())
 assessments=[];input_hashes={str(dp.relative_to(ROOT)):h(dp)}
 for pub,(claimnum,quote,role,support) in a['sources'].items():
  doc=next(x for x in d['source_documents'] if x['publication_number']==pub)
  cp=ROOT/'data'/'claims'/f'{pub}.json'; claims=json.loads(cp.read_text())
  claim=next(x for x in claims if x['claim_number']==claimnum)
  assert quote in claim['text'],(aid,pub,'not in claim',quote)
  qp=[s['chunk_id'] for s in doc['sources'] if quote in s['content']]
  assert qp,(aid,pub,'not in source chunk',quote)
  fullp=ROOT/'data'/'documents'/f'{pub}.txt';full=fullp.read_text()
  assert quote in full,(aid,pub,'not in full document')
  input_hashes[str(cp.relative_to(ROOT))]=h(cp); input_hashes[str(fullp.relative_to(ROOT))]=h(fullp)
  raw=[]
  for s in doc['sources']:
   raw.append(dict(chunk_id=s['chunk_id'],content_sha256=s['content_sha256'],
       raw_entity_rows=s['raw_entity_rows'],raw_relation_endpoint_rows=s['raw_relation_endpoint_rows'],
       extraction_records=s.get('extraction_records',[])))
  assessments.append(dict(publication_number=pub,evidence_quote=quote,
    claim_or_section=f'Claim {claimnum}',source_chunk_ids=doc['source_chunks'],
    quote_contained_in_source_chunk_ids=qp,claim_number=claimnum,
    quote_verification=dict(exact_contiguous_in_claim=True,exact_contiguous_in_indexed_document=True,
       exact_contiguous_in_mapped_source_chunk=True,claim_text_char_offset=claim['text'].index(quote),
       indexed_document_char_offset=full.index(quote)),
    role_zh=role,extraction_description_support=dict(assessment_zh=support,raw_records=raw),
    relevant_actual_edges=doc['incident_edges_from_publication']))
 edges=d['all_incident_edges']
 assert set(a['edge_claims'])=={e['edge_index'] for e in edges},(aid,'edge coverage')
 ereviews=[]
 for e in edges:
  q=dict(edge_index=e['edge_index'],source=e['source'],target=e['target'],source_id=e['source_id'],
   file_path=e['file_path'],canonical_publications=e['canonical_publications'],
   actual_description=e['description'],claim_or_section=a['edge_claims'][e['edge_index']],
   assessment='supported_in_source_scope',
   assessment_zh='关系描述与其实际source_id所指专利的相应原文角色相符；不将其外推到本节点另一来源。')
  if aid=='N030' and e['edge_index'] in [495,502,517]:
   q['assessment']='qualified_role_attribution_candidate'
   q['assessment_zh']='Claim18显式将combine/sort/update赋予server computing machine；chunk002原始抽取及图边以Apparatus为主语。存在局部主体粒度粗化，但若把Apparatus理解为协作整体可有概括解释，未计为已证明跨专利不支持边。'
  if aid=='N037' and e['edge_index']==848:
   q['assessment']='supported_at_class_level_identity_unproven'
   q['assessment_zh']='边描述的computer device执行指令由Claim6支持；端点归一为Data Processing Apparatus仅可作计算设备类概括，不能据此确认与Claim1 apparatus为同一实例。'
  ereviews.append(q)
 detail='已逐条检查全部实际邻边及其source_id/file_path；各关系在所属专利中有对应陈述，未发现将另一专利特征直接写入本专利边描述的确证。共同节点容许潜在无作用域路径组合，但本审计没有执行或观察该传播。'
 if aid=='N030':detail+=' 另列495/502/517的局部主语粗化候选；它们均来自US9514120B1-chunk-002且原始抽取已经如此，不能归因跨专利节点合并。'
 if aid in ['N032','N033','N034']:detail+=' 跨来源合并的token-label边保留两种标注语境及各source_id，未声明两套标签枚举相同。'
 review=dict(audit_id=aid,node_id=d['node_id'],category=a['category'],confidence=a['confidence'],
  reason_zh=a['reason'],class_instance_interpretation_zh=a['instance'],
  concept_class_vs_local_instance='shared_class; document-local instances remain distinct',
  source_assessments=assessments,
  neighbor_audit=dict(reviewed_incident_edge_count=len(edges),observed_unsupported_edge=False,
    observed_unsupported_edge_definition='true仅用于依据原文明确不支持的实际关系；类级概括/端点角色候选单列，不自动计入。',
    details_zh=detail,edge_indices=[e['edge_index'] for e in edges],edge_reviews=ereviews,
    observed_cross_publication_unsupported_edge=False),
  limitations_zh=COMMON_LIMITS+a.get('limits',[]),
  review_method='AI-assisted source-by-source reading; deterministic quote/coverage validation; no external model API',
  reviewed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
  dossier_sha256=h(dp),input_sha256=input_hashes,
  source_and_raw_review_coverage=dict(publication_count=len(assessments),
     source_chunk_ids_reviewed=d['all_source_chunks'],all_source_chunks_read=True,
     all_raw_entity_and_relation_endpoint_rows_read=True,all_actual_incident_edges_reviewed=True))
 if aid=='N030':
  claim18=next(x['text'] for x in json.loads((ROOT/'data/claims/US9514120B1.json').read_text()) if x['claim_number']==18)
  doc=next(x for x in d['source_documents'] if x['publication_number']=='US9514120B1')
  c1=next(x for x in doc['sources'] if x['chunk_id'].endswith('001'))
  c2=next(x for x in doc['sources'] if x['chunk_id'].endswith('002'))
  quote='wherein the server computing machine is to: combine the feedback with additional feedback from a plurality of users for the work and one or more additional works to generate a combined feedback; sort the combined feedback based on the one or more parameters associated with the author-intended string to generate a sorted feedback; and update, based on the sorted feedback, a reference using the author-intended string.'
  assert quote in claim18 and quote in c1['content']
  review['neighbor_audit']['role_attribution_candidates']=[dict(
    edge_indices=[495,502,517],publication_number='US9514120B1',claim_number=18,
    original_claim_text=claim18,exact_subject_clause=quote,subject_clause_source_chunk='US9514120B1-chunk-001',
    next_chunk_id=c2['chunk_id'],next_chunk_exact_start=c2['content'][:280],
    subject_clause_present_in_next_chunk='wherein the server computing machine is to' in c2['content'],
    raw_record_line_numbers=[17,18,19],raw_and_graph_subject='Apparatus',claim_explicit_subject='server computing machine',
    stage_observation_zh='主语粗化已出现在chunk002的原始实体描述及关系行，合并图保留这些行；chunk002起始位于Claim18中段且无显式server主语。边界相关的上下文不足是可见条件，不是受控因果证明。',
    interpretation_zh='按Claim的显式操作执行者粒度，三边不够忠实；按整个协作装置能力粒度可能作概括。将此候选与跨专利contextual_conflation及已证实unsupported edge分开。',
    confidence='medium')]
 op=OUT/'reviews'/f'{aid}.json';op.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
 outputs.append(dict(audit_id=aid,node_id=d['node_id'],category=a['category'],confidence=a['confidence'],
  publications=len(assessments),reviewed_incident_edges=len(edges),qualified_candidates=[495,502,517] if aid=='N030' else []))
summary=dict(scope='N027–N038 only',reviewer='round4_full_eval_f05',ai_assisted_not_human_gold=True,
 outputs=outputs,validation='All 24 source quotes exact in claims, full documents, and actual source chunks; all 69 per-node incident-edge appearances reviewed (shared edges can recur between assigned nodes).',
 total_per_node_incident_edge_appearances=sum(x['reviewed_incident_edges'] for x in outputs),
 category_counts={k:sum(x['category']==k for x in outputs) for k in ['shared_specific_concept','shared_broad_class','contextual_conflation','insufficient_evidence']},
 external_model_api_calls=0,credentials_read=False,original_round2_files_modified=False)
(OUT/'evidence'/'review_n027_n038_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
