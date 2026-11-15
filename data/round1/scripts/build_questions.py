"""Build exact-substring-verified question ground truths; no model calls."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
import json, re, hashlib
from pathlib import Path

BASE = legacy_root()
rows = {r['publication_number']: r for r in json.loads((BASE/'data/selected_patents.json').read_text())}

def ev(pub, num, quote):
    raw = rows[pub]['claims']
    marks = list(re.finditer(r'(?<!\d)(\d+)\.\s', raw))
    matches = [(m.start(), marks[i+1].start() if i+1<len(marks) else len(raw)) for i,m in enumerate(marks) if int(m.group(1))==num]
    assert len(matches)==1, (pub,num,matches)
    start,end = matches[0]
    text = raw[start:end].strip()
    assert quote in text, (pub,num,quote)
    pos = raw.find(quote,start,end)
    return {'publication_number':pub,'claim_number':num,'quote':quote,'quote_char_start_in_raw_claims':pos,'quote_char_end_in_raw_claims':pos+len(quote),'full_claim':text,'source_url':f'https://patents.google.com/patent/{pub}/en','verified_exact_substring':True}

questions=[]
def add(i, cat, q, zh, expected, evidence, **extra):
    questions.append({'id':f'Q{i:02d}','category':cat,'question':q+' Cite the patent publication number, claim number, and exact supporting wording. Separate stated facts from your inferences.','question_zh':zh,'correct_publication_numbers':list(dict.fromkeys(e['publication_number'] for e in evidence)),'expected_answer_zh':expected,'evidence':evidence,'status':'not_run','naive':None,'mix':None,'error_category':None,'attribution':'No official query has been run for this record. Do not interpret missing answers as retrieval failures.',**extra})

add(1,'A_specific_entity',
'Which patent in this collection uses multiple hash functions and hash tables to select a speaker vector and output a speaker identity?',
'哪篇专利用多个哈希函数及哈希表选择说话人向量并输出身份？',
'US9514753B2，Claim 1：对utterance vector计算多个hash values，用hash tables取得speaker vectors，比较、选择后输出speaker identity。',[
ev('US9514753B2',1,'determining hash values for the utterance vector according to multiple different hash functions; determining a set of speaker vectors from a plurality of hash tables using the hash values'),
ev('US9514753B2',1,'determining a speaker identity corresponding to the selected speaker vector; and outputting data indicating the speaker identity.')])

add(2,'A_specific_entity',
'Which patent uses a data catalog history object describing a first ETL process to trigger a second subscribed ETL process?',
'哪篇专利用数据目录中的history object记录首个ETL过程，并触发订阅事件的第二个ETL过程？',
'US11423041B2，Claim 1：在history object中记录首个ETL过程，按事件条件评估并执行第二个ETL过程。',[
ev('US11423041B2',1,'the history object created in the history data structure to specify information expected to be stored to describe the performance of the first ETL process on a given source data object to generate a transformed data object'),
ev('US11423041B2',1,'in response to the determination that the performance of the first ETL process satisfies the criteria for triggering the event, cause the second ETL process to be performed.')])

add(3,'B_claim_evidence',
'In US8509827B2, which claim explicitly ranks context-data sources using the pecuniary cost of acquiring their context data?',
'US8509827B2哪一Claim明确按获取上下文数据的货币成本排序数据源？',
'Claim 1明确规定按specified parameter排序context data source，该参数包括pecuniary cost。Claim 18也有平行装置表达，若答案同时指出也应接受。',[
ev('US8509827B2',1,'algorithmically ranking the at least one context data source according a specified parameter, wherein the specified parameter comprises a pecuniary cost to acquire the context data from the at least one context data source')],
source_quality_caveat='This patent has upstream malformed parent-claim references in claims 2/3; this question uses intact claim 1. Parallel claim 18 is also acceptable with exact supporting text.')

add(4,'B_claim_evidence',
'In US9514753B2, which claim explicitly specifies locality sensitive hash functions, and what exact wording supports this?',
'US9514753B2哪一Claim明确指定locality sensitive hash functions？',
'Claim 6，要求使用one or more locality sensitive hash functions确定hash values。',[
ev('US9514753B2',6,'6. The method of claim 1 , wherein determining the hash values comprises determining the hash values using one or more locality sensitive hash functions.')])

add(5,'B_claim_evidence',
'In US8655901B1, which method claim requires cross-validating a translated query pattern against a query log using an occurrence threshold?',
'US8655901B1哪一方法Claim要求按出现次数阈值，以查询日志交叉验证翻译后的查询模式？',
'方法Claim 7（系统Claim 14有平行表达）：cross-validating the translated query pattern with a query log with respect to a specified occurrence threshold。',[
ev('US8655901B1',7,'7. The method of claim 1 , where extracting a translated query pattern further comprises cross-validating the translated query pattern with a query log with respect to a specified occurrence threshold.')])

add(6,'C_cross_document',
'Compare how US7991757B2 and US8095432B1 select or rank recommendations. Does either claim say the two systems interoperate?',
'比较US7991757B2与US8095432B1的推荐选择/排序依据；原文是否说两个系统互操作？',
'前者Claim 1从外部recommenders取得scores，经normalize后选subset；后者Claim 1依据社交relationship proximity排序，朋友的rank高于非朋友。两者共享推荐排序主题是本次比较归纳；所引Claims没有声称两专利系统互操作，不能推断两专利绝无其他关联。',[
ev('US7991757B2',1,'an optimization module configured to normalize the associated scores; wherein the recommendations service is further configured to select a subset of the recommendations, based at least in part on the normalized scores, to provide to the content site.'),
ev('US8095432B1',1,'ranking, using the processor, the first recommendation with a first rank and the second recommendation with a second rank based on the first relationship proximity and the second relationship proximity, wherein the first rank exceeds the second rank')],
comparison_relation_type='Analyst comparison of separate primary-source facts; no asserted patent-to-patent relationship.')

add(7,'C_cross_document',
'Compare the source-selection criterion in US8509827B2 with the entity-driven content request in US10867122B1. What does each explicitly require?',
'比较US8509827B2的数据源选择标准与US10867122B1的实体驱动内容请求，两者各自明确要求什么？',
'US8509827B2 Claim 1按包括获取成本的参数排序context-data sources；US10867122B1 Claim 1请求与first和second factual entity均相关的UI内容。共同的上下文内容获取主题是比较，不是原文声明的专利间链接。',[
ev('US8509827B2',1,'algorithmically ranking the at least one context data source according a specified parameter, wherein the specified parameter comprises a pecuniary cost to acquire the context data from the at least one context data source'),
ev('US10867122B1',1,'requesting, for a user interface element, content that is related to both the first factual entity and the second factual entity, wherein the user interface element provides a collection of content related to the first factual entity and the second factual entity within the display environment')],
comparison_relation_type='Analyst comparison, not an extracted patent-to-patent factual edge.')

add(8,'D_natural_cross_chunk_candidate',
'In US9514753B2, trace the claim dependency chain connecting hash-table speaker candidates to selection using the smallest cosine distance below a maximum threshold. Identify the relevant claims and conditions.',
'追踪US9514753B2从哈希表候选说话人到按最小余弦距离及最大阈值选取说话人的Claim依赖链。',
'Claim 11依赖10，10依赖9，9依赖1；1以hash values从hash tables取得speaker vectors，9按similarity scores选most similar，10用cosine distance，11要求smallest cosine distance低于maximum distance threshold。这里是原文依赖链，不应把余弦距离最小条件错误归为Claim 1的逐字要求。',[
ev('US9514753B2',1,'determining a set of speaker vectors from a plurality of hash tables using the hash values'),
ev('US9514753B2',9,'9. The method of claim 1 , wherein comparing the speaker vectors in the set with the utterance vector comprises determining similarity scores'),
ev('US9514753B2',10,'10. The method of claim 9 , wherein determining similarity scores that each indicate a degree of similarity of the utterance vector and one of the speaker vectors in the set comprises determining a cosine distance between the utterance vector and each of the speaker vectors in the set.'),
ev('US9514753B2',11,'11. The method of claim 10 , wherein selecting the speaker vector that the similarity scores indicate is most similar to the utterance vector comprises: identifying a smallest cosine distance from among the determined cosine distances; determining that the smallest cosine distance is less than a maximum distance threshold value; and based on determining that the smallest cosine distance is less than the maximum distance threshold value, selecting the speaker vector corresponding to the smallest cosine distance.')],
chunk_boundary_status='candidate_only_pending_actual_official_tokenizer_mapping',dependency_chain=[11,10,9,1],failure_inference_permitted=False)

add(9,'D_natural_cross_chunk_candidate',
'In US9298709B2, connect the geographic-map-based IP-rights visualization process to the on-screen-button update condition. Which dependent claims establish that connection?',
'追踪US9298709B2地图范围内IP权利可视化流程与屏幕按钮触发更新条件之间的Claim依赖。',
'Claim 17依赖16，16依赖10；10生成地理范围及限制条件筛选后的IP可视化，16规定user initiated command之后更新，17指定pressing of an on-screen button。应保留10→16→17的从属关系。',[
ev('US9298709B2',10,'restricting the list of IP rights based on one or more restriction criteria related to the IP rights to form a restricted list of IP rights, generating and displaying an information pane containing one or more data visualizations related to the restricted list of IP rights'),
ev('US9298709B2',16,'16. A process according to claim 10 , wherein generating or updating each data visualization displayed in the information pane based on each set of successively obtained geographic coordinates of the current viewable area of the geographic map display occurs following a user initiated command.'),
ev('US9298709B2',17,'17. A process according to claim 16 , wherein the user initiated command comprises the pressing of an on-screen button.')],
chunk_boundary_status='candidate_only_pending_actual_official_tokenizer_mapping',dependency_chain=[17,16,10],failure_inference_permitted=False)

add(10,'B_claim_evidence',
'In US11423041B2, which dependent system claim says the first ETL process is external to the ETL service while the second is performed by that service? Contrast it with the next claim.',
'US11423041B2哪一从属系统Claim规定首个ETL过程在服务外执行、第二个由服务执行？与下一Claim有何区别？',
'Claim 5：first external、second by service；Claim 6：first和second都由ETL service执行。这是不同从属实施限定，不能把二者同时强加于同一个实施。',[
ev('US11423041B2',5,'5. The system of claim 1 , wherein the first ETL process is performed external to the ETL service and wherein the second ETL process is performed by the ETL service.'),
ev('US11423041B2',6,'6. The system of claim 1 , wherein the first ETL process is performed by the ETL service and wherein the second ETL process is performed by the ETL service.')])

out={'schema_version':'1.0','dataset':'lj408/Dis2Pat','query_execution_status':'not_run','review_method':'AI-assisted reading of source text, exact-substring and numbered-claim mechanical validation; not an independent human gold standard','source_file_sha256':hashlib.sha256((BASE/'data/selected_patents.json').read_bytes()).hexdigest(),'question_count':len(questions),'questions':questions,'interpretation_rules':['Missing answers are not system failures.','Cross-chunk candidates must be confirmed against actual chunk mapping before classification.','A missing graph edge alone does not identify chunking as the cause.','Citation errors must be assessed separately from extraction errors.','Negative claims about interoperability are limited to the cited text.']}
(BASE/'results/questions.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
lines=['LightRAG patent evidence ground truth - NOT EXECUTED','AI-assisted source review; each quotation checked as an exact substring of the designated numbered claim.','No official queries, generated answers, citations, or retrieval results are present in this file.','']
for q in questions:
    lines += [q['id']+' '+q['category'],q['question'],q['question_zh'],'Expected: '+q['expected_answer_zh']]
    for e in q['evidence']: lines += [f"{e['publication_number']} Claim {e['claim_number']} | {e['source_url']}",e['quote'],f"Raw claims characters [{e['quote_char_start_in_raw_claims']}, {e['quote_char_end_in_raw_claims']})"]
    lines.append('Status: not_run\n')
(BASE/'evidence/question_ground_truth.txt').write_text('\n'.join(lines))
summary={'questions':len(questions),'evidence_quotes':sum(len(q['evidence']) for q in questions),'all_exact_quote_and_claim_checks_passed':True,'query_calls':0,'question_ids':[q['id'] for q in questions]}
(BASE/'evidence/question_validation.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
