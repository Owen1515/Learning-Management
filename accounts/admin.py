from django import forms
from django.contrib import admin

from .models import UserProfile, TeacherProfile, StudentProfile
from .widgets import PortalDateInput


class TeacherProfileAdminForm(forms.ModelForm):
    class Meta:
        model = TeacherProfile
        fields = "__all__"

        widgets = {
            "date_employed": PortalDateInput(),
        }


class StudentProfileAdminForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = "__all__"

        widgets = {
            "date_of_birth": PortalDateInput(),
            "admission_date": PortalDateInput(),
        }


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "role",
        "phone_number",
        "is_active",
        "created_at",
    )

    list_filter = (
        "role",
        "is_active",
    )

    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "phone_number",
    )


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    form = TeacherProfileAdminForm

    list_display = (
        "employee_number",
        "first_name",
        "last_name",
        "email",
        "date_employed",
    )

    search_fields = (
        "employee_number",
        "first_name",
        "last_name",
        "email",
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    form = StudentProfileAdminForm

    list_display = (
        "student_number",
        "first_name",
        "last_name",
        "date_of_birth",
        "admission_date",
    )

    search_fields = (
        "student_number",
        "first_name",
        "last_name",
    )