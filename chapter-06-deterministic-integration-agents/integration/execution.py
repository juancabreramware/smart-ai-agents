from __future__ import annotations
from integration.ground_truth import bind_step

def execute_plan(plan,req,contract,env):
    outputs=[]; actions=[]
    for step in plan.steps:
        a=bind_step(step,req); actions.append(a); outputs.append(env.execute(a,contract))
    return {'actions':actions,'outputs':outputs,'final':outputs[-1] if outputs else None}
