# Licence of data/

The repository's MIT licence does **not** apply to this directory (`data/`).

- Source: Dis2Pat, <https://huggingface.co/datasets/lj408/Dis2Pat>, split `train`, revision `eda4a497291e9e8b898639881c34f158524732fc`
- Licence: Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA-4.0), <https://creativecommons.org/licenses/by-sa/4.0/>
- Attribution: the Dis2Pat dataset authors (lj408 on Hugging Face)
- Content: the 20 records actually used (`selected_raw/`, `selected_patents.json`) and the files derived from them: `documents/`, `claims/`, the manifests and the verification files. Derived files only add section labels; the text is not rewritten. They are shared under the same licence.
- The code under `data/round1/scripts/` is repository code and is MIT-licensed.

## The LightRAG index of experiment 01

[`experiments/01_baseline_index_qa/index/`](../experiments/01_baseline_index_qa/index/README.md) contains the LightRAG index built from these 20 patents in the original run of 2026-10-29. It includes the indexed patent text from Dis2Pat (title, abstract, claims, split into chunks) and data derived from it: extracted entities and relations with their descriptions, embeddings, and cached LLM responses for extraction and queries. It is shared under the same licence, **CC-BY-SA-4.0**, with attribution to the Dis2Pat dataset authors; the repository's MIT licence does not apply to it.
