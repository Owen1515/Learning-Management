from django import forms


class PortalDateInput(forms.DateInput):
    input_type = "text"

    def __init__(self, attrs=None, format=None):
        default_attrs = {
            "class": "portal-datepicker",
            "autocomplete": "off",
            "placeholder": "YYYY-MM-DD",
        }

        if attrs:
            default_attrs.update(attrs)

        super().__init__(
            attrs=default_attrs,
            format=format or "%Y-%m-%d"
        )

    class Media:
        css = {
            "all": (
                "https://cdn.jsdelivr.net/npm/air-datepicker@3.6.0/air-datepicker.css",
                "portal/css/datepicker.css",
            )
        }

        js = (
            "https://cdn.jsdelivr.net/npm/air-datepicker@3.6.0/air-datepicker.js",
            "portal/js/datepicker.js",
        )