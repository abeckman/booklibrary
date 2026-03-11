from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("booklibrary", "0004_alter_book_authors"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookinstance",
            name="status",
            field=models.CharField(
                choices=[
                    ("a", "Available"),
                    ("o", "On loan"),
                    ("r", "Reserved"),
                    ("l", "Lost"),
                ],
                default="a",
                help_text="Availability of this copy",
                max_length=1,
            ),
        ),
    ]
