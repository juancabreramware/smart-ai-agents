from src.runner import run
def test_mock_end_to_end(tmp_path):
    m,s,o=run("mock","canonical",tmp_path)
    assert m["request_count"]==180
    assert set(s)=={"always_reason","always_optimize","smart"}
    assert s["always_reason"]["requests"]==180
    assert s["always_reason"]["llm_calls"]==180
    assert s["smart"]["stale_reuse_errors"]==0
    assert (tmp_path/"optimization_cases.jsonl").exists()
def test_smart_does_not_optimize_ambiguous(tmp_path):
    _,_,_=run("mock","canonical",tmp_path)
    import json
    rows=[json.loads(x) for x in (tmp_path/"smart_ledger.jsonl").read_text().splitlines()]
    amb=[r for r in rows if r["family"]=="ambiguous_judgment"]
    assert all(r["route"]=="reason" for r in amb)
