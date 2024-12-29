from urllib.parse import urlparse, urljoin, quote, unquote

class URLHandler:
    def __init__(self, base_url=None):
        self.base_url = base_url

    def join(self, *parts):
        """Join URL parts together."""
        if self.base_url:
            url = self.base_url
        else:
            url = parts[0]
            parts = parts[1:]
        
        for part in parts:
            url = urljoin(url + ('/' if not url.endswith('/') else ''), str(part))
        return url

    def parse(self, url):
        """Parse URL into components."""
        return urlparse(url)

    def encode(self, url):
        """URL-encode string."""
        return quote(url)

    def decode(self, url):
        """URL-decode string."""
        return unquote(url) 