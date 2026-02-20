from django import forms
from django.contrib.auth import get_user_model
from .models import Ticket, Category

User = get_user_model()


class TicketCreateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["title", "description", "category", "priority"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_category(self):
        cat: Category = self.cleaned_data["category"]
        if not cat.is_active:
            raise forms.ValidationError("Selected category is not active.")
        return cat


class AssignTechnicianForm(forms.Form):
    technician = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    def __init__(self, *args, **kwargs):
        tech_qs = kwargs.pop("tech_qs", User.objects.none())
        super().__init__(*args, **kwargs)
        self.fields["technician"].queryset = tech_qs
