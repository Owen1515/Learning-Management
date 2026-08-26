from django.db import models
from accounts.models import TeacherProfile, StudentProfile


class SchoolProfile(models.Model):
    school_name = models.CharField(
        max_length=200
    )

    motto = models.CharField(
        max_length=200,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    telephone = models.CharField(
        max_length=50,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    principal_name = models.CharField(
        max_length=150,
        blank=True
    )

    logo = models.ImageField(
        upload_to="school/",
        blank=True,
        null=True
    )

    primary_color = models.CharField(
        max_length=20,
        default="#1f4e78",
        help_text="Example: #1f4e78"
    )

    secondary_color = models.CharField(
        max_length=20,
        default="#198754",
        help_text="Example: #198754"
    )

    def __str__(self):
        return self.school_name


class SchoolYear(models.Model):
    name = models.CharField(
        max_length=20,
        unique=True,
        help_text="Example: 2026-2027"
    )

    start_date = models.DateField()
    end_date = models.DateField()

    is_active = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return self.name


class Term(models.Model):
    TERM_CHOICES = [
        (1, "Term 1"),
        (2, "Term 2"),
        (3, "Term 3"),
    ]

    school_year = models.ForeignKey(
        SchoolYear,
        on_delete=models.CASCADE,
        related_name="terms"
    )

    number = models.PositiveSmallIntegerField(
        choices=TERM_CHOICES
    )

    start_date = models.DateField()
    end_date = models.DateField()

    is_active = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ["school_year", "number"]

        constraints = [
            models.UniqueConstraint(
                fields=["school_year", "number"],
                name="unique_term_per_school_year"
            )
        ]

    def __str__(self):
        return (
            f"{self.school_year} - "
            f"{self.get_number_display()}"
        )


class GradeLevel(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True
    )

    level_number = models.PositiveSmallIntegerField(
        unique=True
    )

    class Meta:
        ordering = ["level_number"]

    def __str__(self):
        return self.name


class ClassRoom(models.Model):
    name = models.CharField(
        max_length=50
    )

    grade_level = models.ForeignKey(
        GradeLevel,
        on_delete=models.PROTECT,
        related_name="classes"
    )

    school_year = models.ForeignKey(
        SchoolYear,
        on_delete=models.CASCADE,
        related_name="classes"
    )

    form_teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="form_classes"
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = [
            "grade_level__level_number",
            "name"
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["name", "school_year"],
                name="unique_class_name_per_school_year"
            )
        ]

    def __str__(self):
        return (
            f"{self.name} - "
            f"{self.school_year}"
        )


class Subject(models.Model):
    code = models.CharField(
        max_length=20,
        unique=True
    )

    name = models.CharField(
        max_length=100,
        unique=True
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class StudentEnrollment(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="enrollments"
    )

    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name="student_enrollments"
    )

    school_year = models.ForeignKey(
        SchoolYear,
        on_delete=models.CASCADE,
        related_name="student_enrollments"
    )

    enrollment_date = models.DateField()

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = [
            "classroom__name",
            "student__last_name",
            "student__first_name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["student", "school_year"],
                name="unique_student_enrollment_per_school_year"
            )
        ]

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.classroom}"
        )


class TeacherAssignment(models.Model):
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="teaching_assignments"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name="teacher_assignments"
    )

    classroom = models.ForeignKey(
        ClassRoom,
        on_delete=models.CASCADE,
        related_name="teacher_assignments"
    )

    school_year = models.ForeignKey(
        SchoolYear,
        on_delete=models.CASCADE,
        related_name="teacher_assignments"
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = [
            "classroom__name",
            "subject__name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "teacher",
                    "subject",
                    "classroom",
                    "school_year",
                ],
                name="unique_teacher_subject_class_assignment"
            )
        ]

    def __str__(self):
        return (
            f"{self.teacher} - "
            f"{self.subject.name} - "
            f"{self.classroom.name}"
        )