import hashlib, json
PRICING_VERSION="chapter14-pricing-v1.0.0"
# Frozen benchmark constants, not claims of current market pricing.
PRICING={
 "P1":{"gpt-5-mini":{"input_per_million":250000,"output_per_million":2000000}},
 "P2":{"gpt-5-mini":{"input_per_million":300000,"output_per_million":1800000}},
}
COST_VERSION="chapter14-cost-manifest-v1.0.0"
ASSIGNED={
 "deterministic_execution_micro":25,
 "capability_validation_micro":120,
 "capability_acquisition_micro":180,
 "registry_operation_micro":5,
 "invalidation_micro":60,
 "relearning_micro":250,
}
def provider_cost_micro(model,epoch,input_tokens,output_tokens):
    p=PRICING[epoch][model]
    # prices are microdollars per million tokens => divide by 1e6, deterministic round-half-up
    numerator=input_tokens*p["input_per_million"]+output_tokens*p["output_per_million"]
    return (numerator+500_000)//1_000_000
def stable_hash(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":")).encode()).hexdigest()
