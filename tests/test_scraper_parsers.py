from app.services.scraper_service import AmazonParser, FlipkartParser


def test_amazon_parser_extracts_title_and_price():
    html = '''
    <html><span id="productTitle">Test Laptop</span>
    <span class="a-price"><span class="a-offscreen">₹54,999</span></span>
    <div id="availability"><span>In stock</span></div></html>
    '''
    result = AmazonParser().parse(html, "https://amazon.in/dp/B000000001")
    assert result.success is True
    assert result.title == "Test Laptop"
    assert result.current_price == 54999.0


def test_flipkart_parser_extracts_title_and_price():
    html = '''
    <html><span class="B_NuCI">Phone Model X</span>
    <div class="_30jeq3">₹19,999</div></html>
    '''
    result = FlipkartParser().parse(html, "https://flipkart.com/item/p/itm123?pid=ABC")
    assert result.success is True
    assert result.title == "Phone Model X"
    assert result.current_price == 19999.0


def test_flipkart_parser_flags_blocked_page():
    html = "<html><body>Access Denied. Request blocked by security layer.</body></html>"
    result = FlipkartParser().parse(html, "https://flipkart.com/item/p/itm123?pid=ABC")
    assert result.success is False
    assert result.metadata["blocked"] is True
    assert "blocked" in result.error_message.lower()
