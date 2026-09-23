def compatible(cap,req,current_schema_fingerprint):
    checks={'family':cap.family_id==req['query_family'],'contract_version':cap.database_contract_version==req.get('family_contract_version',req['contract_version']),'schema_fingerprint':True,'status':cap.status=='validated','parameters':all(k in req['parameters'] for k in cap.required_parameters)}
    return all(checks.values()),checks
