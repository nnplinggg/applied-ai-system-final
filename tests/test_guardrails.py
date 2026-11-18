from src.guardrails import compute_confidence, validate_query


def test_rejects_empty_and_whitespace():
    assert not validate_query("").ok
    assert not validate_query("   \n").ok


def test_rejects_too_long():
    assert not validate_query("a " * 400).ok


def test_rejects_non_text():
    assert not validate_query("!!! ??? 12345").ok
    assert not validate_query(None).ok


def test_accepts_normal_query_and_strips():
    r = validate_query("  chill study music  ")
    assert r.ok and r.cleaned == "chill study music"


def test_confidence_bounds_and_monotonic():
    lo = compute_confidence(top_ratio=0.3, margin=0.0, similarity=0.05)
    hi = compute_confidence(top_ratio=0.95, margin=0.2, similarity=0.5)
    assert 0.0 <= lo < hi <= 1.0
