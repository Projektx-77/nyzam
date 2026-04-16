from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0004_alter_group_id_alter_student_dormitory_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="student",
            name="course",
            field=models.CharField(
                choices=[
                    ("LLD", "LLD"),
                    ("1", "1 course"),
                    ("2", "2 course"),
                    ("3", "3 course"),
                    ("4", "4 course"),
                ],
                default="LLD",
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="student",
            name="dormitory",
            field=models.CharField(
                choices=[
                    ("yes", "Lives in dormitory"),
                    ("no", "Does not live in dormitory"),
                ],
                default="no",
                max_length=3,
            ),
        ),
        migrations.AlterField(
            model_name="student",
            name="gender",
            field=models.CharField(
                choices=[
                    ("male", "Male"),
                    ("female", "Female"),
                ],
                max_length=6,
            ),
        ),
    ]
