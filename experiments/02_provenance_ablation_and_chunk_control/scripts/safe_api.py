"""Real configured-service calls with secret-free logs, deadlines and spend bounds."""
import sys as _lrp_sys, pathlib as _lrp_pl; _lrp_sys.path.insert(0, str(_lrp_pl.Path(__file__).resolve().parents[3]))  # repo root (paths.py)
from paths import legacy_root  # path mapping only, see paths.py
import asyncio, datetime as dt, json, math, os, sys, time
from pathlib import Path
from urllib.parse import urlsplit

ROOT=legacy_root('round3')
ROUND=ROOT/'round3'
sys.path.insert(0,str(ROOT/'src/LightRAG-v1.5.7'))
os.environ['TIKTOKEN_CACHE_DIR']=str(ROOT/'tiktoken_cache')
import certifi
os.environ['SSL_CERT_FILE']=certifi.where()
os.environ['REQUESTS_CA_BUNDLE']=certifi.where()
import httpx
from dotenv import dotenv_values
# Direct httpx transport preserves the OpenAI-compatible JSON request; no SDK retries or heavyweight imports.
# Generation-only controls do not instantiate LightRAG; official parser is used in the separate extraction evaluator.

from repro_runtime import get_runtime
_runtime=get_runtime()
START=_runtime.start
QUERY_DEADLINE=_runtime.query_deadline
DEADLINE=_runtime.deadline
CONFIG_PATH=_runtime.config_path
CAP_CNY=10.0
INPUT_CNY_PER_M=2.0
OUTPUT_CNY_PER_M=8.0

def now():return dt.datetime.now(dt.timezone.utc)
def write_json(path,data):
    path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str))
    tmp.replace(path)

def safe_error(exc):
    status=getattr(exc,'status_code',None) or getattr(getattr(exc,'response',None),'status_code',None)
    return {'type':type(exc).__name__,'http_status':status,
            'diagnosis':{400:'request/model parameter rejection',401:'authentication rejected',403:'permission rejected',404:'model or endpoint not found',429:'rate limit or quota'}.get(status,'transport/runtime failure; exception text withheld to protect secrets')}

class SafeAPI:
    def __init__(self,stage):
        # The only credential read. Values remain in process memory and clients.
        cfg=dotenv_values(str(CONFIG_PATH))
        required=['LLM_BINDING_HOST','LLM_MODEL','LLM_BINDING_API_KEY','EMBEDDING_BINDING_HOST','EMBEDDING_MODEL','EMBEDDING_BINDING_API_KEY']
        if any(not cfg.get(k) for k in required):raise ValueError('required configuration field missing')
        for field in ['LLM_BINDING_HOST','EMBEDDING_BINDING_HOST']:
            u=urlsplit(cfg[field])
            if u.scheme!='https' or u.hostname!='api.siliconflow.cn' or u.username or u.password or u.query:
                raise ValueError('configured service differs from explicitly price-verified host')
        self.stage=stage;self.llm_model=cfg['LLM_MODEL'];self.embedding_model=cfg['EMBEDDING_MODEL']
        if self.llm_model!='deepseek-ai/DeepSeek-V4.1-Flash' or self.embedding_model!='BAAI/bge-m3':
            raise ValueError('configured models differ from explicitly priced models')
        self.dim=int(cfg.get('EMBEDDING_DIM') or 1024)
        self.embedding_token_limit=int(cfg.get('EMBEDDING_TOKEN_LIMIT') or 8192)
        self.llm=httpx.AsyncClient(base_url=cfg['LLM_BINDING_HOST'].rstrip('/')+'/',
            headers={'Authorization':'Bearer '+cfg['LLM_BINDING_API_KEY']},timeout=160,follow_redirects=False)
        self.lock=asyncio.Lock();self.semaphore=asyncio.Semaphore(2)
        self.ledger_path=ROUND/'results/cost_ledger.json'
        self.ledger=json.loads(self.ledger_path.read_text()) if self.ledger_path.exists() else {
            'run_start_utc':START.isoformat(),'currency':'CNY','hard_cap_cny':CAP_CNY,'budget_conversion_cny_per_usd':4,
            'note':'Conservative price estimate, not provider invoice. Peak rates; no cache discount. Unknown outcomes retain reservation.',
            'estimated_observed_cost_cny':0.0,'reserved_unknown_cny':0.0,'calls':[]}
        if self.ledger.get('run_start_utc')!=START.isoformat():
            raise RuntimeError('Cost ledger belongs to a different or unknown run session; refusing to continue')
        self.public={'provider':'SiliconFlow','host':'https://api.siliconflow.cn/v1','llm_model':self.llm_model,
                     'embedding_model':self.embedding_model,'embedding_dim':self.dim,'embedding_token_limit':self.embedding_token_limit,
                     'client_max_retries':0,'enable_thinking':False,'start_utc':START.isoformat(),
                     'query_deadline_utc':QUERY_DEADLINE.isoformat(),'deadline_utc':DEADLINE.isoformat(),'hard_cap_cny':CAP_CNY}
        write_json(ROUND/'evidence/public_runtime_config.json',self.public)

    def check_deadline(self):
        if now()<START:raise RuntimeError('experiment shared start is in the future')
        if now()>=DEADLINE:raise TimeoutError('experiment hard deadline reached')

    async def reserve(self,kind,reservation):
        async with self.lock:
            self.check_deadline()
            if self.ledger.get('stop_reason'):raise RuntimeError(self.ledger['stop_reason'])
            if len(self.ledger['calls'])>=40:raise RuntimeError('absolute API attempt cap reached')
            used=self.ledger['estimated_observed_cost_cny']+self.ledger['reserved_unknown_cny']
            if used+reservation>CAP_CNY:raise RuntimeError('conservative budget cap reached before call')
            call={'id':len(self.ledger['calls'])+1,'stage':self.stage,'kind':kind,'started_utc':now().isoformat(),
                  'reservation_cny':reservation,'state':'reserved_before_dispatch'}
            self.ledger['reserved_unknown_cny']+=reservation
            self.ledger['calls'].append(call);write_json(self.ledger_path,self.ledger)
            return call['id']

    async def finish(self,cid,usage,details,success=True,error=None):
        async with self.lock:
            c=self.ledger['calls'][cid-1]
            c.update(finished_utc=now().isoformat(),state='success' if success else 'failed_or_uncertain',**details)
            if error:c['error']=error
            valid_llm_usage=(usage is not None and all(isinstance(usage.get(k),(int,float)) and usage[k]>=0 for k in ['prompt_tokens','completion_tokens']))
            if usage is not None and (c['kind']!='llm' or valid_llm_usage):
                c['usage']=usage
                prompt=int(usage.get('prompt_tokens',usage.get('total_tokens',0)) or 0)
                completion=int(usage.get('completion_tokens',0) or 0)
                details_u=usage.get('completion_tokens_details') or {}
                reasoning=int(details_u.get('reasoning_tokens',0) or 0)
                cost=(prompt*INPUT_CNY_PER_M+(completion+reasoning)*OUTPUT_CNY_PER_M)/1_000_000 if c['kind']=='llm' else 0.0
                # Counting reasoning again when it is included in completion is deliberately conservative.
                c['estimated_cost_upper_cny']=cost
                self.ledger['reserved_unknown_cny']=max(0,self.ledger['reserved_unknown_cny']-c['reservation_cny'])
                self.ledger['estimated_observed_cost_cny']+=cost
                if reasoning>0 or details.get('reasoning_content_present'):
                    self.ledger['stop_reason']='thinking observed despite disabled request; stop calls for budget review'
            elif usage is not None:
                c['usage_incomplete_reservation_retained']=True
                c['usage']=usage
            if details.get('reasoning_content_present'):
                self.ledger['stop_reason']='thinking content observed despite disabled request; stop calls for budget review'
            c['cumulative_estimated_and_reserved_cny']=self.ledger['estimated_observed_cost_cny']+self.ledger['reserved_unknown_cny']
            write_json(self.ledger_path,self.ledger)

    async def complete(self,prompt,system_prompt=None,history_messages=None,**kwargs):
        messages=[]
        if system_prompt:messages.append({'role':'system','content':system_prompt})
        messages.extend(history_messages or [])
        messages.append({'role':'user','content':prompt})
        max_tokens=int(kwargs.pop('_experiment_max_tokens',3500))
        response_format=kwargs.get('response_format')
        if response_format is None and (kwargs.get('keyword_extraction') or kwargs.get('entity_extraction')):
            response_format={'type':'json_object'}
        if max_tokens>8192:raise ValueError('per-request output cap exceeded')
        # UTF8-byte bound intentionally exceeds expected tokenizer input count.
        input_bound=len(json.dumps(messages,ensure_ascii=False).encode())+2048
        if input_bound>180000:raise ValueError('per-request input safety bound exceeded')
        reserve=(input_bound*INPUT_CNY_PER_M+(max_tokens+32768)*OUTPUT_CNY_PER_M)/1_000_000
        async with self.semaphore:
            cid=await self.reserve('llm',reserve)
            request={'model':self.llm_model,'messages':messages,'max_tokens':max_tokens,
                     'temperature':0,'stream':False,'extra_body':{'enable_thinking':False}}
            if response_format:request['response_format']=response_format
            write_json(ROUND/'logs'/f'api_{cid:04d}_request.json',{'id':cid,'stage':self.stage,**request})
            try:
                body={k:v for k,v in request.items() if k!='extra_body'}
                body.update(request.get('extra_body') or {})
                res=await asyncio.wait_for(self.llm.post('chat/completions',json=body),timeout=min(165,(DEADLINE-now()).total_seconds()))
                res.raise_for_status()
                payload=res.json()
                write_json(ROUND/'logs'/f'api_{cid:04d}_provider_response.json',payload)
                usage=payload.get('usage')
                choice=payload['choices'][0];content=choice['message'].get('content') or ''
                result={'id':cid,'model_returned':payload.get('model'),'content':content,'finish_reason':choice.get('finish_reason'),'usage':usage,
                        'reasoning_content_present':bool(choice['message'].get('reasoning_content'))}
                write_json(ROUND/'logs'/f'api_{cid:04d}_response.json',result)
                await self.finish(cid,usage,{'model_returned':payload.get('model'),'finish_reason':choice.get('finish_reason'),'output_chars':len(content),
                                          'reasoning_content_present':result['reasoning_content_present']})
                if not content:raise RuntimeError('empty completion content')
                if choice.get('finish_reason')=='length':return content  # raw finish_reason retained; evaluator invalidates truncation
                return content
            except Exception as exc:
                # Never serialize SDK exceptions, headers, request objects, or configuration.
                if self.ledger['calls'][cid-1]['state']=='reserved_before_dispatch':
                    await self.finish(cid,None,{},success=False,error=safe_error(exc))
                raise RuntimeError(json.dumps(safe_error(exc))) from None

    async def embed(self,texts,**kwargs):
        raise RuntimeError('Embedding is disabled in round3; fixed retrieval is reused')

    async def close(self):
        await self.llm.aclose()
