import json
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.models import StudentProfile
from .forms import EcoCashCheckoutForm, normalize_zimbabwe_phone
from .models import EcoCashPaymentAttempt, TermFee, FeePayment
from .payments import (
    PaymentGatewayError,
    complete_demo_payment,
    refresh_ecocash_attempt,
    start_ecocash_payment,
)


@staff_member_required
def fees_overview(request):
    from academics.models import SchoolYear, StudentEnrollment

    school_years    = SchoolYear.objects.all().order_by("-start_date")
    selected_year   = request.GET.get("year")
    selected_status = request.GET.get("status")

    year_obj = None
    if selected_year:
        year_obj = school_years.filter(pk=selected_year).first()
    if not year_obj:
        year_obj = school_years.first()

    if year_obj:
        enrollments = StudentEnrollment.objects.filter(
            school_year=year_obj, is_active=True
        ).select_related("student", "classroom").order_by(
            "classroom__name", "student__last_name"
        )
    else:
        enrollments = StudentEnrollment.objects.filter(
            is_active=True
        ).select_related("student", "classroom")

    student_rows = []
    total_billed = total_collected = total_outstanding = total_collected_zwg = 0
    paid_count = outstanding_count = 0
    total_students = enrollments.values("student").distinct().count()
    seen = set()

    for enr in enrollments:
        s = enr.student
        if s.id in seen:
            continue
        seen.add(s.id)

        terms = year_obj.terms.all() if year_obj else []
        billed = 0
        for t in terms:
            fee = TermFee.objects.filter(term=t).first()
            if fee:
                billed += float(fee.total_usd or 0)

        pay_filter = {"student": s}
        if year_obj:
            pay_filter["term__school_year"] = year_obj

        paid_usd = float(FeePayment.objects.filter(**pay_filter, currency="USD").aggregate(t=Sum("amount"))["t"] or 0)
        paid_zwg = float(FeePayment.objects.filter(**pay_filter, currency="ZWG").aggregate(t=Sum("amount"))["t"] or 0)
        balance  = billed - paid_usd
        pct      = min((paid_usd / billed * 100) if billed > 0 else 0, 100)

        if balance <= 0:
            status = "paid"
        elif paid_usd > 0:
            status = "partial"
        else:
            status = "due"

        if selected_status and status != selected_status:
            continue

        total_billed        += billed
        total_collected     += paid_usd
        total_collected_zwg += paid_zwg
        total_outstanding   += max(balance, 0)
        if status == "paid":
            paid_count += 1
        else:
            outstanding_count += 1

        student_rows.append({
            "student":   s,
            "classroom": enr.classroom.name,
            "billed":    round(billed, 2),
            "paid":      round(paid_usd, 2),
            "balance":   round(balance, 2),
            "pct":       round(pct, 1),
            "status":    status,
        })

    collection_pct = (total_collected / total_billed * 100) if total_billed > 0 else 0

    # Term chart data
    terms_qs = year_obj.terms.all().order_by("number") if year_obj else []
    term_labels, term_billed_data, term_collected_data = [], [], []
    for term in terms_qs:
        fee = TermFee.objects.filter(term=term).first()
        b = float(fee.total_usd or 0) if fee else 0
        c = float(FeePayment.objects.filter(term=term, currency="USD").aggregate(t=Sum("amount"))["t"] or 0)
        term_labels.append(str(term))
        term_billed_data.append(round(b, 2))
        term_collected_data.append(round(c, 2))

    paid_n    = sum(1 for r in student_rows if r["status"] == "paid")
    partial_n = sum(1 for r in student_rows if r["status"] == "partial")
    due_n     = sum(1 for r in student_rows if r["status"] == "due")

    return render(request, "admin/fees/fees_overview.html", {
        # Make it feel native to admin
        "title": "Fees Overview Dashboard",
        "has_permission": True,
        # Data
        "total_billed":        round(total_billed, 2),
        "total_collected":     round(total_collected, 2),
        "total_outstanding":   round(total_outstanding, 2),
        "total_collected_zwg": round(total_collected_zwg, 2),
        "collection_pct":      round(collection_pct, 1),
        "paid_count":          paid_count,
        "outstanding_count":   outstanding_count,
        "total_students":      total_students,
        "student_rows":        student_rows,
        "school_years":        school_years,
        "selected_year":       selected_year or (str(year_obj.pk) if year_obj else ""),
        "selected_status":     selected_status or "",
        "term_chart_data":     json.dumps({"labels": term_labels, "billed": term_billed_data, "collected": term_collected_data}),
        "status_chart_data":   json.dumps({"paid": paid_n, "partial": partial_n, "due": due_n}),
    })


def ecocash_checkout(request):
    form = EcoCashCheckoutForm(request.POST or None)
    form.fields["payer_email"].initial = settings.PAYNOW_AUTH_EMAIL
    errors = []

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        student = StudentProfile.objects.filter(
            student_number__iexact=data["student_number"].strip()
        ).first()
        try:
            recorded_phone = normalize_zimbabwe_phone(student.guardian_phone) if student else ""
        except ValidationError:
            recorded_phone = ""

        if not student or recorded_phone != data["guardian_phone"]:
            errors.append("We could not verify those details. Check them with the school office.")
        else:
            attempt = None
            try:
                with transaction.atomic():
                    locked_student = StudentProfile.objects.select_for_update().get(pk=student.pk)
                    schedule = TermFee.objects.select_for_update().filter(
                        pk=data["fee_schedule"].pk,
                        is_published=True,
                    ).select_related("term").first()
                    if not schedule:
                        errors.append("That fee schedule is no longer available.")
                    else:
                        paid = FeePayment.objects.filter(
                            student=locked_student,
                            term=schedule.term,
                            currency="USD",
                        ).aggregate(total=Sum("amount"))["total"] or 0
                        pending = EcoCashPaymentAttempt.objects.filter(
                            student=locked_student,
                            term=schedule.term,
                            currency="USD",
                            status="PENDING",
                        ).aggregate(total=Sum("amount"))["total"] or 0
                        remaining = schedule.total_usd - paid - pending
                        if data["amount"] > remaining:
                            errors.append("The amount is greater than the remaining USD balance for this term.")
                        else:
                            demo_mode = settings.DEBUG and settings.PAYMENTS_DEMO_MODE
                            attempt = EcoCashPaymentAttempt.objects.create(
                                student=locked_student,
                                term=schedule.term,
                                amount=data["amount"],
                                currency="USD",
                                payer_phone=data["payer_phone"],
                                payer_email=data["payer_email"],
                                reference=f"NH{uuid.uuid4().hex[:22].upper()}",
                                status="DEMO" if demo_mode else "PENDING",
                            )
            except Exception:
                errors.append("We could not start this payment. Please try again or contact the school.")

            if attempt and not errors:
                if attempt.status == "PENDING":
                    try:
                        instructions = start_ecocash_payment(request, attempt)
                        request.session[f"ecocash_instructions_{attempt.reference}"] = instructions
                    except PaymentGatewayError as exc:
                        attempt.status = "FAILED"
                        attempt.save(update_fields=["status", "updated_at"])
                        errors.append(str(exc))
                    except Exception:
                        attempt.status = "FAILED"
                        attempt.save(update_fields=["status", "updated_at"])
                        errors.append("Online payments are not configured yet. Contact the school office.")
                if not errors:
                    return redirect("fees:payment_status", reference=attempt.reference)

    return render(request, "fees/ecocash_checkout.html", {
        "form": form,
        "errors": errors,
        "demo_mode": settings.DEBUG and settings.PAYMENTS_DEMO_MODE,
        "gateway_configured": bool(settings.PAYNOW_INTEGRATION_ID and settings.PAYNOW_INTEGRATION_KEY),
        "receiver_name": settings.ECOCASH_RECEIVER_NAME,
        "receiver_phone": settings.ECOCASH_RECEIVER_PHONE,
        "default_email": settings.PAYNOW_AUTH_EMAIL,
    })


def ecocash_payment_status(request, reference):
    attempt = get_object_or_404(EcoCashPaymentAttempt, reference=reference)
    instructions = request.session.pop(f"ecocash_instructions_{reference}", "")
    if request.method == "POST":
        if attempt.status == "DEMO":
            complete_demo_payment(attempt)
        elif attempt.status == "PENDING":
            attempt = refresh_ecocash_attempt(request, attempt)
    return render(request, "fees/ecocash_status.html", {
        "attempt": attempt,
        "instructions": instructions,
        "is_demo": attempt.status in {"DEMO", "DEMO_PAID"},
    })


def ecocash_payment_return(request):
    reference = request.GET.get("reference", "")
    if reference and EcoCashPaymentAttempt.objects.filter(reference=reference).exists():
        return redirect("fees:payment_status", reference=reference)
    return redirect("fees:ecocash_checkout")


@csrf_exempt
@require_POST
def paynow_result(request):
    reference = request.POST.get("reference", "")
    attempt = EcoCashPaymentAttempt.objects.filter(reference=reference).first()
    if attempt and attempt.status == "PENDING":
        refresh_ecocash_attempt(request, attempt)
    return HttpResponse(status=204)
