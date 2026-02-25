from rest_framework import serializers
from booklibrary.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'authors',
            'summary',
            'publisher',
            'publishedDate',
            'genre',
            'keywords',
            'language',
            'series',
            'previewLink',
            'imageLink',
            'uniqueID',
            'contentType',
        ]
        read_only_fields = ['id']
