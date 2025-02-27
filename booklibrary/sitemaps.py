from django.contrib.sitemaps import Sitemap
from .models import Author, Genre, Book, BookInstance, Language, Location, Series, Keywords

class BookSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

def items(self):
    return Book.all()

def lastmod(self, obj):
    return obj.updated
