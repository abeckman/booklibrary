from django.contrib import admin

# Register your models here.

# from .models import Author, Genre, Book, BookInstance, Language # from catalog
from booklibrary.models import Author, Genre, Book, BookInstance, Language, Location, Series, Keywords

"""Minimal registration of Models. - from catalog
admin.site.register(Book)
admin.site.register(Author)
admin.site.register(BookInstance)
admin.site.register(Genre)
admin.site.register(Language)
admin.site.register(Location)
"""

admin.site.register(Genre) # from catalog
admin.site.register(Language) # from catalog
admin.site.register(Location)
admin.site.register(Series)
admin.site.register(Keywords)

# next from catalog - dead code?
class BooksInline(admin.TabularInline):
    """Defines format of inline book insertion (used in AuthorAdmin)"""
    model = Book

# next from catalog except for last line - was inlines = [BooksInline]
@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Administration object for Author models.
    Defines:
     - fields to be displayed in list view (list_display)
     - orders fields in detail view (fields),
       grouping the date fields horizontally
     - adds inline addition of books in author view (inlines)
    """
    list_display = ('last_name',
                    'first_name', 'date_of_birth', 'date_of_death')
    fields = ['first_name', 'last_name', ('date_of_birth', 'date_of_death')]
    filter_horizontal = ('book',)

# next from catalog
class BooksInstanceInline(admin.TabularInline):
    """Defines format of inline book instance insertion (used in BookAdmin)"""
    model = BookInstance
    extra = 0 # added to get rid of blank entries

# next from catalog except 'display_authors' in list_display as 'author'
class BookAdmin(admin.ModelAdmin):
    """Administration object for Book models.
    Defines:
     - fields to be displayed in list view (list_display)
     - adds inline addition of book instances in book view (inlines)
    """
    list_display = ('title', 'display_authors', 'display_genre')
    inlines = [BooksInstanceInline]

admin.site.register(Book, BookAdmin)

# next from catalog except fieldsets dropped and lists modified as don't use status
@admin.register(BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    """Administration object for BookInstance models.
    Defines:
     - fields to be displayed in list view (list_display)
     - filters that will be displayed in sidebar (list_filter)
     - grouping of fields into sections (fieldsets)
    """
    list_display = ('book', 'id')
    list_filter = ('location',)

