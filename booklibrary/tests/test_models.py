import pytest
import uuid
from datetime import date
from unittest.mock import patch

import factory
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from booklibrary.models import (
    Genre, Keywords, Language, Location, Series,
    Book, BookInstance, Author, BookManager,
)

User = get_user_model()


# ──────────────────────────────────────────────────────────────
# Factories
# ──────────────────────────────────────────────────────────────

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class GenreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Genre

    name = factory.Sequence(lambda n: f"Genre {n}")


class KeywordsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Keywords

    name = factory.Sequence(lambda n: f"Keyword {n}")


class LanguageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Language

    name = "English"


class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Location

    name = factory.Sequence(lambda n: f"Shelf {n}")


class SeriesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Series

    name = factory.Sequence(lambda n: f"Series {n}")


class AuthorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Author

    full_name = factory.LazyAttribute(lambda o: f"{o.first_name} {o.last_name}")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    date_of_birth = None
    date_of_death = None


class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book
        skip_postgeneration_save = True

    title = factory.Sequence(lambda n: f"Book Title {n}")
    summary = factory.Faker("paragraph")
    publisher = "Test Publisher"
    publishedDate = date(2020, 1, 1)
    language = factory.SubFactory(LanguageFactory)
    series = factory.SubFactory(SeriesFactory)
    previewLink = "https://example.com/preview"
    imageLink = "https://example.com/image.jpg"
    uniqueID = factory.Sequence(lambda n: f"UID-{n}")
    contentType = "PHY"

    @factory.post_generation
    def authors(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for author in extracted:
                self.authors.add(author)

    @factory.post_generation
    def genre(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for g in extracted:
                self.genre.add(g)

    @factory.post_generation
    def keywords(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for kw in extracted:
                self.keywords.add(kw)


class BookInstanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BookInstance

    book = factory.SubFactory(BookFactory)
    location = factory.SubFactory(LocationFactory)
    owner = factory.SubFactory(UserFactory)


# ──────────────────────────────────────────────────────────────
# Genre Tests
# ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGenre:

    def test_create_genre(self):
        genre = GenreFactory(name="Science Fiction")
        assert genre.pk is not None
        assert genre.name == "Science Fiction"

    def test_str_representation(self):
        genre = GenreFactory(name="Fantasy")
        assert str(genre) == "Fantasy"

    def test_name_max_length(self):
        genre = GenreFactory()
        max_length = genre._meta.get_field("name").max_length
        assert max_length == 200

    def test_name_exceeds_max_length(self):
        """CharField enforces max_length at DB level on some backends."""
        long_name = "A" * 201
        genre = GenreFactory.build(name=long_name)
        with pytest.raises(ValidationError):
            genre.full_clean()

    def test_empty_name_fails_validation(self):
        genre = GenreFactory.build(name="")
        with pytest.raises(ValidationError):
            genre.full_clean()


# ──────────────────────────────────────────────────────────────
# Keywords Tests
# ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestKeywords:

    def test_create_keyword(self):
        kw = KeywordsFactory(name="Climbing")
        assert kw.pk is not None
        assert kw.name == "Climbing"

    def test_default_value(self):
        kw = Keywords.objects.create()
        assert kw.name == "None"

    def test_str_representation(self):
        kw = KeywordsFactory(name="Knitting")
        assert str(kw) == "Knitting"

    def test_name_max_length(self):
        assert Keywords._meta.get_field("name").max_length == 200


# ──────────────────────────────────────────────────────────────
# Language Tests
# ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLanguage:

    def test_create_language(self):
        lang = LanguageFactory(name="French")
        assert lang.name == "French"

    def test_default_value(self):
        lang = Language.objects.create()
        assert lang.name == "English"

    def test_str_representation(self):
        lang = LanguageFactory(name="Japanese")
        assert str(lang) == "Japanese"


# ──────────────────────────────────────────────────────────────
# Location Tests
# ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLocation:

    def test_create_location(self):
        loc = LocationFactory(name="Hallway Bookcase")
        assert loc.name == "Hallway Bookcase"

    def test_str_representation(self):
        loc = LocationFactory(name="Tub 101")
        assert str(loc) == "Tub 101"

    def test_empty_name_fails_validation(self):
        loc = LocationFactory.build(name="")
        with pytest.raises(ValidationError):
            loc.full_clean()


# ──────────────────────────────────────────────────────────────
# Series Tests
# ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSeries:

    def test_create_series(self):
        series = SeriesFactory(name="Foundation")
        assert series.name == "Foundation"

    def test_default_value(self):
        series = Series.objects.create()
        assert series.name == "None"

    def test_str_representation(self):
        series = SeriesFactory(name="Dune")
        assert str(series) == "Dune"


# ──────────────────────────────────────────────────────────────
# Author Tests
# ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAuthor:

    def test_create_author(self):
        author = AuthorFactory(first_name="Isaac", last_name="Asimov")
        assert author.pk is not None
        assert author.first_name == "Isaac"
        assert author.last_name == "Asimov"

    def test_str_representation(self):
        author = AuthorFactory(first_name="Isaac", last_name="Asimov")
        assert str(author) == "Asimov, Isaac"

    def test_str_with_none_last_name(self):
        author = AuthorFactory(first_name="Cher", last_name=None)
        assert str(author) == "None, Cher"

    def test_get_absolute_url(self):
        author = AuthorFactory()
        expected_url = f"/booklibrary/author/{author.pk}"
        # Adjust URL pattern to your actual urls.py
        assert author.get_absolute_url() == expected_url

    def test_ordering(self):
        a1 = AuthorFactory(first_name="Zelda", last_name="Beta")
        a2 = AuthorFactory(first_name="Alpha", last_name="Alpha")
        a3 = AuthorFactory(first_name="Beta", last_name="Alpha")
        authors = list(Author.objects.filter(pk__in=[a1.pk, a2.pk, a3.pk]))
        assert authors == [a2, a3, a1]

    def test_full_name_optional(self):
        author = AuthorFactory(full_name=None)
        assert author.full_name is None

    def test_dates_optional(self):
        author = AuthorFactory(date_of_birth=None, date_of_death=None)
        assert author.date_of_birth is None
        assert author.date_of_death is None

    def test_dates_populated(self):
        author = AuthorFactory(
            date_of_birth=date(1920, 1, 2),
            date_of_death=date(1992, 4, 6),
        )
        assert author.date_of_birth == date(1920, 1, 2)
        assert author.date_of_death == date(1992, 4, 6)

    def test_first_name_max_length(self):
        assert Author._meta.get_field("first_name").max_length == 100

    def test_last_name_max_length(self):
        assert Author._meta.get_field("last_name").max_length == 100


# ──────────────────────────────────────────────────────────────
# Book Tests
# ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBook:

    def test_create_book(self):
        book = BookFactory(title="Dune")
        assert book.pk is not None
        assert book.title == "Dune"

    def test_str_representation(self):
        book = BookFactory(title="Neuromancer")
        assert str(book) == "Neuromancer"

    def test_title_min_length_validator(self):
        """Title with MinLengthValidator(1) should reject empty strings."""
        book = BookFactory.build(title="")
        with pytest.raises(ValidationError):
            book.full_clean()

    def test_title_max_length(self):
        assert Book._meta.get_field("title").max_length == 200

    def test_title_at_max_boundary(self):
        book = BookFactory(title="A" * 200)
        book.full_clean()  # should not raise
        assert len(book.title) == 200

    def test_ordering(self):
        b1 = BookFactory(title="Zebra")
        b2 = BookFactory(title="Alpha")
        books = list(Book.objects.filter(pk__in=[b1.pk, b2.pk]))
        assert books == [b2, b1]

    def test_get_absolute_url(self):
        book = BookFactory()
        expected = f"/booklibrary/book/{book.pk}"
        # Adjust to match your actual URL conf
        assert book.get_absolute_url() == expected

    def test_summary_nullable(self):
        book = BookFactory(summary=None)
        assert book.summary is None

    def test_publisher_nullable(self):
        book = BookFactory(publisher=None)
        assert book.publisher is None

    def test_published_date_nullable(self):
        book = BookFactory(publishedDate=None)
        assert book.publishedDate is None

    def test_preview_link_nullable(self):
        book = BookFactory(previewLink=None)
        assert book.previewLink is None

    def test_image_link_nullable(self):
        book = BookFactory(imageLink=None)
        assert book.imageLink is None

    def test_unique_id_nullable(self):
        book = BookFactory(uniqueID=None)
        assert book.uniqueID is None

    def test_content_type_nullable(self):
        book = BookFactory(contentType=None)
        assert book.contentType is None

    def test_invalid_preview_link(self):
        book = BookFactory.build(previewLink="not-a-url")
        with pytest.raises(ValidationError):
            book.full_clean()

    def test_invalid_image_link(self):
        book = BookFactory.build(imageLink="not-a-url")
        with pytest.raises(ValidationError):
            book.full_clean()

    # ── M2M: Authors ──

    def test_add_authors(self):
        a1 = AuthorFactory(first_name="Frank", last_name="Herbert")
        a2 = AuthorFactory(first_name="Brian", last_name="Herbert")
        book = BookFactory(authors=[a1, a2])
        assert book.authors.count() == 2

    def test_reverse_relation_books(self):
        author = AuthorFactory()
        book = BookFactory(authors=[author])
        assert book in author.books.all()

    # ── M2M: Genre ──

    def test_add_genres(self):
        g1 = GenreFactory(name="Sci-Fi")
        g2 = GenreFactory(name="Adventure")
        book = BookFactory(genre=[g1, g2])
        assert book.genre.count() == 2

    # ── M2M: Keywords ──

    def test_add_keywords(self):
        kw1 = KeywordsFactory(name="Space")
        kw2 = KeywordsFactory(name="Desert")
        book = BookFactory(keywords=[kw1, kw2])
        assert book.keywords.count() == 2

    # ── FK: Language ──

    def test_language_set_null_on_delete(self):
        lang = LanguageFactory(name="Spanish")
        book = BookFactory(language=lang)
        lang.delete()
        book.refresh_from_db()
        assert book.language is None

    # ── FK: Series ──

    def test_series_set_null_on_delete(self):
        series = SeriesFactory(name="Ringworld")
        book = BookFactory(series=series)
        series.delete()
        book.refresh_from_db()
        assert book.series is None

    # ── display_genre ──

    def test_display_genre_empty(self):
        book = BookFactory()
        assert book.display_genre() == ""

    def test_display_genre_single(self):
        g = GenreFactory(name="Horror")
        book = BookFactory(genre=[g])
        assert book.display_genre() == "Horror"

    def test_display_genre_multiple(self):
        genres = [GenreFactory(name=n) for n in ["A", "B", "C"]]
        book = BookFactory(genre=genres)
        result = book.display_genre()
        # Should contain up to 3, comma-separated
        assert all(g.name in result for g in genres)

    def test_display_genre_truncates_at_three(self):
        genres = [GenreFactory(name=n) for n in ["A", "B", "C", "D"]]
        book = BookFactory(genre=genres)
        parts = book.display_genre().split(", ")
        assert len(parts) == 3

    def test_display_genre_short_description(self):
        assert Book.display_genre.short_description == "Genre"

    # ── display_authors ──

    def test_display_authors_empty(self):
        book = BookFactory()
        assert book.display_authors() == ""

    def test_display_authors_single(self):
        author = AuthorFactory(last_name="Asimov")
        book = BookFactory(authors=[author])
        assert book.display_authors() == "Asimov"

    def test_display_authors_multiple(self):
        a1 = AuthorFactory(last_name="Clarke")
        a2 = AuthorFactory(last_name="Bradbury")
        book = BookFactory(authors=[a1, a2])
        result = book.display_authors()
        assert "Clarke" in result
        assert "Bradbury" in result

    def test_display_authors_truncates_at_three(self):
        authors = [AuthorFactory(last_name=f"Author{i}") for i in range(4)]
        book = BookFactory(authors=authors)
        parts = book.display_authors().split(", ")
        assert len(parts) == 3

    def test_display_authors_short_description(self):
        assert Book.display_authors.short_description == "Authors"

    # ── bookinstance_count ──

    def test_bookinstance_count_zero(self):
        book = BookFactory()
        assert book.bookinstance_count() == 0

    def test_bookinstance_count_nonzero(self):
        book = BookFactory()
        BookInstanceFactory(book=book)
        BookInstanceFactory(book=book)
        assert book.bookinstance_count() == 2


# ──────────────────────────────────────────────────────────────
# BookManager Tests
# ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBookManager:

    def test_with_counts_no_instances(self):
        book = BookFactory()
        qs = Book.objects.with_counts().filter(pk=book.pk)
        assert qs.first().num_copies == 0

    def test_with_counts_with_instances(self):
        book = BookFactory()
        BookInstanceFactory.create_batch(3, book=book)
        qs = Book.objects.with_counts().filter(pk=book.pk)
        assert qs.first().num_copies == 3

    def test_with_counts_returns_queryset(self):
        BookFactory()
        qs = Book.objects.with_counts()
        assert hasattr(qs, "filter")  # confirm it's a QuerySet

    def test_with_counts_multiple_books(self):
        b1 = BookFactory()
        b2 = BookFactory()
        BookInstanceFactory.create_batch(2, book=b1)
        BookInstanceFactory.create_batch(5, book=b2)
        results = {
            b.pk: b.num_copies
            for b in Book.objects.with_counts().filter(pk__in=[b1.pk, b2.pk])
        }
        assert results[b1.pk] == 2
        assert results[b2.pk] == 5


# ──────────────────────────────────────────────────────────────
# BookInstance Tests
# ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestBookInstance:

    def test_create_instance(self):
        bi = BookInstanceFactory()
        assert bi.pk is not None
        assert isinstance(bi.id, uuid.UUID)

    def test_uuid_primary_key(self):
        bi = BookInstanceFactory()
        assert BookInstance.objects.get(pk=bi.pk) == bi

    def test_custom_uuid(self):
        custom_id = uuid.uuid4()
        bi = BookInstanceFactory(id=custom_id)
        assert bi.pk == custom_id

    def test_str_representation(self):
        book = BookFactory(title="Foundation")
        bi = BookInstanceFactory(book=book)
        assert str(bi) == f"{bi.id} (Foundation)"

    def test_book_cascade_delete(self):
        """Deleting a Book should cascade-delete its BookInstances."""
        book = BookFactory()
        bi = BookInstanceFactory(book=book)
        bi_pk = bi.pk
        book.delete()
        assert not BookInstance.objects.filter(pk=bi_pk).exists()

    def test_owner_cascade_delete(self):
        """Deleting the owner should cascade-delete their BookInstances."""
        user = UserFactory()
        bi = BookInstanceFactory(owner=user)
        bi_pk = bi.pk
        user.delete()
        assert not BookInstance.objects.filter(pk=bi_pk).exists()

    def test_location_set_null_on_delete(self):
        loc = LocationFactory()
        bi = BookInstanceFactory(location=loc)
        loc.delete()
        bi.refresh_from_db()
        assert bi.location is None

    def test_book_nullable(self):
        user = UserFactory()
        bi = BookInstance.objects.create(owner=user, book=None)
        assert bi.book is None

    def test_ordering_by_location(self):
        loc_a = LocationFactory(name="A-Shelf")
        loc_z = LocationFactory(name="Z-Shelf")
        user = UserFactory()
        bi1 = BookInstanceFactory(location=loc_z, owner=user)
        bi2 = BookInstanceFactory(location=loc_a, owner=user)
        instances = list(
            BookInstance.objects.filter(pk__in=[bi1.pk, bi2.pk])
        )
        assert instances == [bi2, bi1]

    def test_str_when_book_is_none(self):
        """Regression: __str__ must not crash when book=None."""
        user = UserFactory()
        bi = BookInstance.objects.create(owner=user, book=None)
        result = str(bi)
        assert "No book" in result

    def test_related_name_owner(self):
        user = UserFactory()
        bi = BookInstanceFactory(owner=user)
        assert bi in user.booklibrary_book_instance_owner.all()

    def test_multiple_instances_same_book(self):
        book = BookFactory()
        user = UserFactory()
        bi1 = BookInstanceFactory(book=book, owner=user)
        bi2 = BookInstanceFactory(book=book, owner=user)
        assert book.bookinstance_set.count() == 2


# ──────────────────────────────────────────────────────────────
# Cross-Model / Integration Tests
# ──────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCrossModelIntegration:

    def test_full_book_creation_with_all_relations(self):
        """End-to-end: create a book with all related objects."""
        author = AuthorFactory(first_name="Ursula", last_name="Le Guin")
        genre = GenreFactory(name="Science Fiction")
        keyword = KeywordsFactory(name="Aliens")
        lang = LanguageFactory(name="English")
        series = SeriesFactory(name="Hainish Cycle")

        book = BookFactory(
            title="The Left Hand of Darkness",
            authors=[author],
            genre=[genre],
            keywords=[keyword],
            language=lang,
            series=series,
        )
        user = UserFactory()
        bi = BookInstanceFactory(book=book, owner=user)

        # Validate everything links correctly
        assert book.authors.first() == author
        assert book.genre.first() == genre
        assert book.keywords.first() == keyword
        assert book.language == lang
        assert book.series == series
        assert bi.book == book
        assert bi.owner == user

    def test_author_with_multiple_books(self):
        author = AuthorFactory()
        b1 = BookFactory(authors=[author])
        b2 = BookFactory(authors=[author])
        assert author.books.count() == 2

    def test_deleting_genre_does_not_delete_book(self):
        genre = GenreFactory()
        book = BookFactory(genre=[genre])
        book_pk = book.pk
        genre.delete()
        assert Book.objects.filter(pk=book_pk).exists()
        assert book.genre.count() == 0

    def test_book_manager_is_bookmanager(self):
        """Ensure the custom manager is properly assigned."""
        assert isinstance(Book.objects, BookManager)
