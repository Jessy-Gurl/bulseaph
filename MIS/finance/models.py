from django.db import models
from django.contrib.auth import get_user_model
from beneficiaries.models import Beneficiary, District, Municipality, Barangay
from decimal import Decimal

User = get_user_model()

class LoanTransaction(models.Model):
    beneficiary = models.ForeignKey(
        Beneficiary, 
        on_delete=models.CASCADE,
        related_name='loans'  # 🔥 Add this
    )
    
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    municipality = models.ForeignKey(Municipality, on_delete=models.SET_NULL, null=True, blank=True)
    barangay = models.ForeignKey(Barangay, on_delete=models.SET_NULL, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('partial', 'Partial')
    ], default='pending')
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.beneficiary.beneficiary_id} - ₱{self.amount:,.2f}"
    
    class Meta:
        db_table = 'finance_loan_transaction'
        ordering = ['-loan_date']

class Payment(models.Model):
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE)
    loan = models.ForeignKey(LoanTransaction, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    or_number = models.CharField(max_length=50, blank=True)
    payment_method = models.CharField(max_length=20, choices=[
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('bank', 'Bank Transfer'),
        ('gcash', 'GCash')
    ], default='cash')
    
    # 🔥 ADD THESE FIELDS for proper filtering!
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    municipality = models.ForeignKey(Municipality, on_delete=models.SET_NULL, null=True, blank=True)
    barangay = models.ForeignKey(Barangay, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.beneficiary.beneficiary_id} - OR#{self.or_number}"
    
    class Meta:
        db_table = 'finance_payment'

class TransactionHistory(models.Model):
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=[
        ('loan', 'Loan Given'),
        ('payment', 'Payment Received')
    ])
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    municipality = models.ForeignKey(Municipality, on_delete=models.SET_NULL, null=True, blank=True)
    barangay = models.ForeignKey(Barangay, on_delete=models.SET_NULL, null=True, blank=True) 
    
    class Meta:
        db_table = 'finance_transaction_history'
        ordering = ['-date']