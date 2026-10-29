from django.db import models
from academics.models import Term
from accounts.models import StudentProfile


class TermFee(models.Model):
    """Fee schedule published per term. Supports USD and ZWG."""
    term = models.OneToOneField(
        Term,
        on_delete=models.CASCADE,
        related_name="fee_schedule",
    )
    tuition_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tuition_zwg = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    boarding_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    boarding_zwg = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    development_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    development_zwg = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    exam_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    exam_zwg = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other_zwg = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_label = models.CharField(max_length=80, blank=True)
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["-term__school_year", "term__number"]

    def __str__(self):
        return f"Fee schedule: {self.term}"

    @property
    def total_usd(self):
        return self.tuition_usd + self.boarding_usd + self.development_usd + self.exam_usd + self.other_usd

    @property
    def total_zwg(self):
        return self.tuition_zwg + self.boarding_zwg + self.development_zwg + self.exam_zwg + self.other_zwg


PAYMENT_METHOD_CHOICES = [
    ("CASH", "Cash"),
    ("BANK", "Bank Transfer"),
    ("ECOCASH", "EcoCash"),
    ("INNBUCKS", "InnBucks"),
    ("OTHER", "Other"),
]

CURRENCY_CHOICES = [
    ("USD", "USD"),
    ("ZWG", "ZWG"),
]


class FeePayment(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="fee_payments",
    )
    term = models.ForeignKey(
        Term,
        on_delete=models.CASCADE,
        related_name="fee_payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=5, choices=CURRENCY_CHOICES, default="USD")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default="CASH")
    reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateField()
    recorded_by = models.CharField(max_length=150, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date", "-created_at"]

    def __str__(self):
        return f"{self.student} – {self.term} – {self.currency} {self.amount}"
