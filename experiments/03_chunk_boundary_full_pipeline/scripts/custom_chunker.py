"""Official six-argument extension: exact preplanned token windows, no text edits.

This module imports no model service, secret config, or LightRAG runtime.
Prepare expected_text using the exact content the official pipeline persists.
Do not silently strip or normalize in this callback: mismatches fail closed.
"""
from pathlib import Path
import json,hashlib

def make_precomputed_chunker(expected_text, token_ranges, *, audit_path=None):
    frozen_ranges=tuple((int(a),int(b)) for a,b in token_ranges)
    expected_hash=hashlib.sha256(expected_text.encode()).hexdigest()
    def chunking_func(tokenizer,content,split_by_character=None,split_by_character_only=False,chunk_overlap_token_size=100,chunk_token_size=1200):
        if content != expected_text:
            raise ValueError('Actual official input differs from frozen preflight text; no implicit normalization allowed')
        if split_by_character is not None or split_by_character_only:
            raise ValueError('Character splitting cannot be mixed with the controlled token plan')
        if chunk_overlap_token_size !=100 or chunk_token_size!=1200:
            raise ValueError('Round4 requires exactly1200 max tokens and100-token overlap')
        ids=tokenizer.encode(content)
        if tokenizer.decode(ids)!=content:
            raise ValueError('Whole document token roundtrip does not preserve source')
        if not frozen_ranges or frozen_ranges[0][0]!=0 or frozen_ranges[-1][1]!=len(ids):
            raise ValueError('Frozen windows must cover full document endpoints')
        output=[];audit=[]
        for i,(start,end) in enumerate(frozen_ranges):
            if not(0<=start<end<=len(ids)) or end-start>chunk_token_size:
                raise ValueError('Invalid or oversized global token window')
            if i and (start!=frozen_ranges[i-1][1]-100 or end<=frozen_ranges[i-1][1]):
                raise ValueError('Windows must advance and have exactly100 shared global tokens')
            prefix=tokenizer.decode(ids[:start]);text=tokenizer.decode(ids[start:end]);suffix=tokenizer.decode(ids[end:])
            if prefix+text+suffix!=content:
                raise ValueError('Window splits a Unicode codepoint')
            actual_tokens=len(tokenizer.encode(text))
            if actual_tokens>chunk_token_size:
                raise ValueError('Decoded window exceeds the true retokenized1200-token ceiling')
            # The core contract accepts exactly these fields. Span audit stays external.
            output.append({'tokens':actual_tokens,'content':text,'chunk_order_index':i})
            audit.append({'chunk_order_index':i,'global_token_span':[start,end],
                'source_char_span':[len(prefix),len(prefix)+len(text)],'actual_tokens':actual_tokens,
                'content_sha256':hashlib.sha256(text.encode()).hexdigest(),
                'overlap_previous_global_tokens':100 if i else 0})
        if audit_path:
            p=Path(audit_path);p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(json.dumps({'source_sha256':expected_hash,'source_tokens':len(ids),'chunks':audit},indent=2)+'\n')
        return output
    return chunking_func

def shifted_windows(token_count,first_end,max_tokens=1200,overlap=100):
    """Complete ordered windows with a predeclared first-short-window shift."""
    if max_tokens!=1200 or overlap!=100:raise ValueError('Fixed protocol sizes required')
    if not(0<first_end<=min(max_tokens,token_count)):raise ValueError('Invalid first end')
    if first_end<token_count and first_end<=overlap:raise ValueError('First window must advance beyond overlap')
    out=[(0,first_end)]
    while out[-1][1]<token_count:
        start=out[-1][1]-overlap
        out.append((start,min(start+max_tokens,token_count)))
    return out
