"""
URL configuration for the booklibrary app (namespace: booklibrary).

Browse / search
---------------
  ''                  index                 Home page
  books/              BookListView          Paginated book catalogue
  book/<pk>           BookDetailView        Single-book detail
  authors/            AuthorListView        Paginated author list
  locations/          LocationListView      Paginated location list
  genre/              GenreListView         Paginated genre list
  location/<pk>       LocationDetailView    Location detail with BookInstances
  author/<pk>         AuthorDetailView      Author detail
  book/search/        BookSearchView        Google Books search

Author CRUD (login / permission required)
-----------------------------------------
  author/create/
  author/<pk>/update/
  author/<pk>/delete/

Location CRUD (login / permission required)
-------------------------------------------
  location/create/
  location/<pk>/update/
  location/<pk>/delete/

Book CRUD (login / permission required)
----------------------------------------
  book/add/           Save a book chosen from Google Books results
  book/<pk>/update/
  book/<pk>/delete/

BookInstance CRUD (login required, owner only)
----------------------------------------------
  bookinstance/<uuid:pk>/update/
  bookinstance/<uuid:pk>/delete/

Miscellaneous
-------------
  ip/           Plain-text client IP (diagnostic)
  robots.txt    Managed by django-robots
  sitemap.xml   XML sitemap for all Book pages
"""
from django.urls import path, include, re_path
from . import views
from django.contrib.sitemaps.views import sitemap
from .sitemaps import BookSitemap

sitemaps_dict = {
    'books': BookSitemap,
}

urlpatterns = [
    path('', views.index, name='index'),
    path('books/', views.BookListView.as_view(), name='books'),
    path('book/<int:pk>', views.BookDetailView.as_view(), name='book-detail'),
    path('authors/', views.AuthorListView.as_view(), name='authors'),
    path('locations/', views.LocationListView.as_view(), name='locations'),
    path('genre/', views.GenreListView.as_view(), name='genre'),
    path('location/<int:pk>', views.LocationDetailView.as_view(), name='location-detail'),
    path('author/<int:pk>', views.AuthorDetailView.as_view(), name='author-detail'),
    path('book/search/', views.BookSearchView.as_view(), name='book-search'),
    path("ip/", views.get_ip),
    re_path(r'^robots\.txt', include('robots.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps_dict},
         name='django.contrib.sitemaps.views.sitemap'),
]

# Author CRUD
urlpatterns += [
    path('author/create/', views.AuthorCreate.as_view(), name='author-create'),
    path('author/<int:pk>/update/', views.AuthorUpdate.as_view(), name='author-update'),
    path('author/<int:pk>/delete/', views.AuthorDelete.as_view(), name='author-delete'),
]

# Location CRUD
urlpatterns += [
    path('location/create/', views.LocationCreate.as_view(), name='location-create'),
    path('location/<int:pk>/update/', views.LocationUpdate.as_view(), name='location-update'),
    path('location/<int:pk>/delete/', views.LocationDelete.as_view(), name='location-delete'),
]

# Book CRUD
urlpatterns += [
    path('book/add/', views.add_book, name='book-add'),
    path('book/<int:pk>/update/', views.BookUpdate.as_view(), name='book-update'),
    path('book/<int:pk>/delete/', views.BookDelete.as_view(), name='book-delete'),
]

# BookInstance CRUD
urlpatterns += [
    path('bookinstance/<uuid:pk>/update/', views.BookInstanceUpdate.as_view(), name='bookinstance-update'),
    path('bookinstance/<uuid:pk>/delete/', views.BookInstanceDelete.as_view(), name='bookinstance-delete'),
]
