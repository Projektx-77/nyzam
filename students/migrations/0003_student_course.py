from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0002_alter_group_id_alter_student_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="course",
            field=models.CharField(
                choices=[
                    ("LLD", "LLD"),
                    ("1", "1 курс"),
                    ("2", "2 курс"),
                    ("3", "3 курс"),
                    ("4", "4 курс"),
                ],
                default="LLD",
                max_length=3,
            ),
        ),
    ]
