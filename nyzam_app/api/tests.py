import shutil
from datetime import date, time
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from attendance.models import Attendance
from events.models import Event
from students.models import Group, Student

User = get_user_model()


def build_test_image():
    return SimpleUploadedFile(
        "student.jpg",
        (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
            b"\xff\xdb\x00C\x00"
            + b"\x08" * 64
            + b"\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01"
            + b"\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08"
            + b"\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            + b"\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xd2\xcf \xff\xd9"
        ),
        content_type="image/jpeg",
    )


class ApiIntegrationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_media_root = Path(__file__).resolve().parent.parent / "test_media"
        cls.temp_media_root.mkdir(exist_ok=True)
        cls.override = override_settings(MEDIA_ROOT=cls.temp_media_root)
        cls.override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.override.disable()
        shutil.rmtree(cls.temp_media_root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="senior1",
            password="testpass123",
            first_name="Ali",
            last_name="Valiyev",
            role="senior",
        )
        self.group = Group.objects.create(name="SE-101")
        self.student = Student.objects.create(
            first_name="Bek",
            last_name="Karimov",
            birth_date=date(2005, 5, 1),
            photo=build_test_image(),
            group=self.group,
            course="2",
            gender="male",
            dormitory="yes",
        )
        self.event = Event.objects.create(
            title="Morning lineup",
            event_type="morning",
            date=date.today(),
            start_time=time(8, 0),
            created_by=self.user,
        )

    def authenticate(self):
        response = self.client.post(
            "/auth/login/",
            {"username": "senior1", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}"
        )
        return response

    def test_login_returns_serialized_user_payload(self):
        response = self.client.post(
            "/auth/login/",
            {"username": "senior1", "password": "testpass123"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"]["username"], "senior1")
        self.assertEqual(response.data["user"]["full_name"], "Ali Valiyev")
        self.assertEqual(response.data["user"]["role"], "senior")

    def test_auth_me_returns_current_user(self):
        self.authenticate()

        response = self.client.get("/auth/me/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "senior1")
        self.assertEqual(response.data["full_name"], "Ali Valiyev")

    def test_students_list_includes_absolute_photo_url(self):
        self.authenticate()

        response = self.client.get("/students/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"][0]["group_name"], "SE-101")
        self.assertEqual(response.data["results"][0]["course"], "2")
        self.assertTrue(
            response.data["results"][0]["photo_url"].startswith("http://testserver/media/")
        )

    def test_students_can_be_filtered_by_course_and_group(self):
        self.authenticate()
        other_group = Group.objects.create(name="SE-201")
        Student.objects.create(
            first_name="Olim",
            last_name="Rustamov",
            birth_date=date(2004, 7, 10),
            photo=build_test_image(),
            group=other_group,
            course="3",
            gender="male",
            dormitory="no",
        )

        response = self.client.get(f"/students/?course=2&group={self.group.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.student.id)

    def test_student_can_be_created_with_course(self):
        self.authenticate()

        response = self.client.post(
            "/students/",
            {
                "first_name": "Sardor",
                "last_name": "Nabiyev",
                "birth_date": "2006-09-12",
                "photo": build_test_image(),
                "group": self.group.id,
                "course": "4",
                "gender": "male",
                "dormitory": "no",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["course"], "4")

    def test_student_creation_requires_room_number_for_dormitory(self):
        self.authenticate()

        response = self.client.post(
            "/students/",
            {
                "first_name": "Nilufar",
                "last_name": "Saidova",
                "birth_date": "2006-06-15",
                "photo": build_test_image(),
                "group": self.group.id,
                "course": "2",
                "gender": "female",
                "dormitory": "yes",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("room_number", response.data)

    def test_student_creation_allows_dormitory_room_number(self):
        self.authenticate()

        response = self.client.post(
            "/students/",
            {
                "first_name": "Samandar",
                "last_name": "Juraev",
                "birth_date": "2004-12-01",
                "photo": build_test_image(),
                "group": self.group.id,
                "course": "3",
                "gender": "male",
                "dormitory": "yes",
                "room_number": "101",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["room_number"], "101")

    def test_groups_can_be_filtered_by_course(self):
        self.authenticate()
        other_group = Group.objects.create(name="SE-301")
        Student.objects.create(
            first_name="Madina",
            last_name="Ergasheva",
            birth_date=date(2004, 3, 15),
            photo=build_test_image(),
            group=other_group,
            course="3",
            gender="female",
            dormitory="yes",
        )

        response = self.client.get("/groups/?course=2")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.group.id)

    def test_weekday_morning_attendance_api_creates_event_and_groups_students(self):
        self.authenticate()
        lld_group = Group.objects.create(name="LLD-01")
        lld_student = Student.objects.create(
            first_name="Aziza",
            last_name="Karimova",
            birth_date=date(2006, 1, 10),
            photo=build_test_image(),
            group=lld_group,
            course="LLD",
            gender="female",
            dormitory="yes",
        )

        response = self.client.post(
            "/events/ensure_weekday_morning_attendance/",
            {"date": "2026-04-03"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["event"]["event_type"], "morning")
        self.assertEqual(response.data["attendance_created"], 2)
        self.assertEqual(len(response.data["students_grouped"]), 2)
        self.assertEqual(response.data["students_grouped"][0]["course"], "LLD")
        self.assertEqual(response.data["students_grouped"][0]["groups"][0]["group_name"], "LLD-01")
        self.assertEqual(response.data["students_grouped"][1]["course"], "2")
        self.assertEqual(response.data["students_grouped"][1]["groups"][0]["group_name"], "SE-101")

        morning_event = Event.objects.get(
            date=date(2026, 4, 3),
            event_type="morning",
        )

        self.assertEqual(
            Attendance.objects.filter(student=self.student, event=morning_event).count(),
            1,
        )
        self.assertEqual(
            Attendance.objects.filter(student=lld_student, event=morning_event).count(),
            1,
        )

        second_response = self.client.post(
            "/events/ensure_weekday_morning_attendance/",
            {"date": "2026-04-03"},
            format="json",
        )

        self.assertEqual(second_response.status_code, 201)
        self.assertEqual(
            Event.objects.filter(
                date=date(2026, 4, 3),
                event_type="morning",
            ).count(),
            1,
        )
        self.assertEqual(
            Attendance.objects.filter(student=self.student, event=morning_event).count(),
            1,
        )

    def test_weekday_morning_attendance_api_rejects_weekends(self):
        self.authenticate()

        response = self.client.post(
            "/events/ensure_weekday_morning_attendance/",
            {"date": "2026-04-05"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            Event.objects.filter(date=date(2026, 4, 5), event_type="morning").count(),
            0,
        )

    def test_bulk_create_updates_existing_attendance(self):
        self.authenticate()

        first_response = self.client.post(
            "/attendance/bulk_create/",
            {
                "event_id": self.event.id,
                "attendances": [
                    {"student_id": self.student.id, "status": "present"},
                ],
            },
            format="json",
        )
        second_response = self.client.post(
            "/attendance/bulk_create/",
            {
                "event_id": self.event.id,
                "attendances": [
                    {
                        "student_id": self.student.id,
                        "status": "late",
                        "comments": "Traffic",
                    },
                ],
            },
            format="json",
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 201)
        self.assertEqual(Attendance.objects.count(), 1)
        attendance = Attendance.objects.get(student=self.student, event=self.event)
        self.assertEqual(attendance.status, "late")
        self.assertEqual(attendance.comments, "Traffic")
        self.assertEqual(len(second_response.data["updated"]), 1)
