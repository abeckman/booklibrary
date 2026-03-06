"""
Views for the booklibrary app.

Browse / search
---------------
index               Home page with aggregate counts and a per-session visit counter.
BookListView        Paginated book catalogue with multi-field search and duplicate detection.
BookDetailView      Single-book detail page with a paginated list of physical copies.
BookSearchView      Google Books search form; stores results server-side and renders AddForm.
AuthorListView      Paginated author directory with last-name search.
AuthorDetailView    Single-author detail page.
GenreListView       Paginated genre directory with name search.
LocationListView    Paginated location directory with name search.
LocationDetailView  Location detail page listing all BookInstances held there.

Add / edit / delete  (login or permission required)
----------------------------------------------------
add_book                    Save a book chosen from Google Books results (login required).
AuthorCreate/Update/Delete  Author CRUD.
LocationCreate/Update/Delete Location CRUD.
BookUpdate/Delete           Book CRUD; non-superusers restricted to books they own.
BookInstanceUpdate/Delete   BookInstance CRUD; restricted to the instance owner.

Internal helpers
----------------
SearchableListView      Reusable ListView base with single-field search and pagination.
BookOwnerQuerysetMixin  Limits book querysets to the current owner (or all for superusers).
_parse_published_date   Normalises Google Books date strings to datetime objects.
_get_or_create_author   Deduplicates authors by normalised, accent-stripped name.

Security note
-------------
add_book reads all book data (title, authors, etc.) from the server-side session
(``request.session['google_books_results']``), not from submitted form fields, to
prevent client-side tampering.  The AddForm controls only user choices: genre,
location, keywords, and series.
"""
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from booklibrary.models import Book, Author, BookInstance, Genre, Language, Keywords, Location, Series
from booklibrary.owner import OwnerUpdateView, OwnerDeleteView
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from nameparser import HumanName
import unidecode
from django.contrib import messages
from django.views.generic import TemplateView
from django.template.response import TemplateResponse
from .forms import SearchForm, AddForm
from .utils.pagination import paginate_queryset
import logging
from django.conf import settings
from .utils.google_books import (
    search_books,
    GoogleBooksError,
    GoogleBooksQuotaError,
    GoogleBooksAuthError,
    GoogleBooksBadRequest,
)

# The base code source for my work is based on:
# https://github.com/mdn/django-locallibrary-tutorial

logger = logging.getLogger(__name__)

PAGE_SIZE = getattr(settings, "PAGE_SIZE", 24)

def index(request):
    """Home page: aggregate book/instance/author counts and a per-session visit counter."""
    num_books = Book.objects.count()
    num_instances = BookInstance.objects.count()
    num_authors = Author.objects.count()

    num_visits = request.session.get('num_visits', 0)
    num_visits += 1
    request.session['num_visits'] = num_visits

    return render(request, 'index.html', {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_authors': num_authors,
        'num_visits': num_visits,
    })

class BookListView(generic.ListView):
    """
    Paginated catalogue of all books.

    Accepts optional GET parameters:
      search  – text to search for.
      fields  – field to search: title (default, also searches summary), author,
                genre, series, or keyword.
      dups    – if present, shows only books that have more than one copy.
    """

    model = Book
    template_name = "booklibrary/book_list.html"
    paginate_by = PAGE_SIZE

    _FIELD_QUERIES = {
        "title": lambda s: Q(title__icontains=s) | Q(summary__icontains=s),
        "author": lambda s: (
            Q(authors__last_name__icontains=s)
            | Q(authors__first_name__icontains=s)
            | Q(authors__full_name__icontains=s)
        ),
        "genre": lambda s: Q(genre__name__icontains=s),
        "series": lambda s: Q(series__name__icontains=s),
        "keyword": lambda s: Q(keywords__name__icontains=s),
    }

    def get_queryset(self):
        if self.request.GET.get("dups"):
            return Book.objects.with_counts().filter(num_copies__gt=1).order_by("title")

        qs = Book.objects.select_related().order_by("title")
        search = self.request.GET.get("search", "").strip()
        if not search:
            return qs

        field = self.request.GET.get("fields") or "title"
        build_query = self._FIELD_QUERIES.get(field)
        if build_query is None:
            return qs
        return qs.filter(build_query(search)).distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search"] = self.request.GET.get("search", "").strip() or None
        ctx["fields"] = self.request.GET.get("fields", "")
        ctx["dups"] = self.request.GET.get("dups", "")
        return ctx

class SearchableListView(generic.ListView):
    """
    Base ListView with optional single-field case-insensitive search and pagination.

    Subclasses set ``search_field`` to control which model field is filtered
    (default: ``"name"``).  The raw search string is exposed in context as
    ``search`` so templates can repopulate the search input.
    """

    search_field = "name"
    paginate_by = PAGE_SIZE

    def get_search_value(self):
        return self.request.GET.get("search", "").strip() or None

    def get_queryset(self):
        qs = super().get_queryset().select_related().order_by(self.search_field)
        search = self.get_search_value()
        if search:
            qs = qs.filter(**{f"{self.search_field}__icontains": search})
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search"] = self.get_search_value()
        return ctx


class GenreListView(SearchableListView):
    """Paginated, searchable list of genres."""

    model = Genre
    template_name = "booklibrary/genre_list.html"


class BookDetailView(generic.DetailView):
    """Single-book detail page. Adds a paginated list of physical copies to context."""

    model = Book

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        instances = self.object.bookinstance_set.order_by('location')
        ctx['page_obj'] = paginate_queryset(self.request, instances, PAGE_SIZE)
        return ctx


class BookSearchView(TemplateView):
    """
    Two-phase Google Books search.

    GET  – renders an empty search form.
    POST – submits the query to the Google Books API.  On success, results are
           stored in ``request.session['google_books_results']`` and the results
           template is rendered with an AddForm pre-populated from the user's
           last-used genre.  On failure, an appropriate error message is shown
           and the search form is re-rendered.
    """

    template_name = 'booklibrary/book_search.html'

    def get_context_data(self, **kwargs):
        kwargs.setdefault('form', SearchForm())
        return super().get_context_data(**kwargs)

    def post(self, request):
        form = SearchForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        books, total = self._fetch_books(request, form.cleaned_data['search'])
        if not books:
            messages.info(request, 'Google did not return anything, try again')
            return self.render_to_response(self.get_context_data(form=form))

        request.session['google_books_results'] = books
        return TemplateResponse(request, 'booklibrary/book_results.html', {
            'form': self._build_add_form(request),
            'books': books,
            'total': total,
        })

    def _fetch_books(self, request, query):
        """Call Google Books API, message any errors, and return (books, total)."""
        try:
            return search_books(query, max_results=10)
        except GoogleBooksQuotaError:
            messages.error(request,
                "Google Books is receiving too many requests right now. "
                "Please wait a bit and try again.")
        except GoogleBooksAuthError:
            messages.error(request,
                "Search is temporarily unavailable due to a configuration problem.")
        except GoogleBooksBadRequest:
            messages.error(request,
                "That search could not be sent to Google. Try a simpler query.")
        except GoogleBooksError:
            messages.error(request,
                "There was an unexpected error talking to Google Books. Please try again.")
        return [], 0

    def _build_add_form(self, request):
        """Return an AddForm pre-populated with the user's last-used genre."""
        saved_genre = request.session.get('repeat_genre')
        genre_obj = Genre.objects.filter(name=saved_genre).first() if saved_genre else None
        genre_initial = [genre_obj.id] if genre_obj else []
        return AddForm(initial={'book_genre': genre_initial})

class AuthorListView(SearchableListView):
    """
    Paginated author directory with last-name search.

    Accepts an optional ``author_location`` GET parameter; when present it sets
    ``request.session["location"] = True`` to signal the author detail template
    to display location information for each author's books.
    """

    model = Author
    template_name = "booklibrary/author_list.html"
    search_field = "last_name"

    def get(self, request, *args, **kwargs):
        request.session["location"] = bool(request.GET.get("author_location"))
        return super().get(request, *args, **kwargs)


class AuthorDetailView(generic.DetailView):
    """Single-author detail page."""

    model = Author


class LocationListView(SearchableListView):
    """Paginated, searchable list of locations."""

    model = Location
    template_name = "booklibrary/location_list.html"


class LocationDetailView(generic.DetailView):
    """Location detail page. Adds a paginated list of BookInstances held at this location."""

    model = Location
    template_name = "booklibrary/location_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        instances = BookInstance.objects.filter(location=self.object).order_by('book')
        ctx['page_obj'] = paginate_queryset(self.request, instances, PAGE_SIZE)
        return ctx


def _parse_published_date(value):
    """Normalize a Google Books date string to a datetime, or None."""
    if not isinstance(value, str) or not value:
        return None
    if value == "Not Present":
        return datetime.now()
    if len(value) == 4:
        return datetime(int(value), 1, 1)
    if len(value) == 7:
        return datetime(int(value[:4]), int(value[5:7]), 1)
    return value  # full date string — pass through unchanged


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


@login_required
def add_book(request):
    """
    Save a book chosen from Google Books search results (login required).

    Expects a POST containing:
      book_index  – integer index into ``request.session['google_books_results']``.
      AddForm fields – Book_Genre, Book_Location, Book_Keywords, Book_Series.

    Book data (title, authors, genres, etc.) is read from the server-side session,
    not from submitted form fields, to prevent client-side tampering.  The form
    controls only the user's local choices (location, extra genres, keywords, series).

    On success, creates a Book (or finds the existing one by uniqueID), attaches
    related objects, creates a BookInstance owned by the current user, and redirects
    to the book detail page.
    """
    if request.method != 'POST':
        return render(request, 'booklibrary/book_search.html', {'form': AddForm()})

    form = AddForm(request.POST)
    if not form.is_valid():
        logger.warning("add_book: form invalid: %s", form.errors)
        return render(request, 'booklibrary/book_results.html', {'form': form})

    cd = form.cleaned_data

    try:
        book_index = int(request.POST.get('book_index', ''))
        book_data = request.session['google_books_results'][book_index]
    except (ValueError, TypeError, KeyError, IndexError):
        messages.error(request, "Invalid book selection. Please search again.")
        return redirect('booklibrary:book-search')

    location = cd['book_location']

    (
        title, author1, author2, publisher, published_on,
        description, genre1, genre2, language,
        preview_link, image_link, unique_id, status,
    ) = book_data

    published_on = _parse_published_date(published_on)

    logger.debug(
        "add_book: title=%r author1=%r author2=%r publisher=%r published=%r "
        "genre1=%r genre2=%r language=%r uniqueID=%r status=%r "
        "form_genre=%r location=%r keywords=%r series=%r",
        title, author1, author2, publisher, published_on,
        genre1, genre2, language, unique_id, status,
        cd['book_genre'], location, cd['book_keywords'], cd['book_series'],
    )

    book, created = Book.objects.get_or_create(
        uniqueID=unique_id,
        defaults=dict(
            title=title, summary=description, publisher=publisher,
            publishedDate=published_on, previewLink=preview_link,
            imageLink=image_link, contentType="PH",
        ),
    )
    if not created:
        messages.info(request, 'Duplicate book')

    for name in [author1, author2]:
        if name and name != "None":
            book.authors.add(_get_or_create_author(name))

    for genre_name in [genre1, genre2]:
        if genre_name and genre_name != "None":
            genre_obj, _ = Genre.objects.get_or_create(name=genre_name)
            book.genre.add(genre_obj)

    if cd['book_genre']:
        book.genre.add(*cd['book_genre'])
        first_genre = cd['book_genre'].first()
        if first_genre:
            request.session['repeat_genre'] = first_genre.name

    if language and language != "None":
        lang_obj, _ = Language.objects.get_or_create(name=language)
        book.language = lang_obj

    if cd['book_series']:
        book.series = cd['book_series']

    if cd['book_keywords']:
        book.keywords.add(cd['book_keywords'])

    book.save()

    BookInstance.objects.create(owner=request.user, book=book, location=location)
    return redirect('booklibrary:book-detail', pk=book.pk)


class AuthorCreate(LoginRequiredMixin, CreateView):
    """Create a new author (login required)."""

    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_death': '11/06/2020'}


class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    """Update an existing author (permission required)."""

    model = Author
    fields = ['full_name', 'first_name', 'last_name', 'date_of_birth', 'date_of_death']
    permission_required = 'booklibrary.author.can_change_author'


class AuthorDelete(PermissionRequiredMixin, DeleteView):
    """Delete an author (permission required)."""

    model = Author
    success_url = reverse_lazy('booklibrary:authors')
    permission_required = 'booklibrary.author.can_delete_author'


class LocationCreate(LoginRequiredMixin, CreateView):
    """Create a new location (login required)."""

    model = Location
    fields = ['name']


class LocationUpdate(PermissionRequiredMixin, UpdateView):
    """Update a location name (permission required)."""

    model = Location
    fields = ['name']
    permission_required = 'booklibrary.location.can_change_location'


class LocationDelete(PermissionRequiredMixin, DeleteView):
    """Delete a location (permission required)."""

    model = Location
    success_url = reverse_lazy('booklibrary:locations')
    permission_required = 'booklibrary.location.can_delete_location'


class BookOwnerQuerysetMixin:
    """
    Mixin that restricts the book queryset to books owned by the current user.

    Superusers bypass the restriction and see all books.  Applied to BookUpdate
    and BookDelete so non-superusers cannot edit or delete books they do not own.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_superuser:
            return qs
        return qs.filter(bookinstance__owner=self.request.user).distinct()


class BookUpdate(BookOwnerQuerysetMixin, PermissionRequiredMixin, UpdateView):
    """Update book metadata. Non-superusers may only edit books they own."""

    model = Book
    fields = ['title', 'authors', 'summary', 'genre', 'language', 'publisher', 'publishedDate', 'keywords', 'series']
    permission_required = 'booklibrary.change_book'


class BookDelete(BookOwnerQuerysetMixin, PermissionRequiredMixin, DeleteView):
    """Delete a book. Non-superusers may only delete books they own."""

    model = Book
    success_url = reverse_lazy('booklibrary:books')
    permission_required = 'booklibrary.delete_book'


class BookInstanceUpdate(OwnerUpdateView):
    """Update the location of a physical copy (owner only)."""

    model = BookInstance
    success_url = reverse_lazy('booklibrary:books')
    fields = ['location']


class BookInstanceDelete(OwnerDeleteView):
    """Delete a physical copy (owner only)."""

    model = BookInstance
    success_url = reverse_lazy('booklibrary:books')


def get_ip(request):
    """Return the client's IP address as a plain-text response (diagnostic utility)."""
    return HttpResponse(request.META['REMOTE_ADDR'])


