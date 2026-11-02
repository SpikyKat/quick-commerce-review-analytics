from qcmod.stats import bootstrap_diff, chi2_groups, holm, wilson
from qcmod.themes import hide_star_talk, tag_themes


def test_support_and_refund_are_tagged():
    t = tag_themes("Customer care never replied and my refund is still pending")
    assert t["customer_support_mentioned"] and t["refund_problem"]
    assert not t["wrong_item"]


def test_feel_is_not_a_fee():
    assert not tag_themes("I feel the app is nice")["fees_and_pricing"]
    assert tag_themes("They add a handling fee and a small cart fee")["fees_and_pricing"]


def test_star_talk_removed():
    assert "star" not in hide_star_talk("I give 1 star because it was late")


def test_wilson_contains_rate():
    lo, hi = wilson(30, 100)
    assert lo < 0.3 < hi


def test_chi2_detects_a_real_difference_and_not_a_null_one():
    assert chi2_groups([10, 50], [100, 100])["p"] < 0.001
    assert chi2_groups([50, 51], [100, 100])["p"] > 0.5


def test_holm_is_monotone_and_at_least_raw():
    out = holm({"a": 0.01, "b": 0.02, "c": 0.5})
    assert out["a"] >= 0.01 and out["b"] >= out["a"] and out["c"] >= out["b"]


def test_bootstrap_diff_interval_contains_estimate():
    d, lo, hi = bootstrap_diff([1, 2, 3, 4, 5] * 20, [1, 1, 2, 2, 3] * 20, n_boot=300)
    assert lo < d < hi
