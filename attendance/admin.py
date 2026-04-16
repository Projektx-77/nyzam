from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'event', 'status', 'marked_by')
    list_filter = ('status', 'event')
