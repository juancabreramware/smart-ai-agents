from __future__ import annotations
from dataclasses import dataclass,asdict

@dataclass(frozen=True)
class CostProfile:
    acquisition_micro:int; validation_micro:int; maintenance_micro:int; relearning_micro:int; deterministic_execution_micro:int
DEFAULTS={
 "stable_recurring":CostProfile(2200,1200,300,2200,25),
 "stable_rare":CostProfile(3000,1600,300,3000,25),
 "volatile_recurring":CostProfile(2500,1500,900,2500,25),
 "high_validation_recurring":CostProfile(2400,9000,1200,2400,25),
 "ambiguous_judgment":CostProfile(999999,999999,0,999999,25),
 "emerging_pattern":CostProfile(2200,1200,300,2200,25),
}
INPUT_USD_PER_MILLION=0.25
OUTPUT_USD_PER_MILLION=2.00

def provider_cost_micro(input_tokens:int,output_tokens:int)->int:
    return int(round(input_tokens*INPUT_USD_PER_MILLION+output_tokens*OUTPUT_USD_PER_MILLION))
def assigned_promotion_cost(family:str,relearning:bool=False)->int:
    c=DEFAULTS[family]; return (c.relearning_micro if relearning else c.acquisition_micro)+c.validation_micro+c.maintenance_micro
def deterministic_cost(family:str)->int:return DEFAULTS[family].deterministic_execution_micro
def cost_profiles_dict():return {k:asdict(v) for k,v in sorted(DEFAULTS.items())}
