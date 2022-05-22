# from https://github.com/Manikaran20/Books-Inventory/blob/master/SpoonshotAssignment/googlebooks/serializers.py
from rest_framework import serializers
from googlebooks.models import Book

# Source unknown. Not from catalog.

class BookSerializer(serializers.ModelSerializer):
	class Meta:
		model = Book
		fields = '__all__'
