# api/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from students.models import Student, Group
from events.models import Event
from attendance.models import Attendance
from statistic.models import AttendanceStatistics, GroupStatistics

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    def get_full_name(self, obj):
        return obj.get_full_name().strip() or obj.username

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "role",
            "first_name",
            "last_name",
            "full_name",
        ]
        read_only_fields = ["id"]


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"


class StudentSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)
    photo_url = serializers.SerializerMethodField()

    def get_photo_url(self, obj):
        if not obj.photo:
            return None

        request = self.context.get("request")
        photo_url = obj.photo.url
        return request.build_absolute_uri(photo_url) if request else photo_url

    def validate(self, attrs):
        dormitory = attrs.get("dormitory")
        room_number = attrs.get("room_number")

        if self.instance is not None:
            dormitory = dormitory if dormitory is not None else self.instance.dormitory
            room_number = room_number if room_number is not None else self.instance.room_number

        if dormitory == "yes" and not room_number:
            raise serializers.ValidationError(
                {"room_number": "Room number is required for students living in dormitory."}
            )

        return attrs

    class Meta:
        model = Student
        fields = [
            "group_name",
            "photo",
            "photo_url",
            "first_name",
            "last_name",
            "id",
            "birth_date",
            "group",
            "course",
            "gender",
            "dormitory",
            "room_number",
        ]
        read_only_fields = ["id"]


class EventSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "event_type",
            "date",
            "start_time",
            "created_by",
            "created_by_name",
        ]
        read_only_fields = ["id", "created_by"]


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.__str__", read_only=True)
    event_title = serializers.CharField(source="event.title", read_only=True)
    marked_by_name = serializers.CharField(source="marked_by.get_full_name", read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id",
            "student",
            "student_name",
            "event",
            "event_title",
            "status",
            "reason",
            "marked_by",
            "marked_by_name",
            "marked_at",
            "comments",
        ]
        read_only_fields = ["id", "marked_by", "marked_at"]


class BulkAttendanceSerializer(serializers.Serializer):
    event_id = serializers.IntegerField()
    attendances = serializers.ListField(
        child=serializers.DictField()
    )


class AttendanceStatisticsSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.__str__", read_only=True)

    class Meta:
        model = AttendanceStatistics
        fields = "__all__"


class GroupStatisticsSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = GroupStatistics
        fields = "__all__"
