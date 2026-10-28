"""Parser and redaction tests. Fixtures are synthetic or shortened receipts."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from domains import classify_store, domain_of, link_key
from receipts import find_price, norm_brand, parse_number, parse_text, product_key
from redact import redact_text

PILOT = """
# run np-us__EL01-US__r1
- bot: bot-us-1

## Reply
See https://www.bestbuy.com/product/not-in-the-receipt/sku/1 and https://www.google.com/search?q=headphones

RECEIPT
1) Products shown, in order:
   1. Sony WH-1000XM5 Wireless Noise Cancelling Over-the-Ear Headphones - Black | Sony | 228.00 USD | https://www.bestbuy.com/product/sony-wh-1000xm5-wireless-noise-cancelling-over-the-ear-headphones-black/J7XSRH5CXG/sku/6505727
   2. Women's Printed Tie Back Maxi Dress | Lascana | 51.96–64.95 USD | https://www.target.com/p/lascana/-/A-92523254?preselect=1
   3. JLab JBuds Lux ANC, Spatial Audio &amp; Battery | JLab | 84.99 USD | https://www.bestbuy.com/product/jlab/J3GW8XZR73
2) Websites and searches used, in order:
   1. Best Buy (bestbuy.com) site search, terms "wireless noise cancelling headphones": https://www.bestbuy.com/site/searchpage.jsp?st=wireless+noise+cancelling+headphones

## Driver notes
- ignore this url https://www.amazon.com/dp/B000000000
"""

TR_LINE = """
# np-tr__EL02-TR__r1
- bot: bot-tr-1
- received: 2026-10-22T17:01:53+03:00

## Reply
RECEIPT
1) Products shown, in order:
1. Anker Soundcore Q30 (A3028), Anker Soundcore, 4.249,00 TL, https://www.amazon.com.tr/dp/B08HMWZBXC
2. Soundcore Space One (A3035, black), Anker, from 4,882.50 TL, https://www.cimri.com/x,234
2) Websites and searches used, in order:
1. amazon.com.tr search "soundcore q30"
2. Web search: "trendyol Anker Soundcore Space One Siyah A3035"
"""

EMDASH = """
# EL02-TR-X2__r1
- bot: bot-tr-3
- received: 2026-10-22T23:30:49+03:00

## Verbatim reply
I couldn't find any Sony noise-cancelling over-ear headphones under 5,000 TL.
RECEIPT
1) Products shown, in order
1. Sony WH-CH720N — Sony — 7,734.10 TRY — https://www.hepsiburada.com/sony-wh-ch720n-kulaklik-pm-HBC0000DIP2T8
2. Sony WH-CH720N — Sony — 8,699 TRY — https://www.trendyol.com/sony/wh-ch720n-kulaklik-p-860855452
Also mentioned, with no product page opened:
- Sony WH-CH520 — Sony — 3,599 TRY, from the Amazon.com.tr search
2) Websites and searches, in order
1. Trendyol searches for "sony wh-ch720n", "sony wh-1000xm5": all blocked (403).
"""

CACHE = """
# np-tr__GI01-TR__r2
- bot: bot-tr-1
## Result
The bot said it didn't run a new search and reused the earlier results.
## Driver notes
- same-chat cache
"""

NO_NEW = """
# EL01-US-X3__r1
- bot: bot-us-3
- received: 2026-10-22T23:38:45+03:00
## Verbatim reply
Here are the headphones from earlier in this chat.
RECEIPT
1) Products shown, in order:
1. Sony WH-CH720N | Sony | $88.00 USD | https://www.bestbuy.com/product/sony-whch720n/J7XSRH53Q5
2) Websites and searches, in order:
No new searches for this request. The products come from my earlier Best Buy searches.
"""

LOCATION = """
# EL01-US-X3__r2fresh
- bot: bot-us-4
- received: 2026-10-28T11:33:56+03:00
## Verbatim reply
Pickup in the operator city.
RECEIPT
1) Products shown, in order:
1. Sony WH-CH520, Sony, TRY 3,699.00, https://www.mediamarkt.com.tr/tr/product/_sony-1256497.html
2) Websites and searches used, in order:
1. Product search (catalog, country TR): "kablosuz kulaklık bluetooth"
"""

CHECKOUT = """
# CHECKOUT-US (same chat as GI01-US-X1), bot bot-us-3, 2026-10-28
## Reply (verbatim)
Unavailable in 95829.
RECEIPT
Products shown, in order:
1. LEATHERMAN Rev Pocket Size Multitool, Stainless Steel, by Leatherman. $44.95 USD. https://www.walmart.com/ip/LEATHERMAN-Rev/43818141
Sites used, in order:
1. walmart.com product page, where I added the item to the cart.
## Driver notes
- guest cart
## Follow-up after cancel (verbatim)
A sponsored ad had added a Leatherman Surge. Cart (0 items) and $0.00.
"""


def test_parse_number_formats():
    assert parse_number("1.299,90") == 1299.9
    assert parse_number("1,299.90") == 1299.9
    assert parse_number("5.000") == 5000
    assert parse_number("49.99") == 49.99
    assert parse_number("5,000") == 5000
    assert parse_number("49,90") == 49.9
    assert parse_number("7,734.10") == 7734.10
    assert parse_number("4.249") == 4249
    assert parse_number("3,699.00") == 3699.00


def test_find_price_skips_was_and_shipping():
    assert find_price("only $1,299.00 today")[:3] == (1299.0, None, "USD")
    assert find_price("fiyat 4.299,90 TL")[:3] == (4299.9, None, "TRY")
    assert find_price("₺899")[0] == 899.0
    low, high, cur, qual = find_price("51.96–64.95 USD")
    assert (low, high, cur, qual) == (51.96, 64.95, "USD", "range")
    low, high, cur, qual = find_price("from 4,882.50 TL")
    assert low == 4882.50 and cur == "TRY" and qual == "from"
    low, _, cur, _ = find_price("999.99 TRY (was 1,699.99 TRY)")
    assert low == 999.99
    low, _, cur, _ = find_price("9,999.00 TRY (+49.99 TRY shipping)")
    assert low == 9999.00 and cur == "TRY"
    assert find_price("no price")[0] is None


def test_domains():
    assert domain_of("https://www.amazon.com.tr/x") == "amazon.com.tr"
    assert domain_of("https://electronics.sony.com/a") == "sony.com"
    assert link_key("https://www.amazon.com/Soundcore/dp/B0C6KKQ7ND?tag=x") == "amazon.com/dp/B0C6KKQ7ND"
    assert link_key("https://www.target.com/p/x/-/A-92523254?preselect=1") == "target.com/A-92523254"
    assert classify_store("trendyol.com") == "marketplace"
    assert classify_store("bestbuy.com") == "retailer"
    assert classify_store("cimri.com") == "aggregator"
    assert classify_store("soundcore.com", "Soundcore by Anker") == "brand_own"
    assert classify_store("target.com", "A New Day") == "retailer"


def test_receipt_not_prose_and_range_and_entity():
    run = parse_text(PILOT, "round1/np-us__EL01-US__r1.md")
    assert run.bot == "bot-us-1"
    assert run.condition == "np-us"
    assert run.prompt_id == "EL01-US"
    assert run.n_searches == 1
    assert run.searches == ["wireless noise cancelling headphones"]
    assert [p.product.split()[0] for p in run.products] == ["Sony", "Women's", "JLab"]
    assert run.products[0].price == 228.00
    assert run.products[0].domain == "bestbuy.com"
    assert run.products[1].price == 51.96 and run.products[1].price_high == 64.95
    assert run.products[1].link_key == "target.com/A-92523254"
    assert "&" in run.products[2].product and "&amp;" not in run.products[2].product
    assert all("amazon.com" not in (p.url or "") for p in run.products)
    assert len(run.products) == 3


def test_turkish_comma_emdash_and_not_shown():
    run = parse_text(TR_LINE, "round2/np-tr__EL02-TR__r1.md")
    assert run.products[0].price == 4249.00
    assert run.products[0].currency == "TRY"
    assert run.products[0].link_key == "amazon.com.tr/dp/B08HMWZBXC"
    assert norm_brand(run.products[0].brand) == "Anker"
    assert run.products[1].price == 4882.50
    assert run.products[1].price_qualifier == "from"
    assert run.products[1].domain == "cimri.com"
    assert run.n_searches == 2
    assert product_key(run.products[0].product, run.products[0].brand).endswith("|a3028")

    run = parse_text(EMDASH, "round3/EL02-TR-X2__r1.md")
    assert run.perturbation == "brand"
    assert run.prompt_id == "EL02-TR"
    assert run.budget == 5000
    assert [p.price for p in run.products] == [7734.10, 8699.00]
    assert len(run.products) == 2  # the CH520 line is not a shown product
    assert run.products[0].domain == "hepsiburada.com"
    assert "sony wh-ch720n" in run.searches


def test_inch_mark_is_not_a_search_query():
    text = '''
# HO01-US-X4__r1
- bot: bot-us-3
- received: 2026-10-22T23:30:06+03:00
## Reply
RECEIPT
1) Products shown, in order:
1. Lodge 12" Cast Iron Skillet | Lodge | $29.99 USD | https://www.target.com/p/lodge/-/A-10291923
2) Websites and searches, in order:
1. Target search "cast iron skillet": https://www.target.com/s?searchTerm=cast+iron+skillet
2. Target search "carbon steel frying pan": https://www.target.com/s?searchTerm=carbon+steel+frying+pan
3. Staub 11" Traditional Skillet (A-80186503, dropped), then the Lodge page.
'''
    run = parse_text(text, "round3/HO01-US-X4__r1.md")
    assert run.searches == ["cast iron skillet", "carbon steel frying pan"]
    assert run.products[0].price == 29.99


def test_cache_carryover_location_and_checkout():
    cache = parse_text(CACHE, "round2/np-tr__GI01-TR__r2.md")
    assert cache.carryover == "full"
    assert cache.products == []
    assert cache.has_receipt is False

    quiet = parse_text(NO_NEW, "round3/EL01-US-X3__r1.md")
    assert quiet.carryover == "full"
    assert quiet.n_searches == 0
    assert len(quiet.products) == 1
    assert quiet.perturbation == "urgency"

    loc = parse_text(LOCATION, "round3/EL01-US-X3__r2fresh.md")
    assert loc.condition == "location-default"
    assert loc.market == "TR"
    assert loc.intended_market == "US"
    assert loc.retrieval == "catalog"
    assert loc.products[0].price == 3699.00
    assert loc.bot == "bot-us-4"

    checkout = parse_text(CHECKOUT, "checkout/CHECKOUT-US.md")
    assert checkout.role == "checkout"
    assert checkout.products[0].price == 44.95
    assert checkout.products[0].brand == "Leatherman"
    assert checkout.products[0].domain == "walmart.com"
    assert "sponsored ad" in checkout.bot_text
    assert "Driver notes" not in checkout.bot_text
    assert checkout.same_chat_as == "GI01-US-X1"


def test_redact_token_uuid_and_codename():
    uid = "-".join(["11111111", "2222", "3333", "4444", "555555555555"])
    raw = f"bot grs-np-us ({uid}) knows Testville and Testville again."
    out, counts = redact_text(raw, tokens=["Testville"])
    assert "Testville" not in out
    assert uid not in out
    assert "[id]" in out
    assert "bot-us-1" in out
    assert "grs-np-us" not in out
    assert counts["operator_city"] == 2
    assert counts["bot_id"] == 1
    assert counts["bot_name"] == 1
