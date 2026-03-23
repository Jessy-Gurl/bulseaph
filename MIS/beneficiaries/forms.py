from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import Beneficiary, BeneficiaryDocument

class BeneficiaryForm(forms.ModelForm):
    class Meta:
        model = Beneficiary
        fields = [
            'last_name', 'first_name', 'middle_name', 'sex', 'civil_status', 
            'contact', 'email', 'district', 'municipality', 'barangay', 
            'street_house', 'category', 'project', 'date_of_birth', 'age',
            'spouse_name', 'num_of_dependents', 'ages_of_dependents',
            'education_level', 'business_status', 'type_of_business',
            'business_name', 'business_address', 'years_in_operation',
            'nature_of_business', 'avg_monthly_income', 'avg_monthly_expenses',
            'loan_purpose', 'loan_purpose_other', 'owned_assets', 'net_income', 'other_assets',
            'outstanding_loans', 'is_member_of_org', 'organization_name',
            'documents_submitted_in_person', 'declaration_signed'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'outstanding_loans': forms.Textarea(attrs={'rows': 3}),
            'ages_of_dependents': forms.TextInput(attrs={'placeholder': '3,6,12'}),
            'owned_assets': forms.TextInput(attrs={'placeholder': 'House,Lot'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style all fields
        for field in self.fields:
            if field in ['sex', 'civil_status', 'category', 'project', 'business_status', 'nature_of_business', 'loan_purpose']:
                self.fields[field].widget.attrs['class'] = 'form-select'
            elif field in ['is_member_of_org', 'documents_submitted_in_person', 'declaration_signed']:
                self.fields[field].widget.attrs['class'] = 'form-check-input'
            else:
                self.fields[field].widget.attrs['class'] = 'form-control'
        
        # ForeignKeys optional
        self.fields['district'].required = False
        self.fields['municipality'].required = False
        self.fields['barangay'].required = False

# ✅ EXPORT DocumentFormSet
DocumentFormSet = inlineformset_factory(
    Beneficiary, BeneficiaryDocument,
    fields=['doc_type', 'file', 'note'],
    extra=5,
    can_delete=False,
    widgets={
        'doc_type': forms.Select(attrs={'class': 'form-select'}),
        'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        'note': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional note'}),
    }
)

class SimpleBeneficiaryForm(ModelForm):
    class Meta:
        model = Beneficiary
        fields = ['last_name', 'first_name', 'sex', 'contact', 'street_house', 'category', 'project']
        
class BeneficiaryDocumentForm(forms.ModelForm):
    class Meta:
        model = BeneficiaryDocument
        fields = ['doc_type', 'file', 'note']
        widgets = {
            'note': forms.TextInput(attrs={'placeholder': 'Optional note'}),
        }