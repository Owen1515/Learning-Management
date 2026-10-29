from django.urls import path
from . import views

app_name = "fees"

urlpatterns = [
    path("overview/", views.fees_overview, name="overview"),
]
