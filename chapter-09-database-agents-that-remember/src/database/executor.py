from __future__ import annotations
import re,sqlite3,time
PROHIBITED=re.compile(r'\b(insert|update|delete|drop|alter|create|attach|detach|pragma|replace|vacuum)\b',re.I)
def validate_sql(sql):
    s=sql.strip()
    if not s.lower().startswith('select'): return {'ok':False,'reason':'read_only_select_required'}
    if ';' in s.rstrip(';'): return {'ok':False,'reason':'multi_statement'}
    if PROHIBITED.search(s): return {'ok':False,'reason':'prohibited_construct'}
    return {'ok':True}
def execute(db_path,sql,params):
    chk=validate_sql(sql)
    if not chk['ok']: raise ValueError(chk['reason'])
    t=time.perf_counter(); c=sqlite3.connect(db_path); c.row_factory=sqlite3.Row
    try: rows=[dict(r) for r in c.execute(sql,params).fetchall()]
    finally: c.close()
    return rows,(time.perf_counter()-t)*1000
