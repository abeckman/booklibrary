"""
Admin configuration for the booklibrary app.
"""

from django.contrib import admin

from booklibrary.models import (
    Author, Book, BookInstance, Genre, Keywords, Language, Location, Series,
)


# Simple models with no custom admin behaviour.
admin.site.register(Genre)
admin.site.register(Language)
admin.site.register(Location)
admin.site.register(Series)
admin.site.register(Keywords)


class BookInstanceInline(admin.TabularInline):
    model = BookInstance
    extra = 0


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "date_of_birth", "date_of_death")
    # Tuple groups the date fields side-by-side on the detail page.
    fields = ["first_name", "last_name", ("date_of_birth", "date_of_death")]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "display_authors", "display_genre")
    inlines = [BookInstanceInline]


@admin.register(BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    list_display = ("book", "id")
    list_filter = ("location",)
