"""Serialize AI-assisted source/edge review; no model calls or graph mutation.

The judgments below were made by reading every assigned dossier source chunk,
raw matching extraction row, and actual incident edge. This script validates
quoted text against both the saved source chunks and saved numbered Claims.
It does not turn lexical tests into semantic gold labels.
"""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

ROOT = legacy_root('round2_multisource_audit')
OUT = ROOT / 'round2_multisource_audit'

def source(pub, quote, claim, role, support, extra_quotes=None):
    return dict(publication_number=pub, evidence_quote=quote, claim_or_section=f'Claim {claim}',
                claim_number=claim, role_zh=role, support_note_zh=support,
                additional_quotes=extra_quotes or [])

SPECS = {
'N014': dict(category='shared_broad_class', confidence='high',
 reason='两篇均把 Computer Network 用作计算机系统传输或处理信息的网络。推荐器通信与广告信息评估属于不同应用，而非两种互不兼容的 network 词义；原抽取将一处标为 Concept、另一处标为 Artifact 只是类型粒度不一致，不能据此判为混并。',
 interpretation='共享计算机通信网络这一上位技术类；不是同一个网络部署，也不能把某篇专利的外部推荐器部署关系赋予另一篇。',
 sources=[
 source('US7991757B2','query the plurality of external recommenders over the computer network for recommendations responsive to the second request',1,'内容站点、推荐服务和外部推荐器之间请求/推荐的通信承载。','两块原实体描述分别概括 Claim 1 与 Claim 17，原文支持网络承载请求。'),
 source('US9304738B1','A system to evaluate information via a computer network',13,'停放域名广告信息评估系统使用的计算机网络。','原实体描述和 Data Processing System 邻边直接对应 Claim 13 的 system preamble。')],
 edge_claims={18:'US9304738B1 Claim 13',216:'US7991757B2 Claim 1',217:'US7991757B2 Claim 17'},
 edge_caveats={217:'原文是 requests received over a computer network with a network service interface；描述保留这一陈述，但 keywords=hosts 比原文更具体。未据此确认接口部署/托管事实，也未把关键词粒度问题归因于跨专利混并。'}),
'N015': dict(category='shared_specific_concept', confidence='high',
 reason='两篇都明确声明 non-transitory computer readable medium，且其角色均为携带可执行指令的非暂态计算机可读介质；指令实现的应用分别为邮件关系建模和广告关键词评估，不改变这一明确的技术概念。',
 interpretation='共享“含可执行指令的非暂态计算机可读介质”概念，而不是同一介质实例或同一组指令；某一介质的应用功能须保留其专利来源。',
 sources=[
 source('US10778629B2','A non-transitory computer readable medium containing executable instructions that when executed perform a method of modeling relationships',1,'执行邮件用户关系建模/关系数据生成方法的介质。','chunk000 的 Claim 1、chunk001 的 Claim 20 分别支持两段抽取描述。'),
 source('US9304738B1','A non-transitory computer readable medium having instructions to evaluate information',18,'执行停放域名广告关键词权重评估的介质。','chunk001 Claim 18 与 chunk002 Claim 19 对介质及页面特定关键词权重的陈述支持抽取。')],
 edge_claims={17:'US9304738B1 Claims 13,18',167:'US9304738B1 Claims 18,19',218:'US10778629B2 Claim 1',219:'US10778629B2 Claim 20'}),
'N016': dict(category='contextual_conflation', confidence='medium',
 reason='原文明确呈现两种 event 语义：US11423041B2 中是注册到历史对象、按条件触发并使 ETL 作业执行的数据处理事件；US9118735B1 中是用户声称正在参加、可据以定位的活动/事件。当前单一 Event ID 的描述并列了这两种角色，邻边也将地理位置/人员出席与订阅/触发关系接在同一节点。它们可以同属极抽象的“发生事项”，但这个上位类不足以支持当前具体关系角色的互换；本分类是语义区分需求，非已有错误推理证明。',
 interpretation='可以显式建立 occurrence/event 上位类，并保留数据处理事件与人参加的活动这两个上下文意义或子类。图中没有给定正式 ontology，因而 C3 表示当前单 ID 中具体意义/作用域被折叠的审阅判断，不等于证明类合并错误；若预设节点即宽类，则 shared_broad_class 也是合理解释。不主张任一专利内多个事件是同一实例，也不将跨来源邻接视为人物参加 ETL 事件的事实。',
 sources=[
 source('US11423041B2','criteria for triggering an event to perform a second ETL process subscribed to the event',1,'历史对象的被监控触发事件，触发订阅的 ETL 处理并可发送通知。','两个来源块的原实体行均描述注册/触发/订阅语义，和 Claims 1,8,15 一致。'),
 source('US9118735B1','an event that the third user has identified himself or herself as being at',7,'用户所处/参加的活动，作为 last-known location 的依据。','两块原抽取均描述人在某活动的出席/位置语义。Claim 7 在两块重叠；Claim 17 另说明 same event or venue。抽取中的 connecting person 是全文另一实施例术语，不能因此把两篇 event 视为同义。')],
 edge_claims={201:'US9118735B1 Claims 7,17',239:'US9118735B1 Claim 7',240:'US11423041B2 Claim 1',241:'US11423041B2 Claims 1,8,15',242:'US11423041B2 Abstract, Claim 3',243:'US11423041B2 Claims 1,8,15',244:'US11423041B2 Claim 15',245:'US11423041B2 Claims 8,15',246:'US11423041B2 Claims 10,17'},
 neighbor_note='9 条邻边按自己的来源都可找到对应陈述。未发现实际的“Third User 触发 ETL”或“ETL Event 是地理场所”边；这种路径只可能在忽略上下文后被组合，未运行检索/生成验证。'),
'N017': dict(category='contextual_conflation', confidence='high',
 reason='US8655901B1 和 US9218390B2 的 token 是输入查询的一段/单元，可被分词、标注标签并用于查询模型；US9118735B1 Claim 14 的 token 则是替换第二用户标识符以匿名化结果的代用值。当前单一 ID 合并这两个具体意义。可把它们抽象为数据值，但不足以支持将查询分词/标签关系用于匿名替代标识；两篇查询专利相互共享词元概念是有依据的。',
 interpretation='同名词义混合而非证明 token 实例相等。查询词元子类和匿名替代标识子类须区分；Token—Label 这条跨两篇查询专利的边本身仍有支持。',
 sources=[
 source('US8655901B1','segmenting a given query among the collection into one or more tokens in the first language, wherein each token includes one or more terms from the given query',1,'查询中的一段词语，按查询模式组件加标签，用于跨语言模式挖掘。','原实体行明确 segment of a query，与 Claim 1 的 tokens/terms 定义一致。'),
 source('US9118735B1','anonymizing results based on replacing an identifier associated with the second user with a token',14,'替换用户标识符的匿名化代用值。','原实体描述为 replacement value，原始关系行保留 Second User/Anonymized Results 语义；不应进一步猜测它是身份验证令牌或加密密钥。'),
 source('US9218390B2','receiving an input query, wherein the input query comprises a series of tokens; assigning a label to each of a plurality of the tokens',18,'地理搜索查询中的可标注单元，参与 CRF 模型构建。','当前图源只含 chunk002；新版 dossier 的原抽取仍来自此块的缓存。补回的 chunk000 截断响应不属于该节点的已入图 source set，未偷偷加作图来源。')],
 edge_claims={193:'US9118735B1 Claim 14',249:'US9118735B1 Claim 14',250:'US9218390B2 Claim 18',251:'US8655901B1 Claim 1; US9218390B2 Claim 18',252:'US9218390B2 Claim 18',253:'US8655901B1 Claim 1',254:'US8655901B1 Claim 1'},
 edge_caveats={249:'原文及描述是匿名化后的结果被加密，不是 token 本身执行加密；无向邻接/关键词不能解释为 token 是加密算法。',251:'跨两个查询词元来源的共享标签关系有原文支持；该边 source_id 不含匿名化专利。'},
 neighbor_note='7 条实际邻边的来源均可支持其本地关系。未观察到匿名化 token 被直接加上查询标签或 CRF 角色的实际边；跨来源路径组合风险未转化为已验证的错误检索或答案。'),
'N018': dict(category='shared_broad_class', confidence='high',
 reason='一篇处理社交成员对商品的推荐并排序，另一篇基于角色偏好生成观看内容的推荐。来源对象和生成主体不同，但均支持“建议/推荐某项内容或物品”这个共同类。原文没有证明这些推荐是同一对象，当前描述也不要求该等同性，故不能仅因人工推荐与算法推荐不同而判同名错合并。',
 interpretation='共享推荐信息这一宽类；保留成员作出的推荐和系统生成的内容推荐的子角色与各自实例。',
 sources=[
 source('US8095432B1','obtaining a first recommendation for the item from a first member of a social networking utility',1,'社交成员针对商品给出的推荐，按与询问成员的关系接近程度排序。','原抽取 opinion/endorsement 是对 recommendation 的解释性概括；Claims 1,2,8 支持来源、排序、接收者和库存关联。'),
 source('US9374411B1','send to the user a recommendation to play the second video content feature',1,'根据角色偏好和关系分数给用户生成/发送内容观看推荐。','chunk000 Claim 1 与 chunk001 Claims 11,14 支持发送与生成；不是社交商品推荐的同一实例。')],
 edge_claims={281:'US8095432B1 Claims 1,2',287:'US8095432B1 Claims 1,16',288:'US8095432B1 Claim 1',289:'US8095432B1 Claim 1',290:'US8095432B1 Claim 8',291:'US8095432B1 Claim 1',292:'US9374411B1 Claim 1',293:'US9374411B1 Claims 1,11',294:'US9374411B1 Claim 14'},
 edge_caveats={281:'Claim 1 的 third member 和 Claim 2 的 third member 各自有不同从属语境；边的并列描述不证明是同一具体成员。此为文内作用域注意点，并非跨专利错误传播。'}),
'N019': dict(category='shared_broad_class', confidence='high',
 reason='已逐一审阅 9 篇、14 个来源块。每篇均直接使用 processor(s) 执行其方法或指令：关系数据生成、ETL、归档、垃圾邮件过滤、推荐、查询翻译、媒体过滤、广告库存估计、诊断辅助。它们支持相同的计算处理硬件/执行元件类；应用动作不同不构成不同词义。合并描述显式采用 across various system contexts 及 may be 等范围语句，未证实把九个实例宣称为同一物理处理器。',
 interpretation='共享处理器类而非同一硬件实例；25 条邻边都是来源限定的应用/组件角色。Processor—Memory 的多源关系为常见耦合/执行关系，不能由此推断九篇系统共享一块内存或处理器。',
 sources=[
 source('US10778629B2','transferring, from the server, the data to a processor for generating relationship data by determining a relationship strength associated with each pair of users',10,'接收服务器传来的数据并生成用户对关系强度/关系数据。','Claims 10,21 对两块原抽取都有直接支持。'),
 source('US11423041B2','a memory, storing program instructions that when executed by the at least one processor',1,'执行存于 memory 的指令以实现数据目录。','Claim 1 支持原实体、Processor—Memory 和 Processor—Data Catalog。'),
 source('US7756837B2','A processor operable to execute a software program, the software program causing the processor to perform steps',16,'运行归档程序：接收数据流、抽取管理数据、存储、查询。','chunk000 的 Claim 16 起始与完整方法语境、chunk001 的 Claims 16–30、chunk002 的 Claim 32 支持三块原描述；后两块给出完整处理器/程序角色。'),
 source('US8069128B2','a processor that is operative to perform actions',1,'网络设备内执行两遍消息分析及模型清除的处理器。','Claim 1 的完整动作列表直接支持原实体描述；Network Device 的 comprises 邻边亦对应原文。'),
 source('US8095432B1','a recommendation application executing on the processor, resident in memory',16,'推荐系统中执行应用、计算关系接近度与排序的处理器。','Claim 1 的 using a processor 和 Claim 16 的组件声明支持两个来源块及应用/内存邻边。'),
 source('US8655901B1','one or more processors configured to interact with a computer-readable medium in order to perform operations',8,'执行查询模式翻译挖掘操作、与计算机可读介质交互的处理器。','Claim 8 的开头直接支持实体与两条 System/Medium 邻边。'),
 source('US8719408B2','a processor coupled to memory, the processor programmed by program code stored in the memory',17,'建立用户关系并实施数字媒体过滤各模块的处理器。','Claims 1,9,17 分别支持方法执行、程序指令、与内存耦合三类原抽取描述。'),
 source('US8880423B2','clustering, using a processor, a plurality of viewed pages into a plurality of clusters',1,'聚类浏览页面/关键词并估计广告库存的处理器。','Claims 1,8 支持 cluster/total inventory/deliverable inventory 角色；未把各估算实现等同为其他专利的方法。'),
 source('US9589231B2','a processor in communication with the memory for executing the instructions',20,'诊断辅助系统中执行查询/嵌入等指令的处理器。','chunk001 的 Claims 19,20 直接支持原实体和 Processor—Memory、Diagnosis Assistance System 边。')],
 edge_claims={91:'US10778629B2 Claims 10,21',101:'US7756837B2 Claim 16',153:'US8655901B1 Claim 8',258:'US8095432B1 Claims 1,16',302:'US8095432B1 Claim 16',303:'US8095432B1 Claim 16; US8719408B2 Claim 17; US11423041B2 Claim 1; US9589231B2 Claims 19,20',304:'US8880423B2 Claims 1,8',305:'US8880423B2 Claim 1',306:'US8880423B2 Claim 1',307:'US8880423B2 Claim 8',308:'US8069128B2 Claim 1',309:'US7756837B2 Claims 16,32',310:'US7756837B2 Claim 16',311:'US7756837B2 Claim 16',312:'US7756837B2 Claims 17,18',313:'US7756837B2 Claim 28',314:'US7756837B2 Claim 25',315:'US8719408B2 Claims 1,9',316:'US8719408B2 Claim 9',317:'US8719408B2 Claim 17',318:'US8655901B1 Claim 8',319:'US11423041B2 Claim 1',320:'US10778629B2 Claim 10',321:'US10778629B2 Claim 21',322:'US9589231B2 Claims 19,20'},
 edge_caveats={303:'四篇分别支持 memory/processor 的本地耦合或指令执行关系；共享类边不是同一硬件实例的跨篇证据。'}),
'N020': dict(category='shared_broad_class', confidence='high',
 reason='已逐一审阅 5 篇、6 个来源块。Memory 均为系统/装置中与处理元件相联的计算机存储组件；四篇明确存指令/程序，US9514120B1 Claim 18 仅明确 memory 与 processing device 的耦合。因此共同类是存储组件，不扩张为五篇都明确具有相同存储内容或同一内存实例。',
 interpretation='共享内存/存储部件类，不是跨专利同一对象。不同存储程序只是局部用途；US9514120B1 未明确的内容不由其他来源补足。',
 sources=[
 source('US11423041B2','a memory, storing program instructions that when executed by the at least one processor',1,'存储实现数据目录的程序指令。','原抽取描述与 Claim 1 一致。'),
 source('US8095432B1','a memory operatively connected to the processor',16,'与处理器相连且驻留推荐应用的内存。','Claim 16 的内存声明和 resident in memory 在两个来源块重叠，原抽取没有另造一处内存。'),
 source('US8719408B2','a processor coupled to memory, the processor programmed by program code stored in the memory',17,'存储媒体过滤装置程序代码并耦合处理器的内存。','Claim 17 直接支持原实体及 apparatus/processor 邻边。'),
 source('US9514120B1','An apparatus comprising: a memory; a processing device operatively coupled to the memory',18,'拼写反馈装置中与处理设备耦合的内存。','原实体仅声称组件和耦合，未声称此 Claim 明确把某程序存入内存；这种保守抽取有支持。'),
 source('US9589231B2','memory which stores instructions for: receiving a request for a query from a requester',20,'存储诊断辅助查询、嵌入和返回子集等指令。','Claim 20 以及跨边界的 Claim 19 支持原描述与实际邻边。')],
 edge_claims={303:'US8095432B1 Claim 16; US8719408B2 Claim 17; US11423041B2 Claim 1; US9589231B2 Claims 19,20',323:'US8095432B1 Claim 16',324:'US9514120B1 Claim 18',325:'US8719408B2 Claim 17',326:'US9589231B2 Claim 20'},
 edge_caveats={303:'此边保留四篇来源；每篇支持各自的处理器/内存角色，不保证单个来源支持全部合并措辞或跨篇实例同一。'}),
'N021': dict(category='shared_broad_class', confidence='high',
 reason='两篇 payment 都是经济报酬/款项支付，一篇与商品购买或点击相关，另一篇为专家诊断报酬。收付双方和触发条件不同，但共同货币支付类有直接原文支持，不能因交易场景不同判为语义冲突。',
 interpretation='共享支付类；各篇付款行为、付款人、收款人及触发条件保持独立。',
 sources=[
 source('US8095432B1','receiving a payment upon a purchase of the item from the inquiring member',13,'商品购买/点击关联的款项。','Claims 13,14 直接支持原实体及 Payment—Item/Inquiring Member 邻边。'),
 source('US9589231B2','providing for making a payment to the expert for formulating the diagnosis',13,'选择专家查询时为诊断专家付费。','Claim 13 明确给出专家报酬条件，原抽取忠实。')],
 edge_claims={275:'US8095432B1 Claim 13',301:'US8095432B1 Claims 13,14',335:'US9589231B2 Claim 13'}),
'N022': dict(category='contextual_conflation', confidence='medium',
 reason='US8095432B1 Claim 3 以朋友在内、非朋友在外来界定询问成员的社交关系网络；US9589231B2 Claim 20 则将 network 明确组成定义为诊断辅助系统和连接请求者/专家的用户设备集合。原实体描述沿用这两个不同的成员域，最终单节点却同时承载好友关系邻边与设备/系统组成邻边。两者可抽象为相互连接的集合，因此分类保留中等置信度；但这种极宽上位类没有表达当前具体 member network 与 device/system network 的不同语义约束。',
 interpretation='当前标签混合了社交成员网络与系统/设备网络两个上下文意义。可以显式定义 Network 为相互连接的集合这一上位类并保留子类/实例范围；在这种 ontology 下，shared_broad_class 也是合理解释。当前图没有给定正式 ontology，C3 不是已证明的语义错误或 bug；本审核不把一个全局标签自动解释成同一物理网络或同一组织。',
 sources=[
 source('US8095432B1','friends of the inquiring member are within a network of the inquiring member',3,'按朋友/非朋友内外边界划分的社交成员网络。','原实体 Concept 描述为 set of members，与 Claim 3 一致。'),
 source('US9589231B2','A network comprising a system for diagnosis assistance and a set of user devices for linking requesters and experts with the system',20,'由诊断辅助系统和用户设备构成、连接请求者与专家的系统网络。','原实体将其标为 Organization，原文更直接支持系统架构；实体类型选择不能单独证明语义混并，但组成边和原文与社交成员域确实不同。')],
 edge_claims={273:'US8095432B1 Claim 3',283:'US8095432B1 Claim 3',336:'US9589231B2 Claim 20',337:'US9589231B2 Claim 20'},
 neighbor_note='4 条实际邻边按各自 source_id 都有本地支持。未发现实际边宣称社交好友是诊断系统设备，亦未做任何会造成这种解释的检索/生成运行；仅记录未分词义节点可能产生的跨来源邻接。'),
'N023': dict(category='shared_broad_class', confidence='high',
 reason='5 篇、9 个来源块均将 user 作为使用系统/消费或反馈内容的人：邮件使用者、媒体读者、搜索用户、内容偏好表达者、拼写反馈者。原合并摘要逐一用 in the context of 区分局部角色，没有证据宣称为同一个人；角色不同不足以认定词义混并。',
 interpretation='共享系统用户这一人的角色类。不是五篇中的同一自然人，也不将角色偏好、邮件操作及错误反馈绑定到同一用户实例。',
 sources=[
 source('US8069128B2','such that a user is enabled to move the identified message to another message folder',6,'查看误分类提示、移动消息并可手动选择多遍过滤器的用户。','Claims 6,12,14,17 支持两个来源块的描述及客户端/文件夹/界面等邻边。'),
 source('US8719408B2','each user relationship based on monitoring an online association between a user and a content producer',1,'与内容发布者存在在线关系、接收按关联权重过滤内容的用户。','Claims 1–4 和17–20 支持两个来源块的用户关系、媒体聚合档案和共同兴趣角色。'),
 source('US8880423B2','the search keywords based on search keywords previously submitted by a plurality of users',1,'历史查询和浏览行为产生搜索库存估计输入的用户。','Claim 1 与 Abstract 支持原实体和 submitted/viewed 关系；不主张这些人与其他文档用户身份相同。'),
 source('US9374411B1','associate a preferred character with the user based at least upon the second user interaction data',1,'通过内容交互表达角色偏好并接收内容推荐的用户。','Claims 1,6,11,14,23 支持三个来源块的用户角色；末块原实体没有直接新增关系行，不能虚构额外邻边。'),
 source('US9514120B1','provide data indicative of presence of a potential typographical error in a work to a user via a graphical user interface',18,'通过图形界面反馈潜在排版/拼写错误是否为作者原意的用户。','Claim 18 的提示、用户输入以及多用户反馈合并语境支持原抽取。')],
 edge_claims={293:'US9374411B1 Claims 1,11',361:'US8880423B2 Abstract, Claim 1',366:'US8880423B2 Claim 1',382:'US9514120B1 Claim 18',383:'US9514120B1 Claim 18',384:'US8069128B2 Claim 6',385:'US8069128B2 Claim 6',386:'US8069128B2 Claim 14',387:'US8069128B2 Claims 12,17',388:'US8069128B2 Claim 17',389:'US8069128B2 Claims 14,19',390:'US8069128B2 Claim 14',391:'US9374411B1 Abstract, Claim 1',392:'US9374411B1 Claim 1',393:'US9374411B1 Claim 1',394:'US9374411B1 Claims 6,11',395:'US9374411B1 Claims 6,11',396:'US8719408B2 Claims 1,17',397:'US8719408B2 Claims 2,18',398:'US8719408B2 Claim 4',399:'US8719408B2 Claim 20'})
}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    (OUT/'reviews').mkdir(exist_ok=True)
    for aid, spec in SPECS.items():
        path = OUT/'dossiers'/f'{aid}.json'
        d = json.loads(path.read_text())
        assert set(s['publication_number'] for s in spec['sources']) == set(d['canonical_publications'])
        source_assessments=[]
        for ss in spec['sources']:
            ss = dict(ss)
            pub=ss['publication_number']
            ds=next(x for x in d['source_documents'] if x['publication_number']==pub)
            claim_path=ROOT/'data'/'claims'/f'{pub}.json'
            claims=json.loads(claim_path.read_text())
            claim=next(c for c in claims if c['claim_number']==ss['claim_number'])
            quote=ss['evidence_quote']
            assert quote in claim['text'], (aid,pub,'quote absent in specified claim',quote)
            quote_chunks=[c['chunk_id'] for c in ds['sources'] if quote in c['content']]
            assert quote_chunks,(aid,pub,'quote absent in graph source chunk',quote)
            ss['source_chunk_ids']=ds['source_chunks']
            ss['evidence_quote_present_in_chunk_ids']=quote_chunks
            ss['quote_verification']={
                'exact_contiguous_in_source_chunk':True,'exact_contiguous_in_numbered_claim':True,
                'claim_file':str(claim_path.relative_to(ROOT)), 'claim_file_sha256':sha(claim_path),
                'claim_number':ss['claim_number']}
            raw_entity_rows=[{'chunk_id':c['chunk_id'],**r} for c in ds['sources'] for r in c['raw_entity_rows']]
            raw_relation_rows=[{'chunk_id':c['chunk_id'],**r} for c in ds['sources'] for r in c['raw_relation_endpoint_rows']]
            ss['extraction_description_support']={
                'status':'supported_local_sense','assessment_zh':ss.pop('support_note_zh'),
                'raw_entity_rows_reviewed':raw_entity_rows,
                'raw_relation_endpoint_rows_reviewed':raw_relation_rows,
                'raw_entity_count':len(raw_entity_rows),'raw_relation_endpoint_count':len(raw_relation_rows)}
            ss['relevant_actual_edges']=ds['incident_edges_from_publication']
            ss['source_chunks_read_in_full']=[{'chunk_id':c['chunk_id'],'sha256':c['content_sha256'],'characters':len(c['content'])} for c in ds['sources']]
            source_assessments.append(ss)
        edges=d['all_incident_edges']
        assert set(spec['edge_claims']) == {e['edge_index'] for e in edges},(aid,'edge review coverage')
        edge_reviews=[]
        for e in edges:
            idx=e['edge_index']
            edge_reviews.append({'edge_index':idx,'source_id':e['source_id'],
                'canonical_publications':e['canonical_publications'],
                'assessment':'locally_supported_with_qualification' if idx in spec.get('edge_caveats',{}) else 'locally_supported',
                'source_evidence_claims':spec['edge_claims'][idx],
                'details_zh':spec.get('edge_caveats',{}).get(idx,'按该边自己的来源核对其描述；来源原文支持这一局部关系，不由其他专利补充事实。')})
        result={
            'audit_id':aid,'node_id':d['node_id'],'category':spec['category'],'confidence':spec['confidence'],
            'reason_zh':spec['reason'],'class_instance_interpretation_zh':spec['interpretation'],
            'source_assessments':source_assessments,
            'neighbor_audit':{
                'reviewed_incident_edge_count':len(edges),'observed_unsupported_edge':False,
                'details_zh':spec.get('neighbor_note','已逐条审阅实际邻边及其 source_id。未确认一条缺少其自身来源支持的边；合并后的跨文档邻接不能当成已发生错误边传播的证据。'),
                'edge_indices':[e['edge_index'] for e in edges], 'edge_reviews':edge_reviews,
                'retrieval_or_generation_propagation_tested':False},
            'limitations_zh':[
                '这是 AI 辅助原文/抽取/图结构审阅，非独立人工标注 gold、非新的模型评判 API 实验。',
                '仅审核当前保存的第二轮图快照与其来源块；概念合并不等于实例 sameAs，也没有进行跨专利路径检索或答案生成传播实验。',
                '原文为已索引摘要及 Claims；没有用外部说明书填补缺失事实。原始文本中的格式缺陷保持原样。',
                '边的端点顺序来自保存的无向图；语义方向按原关系描述核对，不把 source/target 字段顺序当作因果方向。',
                'observed_unsupported_edge=false 表示本次检查未确认无原文支持的实际边，不是证明全图无误；关键词粒度/局部实施例范围的警示另记。',
                '未给定显式类/实例 ontology。类别是基于具体词义及作用域的审阅标签，contextual_conflation 数量不是错误边数或代码 bug 率；Event/Network 的宽类解释可改变类别。',
                '缓存提取行未保存 finish_reason 时不推定完整或截断；本审核只对实际保存的实体/关系行与当前已入图事实作语义核验。'],
            'ontology_sensitivity':{
                'explicit_ontology_available':False,
                'alternative_shared_broad_class_plausible':aid in ('N016','N022'),
                'interpretation_zh':'若全局节点被明确规定为足够宽的 occurrence/network 类，并保留文档内谓词范围，宽类解释可以成立；本次 C3 仅记录具体词义/角色范围折叠。' if aid in ('N016','N022') else '类别只描述现有证据下的概念语义，未断言跨专利实例相同或已发生错误推理。'},
            'review_method':{'reviewer':'AI-assisted Codex content review','external_model_api_calls':0,'credentials_read':False,
                'all_source_publications_reviewed':len(source_assessments),'all_source_chunks_reviewed':len(d['all_source_chunks']),
                'all_actual_incident_edges_reviewed':len(edges),'raw_input_kind':'saved extraction rows; no new extraction',
                'review_protocol_sha256':sha(OUT/'evidence'/'review_protocol.json'),
                'dossier_sha256':sha(path),'generated_utc':datetime.now(timezone.utc).isoformat()},
            'graph_node_description_reviewed':d['graph_node']['description']
        }
        (OUT/'reviews'/f'{aid}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(aid,d['node_id'],spec['category'],len(source_assessments),'sources',len(edges),'edges')

if __name__=='__main__':main()
