from src.provider import MockProvider
from src.architectures import StatelessReason,EpisodicReuse,CompoundingSmart
from src.workload import build
def _run(a):
    last=None; routes=[]
    for r in build():
        if r.wave!=last: a.on_wave_start(r.wave); last=r.wave
        routes.append(a.handle(r)[2])
    return routes
def test_stateless_calls_every_time():
    a=StatelessReason(MockProvider()); routes=_run(a); assert routes==["reason_every_time"]*240
def test_episodic_resets_each_later_wave():
    a=EpisodicReuse(MockProvider()); _run(a)
    assert {e["wave"] for e in a.events if e["event"]=="RESET"}=={2,3,4}
def test_compounding_never_resets():
    a=CompoundingSmart(MockProvider()); _run(a)
    assert not any(e["event"]=="RESET" for e in a.events)
def test_compounding_reuses():
    a=CompoundingSmart(MockProvider()); routes=_run(a)
    assert "deterministic_reuse" in routes
def test_compounding_invalidates_drifted_families():
    a=CompoundingSmart(MockProvider()); _run(a)
    for fam in ["invoice","supplier","order"]:
        assert any(e["event"]=="INVALIDATE" and e["family"]==fam for e in a.events)
