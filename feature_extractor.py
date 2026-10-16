import re
import numpy as np
from urllib.parse import urlparse


class URLFeatureExtractor:

    def __init__(self):

        self.suspicious_words = [
            "login", "verify", "secure", "account",
            "update", "bank", "confirm", "signin"
        ]

        self.shorteners = [
            "bit.ly", "tinyurl.com", "goo.gl", "t.co"
        ]

        self.suspicious_tlds = [
            ".ru", ".tk", ".ml", ".ga", ".cf", ".xyz", ".top"
        ]

        self.ip_pattern = re.compile(r"\d+\.\d+\.\d+\.\d+")

    # -------------------------
    # Extract ONE URL
    # -------------------------
    def extract(self, url):

        url = str(url).strip().lower()

        if not url:
            return np.zeros(20)

        parsed = urlparse(url)
        hostname = parsed.netloc.lower()
        path = parsed.path.lower()

        features = []

        # STRUCTURE
        features.append(len(url))
        features.append(len(hostname))
        features.append(url.count("."))
        features.append(url.count("-"))
        features.append(url.count("@"))
        features.append(url.count("/"))
        features.append(1 if "www" in hostname else 0)
        features.append(hostname.count("."))

        # DIGITS
        digits_url = sum(c.isdigit() for c in url)
        digits_host = sum(c.isdigit() for c in hostname)

        features.append(digits_url / len(url) if url else 0)
        features.append(digits_host / len(hostname) if hostname else 0)

        # FLAGS
        features.append(1 if "xn--" in url else 0)
        features.append(1 if "-" in hostname else 0)
        features.append(1 if self.ip_pattern.search(hostname) else 0)

        features.append(1 if any(s in url for s in self.shorteners) else 0)

        # HTTPS FIXED
        features.append(1 if parsed.scheme == "https" else 0)
        features.append(1 if "http" in path else 0)

        features.append(sum(w in url for w in self.suspicious_words))
        features.append(1 if any(tld in hostname for tld in self.suspicious_tlds) else 0)

        # placeholders
        features.append(0)
        features.append(0)

        return np.array(features)

    def transform(self, urls):
        return np.array([self.extract(u) for u in urls])