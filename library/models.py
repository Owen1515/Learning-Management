from django.db import models
from academics.models import Subject
from accounts.models import TeacherProfile


class LibraryDocument(models.Model):
    TYPE_CHOICES = [
        ("NOTES",   "Notes / Study Material"),
        ("PAPER",   "Question Paper"),
        ("SCHEME",  "Marking Scheme"),
        ("ANSWER",  "Model Answers"),
        ("OTHER",   "Other"),
    ]
    LEVEL_CHOICES = [
        ("FORM1", "Form 1"), ("FORM2", "Form 2"),
        ("FORM3", "Form 3"), ("FORM4", "Form 4"),
        ("FORM5", "Form 5"), ("FORM6", "Form 6"),
        ("ALL",   "All Forms"),
    ]

    # Metadata
    title       = models.CharField(max_length=200)
    doc_type    = models.CharField(max_length=10, choices=TYPE_CHOICES)
    subject     = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="library_docs")
    level       = models.CharField(max_length=10, choices=LEVEL_CHOICES, default="ALL")
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)
    is_visible  = models.BooleanField(default=True, help_text="Visible to students")

    # Content: either file upload OR typed content
    file        = models.FileField(upload_to="library/", blank=True, null=True, help_text="Upload PDF/Word/image")
    content     = models.TextField(blank=True, help_text="Typed content (notes, questions, etc.)")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Library Document"
        verbose_name_plural = "Library Documents"

    def __str__(self):
        return f"[{self.get_doc_type_display()}] {self.title} — {self.subject.name}"

    @property
    def has_file(self):
        return bool(self.file)

    @property
    def has_content(self):
        return bool(self.content.strip())


class AIMarkingScheme(models.Model):
    """AI-generated marking scheme linked to a question paper in the library."""
    STATUS_CHOICES = [
        ("PENDING",   "Generating…"),
        ("DONE",      "Ready"),
        ("FAILED",    "Failed"),
    ]

    source_paper  = models.ForeignKey(
        LibraryDocument, on_delete=models.CASCADE,
        related_name="marking_schemes",
        limit_choices_to={"doc_type": "PAPER"},
    )
    generated_by  = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    status        = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    scheme_text   = models.TextField(blank=True, help_text="AI-generated marking scheme")
    saved_as_doc  = models.OneToOneField(
        LibraryDocument, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="ai_source",
        help_text="If saved to library as a document",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "AI Marking Scheme"

    def __str__(self):
        return f"AI Scheme for: {self.source_paper.title}"
