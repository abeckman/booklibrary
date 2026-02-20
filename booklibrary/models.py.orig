from django.db import models # from catalog
from django.urls import reverse  # To generate URLS by reversing URL patterns, from catalog
from django.core.validators import MinLengthValidator
# from django.contrib.auth.models import User # from catalog - not used?
from django.conf import settings
import uuid  # Required for unique book instances - from catalog
# from datetime import date # from catalog
from django.db.models.functions import Coalesce # for model manager to add counts

# Added keywords, location and series

class Genre(models.Model): # all from catalog
    """Model representing a book genre (e.g. Science Fiction, Non Fiction)."""
    name = models.CharField(
        max_length=200,
        help_text="Enter a book genre (e.g. Science Fiction, French Poetry etc.)"
        )

    def __str__(self):
        """String for representing the Model object (in Admin site etc.)"""
        return self.name

class Keywords(models.Model):
    """Model representing key words (e.g. Climbing, Knitting, etc.)"""
    name = models.CharField(
        max_length=200,
        help_text="Enter key words (e.g. Climbing, Knitting, etc.)",
        default='None'
        )

    def __str__(self):
        """String for representing the Model object (in Admin site etc.)"""
        return self.name

class Language(models.Model): # all from catalog except default
    """Model representing a Language (e.g. English, French, Japanese, etc.)"""
    name = models.CharField(max_length=200,
        help_text="Enter the book's natural language (e.g. English, French, Japanese etc.)",
        default='English')

    def __str__(self):
        """String for representing the Model object (in Admin site etc.)"""
        return self.name

class Location(models.Model):
    """Model representing a Location (e.g. Hallway Bookcase, Tub 101, etc.)"""
    name = models.CharField(max_length=200,
            help_text="Enter a location where the book is located)")

    def __str__(self):
        """String for representing the Model object (in Admin site etc.)"""
        return self.name

class Series(models.Model):
    """Model representing a Series (e.g. Foundation, etc.)"""
    name = models.CharField(max_length=200,
            help_text="Enter a series name that the book is part of)",
            default='None')

    def __str__(self):
        """String for representing the Model object (in Admin site etc.)"""
        return self.name

class BookManager(models.Manager):
    def with_counts(self):
        return self.annotate(
            num_copies=Coalesce(models.Count("bookinstance"), 0)
        )

class Book(models.Model): # from catalog. Added title validators, changed author to manytomany
# and dropped on_delete and null=True, summary - dropped max_length, added null, blank
# dropped ISBN, dropped author from Meta ordering. Added publisher, publishedDate,
# series, previewLink, imageLink, uniqueID, contentType. Added authors display
    """Model representing a book (but not a specific copy of a book)."""
    title = models.CharField(max_length=200,
        validators=[MinLengthValidator(1, "Title must be greater than 1 characters")])
    authors = models.ManyToManyField('Author',
        help_text="Select authors for this book", related_name='books')
    # ManytoManyField used because book can have multiple authors and authors can have multiple books
    summary = models.TextField(help_text="Enter a brief description of the book", null=True, blank=True)
    publisher = models.TextField(max_length=250, help_text="Enter the publisher for the book", null=True, blank=True)
    publishedDate = models.DateField(null=True, blank=True)
    # https://stackoverflow.com/questions/35033758/what-is-the-best-practice-to-validate-a-django-datefield-at-the-model-level-as-p
    # https://docs.djangoproject.com/en/dev/ref/forms/validation/#cleaning-a-specific-field-attribute
    genre = models.ManyToManyField('Genre', help_text="Select a genre for this book")
    keywords = models.ManyToManyField('Keywords', help_text="Select keywords for this book")
    # ManyToManyField used because a genre or keywords can contain many books and a Book can
    # cover many genres and keywords.
    language = models.ForeignKey('Language', on_delete=models.SET_NULL, null=True)
    series = models.ForeignKey('Series', on_delete=models.SET_NULL, null=True)
    previewLink = models.URLField(null=True, blank=True)
    imageLink = models.URLField(null=True, blank=True)
    uniqueID = models.CharField(max_length=200, null=True, blank=True)
    contentType = models.TextField(max_length=50, help_text="Enter EBOK for ebook or PHY for physical", null = True, blank = True)
    objects = BookManager()

    class Meta:
        ordering = ['title']

    def display_genre(self):
        """Creates a string for the Genre. This is required to display genre in Admin."""
        return ', '.join([genre.name for genre in self.genre.all()[:3]])

    display_genre.short_description = 'Genre'

    def display_authors(self):
        """Creates a string for authors. This is required to display authors in Admin."""
        return ', '.join([authors.last_name for authors in self.authors.all()[:3]])

    display_authors.short_description = 'Authors'

    def bookinstance_count(self):
        return self.bookinstance_set.count()

    def get_absolute_url(self):
        """Returns the url to access a particular book instance."""
        return reverse('book-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return self.title

class BookInstance(models.Model):
    # Changed class Meta and __str__. Got rid of LOAN_STATUS. Dropped borrower, due_back,
    # and imprint. book - changed on_delete RESTRICT to CASCADE. Added location and owner.
    """Model representing a specific copy of a book (i.e. that can be borrowed from the library)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                          help_text="Unique ID for this particular book across whole library")
    book = models.ForeignKey('Book', on_delete=models.CASCADE, null=True)
    location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='booklibrary_book_instance_owner')
    # borrower = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True) from catalog

    class Meta:
        ordering = ['location']

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.id} ({self.book.title})'


class Author(models.Model):
    # From catalog. Added full_name.
    """Model representing an author."""
    full_name = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField('died', null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def get_absolute_url(self):
        """Returns the url to access a particular author instance."""
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        """String for representing the Model object."""
        return f'{self.last_name}, {self.first_name}'
