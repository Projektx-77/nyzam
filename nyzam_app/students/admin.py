from django.contrib import admin

from .models import Group, Student


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "last_name",
        "first_name",
        "course",
        "group",
        "gender",
        "dormitory",
        "room_number",
    )
    list_filter = ("course", "group", "gender", "dormitory")
    search_fields = ("first_name", "last_name")
