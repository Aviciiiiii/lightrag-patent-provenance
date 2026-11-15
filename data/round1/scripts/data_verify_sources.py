import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
import urllib.request,pathlib,ssl,certifi,json,datetime,re,hashlib,concurrent.futures,bs4
base=(legacy_root()/'data');m=json.loads((base/'manifest.json').read_text());ctx=ssl.create_default_context(cafile=certifi.where());norm=lambda x:re.sub(r'\s+',' ',x).strip()
def check(entry):
 pub=entry['publication_number'];url=f'https://patents.google.com/patent/{pub}/en';dest=base/'source_checks'/f'{pub}.html'
 try:
  if not dest.exists():
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),context=ctx,timeout=20) as res: raw=res.read(5_000_001)
   if len(raw)>5_000_000:raise RuntimeError('Source size cap')
   dest.write_bytes(raw)
  s=bs4.BeautifulSoup(dest.read_bytes(),'html.parser');r=json.loads((base/'selected_raw'/f'{pub}.json').read_text())
  ab=s.select_one('[itemprop=abstract] [itemprop=content]').get_text(' ',strip=True);cl=s.select_one('section[itemprop=claims] [itemprop=content]').get_text(' ',strip=True)
  (base/'source_checks'/f'{pub}.parsed.json').write_text(json.dumps({'publication_number':pub,'abstract':ab,'claims':cl},ensure_ascii=False,indent=2))
  out={'publication_number':pub,'url':url,'abstract_exact_after_whitespace_normalization':norm(ab)==norm(r['abstract']),'entire_claims_exact_after_whitespace_normalization':norm(cl)==norm(r['claims']),'source_claim_count':int(s.select_one('section[itemprop=claims] [itemprop=count]').get_text()),'raw_html_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
  if re.search(r'\bclaim\s+(?:further|comprising)',cl):out['source_quality_warning']='At least one dependent claim refers to "claim" without a number in both dataset and Google Patents HTML. No repair made.'
  return out
 except Exception as e:return {'publication_number':pub,'url':url,'error':type(e).__name__+': '+str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:checks=list(pool.map(check,m['records']))
result={'method':'HTML content extraction with BeautifulSoup; normalized whitespace only; comparison covers full abstract and entire claim set, not selected sentences. Source fidelity does not certify legal-text/OCR accuracy.','checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks}
(base/'source_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));m['source_verification']=result;m['validation']='20 unique US granted publications with nonempty abstract/claims, contiguous numbered claims, no Dataset Viewer truncated_cells; every source check result listed, including upstream anomalies.';(base/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
for c in checks: print(c['publication_number'],c.get('abstract_exact_after_whitespace_normalization'),c.get('entire_claims_exact_after_whitespace_normalization'),c.get('source_quality_warning',''),c.get('error',''))
