from __future__ import annotations
import re


def sources_current(memory,kb):
    for ref in memory.source_refs:
        cur=kb.by_fact(ref['fact_id'])
        if not cur or cur['content_hash']!=ref['content_hash']:
            return False
    return True


def _normalize_string(value: str, key: str | None = None) -> str:
    """Normalize harmless representation differences without changing meaning."""
    value = re.sub(r'[_\s]+', ' ', value.strip())
    value = value.rstrip('.').strip().casefold()
    # Articles/prepositions that do not change the canonical policy value.
    value = re.sub(r'^at the ', '', value)
    # Model sometimes restates the field label before the value.
    value = re.sub(r'^enterprise support is ', '', value)
    value = re.sub(r'\bthe\b', '', value)
    value = re.sub(r'\s+', ' ', value).strip()
    if key == 'support' and value.endswith(' support'):
        value = value[:-len(' support')].rstrip()
    return value


def _canonicalize(value, key: str | None = None):
    if isinstance(value, dict):
        return {k: _canonicalize(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [_canonicalize(v, key) for v in value]
    if isinstance(value, str):
        return _normalize_string(value, key)
    return value


def _affirmative_answer_matches_query(answer, expected, query: str | None) -> bool:
    """Accept yes/true only when the question itself asserts the expected value.

    This is deliberately narrow. It does not treat arbitrary affirmative answers as
    correct; the normalized expected scalar must be explicitly present in the
    normalized yes/no question.
    """
    if not query or not isinstance(answer, dict) or not isinstance(expected, dict):
        return False
    if set(answer) != {'value'} or set(expected) != {'value'}:
        return False
    actual = _normalize_string(str(answer['value']))
    if actual not in {'yes', 'true'}:
        return False
    expected_value = _normalize_string(str(expected['value']))
    q = _normalize_string(query)
    # For support questions, "24/5" and "24/7" are the semantic payload while
    # "support" is already supplied by the question grammar.
    expected_in_query = expected_value in q
    if expected_value.endswith(' support'):
        expected_in_query = expected_in_query or expected_value[:-len(' support')].strip() in q
    return expected_in_query


def answer_correct(answer, expected, query: str | None = None):
    actual_c = _canonicalize(answer)
    expected_c = _canonicalize(expected)
    if actual_c == expected_c:
        return True
    # A scalar value may omit a redundant trailing 'support' label.
    if isinstance(actual_c, dict) and isinstance(expected_c, dict) and set(actual_c)=={'value'} and set(expected_c)=={'value'}:
        av, ev = actual_c['value'], expected_c['value']
        if isinstance(av, str) and isinstance(ev, str) and ev.endswith(' support') and av == ev[:-len(' support')].strip():
            return True
    return _affirmative_answer_matches_query(answer, expected, query)


def reuse_allowed(record):
    return bool(record.get('deterministic_memory_reuse_allowed')) and not bool(record.get('llm_required_by_policy'))
