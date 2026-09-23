def validate_result(rows):
    return {'ok':isinstance(rows,list) and all(isinstance(r,dict) for r in rows),'row_count':len(rows) if isinstance(rows,list) else 0}
