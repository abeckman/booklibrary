# from https://github.com/Manikaran20/Books-Inventory/blob/master/SpoonshotAssignment/googlebooks/api.py
from booklibrary.models import Book
from rest_framework import viewsets, permissions
from booklibrary.serializers import BookSerializer

# ScholarProfile Viewset

class BookViewSet(viewsets.ModelViewSet):
	queryset = Book.objects.all()
	permission_classes = [permissions.IsAuthenticated]
	serializer_class = BookSerializer
