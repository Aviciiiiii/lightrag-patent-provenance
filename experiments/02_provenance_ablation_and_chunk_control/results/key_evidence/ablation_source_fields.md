# Source-field ablation (Q11's retrieved context from API 392 frozen; only its presentation changes)

Condition names: dot's A = original context; B = +source fields (`publication_numbers`, `file_path`, `source_id` added to the 82 relations); C = B + the original text of US7991757B2 claims 1 and 27. The reference list is kept unchanged in all three (`[1]` is still US10867122B1.txt). Source: `results/ablation_{A,B,C}_r{1,2,3}.json`.

| condition | start of answer | references at the end |
|---|---|---|
| original context r1 | I do not have enough information to answer this query. The provided **Context** does not contain any document, knowledge-graph entity, or document chunk for **U… | [1] US10867122B1.txt, [4] US7756837B2.txt |
| original context r2 | I do not have enough information to answer this query. The provided **Context** does not contain any document, knowledge-graph entity, or document chunk for **U… | [1] US10867122B1.txt, [4] US7756837B2.txt, [5] US8095432B1.txt |
| original context r3 | I do not have enough information to answer this query. The provided **Context** does not contain any document, chunk, or knowledge-graph entity for **US7991757B… | [1] US10867122B1.txt, [4] US7756837B2.txt |
| +source fields r1 | I do not have enough information to answer this query. The provided **Context** does not contain the text of Claim 1 or Claim 27 of US7991757B2. **What the evid… | [1] US10867122B1.txt, [4] US7756837B2.txt, [5] US8095432B1.txt |
| +source fields r2 | I do not have enough information to answer this query. The provided **Context** does not contain the text of Claim 1 or Claim 27 of US7991757B2. **What the evid… | [1] US10867122B1.txt, [2] US9374411B1.txt, [3] US8655901B1.txt, [4] US7756837B2.txt, [5] US8095432B1.txt |
| +source fields r3 | I do not have enough information to answer this query. The provided **Context** does not contain the text of US7991757B2's claims. The only evidence relating to… | [1] US10867122B1.txt, [4] US7756837B2.txt |
| +source fields + claim text r1 | **US7991757B2 — Registration Capabilities in Claims 1 and 27** **Claim 1 (explicit evidence).** Claim 1 recites a system comprising a "registration module confi… | [1] US7991757B2.txt |
| +source fields + claim text r2 | **Claim 1 of US7991757B2** specifies a registration module within the claimed system. The claim recites: "a registration module configured to provide functional… | [1] US7991757B2.txt |
| +source fields + claim text r3 | **US7991757B2 — Registration Capability in Claims 1 and 27** **Claim 1 (explicit evidence).** Claim 1 recites a system comprising a "registration module configu… | [1] US7991757B2.txt |
