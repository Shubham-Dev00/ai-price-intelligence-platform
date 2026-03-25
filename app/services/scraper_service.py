from dataclasses import dataclass
import json
import re
import time
import requests
from bs4 import BeautifulSoup
from flask import current_app
from app.utils.helpers import detect_source_site, parse_price_to_float
from app.utils.validators import validate_supported_product_url


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


@dataclass
class ScrapeResult:
    success: bool
    source_site: str
    title: str | None = None
    current_price: float | None = None
    availability: str | None = None
    currency: str = "INR"
    parser_used: str | None = None
    http_status: int | None = None
    error_message: str | None = None
    metadata: dict | None = None
    is_suspicious: bool = False


class BaseSiteParser:
    parser_name = "base"

    def parse(self, html: str, url: str) -> ScrapeResult:
        raise NotImplementedError


class AmazonParser(BaseSiteParser):
    parser_name = "amazon_bs4"

    def parse(self, html: str, url: str) -> ScrapeResult:
        soup = BeautifulSoup(html, "html.parser")
        lower_html = html.lower()

        blocked_markers = [
            "captcha",
            "enter the characters you see below",
            "sorry, we just need to make sure you're not a robot",
            "robot check",
        ]
        if any(marker in lower_html for marker in blocked_markers):
            return ScrapeResult(
                success=False,
                source_site="amazon",
                parser_used=self.parser_name,
                error_message="Amazon returned a blocked/anti-bot page.",
                metadata={"blocked": True},
                is_suspicious=True,
            )

        title = None
        title_selectors = [
            "#productTitle",
            "span#productTitle",
            'meta[property="og:title"]',
            "h1 span",
            "title",
        ]
        for selector in title_selectors:
            node = soup.select_one(selector)
            if node:
                if node.name == "meta":
                    title = (node.get("content") or "").strip()
                else:
                    title = node.get_text(strip=True)
                if title:
                    break

        price = None
        meta_price = soup.select_one('meta[property="product:price:amount"]')
        if meta_price and meta_price.get("content"):
            price = parse_price_to_float(meta_price.get("content"))

        if price is None:
            price_selectors = [
                ".a-price .a-offscreen",
                "#priceblock_ourprice",
                "#priceblock_dealprice",
                "#priceblock_saleprice",
                "#corePrice_feature_div .a-price .a-offscreen",
                "#tp_price_block_total_price_ww .a-offscreen",
                "span.a-price-whole",
            ]
            for selector in price_selectors:
                node = soup.select_one(selector)
                if node:
                    text = node.get_text(strip=True)
                    if selector == "span.a-price-whole":
                        frac = soup.select_one("span.a-price-fraction")
                        if frac:
                            text = f"{text}.{frac.get_text(strip=True)}"
                    price = parse_price_to_float(text)
                    if price is not None:
                        break

        if price is None:
            for script in soup.select('script[type="application/ld+json"]'):
                raw = script.string or script.get_text(strip=True)
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                except Exception:
                    continue
                candidates = data if isinstance(data, list) else [data]
                for item in candidates:
                    if not isinstance(item, dict):
                        continue
                    if not title and item.get("name"):
                        title = item.get("name")
                    offers = item.get("offers")
                    if isinstance(offers, dict):
                        offer_price = offers.get("price")
                        if offer_price is not None:
                            price = parse_price_to_float(str(offer_price))
                            if price is not None:
                                break
                    elif isinstance(offers, list):
                        for offer in offers:
                            if isinstance(offer, dict) and offer.get("price") is not None:
                                price = parse_price_to_float(str(offer.get("price")))
                                if price is not None:
                                    break
                        if price is not None:
                            break
                if price is not None:
                    break

        if price is None:
            regex_patterns = [
                r'"priceAmount"\s*:\s*"?(₹?[\d,]+(?:\.\d+)?)"?',
                r'"price"\s*:\s*"?(₹?[\d,]+(?:\.\d+)?)"?',
                r'"displayPrice"\s*:\s*"?(₹?[\d,]+(?:\.\d+)?)"?',
            ]
            for pattern in regex_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    price = parse_price_to_float(match.group(1))
                    if price is not None:
                        break

        availability_node = soup.select_one("#availability span")
        availability = availability_node.get_text(strip=True) if availability_node else "Unknown"
        if price is not None and availability == "Unknown":
            availability = "In Stock"

        if not title or price is None:
            return ScrapeResult(
                success=False,
                source_site="amazon",
                parser_used=self.parser_name,
                error_message="Failed to parse Amazon product page safely.",
                metadata={
                    "has_title": bool(title),
                    "has_price": price is not None,
                },
            )
        return ScrapeResult(
            success=True,
            source_site="amazon",
            title=title,
            current_price=price,
            availability=availability,
            parser_used=self.parser_name,
            metadata={"soup_title_found": bool(title)},
        )


class FlipkartParser(BaseSiteParser):
    parser_name = "flipkart_bs4"

    def parse(self, html: str, url: str) -> ScrapeResult:
        soup = BeautifulSoup(html, "html.parser")
        lower_html = html.lower()

        blocked_markers = [
            "captcha",
            "access denied",
            "robot",
            "request blocked",
            "sorry, you have been blocked",
        ]
        if any(marker in lower_html for marker in blocked_markers):
            return ScrapeResult(
                success=False,
                source_site="flipkart",
                parser_used=self.parser_name,
                error_message="Flipkart returned a blocked/anti-bot page.",
                metadata={"blocked": True},
                is_suspicious=True,
            )

        title = None
        title_selectors = [
            "span.B_NuCI",
            "h1._6EBuvT span",
            "h1.yhB1nd span",
            "h1",
            'meta[property="og:title"]',
        ]
        for selector in title_selectors:
            node = soup.select_one(selector)
            if node:
                if node.name == "meta":
                    title = (node.get("content") or "").strip()
                else:
                    title = node.get_text(strip=True)
                if title:
                    break

        if not title and soup.title:
            title = soup.title.get_text(strip=True)

        price = None
        meta_price = soup.select_one('meta[property="product:price:amount"]')
        if meta_price and meta_price.get("content"):
            price = parse_price_to_float(meta_price.get("content"))

        if price is None:
            price_selectors = [
                "div._30jeq3",
                "div.Nx9bqj.CxhGGd",
                "div._25b18c ._30jeq3",
                "div.Nx9bqj",
                'div[class*="Nx9bqj"]',
                'div[class*="_30jeq3"]',
            ]
            for selector in price_selectors:
                node = soup.select_one(selector)
                if node:
                    price = parse_price_to_float(node.get_text(strip=True))
                    if price is not None:
                        break

        if price is None:
            for script in soup.select('script[type="application/ld+json"]'):
                raw = script.string or script.get_text(strip=True)
                if not raw:
                    continue
                try:
                    data = json.loads(raw)
                except Exception:
                    continue

                candidates = data if isinstance(data, list) else [data]
                for item in candidates:
                    if not isinstance(item, dict):
                        continue
                    if not title and item.get("name"):
                        title = item.get("name")
                    offers = item.get("offers")
                    if isinstance(offers, dict):
                        offer_price = offers.get("price")
                        if offer_price is not None:
                            price = parse_price_to_float(str(offer_price))
                            if price is not None:
                                break
                    elif isinstance(offers, list):
                        for offer in offers:
                            if isinstance(offer, dict) and offer.get("price") is not None:
                                price = parse_price_to_float(str(offer.get("price")))
                                if price is not None:
                                    break
                        if price is not None:
                            break
                if price is not None:
                    break

        if price is None:
            regex_patterns = [
                r'"sellingPrice"\s*:\s*"?₹?([\d,]+(?:\.\d+)?)"?',
                r'"finalPrice"\s*:\s*"?₹?([\d,]+(?:\.\d+)?)"?',
                r'"price"\s*:\s*"?₹?([\d,]+(?:\.\d+)?)"?',
            ]
            for pattern in regex_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    price = parse_price_to_float(match.group(1))
                    if price is not None:
                        break

        availability = "Unknown"
        if soup.find(string=lambda s: s and "out of stock" in s.lower()):
            availability = "Out of Stock"
        elif price is not None:
            availability = "In Stock"

        if not title or price is None:
            return ScrapeResult(
                success=False,
                source_site="flipkart",
                parser_used=self.parser_name,
                error_message="Failed to parse Flipkart product page safely.",
                metadata={
                    "has_title": bool(title),
                    "has_price": price is not None,
                },
            )
        return ScrapeResult(
            success=True,
            source_site="flipkart",
            title=title,
            current_price=price,
            availability=availability,
            parser_used=self.parser_name,
        )


class ScraperService:
    PARSERS = {
        "amazon": AmazonParser(),
        "flipkart": FlipkartParser(),
    }

    @staticmethod
    def scrape_product(url: str) -> ScrapeResult:
        if not validate_supported_product_url(url):
            return ScrapeResult(
                success=False,
                source_site=detect_source_site(url),
                error_message="Only Amazon and Flipkart product URLs are supported.",
            )

        source_site = detect_source_site(url)
        parser = ScraperService.PARSERS.get(source_site)
        headers = {
            "User-Agent": USER_AGENT,
            "Accept-Language": "en-IN,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        }
        retry_count = current_app.config.get("SCRAPER_RETRY_COUNT", 2)
        timeout = current_app.config.get("SCRAPER_TIMEOUT_SECONDS", 12)

        for attempt in range(retry_count + 1):
            try:
                response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
                html = response.text
                result = parser.parse(html, url)
                result.http_status = response.status_code
                if result.success and result.current_price is not None and result.current_price <= 0:
                    result.success = False
                    result.is_suspicious = True
                    result.error_message = "Parsed non-positive price."
                return result
            except requests.Timeout:
                if attempt == retry_count:
                    return ScrapeResult(
                        success=False,
                        source_site=source_site,
                        error_message="Scrape timed out.",
                    )
                time.sleep(1)
            except Exception as exc:
                current_app.logger.exception("Scraper failure")
                if attempt == retry_count:
                    return ScrapeResult(
                        success=False,
                        source_site=source_site,
                        error_message=str(exc),
                    )

        return ScrapeResult(success=False, source_site=source_site, error_message="Unknown scrape failure")
