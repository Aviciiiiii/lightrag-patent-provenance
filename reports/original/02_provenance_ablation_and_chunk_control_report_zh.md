<!-- 由 tools/html_to_md.py 从 02_provenance_ablation_and_chunk_control_report_zh.html 生成；表格与正文完整，HTML 中折叠/内嵌的历史快照未转换。 -->

LightRAG专利证据溯源：第三轮控制实验

第三轮 · 2026-10-29 · 生成于 2026-10-29T16:25:58.895994+00:00 · 距本轮起点 24.75 分钟

# LightRAG专利证据溯源
来源字段消融与分块边界对照

**结果：**来源字段让模型识别到正确专利，但不足以恢复Claim编号；加入Claim原文后核心问题答对，引用编号仍出错。人工分块对照中，完整技术关系在同块条件3/3保留、跨块条件0/3保留，局部事实仍存在。原Q11的明确“另一专利”错误没有在A的3次重放中复现。

本轮只复用已保存的Q11上下文和同一专利原文，未重新检索、未重建20篇索引。结果适用于本模型、本提示和这些控制条件，不能推断自然语料中的错误率，也不能归因于2025年论文原始实现。

## 1. 运行与成本

| 项目 | 实际设置 |
|---|---|
| 代码 | 官方v1.5.7，commit `28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c`。抽取提示从未修改的官方源码读取，并与第二轮真实请求逐字校验；响应选择性加载并执行官方未修改的 `_process_extraction_result` 及其全部相关辅助函数/常量；不是正常包导入，详见下文核验范围。 |
| 模型与请求 | SiliconFlow / deepseek-ai/DeepSeek-V4.1-Flash；temperature=0；enable_thinking=false；stream=false；无重试；未提供seed（该端点公开schema未列出seed，不保证确定性）。本轮直接发送等价的OpenAI兼容HTTP JSON，避免无用SDK依赖的本机导入延迟。 |
| 实验规模 | 来源消融3条件×3次=9次；边界对照2条件×3次×2块=12次；总21次LLM、0次Embedding。 |
| 用量 | 输入300,642 tokens；输出6,454；缓存输入254,848；reasoning tokens=0。0调用失败、0输出截断、0未知费用保留。 |
| 新增费用估算 | 缓存计价约¥0.1534；忽略缓存优惠的较高估算¥0.6529。这是按返回usage与公开价格的估计，不是供应商账单。此前预计¥1–2.5，内部硬上限¥10，低于用户$5上限。 |
| 时限与隔离 | 起点16:01:14 UTC，绝对停止18:01:14 UTC。所有付费调用已结束；实验产物写入独立round3。未访问AutoDL/FOT，未改变既有隧道、代理或项目。 |

按[官方价格](https://www.siliconflow.cn/pricing)较高档：输入¥2/百万tokens、输出¥8/百万、缓存输入¥0.04/百万。配置只在运行内存使用；请求日志不含Authorization或密钥。

## 2. 来源字段消融：固定Q11检索结果

固定第二轮补充Q11 mix的API392请求：82个实体、82条关系、20个原文块、13项Reference List。A精确重放其system/user文本及生成参数。每条件3次，顺序ABC / BCA / CAB；输出上限均3500。

| 条件 | 唯一新增内容 | 保留条件 |
|---|---|---|
| A 原始 | 无；原始上下文 | 原实体、关系描述、顺序、原文块、用户问题、指令、引用列表均不变。不重新运行检索。 |
| B 来源增强 | 为全部82条既有关系追加publication_numbers、file_path、source_id。 |  |
| C 来源+原文 | B基础上另加US7991757B2的完整Claim1、Claim27原文；这是额外证据诊断。 |  |

每个source_id都逐一查回存储chunk、full_doc_id、file_path和原始文档字符区间。`&lt;SEP&gt;`连接的是聚合来源，不能推断每句话与某个Claim一一对应。B新增的是三个字段的组合，不能分离其中某个字段的贡献；增加字段也改变上下文长度。

关键既有关系：`External Recommender → Registration Module`；`file_path=US7991757B2.txt`；`source_id=US7991757B2-chunk-000&lt;SEP&gt;US7991757B2-chunk-001`。B未添加Claim文字或Claim编号证据。

| 指标（每条件3次） | A | B | C |
|---|---|---|---|
| 正文肯定性错误来源归属/排除 | 0/3 | 0/3 | 0/3 |
| 正确识别US7991757B2来源 | 0/3 | 3/3 | 3/3 |
| 有证据支持的核心Claim任务完成 | 0/3 | 0/3 | 3/3 |
| 尾部References未提供目标专利证据 | 3/3 | 3/3 | 0/3 |
| 目标专利来源与引用编号同时满足 | 0/3 | 0/3 | 0/3 |
| 引用编号与原映射冲突 | 0/3 | 0/3 | 3/3 |

**解释：**A三次均表示缺少可见来源映射而拒绝将图描述归给目标专利；B三次识别文档来源，但恰当拒绝猜测Claim1/27；C三次答对Claim区别与显式依赖。不能宣称B稳定修复了原API392“different patent family”的肯定性错误，因为该错误在A中没有复现。A/B都附上不支持目标注册能力的其他专利尾部References；由于没有逐句引用，不能把所有正文分别强行对应到其中某项。

**引用限制：**为保持纯消融，三个条件的Reference List均不增补US799；原[1]仍是US10867122B1。C却三次输出`[1] US7991757B2.txt`，即来源文档正确、编号映射冲突。这部分失败受控制设计保留旧引用表的限制，不能表述为“正常新增文档的官方端到端引用必然出错”。正式系统需要同步维护证据来源和引用ID。

**逐字引用：**C的核心Claim结论正确，不等于引号内全是逐字原文。三次均有标点规范化；C1把原文`being provided`写为`are provided`，并加入了明确标为推断但无原文直接支持的机制解释。报告因此分别计内容、逐字性与引用映射。

### 9次逐次对照与实际回答

| 运行 | 公开号归属 | Claim任务 | 引用判定 | 关键实际文本 |
|---|---|---|---|---|
| A1 / API1 | 来源不足，拒绝归属 | 缺Claim原文，拒答 | 尾部列表未提供目标专利证据 | These are associated with registration-related concepts, but the graph does not link them to US7991757B2. |
| A2 / API6 | 来源不足，拒绝归属 | 缺Claim原文，拒答 | 尾部列表未提供目标专利证据 | However, these entities are **not linked** in the provided relationships to US7991757B2 (or to any patent number in the reference list). |
| A3 / API8 | 来源不足，拒绝归属 | 缺Claim原文，拒答 | 尾部列表未提供目标专利证据 | However, these are not tied to US7991757B2 in the supplied evidence. |
| B1 / API2 | 正确 | 缺Claim原文，拒答 | 尾部列表未提供目标专利证据 | US7991757B2 is referenced only through Knowledge Graph relationships, not through any Document Chunk. |
| B2 / API4 | 正确 | 缺Claim原文，拒答 | 尾部列表未提供目标专利证据 | US7991757B2 appears only in the Knowledge Graph relationships, not in the Document Chunks. |
| B3 / API9 | 正确 | 缺Claim原文，拒答 | 尾部列表未提供目标专利证据 | The only evidence relating to that patent is Knowledge Graph relationship data, |
| C1 / API3 | 正确 | 核心完成 | [1]映射冲突；文档名正确 | Claim 27 depends from Claim 1 ("The system of claim 1") and adds a further configuration of the same module: |
| C2 / API5 | 正确 | 核心完成 | [1]映射冲突；文档名正确 | Claim 27 explicitly depends on Claim 1 ("The system of claim 1"), so it narrows the Claim 1 system rather than defining a separate one. |
| C3 / API7 | 正确 | 核心完成 | [1]映射冲突；文档名正确 | The dependency is express — Claim 27 incorporates all limitations of Claim 1 and narrows the registration module. |

A1：完整实际回答

```
I do not have enough information to answer this query. The provided **Context** does not contain any document, knowledge-graph entity, or document chunk for **US7991757B2**. The patent publication number US7991757B2 does not appear anywhere in the supplied evidence, so I cannot quote Claim 1 or Claim 27 of that patent, nor explain their dependency.

**What is present vs. missing:**

- **Present in evidence:** The knowledge graph includes a "Registration Module" entity described as "configured to provide functionality for registering an external recommender with a recommendations service," and a "Registration Submission" entity described as a submission "operative to request registration of recommenders." These are associated with registration-related concepts, but the graph does not link them to US7991757B2.
- **Missing:** Any text of US7991757B2, including its claims, title, or abstract. No document chunk corresponds to it, and the Reference Document List does not include it.

**Explicit evidence vs. inference:** It would be inference—not explicit evidence—to assume that the registration capability described in the knowledge graph belongs to US7991757B2. I will not make that link, since the instructions require stating what is missing rather than inventing connections between patents.

To answer, please provide the text of US7991757B2 (at minimum Claims 1 and 27), or confirm the correct publication number if it was mistyped.

### References

- [1] US10867122B1.txt
- [4] US7756837B2.txt
```

A2：完整实际回答

```
I do not have enough information to answer this query. The provided **Context** does not contain any document, knowledge-graph entity, or document chunk for **US7991757B2**. The patent publication number US7991757B2 does not appear anywhere in the supplied evidence, so I cannot quote Claim 1 or Claim 27 of that patent, nor describe their dependency.

**What is present in the evidence (for transparency):**
- The knowledge graph does contain a "Registration Module" entity described as "configured to provide functionality for registering an external recommender with a recommendations service" and "configured to allow a provider of an external recommender to provide machine readable descriptions of the external recommender," along with "Registration Submission(s)" and "Machine Readable Descriptions" entities.
- However, these entities are **not linked** in the provided relationships to US7991757B2 (or to any patent number in the reference list). The reference documents supplied are US10867122B1, US9374411B1, US8655901B1, US7756837B2, US8095432B1, US9514120B1, US8719408B2, US8069128B2, US11423041B2, US9304738B1, US9218390B2, US9514753B2, and US9118735B1.

**Explicit evidence vs. inference:** It would be an unsupported inference to attribute the registration-related entities above to US7991757B2, since no relationship in the context makes that link. Doing so would invent a connection between patents, which the evidence does not support.

**What is missing:** The text of US7991757B2, including its Claim 1 and Claim 27, and any relationship tying that patent to the registration entities. If you can supply that document or confirm the correct publication number, I can quote the claims and explain their dependency.

### References

- [1] US10867122B1.txt
- [4] US7756837B2.txt
- [5] US8095432B1.txt
```

A3：完整实际回答

```
I do not have enough information to answer this query. The provided **Context** does not contain any document, chunk, or knowledge-graph entity for **US7991757B2**, so I cannot quote Claim 1 or Claim 27 of that patent, nor describe their dependency.

**What is present vs. missing**

- **Present in evidence:** The context includes a "Registration Module" entity described as "configured to provide functionality for registering an external recommender with a recommendations service" and "configured to allow a provider of an external recommender to provide machine readable descriptions of the external recommender," along with "Registration Submission(s)" entities. However, these are not tied to US7991757B2 in the supplied evidence.
- **Missing:** Any text of US7991757B2, its claim set, claim numbering, or dependency language. Without the actual claim wording, any statement about Claim 1's registration capability or Claim 27's added capability would be inference, not evidence.

**Explicit evidence vs. inference**

- Explicit: none of the retrieved chunks mention US7991757B2.
- Inference: linking the "Registration Module" concept to that patent would be speculation, which the instructions prohibit.

To answer, please provide the text of US7991757B2 (at least Claims 1 and 27) or confirm the correct publication number, since the retrieved documents cover different patents (e.g., US10867122B1, US7756837B2, US8880423B2).

### References

- [1] US10867122B1.txt
- [4] US7756837B2.txt
```

B1：完整实际回答

```
I do not have enough information to answer this query. The provided **Context** does not contain the text of Claim 1 or Claim 27 of US7991757B2.

**What the evidence does show (document facts):**
- US7991757B2 is referenced only through Knowledge Graph relationships, not through any Document Chunk. The relationships state that "Registration submissions are operative to request registration of recommenders" and that "The registration module provides functionality for registering an external recommender with the recommendations service," with the registration module "configured to allow a provider of an external recommender to provide machine readable descriptions of the external recommender." These are entity descriptions, not claim language.
- No Document Chunk in the Context corresponds to US7991757B2; the Reference Document List contains no entry for it.

**What is missing:**
- The exact wording of Claim 1 and Claim 27 of US7991757B2.
- Any statement of dependency between Claim 27 and another claim (e.g., "The method of claim 1, further comprising...").

Because the instructions require quoting exact supporting wording and stating claim numbers only when present in the evidence, I cannot supply the requested quotes or characterize the dependency. Any description of Claim 27's added capability would be inference, not evidence, so I have not provided one.

### References

- [1] US10867122B1.txt
- [4] US7756837B2.txt
- [5] US8095432B1.txt
```

B2：完整实际回答

```
I do not have enough information to answer this query. The provided **Context** does not contain the text of Claim 1 or Claim 27 of US7991757B2.

**What the evidence does show:** US7991757B2 appears only in the Knowledge Graph relationships, not in the Document Chunks. Those relationships state that "Registration submissions are operative to request registration of recommenders" and that "The registration module provides functionality for registering an external recommender with the recommendations service," with the registration module "configured to allow a provider of an external recommender to provide machine readable descriptions of the external recommender." These are document-level descriptions, not claim language, and no claim numbers are associated with them.

**What is missing:**
- The actual wording of Claim 1 of US7991757B2.
- The actual wording of Claim 27 of US7991757B2.
- Any statement of Claim 27's dependency (e.g., "The method of claim 1, further comprising...").

Because the claim text is absent, I cannot quote the supporting wording from each claim, cannot verify the dependency, and cannot reliably distinguish explicit claim evidence from inference. Any answer about the specific registration capability in Claim 1 or the added capability in Claim 27 would require inventing content not present in the Context.

### References

- [1] US10867122B1.txt
- [2] US9374411B1.txt
- [3] US8655901B1.txt
- [4] US7756837B2.txt
- [5] US8095432B1.txt
```

B3：完整实际回答

```
I do not have enough information to answer this query. The provided **Context** does not contain the text of US7991757B2's claims. The only evidence relating to that patent is Knowledge Graph relationship data, which states that "Registration submissions are operative to request registration of recommenders" and that "The registration module provides functionality for registering an external recommender with the recommendations service," with machine readable descriptions provided by the recommender's provider. However, no claim numbers, claim language, or dependency wording for US7991757B2 appear in the Document Chunks, so I cannot quote Claim 1 or Claim 27, nor explain their dependency.

**What is missing:** the actual claim text of US7991757B2 (Claim 1 and Claim 27), including any "The system of claim 1..." dependency language. Without that, any statement about Claim 27's added capability would be inference rather than evidence, which the instructions prohibit.

### References

- [1] US10867122B1.txt
- [4] US7756837B2.txt
```

C1：完整实际回答

```
**US7991757B2 — Registration Capabilities in Claims 1 and 27**

**Claim 1 (explicit evidence).** Claim 1 recites a system comprising a "registration module configured to provide functionality for registering an external recommender with a recommendations service." The same claim also requires a "data interface operative to provide access to the event data to a plurality of external recommenders registered with the recommendations service," where those recommenders "are provided by one or more entities that differ from a provider of the recommendations service." So Claim 1's registration capability is the basic function of registering an external recommender with the service.

**Claim 27 (explicit evidence).** Claim 27 depends from Claim 1 ("The system of claim 1") and adds a further configuration of the same module: "wherein the registration module is further configured to allow a provider of an external recommender associated with the plurality of external recommenders to provide machine readable descriptions of the external recommender."

**Dependency and relationship.** The dependency is stated expressly in Claim 27's opening phrase, "The system of claim 1." Because Claim 27 incorporates Claim 1, its added capability is a narrowing limitation on the registration module already recited in Claim 1 — namely, enabling the recommender's provider to supply machine-readable descriptions of that recommender.

**Inference (not explicit).** It can reasonably be inferred that Claim 27's machine-readable descriptions are the mechanism by which an external recommender is registered and made accessible via Claim 1's data interface; however, the claims do not expressly state that link, so this is inference rather than quoted fact.

### References

- [1] US7991757B2.txt
```

C2：完整实际回答

```
**Claim 1 of US7991757B2** specifies a registration module within the claimed system. The claim recites: "a registration module configured to provide functionality for registering an external recommender with a recommendations service." This is the explicit registration capability stated in Claim 1.

**Claim 27** adds a further capability to that module. It recites: "The system of claim 1, wherein the registration module is further configured to allow a provider of an external recommender associated with the plurality of external recommenders to provide machine readable descriptions of the external recommender."

**Dependency:** Claim 27 explicitly depends on Claim 1 ("The system of claim 1"), so it narrows the Claim 1 system rather than defining a separate one. The added limitation concerns who may supply the descriptions (the provider of an external recommender) and what they supply (machine readable descriptions of that recommender).

**Explicit evidence vs. inference:** The quotations above are the explicit evidence. It is an inference—not stated in either claim—that Claim 27's machine readable descriptions are used to configure or register the recommender; the claims do not specify that link. Likewise, the claims do not state any format or content requirements for the descriptions.

### References

- [1] US7991757B2.txt
```

C3：完整实际回答

```
**US7991757B2 — Registration Capability in Claims 1 and 27**

**Claim 1 (explicit evidence).** Claim 1 recites a system comprising a "registration module configured to provide functionality for registering an external recommender with a recommendations service." The same claim also requires a "data interface operative to provide access to the event data to a plurality of external recommenders registered with the recommendations service," where those recommenders are "provided by one or more entities that differ from a provider of the recommendations service." So Claim 1's registration capability is the module-level function of registering an external recommender with the service.

**Claim 27 (explicit evidence).** Claim 27 depends from Claim 1 ("The system of claim 1") and adds a further configuration of that same module: "wherein the registration module is further configured to allow a provider of an external recommender associated with the plurality of external recommenders to provide machine readable descriptions of the external recommender."

**Dependency and added capability.** The dependency is express — Claim 27 incorporates all limitations of Claim 1 and narrows the registration module. The additional capability is that the external recommender's *provider* can supply *machine readable descriptions* of that recommender, rather than registration being only a generic registering function.

**Explicit evidence vs. inference.** The quoted wording above is explicit document evidence. Any statement that Claim 27's machine-readable descriptions are used to configure, parameterize, or invoke the recommenders would be inference, since neither quoted claim states that use; the evidence supports only the capability to provide such descriptions.

### References

- [1] US7991757B2.txt
```

## 3. 人工Chunk边界对照

使用US7991757B2原始Claims字段中连续的Claims26–28，字符区间`[9973,10459)`，486字符、93个o200k_base tokens。不添加、重排或改写任何原文。两种条件均2块、无重叠、独立无状态抽取，提示与参数相同，输出上限均8192，gleaning=0。每条件3次；顺序SAME/CROSS、CROSS/SAME、SAME/CROSS。

| 条件 | 边界 | 每块tokens | 目标关系 |
|---|---|---|---|
| SAME | Claim27与28之间，原Claims字符10329 | 64 + 29 | Claim27整句保留在第一块 |
| CROSS | Claim27内，原Claims字符10270；在“ machine readable descriptions”之前 | 55 + 38 | 第一块以“to provide”结束，第二块从宾语开始 |

每组两次调用的API输入token总数为SAME3721、CROSS3722；原文token总数相同，提示包裹与边界处tokenization造成1-token差异。每块长度和语义完整性随分界变化，无法独立消除。

```
26. The system of claim 1 , wherein the computer system comprises multiple physical computing devices. 27. The system of claim 1 , wherein the registration module is further configured to allow a provider of an external recommender associated with the plurality of external recommenders to provide machine readable descriptions of the external recommender. 28. The system of claim 3 , wherein the content site selects at least some of the weights to assign to the external recommenders.
```

| 配对重复 | SAME完整关系 | CROSS完整关系 | 直接Module–Descriptions边 | 输出截断 |
|---|---|---|---|---|
| 1 | 保留 | 未保留 | 两条件均无；SAME以Module–Provider关系描述表达 | 无 |
| 2 | 保留 | 未保留 | 两条件均无；SAME以Module–Provider关系描述表达 | 无 |
| 3 | 保留 | 未保留 | 两条件均无；SAME以Module–Provider关系描述表达 | 无 |

**判据：**主指标接受任何官方解析关系中忠实表达“registration module允许provider提供该recommender的machine readable descriptions”；不要求固定实体端点。直接Module–Descriptions边在两条件均0/3，若只做字符串端点匹配会把SAME的成功误判为失败。

SAME的实际关系描述包括：“The registration module is configured to allow a provider of an external recommender to provide machine readable descriptions.” CROSS的对应描述仅为：“The registration module is configured to allow a provider of an external recommender to provide something.” 原始响应已出现差异，官方解析器保留各自结果，因而本对照中的完整关系缺失发生在局部抽取阶段，而非解析、图索引或检索阶段。

**边界：**CROSS仍保留模块、provider、external recommender及机器可读描述的部分节点/关系片段，不能称全部事实消失。未运行跨块联合重抽取、图合并恢复或最终问答，不能断言下游必然无法恢复。显式Claim27→Claim1法律依赖边两条件均未物化，默认本体也未要求Claim实体；这不是本对照的技术关系主指标。

这是93-token短片段上、零重叠、句内切分的人工压力测试。它与第二轮自然1200-token/100-overlap分块不同；第二轮原Claim1/27跨块时技术关系曾成功保留。本轮可支持“特定人工边界会使独立抽取遗漏完整关系”，不能给出自然分块频率或宣称论文原始方法缺陷。

### 12次抽取原始输出

SAME / 重复1 / 块0 / API10 / stop

```
entity<|#|>Computer System<|#|>Artifact<|#|>A system comprising multiple physical computing devices, referenced in the claims.
entity<|#|>Registration Module<|#|>Artifact<|#|>A module configured to allow a provider of an external recommender to provide machine readable descriptions of the external recommender.
entity<|#|>External Recommender<|#|>Artifact<|#|>One of a plurality of external recommenders associated with a provider who can supply machine readable descriptions of it.
entity<|#|>Provider<|#|>Person<|#|>A provider of an external recommender who is allowed to provide machine readable descriptions of the external recommender.
entity<|#|>Machine Readable Descriptions<|#|>Data<|#|>Descriptions of an external recommender that a provider is allowed to provide in machine readable form.
relation<|#|>Computer System<|#|>Multiple Physical Computing Devices<|#|>comprises, includes<|#|>The computer system comprises multiple physical computing devices.
relation<|#|>Registration Module<|#|>Provider<|#|>allows, configured to allow<|#|>The registration module is configured to allow a provider of an external recommender to provide machine readable descriptions.
relation<|#|>Provider<|#|>External Recommender<|#|>provides, associated with<|#|>The provider provides an external recommender associated with the plurality of external recommenders.
relation<|#|>Provider<|#|>Machine Readable Descriptions<|#|>provides, supplies<|#|>The provider provides machine readable descriptions of the external recommender.
relation<|#|>Machine Readable Descriptions<|#|>External Recommender<|#|>describes, describes<|#|>The machine readable descriptions describe the external recommender.
<|COMPLETE|>
```

SAME / 重复1 / 块1 / API11 / stop

```
entity<|#|>Content Site<|#|>Organization<|#|>A site that selects at least some of the weights to assign to external recommenders, as described in the claim.
entity<|#|>External Recommenders<|#|>Concept<|#|>Entities to which weights are assigned by the content site.
entity<|#|>Weights<|#|>Data<|#|>Values assigned to external recommenders, at least some of which are selected by the content site.
relation<|#|>Content Site<|#|>External Recommenders<|#|>weight assignment, selection<|#|>The content site selects at least some of the weights to assign to the external recommenders.
relation<|#|>Content Site<|#|>Weights<|#|>selection<|#|>The content site selects at least some of the weights.
relation<|#|>Weights<|#|>External Recommenders<|#|>assignment<|#|>The weights are assigned to the external recommenders.
<|COMPLETE|>
```

SAME / 重复2 / 块0 / API16 / stop

```
entity<|#|>Computer System<|#|>Artifact<|#|>A computer system referenced in claim 1 that, in this claim, comprises multiple physical computing devices.
entity<|#|>Registration Module<|#|>Artifact<|#|>A module of the system of claim 1 that is configured to allow a provider of an external recommender to provide machine readable descriptions of the external recommender.
entity<|#|>External Recommender<|#|>Artifact<|#|>A recommender external to the system, one of a plurality of external recommenders, whose provider may provide machine readable descriptions of it via the registration module.
entity<|#|>Provider<|#|>Person<|#|>A provider of an external recommender associated with the plurality of external recommenders, allowed by the registration module to provide machine readable descriptions of the external recommender.
entity<|#|>Machine Readable Descriptions<|#|>Data<|#|>Descriptions of an external recommender that a provider is allowed to provide in machine readable form.
relation<|#|>Computer System<|#|>Registration Module<|#|>component, configuration<|#|>The registration module is a module of the computer system of claim 1 and is configured to allow providers to provide machine readable descriptions.
relation<|#|>Registration Module<|#|>Provider<|#|>allows, configuration<|#|>The registration module is configured to allow a provider of an external recommender to provide machine readable descriptions of the external recommender.
relation<|#|>Provider<|#|>External Recommender<|#|>provides, association<|#|>The provider is a provider of an external recommender associated with the plurality of external recommenders.
relation<|#|>Provider<|#|>Machine Readable Descriptions<|#|>provides<|#|>The provider is allowed to provide machine readable descriptions of the external recommender.
relation<|#|>Machine Readable Descriptions<|#|>External Recommender<|#|>describes<|#|>The machine readable descriptions describe the external recommender.
relation<|#|>Computer System<|#|>External Recommender<|#|>association<|#|>The external recommender is one of the plurality of external recommenders associated with the system.
<|COMPLETE|>
```

SAME / 重复2 / 块1 / API17 / stop

```
entity<|#|>Content Site<|#|>Organization<|#|>A site that selects at least some of the weights to assign to external recommenders, as described in the claim.
entity<|#|>External Recommenders<|#|>Concept<|#|>Entities to which weights are assigned by the content site.
entity<|#|>Weights<|#|>Data<|#|>Values assigned to external recommenders, at least some of which are selected by the content site.
relation<|#|>Content Site<|#|>External Recommenders<|#|>weight assignment, recommendation<|#|>The content site selects at least some of the weights to assign to the external recommenders.
relation<|#|>Content Site<|#|>Weights<|#|>selection, assignment<|#|>The content site selects at least some of the weights.
relation<|#|>Weights<|#|>External Recommenders<|#|>assignment<|#|>The weights are assigned to the external recommenders.
<|COMPLETE|>
```

SAME / 重复3 / 块0 / API18 / stop

```
entity<|#|>Computer System<|#|>Artifact<|#|>A system comprising multiple physical computing devices, as described in the claims.
entity<|#|>Registration Module<|#|>Artifact<|#|>A module configured to allow a provider of an external recommender to provide machine readable descriptions of the external recommender.
entity<|#|>External Recommender<|#|>Artifact<|#|>One of a plurality of external recommenders associated with the system, whose provider may provide machine readable descriptions.
entity<|#|>Provider<|#|>Person<|#|>A provider of an external recommender who is allowed to provide machine readable descriptions of the external recommender.
entity<|#|>Machine Readable Descriptions<|#|>Data<|#|>Descriptions of an external recommender that a provider is allowed to provide in machine readable form.
relation<|#|>Computer System<|#|>Registration Module<|#|>comprises, contains<|#|>The computer system comprises the registration module.
relation<|#|>Registration Module<|#|>Provider<|#|>allows, enables<|#|>The registration module is configured to allow a provider of an external recommender to provide machine readable descriptions.
relation<|#|>Provider<|#|>External Recommender<|#|>provides, associated with<|#|>The provider is a provider of an external recommender associated with the plurality of external recommenders.
relation<|#|>Provider<|#|>Machine Readable Descriptions<|#|>provides<|#|>The provider is allowed to provide machine readable descriptions of the external recommender.
relation<|#|>Machine Readable Descriptions<|#|>External Recommender<|#|>describes<|#|>The machine readable descriptions describe the external recommender.
<|COMPLETE|>
```

SAME / 重复3 / 块1 / API19 / stop

```
entity<|#|>Content Site<|#|>Organization<|#|>A site that selects at least some of the weights to assign to external recommenders, as described in the claim.
entity<|#|>External Recommenders<|#|>Organization<|#|>Entities that receive weights assigned by the content site.
entity<|#|>Weights<|#|>Data<|#|>Values assigned to external recommenders, at least some of which are selected by the content site.
relation<|#|>Content Site<|#|>External Recommenders<|#|>weight assignment, selection<|#|>The content site selects at least some of the weights to assign to the external recommenders.
relation<|#|>Content Site<|#|>Weights<|#|>selection, assignment<|#|>The content site selects at least some of the weights.
relation<|#|>Weights<|#|>External Recommenders<|#|>assignment<|#|>The weights are assigned to the external recommenders.
<|COMPLETE|>
```

CROSS / 重复1 / 块0 / API12 / stop

```
entity<|#|>Computer System<|#|>Artifact<|#|>A system comprising multiple physical computing devices, referenced in the claims.
entity<|#|>Registration Module<|#|>Artifact<|#|>A module configured to allow a provider of an external recommender to provide something, referenced in the claims.
entity<|#|>External Recommender<|#|>Artifact<|#|>One of a plurality of external recommenders associated with a provider.
entity<|#|>Provider<|#|>Person<|#|>A provider of an external recommender associated with the plurality of external recommenders.
relation<|#|>Computer System<|#|>Multiple Physical Computing Devices<|#|>comprises, includes<|#|>The computer system comprises multiple physical computing devices.
relation<|#|>Registration Module<|#|>Provider<|#|>allows, permits<|#|>The registration module is configured to allow a provider of an external recommender to provide something.
relation<|#|>Provider<|#|>External Recommender<|#|>provides, associated with<|#|>The provider provides an external recommender associated with the plurality of external recommenders.
<|COMPLETE|>
```

CROSS / 重复1 / 块1 / API13 / stop

```
entity<|#|>External Recommender<|#|>Artifact<|#|>An external recommender that is described in machine readable descriptions and to which weights are assigned by the content site.
relation<|#|>Content Site<|#|>External Recommender<|#|>weight assignment, configuration<|#|>The content site selects at least some of the weights to assign to the external recommenders.
<|COMPLETE|>
```

CROSS / 重复2 / 块0 / API14 / stop

```
entity<|#|>Computer System<|#|>Artifact<|#|>A computer system referenced in claim 1 that, in this claim, comprises multiple physical computing devices.
entity<|#|>Registration Module<|#|>Artifact<|#|>A module of the system that is further configured to allow a provider of an external recommender to provide something.
entity<|#|>External Recommender<|#|>Artifact<|#|>An external recommender belonging to a plurality of external recommenders, whose provider is allowed by the registration module to provide something.
entity<|#|>Provider<|#|>Person<|#|>A provider of an external recommender associated with the plurality of external recommenders.
relation<|#|>Computer System<|#|>Multiple Physical Computing Devices<|#|>comprises, composition<|#|>The computer system comprises multiple physical computing devices.
relation<|#|>Registration Module<|#|>Provider<|#|>allows, configuration<|#|>The registration module is configured to allow a provider of an external recommender to provide something.
relation<|#|>Provider<|#|>External Recommender<|#|>provides, association<|#|>The provider is a provider of an external recommender associated with the plurality of external recommenders.
<|COMPLETE|>
```

CROSS / 重复2 / 块1 / API15 / stop

```
entity<|#|>External Recommender<|#|>Concept<|#|>An external recommendation source whose behavior is described in machine readable descriptions and to which weights are assigned.
entity<|#|>Content Site<|#|>Concept<|#|>A site that selects at least some of the weights to assign to the external recommenders.
entity<|#|>Machine Readable Descriptions<|#|>Data<|#|>Structured descriptions of the external recommender that can be processed by a machine.
entity<|#|>Weights<|#|>Data<|#|>Values assigned to external recommenders, at least some of which are selected by the content site.
relation<|#|>Content Site<|#|>External Recommender<|#|>weight assignment, selection<|#|>The content site selects at least some of the weights to assign to the external recommenders.
relation<|#|>Machine Readable Descriptions<|#|>External Recommender<|#|>description<|#|>The machine readable descriptions describe the external recommender.
relation<|#|>Content Site<|#|>Weights<|#|>selection<|#|>The content site selects at least some of the weights.
relation<|#|>Weights<|#|>External Recommender<|#|>assignment<|#|>The weights are assigned to the external recommenders.
<|COMPLETE|>
```

CROSS / 重复3 / 块0 / API20 / stop

```
entity<|#|>Computer System<|#|>Artifact<|#|>A system comprising multiple physical computing devices, referenced in the claims.
entity<|#|>Registration Module<|#|>Artifact<|#|>A module configured to allow a provider of an external recommender to provide something, referenced in the claims.
entity<|#|>External Recommender<|#|>Artifact<|#|>One of a plurality of external recommenders associated with a provider, referenced in the claims.
entity<|#|>Provider<|#|>Person<|#|>A provider of an external recommender associated with the plurality of external recommenders.
relation<|#|>Computer System<|#|>Multiple Physical Computing Devices<|#|>comprises, includes<|#|>The computer system comprises multiple physical computing devices.
relation<|#|>Registration Module<|#|>Provider<|#|>allows, enables<|#|>The registration module is configured to allow a provider of an external recommender to provide something.
relation<|#|>Provider<|#|>External Recommender<|#|>provides, associated with<|#|>The provider provides an external recommender associated with the plurality of external recommenders.
<|COMPLETE|>
```

CROSS / 重复3 / 块1 / API21 / stop

```
entity<|#|>External Recommender<|#|>Concept<|#|>An external recommendation system whose behavior is described in machine readable descriptions.
relation<|#|>Content Site<|#|>External Recommender<|#|>weight assignment, selection<|#|>The content site selects at least some of the weights to assign to the external recommenders.
entity<|#|>Content Site<|#|>Concept<|#|>A site that selects at least some of the weights to assign to external recommenders.
<|COMPLETE|>
```

## 4. 归因与下一步研究

| 观察 | 支持的归因 | 不能推出 |
|---|---|---|
| B恢复文档来源 | 固定检索结果下，将已有关系来源传入回答上下文可改善本案例的文档归属。 | 不能分离三个字段各自贡献；不能宣称原肯定性错误已稳定修复。 |
| C完成核心Claim问题 | 原始Claim证据补足了编号、依赖和原文表达。 | 不能把改善全归给来源字段；不能宣称逐字引用和引用ID可靠。 |
| C引用[1]冲突 | 回答生成没有保持冻结引用表的映射；控制设计本身缺少新增文档的有效ID。 | 不能当成正常官方端到端新增证据的无条件失败率。 |
| CROSS未保留完整技术关系 | 相同原文与调用数下，人工句内边界改变局部抽取的可见证据。 | 不能当成全部事实丢失、自然chunk失败率，或下游不可恢复。 |

有价值的方向是：把聚合source_id进一步细化为可核验的Claim/字符区间支持；让图描述、原始证据和引用ID在检索与生成间同步；以跨块证据链恢复代替单纯实体名匹配；用严格区分文档归属、Claim定位、引文逐字性和引用映射的评估，识别错误真正发生的位置。

## 5. 复现与核验范围

**解析执行限制：**正常导入官方operate模块时，本机无关的NumPy/PyYAML/NetworkX文件读取长时间停滞，已停止这些进程；没有修改依赖、官方源码或重新安装。替代路径直接编译执行原源码中未修改的AST函数、辅助函数和常量，记录源码区间与哈希，并使用同名标准logger。对第二轮正常官方解析的API191，已核对42/34节点/边组总数、保存的13个节点组和4个边组（5条记录）完全一致，以及被截断边同样缺失。第二轮未保存的其余记录无法逐项比较，因此不宣称对所有可能输入证明等价。

证据包保存A/B/C完整请求、逐字段diff、82条关系逐source_id核验、Claim字符区间、21次实际请求与完整供应商JSON响应、usage账本、两种分界与token区间、官方解析节点/边、评分脚本和报告。第二轮原始记录不覆盖，索引哈希前后核对。所有核验为AI辅助逐证据复核与程序断言，未声称独立人工标注或统计显著性。

A/B/C判据于16:08:44写入condition_manifest，早于调用。合并evaluation_protocol文件于16:12:40写入，比9次调用结束晚3秒、早于主执行者阅读回答；不把这个后写文件伪装成预注册。分块目标用词在首次分块调用前纠正为原文的“external recommender”，未依据分块结果调整判据。温度0与缓存不等于独立随机重复。

## （已删去）

此处删去一段与实验无关的个人申请材料（研究兴趣段落）。

参考：[Dis2Pat](https://huggingface.co/datasets/lj408/Dis2Pat)；[US7991757B2](https://patents.google.com/patent/US7991757B2/en)；[本次官方源码](https://github.com/HKUDS/LightRAG/tree/28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c)；[LightRAG论文v3](https://arxiv.org/pdf/2410.05779v3)。本次结果属于所记录的当前代码和实验条件。

第二轮完整报告（保留原结果与10题对照）

第二轮 · 起点 2026-10-29 14:13:44 UTC · 报告生成 15:11:28 UTC · 截至报告用时 57.7 分钟 · 硬停止 16:13:44 UTC

# LightRAG 专利证据溯源
第二轮实际实验报告

**官方 v1.5.7 已实际完成 20 篇专利索引和真实问答。**
基线 10 题 × naive/mix 共 20 条回答，两模式各完成 9/10 项核心任务；Q06 因证据未进入上下文而未完成比较。另保留一项自然跨块补充题及检索预算敏感性检查。发现可核验的来源呈现/归属问题与一次配置导致的抽取截断，**没有证明跨 Chunk 导致关系丢失**，也不据此宣称某模式普遍更优。

**20 / 48**专利 / 实际块

**612 / 994**图节点 / 图边

**20 + 2 + 4**基线 / 补充 / 敏感性回答

**¥1.56–1.77**估算新增费用，非账单

## A. 实验完成情况、配置与成本

本轮复用第一轮全部数据和已取得的官方源码，没有重新下载专利或部署新模型。先分别调用 Completion 和 Embedding：实际返回 OK 与有效 1×1024 向量；随后 2 篇冒烟索引达到 processed，得到 71 节点/90 边，并完成 naive/mix 真实问答。官方查询门槛最晚于 **14:26:12 UTC** 满足，早于 15:13:44。20 篇基线运行从 14:27:54 至 14:42:21 UTC；所有 API 调用区间为 14:21:39–14:52:26 UTC。

第一轮于 13:45:45 UTC 因没有模型服务提前停止；其原始记录和本地报告完整保留，本轮不覆盖原证据。本轮从用户指定安全配置文件临时读取服务设置，密钥未写入报告、代码、日志或持久环境。全程未访问 AutoDL，未触碰 FOT、既有进程、权重、SSH 隧道或代理。

| 项目 | 实际设置 / 完成证据 |
|---|---|
| 官方版本 | v1.5.7，API 0344；commit `28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c`。直接导入该固定源码；索引与基线阶段显式断言版本 1.5.7，补充阶段复用同一固定源码路径，官方源码未修改。已安装分发包元数据仍为第一轮 1.5.8，但运行导入路径明确指向 v1.5.7；不混称两个版本。 |
| 数据 | [Dis2Pat](https://huggingface.co/datasets/lj408/Dis2Pat)，20 个去重英文公开号，信息检索/推荐/上下文排序/数据索引方向，438 条编号 Claims。完整标题、摘要、Claims 独立写入，file_paths 为公开号.txt。specification 仅原始保存；生成的 disclosure 未入索引。 |
| 数据核验范围 | 全部摘要与 Google Patents 匹配；19/20 Claims 全文在仅规范空白后匹配。US8509827B2 Claims 2/3 原始来源缺父 Claim 编号；US9218390B2 Claims 10/11 公式存在编码乱码。均未补写，主问题避开这些内容；后述截断案例位于不受该乱码影响的 Claim 2。 |
| LLM / Embedding | SiliconFlow OpenAI-compatible 接口；`deepseek-ai/DeepSeek-V4.1-Flash`，`BAAI/bge-m3`，Embedding 为 1024 维，每项输入限制为 8192 tokens。记录请求和返回模型别名；供应商公告称别名指向 1017 版本，但没有独立验证服务内部构建。 |
| 实际分块与索引 | 固定 1200 tokens、overlap 100；tokenizer 为 o200k_base（gpt-4o-mini 仅 tokenizer 标识）。42,087 输入 tokens→48 个实际块；48/48 与原文区间精确一致。JSON KV、NanoVectorDB、NetworkX；20 processed、0 failed；612 节点、994 边，来源块 ID 无悬空引用。 |
| 抽取与生成 | 官方默认抽取提示；额外 gleaning=0（源码默认为 1，属于本次限制）。temperature=0，最大输出 3500 tokens，thinking=false；SDK 自动重试=0，全局调用并发=2。出现 1 次输出截断，未当作无损抽取。 |
| 基线查询 | naive/mix 使用相同模型、问题、提示和总预算。top_k=12，chunk_top_k=8，实体/关系预算各 2000，总上下文 8000；rerank=false。采用官方 `aquery_llm` 保存同次回答和结构化证据，不把另一次检索冒充原回答上下文。 |
| 成本与停止保护 | 95 次 LLM、297 次 Embedding；实际返回 LLM 输入 421,530、输出 115,419 tokens，缓存命中输入 105,856，reasoning=0；服务失败=0、缺 usage=0。人民币10元累计预算、独立硬截止、关闭自动重试；不存在不确定待结算请求。 |

按 [官方峰时价格](https://www.siliconflow.cn/pricing)，LLM 输入 ¥2/M、输出 ¥8/M、缓存命中 ¥0.04/M，bge-m3 免费。考虑返回缓存量的估算为 ¥1.5589；完全不计缓存优惠的保守估算为 ¥1.7664。按 [当日参考中间价 6.7147 CNY/USD](https://www.chinamoney.com.cn/chinese/)，约 $0.23–$0.26；不是实际结算账单。最初预估 ¥2–6，实际估算更低，低于 $5 上限。

## B. 逐问题对照

审阅为 AI 辅助逐条原文检查，加上精确子串、Claim 归属、引用映射和中间结果核对；不是独立人工金标准。表内“核心正确”不表示每个额外句子或每个标点都逐字正确。点击各格可查看真实完整回答。E/R/C 分别是同次返回的实体、关系、原文块数量。

```
**Answer**

The patent is **US9514753B2**, titled "Speaker identification using hash-based indexing."

**Stated facts (from the document):**

- Claim 1 recites: "determining hash values for the utterance vector according to multiple different hash functions; determining a set of speaker vectors from a plurality of hash tables using the hash values."
- Claim 1 further recites: "selecting a speaker vector based on comparing the speaker vectors in the set with the utterance vector; determining a speaker identity corresponding to the selected speaker vector; and outputting data indicating the speaker identity."
- The abstract describes the same approach: "Hash values are determined for the utterance vector according to multiple different hash functions. A set of speaker vectors from a plurality of hash tables is determined using the hash values."

**Inference (not stated in the document):**

- Because Claim 1 combines multiple hash functions, multiple hash tables, speaker-vector selection, and output of a speaker identity in a single claim, it is the claim that most directly matches the query's combination of features. This is my comparison, not an explicit statement in the source.

**Missing/insufficient evidence:** The provided context does not show equivalent hash-function/hash-table speaker-identification claims in the other documents, so no cross-patent comparison beyond this one can be confirmed.

### References

- [1] US9514753B2.txt
```

```
**Patent identified:** US9514753B2, titled "Speaker identification using hash-based indexing."

**Stated facts (from the document):**

- The abstract describes obtaining "an utterance vector that is derived from an utterance," determining "hash values for the utterance vector according to multiple different hash functions," and determining "a set of speaker vectors from a plurality of hash tables using the hash values."
- Claim 1 recites the full sequence: "determining hash values for the utterance vector according to multiple different hash functions; determining a set of speaker vectors from a plurality of hash tables using the hash values... comparing the speaker vectors in the set with the utterance vector; selecting a speaker vector based on comparing the speaker vectors in the set with the utterance vector; determining a speaker identity corresponding to the selected speaker vector; and outputting data indicating the speaker identity."
- Claim 6 states the hash values may be determined "using one or more locality sensitive hash functions," and Claim 7 states they may be based on "a position of the utterance vector with respect to different hyperplanes."
- Claim 9 describes comparing via "similarity scores that each indicate a degree of similarity of the utterance vector and one of the speaker vectors in the set," selecting the most similar vector.

**Inference (not stated in the document):**

- That US9514753B2 is the only patent in this collection matching the described hash-based speaker-identification approach is an inference from the provided evidence: the other documents (US8655901B1 on translation-based query pattern mining; US8880423B2 on advertisement inventory estimation) contain no speaker-vector or hash-table speaker identification claims. The evidence does not establish links between these patents.

### References

- [1] US9514753B2.txt
```

```
**Answer**

The patent is **US11423041B2**, titled *Maintaining data lineage to detect data events*. The relevant subject matter appears in **claim 1** (system claim), with corresponding method and media claims (claims 8 and 15).

**Stated facts (quoted from the evidence):**

- Claim 1 recites a data catalog configured to "receive, at the data catalog, an indication of a first ETL process applied to one or more source data objects to generate one or more transformed data objects."
- It further recites storing "an instance of a history object in a history data structure according to the received indication," where the history object is "created in the history data structure to specify information expected to be stored to describe the performance of the first ETL process."
- The catalog then "evaluate[s] … the stored information that describes the performance of the first ETL process in the instance of the history object with respect to criteria for triggering an event to perform a second ETL process subscribed to the event."
- Upon determining the criteria are satisfied, the catalog "cause[s] the second ETL process to be performed."

**Inference (not stated as such in the document):** The claim structure implies the history object functions as the monitoring anchor for event registration, since the event is described as "registered for monitoring with regard to the history object." This is a characterization of how the claim elements relate, not an explicit statement in the text.

**Missing/insufficient evidence:** The provided context does not establish any link between US11423041B2 and the other listed patents (US8655901B1, US9118735B1, US7756837B2); no comparison is supported.

### References

- [1] US11423041B2.txt
```

```
**Answer**

The patent that describes this arrangement is **US11423041B2**, titled "Maintaining data lineage to detect data events."

**Stated facts (from the document):**

- **Claim 1** of US11423041B2 recites a system implementing "a data catalog for an Extract, Transform, Load (ETL) service," configured to "store, in the data catalog, an instance of a history object in a history data structure according to the received indication, the history object created in the history data structure to specify information expected to be stored to describe the performance of the first ETL process."
- The same claim states the data catalog is configured to "evaluate, in the data catalog, the stored information that describes the performance of the first ETL process in the instance of the history object with respect to criteria for triggering an event to perform a second ETL process subscribed to the event."
- It further recites: "in response to the determination that the performance of the first ETL process satisfies the criteria for triggering the event, cause the second ETL process to be performed."
- The event is described as "registered for monitoring with regard to the history object."

**Inference (not stated as such in the document):**

- The history object therefore functions as the monitoring anchor that links the first ETL process's recorded performance to the triggering of the subscribed second ETL process. This is a characterization of how the recited elements combine, not an explicit statement in the text.

**Note on scope:** The document also describes a parallel arrangement in **Claim 2** involving a second history object, a third ETL process, and a fourth ETL process subscribed to a different event. No comparison to other patents is supported by the provided evidence.

### References

- [1] US11423041B2.txt
```

```
**Answer**

In US8509827B2, **claim 1** explicitly recites ranking context-data sources using a pecuniary cost. The exact supporting wording is:

> "algorithmically ranking the at least one context data source according a specified parameter, wherein the specified parameter comprises a pecuniary cost to acquire the context data from the at least one context data source"

**Stated facts (from the document):**
- Claim 1 is a method claim that includes receiving a short message, determining a context-data type, identifying at least one context-data source, ranking that source according to a specified parameter, and generating a request for context data.
- The specified parameter in claim 1 is defined as comprising "a pecuniary cost to acquire the context data."
- Claim 18 (apparatus) contains the same ranking limitation with the same pecuniary-cost wording.
- Claim 22 recites selecting relevant context data according to a metric that "comprises a monetary cost of the context-data."

**Inference (not stated):**
- Claims 18 and 22 appear to mirror the pecuniary/monetary cost ranking concept in apparatus and alternative method form, but the document does not expressly link these claims as a family or state that they are equivalent in scope.

### References

- [1] US8509827B2.txt
```

```
**Stated fact (from the evidence):** In US8509827B2, **claim 1** explicitly recites ranking context-data sources using the pecuniary cost of acquiring their context data. The exact supporting wording is:

> "algorithmically ranking the at least one context data source according a specified parameter, wherein the specified parameter comprises a pecuniary cost to acquire the context data from the at least one context data source"

Claim 1 also frames this within a method that includes "receiving a short message from a mobile device with a server" and "algorithmically determining a context-data type, wherein the context-data type is determined by a meaning of a term of the short message."

**Related stated facts:** The same pecuniary-cost parameter appears in independent **claim 18** (apparatus), which recites "algorithmically ranking the at least one context data source according a specified parameter, wherein the specified parameter comprises a pecuniary cost to acquire the context data from the at least one context data source." Dependent **claim 14** separately recites that "the specified parameter comprises a cost value of the context data as provided by the context-data source."

**Inference (not stated in the evidence):** Because claim 1 uses "comprising," the pecuniary-cost limitation appears to be a required element of that claim rather than an optional feature; however, the evidence does not include claim construction or prosecution history, so this is an interpretive inference only.

### References

- [1] US8509827B2.txt
```

```
**Stated fact (from the patent text):** In US9514753B2, **claim 6** explicitly specifies locality sensitive hash functions. The exact supporting wording is: “wherein determining the hash values comprises determining the hash values using one or more locality sensitive hash functions.”

**Related context (also stated):** Claim 1 recites the broader step of “determining hash values for the utterance vector according to multiple different hash functions,” while claim 7 adds that hash values may be determined “based on a position of the utterance vector with respect to different hyperplanes.”

**Inference (not stated as such in the text):** Claim 6 appears to be the claim that most directly names locality sensitive hashing; the hyperplane-based approach in claim 7 is a separate, more specific hash-determination feature, but the text does not expressly label claim 7 as locality sensitive hashing.

### References

- [1] US9514753B2.txt
```

```
**Stated fact (from the patent text):** In US9514753B2, **claim 6** explicitly specifies locality sensitive hash functions. The exact supporting wording is: “wherein determining the hash values comprises determining the hash values using one or more locality sensitive hash functions.”

**Related stated fact:** Claim 7 separately recites hashing “based on a position of the utterance vector with respect to different hyperplanes,” which is distinct from the locality sensitive hash function language in claim 6.

**Inference (not stated in the evidence):** Claim 6 appears to be the claim that most directly ties the claimed hash-value determination to locality sensitive hashing; however, the evidence does not expressly characterize claim 6 as the only such claim or compare it to other claims beyond the quoted text.

### References

- [1] US9514753B2.txt
```

```
**Answer**

In US8655901B1, the method claim that requires cross-validating a translated query pattern against a query log using an occurrence threshold is **claim 7**.

**Stated fact (quoted from the source):** Claim 7 recites: "where extracting a translated query pattern further comprises cross-validating the translated query pattern with a query log with respect to a specified occurrence threshold."

**Inference (not stated in the source):** Because claim 7 depends from claim 1, the cross-validating step is an additional limitation on the method of claim 1 rather than a standalone method. The evidence does not specify how the occurrence threshold is applied or what value it takes.

### References

- [1] US8655901B1.txt
```

```
**Answer**

In US8655901B1, the method claim that requires cross-validating a translated query pattern against a query log using an occurrence threshold is **claim 7**.

The exact supporting wording is: “where extracting a translated query pattern further comprises cross-validating the translated query pattern with a query log with respect to a specified occurrence threshold.”

**Stated facts (from the evidence):**
- US8655901B1 is titled “Translation-based query pattern mining.”
- Claim 7 depends from claim 1 and adds the cross-validation limitation quoted above.
- The same limitation also appears in system claim 14 (“The system of claim 8 … cross-validating the translated query pattern with a query log with respect to a specified occurrence threshold”).

**Inference (not stated in the evidence):**
- Because claim 7 is a method claim and claim 14 is a system claim, claim 7 is the method claim that specifically recites the occurrence-threshold cross-validation step.

### References

- [1] US8655901B1.txt
```

```
I do not have enough information to compare US7991757B2 with US8095432B1, because the provided context contains no document for US7991757B2. Only US8095432B1, US9374411B1, US9514120B1, and US9304738B1 appear in the retrieved evidence.

**Stated facts about US8095432B1 (ranking/selection):**

- Claim 1 recites ranking based on relationship proximity: "ranking, using the processor, the first recommendation with a first rank and the second recommendation with a second rank based on the first relationship proximity and the second relationship proximity, wherein the first rank exceeds the second rank."
- Claim 1 also recites list ordering: "wherein the first recommendation is higher on the recommendation list than the second recommendation based on the first rank exceeding the second rank."
- Claim 1 adds interest-based comparison: "determining that the first member comprises a plurality of interests in common with the inquiring member" and "determining that the first rank is higher than the third rank."
- Claim 3 states proximity rules: "wherein the relationship proximity is closer for friends of the inquiring member, and farther for non-friends to the inquiring member."

**Interoperation:** Neither US8095432B1's claims nor any other provided claim states that US8095432B1 interoperates with US7991757B2. US8095432B1 claim 17 mentions only "an external social networking utility," not another recommendation patent.

**Inference (not stated):** Any comparison of selection logic between the two patents, or any interoperability link, cannot be drawn from this evidence.

### References

- [1] US8095432B1.txt
```

```
I do not have enough information to compare US7991757B2 with US8095432B1, because the provided context contains no document chunks or knowledge-graph facts about US7991757B2. Its selection or ranking approach, claims, and any interoperability disclosure are therefore unavailable.

**What the evidence does show for US8095432B1**

US8095432B1 ranks recommendations by relationship proximity within a social networking utility. Claim 1 recites: "ranking, using the processor, the first recommendation with a first rank and the second recommendation with a second rank based on the first relationship proximity and the second relationship proximity, wherein the first rank exceeds the second rank." The resulting list places the first recommendation higher: "wherein the first recommendation is higher on the recommendation list than the second recommendation based on the first rank exceeding the second rank." Claim 1 also addresses shared interests: "determining that the first member comprises a plurality of interests in common with the inquiring member."

**Interoperability**

For US8095432B1, the only external-system language I can locate is in claim 17, which concerns obtaining recommendations from an external social networking utility: "obtain a plurality of recommendations from an external social networking utility." That is a stated fact about sourcing recommendations; it does not state interoperability with US7991757B2. No claim in the provided evidence names US7991757B2 or describes the two systems interoperating.

**Inference (not stated in the evidence)**

Because US7991757B2 is absent from the context, I cannot infer any ranking comparison or interoperability link between the two patents. The missing evidence is US7991757B2's abstract, claims, and any cross-reference to US8095432B1.

### References

- [1] US8095432B1.txt
```

```
## Comparison: US8509827B2 vs. US10867122B1

**US8509827B2 — source-selection criterion (Claim 1)**

Claim 1 of US8509827B2 explicitly requires "algorithmically ranking the at least one context data source according a specified parameter, wherein the specified parameter comprises a pecuniary cost to acquire the context data from the at least one context data source." The context-data type itself is "determined by a meaning of a term of the short message." So the selection/ranking criterion is tied to a **monetary acquisition cost** of the context data.

**US10867122B1 — entity-driven content request (Claim 1)**

Claim 1 of US10867122B1 requires determining a first factual entity "based on a second portion of the content that (i) was previously typed and (ii) is behind an input cursor," then determining a second factual entity, with the step comprising "determining that a measured level of intent for the third portion of the content is greater than a threshold level of intent." It then requires "requesting, for a user interface element, content that is related to both the first factual entity and the second factual entity." The trigger here is an **intent threshold tied to typed content and derived entities**, not a cost parameter.

**Stated facts vs. inference**

- *Stated:* US8509827B2 ranks sources by pecuniary cost (Claim 1). US10867122B1 requests panel content keyed to two factual entities, gated by an intent threshold (Claim 1).
- *Inference (mine):* The two criteria operate on different axes — cost-based source ranking versus intent-gated entity relevance — but the evidence does not state they are combinable or related.

### References

- [1] US10867122B1.txt
- [2] US8509827B2.txt
```

```
## Comparison: Source Selection vs. Entity-Driven Content Request

**US8509827B2 — source-selection criterion**

Claim 1 of US8509827B2 explicitly requires "algorithmically ranking the at least one context data source according a specified parameter, wherein the specified parameter comprises a pecuniary cost to acquire the context data from the at least one context data source." The method also requires "identifying at least one context-data source that provides the context-data type" and "generating a request for a context data of the context-data type from the at least one context data source." The context-data type itself is "determined by a meaning of a term of the short message."

**US10867122B1 — entity-driven content request**

Claim 1 of US10867122B1 requires "determining ... a first factual entity related to the second portion of content that is behind the input cursor," then "determining a second factual entity" based on the first and second portions collectively, conditioned on "determining that a measured level of intent for the third portion of the content is greater than a threshold level of intent." It then requires "requesting, for a user interface element, content that is related to both the first factual entity and the second factual entity," and "receiving the content of the user interface element for contemporaneous display on the user device with the content of the display environment."

**Stated facts vs. inference**

Stated: US8509827B2's ranking criterion is expressly a pecuniary cost (claim 1); US10867122B1's request is keyed to two determined factual entities and gated by an intent threshold (claim 1). Neither claim recites the other's mechanism.

Inference (not stated in either document): the two criteria address different selection problems—cost-based source ranking versus entity-relevance of requested content—and the evidence does not establish that either patent incorporates the other's criterion.

### References

- [1] US10867122B1.txt
- [2] US8509827B2.txt
```

```
**Claim dependency chain in US9514753B2**

The chain begins at independent claim 1, which recites the hash-table lookup and comparison steps: "determining a set of speaker vectors from a plurality of hash tables using the hash values" and "comparing the speaker vectors in the set with the utterance vector; selecting a speaker vector based on comparing the speaker vectors in the set with the utterance vector."

Claim 9 depends on claim 1 and specifies the comparison/selection mechanism: "comparing the speaker vectors in the set with the utterance vector comprises determining similarity scores that each indicate a degree of similarity of the utterance vector and one of the speaker vectors in the set; and wherein selecting a speaker vector comprises selecting the speaker vector that the similarity scores indicate is most similar to the utterance vector."

Claim 10 depends on claim 9 and narrows the similarity score to cosine distance: "determining a cosine distance between the utterance vector and each of the speaker vectors in the set."

Claim 11 depends on claim 10 and adds the threshold condition: "identifying a smallest cosine distance from among the determined cosine distances; determining that the smallest cosine distance is less than a maximum distance threshold value; and based on determining that the smallest cosine distance is less than the maximum distance threshold value, selecting the speaker vector corresponding to the smallest cosine distance."

**Stated facts vs. inference**

Stated facts: the dependency sequence 1 → 9 → 10 → 11, and the quoted conditions above, are explicit in the claim text. Inference: the chain's practical effect is that hash-table retrieval (claim 1) supplies the candidate set, claim 9/10 rank candidates by cosine distance, and claim 11 gates final selection on a maximum-distance threshold — this functional summary is my interpretation, not claim language. The evidence does not state how the threshold value is set or what happens when no candidate falls below it.

### References

- [1] US9514753B2.txt
```

```
## Claim Dependency Chain in US9514753B2

**Stated facts (from the claims):**

- **Claim 1** (independent) recites the base method: "determining a set of speaker vectors from a plurality of hash tables using the hash values, each speaker vector being derived from one or more utterances of a respective speaker; comparing the speaker vectors in the set with the utterance vector; selecting a speaker vector based on comparing the speaker vectors in the set with the utterance vector."

- **Claim 9** depends on Claim 1 and specifies the comparison/selection mechanism: "comparing the speaker vectors in the set with the utterance vector comprises determining similarity scores that each indicate a degree of similarity of the utterance vector and one of the speaker vectors in the set; and wherein selecting a speaker vector comprises selecting the speaker vector that the similarity scores indicate is most similar to the utterance vector."

- **Claim 10** depends on Claim 9 and specifies the metric: "determining a cosine distance between the utterance vector and each of the speaker vectors in the set."

- **Claim 11** depends on Claim 10 and adds the threshold condition: "identifying a smallest cosine distance from among the determined cosine distances; determining that the smallest cosine distance is less than a maximum distance threshold value; and based on determining that the smallest cosine distance is less than the maximum distance threshold value, selecting the speaker vector corresponding to the smallest cosine distance."

**Inference (not stated in the claims):** The dependency chain is therefore 1 → 9 → 10 → 11, meaning the hash-table candidate set of Claim 1 is narrowed by similarity scoring (Claim 9), measured by cosine distance (Claim 10), and finalized only if the smallest distance falls below the maximum threshold (Claim 11). The claims do not state what happens if the threshold is not met.

### References

- [1] US9514753B2.txt
```

```
## Connection in US9298709B2

**Stated facts (from the claims):**

The geographic-map-based IP-rights visualization process is set out in **claim 10** of US9298709B2, which recites "generating or updating each data visualization displayed in the information pane based on each set of successively obtained geographic co-ordinates of the current viewable area of the geographic map display."

The on-screen-button update condition is established through a chain of dependent claims:

- **Claim 16** depends on claim 10 and states: "wherein generating or updating each data visualization displayed in the information pane based on each set of successively obtained geographic coordinates of the current viewable area of the geographic map display occurs following a user initiated command."
- **Claim 17** depends on claim 16 and states: "wherein the user initiated command comprises the pressing of an on-screen button."

**Inference (not stated in the patent):**

Because claim 17 depends from claim 16, which in turn depends from claim 10, the on-screen-button-triggered update is linked back to the geographic-map-based visualization process of claim 10. This dependency chain is my inference from the claim numbering and dependency references; the patent text itself does not explicitly narrate this linkage.

**Note on scope:** A parallel timing-based condition appears in **claim 15** (depending on claim 10), covering updates "after a pre-defined time period elapses and there has been no change in the viewable area of the geographic map." The evidence does not state whether claims 15 and 16 are mutually exclusive alternatives.

### References

- [1] US9298709B2.txt
```

```
## Stated Facts (US9298709B2)

The patent describes a process for visualizing IP rights data tied to a geographic map. Claim 10 recites a process comprising monitoring/storing geographic co-ordinates, issuing a display change notification, generating a list of IP rights whose owner address falls within the map area, restricting that list by restriction criteria, and "generating or updating each data visualization displayed in the information pane based on each set of successively obtained geographic co-ordinates of the current viewable area of the geographic map display."

The on-screen-button condition appears in the dependent claims:

- **Claim 16** (dependent on claim 10): "wherein generating or updating each data visualization displayed in the information pane based on each set of successively obtained geographic coordinates of the current viewable area of the geographic map display occurs following a user initiated command."
- **Claim 17** (dependent on claim 16): "wherein the user initiated command comprises the pressing of an on-screen button."

So the chain is: **Claim 10** (base process) → **Claim 16** (user-initiated command triggers the update) → **Claim 17** (that command is an on-screen button press).

## Inference (not stated in the patent)

The connection is established through dependency: claim 16 narrows claim 10's updating step to a user-initiated command, and claim 17 further specifies that command as an on-screen button press. The patent does not expressly state that claim 17 "connects" the map-based process to the button condition; that linkage is my reading of the claim dependency structure.

### References

- [1] US9298709B2.txt
```

```
In US11423041B2, the dependent system claim you are asking about is **claim 5**, which states: "wherein the first ETL process is performed external to the ETL service and wherein the second ETL process is performed by the ETL service."

The next claim, **claim 6**, states the opposite arrangement: "wherein the first ETL process is performed by the ETL service and wherein the second ETL process is performed by the ETL service."

**Stated facts:** Claim 5 covers a configuration where the first ETL process runs externally while the second runs within the ETL service; claim 6 covers a configuration where both the first and second ETL processes are performed by the ETL service. Both depend from claim 1 (the system claim).

**Inference (not stated in the patent):** The two claims appear to define mutually exclusive alternatives for where the first ETL process executes (external vs. internal to the ETL service), while both require the second ETL process to be performed by the ETL service. This is my comparison, not wording from the document.

### References

- [1] US11423041B2.txt
```

```
In US11423041B2, the dependent system claim that states the first ETL process is external to the ETL service while the second is performed by that service is **claim 5**. Its exact wording is: “wherein the first ETL process is performed external to the ETL service and wherein the second ETL process is performed by the ETL service.”

**Contrast with the next claim (claim 6):** Claim 6 instead states: “wherein the first ETL process is performed by the ETL service and wherein the second ETL process is performed by the ETL service.” Thus, the stated difference is that claim 5 places the first ETL process outside the ETL service, whereas claim 6 places both the first and second ETL processes within the ETL service.

**Stated facts:** Both claims depend from claim 1 and concern where the first and second ETL processes are performed. **Inference:** Claim 6 appears to cover an entirely in-service arrangement, while claim 5 covers a hybrid arrangement; this characterization is my inference, not express claim language.

### References

- [1] US11423041B2.txt
```

| ID / 类别 | 原问题 | 正确证据与期望 | naive 实际结果 | mix 实际结果 | 归因 |
|---|---|---|---|---|---|
| Q01<br>A | 哪篇专利用多个哈希函数及哈希表选择说话人向量并输出身份？ | **US9514753B2 / Claim 1**<br>US9514753B2，Claim 1：对utterance vector计算多个hash values，用hash tables取得speaker vectors，比较、选择后输出speaker identity。 | **核心事实、专利及 Claim 正确**<br>E 0 / R 0 / C 8实际回答及引用同次返回来源（与答案所提专利相交）：[1] US9514753B2.txt | **核心事实正确；“集合中唯一”推断超出检索范围**<br>E 16 / R 26 / C 5实际回答及引用同次返回来源（与答案所提专利相交）：[1] US9514753B2.txt；[2] US8655901B1.txt；[3] US8880423B2.txt | mix：生成阶段范围扩大；未证明断言为假 |
| Q02<br>A | 哪篇专利用数据目录中的history object记录首个ETL过程，并触发订阅事件的第二个ETL过程？ | **US11423041B2 / Claim 1**<br>US11423041B2，Claim 1：在history object中记录首个ETL过程，按事件条件评估并执行第二个ETL过程。 | **核心事实、专利及 Claim 正确**<br>E 0 / R 0 / C 7实际回答及引用同次返回来源（与答案所提专利相交）：[1] US11423041B2.txt；[2] US8655901B1.txt；[3] US9118735B1.txt；[4] US7756837B2.txt | **核心事实、专利及 Claim 正确**<br>E 14 / R 38 / C 4实际回答及引用同次返回来源（与答案所提专利相交）：[1] US11423041B2.txt | 未发现核心事实错误；引文有格式精度备注 |
| Q03<br>B | US8509827B2哪一Claim明确按获取上下文数据的货币成本排序数据源？ | **US8509827B2 / Claim 1**<br>Claim 1明确规定按specified parameter排序context data source，该参数包括pecuniary cost。Claim 18也有平行装置表达，若答案同时指出也应接受。 | **核心事实、专利及 Claim 正确**<br>E 0 / R 0 / C 6实际回答及引用同次返回来源（与答案所提专利相交）：[1] US8509827B2.txt | **核心事实、专利及 Claim 正确**<br>E 22 / R 32 / C 4实际回答及引用同次返回来源（与答案所提专利相交）：[1] US8509827B2.txt | 未发现核心事实错误；引文有格式精度备注 |
| Q04<br>B | US9514753B2哪一Claim明确指定locality sensitive hash functions？ | **US9514753B2 / Claim 6**<br>Claim 6，要求使用one or more locality sensitive hash functions确定hash values。 | **核心事实、专利及 Claim 正确**<br>E 0 / R 0 / C 6实际回答及引用同次返回来源（与答案所提专利相交）：[1] US9514753B2.txt | **核心事实、专利及 Claim 正确**<br>E 26 / R 21 / C 4实际回答及引用同次返回来源（与答案所提专利相交）：[1] US9514753B2.txt | 未发现核心事实错误；引文有格式精度备注 |
| Q05<br>B | US8655901B1哪一方法Claim要求按出现次数阈值，以查询日志交叉验证翻译后的查询模式？ | **US8655901B1 / Claim 7**<br>方法Claim 7（系统Claim 14有平行表达）：cross-validating the translated query pattern with a query log with respect to a specified occurrence threshold。 | **核心事实、专利及 Claim 正确**<br>E 0 / R 0 / C 6实际回答及引用同次返回来源（与答案所提专利相交）：[1] US8655901B1.txt | **核心事实、专利及 Claim 正确**<br>E 21 / R 33 / C 3实际回答及引用同次返回来源（与答案所提专利相交）：[1] US8655901B1.txt | 未发现核心事实错误；引文有格式精度备注 |
| Q06<br>C | 比较US7991757B2与US8095432B1的推荐选择/排序依据；原文是否说两个系统互操作？ | **US7991757B2 / Claim 1；US8095432B1 / Claim 1**<br>前者Claim 1从外部recommenders取得scores，经normalize后选subset；后者Claim 1依据社交relationship proximity排序，朋友的rank高于非朋友。两者共享推荐排序主题是本次比较归纳；所引Claims没有声称两专利系统互操作，不能推断两专利绝无其他关联。 | **未完成比较；明确说明证据不足**<br>E 0 / R 0 / C 6实际回答及引用同次返回来源（与答案所提专利相交）：[1] US8095432B1.txt；[2] US9374411B1.txt；[3] US9514120B1.txt；[4] US9304738B1.txt | **未完成比较；明确说明证据不足**<br>E 29 / R 27 / C 4实际回答及引用同次返回来源（与答案所提专利相交）：[1] US8095432B1.txt | 检索/上下文覆盖不足；非抽取或索引丢失 |
| Q07<br>C | 比较US8509827B2的数据源选择标准与US10867122B1的实体驱动内容请求，两者各自明确要求什么？ | **US8509827B2 / Claim 1；US10867122B1 / Claim 1**<br>US8509827B2 Claim 1按包括获取成本的参数排序context-data sources；US10867122B1 Claim 1请求与first和second factual entity均相关的UI内容。共同的上下文内容获取主题是比较，不是原文声明的专利间链接。 | **核心事实、专利及 Claim 正确**<br>E 0 / R 0 / C 6实际回答及引用同次返回来源（与答案所提专利相交）：[1] US10867122B1.txt；[2] US8509827B2.txt | **核心事实、专利及 Claim 正确**<br>E 28 / R 29 / C 3实际回答及引用同次返回来源（与答案所提专利相交）：[1] US10867122B1.txt；[2] US8509827B2.txt | 未发现核心事实错误；引文有格式精度备注 |
| Q08<br>D | 追踪US9514753B2从哈希表候选说话人到按最小余弦距离及最大阈值选取说话人的Claim依赖链。 | **US9514753B2 / Claim 1；US9514753B2 / Claim 9；US9514753B2 / Claim 10；US9514753B2 / Claim 11**<br>Claim 11依赖10，10依赖9，9依赖1；1以hash values从hash tables取得speaker vectors，9按similarity scores选most similar，10用cosine distance，11要求smallest cosine distance低于maximum distance threshold。这里是原文依赖链，不应把余弦距离最小条件错误归为Claim 1的逐字要求。 | **核心事实、专利及 Claim 正确**<br>E 0 / R 0 / C 6实际回答及引用同次返回来源（与答案所提专利相交）：[1] US9514753B2.txt | **核心事实、专利及 Claim 正确**<br>E 25 / R 23 / C 4实际回答及引用同次返回来源（与答案所提专利相交）：[1] US9514753B2.txt | 未发现核心事实错误；引文有格式精度备注 |
| Q09<br>D | 追踪US9298709B2地图范围内IP权利可视化流程与屏幕按钮触发更新条件之间的Claim依赖。 | **US9298709B2 / Claim 10；US9298709B2 / Claim 16；US9298709B2 / Claim 17**<br>Claim 17依赖16，16依赖10；10生成地理范围及限制条件筛选后的IP可视化，16规定user initiated command之后更新，17指定pressing of an on-screen button。应保留10→16→17的从属关系。 | **核心事实、专利及 Claim 正确**<br>E 0 / R 0 / C 6实际回答及引用同次返回来源（与答案所提专利相交）：[1] US9298709B2.txt | **核心事实、专利及 Claim 正确**<br>E 26 / R 31 / C 3实际回答及引用同次返回来源（与答案所提专利相交）：[1] US9298709B2.txt | 未发现核心事实错误；引文有格式精度备注 |
| Q10<br>B | US11423041B2哪一从属系统Claim规定首个ETL过程在服务外执行、第二个由服务执行？与下一Claim有何区别？ | **US11423041B2 / Claim 5；US11423041B2 / Claim 6**<br>Claim 5：first external、second by service；Claim 6：first和second都由ETL service执行。这是不同从属实施限定，不能把二者同时强加于同一个实施。 | **核心事实、专利及 Claim 正确**<br>E 0 / R 0 / C 7实际回答及引用同次返回来源（与答案所提专利相交）：[1] US11423041B2.txt | **核心事实、专利及 Claim 正确**<br>E 14 / R 38 / C 4实际回答及引用同次返回来源（与答案所提专利相交）：[1] US11423041B2.txt | 未发现核心事实错误；引文有格式精度备注 |

按“完成所问核心任务”计，两模式均为 9/10；Q06 的部分事实正确，但完整比较未完成。Q01 mix 另有超范围的“集合中唯一”推断，虽然标为 inference，也没有对整个 20 篇集合的证据支持，且没有证明该断言实际为假。因此不能将 9/10 解读为整答完全有据。部分回答引文改动句末标点或显式使用省略号/[s]，技术含义未变，但不应报告为全数逐字一致。末尾 References 是官方提示格式，未强制逐句脚注，不能仅因缺少行内脚注判错。

### 单独的检索预算敏感性检查

为定位失败，保持原问题、模型、提示和索引不变，将 top_k/chunk_top_k 改为 40/20，实体/关系/总上下文预算改为 6000/8000/30000（源码默认量级；rerank 仍关闭）。多个参数同时变化，不是单因素消融，也不混入主对照成绩。前后索引哈希一致。

```
## How US7991757B2 Selects/Ranks Recommendations

US7991757B2 describes a personalization network service that queries multiple external recommenders. In **claim 1**, the system "query the plurality of external recommenders over the computer network for recommendations responsive to the second request, and receive recommendations and associated scores from the external recommenders." Selection is score-based: "an optimization module configured to normalize the associated scores; wherein the recommendations service is further configured to select a subset of the recommendations, based at least in part on the normalized scores."

**Claim 4** adds weighting: "applying weights to each of the recommenders; combining the scores with the weights to produce overall scores; selecting a subset of the recommendations based on the overall scores." **Claim 3** states the optimization module is "further operative to assign weights to the external recommenders."

## How US8095432B1 Selects/Ranks Recommendations

US8095432B1 ranks by social relationship proximity. **Claim 1** recites "ranking, using the processor, the first recommendation with a first rank and the second recommendation with a second rank based on the first relationship proximity and the second relationship proximity, wherein the first rank exceeds the second rank." The list ordering follows rank: "the first recommendation is higher on the recommendation list than the second recommendation based on the first rank exceeding the second rank." Claim 1 also compares interest similarity: "determining that the first member comprises a plurality of interests in common with the inquiring member" and "determining that the first rank is higher than the third rank."

## Interoperation

Neither claim states the two systems interoperate. US7991757B2 claim 1 refers only to "external recommenders" generally, without naming US8095432B1. US8095432B1 claim 1 contains no multi-recommender or external-service element.

**Inference (not stated):** US8095432B1's proximity-ranked engine could conceptually serve as one "external recommender" under US7991757B2's architecture, but no claim wording supports this link.

### References

- [1] US8095432B1.txt
- [6] US7991757B2.txt
```

```
## How Each Patent Selects or Ranks Recommendations

**US7991757B2** ranks/selects by combining scores from multiple external recommenders. Claim 17 recites: "normalizing scores provided by the recommenders to produce normalized scores; applying weights to each of the recommenders; and combining the normalized scores with the weights to generate overall scores to be used in selecting recommendations." Claim 4 similarly recites "applying weights to each of the recommenders; combining the scores with the weights to produce overall scores; selecting a subset of the recommendations based on the overall scores."

**US8095432B1** ranks by relationship proximity within a social network. Claim 1 recites: "ranking, using the processor, the first recommendation with a first rank and the second recommendation with a second rank based on the first relationship proximity and the second relationship proximity, wherein the first rank exceeds the second rank." The abstract adds that proximity "is closest for friends of the inquiring member, and farthest for strangers."

## Do Either Claims Say the Systems Interoperate?

No. Neither claim references the other patent, its system, or any cross-system interoperability. US7991757B2 claim 17 addresses a "network service to content sites" using registered external recommenders; US8095432B1 claim 1 addresses a "social networking utility" and member relationship proximities. No claim wording in the provided evidence links the two.

## Inference (Not Stated Fact)

Both concern recommendation selection, but on different bases—weighted score aggregation versus social-graph proximity. Any suggestion that one could feed the other is my inference only; the evidence does not support it.

### References

- [6] US7991757B2.txt
- [1] US8095432B1.txt
```

```
I do not have enough information to answer this query. The patent **US7991757B2** does not appear anywhere in the provided Context or Reference Document List, so I cannot quote Claim 1 or Claim 27 from it, nor explain their dependency.

The available documents are:

- [1] US10867122B1
- [2] US9374411B1
- [3] US8655901B1
- [4] US7756837B2
- [5] US8095432B1
- [6] US9514120B1
- [7] US8719408B2
- [8] US8069128B2
- [9] US11423041B2
- [10] US9304738B1
- [11] US9218390B2
- [12] US9514753B2
- [13] US9118735B1

**What is missing:** the text of US7991757B2, including its Claim 1 and Claim 27. Without that evidence, any statement about a "registration capability" or an added capability would be inference rather than document fact, which the instructions prohibit. Please provide the relevant claims or confirm the correct publication number.

### References

- [1] US10867122B1.txt
- [2] US9374411B1.txt
- [3] US8655901B1.txt
- [4] US7756837B2.txt
- [5] US8095432B1.txt
```

```
I do not have enough information to answer this query. The provided **Context** does not contain any document, chunk, or knowledge-graph entity for **US7991757B2**, so I cannot quote Claim 1 or Claim 27 of that patent, nor describe their dependency.

**What is present (explicit evidence):** The context does describe a *registration* capability, but in a different patent family. The knowledge graph states that a "Registration Module" is "configured to provide functionality for registering an external recommender with a recommendations service" and is "configured to allow a provider of an external recommender to provide machine readable descriptions of the external recommender." It also states that "Registration submissions are operative to request registration of recommenders" and are "received from a plurality of recommender providers." However, none of the document chunks in the context contain claim text tied to US7991757B2, and no claim numbers 1 or 27 for that publication appear.

**What is missing:** (1) The text of US7991757B2 Claim 1; (2) the text of Claim 27; (3) any statement of Claim 27's dependency (e.g., "The method of claim 1, further comprising…"). Without these, any description of the added capability or the dependency relationship would be inference rather than evidence, which I will not supply.

**Inference vs. evidence:** It would be an unsupported inference to assume the registration language above belongs to US7991757B2 or that Claim 27 depends from Claim 1. To answer, please provide the claims of US7991757B2 or a document chunk containing them.

### References

- [1] US10867122B1.txt
```

| 问题 / 模式 | 返回块 | 结果 |
|---|---|---|
| 原 Q06 跨文档比较 / naive | 20 | 找回目标原文，完成比较实际补充回答 |
| 原 Q06 跨文档比较 / mix | 18 | 找回目标原文，完成比较实际补充回答 |
| 补充 Q11 自然跨块依赖 / naive | 20 | 仍未取回目标原文；拒答实际补充回答 |
| 补充 Q11 自然跨块依赖 / mix | 20 | 仍未取回目标原文；来源判断错误实际补充回答 |

同一 Embedding 模型的候选排名复查：Q06 的 US7991757B2 两块位于第 9、11，低于基线 top-8；补充 Q11 两块位于第 29、30，仍低于扩展 top-20。索引中两条向量记录完整存在，不能归为索引写入丢失。mix 可能额外通过图路径取得事实，因此向量名次不是对全部 mix 行为的唯一解释。

## C. 两个最有价值的实际案例

### 成功：具体 Claim 与原文块可以对应

[US9514753B2](https://patents.google.com/patent/US9514753B2/en)，Q04 询问 locality-sensitive hash functions 位于哪一 Claim。真实证据为 **Claim 6**：6. The method of claim 1 , wherein determining the hash values comprises determining the hash values using one or more locality sensitive hash functions.。naive 与 mix 均指出 Claim 6；同次检索包含 `US9514753B2-chunk-000`，文件来源与公开号一致。

mix 的真实完整回答

```
**Stated fact (from the patent text):** In US9514753B2, **claim 6** explicitly specifies locality sensitive hash functions. The exact supporting wording is: “wherein determining the hash values comprises determining the hash values using one or more locality sensitive hash functions.”

**Related stated fact:** Claim 7 separately recites hashing “based on a position of the utterance vector with respect to different hyperplanes,” which is distinct from the locality sensitive hash function language in claim 6.

**Inference (not stated in the evidence):** Claim 6 appears to be the claim that most directly ties the claimed hash-value determination to locality sensitive hashing; however, the evidence does not expressly characterize claim 6 as the only such claim or compare it to other claims beyond the quoted text.

### References

- [1] US9514753B2.txt
```

这证明本次样本在原文块成功进入上下文时，可以完成正确的文档与 Claim 定位。它不证明系统为每项断言生成了可机器校验的 Claim-span 证据对象。

### 失败：图事实已经取回，却产生错误来源排除

[US7991757B2](https://patents.google.com/patent/US7991757B2/en) 的 Claim 1 定义注册外部推荐器的模块，Claim 27 明确从属于 Claim 1 并增加机器可读描述能力。必要原文：

> **Claim 1:** “a registration module configured to provide functionality for registering an external recommender with a recommendations service”
**Claim 27:** “The system of claim 1 … provide machine readable descriptions of the external recommender.”

两条完整 Claim 位于不同实际块：000 与 001。技术能力均成功抽取和合并；扩展预算的 Q11 mix 同次返回 Registration Module 记录，`file_path=US7991757B2.txt`，`source_id=US7991757B2-chunk-000&lt;SEP&gt;US7991757B2-chunk-001`。但回答提示 API 392 保留描述、没有这些来源字段，目标公开号仅出现在用户问题而未出现在系统证据/引用列表。模型将这些注册能力称为 **“in a different patent family”**，并最终引用 [1] US10867122B1.txt。

该来源排除与已记录的来源相矛盾。这里不是在推断实际专利族谱系，也没有把技术关系缺失误判为抽取错误：**技术事实已抽取、已入图、已被图检索取回；错误发生在来源呈现/最终归属这一链条。**来源字段被省略是可观察到的条件，未经单独来源恢复消融，不能说它是生成错误的唯一原因。模型仍未取得原始 Claim 文本，Claim 级回答没有完成。

完整失败回答

```
I do not have enough information to answer this query. The provided **Context** does not contain any document, chunk, or knowledge-graph entity for **US7991757B2**, so I cannot quote Claim 1 or Claim 27 of that patent, nor describe their dependency.

**What is present (explicit evidence):** The context does describe a *registration* capability, but in a different patent family. The knowledge graph states that a "Registration Module" is "configured to provide functionality for registering an external recommender with a recommendations service" and is "configured to allow a provider of an external recommender to provide machine readable descriptions of the external recommender." It also states that "Registration submissions are operative to request registration of recommenders" and are "received from a plurality of recommender providers." However, none of the document chunks in the context contain claim text tied to US7991757B2, and no claim numbers 1 or 27 for that publication appear.

**What is missing:** (1) The text of US7991757B2 Claim 1; (2) the text of Claim 27; (3) any statement of Claim 27's dependency (e.g., "The method of claim 1, further comprising…"). Without these, any description of the added capability or the dependency relationship would be inference rather than evidence, which I will not supply.

**Inference vs. evidence:** It would be an unsupported inference to assume the registration language above belongs to US7991757B2 or that Claim 27 depends from Claim 1. To answer, please provide the claims of US7991757B2 or a document chunk containing them.

### References

- [1] US10867122B1.txt
```

### 另一个定位明确但受实验条件影响的遗漏

[US9218390B2 Claim 2](https://patents.google.com/patent/US9218390B2/en) 完整位于一个块内。抽取调用 API 191 达到本实验 3500-token 输出上限，`finish_reason=length`，正在输出的 `Class-Based Language Model Features → GEO_TRI_FIRST` 关系行未写完。实际官方解析器重放拒绝该行，最终图也缺这条显式成员边；其他块没有恢复它。

**GEO_TRI_FIRST 节点及其含义仍保留，原文也完整存在。**这是本次输出上限导致的特定抽取关系遗漏，不能称为整项事实完全消失、跨块丢失或已证明回答失败。未把其他未显式建边项目都算作同因果错误，未修改基线索引或提高上限重跑后覆盖原结果。

## D. 研究判断

| 问题 | 本轮证据支持的结论 |
|---|---|
| 当前官方版本能做专利文档级溯源吗？ | 可以，多个真实答案的文件引用正确对应公开号；但并不保证所有图来源都进入回答上下文。补充 Q11 显示，结构化返回保留来源而回答仍错误归属。因此要分别评价“来源数据存在”和“回答正确绑定来源”。 |
| 能可靠回溯具体 Claim 吗？ | 在所需原文块被检索到时，本轮多数题正确定位 Claim；目前没有自动 Claim-span 保证。格式化查询输出没有显式 Claim ID，内部 source-span 和外部核验不能等同为模型每项结论的证明。未取回原文时出现拒答，不能称普遍可靠。 |
| 复现了跨 Chunk 关系丢失吗？ | 没有证明。原 Q08/Q09 的依赖链实际同块；真正跨块的 US7991757B2 技术关系成功抽取并合并，保留两个来源 ID。Q11 失败发生在原文检索/上下文来源与归属层；显式 Claim 从属关系未被图化，也没有同文不同边界的因果实验支持归因给分块。 |
| 是代码缺陷、设计限制还是本次条件？ | Q06 对较低 top-k/上下文预算敏感，扩展后恢复；截断遗漏由本次 3500 输出限制引发；Claim 结构和图来源呈现粒度属于当前系统表示/接口设计范围；错误来源判断还涉及生成行为。没有确认普适软件缺陷，也没有复现论文基准。 |
| 值得 PhD 深入探索的方向？ | 把 Claim、从属约束和原文区间作为明确证据对象；使实体/关系摘要在上下文构建中保留来源身份；结合公开号约束与语义/图检索；逐阶段衡量事实与出处的保留；在证据缺失时区分安全拒答与错误归属。增量一致性本轮未测试，仍是后续问题。 |

当前核心 `aquery_llm` 已真实使用，输出含 entities/relationships/chunks/references。`include_references` 在核心 QueryParam 默认 false，本轮显式 true；`include_chunk_content` 是 REST 参数，核心结果直接保留 chunks 内容；`/query/data` 对应 aquery_data，无最终答案生成但仍可调用关键词/Embedding。HTTP 路由本轮仅源码核对，没有部署 HTTP 服务，不冒称 REST 测试。

版本界限：论文 [v3（2025-04-28）](https://arxiv.org/pdf/2410.05779v3) Figure 1 已示原始块 ID，当前 README 将 citations 功能记于 2025-03；不能声称论文时期完全没有引用机制。这里测试的是 2026 年 [正式发布 v1.5.7](https://github.com/HKUDS/LightRAG/releases/tag/v1.5.7)、指定商业服务和本轮配置，不将新代码行为倒推成论文原始方法结论。

## （已删去）

此处删去一段与实验无关的个人申请材料（研究兴趣段落）。

## 复现与证据

主记录：`round2/results/full_Q*_naive.json`、`full_Q*_mix.json`；补充结果：`supplement_budget_*.json`。每份保留原问题、真实答案、同次实体/关系/块/引用、调用编号与时间。索引、图、原始抽取缓存、LLM 的无密钥请求和完整生成响应，以及 Embedding 的输入/返回元数据和已持久化索引向量均保留；输出截断响应没有被官方正常缓存，因此 API 191 原始记录尤其重要。

审阅与定位：`full_audit_q01_q05.json`、`full_audit_q06_q11.json`、`supplement_budget_audit.json`、`retrieval_rank_probe.json`、`full_provenance_trace.json`、`extraction_truncation_parser_replay.json`、`actual_chunk_source_mapping.json`。成本账本在 `cost_ledger.json`。角色脚本、依赖版本和原始选择清单随小型证据包提供。

方法限制：20 篇目的性样本；单次模型输出，temperature=0 也不保证完全确定性；没有独立人工双盲标注；基线预算低于源码默认值；额外 gleaning=0、rerank 关闭；敏感性检查同时改变多个预算参数；未测试增量插入。所有模式的成功、未完成和来源错误都保留，不按偏好挑选赢家。

20 篇专利清单

| Publication | Title | Claims |
|---|---|---|
| [US9298709B2](https://patents.google.com/patent/US9298709B2/en) | Computer system to visualize data from an IP rights database | 17 |
| [US8509827B2](https://patents.google.com/patent/US8509827B2/en) | Methods and apparatus of context-data acquisition and ranking | 26 |
| [US9514753B2](https://patents.google.com/patent/US9514753B2/en) | Speaker identification using hash-based indexing | 20 |
| [US9304738B1](https://patents.google.com/patent/US9304738B1/en) | Systems and methods for selecting content using weighted terms | 19 |
| [US9118735B1](https://patents.google.com/patent/US9118735B1/en) | Finding people using social networks | 21 |
| [US8095432B1](https://patents.google.com/patent/US8095432B1/en) | Recommendation engine for social networks | 24 |
| [US8880423B2](https://patents.google.com/patent/US8880423B2/en) | Inventory estimation for search retargeting | 17 |
| [US8917913B2](https://patents.google.com/patent/US8917913B2/en) | Searching with face recognition and social networking profiles | 17 |
| [US9514120B1](https://patents.google.com/patent/US9514120B1/en) | Classification of a string as a typographical error based on feedback | 20 |
| [US7991757B2](https://patents.google.com/patent/US7991757B2/en) | System for obtaining recommendations from multiple recommenders | 28 |
| [US8069128B2](https://patents.google.com/patent/US8069128B2/en) | Real-time ad-hoc spam filtering of email | 20 |
| [US9374411B1](https://patents.google.com/patent/US9374411B1/en) | Content recommendations using deep data | 25 |
| [US9218390B2](https://patents.google.com/patent/US9218390B2/en) | Query parser derivation computing device and method for making a query parser for parsing unstructured search queries | 18 |
| [US7756837B2](https://patents.google.com/patent/US7756837B2/en) | Methods and apparatus for searching backup data based on content and attributes | 49 |
| [US8719408B2](https://patents.google.com/patent/US8719408B2/en) | Automated digital media content filtration based on relationship monitoring | 24 |
| [US8655901B1](https://patents.google.com/patent/US8655901B1/en) | Translation-based query pattern mining | 15 |
| [US10867122B1](https://patents.google.com/patent/US10867122B1/en) | Contextually relevant knowledge panels in an application environment | 15 |
| [US11423041B2](https://patents.google.com/patent/US11423041B2/en) | Maintaining data lineage to detect data events | 20 |
| [US10778629B2](https://patents.google.com/patent/US10778629B2/en) | Systems and methods for collation, translation, and analysis of passively created digital interaction and relationship data | 21 |
| [US9589231B2](https://patents.google.com/patent/US9589231B2/en) | Social medical network for diagnosis assistance | 22 |

报告生成 2026-10-29T15:11:28.399993+00:00。第一轮无模型服务的记录保留；第二轮实测结果单独归档。
