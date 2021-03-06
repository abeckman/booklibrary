# Generated by Django 4.0.4 on 2022-05-22 20:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Iso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Site',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('description', models.CharField(max_length=128)),
                ('justification', models.CharField(max_length=128)),
                ('year', models.IntegerField(null=True)),
                ('longitude', models.IntegerField(null=True)),
                ('latitude', models.IntegerField(null=True)),
                ('area_hectares', models.IntegerField(null=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='unesco.category')),
                ('iso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='unesco.iso')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='unesco.region')),
                ('states', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='unesco.state')),
            ],
        ),
    ]
