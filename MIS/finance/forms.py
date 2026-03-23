from django import forms
from django.utils import timezone
from .models import LoanTransaction, Payment, TransactionHistory  
from beneficiaries.models import Beneficiary

class SimpleLoanForm(forms.Form):
    beneficiary_id = forms.CharField(max_length=20)  # 🔥 REQUIRED!
    amount = forms.ChoiceField(
        choices=[
            ('', 'Select Amount'),
            ('2000.00', '2,000'),
            ('5000.00', '5,000'),
            ('10000.00', '10,000'),
        ],
        widget=forms.Select(attrs={'class': 'input-field select-field'}),
    )

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'or_number', 'payment_method']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'or_number': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }

class RenewLoanForm(forms.Form):
    amount = forms.ChoiceField(
        choices=[
            ('2000.00', '2,000'),
            ('5000.00', '5,000'),
            ('10000.00', '10,000'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )