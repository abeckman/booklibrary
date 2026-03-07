# originally from
# https://github.com/Manikaran20/Books-Inventory/blob/master/SpoonshotAssignment/googlebooks/book_search.py
# Not much of original left
import logging
from urllib.parse import urlparse

import requests
from django.conf import settings

from booklibrary.models import Book

logger = logging.getLogger(__name__)

BASE_URL = getattr(settings, "GOOGLE_BOOKS_API_BASE",
    "https://www.googleapis.com/books/v1/volumes")
API_KEY = settings.GOOGLE_BOOKS_API_KEY

_EXPECTED_HOST = urlparse(BASE_URL).netloc


def _safe_https_url(url, field):
    """Return url only if it is an https:// URL, else log and return None."""
    if not url:
        return None
    if isinstance(url, str) and urlparse(url).scheme == "https":
        return url
    logger.warning("Rejected non-https %s in Google Books response: %r", field, url)
    return None


class GoogleBooksError(Exception):
    """Base error for Google Books failures."""

class GoogleBooksQuotaError(GoogleBooksError):
    """Quota / rate limit exceeded."""

class GoogleBooksAuthError(GoogleBooksError):
    """Auth / key / permission error."""

class GoogleBooksBadRequest(GoogleBooksError):
    """Malformed query or invalid parameters."""


def _map_error(response):
    """Raise a typed exception based on HTTP status + JSON error body."""
    status = response.status_code
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    err = (payload.get("error") or {})
    reason = ""
    if isinstance(err.get("errors"), list) and err["errors"]:
        reason = err["errors"][0].get("reason") or ""
    message = err.get("message") or f"HTTP {status} from Google Books"

    if status == 429 or reason in {"rateLimitExceeded", "quotaExceeded"}:
        raise GoogleBooksQuotaError(message)

    if status == 401 or (status == 403 and reason in {"dailyLimitExceeded", "forbidden"}):
        raise GoogleBooksAuthError(message)

    if status in (400, 404):
        raise GoogleBooksBadRequest(message)

    raise GoogleBooksError(message)


def _parse_volume(item):
    """Extract and normalise fields from a single Google Books API volume into a dict."""
    info = item.get("volumeInfo", {})
    authors = info.get("authors") or []
    categories = info.get("categories") or []
    image_links = info.get("imageLinks") or {}

    volume_id = item["id"]
    return {
        "title":         info.get("title") or "Not Present",
        "author1":       authors[0] if authors else "Not Present",
        "author2":       authors[1] if len(authors) > 1 else None,
        "publisher":     info.get("publisher") or "Not Present",
        "published_date": info.get("publishedDate") or "Not Present",
        "description":   info.get("description") or "Not Present",
        "genre1":        categories[0] if categories else None,
        "genre2":        categories[1] if len(categories) > 1 else None,
        "language":      info.get("language") or "en",
        "preview_link":  _safe_https_url(info.get("previewLink"), "previewLink"),
        "image_link":    _safe_https_url(image_links.get("thumbnail"), "imageLink"),
        "volume_id":     volume_id,
        "is_owned":      Book.objects.filter(uniqueID=volume_id).exists(),
    }


def search_books(query, max_results=10, start_index=0):
    """Call Google Books volumes.list; return (list of volume dicts, total_items)."""
    params = {
        "q": query,
        "maxResults": max_results,
        "startIndex": start_index,
        "key": API_KEY,
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=5, verify=True)
    except requests.RequestException as exc:
        logger.warning("Google Books request failed: %s", exc)
        raise GoogleBooksError("Network error talking to Google Books") from exc

    # Guard against redirect-based attacks (e.g. DNS poisoning redirecting to
    # an attacker-controlled host that presents a valid cert for its own domain).
    response_host = urlparse(resp.url).netloc
    if response_host != _EXPECTED_HOST:
        raise GoogleBooksError(
            f"Response came from unexpected host {response_host!r}; "
            f"expected {_EXPECTED_HOST!r}"
        )

    if not resp.ok:
        _map_error(resp)

    data = resp.json()
    items = data.get("items") or []
    return [_parse_volume(item) for item in items], data.get("totalItems") or 0
