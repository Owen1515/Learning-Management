from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from academics.models import ClassRoom, StudentEnrollment
from .models import StudentProfile, UserProfile


class ActiveClassField(forms.ModelChoiceField):
    def label_from_instance(self, classroom):
        return (
            f"{classroom.grade_level.name} - {classroom.name} "
            f"({classroom.school_year.name})"
        )


class StudentRegistrationForm(forms.Form):
    student_number = forms.CharField(
        label="Student number",
        max_length=30,
        help_text="Use the student number issued by the school.",
    )
    first_name = forms.CharField(label="First name", max_length=100)
    last_name = forms.CharField(label="Last name", max_length=100)
    date_of_birth = forms.DateField(
        label="Date of birth",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    classroom = ActiveClassField(
        queryset=ClassRoom.objects.none(),
        label="Class for enrolment",
        empty_label="Choose a class",
    )
    guardian_name = forms.CharField(label="Parent or guardian name", max_length=150)
    guardian_relationship = forms.ChoiceField(
        label="Relationship to student",
        choices=(
            ("", "Choose a relationship"),
            ("Mother", "Mother"),
            ("Father", "Father"),
            ("Guardian", "Guardian"),
            ("Other", "Other"),
        ),
    )
    guardian_phone = forms.CharField(
        label="Parent or guardian phone",
        max_length=20,
    )
    guardian_email = forms.EmailField(
        label="Parent or guardian email",
        required=False,
    )
    home_address = forms.CharField(
        label="Home address",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    previous_school = forms.CharField(
        label="Previous school",
        max_length=150,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["classroom"].queryset = ClassRoom.objects.filter(
            is_active=True,
            school_year__is_active=True,
        ).select_related("grade_level", "school_year")

        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            )

    def clean_student_number(self):
        student_number = self.cleaned_data["student_number"].strip()
        if StudentProfile.objects.filter(student_number__iexact=student_number).exists():
            raise ValidationError("This student number is already registered.")
        if User.objects.filter(username__iexact=student_number).exists():
            raise ValidationError("This student number is already in use.")
        return student_number

    def save(self, admission_date):
        if not self.is_valid():
            raise ValueError("Cannot save an invalid student registration form.")

        data = self.cleaned_data
        user = User(
            username=data["student_number"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            is_active=False,
        )
        user.set_unusable_password()
        user.save()

        user_profile = UserProfile.objects.create(
            user=user,
            role="STUDENT",
            phone_number=data["guardian_phone"],
            is_active=False,
        )
        student = StudentProfile.objects.create(
            user_profile=user_profile,
            student_number=data["student_number"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            date_of_birth=data["date_of_birth"],
            admission_date=admission_date,
            guardian_name=data["guardian_name"],
            guardian_relationship=data["guardian_relationship"],
            guardian_phone=data["guardian_phone"],
            guardian_email=data["guardian_email"],
            home_address=data["home_address"],
            previous_school=data["previous_school"],
        )
        classroom = data["classroom"]
        StudentEnrollment.objects.create(
            student=student,
            classroom=classroom,
            school_year=classroom.school_year,
            enrollment_date=admission_date,
        )
        return student