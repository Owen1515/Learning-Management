from django import forms
from django.contrib import admin

from accounts.widgets import PortalDateInput

from .models import Assessment, StudentGrade


class AssessmentAdminForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = "__all__"

        widgets = {
            "assessment_date": PortalDateInput(),
        }


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    form = AssessmentAdminForm

    list_display = (
        "title",
        "assessment_type",
        "teacher_assignment",
        "term",
        "maximum_score",
        "weight",
        "assessment_date",
        "is_published",
    )

    list_filter = (
        "assessment_type",
        "term",
        "is_published",
        "teacher_assignment__classroom",
        "teacher_assignment__subject",
    )

    search_fields = (
        "title",
        "teacher_assignment__teacher__first_name",
        "teacher_assignment__teacher__last_name",
        "teacher_assignment__subject__name",
        "teacher_assignment__classroom__name",
    )


@admin.register(StudentGrade)
class StudentGradeAdmin(admin.ModelAdmin):
    list_display = (
        "student_enrollment",
        "assessment",
        "score",
        "percentage_display",
    )

    list_filter = (
        "assessment__term",
        "assessment__teacher_assignment__classroom",
        "assessment__teacher_assignment__subject",
    )

    search_fields = (
        "student_enrollment__student__student_number",
        "student_enrollment__student__first_name",
        "student_enrollment__student__last_name",
        "assessment__title",
    )

    def percentage_display(self, obj):
        value = obj.percentage

        if value is None:
            return "-"

        return f"{value:.2f}%"

    percentage_display.short_description = "Percentage"

from .models import TermReport


@admin.register(TermReport)
class TermReportAdmin(admin.ModelAdmin):
    list_display = (
        "student_enrollment", "term", "days_school_open", "days_present",
        "days_absent_display", "times_late", "promotion_status",
    )
    list_filter = ("term", "promotion_status", "student_enrollment__classroom")
    search_fields = (
        "student_enrollment__student__student_number",
        "student_enrollment__student__first_name",
        "student_enrollment__student__last_name",
    )

    def days_absent_display(self, obj):
        return obj.days_absent

    days_absent_display.short_description = "Days Absent"
