LightRAG round2 multi-publication node audit — offline evidence package

Scope: the existing round2 baseline only. Official LightRAG v1.5.7 commit
28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c. 20 patents,48 saved chunks,612 nodes,
994 edges. No new indexing,LLM,embedding or retrieval calls were performed.
No credentials were read for this audit. FOT/AutoDL/SSH/proxy were not accessed.

Results:38 cross-publication nodes,98 node/publication memberships.
Final categories:3 shared_specific_concept,29 shared_broad_class,
6 contextual_conflation,0 insufficient_evidence.
The six are NOT six proven bugs or wrong identity links. Five are explicitly
ontology/scope-sensitive. 266 distinct actual incident edges were reviewed;
three source-local actor-granularity warnings are reported separately from
cross-publication wrong-edge propagation. No such propagation was demonstrated.
AI-assisted review is not independent human gold.

START HERE
round2_multisource_audit/report/LightRAG_round2_multisource_node_audit_zh.html
round2_multisource_audit/report/round2_multisource_nodes.csv (38 rows)
round2_multisource_audit/report/round2_multisource_sources.csv (98 rows)
round2_multisource_audit/report/round2_multisource_nodes.json (full structured audit)

Extract into a NEW empty directory, keeping paths. Do not overwrite original
experiment folders. All audit commands below require Python3.10+ standard
library only; no model service,API key,venv or package installation is required.
Run from the extraction root:

python3 round2_multisource_audit/scripts/build_inventory.py
python3 round2_multisource_audit/scripts/validate_reviews.py --require-complete
python3 round2_multisource_audit/source_mapping_audit.py
python3 round2_multisource_audit/scripts/build_report.py

These regenerate derived counts/dossiers/report only. They do not rerun LLM
extraction or invent new semantic labels. Retained initial reviews and explicit
root_adjudications.json are inputs to report construction. Timestamp fields
change on reproduction; input hashes and substantive counts should match.

TRACEABILITY
Original source data are under round2/ and data/. The full cached extraction
responses cover47chunks; saved raw APIresponse191 covers the one uncached,
truncated extraction. It is explicitly marked finish_reason=length. The archive
contains no embedding vectors/model weights or runnable paid experiment runner.
The official source archive is retained for code-mechanism verification only.

Every node's original ID/type/source fields and actual edge endpoints are in
the JSON/dossiers. source_id is a <SEP>-joined list; file_path is a separate
deduplicated list. Never zip those lists positionally. Use chunk→full_doc_id→
publication mapping. source IDs alone do not identify Claims.

Each quoted Claim/Abstract is checked against its actual source chunk and
indexed full document. Authoritative repeated-quote coordinates are in
evidence/review_validation.json (Claim+Chunk anchored). Initial N024–N026 review
metadata sometimes uses exact_full_doc_char_start for a first literal occurrence;
the final consolidated JSON renames it and supplies authoritative quote locations.

MANIFEST.json lists every packaged payload byte length and SHA256. Run
verify_package_contents.py to check them. SHA256SUMS.txt outside the ZIP records
the ZIP container hash. The original experiments and prior reports remain intact.
