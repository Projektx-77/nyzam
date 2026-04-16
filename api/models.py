from django.db import models

# Create your models here.
class Group(models.Model):
    COURSE_CHOICES = [
        ("LLD", "LLD"),
        ("1", "1 курс"),
        ("2", "2 курс"),
        ("3", "3 курс"),
        ("4", "4 курс"),
    ]

    name = models.CharField(max_length=100)
    course = models.CharField(max_length=10, choices=COURSE_CHOICES)
    

    class Meta:
        ordering = ["course", "name"]
        unique_together = ("name", "course")

    def __str__(self):
        return f"{self.name} ({self.course})"