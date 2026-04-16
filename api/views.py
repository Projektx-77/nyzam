# api/views.py
from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Avg, Sum
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from attendance.models import Attendance
from events.models import Event
from statistic.models import AttendanceStatistics, GroupStatistics
from students.models import Group, Student

from .serializers import (
    AttendanceSerializer,
    AttendanceStatisticsSerializer,
    BulkAttendanceSerializer,
    EventSerializer,
    GroupSerializer,
    GroupStatisticsSerializer,
    StudentSerializer,
    UserSerializer,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data["username"])
            response.data["user"] = UserSerializer(
                user,
                context={"request": request},
            ).data
        return response


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == "dean":
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Student.objects.all()

        group_id = self.request.query_params.get("group")
        if group_id:
            queryset = queryset.filter(group_id=group_id)

        course = self.request.query_params.get("course")
        if course:
            queryset = queryset.filter(course=course)

        dormitory = self.request.query_params.get("dormitory")
        if dormitory:
            queryset = queryset.filter(dormitory=dormitory)

        gender = self.request.query_params.get("gender")
        if gender:
            queryset = queryset.filter(gender=gender)

        return queryset.select_related("group").order_by("last_name", "first_name", "id")


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Group.objects.all()
        course = self.request.query_params.get("course")
        if course:
            queryset = queryset.filter(course=course)  # <-- главное исправление
        return queryset.order_by("name")





class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    COURSE_ORDER = ("LLD", "1", "2", "3", "4")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_queryset(self):
        queryset = Event.objects.all()

        date = self.request.query_params.get("date")
        if date:
            queryset = queryset.filter(date=date)

        event_type = self.request.query_params.get("event_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        return queryset.select_related("created_by")

    def _build_students_grouped_by_course(self, request, students):
        grouped = []

        for course in self.COURSE_ORDER:
            course_students = [student for student in students if student.course == course]
            if not course_students:
                continue

            groups_map = {}
            for student in course_students:
                group_key = student.group_id
                if group_key not in groups_map:
                    groups_map[group_key] = {
                        "group_id": student.group_id,
                        "group_name": student.group.name,
                        "students": [],
                    }
                groups_map[group_key]["students"].append(
                    StudentSerializer(student, context={"request": request}).data
                )

            grouped.append(
                {
                    "course": course,
                    "groups": sorted(
                        groups_map.values(),
                        key=lambda item: item["group_name"],
                    ),
                }
            )

        return grouped

    @action(detail=False, methods=["post"])
    def ensure_weekday_morning_attendance(self, request):
        raw_date = request.data.get("date")
        target_date = (
            datetime.strptime(raw_date, "%Y-%m-%d").date()
            if raw_date
            else timezone.localdate()
        )

        if target_date.weekday() >= 5:
            return Response(
                {
                    "date": target_date,
                    "message": "Morning attendance can only be created for weekdays.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        students = list(
            Student.objects.select_related("group").order_by(
                "course",
                "group__name",
                "last_name",
                "first_name",
                "id",
            )
        )

        with transaction.atomic():
            event, event_created = Event.objects.get_or_create(
                date=target_date,
                event_type="morning",
                defaults={
                    "title": "Morning Attendance",
                    "start_time": time(8, 0),
                    "created_by": request.user,
                },
            )

            created_count = 0
            existing_count = 0
            for student in students:
                _, attendance_created = Attendance.objects.get_or_create(
                    student=student,
                    event=event,
                    defaults={
                        "status": "absent",
                        "marked_by": request.user,
                        "reason": "",
                        "comments": "",
                    },
                )
                if attendance_created:
                    created_count += 1
                else:
                    existing_count += 1

        return Response(
            {
                "date": target_date,
                "weekday": target_date.strftime("%A"),
                "event": EventSerializer(event, context={"request": request}).data,
                "event_created": event_created,
                "attendance_created": created_count,
                "attendance_existing": existing_count,
                "students_grouped": self._build_students_grouped_by_course(request, students),
                "message": "Weekday morning attendance is ready.",
            },
            status=status.HTTP_201_CREATED,
        )


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(marked_by=self.request.user)

    def get_queryset(self):
        queryset = Attendance.objects.all()

        event_id = self.request.query_params.get("event_id")
        if event_id:
            queryset = queryset.filter(event_id=event_id)

        student_id = self.request.query_params.get("student_id")
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        date = self.request.query_params.get("date")
        if date:
            queryset = queryset.filter(event__date=date)

        return queryset.select_related("student", "event", "marked_by")

    @action(detail=False, methods=["post"])
    def bulk_create(self, request):
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        event_id = serializer.validated_data["event_id"]
        attendances = serializer.validated_data["attendances"]

        created = []
        updated = []
        errors = []

        with transaction.atomic():
            for att_data in attendances:
                try:
                    attendance, is_created = Attendance.objects.update_or_create(
                        student_id=att_data["student_id"],
                        event_id=event_id,
                        defaults={
                            "status": att_data.get("status", "present"),
                            "reason": att_data.get("reason", ""),
                            "comments": att_data.get("comments", ""),
                            "marked_by": request.user,
                        },
                    )
                    attendance_data = AttendanceSerializer(
                        attendance,
                        context={"request": request},
                    ).data
                    if is_created:
                        created.append(attendance_data)
                    else:
                        updated.append(attendance_data)
                except Exception as exc:
                    errors.append(
                        {
                            "student_id": att_data.get("student_id"),
                            "error": str(exc),
                        }
                    )

        self.update_statistics(event_id)

        return Response(
            {
                "created": created,
                "updated": updated,
                "errors": errors,
                "message": f"Processed {len(created) + len(updated)} attendance records",
            },
            status=status.HTTP_201_CREATED,
        )

    def update_statistics(self, event_id):
        try:
            event = Event.objects.get(id=event_id)

            students = Student.objects.all()
            for student in students:
                total_events = Event.objects.filter(date=event.date).count()
                attendance_data = Attendance.objects.filter(
                    student=student,
                    event__date=event.date,
                )

                present_count = attendance_data.filter(status="present").count()
                absent_count = attendance_data.filter(status="absent").count()
                late_count = attendance_data.filter(status="late").count()

                attendance_rate = (
                    present_count / total_events * 100 if total_events > 0 else 0
                )

                AttendanceStatistics.objects.update_or_create(
                    student=student,
                    date=event.date,
                    defaults={
                        "total_events": total_events,
                        "present_count": present_count,
                        "absent_count": absent_count,
                        "late_count": late_count,
                        "attendance_rate": attendance_rate,
                    },
                )

            groups = Group.objects.all()
            for group in groups:
                group_students = Student.objects.filter(group=group)
                if group_students.exists():
                    avg_attendance = (
                        AttendanceStatistics.objects.filter(
                            student__in=group_students,
                            date=event.date,
                        ).aggregate(avg=Avg("attendance_rate"))["avg"]
                        or 0
                    )

                    GroupStatistics.objects.update_or_create(
                        group=group,
                        date=event.date,
                        defaults={
                            "total_students": group_students.count(),
                            "average_attendance": avg_attendance,
                        },
                    )

        except Exception as exc:
            print(f"Error updating statistics: {exc}")


class StatisticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["get"])
    def summary_cards(self, request):
        today = request.query_params.get("date", timezone.now().date())

        total_students = Student.objects.count()
        today_attendance = Attendance.objects.filter(event__date=today)

        attended_statuses = ["present", "late", "excused"]
        today_on_classes = (
            today_attendance.filter(status__in=attended_statuses)
            .values("student_id")
            .distinct()
            .count()
        )
        today_absent = (
            today_attendance.filter(status="absent")
            .values("student_id")
            .distinct()
            .count()
        )

        attendance_percentage = (
            round((today_on_classes / total_students) * 100, 2)
            if total_students > 0
            else 0
        )

        return Response(
            {
                "date": today,
                "total_students": total_students,
                "today_on_classes": today_on_classes,
                "today_absent": today_absent,
                "attendance_percentage": attendance_percentage,
            }
        )

    @action(detail=False, methods=["get"])
    def student_statistics(self, request):
        student_id = request.query_params.get("student_id")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date", timezone.now().date())

        queryset = AttendanceStatistics.objects.filter(student_id=student_id)

        if start_date:
            queryset = queryset.filter(date__gte=start_date)

        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        serializer = AttendanceStatisticsSerializer(queryset, many=True)

        total_days = queryset.count()
        if total_days > 0:
            avg_rate = queryset.aggregate(avg=Avg("attendance_rate"))["avg"]
            total_present = queryset.aggregate(sum=Sum("present_count"))["sum"]
            total_absent = queryset.aggregate(sum=Sum("absent_count"))["sum"]
        else:
            avg_rate = 0
            total_present = 0
            total_absent = 0

        return Response(
            {
                "daily_stats": serializer.data,
                "summary": {
                    "total_days": total_days,
                    "average_attendance_rate": avg_rate,
                    "total_present": total_present,
                    "total_absent": total_absent,
                },
            }
        )

    @action(detail=False, methods=["get"])
    def group_statistics(self, request):
        group_id = request.query_params.get("group_id")
        date = request.query_params.get("date", timezone.now().date())

        stats = GroupStatistics.objects.filter(group_id=group_id, date=date).first()

        if stats:
            serializer = GroupStatisticsSerializer(stats)
            return Response(serializer.data)

        return Response(
            {"message": "Statistics not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    @action(detail=False, methods=["get"])
    def dashboard_stats(self, request):
        today = timezone.now().date()
        weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        total_students = Student.objects.count()
        total_groups = Group.objects.count()
        today_events = Event.objects.filter(date=today).count()

        today_attendance = Attendance.objects.filter(event__date=today)

        present_today = today_attendance.filter(status="present").count()
        absent_today = today_attendance.filter(status="absent").count()

        groups_stats = []
        groups = Group.objects.all()
        weekly_attendance = []

        for day_offset in range(6, -1, -1):
            current_date = today - timedelta(days=day_offset)
            current_attendance = Attendance.objects.filter(event__date=current_date)
            present_students = (
                current_attendance.filter(status__in=["present", "late", "excused"])
                .values("student_id")
                .distinct()
                .count()
            )
            attendance_rate = (
                round((present_students / total_students) * 100, 2)
                if total_students > 0
                else 0
            )

            weekly_attendance.append(
                {
                    "date": current_date,
                    "label": weekday_labels[current_date.weekday()],
                    "attendance_rate": attendance_rate,
                }
            )

        for group in groups:
            students_count = Student.objects.filter(group=group).count()
            if students_count > 0:
                attendance_rate = (
                    today_attendance.filter(
                        student__group=group,
                        status="present",
                    ).count()
                    / students_count
                    * 100
                )

                groups_stats.append(
                    {
                        "group_name": group.name,
                        "total_students": students_count,
                        "attendance_rate": attendance_rate,
                    }
                )

        return Response(
            {
                "total_students": total_students,
                "total_groups": total_groups,
                "today_events": today_events,
                "today_present": present_today,
                "today_absent": absent_today,
                "weekly_attendance": weekly_attendance,
                "groups_stats": groups_stats,
            }
        )
