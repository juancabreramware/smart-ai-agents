import hashlib,sqlite3,json
def schema_fingerprint(db_path):
    c=sqlite3.connect(db_path); rows=c.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name").fetchall(); c.close()
    return hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()
