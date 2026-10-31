from django import forms

from .models import ContactInquiry


class ContactInquiryForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    topic = forms.ChoiceField(choices=[(label, label) for _, label in ContactInquiry.TOPIC_CHOICES])

    class Meta:
        model = ContactInquiry
        fields = ["name", "email", "phone", "topic", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "phone": forms.TelInput(attrs={"autocomplete": "tel"}),
            "topic": forms.Select(),
            "message": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if field.widget.is_hidden:
                continue
            field.widget.attrs["class"] = (
                "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            )

    def clean_name(self):
        return self.cleaned_data["name"].strip()

    def clean_topic(self):
        topic_label = self.cleaned_data["topic"]
        return next(
            value for value, label in ContactInquiry.TOPIC_CHOICES if label == topic_label
        )

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 10:
            raise forms.ValidationError("Please provide a little more detail.")
        return message
