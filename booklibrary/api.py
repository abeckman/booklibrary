"""
REST API views for the booklibrary app.

BookViewSet exposes the full CRUD surface for the Book model, restricted
to authenticated users.

Wire up in your URLconf via a DRF router:

    from rest_framework.routers import DefaultRouter
    from booklibrary.api import BookViewSet

    router = DefaultRouter()
    router.register(r"books", BookViewSet, basename="book")
    urlpatterns += router.urls
"""

from rest_framework import permissions, viewsets

from booklibrary.models import Book
from booklibrary.serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    """Full CRUD API for Book objects. Requires authentication."""

    queryset = Book.objects.all().order_by("title")
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BookSerializer
