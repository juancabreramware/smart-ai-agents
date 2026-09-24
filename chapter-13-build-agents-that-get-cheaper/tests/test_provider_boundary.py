from pathlib import Path
def test_openai_provider_has_no_ground_truth_reference():
    s=Path("src/provider.py").read_text(encoding="utf-8")
    openai=s.split("class OpenAIProvider:",1)[1]
    assert "ground_truth" not in openai
def test_openai_provider_uses_current_public_contract():
    s=Path("src/provider.py").read_text(encoding="utf-8")
    openai=s.split("class OpenAIProvider:",1)[1]
    assert "public_contract(r.family,r.version)" in openai
def test_no_eval_exec():
    for p in Path("src").glob("*.py"):
        s=p.read_text(encoding="utf-8")
        assert "eval(" not in s
        assert "exec(" not in s
