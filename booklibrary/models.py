from django.db import models
from django.urls import reverse
from django.core.validators import MinLengthValidator
from django.conf import settings
import uuid


class Genre(models.Model):
    """A book genre (e.g. Science Fiction, Non Fiction)."""

    name = models.CharField(
        max_length=200,
        help_text="Enter a book genre (e.g. Science Fiction, French Poetry etc.)",
    )

    def __str__(self):
        return self.name


class Keywords(models.Model):
    """A descriptive keyword (e.g. Climbing, Knitting)."""

    name = models.CharField(
        max_length=200,
        help_text="Enter key words (e.g. Climbing, Knitting, etc.)",
    )

    def __str__(self):
        return self.name


class Language(models.Model):
    """A language (e.g. English, French, Japanese)."""

    name = models.CharField(
        max_length=200,
        help_text="Enter the book's natural language (e.g. English, French, Japanese etc.)",
        default='English',
    )

    def __str__(self):
        return self.name


class Location(models.Model):
    """A physical storage location (e.g. Hallway Bookcase, Tub 101)."""

    name = models.CharField(
        max_length=200,
        help_text="Enter a location where the book is stored",
    )

    def __str__(self):
        return self.name


class Series(models.Model):
    """A book series (e.g. Foundation, Dune)."""

    name = models.CharField(
        max_length=200,
        help_text="Enter a series name that the book is part of",
    )

    def __str__(self):
        return self.name


class BookManager(models.Manager):
    """Custom manager that adds aggregate annotations to Book querysets."""

    def with_counts(self):
        """Return a queryset with ``num_copies`` annotated (count of BookInstances)."""
        return self.annotate(num_copies=models.Count('bookinstance'))


class Book(models.Model):
    """A book (not a specific physical copy)."""

    title = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(1, "Title must be at least 1 character")],
    )
    authors = models.ManyToManyField(
        'Author',
        help_text="Select authors for this book",
        related_name='books',
    )
    summary = models.TextField(
        help_text="Enter a brief description of the book",
        null=True, blank=True,
    )
    publisher = models.TextField(
        max_length=250,
        help_text="Enter the publisher for the book",
        null=True, blank=True,
    )
    publishedDate = models.DateField(null=True, blank=True)
    genre = models.ManyToManyField(
        'Genre',
        help_text="Select a genre for this book",
    )
    keywords = models.ManyToManyField(
        'Keywords',
        help_text="Select keywords for this book",
    )
    language = models.ForeignKey('Language', on_delete=models.SET_NULL, null=True)
    series = models.ForeignKey('Series', on_delete=models.SET_NULL, null=True)
    previewLink = models.URLField(null=True, blank=True)
    imageLink = models.URLField(null=True, blank=True)
    uniqueID = models.CharField(max_length=200, null=True, blank=True)
    contentType = models.TextField(
        max_length=50,
        help_text="EBOK for ebook, PHY for physical",
        null=True, blank=True,
    )
    objects = BookManager()

    class Meta:
        ordering = ['title']

    def display_genre(self):
        """Return up to three genre names as a comma-separated string (used in admin)."""
        return ', '.join(genre.name for genre in self.genre.all()[:3])

    display_genre.short_description = 'Genre'

    def display_authors(self):
        """Return up to three author last names as a comma-separated string (used in admin)."""
        return ', '.join(author.last_name for author in self.authors.all()[:3])

    display_authors.short_description = 'Authors'

    def bookinstance_count(self):
        """Return the number of physical copies (BookInstances) for this book."""
        return self.bookinstance_set.count()

    def get_absolute_url(self):
        """Return the canonical URL for this book's detail page."""
        return reverse('booklibrary:book-detail', args=[str(self.id)])

    def __str__(self):
        return self.title


class BookInstance(models.Model):
    """A specific physical copy of a book."""

    LOAN_STATUS = [
        ('a', 'Available'),
        ('o', 'On loan'),
        ('r', 'Reserved'),
        ('l', 'Lost'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text="Unique ID for this particular book across whole library",
    )
    book = models.ForeignKey('Book', on_delete=models.CASCADE, null=True)
    location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='booklibrary_book_instance_owner',
    )
    status = models.CharField(
        max_length=1,
        choices=LOAN_STATUS,
        default='a',
        help_text='Availability of this copy',
    )

    class Meta:
        ordering = ['location']

    def __str__(self):
        title = self.book.title if self.book_id else 'No book'
        return f'{self.id} ({title}) — {self.get_status_display()}'


class Author(models.Model):
    """A book author."""

    full_name = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField('died', null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def get_absolute_url(self):
        return reverse('booklibrary:author-detail', args=[str(self.id)])

    def __str__(self):
        if self.last_name:
            return f'{self.last_name}, {self.first_name}'
        return self.first_name
