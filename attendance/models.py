# attendance/models.py
from django.db import models
from django.conf import settings
from students.models import Student
from events.models import Event

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Присутствует'),
        ('absent', 'Отсутствует'),
        ('late', 'Опоздал'),
        ('excused', 'Уважительная причина'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='present'
    )
    reason = models.TextField(blank=True, null=True)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    marked_at = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(blank=True, null=True)
    
    # Уникальность: один студент не может быть отмечен дважды на одном мероприятии
    class Meta:
        unique_together = ['student', 'event']
        ordering = ['-marked_at']

    def __str__(self):
        return f"{self.student} — {self.event} — {self.get_status_display()}"