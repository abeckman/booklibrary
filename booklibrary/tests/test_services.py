"""
Unit tests for booklibrary.services.

Covers create_book_from_google_data() and its private helpers
_parse_published_date() and _get_or_create_author().
"""
import pytest
from datetime import datetime

from booklibrary.models import Author, Book, BookInstance, Genre, Language
from booklibrary.services import (
    _get_or_create_author,
    _parse_published_date,
    create_book_from_google_data,
)

from .conftest import (
    GenreFactory,
    KeywordsFactory,
    LanguageFactory,
    LocationFactory,
    SeriesFactory,
    UserFactory,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _fake_book_data(**overrides):
    """Minimal Google Books volume dict (all fields present)."""
    defaults = {
        "title":          "Test Book",
        "author1":        "Jane Author",
        "author2":        None,
        "publisher":      "Test Pub",
        "published_date": "2020",
        "description":    "A test description.",
        "genre1":         None,
        "genre2":         None,
        "language":       "en",
        "preview_link":   "https://preview.example.com",
        "image_link":     "https://image.example.com",
        "volume_id":      "VOL-001",
        "is_owned":       False,
    }
    return {**defaults, **overrides}


def _fake_cleaned_data(**overrides):
    """Minimal AddForm cleaned_data."""
    defaults = {
        "book_genre":     Genre.objects.none(),
        "book_location":  None,
        "book_keywords":  None,
        "book_series":    None,
    }
    return {**defaults, **overrides}


# ── _parse_published_date ─────────────────────────────────────────────────────

class TestParsePublishedDate:

    def test_four_char_year(self):
        result = _parse_published_date("2023")
        assert result == datetime(2023, 1, 1)

    def test_seven_char_year_month(self):
        result = _parse_published_date("2023-07")
        assert result == datetime(2023, 7, 1)

    def test_full_date(self):
        result = _parse_published_date("2023-07-15")
        assert result == datetime(2023, 7, 15)

    def test_not_present_returns_datetime(self):
        result = _parse_published_date("Not Present")
        assert isinstance(result, datetime)

    def test_empty_string_returns_none(self):
        assert _parse_published_date("") is None

    def test_non_string_returns_none(self):
        assert _parse_published_date(None) is None
        assert _parse_published_date(2023) is None

    def test_invalid_format_returns_none(self):
        assert _parse_published_date("15/07/2023") is None
        assert _parse_published_date("not-a-date") is None


# ── _get_or_create_author ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGetOrCreateAuthor:

    def test_creates_new_author(self):
        author = _get_or_create_author("Isaac Asimov")
        assert Author.objects.filter(last_name="Asimov").exists()
        assert author.first_name == "Isaac"
        assert author.last_name == "Asimov"

    def test_returns_existing_author(self):
        _get_or_create_author("Isaac Asimov")
        _get_or_create_author("Isaac Asimov")
        assert Author.objects.filter(last_name="Asimov").count() == 1

    def test_normalizes_accented_characters(self):
        author = _get_or_create_author("Ångström Björk")
        assert author.first_name == "Angstrom"
        assert author.last_name == "Bjork"


# ── create_book_from_google_data ──────────────────────────────────────────────

@pytest.mark.django_db
class TestCreateBookFromGoogleData:

    def test_creates_book_with_correct_fields(self):
        user = UserFactory()
        book, _ = create_book_from_google_data(
            _fake_book_data(title="Dune", volume_id="dune-1"),
            _fake_cleaned_data(),
            user,
        )
        assert book.title == "Dune"
        assert book.uniqueID == "dune-1"
        assert book.summary == "A test description."
        assert book.publisher == "Test Pub"
        assert book.contentType == "PHY"

    def test_returns_created_true_for_new_book(self):
        user = UserFactory()
        _, created = create_book_from_google_data(
            _fake_book_data(), _fake_cleaned_data(), user
        )
        assert created is True

    def test_returns_created_false_for_duplicate_volume_id(self):
        user = UserFactory()
        data = _fake_book_data(volume_id="dup-1")
        create_book_from_google_data(data, _fake_cleaned_data(), UserFactory())
        _, created = create_book_from_google_data(data, _fake_cleaned_data(), user)
        assert created is False

    def test_creates_book_instance_owned_by_user(self):
        user = UserFactory()
        book, _ = create_book_from_google_data(
            _fake_book_data(volume_id="bi-1"), _fake_cleaned_data(), user
        )
        assert BookInstance.objects.filter(book=book, owner=user).exists()

    def test_creates_book_instance_at_location(self):
        user = UserFactory()
        location = LocationFactory()
        book, _ = create_book_from_google_data(
            _fake_book_data(volume_id="loc-1"),
            _fake_cleaned_data(book_location=location),
            user,
        )
        assert BookInstance.objects.filter(book=book, location=location).exists()

    def test_adds_author1_to_book(self):
        user = UserFactory()
        book, _ = create_book_from_google_data(
            _fake_book_data(author1="Frank Herbert", volume_id="auth-1"),
            _fake_cleaned_data(),
            user,
        )
        assert book.authors.filter(last_name="Herbert").exists()

    def test_adds_author2_when_present(self):
        user = UserFactory()
        book, _ = create_book_from_google_data(
            _fake_book_data(author1="First Author", author2="Second Author", volume_id="auth-2"),
            _fake_cleaned_data(),
            user,
        )
        assert book.authors.count() == 2

    def test_skips_none_author(self):
        user = UserFactory()
        book, _ = create_book_from_google_data(
            _fake_book_data(author1=None, author2=None, volume_id="auth-3"),
            _fake_cleaned_data(),
            user,
        )
        assert book.authors.count() == 0

    def test_adds_genre1_from_book_data(self):
        user = UserFactory()
        book, _ = create_book_from_google_data(
            _fake_book_data(genre1="Science Fiction", volume_id="genre-1"),
            _fake_cleaned_data(),
            user,
        )
        assert book.genre.filter(name="Science Fiction").exists()

    def test_adds_genre2_from_book_data(self):
        user = UserFactory()
        book, _ = create_book_from_google_data(
            _fake_book_data(genre1="Fiction", genre2="Adventure", volume_id="genre-2"),
            _fake_cleaned_data(),
            user,
        )
        genre_names = set(book.genre.values_list("name", flat=True))
        assert {"Fiction", "Adventure"} <= genre_names

    def test_adds_form_genres_from_cleaned_data(self):
        user = UserFactory()
        g1 = GenreFactory(name="Horror")
        g2 = GenreFactory(name="Thriller")
        book, _ = create_book_from_google_data(
            _fake_book_data(volume_id="genre-3"),
            _fake_cleaned_data(book_genre=Genre.objects.filter(pk__in=[g1.pk, g2.pk])),
            user,
        )
        genre_names = set(book.genre.values_list("name", flat=True))
        assert {"Horror", "Thriller"} <= genre_names

    def test_sets_language(self):
        user = UserFactory()
        book, _ = create_book_from_google_data(
            _fake_book_data(language="French", volume_id="lang-1"),
            _fake_cleaned_data(),
            user,
        )
        assert book.language is not None
        assert book.language.name == "French"

    def test_skips_none_language(self):
        user = UserFactory()
        book, _ = create_book_from_google_data(
            _fake_book_data(language=None, volume_id="lang-2"),
            _fake_cleaned_data(),
            user,
        )
        assert book.language is None

    def test_sets_series_from_cleaned_data(self):
        user = UserFactory()
        series = SeriesFactory(name="Foundation")
        book, _ = create_book_from_google_data(
            _fake_book_data(volume_id="series-1"),
            _fake_cleaned_data(book_series=series),
            user,
        )
        assert book.series == series

    def test_adds_keywords_from_cleaned_data(self):
        from booklibrary.models import Keywords
        user = UserFactory()
        kw1 = KeywordsFactory(name="space opera")
        kw2 = KeywordsFactory(name="dystopia")
        book, _ = create_book_from_google_data(
            _fake_book_data(volume_id="kw-1"),
            _fake_cleaned_data(
                book_keywords=Keywords.objects.filter(pk__in=[kw1.pk, kw2.pk])
            ),
            user,
        )
        assert book.keywords.filter(name="space opera").exists()
        assert book.keywords.filter(name="dystopia").exists()

    def test_published_date_is_parsed(self):
        user = UserFactory()
        book, _ = create_book_from_google_data(
            _fake_book_data(published_date="1965", volume_id="date-1"),
            _fake_cleaned_data(),
            user,
        )
        assert book.publishedDate is not None

    def test_duplicate_volume_id_reuses_existing_book(self):
        user = UserFactory()
        data = _fake_book_data(title="Original Title", volume_id="reuse-1")
        book1, _ = create_book_from_google_data(data, _fake_cleaned_data(), UserFactory())
        book2, _ = create_book_from_google_data(data, _fake_cleaned_data(), user)
        assert book1.pk == book2.pk
        assert Book.objects.filter(uniqueID="reuse-1").count() == 1
