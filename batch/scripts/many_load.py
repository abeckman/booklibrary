"""
Bulk-load UNESCO World Heritage Site data from a CSV file.

Run via django-extensions::

    python batch/manage.py runscript many_load

The script expects ``unesco/whc-sites-2018-clean.csv`` to exist relative
to the working directory.  It clears all existing UNESCO records before
importing, so it is safe to re-run for a fresh load.

CSV column order: name, description, justification, year, longitude,
latitude, area_hectares, category, states, region, iso.
"""
import csv

from unesco.models import Site, Category, Iso, Region, State


def run():
    fhand = open('unesco/whc-sites-2018-clean.csv')
    reader = csv.reader(fhand)
    next(reader)  # Advance past the header

    Site.objects.all().delete()
    Category.objects.all().delete()
    Iso.objects.all().delete()
    Region.objects.all().delete()
    State.objects.all().delete()

    # Format
    # name,description,justification,year,longitude,latitude,area_hectares,category,states,region,iso

    for row in reader:
        print(row)

        try:
            y = int(row[3])
        except:
            y = None
        try:
            lo = int(row[4])
        except:
            lo = None
        try:
            la = int(row[5])
        except:
            la = None
        try:
            ah = int(row[6])
        except:
            ah = None
        c, created = Category.objects.get_or_create(name=row[7])
        s, created = State.objects.get_or_create(name=row[8])
        r, created = Region.objects.get_or_create(name=row[9])
        i, created = Iso.objects.get_or_create(name=row[10])

        site = Site(name=row[0], description=row[1], justification=row[2], year=y, \
                longitude = lo, latitude = la, area_hectares = ah, category = c, \
                states = s, region = r, iso = i)
        site.save()
