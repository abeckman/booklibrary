"""
Business-logic service for persisting Google Books results.

Public interface
----------------
create_book_from_google_data(book_data, cleaned_data, user)
    Create (or locate) a Book from a Google Books volume dict and an
    AddForm's cleaned_data, then attach a BookInstance owned by user.
    Returns (Book, created: bool).
"""
import logging
from datetime import datetime

import unidecode
from nameparser import HumanName

from booklibrary.models import Author, Book, BookInstance, Genre, Language

logger = logging.getLogger(__name__)


def _parse_published_date(value):
    """Normalize a Google Books date string to a datetime.datetime, or None."""
    if not isinstance(value, str) or not value:
        return None
    if value == "Not Present":
        return datetime.now()
    if len(value) == 4:
        return datetime(int(value), 1, 1)
    if len(value) == 7:
        return datetime(int(value[:4]), int(value[5:7]), 1)
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def _get_or_create_author(full_name):
    """Look up or create an Author by full name, normalising accented characters."""
    parsed = HumanName(full_name)
    first = unidecode.unidecode(parsed.first)
    last = unidecode.unidecode(parsed.last)
    author, _ = Author.objects.filter(
        first_name__icontains=first,
        last_name__icontains=last,
    ).get_or_create(full_name=full_name, first_name=first, last_name=last)
    return author


def create_book_from_google_data(book_data, cleaned_data, user):
    """
    Persist a Google Books result as a Book + BookInstance owned by user.

    Parameters
    ----------
    book_data : dict
        A volume dict as returned by search_books() (title, author1, author2,
        publisher, published_date, description, genre1, genre2, language,
        preview_link, image_link, volume_id).
    cleaned_data : dict
        Validated data from AddForm (book_genre, book_location, book_keywords,
        book_series).
    user : User
        The authenticated user who will own the new BookInstance.

    Returns
    -------
    (Book, bool)
        The Book instance and a created flag (True = newly inserted row).
    """
    published_on = _parse_published_date(book_data["published_date"])

    book, created = Book.objects.get_or_create(
        uniqueID=book_data["volume_id"],
        defaults=dict(
            title=book_data["title"],
            summary=book_data["description"],
            publisher=book_data["publisher"],
            publishedDate=published_on,
            previewLink=book_data["preview_link"],
            imageLink=book_data["image_link"],
            contentType="PHY",
        ),
    )

    for name in [book_data["author1"], book_data["author2"]]:
        if name:
            book.authors.add(_get_or_create_author(name))

    for genre_name in [book_data["genre1"], book_data["genre2"]]:
        if genre_name:
            genre_obj, _ = Genre.objects.get_or_create(name=genre_name)
            book.genre.add(genre_obj)

    if cleaned_data["book_genre"]:
        book.genre.add(*cleaned_data["book_genre"])

    language = book_data["language"]
    if language:
        lang_obj, _ = Language.objects.get_or_create(name=language)
        book.language = lang_obj

    if cleaned_data["book_series"]:
        book.series = cleaned_data["book_series"]

    if cleaned_data["book_keywords"]:
        book.keywords.add(*cleaned_data["book_keywords"])

    book.save()

    BookInstance.objects.create(
        owner=user,
        book=book,
        location=cleaned_data["book_location"],
    )

    return book, created
