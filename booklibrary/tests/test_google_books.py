"""
Unit tests for booklibrary/utils/google_books.py.

All HTTP calls are mocked so these tests run offline.
"""
import pytest
from unittest.mock import MagicMock, patch

from booklibrary.utils.google_books import (
    GoogleBooksAuthError,
    GoogleBooksBadRequest,
    GoogleBooksError,
    GoogleBooksQuotaError,
    _map_error,
    search_books,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _mock_response(status_code, json_data=None, raise_json=False):
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = status_code < 400
    if raise_json:
        resp.json.side_effect = ValueError("not JSON")
    else:
        resp.json.return_value = json_data or {}
    return resp


def _make_volume(
    title="Test Book",
    authors=None,
    publisher="Test Pub",
    published_date="2023",
    description="A description",
    categories=None,
    language="en",
    preview_link="https://preview.example.com",
    thumbnail="https://img.example.com/thumb.jpg",
    volume_id="vol123",
):
    authors = authors or ["Author One"]
    info = {
        "title": title,
        "authors": authors,
        "publisher": publisher,
        "publishedDate": published_date,
        "description": description,
        "language": language,
        "previewLink": preview_link,
        "imageLinks": {"thumbnail": thumbnail},
    }
    if categories is not None:
        info["categories"] = categories
    return {"id": volume_id, "volumeInfo": info}


# ── _map_error ────────────────────────────────────────────────────────────────

class TestMapError:

    def test_429_raises_quota_error(self):
        resp = _mock_response(429, {"error": {"message": "rate limit"}})
        with pytest.raises(GoogleBooksQuotaError):
            _map_error(resp)

    def test_rateLimitExceeded_reason_raises_quota_error(self):
        payload = {
            "error": {
                "message": "quota",
                "errors": [{"reason": "rateLimitExceeded"}],
            }
        }
        resp = _mock_response(403, payload)
        with pytest.raises(GoogleBooksQuotaError):
            _map_error(resp)

    def test_quotaExceeded_reason_raises_quota_error(self):
        payload = {
            "error": {
                "message": "quota",
                "errors": [{"reason": "quotaExceeded"}],
            }
        }
        resp = _mock_response(403, payload)
        with pytest.raises(GoogleBooksQuotaError):
            _map_error(resp)

    def test_401_raises_auth_error(self):
        resp = _mock_response(401, {"error": {"message": "unauthorized"}})
        with pytest.raises(GoogleBooksAuthError):
            _map_error(resp)

    def test_403_daily_limit_raises_auth_error(self):
        payload = {
            "error": {
                "message": "daily limit",
                "errors": [{"reason": "dailyLimitExceeded"}],
            }
        }
        resp = _mock_response(403, payload)
        with pytest.raises(GoogleBooksAuthError):
            _map_error(resp)

    def test_403_forbidden_raises_auth_error(self):
        payload = {
            "error": {
                "message": "forbidden",
                "errors": [{"reason": "forbidden"}],
            }
        }
        resp = _mock_response(403, payload)
        with pytest.raises(GoogleBooksAuthError):
            _map_error(resp)

    def test_400_raises_bad_request(self):
        resp = _mock_response(400, {"error": {"message": "bad request"}})
        with pytest.raises(GoogleBooksBadRequest):
            _map_error(resp)

    def test_404_raises_bad_request(self):
        resp = _mock_response(404, {"error": {"message": "not found"}})
        with pytest.raises(GoogleBooksBadRequest):
            _map_error(resp)

    def test_500_raises_generic_error(self):
        resp = _mock_response(500, {"error": {"message": "server error"}})
        with pytest.raises(GoogleBooksError):
            _map_error(resp)

    def test_non_json_response_uses_fallback_message(self):
        resp = _mock_response(500, raise_json=True)
        with pytest.raises(GoogleBooksError, match="HTTP 500"):
            _map_error(resp)

    def test_error_message_propagated(self):
        resp = _mock_response(429, {"error": {"message": "Custom quota message"}})
        with pytest.raises(GoogleBooksQuotaError, match="Custom quota message"):
            _map_error(resp)


# ── search_books ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSearchBooks:

    @patch("booklibrary.utils.google_books.requests.get")
    def test_happy_path_single_result(self, mock_get):
        volume = _make_volume(
            title="Foundation",
            authors=["Isaac Asimov"],
            publisher="Gnome Press",
            published_date="1951",
            description="Classic sci-fi.",
            categories=["Science Fiction"],
            language="en",
            preview_link="https://preview.example.com",
            thumbnail="https://img.example.com/t.jpg",
            volume_id="asimov-001",
        )
        mock_get.return_value = _mock_response(200, {"items": [volume], "totalItems": 1})

        results, total = search_books("Foundation")

        assert total == 1
        assert len(results) == 1
        book = results[0]
        assert book[0] == "Foundation"         # title
        assert book[1] == "Isaac Asimov"        # author1
        assert book[2] is None                  # author2 (only one author)
        assert book[3] == "Gnome Press"         # publisher
        assert book[4] == "1951"                # publishedDate
        assert book[5] == "Classic sci-fi."     # description
        assert book[6] == "Science Fiction"     # genre1
        assert book[7] is None                  # genre2
        assert book[8] == "en"                  # language
        assert book[9] == "https://preview.example.com"
        assert book[10] == "https://img.example.com/t.jpg"
        assert book[11] == "asimov-001"         # volume id
        assert book[12] == "not owned"          # ownership flag

    @patch("booklibrary.utils.google_books.requests.get")
    def test_two_authors_captured(self, mock_get):
        volume = _make_volume(authors=["Author A", "Author B", "Author C"])
        mock_get.return_value = _mock_response(200, {"items": [volume], "totalItems": 1})

        results, _ = search_books("test")
        book = results[0]
        assert book[1] == "Author A"
        assert book[2] == "Author B"  # only first two captured

    @patch("booklibrary.utils.google_books.requests.get")
    def test_two_categories_captured(self, mock_get):
        volume = _make_volume(categories=["Cat A", "Cat B", "Cat C"])
        mock_get.return_value = _mock_response(200, {"items": [volume], "totalItems": 1})

        results, _ = search_books("test")
        book = results[0]
        assert book[6] == "Cat A"
        assert book[7] == "Cat B"  # only first two captured

    @patch("booklibrary.utils.google_books.requests.get")
    def test_no_categories_returns_none(self, mock_get):
        volume = _make_volume(categories=None)
        volume["volumeInfo"].pop("categories", None)  # ensure key absent
        mock_get.return_value = _mock_response(200, {"items": [volume], "totalItems": 1})

        results, _ = search_books("test")
        book = results[0]
        assert book[6] is None
        assert book[7] is None

    @patch("booklibrary.utils.google_books.requests.get")
    def test_missing_title_defaults_to_not_present(self, mock_get):
        volume = _make_volume()
        del volume["volumeInfo"]["title"]
        mock_get.return_value = _mock_response(200, {"items": [volume], "totalItems": 1})

        results, _ = search_books("test")
        assert results[0][0] == "Not Present"

    @patch("booklibrary.utils.google_books.requests.get")
    def test_no_items_returns_empty(self, mock_get):
        mock_get.return_value = _mock_response(200, {"totalItems": 0})

        results, total = search_books("nothing")
        assert results == []
        assert total == 0

    @patch("booklibrary.utils.google_books.requests.get")
    def test_items_none_returns_empty(self, mock_get):
        mock_get.return_value = _mock_response(200, {"items": None, "totalItems": 0})

        results, total = search_books("test")
        assert results == []
        assert total == 0

    @patch("booklibrary.utils.google_books.requests.get")
    def test_max_results_param_forwarded(self, mock_get):
        mock_get.return_value = _mock_response(200, {"items": [], "totalItems": 0})

        search_books("test", max_results=5)
        _, kwargs = mock_get.call_args
        # params are passed as keyword arg
        call_params = mock_get.call_args[1].get("params") or mock_get.call_args[0][1]
        assert call_params["maxResults"] == 5

    @patch("booklibrary.utils.google_books.requests.get")
    def test_start_index_param_forwarded(self, mock_get):
        mock_get.return_value = _mock_response(200, {"items": [], "totalItems": 0})

        search_books("test", start_index=10)
        call_params = mock_get.call_args[1].get("params") or mock_get.call_args[0][1]
        assert call_params["startIndex"] == 10

    @patch("booklibrary.utils.google_books.requests.get")
    def test_network_error_raises_google_books_error(self, mock_get):
        import requests as req_lib
        mock_get.side_effect = req_lib.RequestException("DNS failure")

        with pytest.raises(GoogleBooksError, match="Network error"):
            search_books("test")

    @patch("booklibrary.utils.google_books.requests.get")
    def test_429_raises_quota_error(self, mock_get):
        mock_get.return_value = _mock_response(429, {"error": {"message": "quota"}})
        with pytest.raises(GoogleBooksQuotaError):
            search_books("test")

    @patch("booklibrary.utils.google_books.requests.get")
    def test_401_raises_auth_error(self, mock_get):
        mock_get.return_value = _mock_response(401, {"error": {"message": "auth"}})
        with pytest.raises(GoogleBooksAuthError):
            search_books("test")

    @patch("booklibrary.utils.google_books.requests.get")
    def test_400_raises_bad_request(self, mock_get):
        mock_get.return_value = _mock_response(400, {"error": {"message": "bad"}})
        with pytest.raises(GoogleBooksBadRequest):
            search_books("test")

    @patch("booklibrary.utils.google_books.requests.get")
    def test_owned_book_flagged_correctly(self, mock_get):
        """Book already in DB should be flagged 'owned'."""
        from .conftest import BookFactory
        existing = BookFactory(uniqueID="known-id")

        volume = _make_volume(volume_id="known-id")
        mock_get.return_value = _mock_response(200, {"items": [volume], "totalItems": 1})

        results, _ = search_books("test")
        assert results[0][12] == "owned"

    @patch("booklibrary.utils.google_books.requests.get")
    def test_unknown_book_flagged_not_owned(self, mock_get):
        volume = _make_volume(volume_id="brand-new-id")
        mock_get.return_value = _mock_response(200, {"items": [volume], "totalItems": 1})

        results, _ = search_books("test")
        assert results[0][12] == "not owned"

    @patch("booklibrary.utils.google_books.requests.get")
    def test_multiple_results_returned(self, mock_get):
        volumes = [
            _make_volume(title=f"Book {i}", volume_id=f"id-{i}")
            for i in range(5)
        ]
        mock_get.return_value = _mock_response(200, {"items": volumes, "totalItems": 5})

        results, total = search_books("test")
        assert len(results) == 5
        assert total == 5

    @patch("booklibrary.utils.google_books.requests.get")
    def test_timeout_set_to_5_seconds(self, mock_get):
        mock_get.return_value = _mock_response(200, {"items": [], "totalItems": 0})
        search_books("test")
        _, kwargs = mock_get.call_args
        assert kwargs.get("timeout") == 5
