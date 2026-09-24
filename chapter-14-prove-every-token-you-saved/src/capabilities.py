from .models import Capability
class Registry:
    def __init__(self): self.items={}
    def get(self,family): return self.items.get(family)
    def compatible(self,cap,req): return bool(cap and cap.validated and cap.contract_version==req.contract_version and cap.invalidated_seq is None)
    def promote(self,req,operation):
        c=Capability(f"{req.family}:{operation}:{req.contract_version}",req.family,operation,req.contract_version,True,req.seq)
        self.items[req.family]=c; return c
    def invalidate(self,cap,req,reason="contract_changed"):
        cap.invalidated_seq=req.seq; cap.invalidation_reason=reason
