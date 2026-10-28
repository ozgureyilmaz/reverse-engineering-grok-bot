"""Unit tests for the v2 statistics, classifier, schedule, and page parser."""
from __future__ import annotations

import csv
from pathlib import Path

from grokstudy.classify import merchant_class, product_identity, query_style
from grokstudy.power import n_for_difference, n_for_proportion
from grokstudy.schedule import build_tier, load_prereg, tier_sizes, write_schedule
from grokstudy.statsutil import (
    benjamini_hochberg,
    hhi,
    holm,
    kendall_tau_a,
    rbo,
    wilson_interval,
)
from grokstudy.verify import _public_host, parse_page

ROOT = Path(__file__).resolve().parents[2]


def test_wilson_published_example():
    interval = wilson_interval(81, 100)
    assert abs(interval["low"] - 0.722) < 0.01
    assert abs(interval["high"] - 0.875) < 0.01
    assert interval["low"] <= 0.81 <= interval["high"]


def test_wilson_empty():
    assert wilson_interval(0, 0)["p"] is None


def test_holm_and_bh():
    holm_rows = holm([("a", 0.01), ("b", 0.04), ("c", 0.03)])
    by = {row["name"]: row["p_holm"] for row in holm_rows}
    assert abs(by["a"] - 0.03) < 1e-12
    assert abs(by["c"] - 0.06) < 1e-12
    assert abs(by["b"] - 0.06) < 1e-12
    bh = {row["name"]: row["p_bh"] for row in benjamini_hochberg([("a", 0.01), ("b", 0.04), ("c", 0.03)])}
    assert bh["a"] <= bh["c"] <= bh["b"]
    assert bh["b"] <= 1


def test_rbo_and_kendall():
    assert rbo(["a", "b"], ["a", "b"]) == 1
    assert rbo(["a"], ["b"]) == 0
    assert abs(rbo(["a", "b"], ["b", "a"], 0.9) - 0.9) < 1e-9
    forward = kendall_tau_a({"a": 0, "b": 1}, {"a": 0, "b": 1})
    backward = kendall_tau_a({"a": 0, "b": 1}, {"a": 1, "b": 0})
    assert forward["tau_a"] == 1
    assert backward["tau_a"] == -1
    assert kendall_tau_a({"a": 0}, {"a": 0})["defined"] is False


def test_hhi_and_sample_size():
    assert hhi(["a", "a"]) == 1
    assert hhi(["a", "b"]) == 0.5
    assert n_for_proportion(0.15) == 43
    assert n_for_proportion(0.20) == 25
    assert n_for_proportion(0.25) == 16
    assert n_for_proportion(0.35) == 8
    assert n_for_difference(0.30) == 36


def test_merchant_and_query_and_identity():
    assert merchant_class("bestbuy.com") == "retailer"
    assert merchant_class("walmart.com") == "retailer"
    assert merchant_class("getir.com") == "retailer"
    assert merchant_class("amazon.com.tr") == "marketplace"
    assert merchant_class("cimri.com") == "price_comparison"
    assert merchant_class("rtings.com") == "editorial"
    assert merchant_class("sony.com", "Sony") == "brand_site"
    assert query_style("best headphones 2026 RTINGS Wirecutter") == "editorial"
    assert query_style("sony wh-ch720n") == "model"
    assert query_style("wireless noise cancelling headphones") == "generic"
    assert query_style("tefal frying pan") == "brand"
    identity = product_identity("Sony WH-CH720N", "Sony")
    assert identity["identity_strength"] == "model"
    assert identity["product_id"] == "sony|whch720n"
    assert product_identity("Space One", "Soundcore by Anker")["brand_canonical"] == "Anker"


def test_schedule_is_deterministic_and_balanced(tmp_path):
    cfg = load_prereg()
    first = build_tier(cfg, "mve")
    second = build_tier(cfg, "mve")
    assert [row["run_id"] for row in first] == [row["run_id"] for row in second]
    assert [row["bot_slot"] for row in first] == [row["bot_slot"] for row in second]
    sizes = tier_sizes(cfg)
    assert len(first) == sizes["mve"]["primary"] * 2 + sizes["mve"]["secondary"] * 2 * 6 + sizes["mve"]["probe"] * 2 * 4
    assert len(build_tier(cfg, "full")) == 434
    suffix = cfg["receipt_suffix"].strip()
    assert all(row["prompt_text"].endswith(suffix) for row in first)
    assert {row["market"] for row in first[:20]} == {"US", "TR"}
    e01 = [row for row in first if row["experiment_id"] == "E01"]
    blocks = {row["time_block"] for row in e01}
    assert blocks == set(cfg["time_blocks"])
    dates = {row["date_stratum"] for row in e01}
    assert dates == set(cfg["date_strata"])
    summary = write_schedule(cfg, tmp_path)
    assert summary["status"] == "UNEXECUTED"
    assert summary["schedule_rows"]["mve"] == len(first)


def test_parse_page_jsonld_and_private_host():
    html = """
    <html><head><title>Example headphone</title>
    <script type="application/ld+json">
    {"@type":"Product","name":"WH-CH720N","offers":{"@type":"Offer","price":"88.00","priceCurrency":"USD","availability":"https://schema.org/InStock"}}
    </script></head><body><p>In stock.</p></body></html>
    """
    parsed = parse_page(html.encode(), "text/html")
    assert parsed["price"] == 88.0
    assert parsed["currency"] == "USD"
    assert parsed["availability"] == "InStock"
    assert parsed["sponsored_label"] is None
    ok, why = _public_host("127.0.0.1")
    assert ok is False
    assert "non_public" in why


def test_v1_files_unchanged_and_reparse_matches_csv():
    from grokstudy.normalize import corpus_tables
    _runs, products, _queries = corpus_tables()
    shopping = [row for row in products if row["role"] == "shopping"]
    saved = list(csv.DictReader((ROOT / "data" / "records.csv").open(encoding="utf-8")))
    saved_shopping = [row for row in saved if row["role"] == "shopping"]
    assert len(shopping) == len(saved_shopping) == 228
    assert [row["url"] for row in shopping] == [row["url"] for row in saved_shopping]
