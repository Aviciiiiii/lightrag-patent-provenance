# F01 (US9589231B2): raw extraction of the same full text under two chunk boundaries (r3, no truncation in either)

Only relations whose description involves the ontology together with cases/experts or UMLS are listed (records after the official parser, `results/F01_{A,B}_r3/parsed_extraction.json`). Claim 4: “the embedding of the existing medical cases and the set of experts being also based on the medical ontology”; Claim 8: “the medical ontology is based on the Unified Medical Language System”.

**A_r3 (same-chunk)**

- Diagnosis Assistance Method → Medical Ontology: The embedding of the new medical case, existing medical cases, and experts is based on a medical ontology.
- Medical Ontology → Unified Medical Language System: The medical ontology is based on the Unified Medical Language System.
- Multidimensional Representation → Matrix Of Proximities: A matrix of proximities is applied to the multidimensional representation of the new case to account for relationships between concepts in the ontology.

**B_r3 (cross-chunk)**

- Multidimensional Representation → Medical Ontology: The multidimensional representation of the medical case is computed based on the medical ontology.
- Matrix Of Proximities → Multidimensional Representation: The matrix of proximities is applied to the multidimensional representation of the new case to account for relationships between concepts in the ontology.
- Medical Ontology → Unified Medical Language System: The medical ontology is based on the Unified Medical Language System.

Note: under condition B the Claim 4 sentence lies **entirely inside the first chunk**; it is not split. The difference is in how the model represented it during extraction. In the original run, r3 is the only clean pair (no truncation on either side).
