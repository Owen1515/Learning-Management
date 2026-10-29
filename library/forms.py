from django import forms
from .models import LibraryDocument


class LibraryDocumentForm(forms.ModelForm):
    class Meta:
        model  = LibraryDocument
        fields = ["title", "doc_type", "subject", "level", "description", "file", "content", "is_visible"]
        widgets = {
            "title":       forms.TextInput(attrs={"class": "p-input", "placeholder": "Document title…"}),
            "doc_type":    forms.Select(attrs={"class": "p-select"}),
            "subject":     forms.Select(attrs={"class": "p-select"}),
            "level":       forms.Select(attrs={"class": "p-select"}),
            "description": forms.Textarea(attrs={"class": "p-textarea", "rows": 3, "placeholder": "Brief description (optional)…"}),
            "file":        forms.ClearableFileInput(attrs={"class": "p-input"}),
            "content":     forms.Textarea(attrs={"class": "p-textarea", "rows": 12, "placeholder": "Type or paste content here (questions, notes, etc.)…"}),
            "is_visible":  forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "is_visible": "Visible to students",
        }
