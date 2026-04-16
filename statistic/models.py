# Deepseek acdy 
# Create your models here.
# statistics/models.py
from django.db import models
from students.models import Student, Group

class AttendanceStatistics(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    total_events = models.IntegerField(default=0)
    present_count = models.IntegerField(default=0)
    absent_count = models.IntegerField(default=0)
    late_count = models.IntegerField(default=0)
    attendance_rate = models.FloatField(default=0.0)  # процент посещаемости
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date']

class GroupStatistics(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    date = models.DateField()
    total_students = models.IntegerField(default=0)
    average_attendance = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = ['group', 'date']
        ordering = ['-date']