import asyncio
import gzip
import logging
from collections.abc import Callable
from urllib.parse import urlparse, urlunparse
from xml.etree import ElementTree as ET

import httpx


logger = logging.getLogger(__name__)


class SitemapParserError(Exception):
    pass


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _safe_text(element: ET.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    text = element.text.strip()
    return text if text else None


def _is_valid_child_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _normalize_child_sitemap_host(url: str, root_sitemap_url: str) -> str:
    root_host = (urlparse(root_sitemap_url).netloc or "").lower()
    if not root_host.startswith("www."):
        return url

    parsed = urlparse(url)
    child_host = (parsed.netloc or "").lower()
    bare_root = root_host[4:]
    if child_host != bare_root:
        return url

    return urlunparse((parsed.scheme, root_host, parsed.path, parsed.params, parsed.query, parsed.fragment))


async def _fetch_xml(client: httpx.AsyncClient, url: str) -> str:
    max_attempts = 4
    for attempt in range(1, max_attempts + 1):
        try:
            response = await client.get(url, timeout=12.0)
            response.raise_for_status()
            return _prepare_xml_content(url, response)
        except httpx.TimeoutException as exc:
            if attempt == max_attempts:
                raise SitemapParserError(f"Timeout while fetching sitemap after {max_attempts} attempts: {url}") from exc
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if status_code == 403:
                raise SitemapParserError(f"Access denied by target site (403): {url}") from exc
            # Для временных HTTP-ошибок пробуем повторить загрузку.
            if status_code not in {408, 425, 429, 500, 502, 503, 504} or attempt == max_attempts:
                raise SitemapParserError(f"Failed to fetch sitemap ({status_code}): {url}") from exc
        except httpx.HTTPError as exc:
            if attempt == max_attempts:
                raise SitemapParserError(f"Failed to fetch sitemap after {max_attempts} attempts: {url}") from exc

        await asyncio.sleep(min(0.6 * attempt, 2.0))

    raise SitemapParserError(f"Failed to fetch sitemap: {url}")


def _looks_like_xml(raw: bytes) -> bool:
    return raw.lstrip().startswith(b"<")


def _should_decompress_gzip(url: str, response: httpx.Response) -> bool:
    content_type = response.headers.get("Content-Type", "").lower()
    content_encoding = response.headers.get("Content-Encoding", "").lower()
    is_gzip_header = response.content.startswith(b"\x1f\x8b")
    return (
        url.lower().endswith(".gz")
        or "gzip" in content_type
        or "x-gzip" in content_type
        or "gzip" in content_encoding
        or is_gzip_header
    )


def _prepare_xml_content(url: str, response: httpx.Response) -> str:
    raw = response.content
    if _should_decompress_gzip(url, response):
        try:
            raw = gzip.decompress(raw)
        except (OSError, EOFError) as exc:
            # Некоторые сервера отдают уже распакованный XML даже для .gz URL.
            if not _looks_like_xml(raw):
                raise SitemapParserError(f"Failed to decompress gzip sitemap: {url}") from exc
            logger.warning("Skipping gzip decompression because content already looks like XML: %s", url)

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise SitemapParserError(f"Unable to decode sitemap content as UTF-8: {url}") from exc


async def parse_sitemap(
    start_url: str,
    limit: int | None = None,
    progress_callback: Callable[[int], None] | None = None,
) -> list[dict[str, str | None]]:
    seen_sitemaps: set[str] = set()
    found_urls: dict[str, dict[str, str | None]] = {}
    queue: asyncio.Queue[str] = asyncio.Queue()
    await queue.put(start_url)

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SitemapScanner/1.0; +https://localhost)",
        "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8",
    }
    async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
        while not queue.empty():
            sitemap_url = await queue.get()
            if sitemap_url in seen_sitemaps:
                continue
            seen_sitemaps.add(sitemap_url)

            raw_xml = await _fetch_xml(client, sitemap_url)
            try:
                root = ET.fromstring(raw_xml)
            except ET.ParseError as exc:
                raise SitemapParserError(f"Invalid XML in sitemap: {sitemap_url}") from exc

            root_name = _strip_ns(root.tag)
            children = list(root)
            if root_name == "sitemapindex":
                for child in children:
                    if _strip_ns(child.tag) != "sitemap":
                        continue
                    loc = _safe_text(next((x for x in list(child) if _strip_ns(x.tag) == "loc"), None))
                    if loc and _is_valid_child_url(loc):
                        await queue.put(_normalize_child_sitemap_host(loc, start_url))
            elif root_name == "urlset":
                for child in children:
                    if _strip_ns(child.tag) != "url":
                        continue
                    loc = _safe_text(next((x for x in list(child) if _strip_ns(x.tag) == "loc"), None))
                    if not loc:
                        continue
                    item = {
                        "url": loc,
                        "lastmod": _safe_text(next((x for x in list(child) if _strip_ns(x.tag) == "lastmod"), None)),
                        "changefreq": _safe_text(next((x for x in list(child) if _strip_ns(x.tag) == "changefreq"), None)),
                        "priority": _safe_text(next((x for x in list(child) if _strip_ns(x.tag) == "priority"), None)),
                        "source_sitemap": sitemap_url,
                    }
                    is_new = loc not in found_urls
                    found_urls[loc] = item
                    if is_new and progress_callback:
                        progress_callback(len(found_urls))
                    if limit is not None and len(found_urls) >= limit:
                        logger.info("Sitemap limit reached: %s", limit)
                        if progress_callback:
                            progress_callback(len(found_urls))
                        return list(found_urls.values())
            else:
                raise SitemapParserError(f"Unsupported sitemap root tag: {root_name}")

    if progress_callback:
        progress_callback(len(found_urls))
    return list(found_urls.values())
