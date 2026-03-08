"""
Signal handlers for the booklibrary app.

Registered automatically when BooklibraryConfig.ready() runs.
"""
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Book, BookInstance


@receiver(post_delete, sender=BookInstance)
def delete_book_if_last_instance(sender, instance, **kwargs):
    """
    Delete a Book when its last BookInstance is removed.

    Two early-exit guards prevent unintended behaviour:
    - If the BookInstance had no associated book (book_id is NULL), do nothing.
    - If the Book no longer exists (already removed by a cascade from
      Book.delete()), do nothing — we are inside that cascade and the
      book is already being cleaned up.
    """
    if not instance.book_id:
        return
    if not Book.objects.filter(pk=instance.book_id).exists():
        return
    if not BookInstance.objects.filter(book_id=instance.book_id).exists():
        Book.objects.filter(pk=instance.book_id).delete()
