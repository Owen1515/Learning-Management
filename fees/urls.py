from django.urls import path
from . import views

app_name = "fees"

urlpatterns = [
    path("ecocash/", views.ecocash_checkout, name="ecocash_checkout"),
    path("ecocash/return/", views.ecocash_payment_return, name="payment_return"),
    path("ecocash/result/", views.paynow_result, name="paynow_result"),
    path("ecocash/status/<str:reference>/", views.ecocash_payment_status, name="payment_status"),
    path("overview/", views.fees_overview, name="overview"),
]
