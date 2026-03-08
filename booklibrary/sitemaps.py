"""
Sitemaps for the booklibrary app.

Registered in booklibrary/urls.py under /sitemap.xml.
"""
from django.contrib.sitemaps import Sitemap

from .models import Book


class BookSitemap(Sitemap):
    """Sitemap entry for all Book detail pages; refreshed weekly at high priority."""

    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return Book.objects.all()
