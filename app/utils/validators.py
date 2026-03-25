from urllib.parse import urlparse


def validate_supported_product_url(url: str) -> bool:
    netloc = urlparse(url).netloc.lower()
    return "amazon." in netloc or "flipkart." in netloc
