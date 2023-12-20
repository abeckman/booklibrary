from django.urls import path # path from polls and catalog apps
from . import views # from polls and catalog apps
#from django.urls import re_path # suggested replacement for orig url

urlpatterns = [
    path("", views.index, name='index'),
    path("post/<slug>/", views.post_detail, name="blog-post-detail"),
]

