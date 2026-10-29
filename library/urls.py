from django.urls import path
from . import views

app_name = "library"

urlpatterns = [
    # Student
    path("", views.student_library, name="student_library"),
    path("document/<int:pk>/", views.view_document, name="view_document"),
    # Teacher
    path("teacher/", views.teacher_library, name="teacher_library"),
    path("teacher/upload/", views.upload_document, name="upload_document"),
    path("teacher/edit/<int:pk>/", views.edit_document, name="edit_document"),
    path("teacher/delete/<int:pk>/", views.delete_document, name="delete_document"),
    # AI
    path("teacher/ai-scheme/", views.marking_scheme_generator, name="marking_scheme_generator"),
    path("teacher/ai-scheme/generate/", views.generate_marking_scheme, name="generate_marking_scheme"),
    path("teacher/ai-scheme/save/", views.save_scheme_to_library, name="save_scheme_to_library"),
]
