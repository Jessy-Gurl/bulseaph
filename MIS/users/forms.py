# forms.py
from django import forms
from .models import HomepageContent

class HomepageContentForm(forms.ModelForm):
    class Meta:
        model = HomepageContent
        fields = ['section_name', 'title', 'content', 'image', 'order', 'is_active']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }