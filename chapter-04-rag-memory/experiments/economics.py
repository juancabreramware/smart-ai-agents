def economics(base,smart):
    b=base['total_cost_usd'];s=smart['total_cost_usd']; saving=b-s
    avg=b/base['executions'] if base['executions'] else 0
    acq=None
    return {'baseline_total_usd':b,'smart_total_usd':s,'cumulative_savings_usd':saving,'cost_reduction_pct':(saving/b*100 if b else 0),'baseline_avg_cost_per_execution':avg}
