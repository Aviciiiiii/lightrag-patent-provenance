LightRAG evidence delivery: three independent ZIP files

No experiments or model API calls were performed for this delivery operation.
The original complete ZIP is unchanged. All 1,321 entries from it are assigned
exactly once across these three independently extractable ZIP files. Each is
strictly below 10,000,000 bytes. Additional delivery-only notes clearly audit
the limits of the exact-endpoint metric and do not change the original report.

Part 1: original report, scripts, configuration/evaluation/source evidence,
prior minimal-control archive, and an early consecutive range of API calls.
Part 2: all 18 persistent graph/index workspaces.
Part 3: the remaining API calls. Each call's request and responses stay together.
See SPLIT_MANIFEST.json for exact membership, byte sizes and file SHA256 values.

RECONSTRUCTION
1. Download all three ZIPs and place them in one directory.
2. Verify their SHA256 values against the accompanying SHA256SUMS.txt.
3. Extract each ZIP into the same NEW empty directory, retaining paths.
   SPLIT_README.txt and SPLIT_MANIFEST.json are identical in all three archives;
   overwriting these two identical control files is safe. The original 1,321
   entries are disjoint across parts. Do not extract over earlier experiments.
4. Open round4_full_20261030/report/LightRAG_patent_provenance_report_zh.html.
5. Read delivery_notes/endpoint_metric_audit.txt before interpreting edge scores.
6. Run python3 verify_split_contents.py from the reconstructed directory.
   It checks every payload's byte length and SHA256 against SPLIT_MANIFEST.json.

This restores byte-identical evidence FILES, not a byte-identical ZIP container.
The original complete ZIP SHA256 is recorded in SPLIT_MANIFEST.json.
This is not a .z01 multipart archive; every ZIP can be inspected independently.
No credentials or model/virtual-environment binaries were added. Existing old
deadlines and budgets in scripts remain; do not run paid scripts without fresh
authorization. Packaging and post-hoc graph audit are not new experimental data.
