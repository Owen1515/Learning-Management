from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        views.portal_login,
        name="login",
    ),

    path(
        "logout/",
        views.portal_logout,
        name="logout",
    ),

    path(
        "teacher/dashboard/",
        views.teacher_dashboard,
        name="teacher_dashboard",
    ),

    path(
        "teacher/class/<int:assignment_id>/",
        views.teacher_class_detail,
        name="teacher_class_detail",
    ),

    path(
        "teacher/class/<int:assignment_id>/assessment/create/",
        views.teacher_create_assessment,
        name="teacher_create_assessment",
    ),

    path(
        "teacher/assessment/<int:assessment_id>/grades/",
        views.teacher_grade_entry,
        name="teacher_grade_entry",
    ),

    path(
        "teacher/assessment/<int:assessment_id>/publish/",
        views.teacher_toggle_publish,
        name="teacher_toggle_publish",
    ),

    path(
        "student/dashboard/",
        views.student_dashboard,
        name="student_dashboard",
    ),

    path(
        "student/report-card/",
        views.student_report_card,
        name="student_report_card",
    ),
]