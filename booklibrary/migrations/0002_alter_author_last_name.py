# Generated by Django 4.0.4 on 2022-07-12 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booklibrary', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='last_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]