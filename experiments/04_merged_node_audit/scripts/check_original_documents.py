import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
from pathlib import Path
import hashlib,json
O=legacy_root('round2_multisource_audit')/'round2_multisource_audit';ROOT=legacy_root('round2_multisource_audit')
docs=json.loads((O/'evidence/document_registry.json').read_text());rows=[]
for pub,d in docs.items():
 p=ROOT/'data/documents'/f'{pub}.txt';b=p.read_bytes();original=b.decode();indexed=d['content']
 rows.append({'publication_number':pub,'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest(),'original_chars':len(original),'indexed_chars':len(indexed),'exact_equal':original==indexed,'only_difference_one_terminal_LF':original==indexed+'\n','strip_equal':original.strip()==indexed})
out={'documents':len(rows),'all_byte_exact_equal':all(r['exact_equal'] for r in rows),'all_equal_after_removing_one_terminal_LF':all(r['only_difference_one_terminal_LF'] for r in rows),'interpretation':'Each saved original document has one terminal newline removed in the indexed full-doc text. No interior/content difference; no original file was changed. Quoted Claim/chunk coordinates refer to the indexed full-doc text.','rows':rows}
assert out['all_equal_after_removing_one_terminal_LF']
(O/'evidence/indexed_text_original_document_check.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
