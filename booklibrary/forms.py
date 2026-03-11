"""
Forms for the booklibrary app.

SearchForm  – simple single-field search used by BookSearchView.
AddForm     – captures the user's local choices (genre, location, series,
              keywords) when adding a book sourced from Google Books results.
              Hidden fields carry book metadata for validation but the actual
              data used to create the Book record is always read from the
              server-side session, not from cleaned_data.
"""
from django import forms
from booklibrary.models import Genre, Keywords, Location, Series


class SearchForm(forms.Form):
    """Single-field search form for querying the Google Books API."""

    search = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'search for a book',
        })
    )


class AddForm(forms.Form):
    """
    User-supplied choices when adding a book from Google Books search results.

    The four choice fields (book_genre, book_location, book_series,
    book_keywords) capture the user's local shelving preferences.

    The hidden fields carry book metadata submitted by the template and are
    validated server-side, but the actual data used to create the Book record
    is read from the session (not from cleaned_data) to prevent tampering.
    """

    # ── User-supplied choice fields ────────────────────────────────────────────

    book_genre = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.all(),
        required=False,
    )
    book_location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        required=False,
        empty_label='— select location —',
    )
    book_series = forms.ModelChoiceField(
        queryset=Series.objects.all(),
        required=False,
        empty_label='— select series —',
    )
    book_keywords = forms.ModelMultipleChoiceField(
        queryset=Keywords.objects.all(),
        required=False,
        help_text='Keywords (up to 3)',
    )

    # ── Hidden book-metadata fields (validated; values read from session) ──────

    title = forms.CharField(
        widget=forms.HiddenInput(), max_length=200, min_length=2, strip=False,
    )
    author1 = forms.CharField(
        widget=forms.HiddenInput(), max_length=50, strip=False,
    )
    author2 = forms.CharField(
        widget=forms.HiddenInput(), required=False, max_length=50, strip=False,
    )
    publisher = forms.CharField(
        widget=forms.HiddenInput(), required=False, max_length=250, strip=False,
    )
    publishedOn = forms.CharField(
        widget=forms.HiddenInput(), required=False, max_length=250, strip=False,
    )
    description = forms.CharField(
        widget=forms.HiddenInput(), required=False, max_length=4000, strip=False,
    )
    genre1 = forms.CharField(
        widget=forms.HiddenInput(), max_length=200,
    )
    genre2 = forms.CharField(
        widget=forms.HiddenInput(), required=False, max_length=200,
    )
    language = forms.CharField(
        widget=forms.HiddenInput(), max_length=200,
    )
    previewLink = forms.CharField(
        widget=forms.HiddenInput(), required=False, max_length=250,
    )
    imageLink = forms.CharField(
        widget=forms.HiddenInput(), required=False, max_length=250,
    )
    uniqueID = forms.CharField(
        widget=forms.HiddenInput(), max_length=200,
    )
    status = forms.CharField(
        widget=forms.HiddenInput(), max_length=50, strip=False,
    )
