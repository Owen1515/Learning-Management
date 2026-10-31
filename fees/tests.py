from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import StudentProfile, UserProfile
from academics.models import SchoolYear, Term

from .models import EcoCashPaymentAttempt, FeePayment, TermFee
from .payments import refresh_ecocash_attempt


@override_settings(DEBUG=False, PAYMENTS_DEMO_MODE=True)
class EcoCashCheckoutTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username="test-student", password="test-pass")
        profile = UserProfile.objects.create(user=user, role="STUDENT")
        self.student = StudentProfile.objects.create(
            user_profile=profile,
            student_number="NH-1001",
            first_name="Test",
            last_name="Student",
            guardian_phone="0771234567",
        )
        year = SchoolYear.objects.create(
            name="2026-2027",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        term = Term.objects.create(
            school_year=year,
            number=1,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 4, 30),
        )
        self.schedule = TermFee.objects.create(
            term=term,
            tuition_usd=Decimal("100.00"),
            is_published=True,
        )

    def checkout_data(self, **overrides):
        return {
            "payment_method": "ECOCASH",
            "student_number": self.student.student_number,
            "guardian_phone": "0771234567",
            "fee_schedule": str(self.schedule.pk),
            "amount": "25.00",
            "payer_phone": "0777654321",
            "payer_email": "payer@example.com",
            **overrides,
        }

    def test_demo_checkout_never_posts_a_fee_payment(self):
        response = self.client.post(
            reverse("fees:ecocash_checkout"),
            self.checkout_data(),
        )

        self.assertEqual(response.status_code, 302)
        attempt = EcoCashPaymentAttempt.objects.get()
        self.assertEqual(attempt.status, "DEMO")
        status_url = reverse("fees:payment_status", args=[attempt.reference])
        response = self.client.post(status_url)

        self.assertEqual(response.status_code, 200)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "DEMO_PAID")
        self.assertEqual(FeePayment.objects.count(), 0)

    def test_demo_form_is_editable_with_debug_disabled_and_has_no_email_default(self):
        response = self.client.get(reverse("fees:ecocash_checkout"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demo mode:")
        self.assertNotContains(response, "<fieldset disabled>", html=False)
        self.assertContains(response, 'name="payer_email"')
        self.assertNotContains(response, "samuelfifitini0@gmail.com")

    def test_demo_decline_is_not_a_real_payment(self):
        self.client.post(reverse("fees:ecocash_checkout"), self.checkout_data())
        attempt = EcoCashPaymentAttempt.objects.get()

        response = self.client.post(
            reverse("fees:payment_status", args=[attempt.reference]),
            {"demo_result": "failed"},
        )

        self.assertEqual(response.status_code, 200)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "DEMO_FAILED")
        self.assertEqual(FeePayment.objects.count(), 0)

    def test_paynow_demo_option_does_not_require_a_mobile_number(self):
        response = self.client.post(
            reverse("fees:ecocash_checkout"),
            self.checkout_data(payment_method="PAYNOW", payer_phone=""),
        )

        self.assertEqual(response.status_code, 302)
        attempt = EcoCashPaymentAttempt.objects.get()
        self.assertEqual(attempt.payment_method, "PAYNOW")
        self.assertEqual(attempt.status, "DEMO")
        self.assertEqual(FeePayment.objects.count(), 0)

    def test_live_paynow_option_redirects_to_hosted_checkout(self):
        with override_settings(PAYMENTS_DEMO_MODE=False):
            with patch("fees.views.start_paynow_checkout", return_value="https://www.paynow.co.zw/checkout/test"):
                response = self.client.post(
                    reverse("fees:ecocash_checkout"),
                    self.checkout_data(payment_method="PAYNOW", payer_phone=""),
                )

        self.assertRedirects(
            response,
            "https://www.paynow.co.zw/checkout/test",
            fetch_redirect_response=False,
        )
        attempt = EcoCashPaymentAttempt.objects.get()
        self.assertEqual(attempt.payment_method, "PAYNOW")
        self.assertEqual(attempt.status, "PENDING")

    def test_guardian_phone_must_match_school_record(self):
        response = self.client.post(
            reverse("fees:ecocash_checkout"),
            self.checkout_data(guardian_phone="0770000000"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(EcoCashPaymentAttempt.objects.count(), 0)
        self.assertEqual(FeePayment.objects.count(), 0)

    def test_checkout_rejects_amount_above_remaining_balance(self):
        response = self.client.post(
            reverse("fees:ecocash_checkout"),
            self.checkout_data(amount="101.00"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(EcoCashPaymentAttempt.objects.count(), 0)
        self.assertEqual(FeePayment.objects.count(), 0)

    def test_only_provider_paid_status_posts_one_fee_payment(self):
        attempt = EcoCashPaymentAttempt.objects.create(
            student=self.student,
            term=self.schedule.term,
            amount=Decimal("25.00"),
            currency="USD",
            payer_phone="0777654321",
            payer_email="payer@example.com",
            reference="NH-PROVIDER-TEST",
            poll_url="https://www.paynow.co.zw/poll/test",
            status="PENDING",
        )
        provider = SimpleNamespace(paid=True, status="paid")
        with patch("fees.payments._paynow") as paynow_factory:
            paynow_factory.return_value.check_transaction_status.return_value = provider
            refresh_ecocash_attempt(self.client.request().wsgi_request, attempt)
            refresh_ecocash_attempt(self.client.request().wsgi_request, attempt)

        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "PAID")
        self.assertEqual(FeePayment.objects.count(), 1)

    def test_unconfirmed_provider_status_does_not_post_payment(self):
        attempt = EcoCashPaymentAttempt.objects.create(
            student=self.student,
            term=self.schedule.term,
            amount=Decimal("25.00"),
            currency="USD",
            payer_phone="0777654321",
            payer_email="payer@example.com",
            reference="NH-PROVIDER-PENDING",
            poll_url="https://www.paynow.co.zw/poll/pending",
            status="PENDING",
        )
        provider = SimpleNamespace(paid=False, status="created")
        with patch("fees.payments._paynow") as paynow_factory:
            paynow_factory.return_value.check_transaction_status.return_value = provider
            refresh_ecocash_attempt(self.client.request().wsgi_request, attempt)

        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "PENDING")
        self.assertEqual(FeePayment.objects.count(), 0)