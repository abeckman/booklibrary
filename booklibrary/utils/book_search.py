# originally from
# https://github.com/Manikaran20/Books-Inventory/blob/master/SpoonshotAssignment/googlebooks/book_search.py
# Not much of original left
import os
import requests
from booklibrary.models import Book

class gbooks():
    googleapikey=os.environ.get('API_KEY')
    def __init__(self, book_search):
        self.book_search = book_search

    def search(self):
        book_list = []
        parms = {"q":self.book_search, 'key':self.googleapikey}
        try:
            r = requests.get(url="https://www.googleapis.com/books/v1/volumes", params=parms)
            my_json = r.json()
            items = my_json["items"]
        except:
            return book_list
        for i in items:
            book_info = []
            i['volumeInfo'].setdefault('title', 'Not Present')
            book_info.append(i['volumeInfo']['title'])
            i['volumeInfo'].setdefault('authors', 'Not Present')
            book_info.append(i['volumeInfo']['authors'][0])
            if len(i['volumeInfo']['authors']) > 1:             # Only pick first two authors
                book_info.append(i['volumeInfo']['authors'][1])
            else:
                book_info.append(None)
            i['volumeInfo'].setdefault('publisher', 'Not Present')
            book_info.append(i['volumeInfo'].get('publisher'))
            i['volumeInfo'].setdefault('publishedDate', 'Not Present')
            book_info.append(i['volumeInfo'].get('publishedDate'))
            i['volumeInfo'].setdefault('description', 'Not Present')
            book_info.append(i['volumeInfo'].get('description'))
            if i['volumeInfo'].get('categories') == None: # no additional genre
                book_info.append(None)
                book_info.append(None)
            else:
                book_info.append(i['volumeInfo']['categories'][0])
                if len(i['volumeInfo']['categories']) > 2:             # Only pick first two categories
                    book_info.append(i['volumeInfo']['categories'][1])
                else:
                    book_info.append(None)
            i['volumeInfo'].setdefault('language', 'en')
            book_info.append(i["volumeInfo"].get("language"))
            i['volumeInfo'].setdefault('previewLink', 'Not Present')
            book_info.append(i["volumeInfo"].get("previewLink"))
            i['volumeInfo'].setdefault("imageLinks", {'thumbnail': 'https://i.imgur.com/fnVKr.gif'})
            book_info.append(i['volumeInfo']["imageLinks"].get("thumbnail"))
            book_info.append(i["id"])
            if Book.objects.filter(uniqueID = i["id"]):
                book_info.append("owned")
            else:
                book_info.append("not owned")
            book_list.append(book_info) # add just constructed list to overall trial book list

        return book_list

# https://www.geeksforgeeks.org/handling-missing-keys-python-dictionaries/
