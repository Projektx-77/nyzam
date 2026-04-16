from django.db import migrations, models


def set_default_room_numbers(apps, schema_editor):
    Student = apps.get_model("students", "Student")
    Student.objects.filter(dormitory="yes", room_number="").update(room_number="101")


def reverse_set_default_room_numbers(apps, schema_editor):
    Student = apps.get_model("students", "Student")
    Student.objects.filter(room_number="101").update(room_number="")


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0007_alter_group_options_group_course_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="room_number",
            field=models.CharField(blank=True, default="", max_length=10),
        ),
        migrations.RunPython(set_default_room_numbers, reverse_set_default_room_numbers),
    ]
