"""
Form tests for SearchForm and AddForm.

AddForm uses ModelMultipleChoiceField / ModelChoiceField for its four
user-facing choice fields, so those fields reflect live DB state.
Tests that don't seed the related models will see empty querysets (all
optional fields, so forms can still be valid).
"""
import pytest
from django import forms as django_forms
from booklibrary.forms import SearchForm, AddForm


# ── SearchForm ────────────────────────────────────────────────────────────────

class TestSearchForm:
    """SearchForm is a simple Form — no DB required."""

    def test_valid_with_search_term(self):
        form = SearchForm(data={"search": "Dune"})
        assert form.is_valid()
        assert form.cleaned_data["search"] == "Dune"

    def test_valid_with_whitespace_only(self):
        # CharField strips by default; whitespace-only collapses to "" → invalid
        form = SearchForm(data={"search": "   "})
        assert not form.is_valid()

    def test_invalid_when_search_missing(self):
        form = SearchForm(data={})
        assert not form.is_valid()
        assert "search" in form.errors

    def test_invalid_when_search_empty_string(self):
        form = SearchForm(data={"search": ""})
        assert not form.is_valid()
        assert "search" in form.errors

    def test_search_widget_has_placeholder(self):
        widget_attrs = SearchForm().fields["search"].widget.attrs
        assert widget_attrs.get("placeholder") == "search for a book"

    def test_search_widget_has_form_control_class(self):
        widget_attrs = SearchForm().fields["search"].widget.attrs
        assert "form-control" in widget_attrs.get("class", "")

    def test_long_search_term_is_valid(self):
        form = SearchForm(data={"search": "a" * 500})
        assert form.is_valid()


# ── AddForm (empty-choices state) ─────────────────────────────────────────────

@pytest.mark.django_db
class TestAddFormStructure:
    """
    Verify AddForm field presence, required flags, and field types when no
    Genre/Location/Series/Keywords rows exist in the DB (empty querysets).
    """

    def test_required_hidden_fields_present(self):
        form = AddForm()
        required_hidden = ["title", "author1", "genre1", "language", "uniqueID", "status"]
        for field_name in required_hidden:
            assert field_name in form.fields, f"Missing field: {field_name}"
            assert form.fields[field_name].required, f"{field_name} should be required"

    def test_optional_hidden_fields_present(self):
        form = AddForm()
        optional_hidden = ["author2", "publisher", "publishedOn", "description",
                           "genre2", "previewLink", "imageLink"]
        for field_name in optional_hidden:
            assert field_name in form.fields, f"Missing field: {field_name}"
            assert not form.fields[field_name].required, f"{field_name} should be optional"

    def test_title_max_length(self):
        assert AddForm().fields["title"].max_length == 200

    def test_title_min_length(self):
        assert AddForm().fields["title"].min_length == 2

    def test_author1_max_length(self):
        assert AddForm().fields["author1"].max_length == 50

    def test_author2_is_optional(self):
        assert not AddForm().fields["author2"].required

    def test_description_max_length(self):
        assert AddForm().fields["description"].max_length == 4000

    def test_book_genre_is_model_multiple_choice(self):
        assert isinstance(AddForm().fields["book_genre"], django_forms.ModelMultipleChoiceField)

    def test_book_location_is_model_choice(self):
        assert isinstance(AddForm().fields["book_location"], django_forms.ModelChoiceField)

    def test_book_series_is_model_choice(self):
        assert isinstance(AddForm().fields["book_series"], django_forms.ModelChoiceField)

    def test_book_keywords_is_model_choice(self):
        assert isinstance(AddForm().fields["book_keywords"], django_forms.ModelChoiceField)

    def test_book_keywords_help_text(self):
        assert "Keywords" in AddForm().fields["book_keywords"].help_text

    def test_choice_fields_are_optional(self):
        form = AddForm()
        for field_name in ("book_genre", "book_location", "book_series", "book_keywords"):
            assert not form.fields[field_name].required, f"{field_name} should be optional"

    def test_form_valid_with_required_hidden_fields_only(self):
        """
        When no DB rows exist, choice fields are empty querysets; the form is
        valid as long as all required hidden fields are supplied.
        """
        data = {
            "title": "My Book",
            "author1": "Jane Doe",
            "genre1": "Science Fiction",
            "language": "English",
            "uniqueID": "test-001",
            "status": "PH",
            # optional fields empty
            "author2": "",
            "publisher": "",
            "publishedOn": "",
            "description": "",
            "genre2": "",
            "previewLink": "",
            "imageLink": "",
            "book_genre": [],
            "book_location": "",
            "book_keywords": "",
            "book_series": "",
        }
        form = AddForm(data=data)
        assert form.is_valid(), form.errors

    def test_form_invalid_without_title(self):
        data = {
            "author1": "Jane Doe",
            "genre1": "Sci-Fi",
            "language": "English",
            "uniqueID": "uid-001",
            "status": "PH",
        }
        form = AddForm(data=data)
        assert not form.is_valid()
        assert "title" in form.errors

    def test_form_invalid_with_short_title(self):
        data = {
            "title": "A",
            "author1": "Jane Doe",
            "genre1": "Sci-Fi",
            "language": "English",
            "uniqueID": "uid-001",
            "status": "PH",
        }
        form = AddForm(data=data)
        assert not form.is_valid()
        assert "title" in form.errors

    def test_form_invalid_without_author1(self):
        data = {
            "title": "Some Book",
            "genre1": "Sci-Fi",
            "language": "English",
            "uniqueID": "uid-001",
            "status": "PH",
        }
        form = AddForm(data=data)
        assert not form.is_valid()
        assert "author1" in form.errors

    def test_form_invalid_without_uniqueID(self):
        data = {
            "title": "Some Book",
            "author1": "Jane",
            "genre1": "Sci-Fi",
            "language": "English",
            "status": "PH",
        }
        form = AddForm(data=data)
        assert not form.is_valid()
        assert "uniqueID" in form.errors
