"""
Owner-enforcing generic view mixins.

OwnerCreateView  – CreateView that sets owner = request.user on save.
OwnerUpdateView  – UpdateView that restricts the queryset to the request user's objects.
OwnerDeleteView  – DeleteView that restricts the queryset to the request user's objects.

Non-owners receive a 404 response rather than a permission-denied error so
that the existence of other users' records is not disclosed.
"""
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponseNotFound


class OwnerCreateView(LoginRequiredMixin, CreateView):
    """
    CreateView that automatically assigns the logged-in user as the owner
    of the newly created object.
    """

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.owner = self.request.user
        instance.save()
        return super().form_valid(form)


class OwnerUpdateView(LoginRequiredMixin, UpdateView):
    """
    UpdateView that restricts the queryset to objects owned by the
    requesting user, returning 404 for anything else.
    """

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except Http404:
            return HttpResponseNotFound()


class OwnerDeleteView(LoginRequiredMixin, DeleteView):
    """
    DeleteView that restricts the queryset to objects owned by the
    requesting user, returning 404 for anything else.
    """

    def get_queryset(self):
        return super().get_queryset().filter(owner=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except Http404:
            return HttpResponseNotFound()
