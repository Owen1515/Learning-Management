from django.db import models

from academics.models import (
    SchoolYear,
    Term,
    ClassRoom,
    Subject,
    TeacherAssignment,
    StudentEnrollment,
)


class Assessment(models.Model):
    ASSESSMENT_TYPES = [
        ("QUIZ", "Quiz"),
        ("TEST", "Test"),
        ("ASSIGNMENT", "Assignment"),
        ("PROJECT", "Project"),
        ("EXAM", "Exam"),
        ("OTHER", "Other"),
    ]

    teacher_assignment = models.ForeignKey(
        TeacherAssignment,
        on_delete=models.CASCADE,
        related_name="assessments",
    )

    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name="assessments",
    )

    title = models.CharField(
        max_length=150
    )

    assessment_type = models.CharField(
        max_length=20,
        choices=ASSESSMENT_TYPES,
    )

    maximum_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=100,
    )

    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage weight toward the term grade. Example: 20 for 20%",
    )

    assessment_date = models.DateField()

    is_published = models.BooleanField(
        default=False,
        help_text="Students can only see results when this is published.",
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "term",
            "assessment_date",
            "title",
        ]

    def __str__(self):
        return (
            f"{self.teacher_assignment.classroom.name} - "
            f"{self.teacher_assignment.subject.name} - "
            f"{self.title}"
        )


class StudentGrade(models.Model):
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="student_grades",
    )

    student_enrollment = models.ForeignKey(
        StudentEnrollment,
        on_delete=models.CASCADE,
        related_name="grades",
    )

    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )

    comment = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "assessment",
            "student_enrollment__student__last_name",
            "student_enrollment__student__first_name",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assessment",
                    "student_enrollment",
                ],
                name="unique_student_grade_per_assessment",
            )
        ]

    def __str__(self):
        return (
            f"{self.student_enrollment.student} - "
            f"{self.assessment.title}"
        )

    @property
    def percentage(self):
        if self.score is None:
            return None

        if self.assessment.maximum_score == 0:
            return None

        return (
            self.score
            / self.assessment.maximum_score
        ) * 100

class TermReport(models.Model):
    PROMOTION_CHOICES = [
        ("PENDING", "Pending"),
        ("PROMOTED", "Promoted"),
        ("NOT_PROMOTED", "Not Promoted"),
    ]

    student_enrollment = models.ForeignKey(
        StudentEnrollment, on_delete=models.CASCADE, related_name="term_reports"
    )
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="student_reports")
    days_school_open = models.PositiveIntegerField(default=0)
    days_present = models.PositiveIntegerField(default=0)
    times_late = models.PositiveIntegerField(default=0)
    form_teacher_comment = models.TextField(blank=True)
    principal_comment = models.TextField(blank=True)
    promotion_status = models.CharField(max_length=20, choices=PROMOTION_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["term__number", "student_enrollment__student__last_name"]
        constraints = [
            models.UniqueConstraint(fields=["student_enrollment", "term"], name="unique_student_term_report")
        ]

    @property
    def days_absent(self):
        return max(self.days_school_open - self.days_present, 0)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.student_enrollment_id and self.term_id:
            if self.student_enrollment.school_year_id != self.term.school_year_id:
                raise ValidationError("The selected term must belong to the student's school year.")
        if self.days_present > self.days_school_open:
            raise ValidationError("Days present cannot be greater than days school was open.")

    def __str__(self):
        return f"{self.student_enrollment.student} - {self.term}"
