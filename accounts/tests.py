from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from academics.models import ClassRoom, GradeLevel, SchoolYear, StudentEnrollment
from .models import StudentProfile, UserProfile


class StudentRegistrationTests(TestCase):
	def setUp(self):
		self.school_year = SchoolYear.objects.create(
			name="2026",
			start_date="2026-01-01",
			end_date="2026-12-31",
			is_active=True,
		)
		grade = GradeLevel.objects.create(name="Form 1", level_number=1)
		self.classroom = ClassRoom.objects.create(
			name="1A",
			grade_level=grade,
			school_year=self.school_year,
		)

	def test_registration_creates_student_profile_and_enrollment(self):
		response = self.client.post(
			reverse("accounts:student_registration"),
			{
				"student_number": "NH-2026-001",
				"first_name": "Tariro",
				"last_name": "Moyo",
				"date_of_birth": "2012-04-10",
				"classroom": self.classroom.pk,
				"guardian_name": "Rudo Moyo",
				"guardian_relationship": "Mother",
				"guardian_phone": "+263771234567",
				"guardian_email": "rudo@example.com",
				"home_address": "Chivi",
				"previous_school": "Local Primary School",
			},
		)

		self.assertRedirects(
			response,
			reverse("accounts:student_registration_complete"),
		)
		student = StudentProfile.objects.get(student_number="NH-2026-001")
		self.assertEqual(student.guardian_name, "Rudo Moyo")
		self.assertEqual(student.guardian_phone, "+263771234567")
		self.assertEqual(student.previous_school, "Local Primary School")

		user = User.objects.get(username="NH-2026-001")
		self.assertFalse(user.is_active)
		self.assertFalse(student.user_profile.is_active)
		self.assertEqual(student.user_profile.role, "STUDENT")

		enrollment = StudentEnrollment.objects.get(student=student)
		self.assertEqual(enrollment.classroom, self.classroom)
		self.assertEqual(enrollment.school_year, self.school_year)
		self.assertTrue(enrollment.is_active)

	def test_duplicate_student_number_does_not_create_a_second_enrollment(self):
		self.client.post(
			reverse("accounts:student_registration"),
			{
				"student_number": "NH-2026-001",
				"first_name": "Tariro",
				"last_name": "Moyo",
				"date_of_birth": "2012-04-10",
				"classroom": self.classroom.pk,
				"guardian_name": "Rudo Moyo",
				"guardian_relationship": "Mother",
				"guardian_phone": "+263771234567",
				"home_address": "Chivi",
			},
		)
		response = self.client.post(
			reverse("accounts:student_registration"),
			{
				"student_number": "NH-2026-001",
				"first_name": "Tariro",
				"last_name": "Moyo",
				"date_of_birth": "2012-04-10",
				"classroom": self.classroom.pk,
				"guardian_name": "Rudo Moyo",
				"guardian_relationship": "Mother",
				"guardian_phone": "+263771234567",
				"home_address": "Chivi",
			},
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(StudentProfile.objects.count(), 1)
		self.assertEqual(StudentEnrollment.objects.count(), 1)
		self.assertIn("This student number is already registered.", response.content.decode())
