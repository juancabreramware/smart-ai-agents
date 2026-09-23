from .contracts import get_contract
from .capabilities import execute,promote
from .registry import Registry,compatibility
from .provider import candidate
from .models import Decision,Usage
def dec(o):return Decision(o["action"],o["value"],o.get("label"))
class Baseline:
    def __init__(self,p):self.p=p
    def handle(self,r):
        x=self.p.decide(r);return dec(x.output),"baseline_reasoning",x.usage,None,"n/a",False
class Smart:
    def __init__(self,p):self.p=p;self.reg=Registry()
    def handle(self,r):
        c=get_contract(r.family,r.contract_version);cap=self.reg.get(r.family);ok,why=compatibility(cap,c,r.inputs);u=Usage();route="deterministic_reuse";inv=False
        if not ok:
            route="relearning" if cap else "initial_acquisition";inv=bool(cap)
            if cap:self.reg.invalidate(r.family)
            x=self.p.acquire(r);u=x.usage;cap=promote(candidate(x),c,self.reg.next_version(r.family));self.reg.put(cap)
        if r.reasoning_required:
            x=self.p.decide(r);u=Usage(u.input_tokens+x.usage.input_tokens,u.output_tokens+x.usage.output_tokens,u.cost_usd+x.usage.cost_usd,u.latency_ms+x.usage.latency_ms)
            return dec(x.output),"reasoning_required",u,cap,why,inv
        return execute(cap.operation,r.inputs,c),route,u,cap,why,inv
class Naive:
    def __init__(self,p):self.p=p;self.mem={}
    def handle(self,r):
        c=get_contract(r.family,r.contract_version);u=Usage()
        if r.family not in self.mem:
            x=self.p.acquire(r);u=x.usage;self.mem[r.family]=(x.output["operation"],r.contract_version);route="initial_acquisition"
        elif r.reasoning_required:
            x=self.p.decide(r);return dec(x.output),"reasoning_required",x.usage,None,"coarse_reuse",False
        else:route="naive_reuse"
        op,v=self.mem[r.family];old=get_contract(r.family,v);return execute(op,r.inputs,old),route,u,None,"coarse_reuse",False
