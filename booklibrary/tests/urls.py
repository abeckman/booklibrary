"""
Minimal URLconf for the test suite.  Replaces the broken library/urls.py
(which unconditionally imports debug_toolbar and missing blog/newblog apps).
"""
from django.contrib import admin
from django.urls import include, path

from booklibrary import views
from booklibrary.sitemaps import BookSitemap
from django.contrib.sitemaps.views import sitemap

sitemaps_dict = {"books": BookSitemap}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),

    # All booklibrary routes under /booklibrary/ so that get_absolute_url()
    # results (e.g. /booklibrary/author/<pk>) match what the models produce.
    path("booklibrary/", include([
        path("", views.index, name="index"),
        path("books/", views.BookListView.as_view(), name="books"),
        path("book/<int:pk>", views.BookDetailView.as_view(), name="book-detail"),
        path("book/search/", views.BookSearchView.as_view(), name="book-search"),
        path("book/add/", views.add_book, name="book-add"),
        path("book/<int:pk>/update/", views.BookUpdate.as_view(), name="book-update"),
        path("book/<int:pk>/delete/", views.BookDelete.as_view(), name="book-delete"),
        path("authors/", views.AuthorListView.as_view(), name="authors"),
        path("author/<int:pk>", views.AuthorDetailView.as_view(), name="author-detail"),
        path("author/create/", views.AuthorCreate.as_view(), name="author-create"),
        path("author/<int:pk>/update/", views.AuthorUpdate.as_view(), name="author-update"),
        path("author/<int:pk>/delete/", views.AuthorDelete.as_view(), name="author-delete"),
        path("locations/", views.LocationListView.as_view(), name="locations"),
        path("location/<int:pk>", views.LocationDetailView.as_view(), name="location-detail"),
        path("location/create/", views.LocationCreate.as_view(), name="location-create"),
        path("location/<int:pk>/update/", views.LocationUpdate.as_view(), name="location-update"),
        path("location/<int:pk>/delete/", views.LocationDelete.as_view(), name="location-delete"),
        path("genre/", views.GenreListView.as_view(), name="genre"),
        path("bookinstance/<uuid:pk>/update/", views.BookInstanceUpdate.as_view(), name="bookinstance-update"),
        path("bookinstance/<uuid:pk>/delete/", views.BookInstanceDelete.as_view(), name="bookinstance-delete"),
        path("ip/", views.get_ip),
        path("sitemap.xml", sitemap, {"sitemaps": sitemaps_dict},
             name="django.contrib.sitemaps.views.sitemap"),
    ])),
]
