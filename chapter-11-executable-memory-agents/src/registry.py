class Registry:
    def __init__(self): self.caps={}; self.versions={}
    def get(self,f): return self.caps.get(f)
    def next_version(self,f): return self.versions.get(f,0)+1
    def put(self,c): self.caps[c.family]=c; self.versions[c.family]=c.capability_version
    def invalidate(self,f): return self.caps.pop(f,None)
def compatibility(cap,c,inputs):
    if cap is None:return False,"missing"
    if cap.validation_status!="validated":return False,"not_validated"
    if cap.operation!=c.operation:return False,"operation_changed"
    if cap.policy_fingerprint!=c.policy_fingerprint:return False,"policy_changed"
    if cap.environment_fingerprint!=c.environment_fingerprint:return False,"environment_changed"
    if cap.dependencies!=c.dependencies:return False,"dependencies_changed"
    if any(k not in inputs for k in c.dependencies):return False,"missing_inputs"
    return True,"compatible"
