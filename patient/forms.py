from django import forms
from adminpanel.models import *
from django.core.exceptions import ValidationError
from django.db.models import UniqueConstraint
from django.contrib.auth.models import Group


# forms.py

class PatientRegistrationForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control'
        })
    )

    class Meta:
        model = Patient
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender',
            'phone_number', 'email', 'address', 'previous_hospital_history',
            'medical_report_pdf', 'profile_image'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'previous_hospital_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'medical_report_pdf': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'profile_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
