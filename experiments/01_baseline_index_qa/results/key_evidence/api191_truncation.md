# API 191: extraction output cut off at the 3500-token limit

Request `max_tokens=3500`; response `finish_reason=length`, `completion_tokens=3500`. Last lines of the response:

```
relation<|#|>Class-Based Language Model Features<|#|>GEO_BI_FIRST<|#|>includes<|#|>The class-based language model features include GEO_BI_FIRST.
relation<|#|>Class-Based Language Model Features<|#|>GEO_BI_SECOND<|#|>includes<|#|>The class-based language model features include GEO_BI_SECOND.
relation<|#|>Class-Based Language Model Features<|#|>GEO_TRI_FIRST<|#|>includes<|#|>
```

The last relation line, `Class-Based Language Model Features → GEO_TRI_FIRST`, is incomplete; the official parser drops it, so the final graph lacks this edge (see section C of report 01, [`reports/translated/01_baseline_index_qa_report_en.md`](../../../../reports/translated/01_baseline_index_qa_report_en.md), and `evidence/extraction_truncation_parser_replay.json`).
