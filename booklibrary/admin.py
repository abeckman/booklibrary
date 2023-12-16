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
"""We are telling the Django administration site that the model is registered is
the site using a custom class that inherits from ModelAdmin. In this class, we
can include information about how to display the model on the site and how to
interact with it.
   The list_display attribute allows you to set the fields of your model that
you want to display on the administration object list page. The
@admin.register() decorator performs the same function as the
admin.site.register() function that you replaced, registering the ModelAdmin
class that it decorates.

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'author', 'publish', 'status']
    You can see that the fields displayed on the post list page are the ones
    we specified in the list_display attribute.
    list_filter = ['status', 'created', 'publish', 'author']
    The list page now includes a right sidebar that allows you to filter the
results by the fields included in the list_filter attribute.
    search_fields = ['title', 'body']
    A search bar has appeared on the page. This is because we have defined a
list of searchable fields using the search_fields attribute. Just below the
search bar, there are navigation links to navigate through a date hierarchy;
this has been defined by the date_hierarchy attribute. You can also see that
the posts are ordered by STATUS and PUBLISH columns by default.
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    the author field is now displayed with a lookup widget, which can be much
    better than a dropdown select input when you have thousands of users. This
    is achieved with the raw_id_fields attribute
    date_hierarchy = 'publish'
    ordering = ['status', 'publish']
    We have specified the default sorting criteria using the ordering
    attribute.
from Django 4 by Example
"""
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

