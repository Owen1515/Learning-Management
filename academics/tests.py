from django.test import Client, TestCase
from django.urls import reverse

from .models import ContactInquiry


class ContactInquiryTests(TestCase):
	def valid_data(self, **overrides):
		return {
			"name": "Rudo Moyo",
			"email": "rudo@example.com",
			"phone": "+263771234567",
			"topic": "Admissions",
			"message": "Please send us information about school admissions.",
			"website": "",
			**overrides,
		}

	def test_contact_enquiry_is_saved_with_csrf_protection(self):
		client = Client(enforce_csrf_checks=True)
		page = client.get(reverse("school_contact"))
		csrf_token = page.cookies["csrftoken"].value

		response = client.post(
			reverse("school_contact"),
			self.valid_data(),
			HTTP_X_CSRFTOKEN=csrf_token,
		)

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.json()["success"])
		inquiry = ContactInquiry.objects.get()
		self.assertEqual(inquiry.name, "Rudo Moyo")
		self.assertEqual(inquiry.topic, "ADMISSIONS")
		self.assertEqual(inquiry.status, "NEW")

	def test_invalid_contact_enquiry_is_not_saved(self):
		response = self.client.post(
			reverse("school_contact"),
			self.valid_data(email="not-an-email"),
		)

		self.assertEqual(response.status_code, 400)
		self.assertFalse(response.json()["success"])
		self.assertEqual(ContactInquiry.objects.count(), 0)

	def test_honeypot_submission_is_not_saved(self):
		response = self.client.post(
			reverse("school_contact"),
			self.valid_data(website="spam.example"),
		)

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.json()["success"])
		self.assertEqual(ContactInquiry.objects.count(), 0)
