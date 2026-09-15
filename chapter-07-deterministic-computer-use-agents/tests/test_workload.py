from smart_agents_ch7.benchmark.workload import build_benchmark, build_demo, AFFECTED_V2


def test_benchmark_shape_is_frozen():
    rows = build_benchmark()
    assert len(rows) == 150
    assert rows[0].request_id == "CH7-001"
    assert rows[-1].request_id == "CH7-150"
    assert sum(r.phase == "A" for r in rows) == 60
    assert sum(r.phase == "B" for r in rows) == 30
    assert sum(r.phase == "C" for r in rows) == 60
    assert sum(r.reasoning_required for r in rows) == 18
    assert sum(r.v2_affected for r in rows) == 32
    assert all(r.ui_version == "V1" for r in rows[:90])
    assert all(r.ui_version == "V2" for r in rows[90:])


def test_demo_shape():
    rows = build_demo()
    assert len(rows) == 15
    assert rows[0].ui_version == "V1"
    assert rows[-1].ui_version == "V2"
