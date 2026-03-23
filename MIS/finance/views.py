from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .forms import SimpleLoanForm, PaymentForm, RenewLoanForm 
from .models import LoanTransaction, TransactionHistory, Payment
from beneficiaries.models import Beneficiary
from decimal import Decimal, InvalidOperation  

@login_required
def finance(request, id_number):
    if request.method == 'POST':
        form = SimpleLoanForm(request.POST)
        if form.is_valid():
            beneficiary_id = form.cleaned_data['beneficiary_id'].strip()
            amount_str = form.cleaned_data['amount']  # String from ChoiceField
            
            try:
                # 🔥 FIX: Convert string to Decimal
                amount = Decimal(amount_str)
                
                beneficiary = Beneficiary.objects.get(id_number=beneficiary_id)
                
                loan = LoanTransaction.objects.create(
                    beneficiary=beneficiary,
                    district=beneficiary.district,
                    municipality=beneficiary.municipality,
                    barangay=beneficiary.barangay,
                    amount=amount,  # Now Decimal!
                    due_date=timezone.now().date() + timezone.timedelta(days=730),
                    status='pending',
                    created_by=request.user,
                    notes=f"Assistance Loan - {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                )
                
                TransactionHistory.objects.create(
                    beneficiary=beneficiary,
                    transaction_type='loan',
                    amount=amount,
                    balance=amount,
                    reference=f"LOAN-{loan.id}",
                    created_by=request.user
                )
                
                messages.success(request, f'✅ Loan ₱{amount:,.2f} recorded for {beneficiary_id}!')
                return redirect('loan_records', loan.id)  # To loan records!
                
            except Beneficiary.DoesNotExist:
                messages.error(request, f'❌ Beneficiary ID {beneficiary_id} not found!')
            except ValueError as e:
                messages.error(request, f'❌ Invalid amount: {e}')
            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')
    else:
        form = SimpleLoanForm(initial={'beneficiary_id': id_number})
    
    now = timezone.now()
    return render(request, 'finance/finance.html', {
        'form': form,
        'now': now,
        'beneficiary_id': id_number
    })

from django.db.models import Sum, Q
from . import models
from datetime import timedelta

@login_required
def loan_records(request, loan_id):
    loan = get_object_or_404(LoanTransaction, id=loan_id)
    
    # 🔥 Current payments for THIS loan only (not all beneficiary payments)
    payments = Payment.objects.filter(loan=loan).order_by('-payment_date')
    total_paid = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Dynamic properties
    if not hasattr(loan, 'get_balance'):
        loan.get_balance = lambda: max(loan.amount - total_paid, Decimal('0.00'))
    loan.is_overdue = loan.due_date < timezone.now().date() and loan.get_balance() > 0
    
    # 🔥 Get ALL history transactions for this beneficiary
    history_transactions = TransactionHistory.objects.filter(
        beneficiary=loan.beneficiary
    ).select_related('beneficiary', 'created_by', 'district', 'municipality', 'barangay').order_by('-date')[:100]  # Last 100
    
    # Calculate history totals
    history_payments = [t for t in history_transactions if t.transaction_type == 'payment']
    history_loans = [t for t in history_transactions if t.transaction_type == 'loan']
    history_total_paid = sum(t.amount for t in history_payments)
    
    # Filters for current payments
    search = request.GET.get('search', '').strip()
    date_from = request.GET.get('date_from')
    
    if search:
        payments = payments.filter(
            Q(or_number__icontains=search) | 
            Q(amount__icontains=search)
        )
    if date_from:
        payments = payments.filter(payment_date__gte=date_from)
    
    if request.method == 'POST':
        if 'payment_submit' in request.POST:
            try:
                amount_str = request.POST.get('amount', '0').strip()
                amount = Decimal(amount_str) if amount_str else Decimal('0')
                
                if amount > 0:
                    or_number = request.POST.get('or_number', '').strip()
                    if not or_number:
                        payment_count = Payment.objects.filter(loan=loan).count()
                        or_number = f"OR-{loan.id}-{payment_count + 1:03d}"
                    
                    payment = Payment.objects.create(
                        loan=loan,
                        beneficiary=loan.beneficiary,
                        amount=amount,
                        or_number=or_number,
                        payment_method='cash',
                        payment_date=timezone.now().date(),
                        created_by=request.user
                    )
                    
                    messages.success(request, f'✅ ₱{amount:,.2f} recorded! OR#{or_number}')
                    return redirect('loan_records', loan.id)
                else:
                    messages.error(request, '❌ Amount must be > ₱0.01')
                    
            except (InvalidOperation, ValueError):
                messages.error(request, '❌ Invalid amount')
        
        elif 'renew_submit' in request.POST:
            try:
                amount_str = request.POST.get('amount', '0').strip()
                new_amount = Decimal(amount_str) if amount_str else Decimal('0')
                
                if new_amount > 0:
                    # 🔥 1. Archive CURRENT loan payments to history
                    current_payments = Payment.objects.filter(loan=loan)
                    archived_count = current_payments.count()
                    
                    for payment in current_payments:
                        TransactionHistory.objects.create(
                            beneficiary=loan.beneficiary,
                            transaction_type='payment',
                            amount=payment.amount,
                            balance=loan.get_balance(),
                            reference=f"ARCHIVED-PMT-{payment.or_number or 'CASH'}-L{loan.id}",
                            created_by=request.user,
                            district=loan.district,
                            municipality=loan.municipality,
                            barangay=loan.barangay
                        )
                    
                    # 🔥 2. Archive the ORIGINAL loan to history
                    TransactionHistory.objects.create(
                        beneficiary=loan.beneficiary,
                        transaction_type='loan',
                        amount=loan.amount,
                        balance=loan.get_balance(),
                        reference=f"ARCHIVED-LOAN-{loan.id}",
                        created_by=request.user,
                        district=loan.district,
                        municipality=loan.municipality,
                        barangay=loan.barangay
                    )
                    
                    # 🔥 3. Delete old payments and archive loan
                    current_payments.delete()
                    loan.status = 'archived'
                    loan.save()
                    
                    # 🔥 4. Create NEW loan
                    new_loan = LoanTransaction.objects.create(
                        beneficiary=loan.beneficiary,
                        district=loan.district,
                        municipality=loan.municipality,
                        barangay=loan.barangay,
                        amount=new_amount,
                        due_date=timezone.now().date() + timedelta(days=731),
                        status='pending',
                        created_by=request.user,
                        notes=f"Renewed from ARCHIVED Loan-{loan.id} (moved {archived_count} payments to history)"
                    )
                    
                    messages.success(
                        request, 
                        f'✅ Loan renewed! {archived_count} payments → HISTORY. New loan: ₱{new_amount:,.2f}'
                    )
                    return redirect('loan_records', new_loan.id)
            except (InvalidOperation, ValueError):
                messages.error(request, '❌ Invalid amount')
    
    context = {
        'loan': loan,
        'payments': payments,
        'total_paid': total_paid,
        # 🔥 History context
        'history_transactions': history_transactions,
        'history_total_paid': history_total_paid,
        'history_payment_count': len(history_payments),
        'history_loan_count': len(history_loans),
    }
    return render(request, 'finance/loan_records.html', context)