from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from .models import TermFee, FeePayment


def fees_overview_redirect(request):
    return redirect("/fees/overview/")


class FeesAdminSite:
    pass


@admin.register(TermFee)
class TermFeeAdmin(admin.ModelAdmin):
    list_display  = ("term", "is_published", "due_date", "total_usd", "total_zwg")
    list_filter   = ("is_published", "term__school_year")
    list_editable = ("is_published",)
    ordering      = ("-term__school_year__start_date", "term__number")
    fieldsets = (
        ("Term", {"fields": ("term", "is_published", "due_date", "notes")}),
        ("USD Fees", {"fields": ("tuition_usd", "boarding_usd", "development_usd", "exam_usd", "other_usd", "other_label")}),
        ("ZWG Fees", {"fields": ("tuition_zwg", "boarding_zwg", "development_zwg", "exam_zwg", "other_zwg")}),
    )


    def get_urls(self):
        urls = super().get_urls()
        custom = [path("overview/", self.admin_site.admin_view(fees_overview_redirect), name="fees_overview")]
        return custom + urls


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display   = ("student", "term", "amount", "currency", "payment_method", "payment_date", "reference")
    list_filter    = ("currency", "payment_method", "term__school_year")
    search_fields  = ("student__first_name", "student__last_name", "student__student_number", "reference")
    ordering       = ("-payment_date",)
    date_hierarchy = "payment_date"
    autocomplete_fields = ["student"]

