"""
App configuration for the booklibrary app.
"""

from django.apps import AppConfig


class BooklibraryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "booklibrary"
    verbose_name = "Book Library"

    def ready(self):
        import booklibrary.signals  # noqa: F401 — registers signal handlers
