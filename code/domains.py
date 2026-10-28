"""Domain helpers for retailer URLs in saved shopping replies."""
from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

MARKETPLACES = {
    "amazon.com", "amazon.com.tr", "amazon.de", "amazon.co.uk", "trendyol.com",
    "hepsiburada.com", "n11.com", "ebay.com", "etsy.com", "walmart.com",
    "aliexpress.com", "temu.com", "pazarama.com", "pttavm.com", "idefix.com",
    "getir.com", "yemeksepeti.com", "ciceksepeti.com",
}
RETAILERS = {
    "bestbuy.com", "target.com", "costco.com", "mediamarkt.com.tr", "teknosa.com",
    "vatanbilgisayar.com", "rei.com", "bloomingdales.com", "nordstrom.com",
    "macys.com", "kitchenshop.eu",
}
AGGREGATORS = {
    "cimri.com", "akakce.com", "epey.com", "google.com", "shopping.google.com",
    "wirecutter.com", "nytimes.com", "rtings.com", "reddit.com",
}
# Direct-to-consumer hosts seen in the receipts. brand_own is also inferred
# when the brand name and the host match.
BRAND_SITES = {
    "apple.com", "sony.com", "soundcore.com", "shokz.com", "quince.com",
    "abercrombie.com", "gapfactory.com", "leatherman.com", "oxo.com",
    "all-clad.com", "lodgecastiron.com", "stumptowncoffee.com",
    "counterculturecoffee.com", "kickinghorsecoffee.com", "myearfun.com",
    "koton.com", "lcw.com", "ipekyol.com.tr", "beymen.com", "mavi.com",
    "network.com.tr", "uspoloassn.com", "petracoffee.com", "kronotrop.com.tr",
    "coffeedepartment.co", "montagcoffee.com", "tefal.com.tr", "karaca.com",
    "sennheiser-hearing.com.tr", "galenleather.com.tr", "novavera.com.tr",
    "bioliteenergy.com", "flybyjing.com", "storyworth.com", "arcelik.com.tr",
}

_MULTI_TLDS = ("com.tr", "co.uk", "com.au", "co.jp", "com.br", "org.tr", "gen.tr")
_ASIN = re.compile(r"/(?:dp|gp/product)/([A-Z0-9]{10})(?=[/?#]|$)", re.I)
_TARGET_ID = re.compile(r"/A-(\d+)", re.I)


def domain_of(url: str) -> str:
    """Registrable-ish host, lowercased, without www."""
    if not url:
        return ""
    if "://" not in url:
        url = "https://" + url
    host = (urlsplit(url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host.startswith("www2."):
        host = host[5:]
    parts = host.split(".")
    if len(parts) <= 2:
        return host
    for tld in _MULTI_TLDS:
        if host.endswith("." + tld):
            return ".".join(parts[-3:])
    if host.startswith("shopping.google."):
        return host
    # electronics.sony.com, us.soundcore.com, tr.uspoloassn.com, shop.mango.com
    return ".".join(parts[-2:])


def canonical_url(url: str) -> str:
    """Drop scheme, www, query and fragment so tracking params do not split one listing."""
    if not url:
        return ""
    if "://" not in url:
        url = "https://" + url
    parts = urlsplit(url)
    host = (parts.hostname or "").lower().removeprefix("www.")
    path = re.sub(r"/+$", "", parts.path or "")
    return urlunsplit(("", host, path, "", "")).lstrip("/")


def link_key(url: str) -> str:
    """A listing identity. Amazon ASINs and Target A-ids ignore path decoration."""
    if not url:
        return ""
    dom = domain_of(url)
    asin = _ASIN.search(url)
    if asin and dom.startswith("amazon."):
        return f"{dom}/dp/{asin.group(1).upper()}"
    if dom == "target.com":
        tid = _TARGET_ID.search(url)
        if tid:
            return f"target.com/A-{tid.group(1)}"
    return canonical_url(url)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def classify_store(domain: str, brand: str = "") -> str:
    d = (domain or "").lower()
    if not d:
        return "unknown"
    if d in MARKETPLACES or any(d.endswith("." + m) for m in MARKETPLACES):
        return "marketplace"
    if d in RETAILERS:
        return "retailer"
    if d in AGGREGATORS or d.startswith("google."):
        return "aggregator"
    host = d.split(".")[0]
    blob = _slug(brand)
    if host and blob and len(host) >= 4 and (host in blob or (len(blob) >= 4 and blob in host)):
        return "brand_own"
    if d in BRAND_SITES:
        return "brand_own"
    return "unknown"
