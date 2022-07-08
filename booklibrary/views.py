from django.shortcuts import render, redirect # render from catalog
from booklibrary.models import Book, Author, BookInstance, Genre, Language, Keywords, Location, Series # modified from catalog
from booklibrary.owner import OwnerUpdateView, OwnerDeleteView # ,OwnerListView, OwnerDetailView, OwnerCreateView from dj4e
from django.views import generic # from polls and catalog apps
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin # from catalog
# from django.shortcuts import get_object_or_404 # from polls and catalog apps
# from django.http import HttpResponseRedirect # from polls and catalog apps
from django.urls import reverse_lazy # , reverse Reverse from polls and catalog, reverse_lazy from catalog
from datetime import datetime # from catalog app
from django.contrib.auth.decorators import login_required #, permission_required # from catalog
from django.views.generic.edit import CreateView, UpdateView, DeleteView # from catalog
from nameparser import HumanName
from django.db.models import Q
import unidecode
import os
from django.core.paginator import Paginator # added to support pagination
from django.contrib import messages # added to allow passing messages

from django.views.generic import TemplateView
#from django.views.generic.list import ListView
from django.http import HttpResponse # originally from polls app - not used?
from .forms import SearchForm, AddForm
from .book_search import gbooks
import re, requests
from django.utils import timezone

# The base code source for my work is based on:
# https://github.com/mdn/django-locallibrary-tutorial

def index(request):  # slightly modifed from catalog to drop available copies
    """View function for home page of site."""
    # Generate counts of some of the main objects
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    num_authors = Author.objects.count()  # The 'all()' is implied by default.

    # Number of visits to this view, as counted in the session variable.
    num_visits = request.session.get('num_visits', 1)
    request.session['num_visits'] = num_visits+1

    # Render the HTML template index.html with the data in the context variable.
    return render(
        request,
        'index.html',
        context={'num_books': num_books, 'num_instances': num_instances,
                 'num_authors': num_authors, 'num_visits': num_visits},
    )

class BookListView(generic.ListView): # from catalog
    """Generic class-based view for a list of books."""
    model = Book
    paginate_by = 20 # this doesn't work as a variable so probably isn't needed
    template_name = "booklibrary/book_list.html"

    def get(self, request) :
        dups = request.GET.get("List duplicate books", False)
        fields = request.GET.get("fields", False)
        strval =  request.GET.get("search", False)
        if dups :
            book_list = Book.bookInstance_count() > 1
        if strval and (fields == "title" or not fields):
            # we have a search request for a simple title-only search
            query = Q(title__icontains=strval)
            query.add(Q(summary__icontains=strval), Q.OR)
            book_list = Book.objects.filter(query).select_related().order_by('title')
        elif strval and fields == "author":
            # we have a search request for author
            # NOTE: this will require work to refine
            query = Q(authors__last_name__icontains=strval)
            query.add(Q(authors__first_name__icontains=strval), Q.OR)
            book_list = Book.objects.filter(query).select_related().order_by('title')
        elif strval and fields == "genre":
            # we have a search request for genre
            query = Q(genre__name__icontains=strval)
            book_list = Book.objects.filter(query).select_related().order_by('title')
        elif strval and fields == "series":
            # we have a search request for series
            query = Q(series__name__icontains=strval)
            book_list = Book.objects.filter(query).select_related().order_by('title')
        elif strval and fields == "keyword":
            # we have a search request for keyword
            query = Q(keywords__name__icontains=strval)
            book_list = Book.objects.filter(query).select_related().order_by('title')
        else :
            book_list = Book.objects.all().order_by('title')

            # objects = Post.objects.filter(title__contains=strval).select_related().order_by('-updated_at')[:10]

            # Multi-field search
            # __icontains for case-insensitive search
            #query = Q(title__icontains=strval)
            #query.add(Q(summary__icontains=strval), Q.OR)
            #book_list = Book.objects.filter(query).select_related().order_by('title')

        paginator = Paginator(book_list, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        ctx = {'page_obj' : page_obj, 'search': strval}
        return render(request, self.template_name, ctx)

# References

# https://docs.djangoproject.com/en/3.0/topics/db/queries/#one-to-many-relationships

# Note that the select_related() QuerySet method recursively prepopulates the
# cache of all one-to-many relationships ahead of time.

# sql “LIKE” equivalent in django query
# https://stackoverflow.com/questions/18140838/sql-like-equivalent-in-django-query

# How do I do an OR filter in a Django query?
# https://stackoverflow.com/questions/739776/how-do-i-do-an-or-filter-in-a-django-query

# https://stackoverflow.com/questions/1074212/how-can-i-see-the-raw-sql-queries-django-is-running


class GenreListView(generic.ListView): # from catalog
    """Generic class-based list view for a list of Genre."""
    model = Genre
    paginate_by = 20
    template_name = "booklibrary/genre_list.html"

    def get(self, request) :
        strval =  request.GET.get("search", False)
        if strval :
            # Simple title-only search
            # objects = Post.objects.filter(title__contains=strval).select_related().order_by('-updated_at')[:10]

            # Multi-field search
            # __icontains for case-insensitive search
            query = Q(name__icontains=strval)
#        query.add(Q(summary__icontains=strval), Q.OR)
            genre_list = Genre.objects.filter(query).select_related().order_by('name')
        else :
            genre_list = Genre.objects.all().order_by('name')
        test = 0
        if test :
                messages.add_message(request, messages.INFO, 'testing, testing')

        paginator = Paginator(genre_list, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        ctx = {'page_obj' : page_obj, 'search': strval}
        return render(request, self.template_name, ctx)


class BookDetailView(generic.DetailView): # from catalog
    """Generic class-based detail view for a book."""
    model = Book

class BookSearchView(TemplateView):
    template_name = 'booklibrary/book_search.html'
    success_url = reverse_lazy('books')

    def get(self, request):
        search_form = SearchForm()
        ctx = {'form': search_form}
        return render(request, self.template_name, ctx)

    def post(self, request):
        searchform = SearchForm(request.POST)
        if not searchform.is_valid():
            ctx = {'form': searchform}
            return render(request, self.template_name, ctx)
        volume = searchform.cleaned_data['search']
        a = gbooks(volume)
        b = a.search()          # search is defined in book_search.py
        if (b ==[]):
# This is pretty crude. Should add code to send a message and return to the search page
                return HttpResponse("No Books Found", status= 401)
        else:
            saved_genre = request.session.get('repeat_genre', 'None')
            add_form = AddForm(initial={'Book_Genre': Genre.objects.get(name = saved_genre).id})
            add_form.fields['Book_Genre'].initial = [Genre.objects.get(name = saved_genre).id]
            #form.fields['section'].initial = "Changes Approval"
            ctx = {'form': add_form, 'b': b}
            return render(request, 'booklibrary/book_results.html', ctx)
#https://stackoverflow.com/questions/657607/setting-the-selected-value-on-a-django-forms-choicefield

class AuthorListView(generic.ListView): # from catalog
    """Generic class-based list view for a list of authors."""
    model = Author
    paginate_by = 20
    template_name = "booklibrary/author_list.html"

    def get(self, request) :
        strval =  request.GET.get("search", False)
        if strval :
            # Simple title-only search
            # objects = Post.objects.filter(title__contains=strval).select_related().order_by('-updated_at')[:10]

            # Multi-field search
            # __icontains for case-insensitive search
            query = Q(last_name__icontains=strval)
#        query.add(Q(summary__icontains=strval), Q.OR)
            author_list = Author.objects.filter(query).select_related().order_by('last_name')
        else :
            author_list = Author.objects.all().order_by('last_name')

        paginator = Paginator(author_list, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        ctx = {'page_obj' : page_obj, 'search': strval}
        return render(request, self.template_name, ctx)

class AuthorDetailView(generic.DetailView): # from catalog
    """Generic class-based detail view for an author."""
    model = Author


@login_required
def add_book(request):
    print("in views add_book just before test for POST")
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        print("in views add_book just after if and AddForm. Before form.is_valid")
        # create a form instance and populate it with data from the request:
        form = AddForm(request.POST)
        if form.is_valid():
            mytitle=form.cleaned_data['title']
            myauthor1 = form.cleaned_data['author1']
            myauthor2 = form.cleaned_data['author2']
            mypublisher = form.cleaned_data['publisher']
            mypublishedOn = form.cleaned_data['publishedOn']
            if isinstance(mypublishedOn, str) and len(mypublishedOn) == 4:
                mypublishedOn = datetime(int(mypublishedOn[0:4]), 1, 1);
            if isinstance(mypublishedOn, str) and len(mypublishedOn) == 7:
                mypublishedOn = datetime(int(mypublishedOn[0:4]), int(mypublishedOn[5:7]), 1);
            if isinstance(mypublishedOn, str) and mypublishedOn == "Not Present":
                mypublishedOn = datetime.now();
            mydescription = form.cleaned_data['description']
            mygenre1 = form.cleaned_data['genre1']
            mygenre2 = form.cleaned_data['genre2']
            mylanguage = form.cleaned_data['language']
            mypreviewLink = form.cleaned_data['previewLink']
            myimageLink = form.cleaned_data['imageLink']
            myuniqueID = form.cleaned_data['uniqueID']
            mystatus = form.cleaned_data['status']
            myBook_Genre = Genre.objects.get(id=form.cleaned_data['Book_Genre']).name
            myBook_Location = Location.objects.get(id=form.cleaned_data['Book_Location']).name
            myBook_Keywords = form.cleaned_data['Book_Keywords']
            myBook_Series = Series.objects.get(id=form.cleaned_data['Book_Series']).name
# https://stackoverflow.com/questions/657607/setting-the-selected-value-on-a-django-forms-choicefield
            if myBook_Genre != 'None':
                print("***Just before testing repeat_genre***")
                #if 'repeat_genre' in request.session:
                saved_genre = request.session.get('repeat_genre', myBook_Genre)
                print("***Got a genre: ", saved_genre, " ***")
                print("Key of ", saved_genre, " is ", Genre.objects.get(name = saved_genre).id)
                form.fields['Book_Genre'].initial = [Genre.objects.get(name = saved_genre).id]
                #yourFormInstance.fields['max_number'].initial = [1]
            #else:
            #    print("*** went into else statement ***, repeat_genre = ", request.session['repeat_genre'])
            #    if myBook_Genre != 'None':
            #        request.session['repeat_genre'] = myBook_Genre
            #__getitem__(key) Example: fav_color = request.session['fav_color']
            #__setitem__(key, value) Example: request.session['fav_color'] = 'blue'
            #__delitem__(key) Example: del request.session['fav_color']. This raises KeyError if the given key isn’t already in the session.
            #__contains__(key) Example: 'fav_color' in request.session
            #num_visits = request.session.get('num_visits', 1)
            #request.session['num_visits'] = num_visits + 1

            print("***In add_book in views just below working with fields ***")
            print(mytitle)
            print(myauthor1)
            print(myauthor2)
            print(mypublisher)
            print(mypublishedOn)
            print(mydescription)
            print(mygenre1)
            print(mygenre2)
            print(mylanguage)
            print(mypreviewLink)
            print(myimageLink)
            print(myuniqueID)
            print(mystatus)
            print("Read genre = ", myBook_Genre)
            print("Read location = ", myBook_Location)
            print("Read keywords = ", myBook_Keywords)
            print("Read series = ", myBook_Series)
# https://docs.djangoproject.com/en/3.1/topics/db/search/ for unaccent_icontains
# https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-normalize-in-a-python-unicode-string
# https://stackoverflow.com/questions/10366045/django-how-to-save-data-to-manytomanyfield
# https://stackoverflow.com/questions/46314246/how-to-update-a-foreign-key-field-in-django-models-py
# https://stackoverflow.com/questions/1194737/how-to-update-manytomany-field-in-django

            myBook, created = Book.objects.filter(Q(uniqueID__icontains = myuniqueID)).get_or_create(
                    title = mytitle, summary = mydescription, publisher = mypublisher,
                    publishedDate = mypublishedOn, previewLink = mypreviewLink, imageLink = myimageLink,
                    uniqueID = myuniqueID, contentType = "PH")
            if not created : # we have a duplicate book
                messages.add_message(request, messages.INFO, 'Duplicate book')
# Existing code deals with duplicate by adding a new instance. Probably should
#   flag the repeat and offer to add a book instance
            if (myauthor1 and myauthor1 != "None"):
                myfullname1 = HumanName(myauthor1)
                myauthorObject1, created = Author.objects.filter(
                    Q(first_name__icontains = unidecode.unidecode(myfullname1.first)) &
                    Q(last_name__icontains = unidecode.unidecode(myfullname1.last))
                    ).get_or_create(
                    full_name = myauthor1,
                    first_name = unidecode.unidecode(myfullname1.first),
                    last_name = unidecode.unidecode(myfullname1.last),
                    )
                myBook.authors.add(myauthorObject1)
                #myfullname1 = HumanName(myauthor1)
                #if not (Author.objects.filter(first_name__unaccent__icontains = unidecode.unidecode(myfullname1.first)) and
                #    Author.objects.filter(last_name__unaccent__icontains=unidecode.unidecode(myfullname1.last))):
                # Author1 first and last name match existing database record
                #    pass
                #else: # Author1 not in the database
                #    q=Author(full_name=myfullname1, first_name = myfullname1.first, last_name = myfullname1.last)
                #    q.save()
            if (myauthor2 and myauthor2 != "None"):
                myfullname2 = HumanName(myauthor2)
                myauthorObject2, created = Author.objects.filter(
                    Q(first_name__icontains = unidecode.unidecode(myfullname2.first)) &
                    Q(last_name__icontains = unidecode.unidecode(myfullname2.last))
                    ).get_or_create(
                    full_name = myauthor2,
                    first_name = unidecode.unidecode(myfullname2.first),
                    last_name = unidecode.unidecode(myfullname2.last),
                    )
                myBook.authors.add(myauthorObject2)
                #myfullname2 = HumanName(myauthor2)
                #if not (Author.objects.filter(first_name__unaccent__icontains = unidecode.unidecode(myfullname2.first)) and
                #    Author.objects.filter(last_name__unaccent__icontains = unidecode.unidecode(myfullname2.last))):
                # Author2 first and last name dont match existing database record
                #    q=Author(full_name=myfullname2, first_name = myfullname2.first, last_name = myfullname2.last)
                #    q.save()

            if (mygenre1 and mygenre1 != "None"):
                mygenreObject1, created = Genre.objects.filter(
                    Q(name = mygenre1)).get_or_create(name = mygenre1)
                myBook.genre.add(mygenreObject1)
            if (mygenre2 and mygenre2 != "None"):
                mygenreObject2, created = Genre.objects.filter(
                    Q(name = mygenre2)).get_or_create(name = mygenre2)
                myBook.genre.add(mygenreObject2)
            if (myBook_Genre and myBook_Genre != "None"):
                mygenreObject3, created = Genre.objects.filter(
                    Q(name = myBook_Genre)).get_or_create(name = myBook_Genre)
                myBook.genre.add(mygenreObject3)
            if (mylanguage and mylanguage != "None"):
                mylanguageObject, created = Language.objects.filter(
                    Q(name = mylanguage)).get_or_create(name = mylanguage)
                # The following gets "Cannot assign "3": "Book.language" must be a "Language" instance."
                #myBook.language = mylanguageObject.id
                myBook.language = mylanguageObject
                # The following gets "'NoneType' object has no attribute 'add'"
                #myBook.language.add(mylanguageObject)
            if myBook_Series:
                mySeriesObject, created = Series.objects.filter(
                    Q(name = myBook_Series)).get_or_create(name = myBook_Series)
                myBook.series = mySeriesObject
            for keyword_id in myBook_Keywords:
                keyword = Keywords.objects.get(id=keyword_id).name
                if keyword:
                    mykeywordObject, created = Keywords.objects.filter(
                        Q(name = keyword)).get_or_create(name = keyword)
                    myBook.keywords.add(mykeywordObject)
            myBook.save()

            myLocationObject = Location.objects.get(name__contains = myBook_Location)
            myBookInstance = BookInstance.objects.create(owner=request.user, book=myBook, location=myLocationObject)
            myBookInstance.save()
#e = myBook.update_or_create(language = mylanguageObject)
# Update only works on querysets -
# https://stackoverflow.com/questions/15304378/django-error-model-object-has-no-attribute-update/39934249

            books=Book.objects.all()
            return redirect('/booklibrary/books/', {'books':books})
        else:
            print('opps, form not valid')
            return render(request, 'booklibrary/book_results.html', {'form': form})
    # if a GET (or any other method) we'll create a blank form
    else:
        form = AddForm()
    return render(request, 'book_request.html', {'form': form})

class AuthorCreate(LoginRequiredMixin, CreateView): # from catalog
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    initial = {'date_of_death': '11/06/2020'}

class AuthorUpdate(PermissionRequiredMixin, UpdateView): # from catalog
    model = Author
    fields = '__all__' # Not recommended (potential security issue if more fields added)
    permission_required = 'booklibrary.author.can_change_author'

class AuthorDelete(PermissionRequiredMixin, DeleteView): # from catalog
    model = Author
    success_url = reverse_lazy('authors')
    permission_required = 'booklibrary.author.can_delete_author'

class BookCreate(LoginRequiredMixin, TemplateView): # almost nothing left from catalog
	def get(self, request):
		addform = AddForm
		return render(request, 'booklibrary/book_create.html', {'form':addform})

	def post(self, request):
		addform= AddForm(request.POST)
		if addform.is_valid():
			url=addform.cleaned_data['url']
			key=re.findall("id=.+?[&]", url)
			temp_key=key[0][3:-1]
		googleapikey=os.environ.get('API_KEY')
		book_url="https://www.googleapis.com/books/v1/volumes/{}".format(temp_key)
		r = requests.get(url=book_url, params={'key':googleapikey})
		my_json= r.json()
		p_link="https://books.google.co.in/books?id={}".format(temp_key)
		q=Book(book_name=my_json['volumeInfo']['title'], ID=temp_key, preview_link='p_link', created_at= timezone.now())
		q.save()
		books=Book.objects.all()
		return render(request, 'booklibrary/book_list.html', {'books':books})

class BookUpdate(PermissionRequiredMixin, UpdateView): # from catalog
    model = Book
    fields = ['title', 'authors', 'summary', 'genre', 'language', 'publisher', 'publishedDate', 'keywords', 'series']
    permission_required = 'booklibrary.book.can_change_book'

class BookDelete(PermissionRequiredMixin, DeleteView): # from catalog
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'booklibrary.book.can_delete_book'

class BookInstanceUpdate(OwnerUpdateView):
    model = BookInstance
    fields = ['book', 'location']


class BookInstanceDelete(OwnerDeleteView):
    model = BookInstance
    success_url = reverse_lazy('books')

###############################################################################################

#class BooksUpdate(TemplateView):
#	def get(self, request, ID):
#		form=UpdateForm
#		return render(request, 'googlebooks/update.html', {'form':form})
#	def post(self, request, ID):
#		updateform= UpdateForm(request.POST)
#		if updateform.is_valid():
#			title=updateform.cleaned_data['title']
#			preview_link=updateform.cleaned_data['previewLink']
#			key=updateform.cleaned_data['ID']
#			copies=updateform.cleaned_data['copies']

#			q=Books.objects.filter(ID=ID)
#			q.book_name=title
#			q.preview_link=preview_link
#			q.ID=key
#			q.count=copies
#			q.save()
#		books= Books.objects.all()
#		return render(request, 'googlebooks/inventory', {'books': books})

# This next is from catalog and I'm not using it. Looks like a good template for searches however
#class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
#    """Generic class-based view listing books on loan to current user."""
#    model = BookInstance
#    template_name = 'catalog/bookinstance_list_borrowed_user.html'
#    paginate_by = 10

#   def get_queryset(self):
#        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

