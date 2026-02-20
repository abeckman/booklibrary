"""
Form tests for SearchForm and AddForm.

AddForm populates its Genre/Location/Series/Keywords choices lazily inside
__init__, so choices reflect the database state at the time each form
instance is created.  Tests that don't seed those models will see empty
choice lists; tests that do seed them will see real choices.
"""
import pytest
from booklibrary.forms import SearchForm, AddForm


# ── SearchForm ────────────────────────────────────────────────────────────────

class TestSearchForm:
    """SearchForm is a simple Form — no DB required."""

    def test_valid_with_search_term(self):
        form = SearchForm(data={"search": "Dune"})
        assert form.is_valid()
        assert form.cleaned_data["search"] == "Dune"

    def test_valid_with_whitespace_only(self):
        # CharField strips by default; whitespace-only is non-empty before strip
        form = SearchForm(data={"search": "   "})
        # Django strips leading/trailing whitespace, leaving ""
        # CharField with strip=True (default) will make this empty → invalid
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
        form = SearchForm()
        widget_attrs = form.fields["search"].widget.attrs
        assert widget_attrs.get("placeholder") == "search for a book"

    def test_search_widget_has_form_control_class(self):
        form = SearchForm()
        widget_attrs = form.fields["search"].widget.attrs
        assert "form-control" in widget_attrs.get("class", "")

    def test_long_search_term_is_valid(self):
        form = SearchForm(data={"search": "a" * 500})
        # CharField has no max_length by default
        assert form.is_valid()


# ── AddForm (empty-choices state) ─────────────────────────────────────────────

@pytest.mark.django_db
class TestAddFormStructure:
    """
    Tests that verify AddForm field presence, required flags, and behavior
    when no Genre/Location/Series/Keywords rows exist in the DB (empty choices).
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

    def test_book_genre_is_multiple_choice(self):
        from django import forms
        assert isinstance(AddForm().fields["Book_Genre"], forms.MultipleChoiceField)

    def test_book_location_is_choice_field(self):
        from django import forms
        assert isinstance(AddForm().fields["Book_Location"], forms.ChoiceField)

    def test_book_keywords_help_text(self):
        assert "Keywords" in AddForm().fields["Book_Keywords"].help_text

    def test_form_valid_with_required_hidden_fields_only(self):
        """
        When no DB rows exist, choices are empty and optional choice fields
        accept '' — form is valid when all required hidden fields are supplied.
        """
        data = {
            "title": "My Book",
            "author1": "Jane Doe",
            "genre1": "Science Fiction",
            "language": "English",
            "uniqueID": "test-001",
            "status": "PH",
            # optional fields omitted / empty
            "author2": "",
            "publisher": "",
            "publishedOn": "",
            "description": "",
            "genre2": "",
            "previewLink": "",
            "imageLink": "",
            "Book_Genre": [],
            "Book_Location": "",
            "Book_Keywords": "",
            "Book_Series": "",
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
        """min_length=2 means a single character is rejected."""
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
