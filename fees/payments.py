import logging
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.urls import reverse
from django.utils import timezone
from paynow import Paynow

from .models import EcoCashPaymentAttempt, FeePayment

logger = logging.getLogger(__name__)


class PaymentGatewayError(Exception):
    pass


def _callback_url(request, configured_url, route_name, reference):
    base_url = configured_url or request.build_absolute_uri(reverse(route_name))
    parts = urlsplit(base_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["reference"] = reference
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _paynow(request, reference):
    integration_id = settings.PAYNOW_INTEGRATION_ID
    integration_key = settings.PAYNOW_INTEGRATION_KEY
    if not integration_id or not integration_key:
        raise ImproperlyConfigured("Paynow integration credentials are not configured.")

    return Paynow(
        integration_id,
        integration_key,
        _callback_url(request, settings.PAYNOW_RETURN_URL, "fees:payment_return", reference),
        _callback_url(request, settings.PAYNOW_RESULT_URL, "fees:paynow_result", reference),
    )


def start_ecocash_payment(request, attempt):
    try:
        paynow = _paynow(request, attempt.reference)
        payment = paynow.create_payment(
            attempt.reference,
            attempt.payer_email,
        )
        payment.add(f"School fees {attempt.term}", attempt.amount)
        response = paynow.send_mobile(payment, attempt.payer_phone, "ecocash")
    except ImproperlyConfigured:
        raise
    except Exception as exc:
        logger.exception("Paynow EcoCash initiation failed for %s", attempt.reference)
        raise PaymentGatewayError("The payment request could not be started. Please try again later.") from exc

    if not response.success or not response.poll_url:
        logger.warning("Paynow rejected EcoCash initiation for %s", attempt.reference)
        raise PaymentGatewayError("Paynow could not start this payment. Check the EcoCash number and try again.")

    poll_host = urlsplit(response.poll_url).hostname or ""
    if not (poll_host == "paynow.co.zw" or poll_host.endswith(".paynow.co.zw")):
        raise PaymentGatewayError("Paynow returned an invalid payment status address.")

    attempt.poll_url = response.poll_url
    attempt.save(update_fields=["poll_url", "updated_at"])
    return getattr(response, "instructions", "Approve the payment prompt on your EcoCash phone.")


def refresh_ecocash_attempt(request, attempt):
    if attempt.status != "PENDING" or not attempt.poll_url:
        return attempt

    try:
        status_response = _paynow(request, attempt.reference).check_transaction_status(attempt.poll_url)
    except Exception:
        logger.exception("Paynow status check failed for %s", attempt.reference)
        return attempt

    provider_status = str(getattr(status_response, "status", "")).lower()
    is_paid = bool(getattr(status_response, "paid", False)) or provider_status == "paid"
    is_failed = provider_status in {"cancelled", "failed", "refunded", "disputed"}

    with transaction.atomic():
        locked_attempt = EcoCashPaymentAttempt.objects.select_for_update().select_related(
            "student", "term"
        ).get(pk=attempt.pk)
        if locked_attempt.status == "PENDING" and is_paid:
            payment = FeePayment.objects.create(
                student=locked_attempt.student,
                term=locked_attempt.term,
                amount=locked_attempt.amount,
                currency=locked_attempt.currency,
                payment_method="ECOCASH",
                reference=locked_attempt.reference,
                payment_date=timezone.localdate(),
                recorded_by="Paynow EcoCash",
                notes="Provider-confirmed payment",
            )
            locked_attempt.fee_payment = payment
            locked_attempt.status = "PAID"
            locked_attempt.save(update_fields=["fee_payment", "status", "updated_at"])
        elif locked_attempt.status == "PENDING" and is_failed:
            locked_attempt.status = "FAILED"
            locked_attempt.save(update_fields=["status", "updated_at"])
        attempt = locked_attempt

    return attempt


def complete_demo_payment(attempt, outcome="paid"):
    if not settings.PAYMENTS_DEMO_MODE:
        raise ImproperlyConfigured("Demo payments are not enabled.")
    if outcome not in {"paid", "failed"}:
        raise ValueError("Invalid demo payment outcome.")
    status = "DEMO_PAID" if outcome == "paid" else "DEMO_FAILED"
    EcoCashPaymentAttempt.objects.filter(pk=attempt.pk, status="DEMO").update(
        status=status, updated_at=timezone.now()
    )
    attempt.refresh_from_db()
    return attempt