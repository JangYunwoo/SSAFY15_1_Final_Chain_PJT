from django import forms

from .models import AnalysisBatch, Lot, WaferAnalysis


class WaferUploadForm(forms.ModelForm):
    class Meta:
        model = WaferAnalysis
        fields = ["uploaded_file", "yield_threshold"]
        widgets = {
            "uploaded_file": forms.FileInput(attrs={"class": "form-control", "accept": ".csv,.png,.jpg,.jpeg"}),
            "yield_threshold": forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 100, "step": 0.1}),
        }


class BatchUploadForm(forms.ModelForm):
    class Meta:
        model = AnalysisBatch
        fields = ["lot", "uploaded_file"]
        widgets = {
            "lot": forms.Select(attrs={"class": "form-select"}),
            "uploaded_file": forms.FileInput(attrs={"class": "form-control", "accept": ".csv"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and not user.is_staff:
            self.fields["lot"].queryset = Lot.objects.filter(assignments__user=user).distinct()
        else:
            self.fields["lot"].queryset = Lot.objects.all()
