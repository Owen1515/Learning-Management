from django import forms
from django.contrib import admin

from accounts.widgets import PortalDateInput

from .models import (
    SchoolProfile,
    SchoolYear,
    Term,
    GradeLevel,
    ClassRoom,
    Subject,
    StudentEnrollment,
    TeacherAssignment,
    ContactInquiry,
)


class SchoolYearAdminForm(forms.ModelForm):
    class Meta:
        model = SchoolYear
        fields = "__all__"

        widgets = {
            "start_date": PortalDateInput(),
            "end_date": PortalDateInput(),
        }


class TermAdminForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = "__all__"

        widgets = {
            "start_date": PortalDateInput(),
            "end_date": PortalDateInput(),
        }


class StudentEnrollmentAdminForm(forms.ModelForm):
    class Meta:
        model = StudentEnrollment
        fields = "__all__"

        widgets = {
            "enrollment_date": PortalDateInput(),
        }


@admin.register(SchoolProfile)
class SchoolProfileAdmin(admin.ModelAdmin):
    list_display = (
        "school_name",
        "telephone",
        "email",
        "principal_name",
    )


@admin.register(SchoolYear)
class SchoolYearAdmin(admin.ModelAdmin):
    form = SchoolYearAdminForm

    list_display = (
        "name",
        "start_date",
        "end_date",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
    )


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    form = TermAdminForm

    list_display = (
        "school_year",
        "number",
        "start_date",
        "end_date",
        "is_active",
    )

    list_filter = (
        "school_year",
        "number",
        "is_active",
    )


@admin.register(GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    list_display = (
        "level_number",
        "name",
    )

    ordering = (
        "level_number",
    )


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "grade_level",
        "school_year",
        "form_teacher",
        "is_active",
    )

    list_filter = (
        "school_year",
        "grade_level",
        "is_active",
    )

    search_fields = (
        "name",
    )


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "is_active",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "code",
        "name",
    )


@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    form = StudentEnrollmentAdminForm

    list_display = (
        "student",
        "classroom",
        "school_year",
        "enrollment_date",
        "is_active",
    )

    list_filter = (
        "school_year",
        "classroom",
        "is_active",
    )

    search_fields = (
        "student__student_number",
        "student__first_name",
        "student__last_name",
    )


@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "teacher",
        "subject",
        "classroom",
        "school_year",
        "is_active",
    )

    list_filter = (
        "school_year",
        "classroom",
        "subject",
        "is_active",
    )

    search_fields = (
        "teacher__employee_number",
        "teacher__first_name",
        "teacher__last_name",
        "subject__name",
        "subject__code",
    )


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "topic", "status", "created_at")
    list_filter = ("status", "topic", "created_at")
    search_fields = ("name", "email", "phone", "message")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)