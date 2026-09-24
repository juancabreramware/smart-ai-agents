from __future__ import annotations
import os
# Frozen at run time through manifest. Defaults are configurable and are not claims about current market pricing.
INPUT_USD_PER_MILLION=float(os.getenv("CH13_INPUT_USD_PER_MILLION","0.25"))
OUTPUT_USD_PER_MILLION=float(os.getenv("CH13_OUTPUT_USD_PER_MILLION","2.0"))

def provider_cost_micro(input_tokens:int,output_tokens:int)->int:
    usd=(input_tokens/1_000_000)*INPUT_USD_PER_MILLION+(output_tokens/1_000_000)*OUTPUT_USD_PER_MILLION
    return int(round(usd*1_000_000))
