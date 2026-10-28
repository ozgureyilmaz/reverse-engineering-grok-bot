"""Merchant class, query style, and product identity for v2.

v1 store types are preserved on each row as v1_store_type. v2 merchant classes
split price-comparison hosts from editorial hosts, and code Walmart and Getir
as retailers. That is a coding rule, not a finding about who owns the inventory.
A Walmart page can still be a marketplace offer; the receipt and the page, not
this function, say who sold it.
"""
from __future__ import annotations

import re
import sys

from .paths import V1_CODE

if str(V1_CODE) not in sys.path:
    sys.path.insert(0, str(V1_CODE))

from domains import classify_store, domain_of  # noqa: E402
from receipts import _MODEL, norm_brand, product_key  # noqa: E402

# Hosts whose pages compare sellers. Not retailers.
PRICE_COMPARISON = {
    "cimri.com",
    "akakce.com",
    "epey.com",
}
# Hosts that publish reviews or roundups. A product URL on one of these is
# editorial. Most editorial names in the corpus appear inside quoted queries,
# not as the product URL.
EDITORIAL = {
    "wirecutter.com",
    "nytimes.com",
    "rtings.com",
    "reddit.com",
    "soundguys.com",
    "seriouseats.com",
    "theverge.com",
    "tomsguide.com",
}
# Recodes relative to v1's MARKETPLACES set. Both hosts also carry third-party
# stock. v2's retailer class means "named retail chain", which is the contrast
# this study can actually see. v1_store_type keeps the old code.
RETAILER_RECODES = {
    "walmart.com": "v1 coded walmart.com as marketplace; v2 codes the chain as retailer",
    "getir.com": "v1 coded getir.com as marketplace; v2 codes the chain as retailer",
}

# Brands named in v1 queries or product rows. A query that uses a brand outside
# this list is coded generic. That is a false-negative risk, stated in the
# methodology. Matching is case-insensitive and on word boundaries.
BRAND_LEXICON = (
    "sony", "anker", "soundcore", "jbl", "bose", "apple", "sennheiser", "beats",
    "jlab", "philips", "tefal", "t-fal", "karaca", "lava", "quince", "yeti",
    "leatherman", "thermopro", "xiaomi", "edifier", "samsung", "ugreen",
    "baseus", "koton", "ipekyol", "beymen", "mavi", "lavazza", "starbucks",
    "illy", "lodge", "greenpan", "figmint", "casio", "huawei", "arzum",
    "kronotrop", "petra", "shokz", "earfun", "oxo", "all-clad", "allclad",
    "stumptown", "a new day", "lc waikiki", "lcw", "abercrombie", "gap",
    "storyworth", "biolite", "us polo", "network", "montag", "counter culture",
    "kicking horse", "sennheiser",
)

_EDITORIAL_QUERY = re.compile(
    r"(?i)\b(best|review|reviews|wirecutter|rtings|soundguys|serious eats|"
    r"well reviewed|en iyi|roundup|buyer's guide|buyers guide)\b"
)
_BRAND_PATTERNS = [
    (name, re.compile(rf"(?i)(?<![a-z0-9]){re.escape(name)}(?![a-z0-9])"))
    for name in sorted(set(BRAND_LEXICON), key=len, reverse=True)
]


def merchant_class(domain: str, brand: str = "") -> str:
    """One of retailer, marketplace, brand_site, editorial, price_comparison, unknown."""
    d = (domain or "").lower()
    if not d:
        return "unknown"
    if d in PRICE_COMPARISON or any(d.endswith("." + host) for host in PRICE_COMPARISON):
        return "price_comparison"
    if d in EDITORIAL or any(d.endswith("." + host) for host in EDITORIAL):
        return "editorial"
    if d in RETAILER_RECODES:
        return "retailer"
    v1 = classify_store(d, brand)
    if v1 == "brand_own":
        return "brand_site"
    if v1 == "marketplace":
        return "marketplace"
    if v1 == "retailer":
        return "retailer"
    if v1 == "aggregator":
        return "unknown"
    return "unknown"


def v1_store_type(domain: str, brand: str = "") -> str:
    return classify_store(domain or "", brand or "")


def query_flags(query: str) -> dict[str, bool]:
    text = query or ""
    return {
        "editorial": bool(_EDITORIAL_QUERY.search(text)),
        "model": bool(_MODEL.search(text)),
        "brand": any(pattern.search(text) for _, pattern in _BRAND_PATTERNS),
    }


def query_style(query: str) -> str:
    """Primary class. Priority matches v1: editorial, then model, then brand, else generic."""
    flags = query_flags(query)
    if flags["editorial"]:
        return "editorial"
    if flags["model"]:
        return "model"
    if flags["brand"]:
        return "brand"
    return "generic"


def model_token(name: str) -> str:
    found = _MODEL.findall(name or "")
    if not found:
        return ""
    tokens = [re.sub(r"[^a-z0-9]", "", item.lower()) for item in found]
    return max(tokens, key=len) if tokens else ""


def brand_canonical(brand: str, name: str = "") -> str:
    """Fold aliases via the v1 map, then a lexicon hit at the start of the name."""
    folded = norm_brand(brand)
    if folded:
        return folded
    text = name or ""
    for lexicon_name, pattern in _BRAND_PATTERNS:
        if pattern.search(text):
            return norm_brand(lexicon_name) or lexicon_name
    return ""


def product_identity(name: str, brand: str) -> dict[str, str]:
    """Canonical brand, model token, and a product id.

    identity_strength is 'model' only when a model code was extracted. Weaker
    text keys are kept for description and are not used as within-product matches.
    """
    canonical = brand_canonical(brand, name)
    model = model_token(f"{brand or ''} {name or ''}")
    if model and canonical:
        product_id = f"{canonical.casefold()}|{model}"
        strength = "model"
    elif model:
        product_id = f"unknown|{model}"
        strength = "model"
    else:
        product_id = product_key(name, brand)
        strength = "text"
    return {
        "brand_canonical": canonical,
        "model": model,
        "product_id": product_id,
        "identity_strength": strength,
        "v1_product_key": product_key(name, brand),
    }


def host_of(url: str) -> str:
    return domain_of(url or "")
