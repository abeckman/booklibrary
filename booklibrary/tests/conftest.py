"""
Shared factories and pytest fixtures for the booklibrary test suite.

Factories mirror those in test_models.py so that test_views.py, test_forms.py,
and test_google_books.py can use them without circular imports.
"""
import pytest
import factory
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory

from booklibrary.models import (
    Author, Book, BookInstance, Genre, Keywords, Language, Location, Series,
)

User = get_user_model()


# ── Factories ─────────────────────────────────────────────────────────────────

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


# ── Request helpers ───────────────────────────────────────────────────────────

def add_session(request, data=None):
    """Attach a working DB-backed session to a RequestFactory request."""
    session = SessionStore()
    if data:
        session.update(data)
    session.save()
    request.session = session
    return request


def add_messages(request):
    """Attach a FallbackStorage message backend to a RequestFactory request."""
    request._messages = FallbackStorage(request)
    return request


def setup_request(request, user=None, session_data=None):
    """One-shot helper: attach session, messages, and user to a request."""
    from django.contrib.auth.models import AnonymousUser
    request.user = user if user is not None else AnonymousUser()
    add_session(request, session_data)
    add_messages(request)
    return request


# ── Pytest fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def other_user(db):
    return UserFactory()


@pytest.fixture
def genre(db):
    return GenreFactory()


@pytest.fixture
def language(db):
    return LanguageFactory()


@pytest.fixture
def location(db):
    return LocationFactory()


@pytest.fixture
def series(db):
    return SeriesFactory()


@pytest.fixture
def author(db):
    return AuthorFactory()


@pytest.fixture
def book(db):
    return BookFactory()


@pytest.fixture
def book_instance(db, user):
    return BookInstanceFactory(owner=user)
