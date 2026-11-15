import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
import pathlib,json,re,hashlib,csv,datetime
base=(legacy_root()/'data')
d=json.loads((base/'dis2pat_train_rows_0000.json').read_text())
selected=[8,10,21,22,25,28,29,37,49,50,52,54,60,69,72,73,77,84,85,88]
manifest=[]; records=[]; (base/'documents').mkdir(exist_ok=True); (base/'selected_raw').mkdir(exist_ok=True);(base/'claims').mkdir(exist_ok=True)
for i in selected:
 wrapper=d['rows'][i];r=wrapper['row'];pub=r['publication_number'];claims=r['claims']
 starts=list(re.finditer(r'\b(\d+)\.\s+(?=[A-Z])',claims));nums=[int(x.group(1)) for x in starts]
 assert nums==list(range(1,len(nums)+1)),(pub,nums)
 assert not wrapper.get('truncated_cells'),pub
 assert all(r[k] and 'TRUNCATED' not in r[k] for k in ['title','abstract','claims'])
 assert re.match(r'US\d+B[12]$',pub)
 claimparts=[{'claim_number':int(m.group(1)),'start_char_in_raw_claims':m.start(),'end_char_in_raw_claims': starts[j+1].start() if j+1<len(starts) else len(claims),'text':claims[m.start():starts[j+1].start() if j+1<len(starts) else len(claims)].strip()} for j,m in enumerate(starts)]
 (base/'selected_raw'/f'{pub}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
 (base/'claims'/f'{pub}.json').write_text(json.dumps(claimparts,ensure_ascii=False,indent=2))
 # Only source values and section labels; the source claims text is not rewritten.
 text=f'Publication number: {pub}\nTitle: {r["title"]}\n\nABSTRACT\n{r["abstract"]}\n\nCLAIMS\n{claims}\n'
 (base/'documents'/f'{pub}.txt').write_text(text)
 entry={'publication_number':pub,'title':r['title'],'dataset':'lj408/Dis2Pat','split':'train','row_idx':i,'claim_count':len(nums),'abstract_chars':len(r['abstract']),'claims_chars':len(claims),'specification_chars':len(r['specification']),'sha256_document':hashlib.sha256(text.encode()).hexdigest(),'viewer_truncated_cells':wrapper.get('truncated_cells'),'patent_url':f'https://patents.google.com/patent/{pub}/en','document':f'documents/{pub}.txt','scope':'information retrieval, recommendation, context ranking, and data/relationship indexing'}
 manifest.append(entry);records.append(r)
assert len({x['publication_number'] for x in manifest})==len(manifest)
(base/'manifest.json').write_text(json.dumps({'dataset':'lj408/Dis2Pat','dataset_url':'https://huggingface.co/datasets/lj408/Dis2Pat','viewer_url':'https://datasets-server.huggingface.co/rows?dataset=lj408%2FDis2Pat&config=default&split=train&offset=0&length=100','sample_method':'Purposive selection of related information retrieval, recommendation, context ranking, and relationship/data indexing patents from first 100 train rows. Not a representative random sample. One repeated publication in fetched batch was not selected twice.','input_fields':['publication_number','title','abstract','claims'],'excluded_from_index':['specification','disclosure','figures'],'exclusion_reason':'Use complete authentic abstract/claims to constrain time and cost; generated disclosure intentionally excluded. Specification preserved in raw JSON for verification only.','validation':'20 unique US granted publications; all have nonempty abstracts/claims, sequential numbered claims and no Dataset Viewer truncated_cells. These are structural checks; source text correspondence checked separately on two patents.','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'records':manifest},ensure_ascii=False,indent=2))
with (base/'manifest.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(manifest[0]));w.writeheader();w.writerows(manifest)
(base/'selected_patents.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print(json.dumps({'patents':len(records),'claims':sum(x['claim_count'] for x in manifest),'abstract_chars':sum(x['abstract_chars'] for x in manifest),'claim_chars':sum(x['claims_chars'] for x in manifest),'documents_bytes':sum(p.stat().st_size for p in (base/'documents').glob('*.txt'))},indent=2))
