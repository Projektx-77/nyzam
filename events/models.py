from django.conf import settings
from django.db import models


class Event(models.Model):
    EVENT_TYPE_CHOICES = (
        ("morning", "Morning lineup"),
        ("dorm_morning", "Dormitory morning check"),
        ("dorm_night", "Dormitory night check"),
        ("dorm_male", "Dormitory boys"),
        ("dorm_female", "Dormitory girls"),
        ("other", "Other"),
    )

    title = models.CharField(max_length=100)
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
    )
    date = models.DateField()
    start_time = models.TimeField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"{self.title} ({self.date})"
