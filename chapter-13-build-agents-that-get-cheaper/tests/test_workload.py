from src.workload import build,workload_hash,WAVE_COUNTS
def test_240_requests(): assert len(build())==240
def test_four_waves_60_each():
    w=build()
    assert {i:sum(r.wave==i for r in w) for i in range(1,5)}=={1:60,2:60,3:60,4:60}
def test_late_families():
    w=build()
    assert not any(r.family=="returns" for r in w if r.wave==1)
    assert not any(r.family=="capacity" for r in w if r.wave<4)
def test_drift_only_wave3_plus():
    w=build()
    for r in w:
        if r.family in {"invoice","supplier","order"}:
            assert r.version==("v2" if r.wave>=3 else "v1")
def test_hash_deterministic(): assert workload_hash(build())==workload_hash(build())
