import re
from urllib.parse import urlparse, urlunparse, parse_qs


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = "https"
    netloc = parsed.netloc.lower().replace("www.", "")
    path = re.sub(r"/+$", "", parsed.path)
    if "amazon." in netloc:
        path_match = re.search(r"/(dp|gp/product)/([A-Z0-9]{10})", path, re.IGNORECASE)
        if path_match:
            path = f"/dp/{path_match.group(2).upper()}"
    if "flipkart." in netloc:
        query = parse_qs(parsed.query)
        pid = query.get("pid", [""])[0]
        if pid:
            return urlunparse((scheme, netloc, path, "", f"pid={pid}", ""))
    return urlunparse((scheme, netloc, path, "", "", ""))


def detect_source_site(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    if "amazon." in netloc:
        return "amazon"
    if "flipkart." in netloc:
        return "flipkart"
    return "unknown"


def normalize_title(title: str) -> str:
    title = title.lower().strip()
    title = re.sub(r"[^a-z0-9\s]", " ", title)
    title = re.sub(r"\s+", " ", title)
    return title


def parse_price_to_float(raw_price: str):
    if raw_price is None:
        return None
    cleaned = re.sub(r"[^0-9.,]", "", raw_price)
    cleaned = cleaned.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None
