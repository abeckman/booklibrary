from django.urls import path # path from polls and catalog apps
from . import views # from polls and catalog apps
#from django.urls import re_path # suggested replacement for orig url
from django.urls import include, re_path # added by robots_django
from django.contrib.sitemaps.views import sitemap # from Django 4 by Example
from booklibrary.sitemaps import BookSitemap

sitemaps = { # from Django 4 by Example
'books': BookSitemap,
}

urlpatterns = [
    path('', views.index, name='index'), # from polls and catalog apps
    path('books/', views.BookListView.as_view(), name='books'), # from catalog app
    path('book/<int:pk>', views.BookDetailView.as_view(), name='book-detail'), # from catalog app
    path('authors/', views.AuthorListView.as_view(), name='authors'), # from catalog app
    path('locations/', views.LocationListView.as_view(), name='locations'), # from catalog app
    path('genre/', views.GenreListView.as_view(), name='genre'), # page for testing
    path('location/<int:pk>',
         views.LocationDetailView.as_view(), name='location-detail'),
    path('author/<int:pk>',
         views.AuthorDetailView.as_view(), name='author-detail'), # from catalog app
    path('book/search/', views.BookSearchView.as_view(), name='book-search'),
    path("ip/", views.get_ip),
    re_path(r'^robots\.txt', include('robots.urls')), # from robots-django
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap') # from Django4 by Example
]

# Add URLConf to create, update, and delete authors
urlpatterns += [
    path('author/create/', views.AuthorCreate.as_view(), name='author-create'), # from catalog app
    path('author/<int:pk>/update/', views.AuthorUpdate.as_view(), name='author-update'), # from catalog app
    path('author/<int:pk>/delete/', views.AuthorDelete.as_view(), name='author-delete'), # from catalog app
]

# Add URLConf to create, update, and delete locations
urlpatterns += [
    path('location/create/', views.LocationCreate.as_view(), name='location-create'),
    path('location/<int:pk>/update/', views.LocationUpdate.as_view(), name='location-update'),
    path('location/<int:pk>/delete/', views.LocationDelete.as_view(), name='location-delete'),
]

# Add URLConf to create, update, and delete books
urlpatterns += [
    path('book/add/', views.add_book, name='book-add'),
    path('book/create/', views.BookCreate.as_view(), name='book-create'), # from catalog app
    path('book/<int:pk>/update/', views.BookUpdate.as_view(), name='book-update'), # from catalog app
    path('book/<int:pk>/delete/', views.BookDelete.as_view(), name='book-delete'), # from catalog app
]

# Add URLConf to update and delete bookinstances
urlpatterns += [
    path('bookinstance/<uuid:pk>/update/', views.BookInstanceUpdate.as_view(), name='bookinstance-update'), # from catalog app
    path('bookinstance/<uuid:pk>/delete/', views.BookInstanceDelete.as_view(), name='bookinstance-delete'), # from catalog app
]


