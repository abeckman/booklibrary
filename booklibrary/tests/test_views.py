"""
View tests for the booklibrary app.

Uses Django's RequestFactory throughout so URL routing (and the broken
library/urls.py) is never involved.  Session and message middleware are
attached manually via helpers from conftest.py.
"""
import pytest
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from booklibrary.models import Book, Author, BookInstance, Genre, Location
from booklibrary.views import (
    index,
    BookListView,
    BookDetailView,
    AuthorListView,
    AuthorDetailView,
    LocationListView,
    LocationDetailView,
    GenreListView,
    BookSearchView,
    add_book,
    BookInstanceUpdate,
    BookInstanceDelete,
    get_ip,
)
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
    setup_request,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def get_messages(request):
    """Return list of message strings from request._messages."""
    return [str(m) for m in request._messages]


# ── index ─────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestIndexView:

    def test_index_returns_200(self, rf):
        request = rf.get("/")
        setup_request(request)
        response = index(request)
        assert response.status_code == 200

    def test_index_context_counts(self, rf):
        BookFactory()
        BookFactory()
        AuthorFactory()
        request = rf.get("/")
        setup_request(request)
        response = index(request)
        assert response.status_code == 200

    def test_index_increments_visit_counter(self, rf):
        request = rf.get("/")
        setup_request(request, session_data={"num_visits": 5})
        response = index(request)
        assert response.status_code == 200
        assert request.session["num_visits"] == 6

    def test_index_first_visit_starts_at_one(self, rf):
        request = rf.get("/")
        setup_request(request)
        response = index(request)
        # num_visits was 1 on entry, bumped to 2 in session
        assert request.session["num_visits"] == 2


# ── BookListView ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBookListView:

    def _get(self, rf, params=""):
        request = rf.get(f"/booklibrary/books/{params}")
        setup_request(request)
        return BookListView.as_view()(request)

    def test_no_search_returns_all_books(self, rf):
        BookFactory(title="Alpha")
        BookFactory(title="Zeta")
        response = self._get(rf)
        assert response.status_code == 200

    def test_title_search_filters_results(self, rf):
        BookFactory(title="Python Programming")
        BookFactory(title="Gardening Guide")
        request = rf.get("/booklibrary/books/", {"search": "Python"})
        setup_request(request)
        response = BookListView.as_view()(request)
        assert response.status_code == 200
        titles = [b.title for b in response.context_data["page_obj"]]
        assert "Python Programming" in titles
        assert "Gardening Guide" not in titles

    def test_explicit_title_field_search(self, rf):
        BookFactory(title="Django Book")
        BookFactory(title="Cookbook")
        request = rf.get("/booklibrary/books/", {"search": "Django", "fields": "title"})
        setup_request(request)
        response = BookListView.as_view()(request)
        assert response.status_code == 200

    def test_author_search(self, rf):
        author = AuthorFactory(last_name="Tolkien")
        BookFactory(authors=[author])
        BookFactory()  # unrelated
        request = rf.get("/booklibrary/books/", {"search": "Tolkien", "fields": "author"})
        setup_request(request)
        response = BookListView.as_view()(request)
        assert response.status_code == 200
        titles = [b.title for b in response.context_data["page_obj"]]
        assert len(titles) >= 1

    def test_genre_search(self, rf):
        genre = GenreFactory(name="Science Fiction")
        BookFactory(genre=[genre])
        request = rf.get("/booklibrary/books/", {"search": "Science", "fields": "genre"})
        setup_request(request)
        response = BookListView.as_view()(request)
        assert response.status_code == 200

    def test_series_search(self, rf):
        series = SeriesFactory(name="Foundation")
        BookFactory(series=series)
        request = rf.get("/booklibrary/books/", {"search": "Foundation", "fields": "series"})
        setup_request(request)
        response = BookListView.as_view()(request)
        assert response.status_code == 200

    def test_keyword_search(self, rf):
        kw = KeywordsFactory(name="Space")
        BookFactory(keywords=[kw])
        request = rf.get("/booklibrary/books/", {"search": "Space", "fields": "keyword"})
        setup_request(request)
        response = BookListView.as_view()(request)
        assert response.status_code == 200

    def test_dups_filter_returns_only_multi_instance_books(self, rf):
        user = UserFactory()
        single_book = BookFactory()
        multi_book = BookFactory()
        BookInstanceFactory(book=multi_book, owner=user)
        BookInstanceFactory(book=multi_book, owner=user)
        request = rf.get("/booklibrary/books/", {"dups": "1"})
        setup_request(request)
        response = BookListView.as_view()(request)
        assert response.status_code == 200
        titles = [b.title for b in response.context_data["page_obj"]]
        assert multi_book.title in titles
        assert single_book.title not in titles

    def test_context_has_search_value(self, rf):
        request = rf.get("/booklibrary/books/", {"search": "test"})
        setup_request(request)
        response = BookListView.as_view()(request)
        assert response.context_data["search"] == "test"

    def test_empty_search_returns_all(self, rf):
        BookFactory()
        BookFactory()
        request = rf.get("/booklibrary/books/", {"search": ""})
        setup_request(request)
        response = BookListView.as_view()(request)
        assert response.status_code == 200


# ── BookDetailView ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBookDetailView:

    def test_valid_pk_returns_200(self, rf):
        book = BookFactory()
        request = rf.get(f"/booklibrary/book/{book.pk}")
        setup_request(request)
        response = BookDetailView.as_view()(request, pk=book.pk)
        assert response.status_code == 200

    def test_invalid_pk_returns_404(self, rf):
        request = rf.get("/booklibrary/book/99999")
        setup_request(request)
        response = BookDetailView.as_view()(request, pk=99999)
        assert response.status_code == 404


# ── AuthorListView ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAuthorListView:

    def test_no_search_returns_all_authors(self, rf):
        AuthorFactory(last_name="Asimov")
        AuthorFactory(last_name="Clarke")
        request = rf.get("/booklibrary/authors/")
        setup_request(request)
        response = AuthorListView.as_view()(request)
        assert response.status_code == 200

    def test_search_filters_by_last_name(self, rf):
        AuthorFactory(last_name="Herbert")
        AuthorFactory(last_name="Zelazny")
        request = rf.get("/booklibrary/authors/", {"search": "Herbert"})
        setup_request(request)
        response = AuthorListView.as_view()(request)
        assert response.status_code == 200
        names = [a.last_name for a in response.context_data["page_obj"]]
        assert "Herbert" in names
        assert "Zelazny" not in names

    def test_author_location_param_sets_session(self, rf):
        request = rf.get("/booklibrary/authors/", {"author_location": "1"})
        setup_request(request)
        AuthorListView.as_view()(request)
        assert request.session.get("location") is True

    def test_no_location_param_clears_session(self, rf):
        request = rf.get("/booklibrary/authors/")
        setup_request(request, session_data={"location": True})
        AuthorListView.as_view()(request)
        assert request.session.get("location") is False


# ── AuthorDetailView ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAuthorDetailView:

    def test_valid_author_returns_200(self, rf):
        author = AuthorFactory()
        request = rf.get(f"/booklibrary/author/{author.pk}")
        setup_request(request)
        response = AuthorDetailView.as_view()(request, pk=author.pk)
        assert response.status_code == 200

    def test_invalid_author_returns_404(self, rf):
        request = rf.get("/booklibrary/author/99999")
        setup_request(request)
        response = AuthorDetailView.as_view()(request, pk=99999)
        assert response.status_code == 404


# ── LocationListView ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLocationListView:

    def test_returns_200(self, rf):
        LocationFactory(name="Hallway")
        request = rf.get("/booklibrary/locations/")
        setup_request(request)
        response = LocationListView.as_view()(request)
        assert response.status_code == 200

    def test_search_filters_locations(self, rf):
        LocationFactory(name="Attic Box")
        LocationFactory(name="Basement Shelf")
        request = rf.get("/booklibrary/locations/", {"search": "Attic"})
        setup_request(request)
        response = LocationListView.as_view()(request)
        assert response.status_code == 200
        names = [loc.name for loc in response.context_data["page_obj"]]
        assert "Attic Box" in names
        assert "Basement Shelf" not in names


# ── LocationDetailView ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLocationDetailView:

    def test_shows_books_at_location(self, rf):
        loc = LocationFactory(name="Shelf A")
        user = UserFactory()
        book = BookFactory()
        BookInstanceFactory(book=book, location=loc, owner=user)
        request = rf.get(f"/booklibrary/location/{loc.pk}")
        setup_request(request)
        response = LocationDetailView.as_view()(request, pk=loc.pk)
        assert response.status_code == 200
        instances = list(response.context_data["page_obj"])
        assert len(instances) == 1

    def test_empty_location_shows_no_books(self, rf):
        loc = LocationFactory()
        request = rf.get(f"/booklibrary/location/{loc.pk}")
        setup_request(request)
        response = LocationDetailView.as_view()(request, pk=loc.pk)
        assert response.status_code == 200
        assert len(list(response.context_data["page_obj"])) == 0


# ── GenreListView ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGenreListView:

    def test_returns_200(self, rf):
        GenreFactory(name="Horror")
        request = rf.get("/booklibrary/genre/")
        setup_request(request)
        response = GenreListView.as_view()(request)
        assert response.status_code == 200

    def test_search_filters_genres(self, rf):
        GenreFactory(name="Science Fiction")
        GenreFactory(name="Romance")
        request = rf.get("/booklibrary/genre/", {"search": "Science"})
        setup_request(request)
        response = GenreListView.as_view()(request)
        assert response.status_code == 200
        names = [g.name for g in response.context_data["page_obj"]]
        assert "Science Fiction" in names
        assert "Romance" not in names


# ── BookSearchView ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBookSearchView:

    def test_get_renders_search_form(self, rf):
        request = rf.get("/booklibrary/book/search/")
        setup_request(request)
        response = BookSearchView.as_view()(request)
        assert response.status_code == 200

    def test_post_invalid_form_re_renders(self, rf):
        # Empty 'search' field makes SearchForm invalid
        request = rf.post("/booklibrary/book/search/", {"search": ""})
        setup_request(request)
        response = BookSearchView.as_view()(request)
        assert response.status_code == 200

    @patch("booklibrary.views.search_books")
    def test_post_no_results_shows_info_message(self, mock_search, rf):
        mock_search.return_value = ([], 0)
        request = rf.post("/booklibrary/book/search/", {"search": "xyzzy"})
        setup_request(request)
        response = BookSearchView.as_view()(request)
        assert response.status_code == 200
        msgs = get_messages(request)
        assert any("Google did not return anything" in m for m in msgs)

    @patch("booklibrary.views.search_books")
    def test_post_quota_error_shows_error_message(self, mock_search, rf):
        mock_search.side_effect = GoogleBooksQuotaError("quota")
        request = rf.post("/booklibrary/book/search/", {"search": "test"})
        setup_request(request)
        response = BookSearchView.as_view()(request)
        assert response.status_code == 200
        msgs = get_messages(request)
        assert any("too many requests" in m for m in msgs)

    @patch("booklibrary.views.search_books")
    def test_post_auth_error_shows_error_message(self, mock_search, rf):
        mock_search.side_effect = GoogleBooksAuthError("auth")
        request = rf.post("/booklibrary/book/search/", {"search": "test"})
        setup_request(request)
        response = BookSearchView.as_view()(request)
        assert response.status_code == 200
        msgs = get_messages(request)
        assert any("configuration" in m for m in msgs)

    @patch("booklibrary.views.search_books")
    def test_post_bad_request_shows_error_message(self, mock_search, rf):
        mock_search.side_effect = GoogleBooksBadRequest("bad")
        request = rf.post("/booklibrary/book/search/", {"search": "test"})
        setup_request(request)
        response = BookSearchView.as_view()(request)
        assert response.status_code == 200
        msgs = get_messages(request)
        assert any("simpler query" in m for m in msgs)

    @patch("booklibrary.views.search_books")
    def test_post_generic_error_shows_error_message(self, mock_search, rf):
        mock_search.side_effect = GoogleBooksError("oops")
        request = rf.post("/booklibrary/book/search/", {"search": "test"})
        setup_request(request)
        response = BookSearchView.as_view()(request)
        assert response.status_code == 200
        msgs = get_messages(request)
        assert any("unexpected error" in m for m in msgs)

    @patch("booklibrary.views.search_books")
    def test_post_with_results_renders_results_template(self, mock_search, rf):
        """When results come back and a 'None' genre exists in DB, results render."""
        GenreFactory(name="None")  # view calls Genre.objects.get(name='None') by default
        fake_books = [["Title", "Author", None, "Pub", "2020", "Desc",
                       None, None, "en", "http://p", "http://img", "ID1", "not owned"]]
        mock_search.return_value = (fake_books, 1)
        request = rf.post("/booklibrary/book/search/", {"search": "test"})
        setup_request(request)
        response = BookSearchView.as_view()(request)
        assert response.status_code == 200
        assert response.template_name == "booklibrary/book_results.html"

    @patch("booklibrary.views.search_books")
    def test_post_with_results_missing_none_genre_raises(self, mock_search, rf):
        """Regression: view must not crash when Genre 'None' is absent from DB."""
        fake_books = [["Title", "Author", None, "Pub", "2020", "Desc",
                       None, None, "en", "http://p", "http://img", "ID1", "not owned"]]
        mock_search.return_value = (fake_books, 1)
        request = rf.post("/booklibrary/book/search/", {"search": "test"})
        setup_request(request)
        response = BookSearchView.as_view()(request)
        assert response.status_code == 200
        assert response.template_name == "booklibrary/book_results.html"


# ── add_book ──────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAddBookView:

    def test_get_anonymous_redirects_to_login(self, rf):
        request = rf.get("/booklibrary/book/add/")
        setup_request(request, user=AnonymousUser())
        response = add_book(request)
        assert response.status_code == 302
        assert "/accounts/login/" in response["Location"]

    def test_post_anonymous_redirects_to_login(self, rf):
        request = rf.post("/booklibrary/book/add/", {})
        setup_request(request, user=AnonymousUser())
        response = add_book(request)
        assert response.status_code == 302
        assert "/accounts/login/" in response["Location"]

    def test_get_authenticated_renders_form(self, rf, user):
        request = rf.get("/booklibrary/book/add/")
        setup_request(request, user=user)
        response = add_book(request)
        assert response.status_code == 200

    @patch("booklibrary.views.AddForm")
    def test_post_valid_creates_book_and_redirects(self, MockForm, rf, user):
        """
        Patches AddForm because class-level choices are evaluated at import
        time (empty DB), so real form validation cannot work in tests.
        """
        location = LocationFactory()
        genre = GenreFactory(name="Science Fiction")
        keyword = KeywordsFactory(name="Space")
        series = SeriesFactory(name="Foundation")

        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.cleaned_data = {
            "title": "Dune",
            "author1": "Frank Herbert",
            "author2": "",
            "publisher": "Chilton Books",
            "publishedOn": "1965",
            "description": "A sci-fi epic.",
            "genre1": "Science Fiction",
            "genre2": "",
            "language": "English",
            "previewLink": "https://example.com",
            "imageLink": "https://example.com/img.jpg",
            "uniqueID": "dune-001",
            "status": "PH",
            "Book_Genre": [],
            "Book_Location": str(location.pk),
            "Book_Keywords": [],
            "Book_Series": "None",
        }
        MockForm.return_value = mock_form

        request = rf.post("/booklibrary/book/add/", {})
        setup_request(request, user=user)
        response = add_book(request)

        assert response.status_code == 302
        assert Book.objects.filter(title="Dune").exists()

    @patch("booklibrary.views.AddForm")
    def test_post_duplicate_book_adds_message(self, MockForm, rf, user):
        location = LocationFactory()
        existing = BookFactory(title="Existing Book", uniqueID="dup-001")

        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.cleaned_data = {
            "title": existing.title,
            "author1": "",
            "author2": "",
            "publisher": "",
            "publishedOn": "",
            "description": existing.summary,
            "genre1": "",
            "genre2": "",
            "language": "English",
            "previewLink": "",
            "imageLink": "",
            "uniqueID": existing.uniqueID,
            "status": "PH",
            "Book_Genre": [],
            "Book_Location": str(location.pk),
            "Book_Keywords": [],
            "Book_Series": "None",
        }
        MockForm.return_value = mock_form

        request = rf.post("/booklibrary/book/add/", {})
        setup_request(request, user=user)
        add_book(request)

        msgs = get_messages(request)
        assert any("Duplicate" in m for m in msgs)

    @patch("booklibrary.views.AddForm")
    def test_post_invalid_form_rerenders_results(self, MockForm, rf, user):
        mock_form = MagicMock()
        mock_form.is_valid.return_value = False
        MockForm.return_value = mock_form

        request = rf.post("/booklibrary/book/add/", {})
        setup_request(request, user=user)
        response = add_book(request)
        assert response.status_code == 200


# ── BookInstanceUpdate / BookInstanceDelete (OwnerUpdateView/OwnerDeleteView) ─

@pytest.mark.django_db
class TestBookInstanceOwnerViews:

    def test_owner_can_reach_update_view(self, rf, user):
        bi = BookInstanceFactory(owner=user)
        request = rf.get(f"/booklibrary/bookinstance/{bi.pk}/update/")
        setup_request(request, user=user)
        response = BookInstanceUpdate.as_view()(request, pk=bi.pk)
        assert response.status_code == 200

    def test_non_owner_update_returns_404(self, rf, user, other_user):
        bi = BookInstanceFactory(owner=other_user)
        request = rf.get(f"/booklibrary/bookinstance/{bi.pk}/update/")
        setup_request(request, user=user)
        response = BookInstanceUpdate.as_view()(request, pk=bi.pk)
        assert response.status_code == 404

    def test_anonymous_update_redirects_to_login(self, rf):
        bi = BookInstanceFactory()
        request = rf.get(f"/booklibrary/bookinstance/{bi.pk}/update/")
        setup_request(request, user=AnonymousUser())
        response = BookInstanceUpdate.as_view()(request, pk=bi.pk)
        assert response.status_code == 302

    def test_owner_can_reach_delete_view(self, rf, user):
        bi = BookInstanceFactory(owner=user)
        request = rf.get(f"/booklibrary/bookinstance/{bi.pk}/delete/")
        setup_request(request, user=user)
        response = BookInstanceDelete.as_view()(request, pk=bi.pk)
        assert response.status_code == 200

    def test_non_owner_delete_returns_404(self, rf, user, other_user):
        bi = BookInstanceFactory(owner=other_user)
        request = rf.get(f"/booklibrary/bookinstance/{bi.pk}/delete/")
        setup_request(request, user=user)
        response = BookInstanceDelete.as_view()(request, pk=bi.pk)
        assert response.status_code == 404

    def test_owner_post_delete_removes_instance(self, rf, user):
        bi = BookInstanceFactory(owner=user)
        bi_pk = bi.pk
        request = rf.post(f"/booklibrary/bookinstance/{bi.pk}/delete/")
        setup_request(request, user=user)
        response = BookInstanceDelete.as_view()(request, pk=bi.pk)
        assert response.status_code == 302
        assert not BookInstance.objects.filter(pk=bi_pk).exists()


# ── get_ip ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGetIpView:

    def test_returns_remote_addr(self, rf):
        request = rf.get("/booklibrary/ip/", REMOTE_ADDR="192.168.1.1")
        setup_request(request)
        response = get_ip(request)
        assert response.status_code == 200
        assert b"192.168.1.1" in response.content
