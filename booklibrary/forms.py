#from django.core.exceptions import ValidationError # from catalog
#from django.utils.translation import gettext_lazy as _ # from catalog
#import datetime  # for checking renewal date range. from catalog
from django import forms # from catalog
from booklibrary.models import Genre, Location, Series, Keywords

# None of this is from catalog except a few imports

class SearchForm(forms.Form):
	search = forms.CharField(widget=forms.TextInput(
		attrs={
			'class': 'form-control',
			'placeholder': 'search for a book'
		}
	))

# Look at putting first location selected into session variable. Same for the genre
# Offer selection or entry for location with session value or default
# Offer check list of genre and option of new one

class AddForm(forms.Form):
# NOTE: for whatever reason, when the database hasn't been created, makemigrations and
#   check will get a table doesn't exist error on the next several lines. All have to
#   be commented out until the db is created, then restored.
    genres = [(choice.pk, choice.name) for choice in Genre.objects.all()]
    #Book_Genre = forms.ChoiceField(choices = genres, initial='6', required=False)
    Book_Genre = forms.ChoiceField(choices = genres, required=False)
    locations = [(choice.pk, choice.name) for choice in Location.objects.all()]
    Book_Location = forms.ChoiceField(choices = locations, required=False)
    series = [(choice.pk, choice.name) for choice in Series.objects.all()]
    Book_Series = forms.ChoiceField(choices = series, required=False)
    keywords = [(choice.pk, choice.name) for choice in Keywords.objects.all()]
    #Book_Keywords = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple(),
    Book_Keywords = forms.MultipleChoiceField(choices = keywords, initial = keywords[0],
        help_text="Keywords (up to 3)")
# https://www.geeksforgeeks.org/choicefield-django-forms/
# https://stackoverflow.com/questions/31035112/django-init-got-an-unexpected-keyword-argument-choices
# https://stackoverflow.com/questions/34781524/django-populate-a-form-choicefield-field-from-a-queryset-and-relate-the-choice-b
    #gender = forms.ChoiceField(widget=forms.RadioSelect(
    #             choices=Evangelized.GENDER_CHOICES), help_text="Gender")
    #allGenre = forms.ChoiceField(choises=[(choice.pk, choice) for choice in Genre.objects.all()], help_text="Genre")
    #allGenre = forms.ModelChoiceField(queryset=Genre.objects.all())
    title = forms.CharField(widget = forms.HiddenInput(), required=True, max_length=200, min_length=2, strip = False)
    author1 = forms.CharField(widget = forms.HiddenInput(), required=True, max_length=50, strip = False)
    author2 = forms.CharField(widget = forms.HiddenInput(), required=False, max_length=50, strip = False)
    publisher = forms.CharField(widget = forms.HiddenInput(), required=False, max_length=250, strip = False)
    publishedOn = forms.CharField(widget = forms.HiddenInput(), required=False, max_length=250, strip = False)
    description = forms.CharField(widget = forms.HiddenInput(), required=False, max_length=4000, strip = False)
    genre1 = forms.CharField(widget = forms.HiddenInput(), required=True, max_length=200)
    genre2 = forms.CharField(widget = forms.HiddenInput(), required=False, max_length=200)
    language = forms.CharField(widget = forms.HiddenInput(), required=True, max_length=200)
    previewLink = forms.CharField(widget = forms.HiddenInput(), required=False, max_length=250)
    imageLink = forms.CharField(widget = forms.HiddenInput(), required=False, max_length=250)
    uniqueID = forms.CharField(widget = forms.HiddenInput(), required=True, max_length=200)
    status = forms.CharField(widget = forms.HiddenInput(), required=True, max_length = 50, strip = False)

#class UpdateForm(forms.Form):
#	title = forms.CharField(widget=forms.TextInput(
#		attrs={
#			'class': 'form-control',
#			'placeholder': 'Enter Title'
#		}
#	))
#	previewLink=forms.URLField(widget=forms.TextInput(
#		attrs={
#			'class': 'form-control',
#			'placeholder' 'Google books Link'
#		}
#	))
#	ID = forms.CharField(widget=forms.TextInput(
#		attrs={
#			'class': 'form-control',
#			'placeholder': 'must be google book id'
#		}
#	))
#	copies = forms.IntegerField(widget=forms.TextInput(
#		attrs={
#			'class': 'form-control',
#			'placeholder': 'how many copies you want to add'
#		}
#	))
