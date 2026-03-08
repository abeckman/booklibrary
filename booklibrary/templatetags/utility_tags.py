"""
Custom template tags for the booklibrary app.

modify_query  – rewrites the current URL's query string without a full page
                description, making it easy to build sort/filter/page links
                that preserve existing parameters.

Usage in templates::

    {% load utility_tags %}
    <a href="{% modify_query page=page_obj.next_page_number %}">Next</a>
    <a href="{% modify_query 'sort' sort='title' %}">Sort by title</a>
"""
from urllib.parse import urlencode

from django import template
from django.utils.encoding import force_str
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


def construct_query_string(context, query_params):
    """Build a safe URL string from the current path plus the given query params.

    Empty values are omitted. Ampersands are escaped to ``&amp;`` for HTML safety.
    Returns a ``SafeString`` suitable for use directly in href attributes.
    """
    path = conditional_escape(context["request"].path)
    if len(query_params):
        encoded_params = urlencode([
            (key, force_str(value))
            for (key, value) in query_params if value
        ]).replace("&", "&amp;")
        return mark_safe(f"{path}?{encoded_params}")
    return mark_safe(path)


@register.simple_tag(takes_context=True)
def modify_query(context, *params_to_remove, **params_to_change):
    """Renders a link with modified current query parameters"""
    query_params = []
    for key, value_list in context["request"].GET.lists():
        if not key in params_to_remove:
            # don't add key-value pairs for params_to_remove
            if key in params_to_change:
                # update values for keys in params_to_change
                query_params.append((key, params_to_change[key]))
                params_to_change.pop(key)
            else:
                # leave existing parameters as they were
                # if not mentioned in the params_to_change
                for value in value_list:
                    query_params.append((key, value))
                    # attach new params
    for key, value in params_to_change.items():
        query_params.append((key, value))
    return construct_query_string(context, query_params)
