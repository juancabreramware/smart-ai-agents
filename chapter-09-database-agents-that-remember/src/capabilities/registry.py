import json
class CapabilityRegistry:
    def __init__(self): self.active={}; self.history=[]
    def get(self,f): return self.active.get(f)
    def promote(self,c): self.active[c.family_id]=c; self.history.append(c.to_dict())
    def invalidate(self,f):
        if f in self.active: self.active[f].status='invalidated'; self.active.pop(f)
    def snapshot(self,path): path.write_text(json.dumps({'active':{k:v.to_dict() for k,v in self.active.items()},'history':self.history},indent=2))
