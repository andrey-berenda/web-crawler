from crawler import get_urls

SIMPLE_HTML = """
<!DOCTYPE html>
<html>
<body>
<a href="https://example.com">Main</a>
<a href="/test-page">Test page</a>
<a href="./test-page-1">Test page 1</a>
<a href="../test-page-2">Test page 2</a>
</body>
</html>
"""


def test_get_urls():
    url = 'https://example.com/test?q=test'
    urls = list(get_urls(url, SIMPLE_HTML))
    assert urls == [
        'https://example.com',
        'https://example.com/test-page',
        'https://example.com/test/test-page-1',
        'https://example.com/test-page-2',
    ]
