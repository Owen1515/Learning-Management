from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):

    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class TeacherProfile(models.Model):

    user_profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='teacher_profile'
    )

    employee_number = models.CharField(
        max_length=30,
        unique=True
    )

    first_name = models.CharField(
        max_length=100
    )

    last_name = models.CharField(
        max_length=100
    )

    email = models.EmailField(
        blank=True
    )

    date_employed = models.DateField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class StudentProfile(models.Model):

    user_profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )

    student_number = models.CharField(
        max_length=30,
        unique=True
    )

    first_name = models.CharField(
        max_length=100
    )

    last_name = models.CharField(
        max_length=100
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    admission_date = models.DateField(
        null=True,
        blank=True
    )

    guardian_name = models.CharField(
        max_length=150,
        blank=True
    )

    guardian_relationship = models.CharField(
        max_length=50,
        blank=True
    )

    guardian_phone = models.CharField(
        max_length=20,
        blank=True
    )

    guardian_email = models.EmailField(
        blank=True
    )

    home_address = models.TextField(
        blank=True
    )

    previous_school = models.CharField(
        max_length=150,
        blank=True
    )

    def __str__(self):
        return f"{self.student_number} - {self.first_name} {self.last_name}"