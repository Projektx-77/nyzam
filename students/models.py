from django.core.exceptions import ValidationError
from django.db import models


class Group(models.Model):
    COURSE_CHOICES = (
        ("LLD", "LLD"),
        ("1", "1 course"),
        ("2", "2 course"),
        ("3", "3 course"),
        ("4", "4 course"),
    )

    name = models.CharField(max_length=50)
    course = models.CharField(
        max_length=3,
        choices=COURSE_CHOICES,
        default="LLD",
    )

    class Meta:
        ordering = ["course", "name"]

    def __str__(self):
        return f"{self.name} ({self.course})"


class Student(models.Model):
    COURSE_CHOICES = (
        ("LLD", "LLD"),
        ("1", "1 course"),
        ("2", "2 course"),
        ("3", "3 course"),
        ("4", "4 course"),
    )

    GENDER_CHOICES = (
        ("male", "Male"),
        ("female", "Female"),
    )

    DORMITORY_CHOICES = (
        ("yes", "Lives in dormitory"),
        ("no", "Does not live in dormitory"),
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    photo = models.ImageField(upload_to="students/", null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    course = models.CharField(
        max_length=3,
        choices=COURSE_CHOICES,
        default="LLD",
    )
    gender = models.CharField(
        max_length=6,
        choices=GENDER_CHOICES,
    )
    dormitory = models.CharField(
        max_length=3,
        choices=DORMITORY_CHOICES,
        default="no",
    )
    room_number = models.CharField(
        max_length=10,
        blank=True,
        default="",
    )

    def clean(self):
        if self.dormitory == "yes" and not self.room_number:
            raise ValidationError(
                {"room_number": "Room number is required for students living in dormitory."}
            )
        super().clean()

    def __str__(self):
        return f"{self.last_name} {self.first_name}"
