"""Polite HTTP layer — UA rotation, retries, robots awareness, throttling."""
from __future__ import annotations
import time, random, urllib.parse, urllib.robotparser
import requests

UAS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
]

_robots_cache: dict = {}

def _robots(host: str):
    if host in _robots_cache:
        return _robots_cache[host]
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(f"https://{host}/robots.txt")
    try:
        rp.read()
    except Exception:
        rp = None
    _robots_cache[host] = rp
    return rp

def allowed(url: str, ua: str = "boathire24-leadbot") -> bool:
    host = urllib.parse.urlparse(url).hostname or ""
    rp = _robots(host)
    if rp is None:
        return True
    try:
        return rp.can_fetch(ua, url)
    except Exception:
        return True

def get(url: str, timeout: int = 12, respect_robots: bool = True, max_retries: int = 2):
    if respect_robots and not allowed(url):
        return None
    headers = {
        "User-Agent": random.choice(UAS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,es;q=0.5",
    }
    for attempt in range(max_retries + 1):
        try:
            r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            if r.status_code in (429, 503):
                time.sleep(2 ** attempt + random.random())
                continue
            return r
        except requests.RequestException:
            if attempt == max_retries:
                return None
            time.sleep(1 + random.random())
    return None

def polite_sleep(base: float = 1.0, jitter: float = 1.0):
    time.sleep(base + random.random() * jitter)
