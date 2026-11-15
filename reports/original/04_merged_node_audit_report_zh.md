<!-- 由 tools/html_to_md.py 从 04_merged_node_audit_report_zh.html 生成；表格与正文完整，HTML 中折叠/内嵌的历史快照未转换。 -->

LightRAG 第二轮跨专利节点审计

# LightRAG 第二轮：跨专利节点来源与语义审计

2026-10-30 · 既有 v1.5.7 快照 · 只读审计 · 新增 API 成本 $0

612 个节点中，**38 个节点（6.21%）**来自两篇或以上专利。逐项审阅后，**32 个支持合理的类／概念共享**；另外 **6 个表现为异义或文档局部角色在同一 ID 中并置**。后者不是“6 个已证实错误合并”：其中 5 个对本体粒度和角色作用域的解释较敏感。

**完成范围：**38/38 节点、98/98 个节点—专利来源、307 次逐节点邻边审阅（266 条不同实际边）。98 条代表性引文均核对到具体原文、Claim／摘要及实际来源 Chunk。原图、原索引和旧报告未改动；没有重建索引、运行新查询或调用 LLM／Embedding。

## 统计与判定边界

| 最终类别 | 节点数 | 占38个多源节点 |
|---|---|---|
| 较具体的共享技术概念 | 3 | 7.9% |
| 合理共享的宽泛类别 | 29 | 76.3% |
| 异义／文档局部角色并置 | 6 | 15.8% |
| 证据不足 | 0 | 0.0% |

“共享宽类”包括 Processor、Memory、Server、System 等通用类别。不同专利内的具体实例不能互换，但可以共享同一个上位类；泛化名称本身不是错误。较具体的共享概念为查询语境中的 Tokens、Labels、Label。两类共 32 个，均未因名称通用而判错。

**本体敏感性：**6 个并置节点为 First User、Second User、Third User、Event、Token、Network。Token 的“匿名替代值／查询词元”差异最清楚；其余5项保留合法宽类解释。若采用该解释，计数可变为共享技术概念3、共享宽类34、异义并置1。两种计数都不能作为代码缺陷率或实体解析准确率。

这是 AI 辅助逐项内容审阅，另对7个重点节点进行第二次 AI 审阅，**不是独立人工 gold**。高／中置信度是定性判断。初评把2种存储载体列为较具体概念；为与其他存储介质、Processor／Memory保持同一粒度，最终统一为共享宽类。初评与裁决均保留，这不改变合理共享总数或并置节点数。

## 来源统计如何复现

复用 `lj408/Dis2Pat` 数据集首100行中有目的选取的20篇信息检索、推荐、上下文排序等专利；不是随机代表性样本。本次未重新下载。实际快照为20篇专利、48个Chunk、612节点、994边。以节点 `source_id` 与完整 `entity_chunks.chunk_ids` 的并集为起点，按 `text_chunks.full_doc_id → full_docs 的 publication header` 归并公开号；同专利的多个Chunk和路径别名只计一次。随后交叉核对节点 `file_path`，不按分隔后的列表位置配对。

`&lt;SEP&gt;` 是保存字段的分隔符。38节点中，28个来自2篇、6个来自3篇、3个来自5篇、1个来自9篇。节点最多14个Chunk；缺失映射、文档冲突、来源KV与图字段差异、路径对应差异均为0。48个实际Chunk都能在所属完整索引文本中逐字定位。本快照未出现来源列表截断；这不表示所有规模下都不会截断。

47条抽取响应由原缓存读取；US9218390B2-chunk-000曾因输出上限截断、未入缓存，使用保存的调用191请求与原始响应补齐审阅，并保留 `finish_reason=length` 限定。没有补调模型。98个节点—专利来源均找到该名字的原始实体抽取行。审计范围是当时实际索引的标题、完整摘要及Claims，不含未索引的完整说明书。

## 三个代表案例

### 1. 真正共享：Tokens（N032，2篇）

两篇专利都把查询分成词元并赋予标注：一个服务于跨语言查询模式，另一个服务于地理搜索查询解析。它们共享查询词元这一技术概念，不表示两个查询或算法实例相同。

**US8655901B1 · Claim 15**
segmenting a given query among the collection into one or more tokens in the first language, wherein each token includes one or more terms from the given query;
第一语言query的词/词组分段，绑定查询模式组件标签，翻译顺序用于恢复目标语言模式。
来源 Chunk：US8655901B1-chunk-001

**US9218390B2 · Claim 1**
receiving an input query, wherein the input query comprises a series of tokens; assigning a label to each of a plurality of the tokens;
输入地理网页搜索query的token序列，标签用于条件随机场解析。
来源 Chunk：US9218390B2-chunk-000

实际边704为 `Tokens — Labels`，保留两篇来源；相应单数节点边251 `Token — Label` 也有两篇查询专利的支持。现图的单数与复数是不同ID；本任务不评价应合而未合的同义节点。

### 2. 合理但宽泛：Processor（N019，9篇）

9篇原文都提供处理器／执行指令的硬件角色，因此共享 Processor 类合理；各专利中的处理器实例及其职责不可据此对齐。其25条实际邻边按各自来源审阅，没有把跨文档邻接自动认作错误。

**US10778629B2 · Claim 10**
transferring, from the server, the data to a processor for generating relationship data by determining a relationship strength associated with each pair of users
接收服务器传来的数据并生成用户对关系强度/关系数据。
来源 Chunk：US10778629B2-chunk-000, US10778629B2-chunk-001

**US11423041B2 · Claim 1**
a memory, storing program instructions that when executed by the at least one processor
执行存于 memory 的指令以实现数据目录。
来源 Chunk：US11423041B2-chunk-000

其余7篇的原文、Claim、source_id和邻边详见N019展开项及逐来源CSV。

### 3. 清楚的异义并置：Token（N017，3篇）

**US8655901B1 · Claim 1**
segmenting a given query among the collection into one or more tokens in the first language, wherein each token includes one or more terms from the given query
查询中的一段词语，按查询模式组件加标签，用于跨语言模式挖掘。
来源 Chunk：US8655901B1-chunk-000

**US9118735B1 · Claim 14**
anonymizing results based on replacing an identifier associated with the second user with a token
替换用户标识符的匿名化代用值。
来源 Chunk：US9118735B1-chunk-001

**US9218390B2 · Claim 18**
receiving an input query, wherein the input query comprises a series of tokens; assigning a label to each of a plurality of the tokens
地理搜索查询中的可标注单元，参与 CRF 模型构建。
来源 Chunk：US9218390B2-chunk-002

同一 `Token` 节点合入匿名化替代值与NLP查询词元两种含义。实际边193为 `Second User — Token`（仅US9118735B1），边251为 `Token — Label`（仅US8655901B1、US9218390B2）。共享节点因此允许形成跨语义路径；两条边在各自来源中仍有支持。

**没有新增或观察到一条“匿名用户必须具备查询标签”的直接边，也没有在本次运行查询证明错误答案传播。**这是一项可复核的词义区分／来源作用域风险，不能直接归为LightRAG代码bug。

## 邻边检查：语义混并与错误传播分开

266条相关实际边中，本次未确认由跨专利合并造成的不支持边或答案传播。实际跨专利来源的边只有4条：Weight—Characteristic、Token—Label、Processor—Memory、Tokens—Labels；来源子句需逐一解释，不能把任一合并描述都归给每一篇专利。

**另有3条源内角色警示：**US9514120B1 Claim18明确由 `server computing machine` 执行combine、sort、update；chunk002从句中间开始，保存的原抽取及图边495、502、517则使用 `Apparatus` 作动作主体。这是已观察的角色粒度不一致，最早出现在单专利原始抽取中。整体装置功能概括的解释仍需限定；不能归因于跨专利合并，也没有本次边界控制或新问答来证明因果传播。Apparatus节点本身仍归共享宽类。

## 逐节点总表

完整38项，非抽样。点击编号或向下展开可查所有来源、短引文与真实边端点。类型为保存原图中的entity_type，不把它当人工本体金标准。

| 编号 | 原节点 ID／label | 原图类型 | 专利数 | 最终类别 | 置信度 |
|---|---|---|---|---|---|
| [N001] | Data Processing System | artifact | 2 | 共享宽类 | 高 |
| [N002] | Mobile Device | artifact | 2 | 共享宽类 | 高 |
| [N003] | Server | artifact | 5 | 共享宽类 | 高 |
| [N004] | Database | artifact | 3 | 共享宽类 | 高 |
| [N005] | Communication Network | artifact | 2 | 共享宽类 | 高 |
| [N006] | Computer-Readable Storage Device | artifact | 2 | 共享宽类 | 高 |
| [N007] | System | artifact | 3 | 共享宽类 | 高 |
| [N008] | Keyword | data | 2 | 共享宽类 | 高 |
| [N009] | Weight | concept | 3 | 共享宽类 | 高 |
| [N010] | First User | person | 2 | 异义／角色并置 | 中 |
| [N011] | Second User | person | 2 | 异义／角色并置 | 中 |
| [N012] | Third User | person | 2 | 异义／角色并置 | 中 |
| [N013] | Characteristic | concept | 2 | 共享宽类 | 高 |
| [N014] | Computer Network | artifact | 2 | 共享宽类 | 高 |
| [N015] | Non-Transitory Computer Readable Medium | artifact | 2 | 共享宽类 | 高 |
| [N016] | Event | concept | 2 | 异义／角色并置 | 中 |
| [N017] | Token | concept | 3 | 异义／角色并置 | 高 |
| [N018] | Recommendation | concept | 2 | 共享宽类 | 高 |
| [N019] | Processor | artifact | 9 | 共享宽类 | 高 |
| [N020] | Memory | artifact | 5 | 共享宽类 | 高 |
| [N021] | Payment | concept | 2 | 共享宽类 | 高 |
| [N022] | Network | organization | 2 | 异义／角色并置 | 中 |
| [N023] | User | person | 5 | 共享宽类 | 高 |
| [N024] | Application | artifact | 2 | 共享宽类 | 高 |
| [N025] | User Interface | artifact | 3 | 共享宽类 | 高 |
| [N026] | Computing Device | artifact | 3 | 共享宽类 | 高 |
| [N027] | User Feedback | data | 2 | 共享宽类 | 高 |
| [N028] | Non-Transitory Computer-Readable Medium | artifact | 2 | 共享宽类 | 高 |
| [N029] | Users | person | 2 | 共享宽类 | 高 |
| [N030] | Apparatus | artifact | 2 | 共享宽类 | 中 |
| [N031] | Score | data | 2 | 共享宽类 | 高 |
| [N032] | Tokens | concept | 2 | 共享技术概念 | 高 |
| [N033] | Labels | concept | 2 | 共享技术概念 | 中 |
| [N034] | Label | concept | 2 | 共享技术概念 | 中 |
| [N035] | Query | concept | 2 | 共享宽类 | 高 |
| [N036] | Non-Transitory Computer Storage Medium | artifact | 2 | 共享宽类 | 高 |
| [N037] | Data Processing Apparatus | artifact | 2 | 共享宽类 | 高 |
| [N038] | Computing Devices | artifact | 2 | 共享宽类 | 高 |

## 完整证据展开

N001 · Data Processing System · 共享宽类 · 2 篇

**判定：**两篇都把该词用于执行数据处理的软件/计算机系统：一篇处理IP权利地理可视化，一篇依据用户兴趣与关键词权重选择广告。原文用途和局部系统不同，但计算机数据处理系统这一共同上位类足以解释同名节点；没有原文或图边证明二者是同一部署实例。

**类与实例：**共同的系统类别，非同一系统实例。合并描述以&lt;SEP&gt;并列各自任务，不能把所有组件同时断言给任一专利中的单一系统；共享节点仅产生潜在跨文档邻接。

**原图类型：**artifact；**置信度：**高；**文件：**US9298709B2.txt, US9304738B1.txt

**US9298709B2 · Claim 1**
A data processing system to visualise data from an IP rights database comprising:
以IP权利数据库为数据源，在地图可视区域内筛选并更新可视化的计算机系统。
来源 Chunk：US9298709B2-chunk-000

**US9304738B1 · Claim 13**
a data processing system having one or more processors and memory, the data processing system configured to:
接收广告兴趣信号、识别和加权关键词、排序并选择广告的处理系统。
来源 Chunk：US9304738B1-chunk-000, US9304738B1-chunk-001

**邻边审阅：**19条邻边全部按各自source_id分组复核：0–8为IP可视化；9–18为关键词广告选择。未发现把地图组件直接归因于广告专利的实际边。共享节点允许组合路径，但没有保存查询证明发生传播。

**局限：**['此为AI辅助逐条原文审阅，非独立人类gold，不使用模型评判API。', '类别判断针对共同概念/角色意义；原文没有给出跨专利实例等同或全部成员共享属性的本体断言。', '共享节点可能允许无来源约束的路径组合，但本审计未运行检索/生成，也不能把潜在风险报告成已发生的答案污染。', '抽取句的全部细粒度法律限定不在此四节点语义分类的穷尽验证范围；已记录的端点精度警示不等于确定错误。']

实际邻边端点、描述与来源（19 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 0 | US9298709B2 — Data Processing System | The patent publication US9298709B2 describes a data processing system to visualize data from an IP rights database. | US9298709B2<br>`US9298709B2-chunk-000` |
| 1 | Data Processing System — IP Rights Database | The data processing system visualizes data from the IP rights database. | US9298709B2<br>`US9298709B2-chunk-000` |
| 2 | Data Processing System — Geographic Map | The data processing system displays a geographic map having a viewable area. | US9298709B2<br>`US9298709B2-chunk-000` |
| 3 | Data Processing System — Map Display Change Monitor | The data processing system comprises the map display change monitor. | US9298709B2<br>`US9298709B2-chunk-000` |
| 4 | Data Processing System — IP Rights List Generator | The data processing system comprises the IP rights list generator. | US9298709B2<br>`US9298709B2-chunk-000` |
| 5 | Data Processing System — Information Display Generator | The data processing system comprises the information display generator. | US9298709B2<br>`US9298709B2-chunk-000` |
| 6 | Data Processing System — Restriction Criteria Interface | The data processing system comprises the restriction criteria interface. | US9298709B2<br>`US9298709B2-chunk-000` |
| 7 | Data Processing System — Geographic Map Display Interface | The data processing system comprises the geographic map display interface. | US9298709B2<br>`US9298709B2-chunk-000` |
| 8 | Data Processing System — Data Visualization Selector | The data processing system further comprises a data visualization selector. | US9298709B2<br>`US9298709B2-chunk-000` |
| 9 | Data Processing System — Parked Domain Web Page | The data processing system provides content for display with the parked domain web page.&lt;SEP&gt;The data processing system provides content and advertisements for display with the parked domain web page. | US9304738B1<br>`US9304738B1-chunk-000&lt;SEP&gt;US9304738B1-chunk-001` |
| 10 | Data Processing System — User Interest Indication | The data processing system receives an indication of user interest of a user in an advertisement displayed with a parked domain web page.&lt;SEP&gt;The data processing system receives indications of user interest in advertisements displayed on the parked domain web page. | US9304738B1<br>`US9304738B1-chunk-000&lt;SEP&gt;US9304738B1-chunk-001` |
| 11 | Data Processing System — Keyword | The data processing system identifies a plurality of keywords associated with an advertisement using the unique identifier and determines a weight of each keyword.&lt;SEP&gt;The data processing system identifies keywords of advertisements and determines a weight for each keyword. | US9304738B1<br>`US9304738B1-chunk-000&lt;SEP&gt;US9304738B1-chunk-001` |
| 12 | Data Processing System — Database | The data processing system accesses the database storing keywords and their weights.&lt;SEP&gt;The data processing system identifies keywords from the database and associates increased keyword weights with the parked domain web page in the database. | US9304738B1<br>`US9304738B1-chunk-000&lt;SEP&gt;US9304738B1-chunk-001` |
| 13 | Data Processing System — Content Request | The data processing system receives a request for content to provide for display with the parked domain web page. | US9304738B1<br>`US9304738B1-chunk-000` |
| 14 | Data Processing System — Keyword Ranking | The data processing system ranks keywords based on their weights to select a highest ranked keyword. | US9304738B1<br>`US9304738B1-chunk-000` |
| 15 | Data Processing System — Content Selection | The data processing system selects an advertisement to provide for display based on the highest ranked keyword. | US9304738B1<br>`US9304738B1-chunk-000` |
| 16 | Data Processing System — Advertisement | The data processing system selects an advertisement to provide for display with the parked domain web page based on the highest ranked keyword. | US9304738B1<br>`US9304738B1-chunk-001` |
| 17 | Data Processing System — Non-Transitory Computer Readable Medium | The non-transitory computer readable medium has instructions to evaluate information performed by the data processing system. | US9304738B1<br>`US9304738B1-chunk-001` |
| 18 | Data Processing System — Computer Network | The data processing system evaluates information via a computer network. | US9304738B1<br>`US9304738B1-chunk-001` |

N002 · Mobile Device · 共享宽类 · 2 篇

**判定：**两来源均使用移动终端类：一个产生短消息/查询并接收上下文数据，另一个带相机和屏幕进行社交人脸搜索。硬件配置与任务不同，但仍属于共同移动设备上位类，没有互斥词义或同一设备身份断言。

**类与实例：**共享移动设备类别，不代表两篇专利的设备实例相同，也不意味着全部移动设备必带相机。Smart Phone及Tablet等邻接应保留来源限定。

**原图类型：**artifact；**置信度：**高；**文件：**US8509827B2.txt, US8917913B2.txt

**US8509827B2 · Claim 1**
receiving a short message from a mobile device with a server;
产生短消息的移动终端；上下文类型描述其环境，Claim16允许该终端为智能手机。
来源 Chunk：US8509827B2-chunk-000

**US8917913B2 · Claim 1**
wherein the mobile device includes at least a camera and a screen
带相机、屏幕、应用和互联网接入的移动终端，向社交搜索服务发送输入并显示返回结果。
来源 Chunk：US8917913B2-chunk-000, US8917913B2-chunk-001

**邻边审阅：**13条邻边均已读：52、65、72对应上下文消息专利；73–82对应人脸/社交搜索专利。各边的source_id仍限定原专利，未观察到将camera属性明确标给上下文消息专利的边。

**局限：**['此为AI辅助逐条原文审阅，非独立人类gold，不使用模型评判API。', '类别判断针对共同概念/角色意义；原文没有给出跨专利实例等同或全部成员共享属性的本体断言。', '共享节点可能允许无来源约束的路径组合，但本审计未运行检索/生成，也不能把潜在风险报告成已发生的答案污染。', '抽取句的全部细粒度法律限定不在此四节点语义分类的穷尽验证范围；已记录的端点精度警示不等于确定错误。']

实际邻边端点、描述与来源（13 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 52 | Context-Data Acquisition And Ranking — Mobile Device | The method provides received context data to the mobile device that generated the short message or query. | US8509827B2<br>`US8509827B2-chunk-000` |
| 65 | Context-Data Type — Mobile Device | The context-data type provides information about the environment or context of the mobile device. | US8509827B2<br>`US8509827B2-chunk-000` |
| 72 | Mobile Device — Smart Phone | The mobile device that generated the short message may be a smart phone. | US8509827B2<br>`US8509827B2-chunk-000` |
| 73 | Mobile Device — Application | The application is associated with the mobile device and is in operative communication with its camera.&lt;SEP&gt;The application is associated with the mobile device. | US8917913B2<br>`US8917913B2-chunk-000&lt;SEP&gt;US8917913B2-chunk-001` |
| 74 | Mobile Device — Internet Access Mechanism | The Internet access mechanism is associated with the mobile device. | US8917913B2<br>`US8917913B2-chunk-000&lt;SEP&gt;US8917913B2-chunk-001` |
| 75 | Mobile Device — Search Service | The search service sends results back to the mobile device via the Internet access mechanism. | US8917913B2<br>`US8917913B2-chunk-000` |
| 76 | Mobile Device — Screen | The mobile device includes at least a screen. | US8917913B2<br>`US8917913B2-chunk-000` |
| 77 | Mobile Device — Camera | The mobile device includes at least a camera. | US8917913B2<br>`US8917913B2-chunk-000` |
| 78 | Mobile Device — Result | The search service sends the result back to the mobile device via the Internet access mechanism. | US8917913B2<br>`US8917913B2-chunk-001` |
| 79 | Mobile Device — Mobile Phone | The mobile device may be selected as a mobile phone. | US8917913B2<br>`US8917913B2-chunk-001` |
| 80 | Mobile Device — Tablet | The mobile device may be selected as a tablet. | US8917913B2<br>`US8917913B2-chunk-001` |
| 81 | Mobile Device — PDA | The mobile device may be selected as a PDA. | US8917913B2<br>`US8917913B2-chunk-001` |
| 82 | Mobile Device — Dedicated Camera | The mobile device may be selected as a dedicated camera. | US8917913B2<br>`US8917913B2-chunk-001` |

N003 · Server · 共享宽类 · 5 篇

**判定：**五来源都支持计算/服务端角色，分别承担邮件关系数据处理、上下文数据收集、社交网络找人、视频流传送和排字错误分类。服务内容不同并不构成server词义冲突；可归为广义服务端类别。Server→User Interface边的具体执行者较弱，单独记录而不升级为跨专利混并。

**类与实例：**共享服务端上位类；不等于一个服务器同时运行五个系统，也不能据此合并五项服务的身份。provider关联server与接收短消息server还可能是同一文档中的不同部署角色，来源原文未要求它们相同。

**原图类型：**artifact；**置信度：**高；**文件：**US10778629B2.txt, US8509827B2.txt, US9118735B1.txt, US9374411B1.txt, US9514120B1.txt

**US10778629B2 · Claim 21**
a server to: receive data comprising a plurality of characteristics of e-mail exchanges between pairs of users of the e-mail system,
从interaction database接收邮件交换特征、赋权并向processor传递数据的关系建模服务端。
来源 Chunk：US10778629B2-chunk-000, US10778629B2-chunk-001

**US8509827B2 · Claim 1**
receiving a short message from a mobile device with a server;
接收移动短消息并用于上下文数据收集的服务端；Claim22另述至少一个server从provider收集数据。
来源 Chunk：US8509827B2-chunk-000, US8509827B2-chunk-001

**US9118735B1 · ABSTRACT**
The server may then traverse that person's social network to identify someone who is in a similar location and who knows the person being sought.
接收找人请求、遍历请求者社交网络、寻找中介并返回标识或回应的服务器。
来源 Chunk：US9118735B1-chunk-000

**US9374411B1 · Claim 1**
stream a first video content feature from at least one server to a client associated with a user;
向用户client流式提供视频内容的服务端。
来源 Chunk：US9374411B1-chunk-000

**US9514120B1 · ABSTRACT**
A computing device hosting a server identifies one or more potential typographical errors in a work using an initial reference.
由computing device承载、参与作品排字错误识别及反馈处理的server。
来源 Chunk：US9514120B1-chunk-000

**邻边审阅：**12条实际邻边均按source_id核查。53/83为上下文处理，84–87为找人，88为host，89为视频传送，90–93为邮件关系数据。未发现被明确错误归源的跨专利新边；edge92只有UI显示事实，没有明确server执行该显示动作，标为端点语义强度警示。

**局限：**['此为AI辅助逐条原文审阅，非独立人类gold，不使用模型评判API。', '类别判断针对共同概念/角色意义；原文没有给出跨专利实例等同或全部成员共享属性的本体断言。', '共享节点可能允许无来源约束的路径组合，但本审计未运行检索/生成，也不能把潜在风险报告成已发生的答案污染。', '抽取句的全部细粒度法律限定不在此四节点语义分类的穷尽验证范围；已记录的端点精度警示不等于确定错误。']

实际邻边端点、描述与来源（12 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 53 | Context-Data Acquisition And Ranking — Server | The method is performed with a server that receives short messages and generates requests for context data. | US8509827B2<br>`US8509827B2-chunk-000` |
| 83 | Server — Context-Data Provider | At least one server is associated with the context-data provider.&lt;SEP&gt;A set of context data is collected from the context-data provider with at least one server. | US8509827B2<br>`US8509827B2-chunk-000&lt;SEP&gt;US8509827B2-chunk-001` |
| 84 | Server — US9118735B1 | The patent document describes a server that receives requests and traverses social networks to identify connecting persons. | US9118735B1<br>`US9118735B1-chunk-000` |
| 85 | Server — Requesting Person | The server sends an identifier associated with the connecting person, a response based on the connecting person's response, or a possible location of the target person to the requesting person's computer.&lt;SEP&gt;The requesting person sends a request to the server identifying himself or herself, the target person, and the requestor's location. | US9118735B1<br>`US9118735B1-chunk-000` |
| 86 | Server — Social Network | The server traverses the requesting person's social network to identify a connecting person. | US9118735B1<br>`US9118735B1-chunk-000` |
| 87 | Server — Connecting Person | The server determines an identifier associated with a connecting person in the requesting person's social network. | US9118735B1<br>`US9118735B1-chunk-000` |
| 88 | Server — Computing Device | The computing device hosts a server that performs typographical error classification. | US9514120B1<br>`US9514120B1-chunk-000` |
| 89 | Server — Client | The server streams the first video content feature to the client associated with the user. | US9374411B1<br>`US9374411B1-chunk-000` |
| 90 | Server — Interaction Database | The server receives data comprising characteristics of e-mail exchanges transferred from the interaction database.&lt;SEP&gt;Data comprising characteristics of e-mail exchanges is transferred to the server from an interaction database. | US10778629B2<br>`US10778629B2-chunk-000&lt;SEP&gt;US10778629B2-chunk-001` |
| 91 | Server — Processor | The server transfers the data to a processor for generating relationship data.&lt;SEP&gt;The server transfers data to a processor for generating relationship data. | US10778629B2<br>`US10778629B2-chunk-000&lt;SEP&gt;US10778629B2-chunk-001` |
| 92 | Server — User Interface | Relationship data is displayed on a user interface. | US10778629B2<br>`US10778629B2-chunk-000` |
| 93 | Server — Weight | The server assigns a weight to each of the plurality of characteristics for each pair of users. | US10778629B2<br>`US10778629B2-chunk-001` |

N004 · Database · 共享宽类 · 3 篇

**判定：**三来源都指可存储/查询数据的数据库：分别存备份管理数据、接收的上下文数据、广告关键词及权重。所存数据不同没有改变database的共同存储类意义，不能仅因邻居不同判定混并。

**类与实例：**共同数据库类别，非同一数据库实例、表或schema。所有数据类型不会因此自动属于每一专利的本地数据库；Artifact/Data类型标签差异属抽取类型粒度差异，未见异义。

**原图类型：**artifact；**置信度：**高；**文件：**US7756837B2.txt, US8509827B2.txt, US9304738B1.txt

**US7756837B2 · Claim 1**
storing the management data in a searchable format in a database
存储从备份数据流提取的management data，便于后续检索与查询的数据库。
来源 Chunk：US7756837B2-chunk-000, US7756837B2-chunk-001, US7756837B2-chunk-002, US7756837B2-chunk-003

**US8509827B2 · Claim 9**
storing the received context data in a database available to a recipient mobile device
接收移动设备可访问的上下文数据存储库，配合URI及元数据查询指令。
来源 Chunk：US8509827B2-chunk-000

**US9304738B1 · Claim 12**
accessing the database storing the plurality of keywords and a second plurality of keywords corresponding to advertisements previously displayed on the parked domain web page
将停放域名页面关联到广告关键词、权重等信息的数据库。
来源 Chunk：US9304738B1-chunk-000, US9304738B1-chunk-001

**邻边审阅：**9条实际邻边已全部核查：12、98、99的关键词/权重来源是US9304738B1；56、96上下文数据来源US8509827B2；100–103管理数据/processor/apparatus/method来源US7756837B2。未见明确把一种数据放到另一专利数据库的实际错误边；只有共享上位类节点的跨文档邻接。

**局限：**['此为AI辅助逐条原文审阅，非独立人类gold，不使用模型评判API。', '类别判断针对共同概念/角色意义；原文没有给出跨专利实例等同或全部成员共享属性的本体断言。', '共享节点可能允许无来源约束的路径组合，但本审计未运行检索/生成，也不能把潜在风险报告成已发生的答案污染。', '抽取句的全部细粒度法律限定不在此四节点语义分类的穷尽验证范围；已记录的端点精度警示不等于确定错误。']

实际邻边端点、描述与来源（9 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 12 | Data Processing System — Database | The data processing system accesses the database storing keywords and their weights.&lt;SEP&gt;The data processing system identifies keywords from the database and associates increased keyword weights with the parked domain web page in the database. | US9304738B1<br>`US9304738B1-chunk-000&lt;SEP&gt;US9304738B1-chunk-001` |
| 56 | Context-Data Acquisition And Ranking — Database | The method stores received context data in a database available to a recipient mobile device. | US8509827B2<br>`US8509827B2-chunk-000` |
| 96 | Recipient Mobile Device — Database | The database is available to the recipient mobile device for storing and querying received context data. | US8509827B2<br>`US8509827B2-chunk-000` |
| 98 | Database — Keyword | The database stores a plurality of keywords and their weights. | US9304738B1<br>`US9304738B1-chunk-001` |
| 99 | Database — Weight | The database associates the increased weight of a keyword with the parked domain web page having the unique identifier. | US9304738B1<br>`US9304738B1-chunk-001` |
| 100 | Database — Management Data | The management data is stored in a searchable format in a database for subsequent review and query.&lt;SEP&gt;The management data is stored in a searchable format in the database.&lt;SEP&gt;Management data is stored in a searchable format in the database. | US7756837B2<br>`US7756837B2-chunk-000&lt;SEP&gt;US7756837B2-chunk-002&lt;SEP&gt;US7756837B2-chunk-003` |
| 101 | Database — Processor | The processor stores the management data in a searchable format in a database. | US7756837B2<br>`US7756837B2-chunk-001` |
| 102 | Database — Apparatus | The apparatus comprises means for storing the management data in a searchable format in a database. | US7756837B2<br>`US7756837B2-chunk-001&lt;SEP&gt;US7756837B2-chunk-003` |
| 103 | Database — Method | The method comprises storing the management data in a searchable format in a database. | US7756837B2<br>`US7756837B2-chunk-003` |

N005 · Communication Network · 共享宽类 · 2 篇

**判定：**两篇都指承载电子数据通信的网络类别：一篇传输备份查询与回复，另一篇传输移动设备上下文数据并以网络状态作为排序参数。不同承载内容并未构成不相容词义。Internet只由US7756837B2支持，不应扩张到另一篇的所有网络。

**类与实例：**共享的是通信网络这一宽类，不是两篇实现中的同一物理网络，也不是所有通信网络等同Internet。合并节点汇集带来源的用途描述；没有同一个体等同声明。

**原图类型：**artifact；**置信度：**高；**文件：**US7756837B2.txt, US8509827B2.txt

**US7756837B2 · Claim 14**
wherein the query is received electronically over a communication network
备份数据检索中接收查询并向请求方发送回复的电子通信网络；从属Claim15将其限定为Internet。
来源 Chunk：US7756837B2-chunk-000, US7756837B2-chunk-001, US7756837B2-chunk-002

**US8509827B2 · Claim 13**
wherein the specified parameter comprises a state of an available communication network.
其网络状态可成为上下文数据排序参数；Claim19也用网络向移动设备传输上下文数据。
来源 Chunk：US8509827B2-chunk-000

**邻边审阅：**已核对全部4条实际邻边：95是上下文排序参数使用网络状态；110、111、112分别为电子回复、Internet和查询传输，来源均与相应Claims一致。111的is/may表述对应不同从属范围，不能作为所有来源网络必为Internet的断言。未观察到把US7756837B2的Internet限定写成US8509827B2专属事实的新增边。

**局限：**['AI辅助逐条审阅，不是独立人工gold；分类是概念/实例解释，不是LightRAG本体声明。', '只审查已保存来源、抽取记录和实际邻边；没有新查询或生成，不能推断潜在跨文档路径已经引起答案污染。', '相同source_id需结合原round2工作空间解释；合并description每个片段的细粒度来源需回查原抽取行。']

实际邻边端点、描述与来源（4 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 95 | Specified Parameter — Communication Network | The specified parameter may comprise a state of an available communication network. | US8509827B2<br>`US8509827B2-chunk-000` |
| 110 | Communication Network — Party | The party receives responses electronically over the communication network. | US7756837B2<br>`US7756837B2-chunk-000` |
| 111 | Communication Network — Internet | The communication network is the Internet.&lt;SEP&gt;The communication network may be the Internet. | US7756837B2<br>`US7756837B2-chunk-000&lt;SEP&gt;US7756837B2-chunk-001&lt;SEP&gt;US7756837B2-chunk-002` |
| 112 | Communication Network — Query | The query is received electronically over a communication network.&lt;SEP&gt;The query is received electronically over the communication network and responses are transmitted electronically over it. | US7756837B2<br>`US7756837B2-chunk-001&lt;SEP&gt;US7756837B2-chunk-002` |

N006 · Computer-Readable Storage Device · 共享宽类 · 2 篇

**判定：**计算机可读存储设备在两专利均为通用指令载体；同概念共享成立，但按本报告统一颗粒度，与Processor/Memory及其他通用存储介质归共享宽类。这只是C1/C2粒度统一，不是从成功改判错误。

**类与实例：**共同概念是可承载计算机可执行指令的存储设备类。这里的specific相对于泛称System，绝不主张同一介质实例、同一程序或同一任务。

**原图类型：**artifact；**置信度：**高；**文件：**US8719408B2.txt, US9514753B2.txt

**US8719408B2 · Claim 9**
A computer-readable storage device with an executable program stored thereon
存储对内容生产者关系进行监测并过滤/呈现数字媒体的可执行程序。
来源 Chunk：US8719408B2-chunk-000

**US9514753B2 · Claim 16**
A computer-readable storage device storing instructions that, when executed by one or more computers
存储执行话语向量哈希、候选说话人向量比较等识别操作的指令；也是Claim18系统组成。
来源 Chunk：US9514753B2-chunk-001

**邻边审阅：**全部6条实际邻边按来源核对：146/147属于说话人识别系统的指令执行及组成；148–151属于内容过滤程序的存储、呈现、关系建立和相关性权重计算。各边描述保留program code/指令层作用，没有实际边声称一个专利的存储设备运行另一专利全部算法。

**局限：**['AI辅助逐条审阅，不是独立人工gold；分类是概念/实例解释，不是LightRAG本体声明。', '只审查已保存来源、抽取记录和实际邻边；没有新查询或生成，不能推断潜在跨文档路径已经引起答案污染。', '相同source_id需结合原round2工作空间解释；合并description每个片段的细粒度来源需回查原抽取行。']

实际邻边端点、描述与来源（6 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 146 | Computer-Readable Storage Device — Computer | The storage device stores instructions that, when executed by one or more computers, cause the computers to perform operations. | US9514753B2<br>`US9514753B2-chunk-001` |
| 147 | Computer-Readable Storage Device — System | The system comprises a computer-readable storage device storing instructions. | US9514753B2<br>`US9514753B2-chunk-001` |
| 148 | Computer-Readable Storage Device — Executable Program | The computer-readable storage device stores an executable program thereon. | US8719408B2<br>`US8719408B2-chunk-000` |
| 149 | Computer-Readable Storage Device — Digital Media Content | The storage device contains executable program code for presenting digital media content. | US8719408B2<br>`US8719408B2-chunk-001` |
| 150 | Computer-Readable Storage Device — User Relationship | The storage device contains executable program code for establishing a plurality of user relationships. | US8719408B2<br>`US8719408B2-chunk-001` |
| 151 | Computer-Readable Storage Device — Relevancy Weight | The storage device contains executable program code for determining a relevancy weight for each published digital media content item. | US8719408B2<br>`US8719408B2-chunk-001` |

N007 · System · 共享宽类 · 3 篇

**判定：**三篇均为由计算部件执行程序的系统宽类，分别服务于内容界面辅助、翻译式查询模式挖掘和说话人识别。原抽取描述和各邻边分别保留其任务，未证实互不相容的System词义。

**类与实例：**每篇的system是本专利的局部系统实施例；共享类级ID不证明三者是同一个体或拥有彼此全部功能。以计算系统宽类解释足够，故不单凭应用不同判contextual_conflation。

**原图类型：**artifact；**置信度：**高；**文件：**US10867122B1.txt, US8655901B1.txt, US9514753B2.txt

**US10867122B1 · Claim 11**
A system comprising: one or more processors configured to execute computer program instructions;
根据用户正在输入的内容确定事实实体、提供相关界面内容，并响应输入插入内容的计算系统。
来源 Chunk：US10867122B1-chunk-001

**US8655901B1 · Claim 8**
A system comprising: one or more processors configured to interact with a computer-readable medium
执行查询模式匹配、标签注释、翻译及译后模式提取的计算系统。
来源 Chunk：US8655901B1-chunk-000

**US9514753B2 · Claim 18**
A system comprising: one or more computers; and a computer-readable storage device storing instructions
运行话语向量哈希与说话人向量比较的系统；共享类不等于与查询模式挖掘系统同一实例。
来源 Chunk：US9514753B2-chunk-001

**邻边审阅：**全部9条实际邻边已核对：147/152对应US9514753B2的存储设备/计算机；153/154对应US8655901B1的处理器/查询挖掘；155–159对应US10867122B1的处理器、指令和界面操作。157的chunk002以Claim14尾句开始，完整Claim14与相邻chunk001可补足主语；未把片段主语缺失误判为无原文支持边。

**局限：**['AI辅助逐条审阅，不是独立人工gold；分类是概念/实例解释，不是LightRAG本体声明。', '只审查已保存来源、抽取记录和实际邻边；没有新查询或生成，不能推断潜在跨文档路径已经引起答案污染。', '相同source_id需结合原round2工作空间解释；合并description每个片段的细粒度来源需回查原抽取行。']

实际邻边端点、描述与来源（9 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 147 | Computer-Readable Storage Device — System | The system comprises a computer-readable storage device storing instructions. | US9514753B2<br>`US9514753B2-chunk-001` |
| 152 | Computer — System | The system comprises one or more computers. | US9514753B2<br>`US9514753B2-chunk-001` |
| 153 | System — Processor | The system comprises one or more processors configured to interact with a computer-readable medium to perform operations. | US8655901B1<br>`US8655901B1-chunk-000` |
| 154 | System — Translation-Based Query Pattern Mining | The system is configured to perform operations comprising receiving a query pattern, identifying queries, annotating, translating, and extracting a translated query pattern. | US8655901B1<br>`US8655901B1-chunk-000` |
| 155 | System — Processors | The system comprises one or more processors configured to execute computer program instructions. | US10867122B1<br>`US10867122B1-chunk-001` |
| 156 | System — Computer Program Instructions | The system's processors execute computer program instructions to cause a computer device to perform operations. | US10867122B1<br>`US10867122B1-chunk-001` |
| 157 | System — User Interface Element | The system causes display of the updated content in the user interface element with the display environment. | US10867122B1<br>`US10867122B1-chunk-002` |
| 158 | System — Input Indication | The system receives an indication that the user device supplied input to the input element. | US10867122B1<br>`US10867122B1-chunk-002` |
| 159 | System — Content Portion | The system inserts a portion of the content displayed in the user interface element into the content of the display environment. | US10867122B1<br>`US10867122B1-chunk-002` |

N008 · Keyword · 共享宽类 · 2 篇

**判定：**两篇都以keyword表示与内容相关、用于索引/选择的词项。一篇是备份文件管理元数据中的索引关键词，另一篇是带页面特定权重的广告关键词；共同词项类别有原文依据，未显示不相容含义。

**类与实例：**共享的是内容描述/检索词项类别；不把某一备份文件的关键词集合与某广告的关键词集合视作相同实例。广告权重不是所有关键词的普遍属性。

**原图类型：**data；**置信度：**高；**文件：**US7756837B2.txt, US9304738B1.txt

**US7756837B2 · Claim 1**
keywords of the data files of the data-stream
数据流文件的内容关键词，作为可检索管理数据；对数据类型索引产生。
来源 Chunk：US7756837B2-chunk-000

**US9304738B1 · Claim 1**
a plurality of keywords of the first advertisement using the unique identifier of the parked domain web page
广告/信息资源关联词项，按页面的用户兴趣与历史表现赋权，用于广告选择。
来源 Chunk：US9304738B1-chunk-000

**邻边审阅：**全部7条邻边已核对：11/98/160/168/169为广告识别、存储、页面关联、权重和广告关联；170/171为备份management data与indexing。所有边按source_id可回到相应专利，未见把备份关键词直接断言为广告关键词的无依据边。跨两侧进行无来源约束路径拼接是风险，但本审阅未运行检索、未观察其传播。

**局限：**['AI辅助逐条审阅，不是独立人工gold；分类是概念/实例解释，不是LightRAG本体声明。', '只审查已保存来源、抽取记录和实际邻边；没有新查询或生成，不能推断潜在跨文档路径已经引起答案污染。', '相同source_id需结合原round2工作空间解释；合并description每个片段的细粒度来源需回查原抽取行。']

实际邻边端点、描述与来源（7 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 11 | Data Processing System — Keyword | The data processing system identifies a plurality of keywords associated with an advertisement using the unique identifier and determines a weight of each keyword.&lt;SEP&gt;The data processing system identifies keywords of advertisements and determines a weight for each keyword. | US9304738B1<br>`US9304738B1-chunk-000&lt;SEP&gt;US9304738B1-chunk-001` |
| 98 | Database — Keyword | The database stores a plurality of keywords and their weights. | US9304738B1<br>`US9304738B1-chunk-001` |
| 160 | Parked Domain Web Page — Keyword | Keywords are associated with advertisements displayed on the parked domain web page.&lt;SEP&gt;Keywords are associated with the parked domain web page and have weights specific to that page. | US9304738B1<br>`US9304738B1-chunk-000&lt;SEP&gt;US9304738B1-chunk-001` |
| 168 | Keyword — Weight | Each keyword has a weight determined based on user interest indications and historic performance.&lt;SEP&gt;Each keyword is assigned a weight determined based on user interest indications and historic performance. | US9304738B1<br>`US9304738B1-chunk-000&lt;SEP&gt;US9304738B1-chunk-001` |
| 169 | Keyword — Advertisement | An advertisement is associated with one or more keywords of the plurality of keywords.&lt;SEP&gt;Keywords are associated with advertisements displayed on the parked domain web page. | US9304738B1<br>`US9304738B1-chunk-000&lt;SEP&gt;US9304738B1-chunk-001` |
| 170 | Keyword — Management Data | The management data includes keywords of the data files of the data-stream. | US7756837B2<br>`US7756837B2-chunk-000` |
| 171 | Keyword — Indexing | Indexing at least one of the types of data obtains keywords thereof. | US7756837B2<br>`US7756837B2-chunk-000` |

N009 · Weight · 共享宽类 · 3 篇

**判定：**三篇的weight均为赋予对象的评分/相对重要性数值：对象分别是用户对的互动特征、推荐器和广告关键词；没有物理重量等不同词义。共同加权值类别足以解释合并，但不能互换三种权重的对象、单位或更新规则。

**类与实例：**共享类为计算中的权重值，文档局部实例分别是特征权重、推荐器权重和关键词权重。图未显式建立sameAs或声称这些数值相等。宽类节点的邻接不能作为跨应用参数可替代的证据。

**原图类型：**concept；**置信度：**高；**文件：**US10778629B2.txt, US7991757B2.txt, US9304738B1.txt

**US10778629B2 · Claim 20**
assigning a weight to each of the plurality of characteristics for each pair of users;
对每一用户对的邮件交互特征赋权，据此计算关系强度；Claim21由服务器赋值。
来源 Chunk：US10778629B2-chunk-001

**US7991757B2 · Claim 4**
applying weights to each of the recommenders; combining the scores with the weights to produce overall scores;
对推荐器赋权，与其推荐分数组合，并根据用户事件调整；可按用户分段特定化。
来源 Chunk：US7991757B2-chunk-000

**US9304738B1 · Claim 10**
assigning the weight to each of the plurality of keywords based on a number of user interactions
对页面广告关键词赋权，依据用户兴趣、历史表现、交互次数等，用于排序选广告。
来源 Chunk：US9304738B1-chunk-000

**邻边审阅：**已核对全部12条实际邻边。93/180对应关系强度特征赋权；176–179对应推荐器权重与分数、事件、用户分段；99/168/172/174/175对应关键词权重。173是实际跨专利合并边：同一Weight–Characteristic端点下，一段为关键词权重based on用户兴趣特征，另一段为用户对特征被assigned weight；两段各有原始抽取行与原文支持，source_id保留两个专利。它丢失统一谓词/论元粒度，需按段和来源解释，但尚不能称新增不受支持边或已发生检索/生成污染。

**局限：**['AI辅助逐条审阅，不是独立人工gold；分类是概念/实例解释，不是LightRAG本体声明。', '只审查已保存来源、抽取记录和实际邻边；没有新查询或生成，不能推断潜在跨文档路径已经引起答案污染。', '相同source_id需结合原round2工作空间解释；合并description每个片段的细粒度来源需回查原抽取行。']

实际邻边端点、描述与来源（12 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 93 | Server — Weight | The server assigns a weight to each of the plurality of characteristics for each pair of users. | US10778629B2<br>`US10778629B2-chunk-001` |
| 99 | Database — Weight | The database associates the increased weight of a keyword with the parked domain web page having the unique identifier. | US9304738B1<br>`US9304738B1-chunk-001` |
| 168 | Keyword — Weight | Each keyword has a weight determined based on user interest indications and historic performance.&lt;SEP&gt;Each keyword is assigned a weight determined based on user interest indications and historic performance. | US9304738B1<br>`US9304738B1-chunk-000&lt;SEP&gt;US9304738B1-chunk-001` |
| 172 | Weight — Historic Performance | The weight of a keyword is also determined based on historic performance on the parked domain web page.&lt;SEP&gt;Keyword weights are determined based also on historic performance on the parked domain web page. | US9304738B1<br>`US9304738B1-chunk-000&lt;SEP&gt;US9304738B1-chunk-001` |
| 173 | Weight — Characteristic | Keyword weights are determined based on a characteristic associated with user interest, such as temporal, day, content slot, monetary, or performance characteristics.&lt;SEP&gt;A weight is assigned to each of the plurality of characteristics for each pair of users. | US10778629B2, US9304738B1<br>`US9304738B1-chunk-000&lt;SEP&gt;US10778629B2-chunk-001` |
| 174 | Weight — User Interaction | Weights are assigned to keywords based on a number of user interactions with corresponding advertisements previously displayed on the parked domain web page. | US9304738B1<br>`US9304738B1-chunk-000` |
| 175 | Weight — User Interest Indication | The weight of a keyword is determined based on the indication of user interest in the corresponding advertisement. | US9304738B1<br>`US9304738B1-chunk-001` |
| 176 | Weight — Optimization Module | The optimization module assigns weights to the external recommenders. | US7991757B2<br>`US7991757B2-chunk-000` |
| 177 | Weight — Score | Scores are combined with weights to produce overall scores. | US7991757B2<br>`US7991757B2-chunk-000` |
| 178 | Weight — User-Generated Event | Weights for each recommender are adjusted based at least in part on user-generated events responsive to recommendations. | US7991757B2<br>`US7991757B2-chunk-000` |
| 179 | Weight — User Segment | User segment-specific weights are applied to at least some of the recommenders. | US7991757B2<br>`US7991757B2-chunk-000` |
| 180 | Weight — Relationship Strength | Relationship strength is determined based on the weight assigned to each of the plurality of characteristics for each pair of users. | US10778629B2<br>`US10778629B2-chunk-001` |

N010 · First User · 异义／角色并置 · 2 篇

**判定：**两篇原文中First User分别是社交寻人流程的发起者和广告权重学习中的第一兴趣提供者；first仅在各自文档内赋予指称作用域，不能跨专利用同一个序号判定角色对应。现图把两类具体角色描述和其邻边聚合为单一Person ID。共同User上位类可容纳两类人，但不足以保留First User这一有文档作用域的参与者角色语义；这里只认定作用域折叠，不认定现实个体同一或已发生错误传播。

**类与实例：**document-local participant role被折叠；不是现实中命名个体的同一性判断。若将节点专门重解释为“任一文档中的第一用户”宽类，则可以合法聚合，但现有图未明确声明该类、实例边或文档局部角色映射，不能用它连接两个场景中的特定参与者。此替代解释是medium置信度的主要原因。

**原图类型：**person；**置信度：**中；**文件：**US9118735B1.txt, US9304738B1.txt

**US9118735B1 · Claim 16**
for assisting a first user in finding a second user using a social network
寻人发起者；使用其位置和社交网络寻找第二用户，接收第三用户的标识或回应。
来源 Chunk：US9118735B1-chunk-001

**US9304738B1 · Claim 1**
an indication of user interest of a first user in a first advertisement displayed on a parked domain web page
对停放域名网页第一广告表现兴趣的用户；该兴趣参与关键词权重计算。
来源 Chunk：US9304738B1-chunk-000, US9304738B1-chunk-001, US9304738B1-chunk-002

**邻边审阅：**6条实际邻边按各自source_id均有本专利原文支持；广告边181仅源于US9304738B1，寻人/社交/位置边188–192仅源于US9118735B1。未观察到某条边把广告参与者直接断言为寻人发起者；共享节点允许不带来源作用域的跨文档路径组合，但没有读取到这种组合已进入检索/答案的证据。

**局限：**['AI辅助逐条原文审阅，非独立人工gold；未调用外部模型API。', '只判断保存快照中的角色/概念与实际邻边，不测试新查询，不据邻接推断已发生检索或生成传播。', '描述以SEP合并后没有句级来源标签；本文借原始抽取行复核句子来源，不能要求多源边的每个子句都被每个source支持。']

实际邻边端点、描述与来源（6 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 181 | First Advertisement — First User | The first user indicates interest in the first advertisement displayed with the parked domain web page.&lt;SEP&gt;The first user shows interest in the first advertisement displayed on the parked domain web page. | US9304738B1<br>`US9304738B1-chunk-000&lt;SEP&gt;US9304738B1-chunk-001` |
| 188 | First User — Second User | The first user is assisted in finding the second user using a social network. | US9118735B1<br>`US9118735B1-chunk-001` |
| 189 | First User — Social Network | The social network of the first user may be determined by combining a first social network and a second social network of different types, and traversed using the first user and second user as origins.&lt;SEP&gt;The social network of the first user is determined based on the identifier associated with the first user and can be traversed using the first user as an origin. | US9118735B1<br>`US9118735B1-chunk-001` |
| 190 | First User — Third User | The third user has a last-known location within a predetermined distance from the first user's location and has a number of degrees of separation and a type of relationship with the first user.&lt;SEP&gt;The last-known location of the third user and the location of the first user may be determined to be the same event or venue. | US9118735B1<br>`US9118735B1-chunk-001` |
| 191 | First User — Fourth User | The first user and the fourth user have a negative affinity, based on which a determination is made not to return the fourth user's identifier. | US9118735B1<br>`US9118735B1-chunk-001` |
| 192 | First User — Kiosk | The identifier associated with the first user is received at a kiosk having a pre-determined location. | US9118735B1<br>`US9118735B1-chunk-001` |

N011 · Second User · 异义／角色并置 · 2 篇

**判定：**Second User在US9118735B1中是被第一用户寻找、其标识可匿名化的目标；在US9304738B1中是第二广告的兴趣提供者。两角色的定义及关联行为都由文档内序号约束，而不是一个跨文档稳定技术角色。归为User宽类虽可容纳二者，却不能证明两个Second User占位符有对应身份或可互换，单一ID丢失了该局部角色作用域。未声称模型实际认定同一现实人。

**类与实例：**局部角色占位符，不是已知个体，也不是明确建模的全局“第二用户”本体类。contextual_conflation只用于该角色作用域碰撞；若调用方严格按来源把它当多态User宽类使用，可避免错误，故置信度medium。

**原图类型：**person；**置信度：**中；**文件：**US9118735B1.txt, US9304738B1.txt

**US9118735B1 · Claim 16**
for assisting a first user in finding a second user using a social network
被寻找的第二用户；关联标识可替换为token，可能位置可返回第一用户。
来源 Chunk：US9118735B1-chunk-001

**US9304738B1 · Claim 1**
an indication of user interest of a second user in a second advertisement displayed on the parked domain web page
对第二广告表现兴趣，兴趣用于第二关键词权重的用户。
来源 Chunk：US9304738B1-chunk-000, US9304738B1-chunk-001, US9304738B1-chunk-002

**邻边审阅：**3条实际边183（广告兴趣）、188（被寻找）、193（标识token匿名化）均可按实际source_id归属其专利并找到支持。没有一条边声称第二广告用户就是被找的人；不把单一节点邻接造成的潜在跨文档组合当作已观察的错误边。

**局限：**['AI辅助逐条原文审阅，非独立人工gold；未调用外部模型API。', '只判断保存快照中的角色/概念与实际邻边，不测试新查询，不据邻接推断已发生检索或生成传播。', '描述以SEP合并后没有句级来源标签；本文借原始抽取行复核句子来源，不能要求多源边的每个子句都被每个source支持。']

实际邻边端点、描述与来源（3 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 183 | Second Advertisement — Second User | The second user indicates interest in the second advertisement displayed on the parked domain web page.&lt;SEP&gt;The second user shows interest in the second advertisement displayed on the parked domain web page.&lt;SEP&gt;An indication of the second user's interest in the second advertisement is received. | US9304738B1<br>`US9304738B1-chunk-000&lt;SEP&gt;US9304738B1-chunk-001&lt;SEP&gt;US9304738B1-chunk-002` |
| 188 | First User — Second User | The first user is assisted in finding the second user using a social network. | US9118735B1<br>`US9118735B1-chunk-001` |
| 193 | Second User — Token | An identifier associated with the second user is replaced with a token to anonymize results. | US9118735B1<br>`US9118735B1-chunk-001` |

N012 · Third User · 异义／角色并置 · 2 篇

**判定：**Third User在一篇专利是区别于前两用户、其请求触发广告内容选择的接收者；在另一篇是位于第一用户社交网络、满足位置/同意共享条件的桥接者。third是文档局部角色名称，原文没有赋予跨场景统一角色定义。仅抽象为User会丢失“第三参与者”依赖具体流程的含义；现图的单一Person ID汇总了这些不应直接互换的局部角色。此为作用域折叠证据，不是同人断言或跨专利错误传播证据。

**类与实例：**同名局部角色，不是同一现实individual；共享User上位类本身合理，不能从中推出Third User实例或角色同一。没有独立schema约束禁止宽类解释，所以不把这个分类升格为确定的程序合并bug。

**原图类型：**person；**置信度：**中；**文件：**US9118735B1.txt, US9304738B1.txt

**US9118735B1 · Claim 16**
determining a third user in the social network of the first user who is likely to connect the social network of the first user with a social network of the third user
社交寻人中的第三用户/网络桥接者，具有邻近位置、分离度和opt-in共享约束。
来源 Chunk：US9118735B1-chunk-001

**US9304738B1 · Claim 1**
for a third user different from the first user and the second user, a request for content to provide for display with the parked domain web page
与前两兴趣提供用户不同的第三用户；接收与停放域名页面一起展示的内容，请求触发权重排序与广告选择。
来源 Chunk：US9304738B1-chunk-000, US9304738B1-chunk-001, US9304738B1-chunk-002

**邻边审阅：**11条实际边都保留专利source_id，逐项对应Claims7/16/17/20/21或广告Claims1/13/18。两套邻边聚合在同一Third User，但未出现“广告请求者一定是社交桥接者”这条实际边。没有任何原查询证明发生了这种错误传播。

**局限：**['AI辅助逐条原文审阅，非独立人工gold；未调用外部模型API。', '只判断保存快照中的角色/概念与实际邻边，不测试新查询，不据邻接推断已发生检索或生成传播。', '描述以SEP合并后没有句级来源标签；本文借原始抽取行复核句子来源，不能要求多源边的每个子句都被每个source支持。']

实际邻边端点、描述与来源（11 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 163 | Parked Domain Web Page — Third User | The third user requests content to provide for display with the parked domain web page. | US9304738B1<br>`US9304738B1-chunk-001` |
| 190 | First User — Third User | The third user has a last-known location within a predetermined distance from the first user's location and has a number of degrees of separation and a type of relationship with the first user.&lt;SEP&gt;The last-known location of the third user and the location of the first user may be determined to be the same event or venue. | US9118735B1<br>`US9118735B1-chunk-001` |
| 194 | Third User — Content Request | The third user requests content to provide for display with the parked domain web page. | US9304738B1<br>`US9304738B1-chunk-000` |
| 195 | Third User — Request For Content | The third user submits a request for content to provide for display with the parked domain web page. | US9304738B1<br>`US9304738B1-chunk-002` |
| 196 | Third User — Social Network | The third user is in the social network of the first user and is likely to connect the first user's social network with the third user's own social network. | US9118735B1<br>`US9118735B1-chunk-001` |
| 197 | Third User — Opt-In | The third user has opted in to sharing information about his or her identity, social network, or location with users of at least as many degrees of separation as the number of degrees of separation for the type of relationship with the first user. | US9118735B1<br>`US9118735B1-chunk-001` |
| 198 | Third User — Fourth User | The fourth user connects the first and third users, and the third user has at least two degrees of separation from the first user with the fourth user connecting them. | US9118735B1<br>`US9118735B1-chunk-001` |
| 199 | Third User — Geolocation | A geolocation may be provided by the computer of the third user. | US9118735B1<br>`US9118735B1-chunk-001` |
| 200 | Third User — Venue | The third user may have identified himself or herself as being at a venue. | US9118735B1<br>`US9118735B1-chunk-001` |
| 201 | Third User — Event | The third user may have identified himself or herself as being at an event. | US9118735B1<br>`US9118735B1-chunk-001` |
| 202 | Third User — Identifier | The identifier associated with the third user may comprise a name, image, or location of the third user, a relationship between the first user and the third user, or a relationship between the second user and the third user. | US9118735B1<br>`US9118735B1-chunk-001` |

N013 · Characteristic · 共享宽类 · 2 篇

**判定：**两来源均把Characteristic用作可测量/可描述的属性：一类用于广告用户兴趣与关键词权重，另一类用于邮件交流与关系强度。属性所属对象和取值不同，但都保留attribute这一共同宽类语义；没有证据要求它们是同一个特征实例、同一特征向量或相同计算规则。

**类与实例：**Concept宽类“属性/特征”，不是某个具体变量实例。可把邮件频率与广告时段视为不同属性类型，现有合并描述以SEP保留不同场景；不能因具体维度不相同就判定语义错合。

**原图类型：**concept；**置信度：**高；**文件：**US10778629B2.txt, US9304738B1.txt

**US10778629B2 · Claim 13**
the characteristic comprises at least one selected from a group consisting of interaction frequency, interaction type, and number of communication participants
邮件交互的属性（频率、类型、参与人数及时间/体量/双向比率）；各属性可赋权以估计用户关系强度。
来源 Chunk：US10778629B2-chunk-001

**US9304738B1 · Claim 6**
determining the weight of each of the plurality of keywords based on a characteristic associated with the user interest of the first user
广告用户兴趣的属性，用于关键词权重；可为时间、日期、页面位置、金钱或表现属性。
来源 Chunk：US9304738B1-chunk-000

**邻边审阅：**6条邻边均审阅。173是实际多源Weight—Characteristic边，两段描述分别是广告关键词权重基于兴趣属性、邮件属性被赋权；两个句子分别有对应来源，不要求每篇专利支持整段合并描述。211–215均来自邮件专利，未观察到把广告特征直接声明为邮件特征的无来源边；可能的无作用域路径组合仅属风险，不是已发生污染。

**局限：**['AI辅助逐条原文审阅，非独立人工gold；未调用外部模型API。', '只判断保存快照中的角色/概念与实际邻边，不测试新查询，不据邻接推断已发生检索或生成传播。', '描述以SEP合并后没有句级来源标签；本文借原始抽取行复核句子来源，不能要求多源边的每个子句都被每个source支持。']

实际邻边端点、描述与来源（6 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 173 | Weight — Characteristic | Keyword weights are determined based on a characteristic associated with user interest, such as temporal, day, content slot, monetary, or performance characteristics.&lt;SEP&gt;A weight is assigned to each of the plurality of characteristics for each pair of users. | US10778629B2, US9304738B1<br>`US9304738B1-chunk-000&lt;SEP&gt;US10778629B2-chunk-001` |
| 211 | Characteristic — E-Mail Exchange | The characteristics are attributes of e-mail exchanges between pairs of users, such as interaction frequency, interaction type, and time between interactions. | US10778629B2<br>`US10778629B2-chunk-001` |
| 212 | Characteristic — Calendar | Characteristics of e-mail exchanges between pairs of users may be further associated with the calendar medium. | US10778629B2<br>`US10778629B2-chunk-001` |
| 213 | Characteristic — Instant Messaging | Characteristics of e-mail exchanges between pairs of users may be further associated with the instant messaging medium. | US10778629B2<br>`US10778629B2-chunk-001` |
| 214 | Characteristic — SMS | Characteristics of e-mail exchanges between pairs of users may be further associated with the SMS medium. | US10778629B2<br>`US10778629B2-chunk-001` |
| 215 | Characteristic — Phone | Characteristics of e-mail exchanges between pairs of users may be further associated with the phone medium. | US10778629B2<br>`US10778629B2-chunk-001` |

N014 · Computer Network · 共享宽类 · 2 篇

**判定：**两篇均把 Computer Network 用作计算机系统传输或处理信息的网络。推荐器通信与广告信息评估属于不同应用，而非两种互不兼容的 network 词义；原抽取将一处标为 Concept、另一处标为 Artifact 只是类型粒度不一致，不能据此判为混并。

**类与实例：**共享计算机通信网络这一上位技术类；不是同一个网络部署，也不能把某篇专利的外部推荐器部署关系赋予另一篇。

**原图类型：**artifact；**置信度：**高；**文件：**US7991757B2.txt, US9304738B1.txt

**US7991757B2 · Claim 1**
query the plurality of external recommenders over the computer network for recommendations responsive to the second request
内容站点、推荐服务和外部推荐器之间请求/推荐的通信承载。
来源 Chunk：US7991757B2-chunk-000, US7991757B2-chunk-001

**US9304738B1 · Claim 13**
A system to evaluate information via a computer network
停放域名广告信息评估系统使用的计算机网络。
来源 Chunk：US9304738B1-chunk-001

**邻边审阅：**已逐条审阅实际邻边及其 source_id。未确认一条缺少其自身来源支持的边；合并后的跨文档邻接不能当成已发生错误边传播的证据。

**局限：**['这是 AI 辅助原文/抽取/图结构审阅，非独立人工标注 gold、非新的模型评判 API 实验。', '仅审核当前保存的第二轮图快照与其来源块；概念合并不等于实例 sameAs，也没有进行跨专利路径检索或答案生成传播实验。', '原文为已索引摘要及 Claims；没有用外部说明书填补缺失事实。原始文本中的格式缺陷保持原样。', '边的端点顺序来自保存的无向图；语义方向按原关系描述核对，不把 source/target 字段顺序当作因果方向。', 'observed_unsupported_edge=false 表示本次检查未确认无原文支持的实际边，不是证明全图无误；关键词粒度/局部实施例范围的警示另记。', '未给定显式类/实例 ontology。类别是基于具体词义及作用域的审阅标签，contextual_conflation 数量不是错误边数或代码 bug 率；Event/Network 的宽类解释可改变类别。', '缓存提取行未保存 finish_reason 时不推定完整或截断；本审核只对实际保存的实体/关系行与当前已入图事实作语义核验。']

实际邻边端点、描述与来源（3 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 18 | Data Processing System — Computer Network | The data processing system evaluates information via a computer network. | US9304738B1<br>`US9304738B1-chunk-001` |
| 216 | Computer Network — External Recommender | External recommenders are queried over the computer network for recommendations. | US7991757B2<br>`US7991757B2-chunk-000` |
| 217 | Computer Network — Network Service Interface | Requests are received over a computer network with a network service interface. | US7991757B2<br>`US7991757B2-chunk-001` |

N015 · Non-Transitory Computer Readable Medium · 共享宽类 · 2 篇

**判定：**非暂态计算机可读介质是通用指令载体，与N028的连字符拼写变体及N036同属宽泛计算载体类别；统一归共享宽类。保留原审阅，不以拼写决定具体概念等级。

**类与实例：**共享“含可执行指令的非暂态计算机可读介质”概念，而不是同一介质实例或同一组指令；某一介质的应用功能须保留其专利来源。

**原图类型：**artifact；**置信度：**高；**文件：**US10778629B2.txt, US9304738B1.txt

**US10778629B2 · Claim 1**
A non-transitory computer readable medium containing executable instructions that when executed perform a method of modeling relationships
执行邮件用户关系建模/关系数据生成方法的介质。
来源 Chunk：US10778629B2-chunk-000, US10778629B2-chunk-001

**US9304738B1 · Claim 18**
A non-transitory computer readable medium having instructions to evaluate information
执行停放域名广告关键词权重评估的介质。
来源 Chunk：US9304738B1-chunk-001, US9304738B1-chunk-002

**邻边审阅：**已逐条审阅实际邻边及其 source_id。未确认一条缺少其自身来源支持的边；合并后的跨文档邻接不能当成已发生错误边传播的证据。

**局限：**['这是 AI 辅助原文/抽取/图结构审阅，非独立人工标注 gold、非新的模型评判 API 实验。', '仅审核当前保存的第二轮图快照与其来源块；概念合并不等于实例 sameAs，也没有进行跨专利路径检索或答案生成传播实验。', '原文为已索引摘要及 Claims；没有用外部说明书填补缺失事实。原始文本中的格式缺陷保持原样。', '边的端点顺序来自保存的无向图；语义方向按原关系描述核对，不把 source/target 字段顺序当作因果方向。', 'observed_unsupported_edge=false 表示本次检查未确认无原文支持的实际边，不是证明全图无误；关键词粒度/局部实施例范围的警示另记。', '未给定显式类/实例 ontology。类别是基于具体词义及作用域的审阅标签，contextual_conflation 数量不是错误边数或代码 bug 率；Event/Network 的宽类解释可改变类别。', '缓存提取行未保存 finish_reason 时不推定完整或截断；本审核只对实际保存的实体/关系行与当前已入图事实作语义核验。']

实际邻边端点、描述与来源（4 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 17 | Data Processing System — Non-Transitory Computer Readable Medium | The non-transitory computer readable medium has instructions to evaluate information performed by the data processing system. | US9304738B1<br>`US9304738B1-chunk-001` |
| 167 | Parked Domain Web Page — Non-Transitory Computer Readable Medium | The non-transitory computer readable medium stores instructions relating to the parked domain web page keyword weighting. | US9304738B1<br>`US9304738B1-chunk-002` |
| 218 | Non-Transitory Computer Readable Medium — Relationship Modeling Program | The non-transitory computer readable medium contains executable instructions that when executed perform a method of modeling relationships using the relationship modeling program. | US10778629B2<br>`US10778629B2-chunk-000` |
| 219 | Non-Transitory Computer Readable Medium — Relationship Data | The non-transitory computer readable medium contains executable instructions that when executed perform a method of generating relationship data. | US10778629B2<br>`US10778629B2-chunk-001` |

N016 · Event · 异义／角色并置 · 2 篇

**判定：**原文明确呈现两种 event 语义：US11423041B2 中是注册到历史对象、按条件触发并使 ETL 作业执行的数据处理事件；US9118735B1 中是用户声称正在参加、可据以定位的活动/事件。当前单一 Event ID 的描述并列了这两种角色，邻边也将地理位置/人员出席与订阅/触发关系接在同一节点。它们可以同属极抽象的“发生事项”，但这个上位类不足以支持当前具体关系角色的互换；本分类是语义区分需求，非已有错误推理证明。

**类与实例：**可以显式建立 occurrence/event 上位类，并保留数据处理事件与人参加的活动这两个上下文意义或子类。图中没有给定正式 ontology，因而 C3 表示当前单 ID 中具体意义/作用域被折叠的审阅判断，不等于证明类合并错误；若预设节点即宽类，则 shared_broad_class 也是合理解释。不主张任一专利内多个事件是同一实例，也不将跨来源邻接视为人物参加 ETL 事件的事实。

**原图类型：**concept；**置信度：**中；**文件：**US11423041B2.txt, US9118735B1.txt

**US11423041B2 · Claim 1**
criteria for triggering an event to perform a second ETL process subscribed to the event
历史对象的被监控触发事件，触发订阅的 ETL 处理并可发送通知。
来源 Chunk：US11423041B2-chunk-000, US11423041B2-chunk-001

**US9118735B1 · Claim 7**
an event that the third user has identified himself or herself as being at
用户所处/参加的活动，作为 last-known location 的依据。
来源 Chunk：US9118735B1-chunk-000, US9118735B1-chunk-001

**邻边审阅：**9 条邻边按自己的来源都可找到对应陈述。未发现实际的“Third User 触发 ETL”或“ETL Event 是地理场所”边；这种路径只可能在忽略上下文后被组合，未运行检索/生成验证。

**局限：**['这是 AI 辅助原文/抽取/图结构审阅，非独立人工标注 gold、非新的模型评判 API 实验。', '仅审核当前保存的第二轮图快照与其来源块；概念合并不等于实例 sameAs，也没有进行跨专利路径检索或答案生成传播实验。', '原文为已索引摘要及 Claims；没有用外部说明书填补缺失事实。原始文本中的格式缺陷保持原样。', '边的端点顺序来自保存的无向图；语义方向按原关系描述核对，不把 source/target 字段顺序当作因果方向。', 'observed_unsupported_edge=false 表示本次检查未确认无原文支持的实际边，不是证明全图无误；关键词粒度/局部实施例范围的警示另记。', '未给定显式类/实例 ontology。类别是基于具体词义及作用域的审阅标签，contextual_conflation 数量不是错误边数或代码 bug 率；Event/Network 的宽类解释可改变类别。', '缓存提取行未保存 finish_reason 时不推定完整或截断；本审核只对实际保存的实体/关系行与当前已入图事实作语义核验。']

实际邻边端点、描述与来源（9 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 201 | Third User — Event | The third user may have identified himself or herself as being at an event. | US9118735B1<br>`US9118735B1-chunk-001` |
| 239 | Last-Known Location — Event | The last-known location of the connecting person may be determined based on an event the connecting person has identified himself or herself as being at. | US9118735B1<br>`US9118735B1-chunk-000` |
| 240 | Event — ETL Process | A second ETL process subscribed to the event is caused to be performed when the event is triggered. | US11423041B2<br>`US11423041B2-chunk-000` |
| 241 | Event — History Object | The event is registered for monitoring with regard to the history object. | US11423041B2<br>`US11423041B2-chunk-000&lt;SEP&gt;US11423041B2-chunk-001` |
| 242 | Event — Subscriber | A notification of the event is sent to one or more subscribers for the event. | US11423041B2<br>`US11423041B2-chunk-000` |
| 243 | Event — Criteria | Satisfying the criteria for triggering an event causes the event to be triggered.&lt;SEP&gt;The criteria are evaluated to determine whether the event should be triggered. | US11423041B2<br>`US11423041B2-chunk-000&lt;SEP&gt;US11423041B2-chunk-001` |
| 244 | Event — Second ETL Process | The second ETL process is subscribed to the event to be performed when the event is triggered. | US11423041B2<br>`US11423041B2-chunk-001` |
| 245 | Event — Data Catalog | The data catalog determines that the performance of the first ETL process satisfies the criteria for triggering the event. | US11423041B2<br>`US11423041B2-chunk-001` |
| 246 | Event — Notification | The notification communicates the event to another subscriber. | US11423041B2<br>`US11423041B2-chunk-001` |

N017 · Token · 异义／角色并置 · 3 篇

**判定：**US8655901B1 和 US9218390B2 的 token 是输入查询的一段/单元，可被分词、标注标签并用于查询模型；US9118735B1 Claim 14 的 token 则是替换第二用户标识符以匿名化结果的代用值。当前单一 ID 合并这两个具体意义。可把它们抽象为数据值，但不足以支持将查询分词/标签关系用于匿名替代标识；两篇查询专利相互共享词元概念是有依据的。

**类与实例：**同名词义混合而非证明 token 实例相等。查询词元子类和匿名替代标识子类须区分；Token—Label 这条跨两篇查询专利的边本身仍有支持。

**原图类型：**concept；**置信度：**高；**文件：**US8655901B1.txt, US9118735B1.txt, US9218390B2.txt

**US8655901B1 · Claim 1**
segmenting a given query among the collection into one or more tokens in the first language, wherein each token includes one or more terms from the given query
查询中的一段词语，按查询模式组件加标签，用于跨语言模式挖掘。
来源 Chunk：US8655901B1-chunk-000

**US9118735B1 · Claim 14**
anonymizing results based on replacing an identifier associated with the second user with a token
替换用户标识符的匿名化代用值。
来源 Chunk：US9118735B1-chunk-001

**US9218390B2 · Claim 18**
receiving an input query, wherein the input query comprises a series of tokens; assigning a label to each of a plurality of the tokens
地理搜索查询中的可标注单元，参与 CRF 模型构建。
来源 Chunk：US9218390B2-chunk-002

**邻边审阅：**7 条实际邻边的来源均可支持其本地关系。未观察到匿名化 token 被直接加上查询标签或 CRF 角色的实际边；跨来源路径组合风险未转化为已验证的错误检索或答案。

**局限：**['这是 AI 辅助原文/抽取/图结构审阅，非独立人工标注 gold、非新的模型评判 API 实验。', '仅审核当前保存的第二轮图快照与其来源块；概念合并不等于实例 sameAs，也没有进行跨专利路径检索或答案生成传播实验。', '原文为已索引摘要及 Claims；没有用外部说明书填补缺失事实。原始文本中的格式缺陷保持原样。', '边的端点顺序来自保存的无向图；语义方向按原关系描述核对，不把 source/target 字段顺序当作因果方向。', 'observed_unsupported_edge=false 表示本次检查未确认无原文支持的实际边，不是证明全图无误；关键词粒度/局部实施例范围的警示另记。', '未给定显式类/实例 ontology。类别是基于具体词义及作用域的审阅标签，contextual_conflation 数量不是错误边数或代码 bug 率；Event/Network 的宽类解释可改变类别。', '缓存提取行未保存 finish_reason 时不推定完整或截断；本审核只对实际保存的实体/关系行与当前已入图事实作语义核验。']

实际邻边端点、描述与来源（7 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 193 | Second User — Token | An identifier associated with the second user is replaced with a token to anonymize results. | US9118735B1<br>`US9118735B1-chunk-001` |
| 249 | Token — Anonymized Results | The anonymized results are encrypted after replacing the second user's identifier with a token. | US9118735B1<br>`US9118735B1-chunk-001` |
| 250 | Token — Unstructured Geographic Web-Search Query | The unstructured geographic web-search query comprises a series of tokens. | US9218390B2<br>`US9218390B2-chunk-002` |
| 251 | Token — Label | A label is assigned to each of a plurality of the tokens.&lt;SEP&gt;The one or more tokens are annotated with labels for the corresponding components of the first query pattern. | US8655901B1, US9218390B2<br>`US9218390B2-chunk-002&lt;SEP&gt;US8655901B1-chunk-000` |
| 252 | Token — Conditional Random Field Model | The conditional random field model is created based at least in part on the tokens. | US9218390B2<br>`US9218390B2-chunk-002` |
| 253 | Token — Query | A given query among the collection is segmented into one or more tokens in the first language. | US8655901B1<br>`US8655901B1-chunk-000` |
| 254 | Token — Query Pattern | Each of the one or more tokens is associated with corresponding components of the first query pattern. | US8655901B1<br>`US8655901B1-chunk-000` |

N018 · Recommendation · 共享宽类 · 2 篇

**判定：**一篇处理社交成员对商品的推荐并排序，另一篇基于角色偏好生成观看内容的推荐。来源对象和生成主体不同，但均支持“建议/推荐某项内容或物品”这个共同类。原文没有证明这些推荐是同一对象，当前描述也不要求该等同性，故不能仅因人工推荐与算法推荐不同而判同名错合并。

**类与实例：**共享推荐信息这一宽类；保留成员作出的推荐和系统生成的内容推荐的子角色与各自实例。

**原图类型：**concept；**置信度：**高；**文件：**US8095432B1.txt, US9374411B1.txt

**US8095432B1 · Claim 1**
obtaining a first recommendation for the item from a first member of a social networking utility
社交成员针对商品给出的推荐，按与询问成员的关系接近程度排序。
来源 Chunk：US8095432B1-chunk-000

**US9374411B1 · Claim 1**
send to the user a recommendation to play the second video content feature
根据角色偏好和关系分数给用户生成/发送内容观看推荐。
来源 Chunk：US9374411B1-chunk-000, US9374411B1-chunk-001

**邻边审阅：**已逐条审阅实际邻边及其 source_id。未确认一条缺少其自身来源支持的边；合并后的跨文档邻接不能当成已发生错误边传播的证据。

**局限：**['这是 AI 辅助原文/抽取/图结构审阅，非独立人工标注 gold、非新的模型评判 API 实验。', '仅审核当前保存的第二轮图快照与其来源块；概念合并不等于实例 sameAs，也没有进行跨专利路径检索或答案生成传播实验。', '原文为已索引摘要及 Claims；没有用外部说明书填补缺失事实。原始文本中的格式缺陷保持原样。', '边的端点顺序来自保存的无向图；语义方向按原关系描述核对，不把 source/target 字段顺序当作因果方向。', 'observed_unsupported_edge=false 表示本次检查未确认无原文支持的实际边，不是证明全图无误；关键词粒度/局部实施例范围的警示另记。', '未给定显式类/实例 ontology。类别是基于具体词义及作用域的审阅标签，contextual_conflation 数量不是错误边数或代码 bug 率；Event/Network 的宽类解释可改变类别。', '缓存提取行未保存 finish_reason 时不推定完整或截断；本审核只对实际保存的实体/关系行与当前已入图事实作语义核验。']

实际邻边端点、描述与来源（9 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 281 | Third Member — Recommendation | The third member may receive a third recommendation of the item from the inquiring member and provides a third recommendation. | US8095432B1<br>`US8095432B1-chunk-000` |
| 287 | Recommendation — Recommendation Application | The recommendation application obtains first and second recommendations for an item from members. | US8095432B1<br>`US8095432B1-chunk-000` |
| 288 | Recommendation — Item | Each recommendation is an endorsement of the item provided by a member. | US8095432B1<br>`US8095432B1-chunk-000` |
| 289 | Recommendation — Recommendation List | The recommendation list comprises the first and second recommendations, with the first ranked higher than the second. | US8095432B1<br>`US8095432B1-chunk-000` |
| 290 | Recommendation — Inventory Details | The inventory details are associated with the first and second recommendations. | US8095432B1<br>`US8095432B1-chunk-000` |
| 291 | Recommendation — Interests | Common and differing interests are compared when ranking recommendations of members. | US8095432B1<br>`US8095432B1-chunk-000` |
| 292 | Recommendation — Second Video Content Feature | The recommendation is sent to the user to play the second video content feature. | US9374411B1<br>`US9374411B1-chunk-000` |
| 293 | Recommendation — User | The recommendation to play the second video content feature is sent to the user.&lt;SEP&gt;The recommendation is generated for another user in response to the user specifying a preference for a character. | US9374411B1<br>`US9374411B1-chunk-000&lt;SEP&gt;US9374411B1-chunk-001` |
| 294 | Recommendation — Computing Device | The computing device sends a recommendation for presentation of the second network content. | US9374411B1<br>`US9374411B1-chunk-001` |

N019 · Processor · 共享宽类 · 9 篇

**判定：**已逐一审阅 9 篇、14 个来源块。每篇均直接使用 processor(s) 执行其方法或指令：关系数据生成、ETL、归档、垃圾邮件过滤、推荐、查询翻译、媒体过滤、广告库存估计、诊断辅助。它们支持相同的计算处理硬件/执行元件类；应用动作不同不构成不同词义。合并描述显式采用 across various system contexts 及 may be 等范围语句，未证实把九个实例宣称为同一物理处理器。

**类与实例：**共享处理器类而非同一硬件实例；25 条邻边都是来源限定的应用/组件角色。Processor—Memory 的多源关系为常见耦合/执行关系，不能由此推断九篇系统共享一块内存或处理器。

**原图类型：**artifact；**置信度：**高；**文件：**US10778629B2.txt, US11423041B2.txt, US7756837B2.txt, US8069128B2.txt, US8095432B1.txt, US8655901B1.txt, US8719408B2.txt, US8880423B2.txt, US9589231B2.txt

**US10778629B2 · Claim 10**
transferring, from the server, the data to a processor for generating relationship data by determining a relationship strength associated with each pair of users
接收服务器传来的数据并生成用户对关系强度/关系数据。
来源 Chunk：US10778629B2-chunk-000, US10778629B2-chunk-001

**US11423041B2 · Claim 1**
a memory, storing program instructions that when executed by the at least one processor
执行存于 memory 的指令以实现数据目录。
来源 Chunk：US11423041B2-chunk-000

**US7756837B2 · Claim 16**
A processor operable to execute a software program, the software program causing the processor to perform steps
运行归档程序：接收数据流、抽取管理数据、存储、查询。
来源 Chunk：US7756837B2-chunk-000, US7756837B2-chunk-001, US7756837B2-chunk-002

**US8069128B2 · Claim 1**
a processor that is operative to perform actions
网络设备内执行两遍消息分析及模型清除的处理器。
来源 Chunk：US8069128B2-chunk-000

**US8095432B1 · Claim 16**
a recommendation application executing on the processor, resident in memory
推荐系统中执行应用、计算关系接近度与排序的处理器。
来源 Chunk：US8095432B1-chunk-000, US8095432B1-chunk-001

**US8655901B1 · Claim 8**
one or more processors configured to interact with a computer-readable medium in order to perform operations
执行查询模式翻译挖掘操作、与计算机可读介质交互的处理器。
来源 Chunk：US8655901B1-chunk-000

**US8719408B2 · Claim 17**
a processor coupled to memory, the processor programmed by program code stored in the memory
建立用户关系并实施数字媒体过滤各模块的处理器。
来源 Chunk：US8719408B2-chunk-000, US8719408B2-chunk-001

**US8880423B2 · Claim 1**
clustering, using a processor, a plurality of viewed pages into a plurality of clusters
聚类浏览页面/关键词并估计广告库存的处理器。
来源 Chunk：US8880423B2-chunk-000

**US9589231B2 · Claim 20**
a processor in communication with the memory for executing the instructions
诊断辅助系统中执行查询/嵌入等指令的处理器。
来源 Chunk：US9589231B2-chunk-001

**邻边审阅：**已逐条审阅实际邻边及其 source_id。未确认一条缺少其自身来源支持的边；合并后的跨文档邻接不能当成已发生错误边传播的证据。

**局限：**['这是 AI 辅助原文/抽取/图结构审阅，非独立人工标注 gold、非新的模型评判 API 实验。', '仅审核当前保存的第二轮图快照与其来源块；概念合并不等于实例 sameAs，也没有进行跨专利路径检索或答案生成传播实验。', '原文为已索引摘要及 Claims；没有用外部说明书填补缺失事实。原始文本中的格式缺陷保持原样。', '边的端点顺序来自保存的无向图；语义方向按原关系描述核对，不把 source/target 字段顺序当作因果方向。', 'observed_unsupported_edge=false 表示本次检查未确认无原文支持的实际边，不是证明全图无误；关键词粒度/局部实施例范围的警示另记。', '未给定显式类/实例 ontology。类别是基于具体词义及作用域的审阅标签，contextual_conflation 数量不是错误边数或代码 bug 率；Event/Network 的宽类解释可改变类别。', '缓存提取行未保存 finish_reason 时不推定完整或截断；本审核只对实际保存的实体/关系行与当前已入图事实作语义核验。']

实际邻边端点、描述与来源（25 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 91 | Server — Processor | The server transfers the data to a processor for generating relationship data.&lt;SEP&gt;The server transfers data to a processor for generating relationship data. | US10778629B2<br>`US10778629B2-chunk-000&lt;SEP&gt;US10778629B2-chunk-001` |
| 101 | Database — Processor | The processor stores the management data in a searchable format in a database. | US7756837B2<br>`US7756837B2-chunk-001` |
| 153 | System — Processor | The system comprises one or more processors configured to interact with a computer-readable medium to perform operations. | US8655901B1<br>`US8655901B1-chunk-000` |
| 258 | Recommendation Engine For Social Networks — Processor | The recommendation engine operates using a processor to determine proximities and rank recommendations. | US8095432B1<br>`US8095432B1-chunk-000` |
| 302 | Processor — Recommendation Application | The recommendation application executes on the processor. | US8095432B1<br>`US8095432B1-chunk-000&lt;SEP&gt;US8095432B1-chunk-001` |
| 303 | Processor — Memory | The memory is operatively connected to the processor.&lt;SEP&gt;The processor is coupled to memory and programmed by program code stored in the memory.&lt;SEP&gt;The at least one processor executes program instructions stored in the memory.&lt;SEP&gt;The processor is in communication with the memory for executing the instructions. | US11423041B2, US8095432B1, US8719408B2, US9589231B2<br>`US8095432B1-chunk-001&lt;SEP&gt;US8719408B2-chunk-001&lt;SEP&gt;US11423041B2-chunk-000&lt;SEP&gt;US9589231B2-chunk-001` |
| 304 | Processor — US8880423B2 | The patent's methods use a processor to perform clustering and estimating steps. | US8880423B2<br>`US8880423B2-chunk-000` |
| 305 | Processor — Cluster | The processor clusters viewed pages and search keywords into clusters. | US8880423B2<br>`US8880423B2-chunk-000` |
| 306 | Processor — Total Inventory | The processor estimates the plurality of total inventories. | US8880423B2<br>`US8880423B2-chunk-000` |
| 307 | Processor — Deliverable Inventory | The processor estimates the deliverable inventory for the segment. | US8880423B2<br>`US8880423B2-chunk-000` |
| 308 | Processor — Network Device | The network device comprises a processor operative to perform the described actions. | US8069128B2<br>`US8069128B2-chunk-000` |
| 309 | Processor — Software Program | The processor is operable to execute the software program, which causes the processor to perform the archiving steps.&lt;SEP&gt;The processor is operable to execute the software program.&lt;SEP&gt;The software program is capable of causing the processor to carry out actions. | US7756837B2<br>`US7756837B2-chunk-000&lt;SEP&gt;US7756837B2-chunk-001&lt;SEP&gt;US7756837B2-chunk-002` |
| 310 | Processor — Management Data | The processor extracts management data from the data-stream. | US7756837B2<br>`US7756837B2-chunk-001` |
| 311 | Processor — Data-Stream | The processor receives at least one data-stream intended for archiving on a backup storage device. | US7756837B2<br>`US7756837B2-chunk-001` |
| 312 | Processor — Backup Storage Device | The processor passes the data-stream to the backup storage device and reads back data from it to re-create the data-stream. | US7756837B2<br>`US7756837B2-chunk-001` |
| 313 | Processor — Query | The processor receives a query from a party and formulates responses based on analysis of the management data stored in the database. | US7756837B2<br>`US7756837B2-chunk-001` |
| 314 | Processor — Predetermined Rule Set | The processor uses a predetermined rule set to recognize the distinct data sets of the data-stream. | US7756837B2<br>`US7756837B2-chunk-001` |
| 315 | Processor — Automated Digital Media Content Filtration | The filtration method is performed by a processor. | US8719408B2<br>`US8719408B2-chunk-000` |
| 316 | Processor — Executable Program | The executable program instructs a processor to perform the filtration steps. | US8719408B2<br>`US8719408B2-chunk-000` |
| 317 | Processor — Apparatus For Automated Digital Media Content Filtration | The apparatus comprises a processor coupled to memory. | US8719408B2<br>`US8719408B2-chunk-001` |
| 318 | Processor — Computer-Readable Medium | The one or more processors are configured to interact with a computer-readable medium in order to perform operations. | US8655901B1<br>`US8655901B1-chunk-000` |
| 319 | Processor — Data Catalog | The at least one processor implements the data catalog by executing program instructions. | US11423041B2<br>`US11423041B2-chunk-000` |
| 320 | Processor — Relationship Strength | The processor generates relationship data by determining a relationship strength associated with each pair of users. | US10778629B2<br>`US10778629B2-chunk-000` |
| 321 | Processor — Relationship Data | The processor generates relationship data by determining relationship strength associated with each pair of users. | US10778629B2<br>`US10778629B2-chunk-001` |
| 322 | Processor — Diagnosis Assistance System | The diagnosis assistance system comprises a processor in communication with the memory. | US9589231B2<br>`US9589231B2-chunk-001` |

N020 · Memory · 共享宽类 · 5 篇

**判定：**已逐一审阅 5 篇、6 个来源块。Memory 均为系统/装置中与处理元件相联的计算机存储组件；四篇明确存指令/程序，US9514120B1 Claim 18 仅明确 memory 与 processing device 的耦合。因此共同类是存储组件，不扩张为五篇都明确具有相同存储内容或同一内存实例。

**类与实例：**共享内存/存储部件类，不是跨专利同一对象。不同存储程序只是局部用途；US9514120B1 未明确的内容不由其他来源补足。

**原图类型：**artifact；**置信度：**高；**文件：**US11423041B2.txt, US8095432B1.txt, US8719408B2.txt, US9514120B1.txt, US9589231B2.txt

**US11423041B2 · Claim 1**
a memory, storing program instructions that when executed by the at least one processor
存储实现数据目录的程序指令。
来源 Chunk：US11423041B2-chunk-000

**US8095432B1 · Claim 16**
a memory operatively connected to the processor
与处理器相连且驻留推荐应用的内存。
来源 Chunk：US8095432B1-chunk-000, US8095432B1-chunk-001

**US8719408B2 · Claim 17**
a processor coupled to memory, the processor programmed by program code stored in the memory
存储媒体过滤装置程序代码并耦合处理器的内存。
来源 Chunk：US8719408B2-chunk-001

**US9514120B1 · Claim 18**
An apparatus comprising: a memory; a processing device operatively coupled to the memory
拼写反馈装置中与处理设备耦合的内存。
来源 Chunk：US9514120B1-chunk-001

**US9589231B2 · Claim 20**
memory which stores instructions for: receiving a request for a query from a requester
存储诊断辅助查询、嵌入和返回子集等指令。
来源 Chunk：US9589231B2-chunk-001

**邻边审阅：**已逐条审阅实际邻边及其 source_id。未确认一条缺少其自身来源支持的边；合并后的跨文档邻接不能当成已发生错误边传播的证据。

**局限：**['这是 AI 辅助原文/抽取/图结构审阅，非独立人工标注 gold、非新的模型评判 API 实验。', '仅审核当前保存的第二轮图快照与其来源块；概念合并不等于实例 sameAs，也没有进行跨专利路径检索或答案生成传播实验。', '原文为已索引摘要及 Claims；没有用外部说明书填补缺失事实。原始文本中的格式缺陷保持原样。', '边的端点顺序来自保存的无向图；语义方向按原关系描述核对，不把 source/target 字段顺序当作因果方向。', 'observed_unsupported_edge=false 表示本次检查未确认无原文支持的实际边，不是证明全图无误；关键词粒度/局部实施例范围的警示另记。', '未给定显式类/实例 ontology。类别是基于具体词义及作用域的审阅标签，contextual_conflation 数量不是错误边数或代码 bug 率；Event/Network 的宽类解释可改变类别。', '缓存提取行未保存 finish_reason 时不推定完整或截断；本审核只对实际保存的实体/关系行与当前已入图事实作语义核验。']

实际邻边端点、描述与来源（5 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 303 | Processor — Memory | The memory is operatively connected to the processor.&lt;SEP&gt;The processor is coupled to memory and programmed by program code stored in the memory.&lt;SEP&gt;The at least one processor executes program instructions stored in the memory.&lt;SEP&gt;The processor is in communication with the memory for executing the instructions. | US11423041B2, US8095432B1, US8719408B2, US9589231B2<br>`US8095432B1-chunk-001&lt;SEP&gt;US8719408B2-chunk-001&lt;SEP&gt;US11423041B2-chunk-000&lt;SEP&gt;US9589231B2-chunk-001` |
| 323 | Memory — Recommendation Application | The recommendation application is resident in the memory.&lt;SEP&gt;The recommendation application is resident in memory operatively connected to the processor. | US8095432B1<br>`US8095432B1-chunk-000&lt;SEP&gt;US8095432B1-chunk-001` |
| 324 | Memory — Apparatus | The apparatus comprises a memory operatively coupled to the processing device. | US9514120B1<br>`US9514120B1-chunk-001` |
| 325 | Memory — Apparatus For Automated Digital Media Content Filtration | The apparatus comprises memory coupled to the processor. | US8719408B2<br>`US8719408B2-chunk-001` |
| 326 | Memory — Diagnosis Assistance System | The diagnosis assistance system comprises memory that stores instructions. | US9589231B2<br>`US9589231B2-chunk-001` |

N021 · Payment · 共享宽类 · 2 篇

**判定：**两篇 payment 都是经济报酬/款项支付，一篇与商品购买或点击相关，另一篇为专家诊断报酬。收付双方和触发条件不同，但共同货币支付类有直接原文支持，不能因交易场景不同判为语义冲突。

**类与实例：**共享支付类；各篇付款行为、付款人、收款人及触发条件保持独立。

**原图类型：**concept；**置信度：**高；**文件：**US8095432B1.txt, US9589231B2.txt

**US8095432B1 · Claim 13**
receiving a payment upon a purchase of the item from the inquiring member
商品购买/点击关联的款项。
来源 Chunk：US8095432B1-chunk-000

**US9589231B2 · Claim 13**
providing for making a payment to the expert for formulating the diagnosis
选择专家查询时为诊断专家付费。
来源 Chunk：US9589231B2-chunk-000

**邻边审阅：**已逐条审阅实际邻边及其 source_id。未确认一条缺少其自身来源支持的边；合并后的跨文档邻接不能当成已发生错误边传播的证据。

**局限：**['这是 AI 辅助原文/抽取/图结构审阅，非独立人工标注 gold、非新的模型评判 API 实验。', '仅审核当前保存的第二轮图快照与其来源块；概念合并不等于实例 sameAs，也没有进行跨专利路径检索或答案生成传播实验。', '原文为已索引摘要及 Claims；没有用外部说明书填补缺失事实。原始文本中的格式缺陷保持原样。', '边的端点顺序来自保存的无向图；语义方向按原关系描述核对，不把 source/target 字段顺序当作因果方向。', 'observed_unsupported_edge=false 表示本次检查未确认无原文支持的实际边，不是证明全图无误；关键词粒度/局部实施例范围的警示另记。', '未给定显式类/实例 ontology。类别是基于具体词义及作用域的审阅标签，contextual_conflation 数量不是错误边数或代码 bug 率；Event/Network 的宽类解释可改变类别。', '缓存提取行未保存 finish_reason 时不推定完整或截断；本审核只对实际保存的实体/关系行与当前已入图事实作语义核验。']

实际邻边端点、描述与来源（3 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 275 | Inquiring Member — Payment | A payment is received upon a purchase of the item from the inquiring member. | US8095432B1<br>`US8095432B1-chunk-000` |
| 301 | Item — Payment | Payment is received upon purchase of the item or for each click associated with the item. | US8095432B1<br>`US8095432B1-chunk-000` |
| 335 | Payment — Query-For-Experts | When query-for-experts is selected, provision is made for making a payment to the expert for formulating the diagnosis. | US9589231B2<br>`US9589231B2-chunk-000` |

N022 · Network · 异义／角色并置 · 2 篇

**判定：**US8095432B1 Claim 3 以朋友在内、非朋友在外来界定询问成员的社交关系网络；US9589231B2 Claim 20 则将 network 明确组成定义为诊断辅助系统和连接请求者/专家的用户设备集合。原实体描述沿用这两个不同的成员域，最终单节点却同时承载好友关系邻边与设备/系统组成邻边。两者可抽象为相互连接的集合，因此分类保留中等置信度；但这种极宽上位类没有表达当前具体 member network 与 device/system network 的不同语义约束。

**类与实例：**当前标签混合了社交成员网络与系统/设备网络两个上下文意义。可以显式定义 Network 为相互连接的集合这一上位类并保留子类/实例范围；在这种 ontology 下，shared_broad_class 也是合理解释。当前图没有给定正式 ontology，C3 不是已证明的语义错误或 bug；本审核不把一个全局标签自动解释成同一物理网络或同一组织。

**原图类型：**organization；**置信度：**中；**文件：**US8095432B1.txt, US9589231B2.txt

**US8095432B1 · Claim 3**
friends of the inquiring member are within a network of the inquiring member
按朋友/非朋友内外边界划分的社交成员网络。
来源 Chunk：US8095432B1-chunk-000

**US9589231B2 · Claim 20**
A network comprising a system for diagnosis assistance and a set of user devices for linking requesters and experts with the system
由诊断辅助系统和用户设备构成、连接请求者与专家的系统网络。
来源 Chunk：US9589231B2-chunk-001

**邻边审阅：**4 条实际邻边按各自 source_id 都有本地支持。未发现实际边宣称社交好友是诊断系统设备，亦未做任何会造成这种解释的检索/生成运行；仅记录未分词义节点可能产生的跨来源邻接。

**局限：**['这是 AI 辅助原文/抽取/图结构审阅，非独立人工标注 gold、非新的模型评判 API 实验。', '仅审核当前保存的第二轮图快照与其来源块；概念合并不等于实例 sameAs，也没有进行跨专利路径检索或答案生成传播实验。', '原文为已索引摘要及 Claims；没有用外部说明书填补缺失事实。原始文本中的格式缺陷保持原样。', '边的端点顺序来自保存的无向图；语义方向按原关系描述核对，不把 source/target 字段顺序当作因果方向。', 'observed_unsupported_edge=false 表示本次检查未确认无原文支持的实际边，不是证明全图无误；关键词粒度/局部实施例范围的警示另记。', '未给定显式类/实例 ontology。类别是基于具体词义及作用域的审阅标签，contextual_conflation 数量不是错误边数或代码 bug 率；Event/Network 的宽类解释可改变类别。', '缓存提取行未保存 finish_reason 时不推定完整或截断；本审核只对实际保存的实体/关系行与当前已入图事实作语义核验。']

实际邻边端点、描述与来源（4 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 273 | Inquiring Member — Network | The inquiring member has a network within which friends reside. | US8095432B1<br>`US8095432B1-chunk-000` |
| 283 | Relationship Proximity — Network | Relationship proximity is closer for friends within the network and farther for non-friends outside the network. | US8095432B1<br>`US8095432B1-chunk-000` |
| 336 | Network — User Devices | The network comprises a set of user devices. | US9589231B2<br>`US9589231B2-chunk-001` |
| 337 | Network — Diagnosis Assistance System | The network comprises a system for diagnosis assistance. | US9589231B2<br>`US9589231B2-chunk-001` |

N023 · User · 共享宽类 · 5 篇

**判定：**5 篇、9 个来源块均将 user 作为使用系统/消费或反馈内容的人：邮件使用者、媒体读者、搜索用户、内容偏好表达者、拼写反馈者。原合并摘要逐一用 in the context of 区分局部角色，没有证据宣称为同一个人；角色不同不足以认定词义混并。

**类与实例：**共享系统用户这一人的角色类。不是五篇中的同一自然人，也不将角色偏好、邮件操作及错误反馈绑定到同一用户实例。

**原图类型：**person；**置信度：**高；**文件：**US8069128B2.txt, US8719408B2.txt, US8880423B2.txt, US9374411B1.txt, US9514120B1.txt

**US8069128B2 · Claim 6**
such that a user is enabled to move the identified message to another message folder
查看误分类提示、移动消息并可手动选择多遍过滤器的用户。
来源 Chunk：US8069128B2-chunk-000, US8069128B2-chunk-001

**US8719408B2 · Claim 1**
each user relationship based on monitoring an online association between a user and a content producer
与内容发布者存在在线关系、接收按关联权重过滤内容的用户。
来源 Chunk：US8719408B2-chunk-000, US8719408B2-chunk-001

**US8880423B2 · Claim 1**
the search keywords based on search keywords previously submitted by a plurality of users
历史查询和浏览行为产生搜索库存估计输入的用户。
来源 Chunk：US8880423B2-chunk-000

**US9374411B1 · Claim 1**
associate a preferred character with the user based at least upon the second user interaction data
通过内容交互表达角色偏好并接收内容推荐的用户。
来源 Chunk：US9374411B1-chunk-000, US9374411B1-chunk-001, US9374411B1-chunk-002

**US9514120B1 · Claim 18**
provide data indicative of presence of a potential typographical error in a work to a user via a graphical user interface
通过图形界面反馈潜在排版/拼写错误是否为作者原意的用户。
来源 Chunk：US9514120B1-chunk-001

**邻边审阅：**已逐条审阅实际邻边及其 source_id。未确认一条缺少其自身来源支持的边；合并后的跨文档邻接不能当成已发生错误边传播的证据。

**局限：**['这是 AI 辅助原文/抽取/图结构审阅，非独立人工标注 gold、非新的模型评判 API 实验。', '仅审核当前保存的第二轮图快照与其来源块；概念合并不等于实例 sameAs，也没有进行跨专利路径检索或答案生成传播实验。', '原文为已索引摘要及 Claims；没有用外部说明书填补缺失事实。原始文本中的格式缺陷保持原样。', '边的端点顺序来自保存的无向图；语义方向按原关系描述核对，不把 source/target 字段顺序当作因果方向。', 'observed_unsupported_edge=false 表示本次检查未确认无原文支持的实际边，不是证明全图无误；关键词粒度/局部实施例范围的警示另记。', '未给定显式类/实例 ontology。类别是基于具体词义及作用域的审阅标签，contextual_conflation 数量不是错误边数或代码 bug 率；Event/Network 的宽类解释可改变类别。', '缓存提取行未保存 finish_reason 时不推定完整或截断；本审核只对实际保存的实体/关系行与当前已入图事实作语义核验。']

实际邻边端点、描述与来源（21 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 293 | Recommendation — User | The recommendation to play the second video content feature is sent to the user.&lt;SEP&gt;The recommendation is generated for another user in response to the user specifying a preference for a character. | US9374411B1<br>`US9374411B1-chunk-000&lt;SEP&gt;US9374411B1-chunk-001` |
| 361 | Viewed Page — User | Viewed pages are pages previously viewed by users. | US8880423B2<br>`US8880423B2-chunk-000` |
| 366 | Search Keyword — User | Search keywords were previously submitted by a plurality of users. | US8880423B2<br>`US8880423B2-chunk-000` |
| 382 | User — Feedback | Users provide feedback on potential typographical errors in a work. | US9514120B1<br>`US9514120B1-chunk-001` |
| 383 | User — Graphical User Interface | A user receives data indicative of potential typographical errors via a graphical user interface. | US9514120B1<br>`US9514120B1-chunk-001` |
| 384 | User — Misclassification Identification | The misclassification identification is displayed to the user so a misclassified message can be moved. | US8069128B2<br>`US8069128B2-chunk-000` |
| 385 | User — Message Folders | The user is enabled to move an identified misclassified message to a different message folder. | US8069128B2<br>`US8069128B2-chunk-000` |
| 386 | User — Interface | The user selects the multi-pass message filter for execution through an interface on the client device.&lt;SEP&gt;The multi-pass message filter is selectable for execution by a user through an interface on the client device. | US8069128B2<br>`US8069128B2-chunk-000&lt;SEP&gt;US8069128B2-chunk-001` |
| 387 | User — Message Folder | A user is enabled to move the identified message to another message folder. | US8069128B2<br>`US8069128B2-chunk-001` |
| 388 | User — Client Device | The client device provides a display of information associated with incorrectly sorted messages, such that a user is enabled to move the identified message to another message folder. | US8069128B2<br>`US8069128B2-chunk-001` |
| 389 | User — Multi-Pass Message Filter | The multi-pass message filter is selectable for execution by a user through an interface on the client device. | US8069128B2<br>`US8069128B2-chunk-001` |
| 390 | User — First Message Filter | The first message filter is automatically executed independent of a user action. | US8069128B2<br>`US8069128B2-chunk-001` |
| 391 | User — Content Recommendation System | The content recommendation system recommends network content to users based on character preferences and relationship scores. | US9374411B1<br>`US9374411B1-chunk-000` |
| 392 | User — Preferred Character | The user is associated with a preferred character based on user interaction data expressing a preference toward that character. | US9374411B1<br>`US9374411B1-chunk-000` |
| 393 | User — Client | The client is associated with the user. | US9374411B1<br>`US9374411B1-chunk-000` |
| 394 | User — Second Character | The user may specify a preference for the second character. | US9374411B1<br>`US9374411B1-chunk-001` |
| 395 | User — First Character | The user may specify a preference for the first character. | US9374411B1<br>`US9374411B1-chunk-001` |
| 396 | User — User Relationship | A user relationship is established between a user and a content producer and involves the user.&lt;SEP&gt;Each user relationship involves a user. | US8719408B2<br>`US8719408B2-chunk-000&lt;SEP&gt;US8719408B2-chunk-001` |
| 397 | User — Media Aggregator Profile | The media aggregator profile is associated with the user. | US8719408B2<br>`US8719408B2-chunk-000&lt;SEP&gt;US8719408B2-chunk-001` |
| 398 | User — Mutual Interest | Mutual interests exist between the user and the content producer that published the digital media content. | US8719408B2<br>`US8719408B2-chunk-000` |
| 399 | User — Mutual Interests | The mutual interests are between the user and the content producer. | US8719408B2<br>`US8719408B2-chunk-001` |

N024 · Application · 共享宽类 · 2 篇

**判定：**两个来源的 Application 都是可在设备上执行、接受输入并完成功能的软件应用。一项做人脸/社交检索，另一项做内容推荐，功能差异不使 application 发生词义冲突。现有描述分段与各边来源仍可区分各专利，支持共享软件应用大类；没有证据表明两文档指向同一应用实例。

**类与实例：**按共享概念类别解释成立；不是跨专利同一个体身份声明。图中一个 ID 汇集多个文档内实例/功能描述，后续推理仍须保留每条边和原文的专利作用域。

**原图类型：**artifact；**置信度：**高；**文件：**US8917913B2.txt, US9374411B1.txt

**US8917913B2 · Claim 1**
an application associated with the mobile device, wherein the application is in operative communication with the camera
移动设备上的软件应用，与相机、用户接口和搜索服务交互；不是专利申请这一不同词义。
来源 Chunk：US8917913B2-chunk-000, US8917913B2-chunk-001

**US9374411B1 · Claim 6**
at least one application executable in the at least one computing device
执行内容推荐操作的软件应用；与人脸检索应用属于相同软件大类，具体实例不同。
来源 Chunk：US9374411B1-chunk-000, US9374411B1-chunk-001

**邻边审阅：**

**局限：**['本结果是助手逐文内容审阅，不是独立人类金标准，也未调用新的模型评判 API。', '共享宽类不保证所有合并描述适用于每个来源，也不验证物理/软件实例身份相等。', '未运行新的检索和生成实验，不能据邻接路径推定已发生错误传播。', '缓存行未保存 finish_reason；本评审不从缓存缺该字段推定响应完整或截断。']

实际邻边端点、描述与来源（7 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 73 | Mobile Device — Application | The application is associated with the mobile device and is in operative communication with its camera.&lt;SEP&gt;The application is associated with the mobile device. | US8917913B2<br>`US8917913B2-chunk-000&lt;SEP&gt;US8917913B2-chunk-001` |
| 426 | Application — Camera | The application is in operative communication with the camera and receives source images from it. | US8917913B2<br>`US8917913B2-chunk-000&lt;SEP&gt;US8917913B2-chunk-001` |
| 427 | Application — User Interface | The application provides a user interface and receives friend identifiers and friend level indicators from it.&lt;SEP&gt;The application provides a user interface and receives search terms or friend identifiers from it. | US8917913B2<br>`US8917913B2-chunk-000&lt;SEP&gt;US8917913B2-chunk-001` |
| 428 | Application — Internet Access Mechanism | The Internet access mechanism is in operative communication with the application. | US8917913B2<br>`US8917913B2-chunk-000&lt;SEP&gt;US8917913B2-chunk-001` |
| 429 | Application — Friend Identifier | The application receives at least one friend identifier from the user interface. | US8917913B2<br>`US8917913B2-chunk-001` |
| 430 | Application — Source Image | The application receives at least one source image from the camera. | US8917913B2<br>`US8917913B2-chunk-001` |
| 431 | Application — Computing Device | The application is executable in the computing device and causes it to perform content recommendation functions.&lt;SEP&gt;The application is executed by the computing device and causes it to perform various operations. | US9374411B1<br>`US9374411B1-chunk-000&lt;SEP&gt;US9374411B1-chunk-001` |

N025 · User Interface · 共享宽类 · 3 篇

**判定：**三个来源都把 User Interface 用作用户输入、内容显示或反馈收集的人机交互界面。展示邮件关系、接收好友输入、展示内容/采集角色反馈是同一宽类的不同实例用途；并无界面一词变成非交互技术对象的证据。因此不能仅凭角色不同判为上下文混并。

**类与实例：**按共享概念类别解释成立；不是跨专利同一个体身份声明。图中一个 ID 汇集多个文档内实例/功能描述，后续推理仍须保留每条边和原文的专利作用域。

**原图类型：**artifact；**置信度：**高；**文件：**US10778629B2.txt, US8917913B2.txt, US9374411B1.txt

**US10778629B2 · Claim 21**
a user interface to display the relationship data.
显示电子邮件用户关系模型／关系数据的界面。
来源 Chunk：US10778629B2-chunk-000, US10778629B2-chunk-001

**US8917913B2 · Claim 1**
wherein the application provides a user interface
接收搜索词、好友标识及好友层级输入的移动应用界面。
来源 Chunk：US8917913B2-chunk-000, US8917913B2-chunk-001

**US9374411B1 · Claim 23**
obtain explicit user feedback expressing that the user favors the first fictional character via a user interface.
显示内容并获取虚构角色偏好反馈的界面。
来源 Chunk：US9374411B1-chunk-000, US9374411B1-chunk-002

**邻边审阅：**

**局限：**['本结果是助手逐文内容审阅，不是独立人类金标准，也未调用新的模型评判 API。', '共享宽类不保证所有合并描述适用于每个来源，也不验证物理/软件实例身份相等。', '未运行新的检索和生成实验，不能据邻接路径推定已发生错误传播。', '缓存行未保存 finish_reason；本评审不从缓存缺该字段推定响应完整或截断。']

实际邻边端点、描述与来源（8 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 92 | Server — User Interface | Relationship data is displayed on a user interface. | US10778629B2<br>`US10778629B2-chunk-000` |
| 427 | Application — User Interface | The application provides a user interface and receives friend identifiers and friend level indicators from it.&lt;SEP&gt;The application provides a user interface and receives search terms or friend identifiers from it. | US8917913B2<br>`US8917913B2-chunk-000&lt;SEP&gt;US8917913B2-chunk-001` |
| 437 | Search Term — User Interface | The search term is received from the user interface of the application. | US8917913B2<br>`US8917913B2-chunk-000` |
| 438 | User Interface — Friend Identifier | The friend identifier is received from the user interface of the application. | US8917913B2<br>`US8917913B2-chunk-000` |
| 439 | User Interface — First Video Content Feature | The first video content feature is caused to be rendered in a user interface for display on the client. | US9374411B1<br>`US9374411B1-chunk-000` |
| 440 | User Interface — User Feedback | The explicit user feedback is obtained via a user interface. | US9374411B1<br>`US9374411B1-chunk-002` |
| 441 | User Interface — Relationship Modeling Program | The model of relationships produced by the relationship modeling program is displayed on a user interface. | US10778629B2<br>`US10778629B2-chunk-000` |
| 442 | User Interface — Relationship Data | The user interface displays the relationship data. | US10778629B2<br>`US10778629B2-chunk-001` |

N026 · Computing Device · 共享宽类 · 3 篇

**判定：**三个来源的 Computing Device 都指执行指令或软件操作的计算硬件类；地理查询解析、内容推荐和拼写反馈分类是不同应用负载，不是互斥词义。可把它们视为同一宽类，但没有证据证明为同一物理设备或允许把每项负载移植为其他专利已声明的功能。

**类与实例：**按共享概念类别解释成立；不是跨专利同一个体身份声明。图中一个 ID 汇集多个文档内实例/功能描述，后续推理仍须保留每条边和原文的专利作用域。

**原图类型：**artifact；**置信度：**高；**文件：**US9218390B2.txt, US9374411B1.txt, US9514120B1.txt

**US9218390B2 · Claim 18**
which instructions, when executed by one or more computing devices, cause the one or more computing devices to:
执行机器可读指令、实现地理查询解析和消歧的计算设备。
来源 Chunk：US9218390B2-chunk-002

**US9374411B1 · Claim 6**
at least one application executable in the at least one computing device
执行内容推荐应用和计算机指令的设备。
来源 Chunk：US9374411B1-chunk-000, US9374411B1-chunk-001, US9374411B1-chunk-002

**US9514120B1 · Abstract**
A computing device hosting a server identifies one or more potential typographical errors in a work using an initial reference.
承载服务器并汇总用户反馈、分类拼写错误的计算设备。
来源 Chunk：US9514120B1-chunk-000

**邻边审阅：**

**局限：**['本结果是助手逐文内容审阅，不是独立人类金标准，也未调用新的模型评判 API。', '共享宽类不保证所有合并描述适用于每个来源，也不验证物理/软件实例身份相等。', '未运行新的检索和生成实验，不能据邻接路径推定已发生错误传播。', '缓存行未保存 finish_reason；本评审不从缓存缺该字段推定响应完整或截断。', 'US9514120B1 的 computing device 主要引用摘要，权利要求采用 processing device，不混标 Claim 来源。']

实际邻边端点、描述与来源（16 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 88 | Server — Computing Device | The computing device hosts a server that performs typographical error classification. | US9514120B1<br>`US9514120B1-chunk-000` |
| 294 | Recommendation — Computing Device | The computing device sends a recommendation for presentation of the second network content. | US9374411B1<br>`US9374411B1-chunk-001` |
| 431 | Application — Computing Device | The application is executable in the computing device and causes it to perform content recommendation functions.&lt;SEP&gt;The application is executed by the computing device and causes it to perform various operations. | US9374411B1<br>`US9374411B1-chunk-000&lt;SEP&gt;US9374411B1-chunk-001` |
| 446 | US9514120B1 — Computing Device | The patent document describes operations performed by a computing device for classifying typographical errors. | US9514120B1<br>`US9514120B1-chunk-000` |
| 448 | Computing Device — Initial Reference | The computing device identifies potential typographical errors using an initial reference and updates the initial reference to include acceptable strings. | US9514120B1<br>`US9514120B1-chunk-000` |
| 449 | Computing Device — Work | The computing device identifies potential typographical errors in a work. | US9514120B1<br>`US9514120B1-chunk-000` |
| 450 | Computing Device — User Feedback | The computing device collects feedback from users, combines it with feedback for other works, and sorts the combined feedback. | US9514120B1<br>`US9514120B1-chunk-000` |
| 451 | Computing Device — Users | The computing device sends data indicative of potential typographical errors to users and collects feedback from them. | US9514120B1<br>`US9514120B1-chunk-000` |
| 452 | Computing Device — Non-Transitory Computer-Readable Medium | The non-transitory computer-readable medium has computer instructions executable by a computing device.&lt;SEP&gt;The computer instructions on the medium are executable by the computing device to cause it to perform operations. | US9374411B1<br>`US9374411B1-chunk-000&lt;SEP&gt;US9374411B1-chunk-001` |
| 453 | Computing Device — First Video Content Feature | The computing device processes the first video content feature and identifies the first character in its scene. | US9374411B1<br>`US9374411B1-chunk-001` |
| 454 | Computing Device — First Network Content | The computing device causes the first network content to be rendered in a user interface for display on a client. | US9374411B1<br>`US9374411B1-chunk-001` |
| 455 | Computing Device — User Interaction Data | The computing device obtains user interaction data from the client based on interactions with content. | US9374411B1<br>`US9374411B1-chunk-001` |
| 456 | Computing Device — Timeline User Interface | The computing device causes the timeline user interface to be rendered in response to obtaining interaction data. | US9374411B1<br>`US9374411B1-chunk-001` |
| 457 | Computing Device — Library | The computing device references the library to identify a recommended character. | US9374411B1<br>`US9374411B1-chunk-001` |
| 458 | Computing Device — Computer Instructions | The plurality of computer instructions causes the at least one computing device to perform operations. | US9374411B1<br>`US9374411B1-chunk-002` |
| 459 | Computing Device — Non-Transitory Machine-Readable Media | The computing devices execute machine-readable instructions on the non-transitory machine-readable media. | US9218390B2<br>`US9218390B2-chunk-002` |

N027 · User Feedback · 共享宽类 · 2 篇

**判定：**两来源都指用户显式提供的反馈数据；一处判断用户是否偏好虚构角色，另一处判断疑似拼写错误是否为作者有意写法。不同反馈对象和字段不改变“用户反馈”这一共同上位数据类。合并描述保留两种任务，不能据此认定两个反馈实例相同或词义冲突。

**类与实例：**共同类为用户提供的意见/判定；US9374411B1的角色偏好反馈与US9514120B1的文本校验反馈是不同文档局部数据实例，字段及取值不应跨文档移植。

**原图类型：**data；**置信度：**高；**文件：**US9374411B1.txt, US9514120B1.txt

**US9374411B1 · Claim 23**
obtain explicit user feedback expressing that the user favors the first fictional character via a user interface.
用户经界面表达对第一个虚构角色的偏好。
来源 Chunk：US9374411B1-chunk-002

**US9514120B1 · Claim 1**
feedback comprising an indicator that specifies that the potential typographical error is an author-intended string for the work
用户反馈是判断疑似排版/拼写错误是否为作者意图的输入，并与其他作品反馈组合。
来源 Chunk：US9514120B1-chunk-000

**邻边审阅：**已逐条检查全部实际邻边及其source_id/file_path；各关系在所属专利中有对应陈述，未发现将另一专利特征直接写入本专利边描述的确证。共同节点容许潜在无作用域路径组合，但本审计没有执行或观察该传播。

**局限：**['本结果为AI辅助逐来源语义审阅，不是独立人工金标准；分类依赖所声明的类/实例粒度。', '只审计第二轮既有20篇索引中的可见原chunk、原抽取与实际图邻边；原文范围为已索引的标题、摘要及Claims，未额外读取完整说明书或新语料，未调用模型API，也未进行新的检索/生成传播测试。', '共享节点产生跨专利邻接不等于已观察到错误跨文档推理；边的source_id和file_path应保持作用域。']

实际邻边端点、描述与来源（7 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 440 | User Interface — User Feedback | The explicit user feedback is obtained via a user interface. | US9374411B1<br>`US9374411B1-chunk-002` |
| 450 | Computing Device — User Feedback | The computing device collects feedback from users, combines it with feedback for other works, and sorts the combined feedback. | US9514120B1<br>`US9514120B1-chunk-000` |
| 461 | Processing Device — User Feedback | The processing device receives feedback from users, combines it with feedback for additional works, and sorts the combined feedback. | US9514120B1<br>`US9514120B1-chunk-000` |
| 480 | Author-Intended String — User Feedback | User feedback indicates whether potential typographical errors are author-intended strings. | US9514120B1<br>`US9514120B1-chunk-000` |
| 490 | User Feedback — Combined Feedback | Feedback for a work is combined with feedback for additional works to generate combined feedback. | US9514120B1<br>`US9514120B1-chunk-000` |
| 491 | User Feedback — Computer Instructions | The computer instructions cause the computing device to obtain explicit user feedback expressing that the user favors the first fictional character. | US9374411B1<br>`US9374411B1-chunk-002` |
| 492 | User Feedback — First Fictional Character | The user feedback expresses that the user favors the first fictional character. | US9374411B1<br>`US9374411B1-chunk-002` |

N028 · Non-Transitory Computer-Readable Medium · 共享宽类 · 2 篇

**判定：**两篇都使用非暂态计算机可读介质承载可执行指令的共同存储载体类；指令分别完成内容推荐和排版错误反馈处理。应用功能不同不足以证明介质概念异义。

**类与实例：**介质是共同类；各独立权利要求中的具体指令集和介质实施例具有各自专利作用域，不能断言同一实际介质同时执行全部功能。

**原图类型：**artifact；**置信度：**高；**文件：**US9374411B1.txt, US9514120B1.txt

**US9374411B1 · Claim 1**
A non-transitory computer-readable medium having a plurality of computer instructions executable by at least one computing device
承载内容呈现、角色偏好及推荐流程的指令介质。
来源 Chunk：US9374411B1-chunk-000, US9374411B1-chunk-001, US9374411B1-chunk-002

**US9514120B1 · Claim 10**
A non-transitory computer-readable medium having instructions stored thereon which, when executed by a processing device, cause the processing device to perform operations comprising:
承载判别作者意图字符串、反馈组合及参考更新操作的指令介质。
来源 Chunk：US9514120B1-chunk-000, US9514120B1-chunk-001

**邻边审阅：**已逐条检查全部实际邻边及其source_id/file_path；各关系在所属专利中有对应陈述，未发现将另一专利特征直接写入本专利边描述的确证。共同节点容许潜在无作用域路径组合，但本审计没有执行或观察该传播。

**局限：**['本结果为AI辅助逐来源语义审阅，不是独立人工金标准；分类依赖所声明的类/实例粒度。', '只审计第二轮既有20篇索引中的可见原chunk、原抽取与实际图邻边；原文范围为已索引的标题、摘要及Claims，未额外读取完整说明书或新语料，未调用模型API，也未进行新的检索/生成传播测试。', '共享节点产生跨专利邻接不等于已观察到错误跨文档推理；边的source_id和file_path应保持作用域。', '介质—计算设备边是“介质上指令由设备执行”的简写，不能将其读为物理介质本体被执行。']

实际邻边端点、描述与来源（3 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 452 | Computing Device — Non-Transitory Computer-Readable Medium | The non-transitory computer-readable medium has computer instructions executable by a computing device.&lt;SEP&gt;The computer instructions on the medium are executable by the computing device to cause it to perform operations. | US9374411B1<br>`US9374411B1-chunk-000&lt;SEP&gt;US9374411B1-chunk-001` |
| 463 | Processing Device — Non-Transitory Computer-Readable Medium | The processing device executes instructions stored on the non-transitory computer-readable medium.&lt;SEP&gt;The non-transitory computer-readable medium stores instructions that cause the processing device to perform operations. | US9514120B1<br>`US9514120B1-chunk-000&lt;SEP&gt;US9514120B1-chunk-001` |
| 512 | Non-Transitory Computer-Readable Medium — Computer Instructions | The non-transitory computer-readable medium stores a plurality of computer instructions. | US9374411B1<br>`US9374411B1-chunk-002` |

N029 · Users · 共享宽类 · 2 篇

**判定：**两来源均是系统的人类用户群体：推荐结果受众与疑似文字错误反馈参与者。共同人类使用者角色成立，场景和具体人员集合不同不是实体语义错误。

**类与实例：**Users为用户类/集合角色，不是跨专利可唯一识别的一批人；不能从共享节点推出两篇用户身份或行为相同。

**原图类型：**person；**置信度：**高；**文件：**US7991757B2.txt, US9514120B1.txt

**US7991757B2 · Claim 22**
A system for enabling site operators to obtain item recommendations for presentation to users
内容站点展示项目推荐的最终用户。
来源 Chunk：US7991757B2-chunk-001

**US9514120B1 · Claim 1**
sending, by the processing device, data indicative of presence of the potential typographical error in the work to a plurality of users
收到潜在文字错误提示并提供作者意图反馈的用户群体。
来源 Chunk：US9514120B1-chunk-000

**邻边审阅：**已逐条检查全部实际邻边及其source_id/file_path；各关系在所属专利中有对应陈述，未发现将另一专利特征直接写入本专利边描述的确证。共同节点容许潜在无作用域路径组合，但本审计没有执行或观察该传播。

**局限：**['本结果为AI辅助逐来源语义审阅，不是独立人工金标准；分类依赖所声明的类/实例粒度。', '只审计第二轮既有20篇索引中的可见原chunk、原抽取与实际图邻边；原文范围为已索引的标题、摘要及Claims，未额外读取完整说明书或新语料，未调用模型API，也未进行新的检索/生成传播测试。', '共享节点产生跨专利邻接不等于已观察到错误跨文档推理；边的source_id和file_path应保持作用域。']

实际邻边端点、描述与来源（2 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 451 | Computing Device — Users | The computing device sends data indicative of potential typographical errors to users and collects feedback from them. | US9514120B1<br>`US9514120B1-chunk-000` |
| 513 | Users — Site Operators | Site operators obtain item recommendations for presentation to users. | US7991757B2<br>`US7991757B2-chunk-001` |

N030 · Apparatus · 共享宽类 · 2 篇

**判定：**Apparatus在两来源中均是由硬件/功能模块构成的装置类：备份数据管理装置与收集文字校验反馈的装置。原文没有表示同一个装置；泛化名称本身不足以判跨专利语义混并。US9514120B1另有同专利内的操作主体粗化候选，须与跨来源类合并分开。

**类与实例：**共同类为装置/设备；Claim31/47/48的备份流装置与另一专利Claim18的处理器/内存装置是局部实施例。把全部邻边无作用域地合成为同一机器能力会超出原文，但本审计未运行该种推理。

**原图类型：**artifact；**置信度：**中；**文件：**US7756837B2.txt, US9514120B1.txt

**US7756837B2 · Claim 31**
An apparatus, comprising: means for receiving at least one data-stream intended for archiving on a backup storage device;
透明接收备份流、提取管理数据并存储到数据库的装置；Claim47/48分别含存储路由/服务器功能。
来源 Chunk：US7756837B2-chunk-001, US7756837B2-chunk-002, US7756837B2-chunk-003

**US9514120B1 · Claim 18**
An apparatus comprising: a memory; a processing device operatively coupled to the memory
含内存和处理设备的装置，向用户显示疑似文字错误并向服务器提交反馈；服务器随后组合、排序及更新参考。
来源 Chunk：US9514120B1-chunk-001, US9514120B1-chunk-002

**邻边审阅：**已逐条检查全部实际邻边及其source_id/file_path。除495/502/517这3条主语粒度警示外，其余关系按所属来源有支持；未确认跨专利不支持边。3条警示均来自US9514120B1-chunk-002：完整Claim18的server computing machine在原抽取及图中被概括为Apparatus，最早已出现在单专利抽取。共同节点仍可形成潜在无作用域路径，但没有本次查询或传播证据，不能把这些源内警示归因于跨专利节点合并。

**局限：**['本结果为AI辅助逐来源语义审阅，不是独立人工金标准；分类依赖所声明的类/实例粒度。', '只审计第二轮既有20篇索引中的可见原chunk、原抽取与实际图邻边；原文范围为已索引的标题、摘要及Claims，未额外读取完整说明书或新语料，未调用模型API，也未进行新的检索/生成传播测试。', '共享节点产生跨专利邻接不等于已观察到错误跨文档推理；边的source_id和file_path应保持作用域。', '是否可把server操作作为整机功能间接概括存在粒度解释空间；目前将三个显式主语不一致的边列为qualified_role_attribution_candidate，不计为已证明跨专利错误边。']

实际邻边端点、描述与来源（18 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 102 | Database — Apparatus | The apparatus comprises means for storing the management data in a searchable format in a database. | US7756837B2<br>`US7756837B2-chunk-001&lt;SEP&gt;US7756837B2-chunk-003` |
| 324 | Memory — Apparatus | The apparatus comprises a memory operatively coupled to the processing device. | US9514120B1<br>`US9514120B1-chunk-001` |
| 468 | Processing Device — Apparatus | The apparatus comprises a processing device operatively coupled to the memory. | US9514120B1<br>`US9514120B1-chunk-001` |
| 477 | Potential Typographical Error — Apparatus | The input to the apparatus may comprise a string identified as a potential typographical error, and the apparatus uses data indicative of the presence of the potential typographical error. | US9514120B1<br>`US9514120B1-chunk-002` |
| 495 | Combined Feedback — Apparatus | The apparatus generates a combined feedback from one or more additional works. | US9514120B1<br>`US9514120B1-chunk-002` |
| 502 | Sorted Feedback — Apparatus | The apparatus sorts the combined feedback to generate a sorted feedback. | US9514120B1<br>`US9514120B1-chunk-002` |
| 514 | Feedback — Apparatus | The apparatus provides feedback for a work to a server computing machine, the feedback comprising identification of author-intended strings and associated parameters. | US9514120B1<br>`US9514120B1-chunk-001` |
| 515 | Server Computing Machine — Apparatus | The apparatus provides feedback for a work to a server computing machine. | US9514120B1<br>`US9514120B1-chunk-001` |
| 516 | Graphical User Interface — Apparatus | The apparatus provides data indicative of potential typographical errors to a user via a graphical user interface. | US9514120B1<br>`US9514120B1-chunk-001` |
| 517 | Apparatus — Reference | The apparatus updates a reference based on the sorted feedback. | US9514120B1<br>`US9514120B1-chunk-002` |
| 518 | Apparatus — User Identifier | The input to the apparatus may comprise a user identifier. | US9514120B1<br>`US9514120B1-chunk-002` |
| 519 | Apparatus — Work Identifier | The input to the apparatus may comprise a work identifier. | US9514120B1<br>`US9514120B1-chunk-002` |
| 520 | Apparatus — Decision | The input to the apparatus may comprise a decision indicating whether a corresponding string is an author-intended string. | US9514120B1<br>`US9514120B1-chunk-002` |
| 521 | Apparatus — Confidence Level | The input to the apparatus may comprise a confidence level of the decision. | US9514120B1<br>`US9514120B1-chunk-002` |
| 522 | Apparatus — Data-Stream | The apparatus comprises means for receiving at least one data-stream intended for archiving on a backup storage device.&lt;SEP&gt;The apparatus comprises means for receiving at least one data-stream from one or more sources. | US7756837B2<br>`US7756837B2-chunk-001&lt;SEP&gt;US7756837B2-chunk-002` |
| 523 | Apparatus — Management Data | The apparatus comprises means for extracting management data from the data-stream. | US7756837B2<br>`US7756837B2-chunk-001&lt;SEP&gt;US7756837B2-chunk-002&lt;SEP&gt;US7756837B2-chunk-003` |
| 524 | Apparatus — Storage Router Function | The apparatus comprises means for carrying out a storage router function between the sources and the backup storage device. | US7756837B2<br>`US7756837B2-chunk-002` |
| 525 | Apparatus — Server Function | The apparatus comprises means for carrying out a server function as between the sources and the backup storage device. | US7756837B2<br>`US7756837B2-chunk-003` |

N031 · Score · 共享宽类 · 2 篇

**判定：**两来源的Score均为算法评估值，但一处评估推荐项目并加权归一化，另一处评估消息是否误放文件夹。可共同解释为评估分数类；量纲、算法与数值实例不可互换不等于Score一词的异义误并。

**类与实例：**共享量化评估值类；推荐分数及消息分类分数的取值域、阈值和计算过程属于各自文档，图中未声明同一数值变量。

**原图类型：**data；**置信度：**高；**文件：**US7991757B2.txt, US8069128B2.txt

**US7991757B2 · Claim 4**
receiving recommendations and corresponding scores from the recommenders; applying weights to each of the recommenders; combining the scores with the weights to produce overall scores;
推荐器返回的项目评分，归一化及加权后生成总分。
来源 Chunk：US7991757B2-chunk-000

**US8069128B2 · Claim 17**
using the second classification data, executing a second pass of the multi-pass message filter on the sorted plurality of messages to score each message;
多遍消息过滤器第二遍对消息打分，用以发现错误文件夹中的消息。
来源 Chunk：US8069128B2-chunk-001

**邻边审阅：**已逐条检查全部实际邻边及其source_id/file_path；各关系在所属专利中有对应陈述，未发现将另一专利特征直接写入本专利边描述的确证。共同节点容许潜在无作用域路径组合，但本审计没有执行或观察该传播。

**局限：**['本结果为AI辅助逐来源语义审阅，不是独立人工金标准；分类依赖所声明的类/实例粒度。', '只审计第二轮既有20篇索引中的可见原chunk、原抽取与实际图邻边；原文范围为已索引的标题、摘要及Claims，未额外读取完整说明书或新语料，未调用模型API，也未进行新的检索/生成传播测试。', '共享节点产生跨专利邻接不等于已观察到错误跨文档推理；边的source_id和file_path应保持作用域。']

实际邻边端点、描述与来源（4 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 177 | Weight — Score | Scores are combined with weights to produce overall scores. | US7991757B2<br>`US7991757B2-chunk-000` |
| 556 | Optimization Module — Score | The optimization module normalizes the associated scores. | US7991757B2<br>`US7991757B2-chunk-000` |
| 558 | Score — Overall Score | Combining scores with weights produces overall scores. | US7991757B2<br>`US7991757B2-chunk-000` |
| 559 | Score — Message | Each message's respective score indicates whether the message is sorted into an incorrect message folder. | US8069128B2<br>`US8069128B2-chunk-001` |

N032 · Tokens · 共享技术概念 · 2 篇

**判定：**两来源都明确把搜索query表示/分割为tokens，并给tokens赋予语义标签；因此是查询语言处理中的词/词组单元这一共同技术概念，不是名称巧合。第一来源允许token含多个terms，第二来源的具体分词方式未完全定义，不能推定分词粒度相同。

**类与实例：**共同概念为查询中的token单元；翻译模式挖掘和地理查询解析中的具体token序列、词表及标签方案是各自局部实例。

**原图类型：**concept；**置信度：**高；**文件：**US8655901B1.txt, US9218390B2.txt

**US8655901B1 · Claim 15**
segmenting a given query among the collection into one or more tokens in the first language, wherein each token includes one or more terms from the given query;
第一语言query的词/词组分段，绑定查询模式组件标签，翻译顺序用于恢复目标语言模式。
来源 Chunk：US8655901B1-chunk-001

**US9218390B2 · Claim 1**
receiving an input query, wherein the input query comprises a series of tokens; assigning a label to each of a plurality of the tokens;
输入地理网页搜索query的token序列，标签用于条件随机场解析。
来源 Chunk：US9218390B2-chunk-000

**邻边审阅：**已逐条检查全部实际邻边及其source_id/file_path；各关系在所属专利中有对应陈述，未发现将另一专利特征直接写入本专利边描述的确证。共同节点容许潜在无作用域路径组合，但本审计没有执行或观察该传播。 跨来源合并的token-label边保留两种标注语境及各source_id，未声明两套标签枚举相同。

**局限：**['本结果为AI辅助逐来源语义审阅，不是独立人工金标准；分类依赖所声明的类/实例粒度。', '只审计第二轮既有20篇索引中的可见原chunk、原抽取与实际图邻边；原文范围为已索引的标题、摘要及Claims，未额外读取完整说明书或新语料，未调用模型API，也未进行新的检索/生成传播测试。', '共享节点产生跨专利邻接不等于已观察到错误跨文档推理；边的source_id和file_path应保持作用域。', 'US9218390B2-chunk-000的原抽取响应因length截断，补证来自原API日志而非成功提取cache；当前完整可见行与图存在性可核验，抽取完整性不能据此确认。']

实际邻边端点、描述与来源（5 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 701 | Input Query — Tokens | The input query comprises a series of tokens. | US9218390B2<br>`US9218390B2-chunk-000` |
| 704 | Tokens — Labels | A label is assigned to each of a plurality of the tokens.&lt;SEP&gt;The tokens are annotated with labels for the corresponding components of the first query pattern. | US8655901B1, US9218390B2<br>`US9218390B2-chunk-000&lt;SEP&gt;US8655901B1-chunk-001` |
| 705 | Tokens — Query Pattern | Each token is associated with corresponding components of the first query pattern. | US8655901B1<br>`US8655901B1-chunk-001` |
| 706 | Tokens — Query | A given query among the collection is segmented into one or more tokens in the first language. | US8655901B1<br>`US8655901B1-chunk-001` |
| 707 | Tokens — Translated Query Pattern | The order in which tokens are translated into the second language determines the order in which labels correspond to translated terms, from which the translated query pattern is extracted. | US8655901B1<br>`US8655901B1-chunk-001` |

N033 · Labels · 共享技术概念 · 2 篇

**判定：**两来源都将Labels作为query token/片段的语义标注：一处表示查询模式组件，一处表示搜索词、地理表达等查询解析类别。作为查询token语义标签概念可共享；各自完整标签集合和学习机制不相同，不能把一个来源的具体枚举强加给另一来源。

**类与实例：**共享查询token语义标签概念；不同专利标签schema及每个token上的标签赋值是局部对象。共同节点不能证明相同label ID或枚举。

**原图类型：**concept；**置信度：**中；**文件：**US8655901B1.txt, US9218390B2.txt

**US8655901B1 · Claim 15**
annotating the one or more tokens with labels for the corresponding components of the first query pattern;
查询模式组件的标注，用其对应次序抽取翻译后query pattern。
来源 Chunk：US8655901B1-chunk-001

**US9218390B2 · Claim 12**
the respective sentence identifies the respective label as corresponding to one or more of a search term, a geographic expression, a geographic expression relation indication, and/or uninteresting information;
地理查询解析的语义类别标签；句子被关联到标签以标识其意义。
来源 Chunk：US9218390B2-chunk-000, US9218390B2-chunk-001

**邻边审阅：**已逐条检查全部实际邻边及其source_id/file_path；各关系在所属专利中有对应陈述，未发现将另一专利特征直接写入本专利边描述的确证。共同节点容许潜在无作用域路径组合，但本审计没有执行或观察该传播。 跨来源合并的token-label边保留两种标注语境及各source_id，未声明两套标签枚举相同。

**局限：**['本结果为AI辅助逐来源语义审阅，不是独立人工金标准；分类依赖所声明的类/实例粒度。', '只审计第二轮既有20篇索引中的可见原chunk、原抽取与实际图邻边；原文范围为已索引的标题、摘要及Claims，未额外读取完整说明书或新语料，未调用模型API，也未进行新的检索/生成传播测试。', '共享节点产生跨专利邻接不等于已观察到错误跨文档推理；边的source_id和file_path应保持作用域。', 'shared_specific_concept的粒度限定为查询token语义标签，不包括两个具体标签集等价。', 'US9218390B2-chunk-000的原抽取响应finish_reason=length，已见完整条目可核验，但不能作无遗漏保证。']

实际邻边端点、描述与来源（5 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 673 | Query Parser Derivation Computing Device — Labels | The query parser derivation computing device assigns a label to each of a plurality of the tokens. | US9218390B2<br>`US9218390B2-chunk-001` |
| 704 | Tokens — Labels | A label is assigned to each of a plurality of the tokens.&lt;SEP&gt;The tokens are annotated with labels for the corresponding components of the first query pattern. | US8655901B1, US9218390B2<br>`US9218390B2-chunk-000&lt;SEP&gt;US8655901B1-chunk-001` |
| 708 | Labels — Sentences | One or more sentences are assigned to each label so that the respective sentence identifies the respective label.&lt;SEP&gt;One or more sentences are assigned to each label based at least in part on the most probable label sequence. | US9218390B2<br>`US9218390B2-chunk-000&lt;SEP&gt;US9218390B2-chunk-001` |
| 709 | Labels — Query | Annotating each query includes labeling portions of the query according to the first query pattern. | US8655901B1<br>`US8655901B1-chunk-001` |
| 710 | Labels — Translated Query Pattern | The translated query pattern is extracted from the order in which labels for the components of the first query pattern correspond to the translated terms. | US8655901B1<br>`US8655901B1-chunk-001` |

N034 · Label · 共享技术概念 · 2 篇

**判定：**Label单数节点同样表示query token的语义类别标注，一处对应模式组件，另一处对应地理解析类别；技术角色相容。各标签集合不同不是已证明多义混并，且本节点与Labels复数节点是图中两个真实ID，不能在审计中人为合并。

**类与实例：**共享查询token语义标签概念，具体标签赋值和标签集按文档限定；Label/Labels命名变体的存在另属归一化粒度问题，本轮不改图。

**原图类型：**concept；**置信度：**中；**文件：**US8655901B1.txt, US9218390B2.txt

**US8655901B1 · Claim 1**
annotating the one or more tokens with labels for the corresponding components of the first query pattern;
绑定到第一查询模式组件的token标注。
来源 Chunk：US8655901B1-chunk-000

**US9218390B2 · Claim 18**
the respective sentence identifies the respective label as corresponding to one or more of a search term, a geographic expression, a geographic expression relation indication, and/or uninteresting information;
机器可读介质权利要求中，token上的地理/搜索语义类别标注，参与建立CRF模型。
来源 Chunk：US9218390B2-chunk-002

**邻边审阅：**已逐条检查全部实际邻边及其source_id/file_path；各关系在所属专利中有对应陈述，未发现将另一专利特征直接写入本专利边描述的确证。共同节点容许潜在无作用域路径组合，但本审计没有执行或观察该传播。 跨来源合并的token-label边保留两种标注语境及各source_id，未声明两套标签枚举相同。

**局限：**['本结果为AI辅助逐来源语义审阅，不是独立人工金标准；分类依赖所声明的类/实例粒度。', '只审计第二轮既有20篇索引中的可见原chunk、原抽取与实际图邻边；原文范围为已索引的标题、摘要及Claims，未额外读取完整说明书或新语料，未调用模型API，也未进行新的检索/生成传播测试。', '共享节点产生跨专利邻接不等于已观察到错误跨文档推理；边的source_id和file_path应保持作用域。', '不同标签schema不能等同；技术概念共享的判断不意味着单复数ID已被正确归一。']

实际邻边端点、描述与来源（3 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 251 | Token — Label | A label is assigned to each of a plurality of the tokens.&lt;SEP&gt;The one or more tokens are annotated with labels for the corresponding components of the first query pattern. | US8655901B1, US9218390B2<br>`US9218390B2-chunk-002&lt;SEP&gt;US8655901B1-chunk-000` |
| 732 | Conditional Random Field Model — Label | The conditional random field model is created based at least in part on the labels. | US9218390B2<br>`US9218390B2-chunk-002` |
| 736 | Label — Sentence | One or more sentences are assigned to each label based at least in part on the most probable label sequence. | US9218390B2<br>`US9218390B2-chunk-002` |

N035 · Query · 共享宽类 · 2 篇

**判定：**两来源均指为获取信息而提出的查询请求：备份数据管理查询与用于模式挖掘/翻译的搜索query。前者未限定自然语言格式，后者明确token/语言结构；共同信息查询类仍成立，不能仅因处理流程不同判异义。

**类与实例：**共同类为信息检索查询请求；备份管理查询实例不应被默认分词或翻译，语言模式挖掘query也不能默认访问备份数据库。原始边的source_id可区分这些条件。

**原图类型：**concept；**置信度：**高；**文件：**US7756837B2.txt, US8655901B1.txt

**US7756837B2 · Claim 13**
receiving at least one query from a party concerning the archived data-stream; formulating one or more responses to the query based on an analysis of the management data stored in the database;
来自请求方、关于已归档数据流的查询；通过分析管理数据库形成响应，并可经网络收发。
来源 Chunk：US7756837B2-chunk-000, US7756837B2-chunk-001, US7756837B2-chunk-002

**US8655901B1 · Claim 1**
segmenting a given query among the collection into one or more tokens in the first language, wherein each token includes one or more terms from the given query;
从query log识别、切分、标注、翻译的搜索query，也包括用翻译模式解释的新query。
来源 Chunk：US8655901B1-chunk-000, US8655901B1-chunk-001

**邻边审阅：**已逐条检查全部实际邻边及其source_id/file_path；各关系在所属专利中有对应陈述，未发现将另一专利特征直接写入本专利边描述的确证。共同节点容许潜在无作用域路径组合，但本审计没有执行或观察该传播。

**局限：**['本结果为AI辅助逐来源语义审阅，不是独立人工金标准；分类依赖所声明的类/实例粒度。', '只审计第二轮既有20篇索引中的可见原chunk、原抽取与实际图邻边；原文范围为已索引的标题、摘要及Claims，未额外读取完整说明书或新语料，未调用模型API，也未进行新的检索/生成传播测试。', '共享节点产生跨专利邻接不等于已观察到错误跨文档推理；边的source_id和file_path应保持作用域。']

实际邻边端点、描述与来源（14 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 112 | Communication Network — Query | The query is received electronically over a communication network.&lt;SEP&gt;The query is received electronically over the communication network and responses are transmitted electronically over it. | US7756837B2<br>`US7756837B2-chunk-001&lt;SEP&gt;US7756837B2-chunk-002` |
| 253 | Token — Query | A given query among the collection is segmented into one or more tokens in the first language. | US8655901B1<br>`US8655901B1-chunk-000` |
| 313 | Processor — Query | The processor receives a query from a party and formulates responses based on analysis of the management data stored in the database. | US7756837B2<br>`US7756837B2-chunk-001` |
| 706 | Tokens — Query | A given query among the collection is segmented into one or more tokens in the first language. | US8655901B1<br>`US8655901B1-chunk-001` |
| 709 | Labels — Query | Annotating each query includes labeling portions of the query according to the first query pattern. | US8655901B1<br>`US8655901B1-chunk-001` |
| 758 | Management Data — Query | Responses to the query are formulated based on an analysis of the management data stored in the database. | US7756837B2<br>`US7756837B2-chunk-000&lt;SEP&gt;US7756837B2-chunk-002` |
| 769 | Query — Party | The query is received from a party concerning the archived data-stream.&lt;SEP&gt;The party submits a query concerning the archived data-stream. | US7756837B2<br>`US7756837B2-chunk-000&lt;SEP&gt;US7756837B2-chunk-001` |
| 770 | Query — Translation-Based Query Pattern Mining | The method identifies a collection of queries, segments and annotates each query with labels, and translates the annotated queries into a second language. | US8655901B1<br>`US8655901B1-chunk-000` |
| 771 | Query — First Language | The collection of queries matching the query pattern is in the first language. | US8655901B1<br>`US8655901B1-chunk-000` |
| 772 | Query — Second Language | The collection of annotated queries in the first language is translated into a translated collection of queries in a second language. | US8655901B1<br>`US8655901B1-chunk-000&lt;SEP&gt;US8655901B1-chunk-001` |
| 773 | Query — Translated Query Pattern | The translated query pattern is applied to a received query to identify query splits into query components.&lt;SEP&gt;The translated query pattern is used to interpret received queries in the second language and applied to a received query to identify query splits. | US8655901B1<br>`US8655901B1-chunk-000&lt;SEP&gt;US8655901B1-chunk-001` |
| 774 | Query — Query Log | Identifying a collection of queries includes identifying queries from a query log that match the first query pattern. | US8655901B1<br>`US8655901B1-chunk-001` |
| 775 | Query — Query Pattern | The query pattern identifies a particular rule to interpret a particular type of query, and a collection of queries matching the query pattern is identified. | US8655901B1<br>`US8655901B1-chunk-001` |
| 776 | Query — Computing Devices | A system comprising one or more computing devices translates the collection of annotated queries into a translated collection of queries. | US8655901B1<br>`US8655901B1-chunk-001` |

N036 · Non-Transitory Computer Storage Medium · 共享宽类 · 2 篇

**判定：**两来源明确描述非暂态计算机存储介质编码程序指令，分别用于知识面板内容处理和query pattern翻译。相同的存储载体类可共享，应用程序功能差异不是媒介词义混并。

**类与实例：**共同存储介质类；两篇中的程序和实际存储实例分别限定，不应解释成同一载体上必然安装两套程序。

**原图类型：**artifact；**置信度：**高；**文件：**US10867122B1.txt, US8655901B1.txt

**US10867122B1 · Claim 6**
A non-transitory computer storage medium encoded with computer program instructions that, when executed by one or more processors, cause a computer device to perform operations comprising:
编码用于内容接收、事实实体识别和知识面板/界面呈现操作的指令。
来源 Chunk：US10867122B1-chunk-000, US10867122B1-chunk-001

**US8655901B1 · Claim 15**
A non-transitory computer storage medium encoded with a computer program, the program comprising instructions that when executed by data processing apparatus cause the data processing apparatus to perform operations comprising:
编码执行查询模式标注与翻译操作的程序。
来源 Chunk：US8655901B1-chunk-001

**邻边审阅：**已逐条检查全部实际邻边及其source_id/file_path；各关系在所属专利中有对应陈述，未发现将另一专利特征直接写入本专利边描述的确证。共同节点容许潜在无作用域路径组合，但本审计没有执行或观察该传播。

**局限：**['本结果为AI辅助逐来源语义审阅，不是独立人工金标准；分类依赖所声明的类/实例粒度。', '只审计第二轮既有20篇索引中的可见原chunk、原抽取与实际图邻边；原文范围为已索引的标题、摘要及Claims，未额外读取完整说明书或新语料，未调用模型API，也未进行新的检索/生成传播测试。', '共享节点产生跨专利邻接不等于已观察到错误跨文档推理；边的source_id和file_path应保持作用域。']

实际邻边端点、描述与来源（2 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 844 | Non-Transitory Computer Storage Medium — Data Processing Apparatus | The storage medium is encoded with a computer program whose instructions, when executed by data processing apparatus, cause the apparatus to perform operations. | US8655901B1<br>`US8655901B1-chunk-001` |
| 845 | Non-Transitory Computer Storage Medium — Computer Program Instructions | The non-transitory computer storage medium is encoded with computer program instructions.&lt;SEP&gt;The non-transitory computer storage medium is encoded with computer program instructions causing a computer device to perform operations. | US10867122B1<br>`US10867122B1-chunk-000&lt;SEP&gt;US10867122B1-chunk-001` |

N037 · Data Processing Apparatus · 共享宽类 · 2 篇

**判定：**两来源的Data Processing Apparatus都是执行数据处理方法的计算装置，分别承担内容相关知识面板和查询模式翻译流程。通用执行设备类相容；没有原文身份等同声明。

**类与实例：**共同可执行数据处理的装置类；两篇文档内装置是独立实施例。US10867122B1中Claim1的apparatus与Claim6的computer device可以有类级近义解释，但不能据此证明实际个体相同。

**原图类型：**artifact；**置信度：**高；**文件：**US10867122B1.txt, US8655901B1.txt

**US10867122B1 · Claim 1**
A method performed by a data processing apparatus, the method comprising:
接收用户输入内容、确定事实实体、请求相关界面内容并提供显示指令的方法执行者。
来源 Chunk：US10867122B1-chunk-000

**US8655901B1 · Claim 15**
instructions that when executed by data processing apparatus cause the data processing apparatus to perform operations comprising:
执行存储介质中程序、完成query pattern翻译的方法执行装置。
来源 Chunk：US8655901B1-chunk-001

**邻边审阅：**已逐条检查全部实际邻边及其source_id/file_path；各关系在所属专利中有对应陈述，未发现将另一专利特征直接写入本专利边描述的确证。共同节点容许潜在无作用域路径组合，但本审计没有执行或观察该传播。

**局限：**['本结果为AI辅助逐来源语义审阅，不是独立人工金标准；分类依赖所声明的类/实例粒度。', '只审计第二轮既有20篇索引中的可见原chunk、原抽取与实际图邻边；原文范围为已索引的标题、摘要及Claims，未额外读取完整说明书或新语料，未调用模型API，也未进行新的检索/生成传播测试。', '共享节点产生跨专利邻接不等于已观察到错误跨文档推理；边的source_id和file_path应保持作用域。', 'edge848的端点名称是抽取时把computer device用Data Processing Apparatus概括；作为共同计算设备类可解释，作为同一个体等同则缺乏证明。']

实际邻边端点、描述与来源（4 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 844 | Non-Transitory Computer Storage Medium — Data Processing Apparatus | The storage medium is encoded with a computer program whose instructions, when executed by data processing apparatus, cause the apparatus to perform operations. | US8655901B1<br>`US8655901B1-chunk-001` |
| 846 | Data Processing Apparatus — Factual Entity | The data processing apparatus performs the method of determining factual entities from received content. | US10867122B1<br>`US10867122B1-chunk-000` |
| 847 | Data Processing Apparatus — Knowledge Panel | The data processing apparatus requests content for a user interface element related to the factual entities. | US10867122B1<br>`US10867122B1-chunk-000` |
| 848 | Data Processing Apparatus — Computer Program Instructions | The computer program instructions, when executed by processors, cause a computer device to perform operations including determining factual entities. | US10867122B1<br>`US10867122B1-chunk-000` |

N038 · Computing Devices · 共享宽类 · 2 篇

**判定：**两来源均指执行计算/程序操作的一台或多台设备；ETL历史事件触发与查询翻译属于不同应用，不能据此判设备概念误并。

**类与实例：**共同计算设备类；ETL服务中的设备集合与query翻译系统中的设备集合是各自文档局部实例，不表示同一部署或同一机器。

**原图类型：**artifact；**置信度：**高；**文件：**US11423041B2.txt, US8655901B1.txt

**US11423041B2 · Claim 15**
storing program instructions that when executed on or across one or more computing devices, cause the one or more computing devices to implement:
执行数据目录记录、条件评估及ETL事件触发指令的一台或多台设备。
来源 Chunk：US11423041B2-chunk-001

**US8655901B1 · Claim 15**
translating, with a system comprising one or more computing devices, the collection of annotated queries in the first language into a translated collection of queries in a second language;
构成系统来翻译已标注query集合的计算设备。
来源 Chunk：US8655901B1-chunk-001

**邻边审阅：**已逐条检查全部实际邻边及其source_id/file_path；各关系在所属专利中有对应陈述，未发现将另一专利特征直接写入本专利边描述的确证。共同节点容许潜在无作用域路径组合，但本审计没有执行或观察该传播。

**局限：**['本结果为AI辅助逐来源语义审阅，不是独立人工金标准；分类依赖所声明的类/实例粒度。', '只审计第二轮既有20篇索引中的可见原chunk、原抽取与实际图邻边；原文范围为已索引的标题、摘要及Claims，未额外读取完整说明书或新语料，未调用模型API，也未进行新的检索/生成传播测试。', '共享节点产生跨专利邻接不等于已观察到错误跨文档推理；边的source_id和file_path应保持作用域。']

实际邻边端点、描述与来源（2 条）

| 边索引 | 真实端点（无向图） | 保存描述 | 公开号与 source_id |
|---|---|---|---|
| 776 | Query — Computing Devices | A system comprising one or more computing devices translates the collection of annotated queries into a translated collection of queries. | US8655901B1<br>`US8655901B1-chunk-001` |
| 849 | Computing Devices — Non-Transitory Computer-Readable Storage Media | The program instructions stored on the storage media are executed on or across the computing devices. | US11423041B2<br>`US11423041B2-chunk-001` |

## 复现与局限

证据包保留原始图快照、GraphML、来源KV、20篇索引文本与Claims、47条缓存抽取和调用191原始记录；同时提供逐节点／逐来源CSV、完整JSON、所有初审、裁决、核验结果及文件SHA256清单。统计脚本只用Python标准库，运行 `python3 round2_multisource_audit/scripts/build_inventory.py`，随后运行 `python3 round2_multisource_audit/scripts/validate_reviews.py --require-complete`。语义分类是保留的AI审阅结论，统计重跑不会自动生成新的人工判断。

本次是单个20专利图的穷尽多源节点审计，不是泛化性能评测；没有独立人工复标、查询干预或instance/sameAs金标准。泛化类与具体概念的边界、Event／Network及局部序号角色的本体选择均可能影响分类。来源完整不等于逐Claim结构已被建模，也不等于每条合并摘要有子句级出处。

 官方版本v1.5.7 · commit 28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c
仅审计第二轮基线；不混用后续边界实验数据。新增模型与Embedding API调用0，新增API费用$0，未读取密钥；未访问或修改FOT、AutoDL、SSH隧道或代理。原始输入哈希复核未变。
