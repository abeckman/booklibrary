"""
Application-level template filters for the booklibrary app.

gravatar  – returns a Gravatar image URL for a Django user object.

Usage::

    {% load app_tags %}
    <img src="{{ user|gravatar:40 }}" alt="avatar">
"""
from hashlib import md5
from django import template

register = template.Library()


@register.filter(name='gravatar')
def gravatar(user, size=35):
    """Return the Gravatar URL for ``user``'s email address.

    Falls back to an identicon if the address has no registered Gravatar.
    The rating is set to PG so adult-only images are excluded.

    Args:
        user: A Django user object with an ``email`` attribute.
        size: Pixel dimensions of the square avatar image (default 35).
    """
    email = str(user.email.strip().lower()).encode('utf-8')
    email_hash = md5(email).hexdigest()
    url = "//www.gravatar.com/avatar/{0}?s={1}&d=identicon&r=PG"
    return url.format(email_hash, size)
