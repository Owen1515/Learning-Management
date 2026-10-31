import re

from django import forms

from .models import TermFee


def normalize_zimbabwe_phone(value):
    digits = re.sub(r"\D", "", value)
    if digits.startswith("263"):
        digits = "0" + digits[3:]
    if not re.fullmatch(r"07\d{8}", digits):
        raise forms.ValidationError("Enter a valid Zimbabwe mobile number, such as 0771234567.")
    return digits


class EcoCashCheckoutForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=[
            ("ECOCASH", "EcoCash phone prompt"),
            ("PAYNOW", "Paynow hosted checkout: bank and card options enabled for the school"),
        ],
        widget=forms.Select(attrs={"class": "pay-select"}),
        label="Payment option",
    )
    student_number = forms.CharField(max_length=30, label="Student number")
    guardian_phone = forms.CharField(max_length=24, label="Guardian phone on school record")
    fee_schedule = forms.ModelChoiceField(
        queryset=TermFee.objects.filter(is_published=True).select_related("term", "term__school_year"),
        label="Term",
    )
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    payer_phone = forms.CharField(
        max_length=24,
        required=False,
        label="EcoCash number for phone prompt",
    )
    payer_email = forms.EmailField(label="Payer email")

    def clean_guardian_phone(self):
        return normalize_zimbabwe_phone(self.cleaned_data["guardian_phone"])

    def clean_payer_phone(self):
        phone = self.cleaned_data["payer_phone"]
        return normalize_zimbabwe_phone(phone) if phone else ""

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("payment_method") == "ECOCASH" and not cleaned_data.get("payer_phone"):
            self.add_error("payer_phone", "Enter the EcoCash number that should receive the phone prompt.")
        return cleaned_data