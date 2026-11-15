# Artificial chunking control: the same Claims 26–28, two boundaries

Source: `results/chunk_{SAME,CROSS}_r{1,2,3}_c{0,1}.json` (raw extraction output of the model). Only relation descriptions with Registration Module as an endpoint are listed. In CROSS the boundary falls inside the Claim 27 sentence, before “machine readable descriptions”.

| condition / repeat | relation descriptions of Registration Module (verbatim) |
|---|---|
| SAME r1 | The registration module is configured to allow a provider of an external recommender to provide machine readable descriptions. |
| SAME r2 | The registration module is a module of the computer system of claim 1 and is configured to allow providers to provide machine readable descriptions.<br>The registration module is configured to allow a provider of an external recommender to provide machine readable descriptions of the external recommender. |
| SAME r3 | The computer system comprises the registration module.<br>The registration module is configured to allow a provider of an external recommender to provide machine readable descriptions. |
| CROSS r1 | The registration module is configured to allow a provider of an external recommender to provide something. |
| CROSS r2 | The registration module is configured to allow a provider of an external recommender to provide something. |
| CROSS r3 | The registration module is configured to allow a provider of an external recommender to provide something. |
