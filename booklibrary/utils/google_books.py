# originally from
# https://github.com/Manikaran20/Books-Inventory/blob/master/SpoonshotAssignment/googlebooks/book_search.py
# Not much of original left
import logging
import requests
from booklibrary.models import Book
from django.conf import settings # pick up Google settings

logger = logging.getLogger(__name__)

BASE_URL = getattr(settings, "GOOGLE_BOOKS_API_BASE",
    "https://www.googleapis.com/books/v1/volumes")
API_KEY = settings.GOOGLE_BOOKS_API_KEY

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

    # Quota / rate limiting
    if status == 429 or reason in {"rateLimitExceeded", "quotaExceeded"}:
        raise GoogleBooksQuotaError(message)

    # Auth / key issues
    if status == 401 or (status == 403 and reason in {"dailyLimitExceeded", "forbidden"}):
        raise GoogleBooksAuthError(message)

    # Bad request
    if status in (400, 404):
        raise GoogleBooksBadRequest(message)

    # Generic
    raise GoogleBooksError(message)

def search_books(query, max_results=10, start_index=0):
    """Call Google Books volumes.list and return parsed items list."""
    params = {
        "q": query,
        "maxResults": max_results,
        "startIndex": start_index,
        "key": API_KEY,
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=5)
    except requests.RequestException as exc:
        # Network, DNS, timeouts, etc.
        logger.warning("Google Books request failed: %s", exc)
        raise GoogleBooksError("Network error talking to Google Books") from exc

    if not resp.ok:
        _map_error(resp)

    data = resp.json()  # In success path Books returns valid JSON.[web:13][web:38]
    items = data.get("items", []) or []  # Some queries return no items.[web:13]
    results = []
    for item in items:
        book_info = []
        item['volumeInfo'].setdefault('title', 'Not Present')
        book_info.append(item['volumeInfo']['title'])
        item['volumeInfo'].setdefault('authors', 'Not Present')
        book_info.append(item['volumeInfo']['authors'][0])
        if len(item['volumeInfo']['authors']) > 1:             # Only pick first two authors
            book_info.append(item['volumeInfo']['authors'][1])
        else:
            book_info.append(None)
        item['volumeInfo'].setdefault('publisher', 'Not Present')
        book_info.append(item['volumeInfo'].get('publisher'))
        item['volumeInfo'].setdefault('publishedDate', 'Not Present')
        book_info.append(item['volumeInfo'].get('publishedDate'))
        item['volumeInfo'].setdefault('description', 'Not Present')
        book_info.append(item['volumeInfo'].get('description'))
        if item['volumeInfo'].get('categories') == None: # no additional genre
            book_info.append(None)
            book_info.append(None)
        else:
            book_info.append(item['volumeInfo']['categories'][0])
            if len(item['volumeInfo']['categories']) > 2:             # Only pick first two categories
                book_info.append(item['volumeInfo']['categories'][1])
            else:
                book_info.append(None)
        item['volumeInfo'].setdefault('language', 'en')
        book_info.append(item["volumeInfo"].get("language"))
        item['volumeInfo'].setdefault('previewLink', 'Not Present')
        book_info.append(item["volumeInfo"].get("previewLink"))
        item['volumeInfo'].setdefault("imageLinks", {'thumbnail': 'https://i.imgur.com/fnVKr.gif'})
        book_info.append(item['volumeInfo']["imageLinks"].get("thumbnail"))
        book_info.append(item["id"])
        if Book.objects.filter(uniqueID = item["id"]):
            book_info.append("owned")
        else:
            book_info.append("not owned")
        results.append(book_info) # add just constructed list to overall trial book list

    return results, data.get("totalItems", 0) or 0
# https://www.geeksforgeeks.org/handling-missing-keys-python-dictionaries/
