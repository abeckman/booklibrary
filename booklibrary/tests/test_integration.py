"""
Integration tests for the booklibrary app.

These tests exercise the *full* Django request/response stack using the
Django test client: URL routing, middleware, sessions, authentication,
message queuing, and template rendering.

They complement the unit-level tests in test_views.py (which use
RequestFactory and bypass routing/middleware).

The message block in base_menu.html is commented out, so Django messages
are never rendered into HTML.  All message assertions therefore call
``get_messages(response.wsgi_request)`` on the raw request object where the
messages remain unconsumed.

External services are mocked throughout.

Run with:
    pytest booklibrary/tests/test_integration.py -v
"""

import pytest
from unittest.mock import patch

from django.contrib.messages import get_messages
from django.urls import reverse

from booklibrary.models import Author, Book, BookInstance, Genre, Language, Location
from booklibrary.utils.google_books import (
    GoogleBooksAuthError,
    GoogleBooksBadRequest,
    GoogleBooksError,
    GoogleBooksQuotaError,
)

from .conftest import (
    AuthorFactory,
    BookFactory,
    BookInstanceFactory,
    GenreFactory,
    KeywordsFactory,
    LanguageFactory,
    LocationFactory,
    SeriesFactory,
    UserFactory,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _msgs(response):
    """
    Return all queued message strings for a response.

    Works for both 200 and 302 responses.  Because the base template does
    *not* iterate the messages context variable (the block is commented out),
    the messages storage is never consumed during template rendering and
    remains fully readable here.
    """
    return [str(m) for m in get_messages(response.wsgi_request)]


def _add_book_payload(location, **overrides):
    """
    Build a minimal, valid POST payload for the ``add_book`` view.

    Key constraints imposed by the view's implementation:

    - ``Book_Location`` **must** be a real Location PK.  Even though the
      form field is ``required=False``, the view always calls
      ``Location.objects.get(id=Book_Location)`` unconditionally.
    - ``Book_Keywords`` should be ``""`` (empty string).  The view iterates
      over the raw string value character-by-character, so a non-empty value
      would be mis-parsed as individual character PKs.
    - ``Book_Series`` should be ``""`` (empty string).  An empty value is
      falsy and causes the view's series-processing block to be skipped
      entirely.
    - ``publishedOn`` of ``"1965"`` (exactly 4 chars) is converted to a
      ``datetime`` by the view, which Django's DateField accepts.
    """
    data = {
        "title": "Dune",
        "author1": "Frank Herbert",
        "author2": "",
        "publisher": "Chilton Books",
        "publishedOn": "1965",
        "description": "A science-fiction epic set on the desert planet Arrakis.",
        "genre1": "Science Fiction",
        "genre2": "",
        "language": "English",
        "previewLink": "https://example.com/preview",
        "imageLink": "https://example.com/image.jpg",
        "uniqueID": "dune-integration-001",
        "status": "PHY",
        "Book_Genre": [],
        "Book_Location": str(location.pk),
        "Book_Keywords": "",
        "Book_Series": "",
    }
    data.update(overrides)
    return data


# ── 1. Authentication / redirect behaviour ───────────────────────────────────

@pytest.mark.django_db
class TestAuthenticationRedirects:
    """
    Anonymous users must be redirected to the login page for every
    login-required view.  Logged-in users must be able to reach those
    same views.
    """

    def test_anonymous_get_add_book_redirects_to_login(self, client):
        url = reverse("booklibrary:book-add")
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response["Location"]

    def test_anonymous_post_add_book_redirects_to_login(self, client):
        url = reverse("booklibrary:book-add")
        response = client.post(url, data={"title": "Fake"})
        assert response.status_code == 302
        assert "/accounts/login/" in response["Location"]

    def test_anonymous_bookinstance_update_redirects_to_login(self, client):
        bi = BookInstanceFactory()
        url = reverse("booklibrary:bookinstance-update", kwargs={"pk": bi.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response["Location"]

    def test_anonymous_bookinstance_delete_redirects_to_login(self, client):
        bi = BookInstanceFactory()
        url = reverse("booklibrary:bookinstance-delete", kwargs={"pk": bi.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert "/accounts/login/" in response["Location"]

    def test_logged_in_user_can_reach_add_book_page(self, client):
        user = UserFactory()
        client.force_login(user)
        url = reverse("booklibrary:book-add")
        response = client.get(url)
        assert response.status_code == 200


# ── 2. Full add_book workflow ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestAddBookWorkflow:
    """
    End-to-end flows through the ``add_book`` view:
    form → view logic → model.save() → BookInstance creation → redirect.
    """

    def test_valid_post_creates_book_author_and_instance_in_db(self, client):
        """
        Login → POST valid add_book form →
        Book, Author, and BookInstance all land in the database.
        """
        user = UserFactory()
        location = LocationFactory()
        client.force_login(user)

        response = client.post(
            reverse("booklibrary:book-add"),
            data=_add_book_payload(location),
        )

        assert response.status_code == 302
        assert Book.objects.filter(title="Dune").exists()
        assert Author.objects.filter(last_name="Herbert").exists()
        assert BookInstance.objects.filter(owner=user).exists()

    def test_valid_post_links_genre_and_language_to_book(self, client):
        """Genre and Language records are created and associated with the book."""
        user = UserFactory()
        location = LocationFactory()
        client.force_login(user)

        client.post(
            reverse("booklibrary:book-add"),
            data=_add_book_payload(location),
        )

        book = Book.objects.get(title="Dune")
        assert book.genre.filter(name="Science Fiction").exists()
        assert book.language is not None
        assert book.language.name == "English"

    def test_valid_post_sets_bookinstance_owner_to_logged_in_user(self, client):
        """The BookInstance created by add_book must be owned by the request user."""
        user = UserFactory()
        location = LocationFactory()
        client.force_login(user)

        client.post(
            reverse("booklibrary:book-add"),
            data=_add_book_payload(location),
        )

        book = Book.objects.get(title="Dune")
        bi = BookInstance.objects.get(book=book)
        assert bi.owner == user

    def test_duplicate_uniqueid_queues_duplicate_message(self, client):
        """
        Posting a uniqueID that already exists adds a 'Duplicate book' message.
        The pre-existing book count stays at 1 (no second Book row created).
        """
        user = UserFactory()
        location = LocationFactory()
        BookFactory(title="Existing Dune", uniqueID="dune-dup-001")
        client.force_login(user)

        response = client.post(
            reverse("booklibrary:book-add"),
            data=_add_book_payload(location, uniqueID="dune-dup-001"),
        )

        # View still redirects; message is queued but not yet rendered.
        assert any("Duplicate" in m for m in _msgs(response))
        assert Book.objects.filter(uniqueID="dune-dup-001").count() == 1

    def test_invalid_post_empty_title_rerenders_form_no_db_changes(self, client):
        """Empty title fails AddForm validation (min_length=2) → 200, no Book."""
        user = UserFactory()
        location = LocationFactory()
        client.force_login(user)

        response = client.post(
            reverse("booklibrary:book-add"),
            data=_add_book_payload(location, title=""),
        )

        assert response.status_code == 200
        assert Book.objects.count() == 0

    def test_invalid_post_missing_author1_rerenders_form_no_db_changes(self, client):
        """Missing required author1 → AddForm invalid → 200, no records created."""
        user = UserFactory()
        location = LocationFactory()
        client.force_login(user)

        response = client.post(
            reverse("booklibrary:book-add"),
            data=_add_book_payload(location, author1=""),
        )

        assert response.status_code == 200
        assert Book.objects.count() == 0
        assert Author.objects.count() == 0

    def test_invalid_post_missing_uniqueid_rerenders_form_no_db_changes(self, client):
        """Missing required uniqueID → AddForm invalid → 200, no records created."""
        user = UserFactory()
        location = LocationFactory()
        client.force_login(user)

        response = client.post(
            reverse("booklibrary:book-add"),
            data=_add_book_payload(location, uniqueID=""),
        )

        assert response.status_code == 200
        assert Book.objects.count() == 0


# ── 3. BookInstance owner-only update / delete ────────────────────────────────

@pytest.mark.django_db
class TestBookInstanceOwnerEnforcement:
    """
    ``OwnerUpdateView`` and ``OwnerDeleteView`` restrict queryset to objects
    owned by the requesting user.  Non-owners receive 404; anonymous users
    are redirected to login.
    """

    def test_owner_can_reach_bookinstance_update_view(self, client):
        user = UserFactory()
        bi = BookInstanceFactory(owner=user)
        client.force_login(user)

        url = reverse("booklibrary:bookinstance-update", kwargs={"pk": bi.pk})
        response = client.get(url)
        assert response.status_code == 200

    def test_non_owner_update_returns_404(self, client):
        owner = UserFactory()
        intruder = UserFactory()
        bi = BookInstanceFactory(owner=owner)
        client.force_login(intruder)

        url = reverse("booklibrary:bookinstance-update", kwargs={"pk": bi.pk})
        response = client.get(url)
        assert response.status_code == 404

    def test_owner_post_delete_removes_instance_and_redirects(self, client):
        """
        POST to the delete view as the owning user removes the BookInstance
        from the database and redirects to the book list.
        """
        user = UserFactory()
        bi = BookInstanceFactory(owner=user)
        bi_pk = bi.pk
        client.force_login(user)

        url = reverse("booklibrary:bookinstance-delete", kwargs={"pk": bi.pk})
        response = client.post(url)

        assert response.status_code == 302
        assert not BookInstance.objects.filter(pk=bi_pk).exists()

    def test_owner_delete_redirect_target_is_book_list(self, client):
        user = UserFactory()
        bi = BookInstanceFactory(owner=user)
        client.force_login(user)

        url = reverse("booklibrary:bookinstance-delete", kwargs={"pk": bi.pk})
        response = client.post(url)

        assert reverse("booklibrary:books") in response["Location"]

    def test_non_owner_post_delete_returns_404_and_preserves_instance(self, client):
        owner = UserFactory()
        intruder = UserFactory()
        bi = BookInstanceFactory(owner=owner)
        client.force_login(intruder)

        url = reverse("booklibrary:bookinstance-delete", kwargs={"pk": bi.pk})
        response = client.post(url)

        assert response.status_code == 404
        assert BookInstance.objects.filter(pk=bi.pk).exists()


# ── 4. Book list and detail views ─────────────────────────────────────────────

@pytest.mark.django_db
class TestBookListAndDetailViews:
    """Verify list filtering and detail rendering through the full HTTP stack."""

    def test_book_list_returns_200_and_shows_all_books(self, client):
        BookFactory(title="Alpha Book")
        BookFactory(title="Zeta Book")
        with patch.object(
            Book,
            "get_absolute_url",
            lambda self: f"/booklibrary/book/{self.pk}/",
        ):
            response = client.get(reverse("booklibrary:books"))
            content = response.content.decode()
        assert response.status_code == 200
        assert "Alpha Book" in content
        assert "Zeta Book" in content

    def test_book_list_title_search_filters_results(self, client):
        BookFactory(title="Python Programming")
        BookFactory(title="Gardening Guide")
        with patch.object(
            Book,
            "get_absolute_url",
            lambda self: f"/booklibrary/book/{self.pk}/",
        ):
            response = client.get(
                reverse("booklibrary:books"),
                {"search": "Python"},
            )
            content = response.content.decode()
        assert response.status_code == 200
        assert "Python Programming" in content
        assert "Gardening Guide" not in content

    def test_book_list_author_search_filters_results(self, client):
        author = AuthorFactory(last_name="Tolkien")
        BookFactory(title="The Lord of the Rings", authors=[author])
        BookFactory(title="Unrelated Book")
        with patch.object(
            Book,
            "get_absolute_url",
            lambda self: f"/booklibrary/book/{self.pk}/",
        ):
            response = client.get(
                reverse("booklibrary:books"),
                {"search": "Tolkien", "fields": "author"},
            )
            content = response.content.decode()
        assert response.status_code == 200
        assert "Lord of the Rings" in content
        assert "Unrelated Book" not in content

    def test_book_list_genre_search_filters_results(self, client):
        genre = GenreFactory(name="Horror")
        BookFactory(title="It", genre=[genre])
        BookFactory(title="Silent Spring")
        with patch.object(
            Book,
            "get_absolute_url",
            lambda self: f"/booklibrary/book/{self.pk}/",
        ):
            response = client.get(
                reverse("booklibrary:books"),
                {"search": "Horror", "fields": "genre"},
            )
            content = response.content.decode()
        assert response.status_code == 200
        assert "It" in content
        assert "Silent Spring" not in content

    def test_book_list_dups_filter_returns_only_multi_instance_books(self, client):
        user = UserFactory()
        single_book = BookFactory(title="Once Only")
        multi_book = BookFactory(title="Multiple Copies")
        BookInstanceFactory(book=multi_book, owner=user)
        BookInstanceFactory(book=multi_book, owner=user)

        # The dups code path returns a Python list (not a queryset).  Django's
        # template engine calls book.get_absolute_url() on each item and, unlike
        # AttributeError/TypeError, the resulting NoReverseMatch is re-raised
        # rather than silently swallowed.  Patch the method to a plain URL so
        # the template renders cleanly; the filter logic is still exercised.
        with patch.object(
            Book,
            "get_absolute_url",
            lambda self: f"/booklibrary/book/{self.pk}/",
        ):
            response = client.get(reverse("booklibrary:books"), {"dups": "1"})
            content = response.content.decode()

        assert response.status_code == 200
        assert "Multiple Copies" in content
        assert "Once Only" not in content

    def test_book_detail_shows_book_title(self, client):
        book = BookFactory(title="Foundation")
        response = client.get(
            reverse("booklibrary:book-detail", kwargs={"pk": book.pk})
        )
        assert response.status_code == 200
        assert b"Foundation" in response.content

    def test_book_detail_with_nonexistent_pk_returns_404(self, client):
        response = client.get(
            reverse("booklibrary:book-detail", kwargs={"pk": 999_999})
        )
        assert response.status_code == 404


# ── 5. Google Books search view (external API mocked) ────────────────────────

@pytest.mark.django_db
class TestBookSearchViewIntegration:
    """
    Full-stack tests for ``BookSearchView``.  The Google Books API is mocked
    so tests run without network access.

    Message assertions use ``_msgs(response)`` because ``base_menu.html``
    has the messages block commented out, meaning messages are not rendered
    into HTML and remain readable in the request's storage object.
    """

    def test_get_renders_search_form_with_200(self, client):
        response = client.get(reverse("booklibrary:book-search"))
        assert response.status_code == 200

    def test_post_empty_search_is_invalid_and_rerenders(self, client):
        """Empty search string fails SearchForm validation — no API call made."""
        response = client.post(
            reverse("booklibrary:book-search"),
            data={"search": ""},
        )
        assert response.status_code == 200

    @patch("booklibrary.views.search_books")
    def test_post_quota_error_queues_error_message(self, mock_search, client):
        mock_search.side_effect = GoogleBooksQuotaError("quota exceeded")
        response = client.post(
            reverse("booklibrary:book-search"),
            data={"search": "anything"},
        )
        assert response.status_code == 200
        assert any("too many requests" in m for m in _msgs(response))

    @patch("booklibrary.views.search_books")
    def test_post_auth_error_queues_error_message(self, mock_search, client):
        mock_search.side_effect = GoogleBooksAuthError("bad key")
        response = client.post(
            reverse("booklibrary:book-search"),
            data={"search": "anything"},
        )
        assert response.status_code == 200
        assert any("configuration" in m for m in _msgs(response))

    @patch("booklibrary.views.search_books")
    def test_post_bad_request_error_queues_error_message(self, mock_search, client):
        mock_search.side_effect = GoogleBooksBadRequest("bad query")
        response = client.post(
            reverse("booklibrary:book-search"),
            data={"search": "test"},
        )
        assert response.status_code == 200
        assert any("simpler query" in m for m in _msgs(response))

    @patch("booklibrary.views.search_books")
    def test_post_generic_error_queues_error_message(self, mock_search, client):
        mock_search.side_effect = GoogleBooksError("unknown")
        response = client.post(
            reverse("booklibrary:book-search"),
            data={"search": "test"},
        )
        assert response.status_code == 200
        assert any("unexpected error" in m for m in _msgs(response))

    @patch("booklibrary.views.search_books")
    def test_post_no_results_queues_info_message(self, mock_search, client):
        mock_search.return_value = ([], 0)
        response = client.post(
            reverse("booklibrary:book-search"),
            data={"search": "xyzzy"},
        )
        assert response.status_code == 200
        assert any("Google did not return anything" in m for m in _msgs(response))

    @patch("booklibrary.views.search_books")
    def test_post_with_results_renders_results_template(self, mock_search, client):
        """When books are returned the view renders book_results.html."""
        fake_books = [[
            "Title", "Author", None, "Pub", "2020", "Desc",
            None, None, "en", "https://p.example.com",
            "https://img.example.com", "ID1", "not owned",
        ]]
        mock_search.return_value = (fake_books, 1)
        response = client.post(
            reverse("booklibrary:book-search"),
            data={"search": "test"},
        )
        assert response.status_code == 200
        assert response.templates[0].name == "booklibrary/book_results.html"
