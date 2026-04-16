from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0003_alter_event_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("morning", "Morning lineup"),
                    ("dorm_morning", "Dormitory morning check"),
                    ("dorm_night", "Dormitory night check"),
                    ("dorm_male", "Dormitory boys"),
                    ("dorm_female", "Dormitory girls"),
                    ("other", "Other"),
                ],
                max_length=20,
            ),
        ),
    ]
