from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django import forms
from django.forms import inlineformset_factory
from django.db import transaction
import logging  # ✅ MOVE HERE
from .models import District, Municipality, Barangay, Beneficiary, BeneficiaryDocument
from .forms import BeneficiaryForm, BeneficiaryDocumentForm
from django.forms import modelformset_factory
from decimal import Decimal
from django.utils import timezone
from users.models import UserActivity

logger = logging.getLogger(__name__)  # ✅ KEEP HERE

@login_required
def beneficiaries(request):
    # Counts
    active_count = Beneficiary.objects.filter(application_status='Approved').count()
    inactive_count = Beneficiary.objects.filter(application_status='Inactive').count()
    total_count = Beneficiary.objects.count()
    
    # 🔥 Base querysets with select_related
    active_beneficiaries = Beneficiary.objects.filter(
        application_status='Approved'
    ).select_related('district', 'municipality', 'barangay').prefetch_related('loans')[:20]
    
    inactive_beneficiaries = Beneficiary.objects.filter(
        application_status='Inactive'
    ).select_related('district', 'municipality', 'barangay').prefetch_related('loans')[:20]
    
    # 🔥 Pre-calculate loan info for each beneficiary
    for beneficiary in active_beneficiaries:
        beneficiary.has_loans = beneficiary.loans.exists()
        if beneficiary.has_loans:
            beneficiary.latest_loan = beneficiary.loans.order_by('-loan_date').first()
    
    for beneficiary in inactive_beneficiaries:
        beneficiary.has_loans = beneficiary.loans.exists()
        if beneficiary.has_loans:
            beneficiary.latest_loan = beneficiary.loans.order_by('-loan_date').first()
    
    context = {
        'active_count': active_count,
        'inactive_count': inactive_count,
        'total_count': total_count,
        'active_beneficiaries': active_beneficiaries,
        'inactive_beneficiaries': inactive_beneficiaries,
        
        'current_filters': {
            'district': request.GET.get('district'),
            'municipality': request.GET.get('municipality'),
            'barangay': request.GET.get('barangay'),
            'search': request.GET.get('search', ''),
            'tab': request.GET.get('tab', 'active'),
        }
    }
    
    return render(request, 'beneficiaries/beneficiaries.html', context)

def api_table(request):
    """🔥 Table filter API - Clean HTML generation"""
    district_id = request.GET.get('district')
    municipality_id = request.GET.get('municipality')
    barangay_id = request.GET.get('barangay')
    search = request.GET.get('search', '').strip()
    tab = request.GET.get('tab', 'active')
    
    # Filter queryset
    if tab == 'active':
        queryset = Beneficiary.objects.filter(application_status='Approved')
    else:
        queryset = Beneficiary.objects.filter(application_status='Inactive')
    
    if district_id:
        queryset = queryset.filter(district_id=district_id)
    if municipality_id:
        queryset = queryset.filter(municipality_id=municipality_id)
    if barangay_id:
        queryset = queryset.filter(barangay_id=barangay_id)
    
    if search:
        queryset = queryset.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(contact__icontains=search) |
            Q(beneficiary_id__icontains=search)
        )
    
    beneficiaries = queryset.select_related('district', 'municipality', 'barangay')[:50]
    
    # 🔥 SAFE HTML generation - No template syntax
    html_rows = []
    for b in beneficiaries:
        initials = f"{b.first_name[0].upper() if b.first_name else 'U'}{b.last_name[0].upper() if b.last_name else 'N'}"
        middle_initial = f" {b.middle_name[0]}. " if b.middle_name else ""
        district_name = b.district.name if b.district else "N/A"
        municipality_name = b.municipality.name if b.municipality else ""
        barangay_name = f", {b.barangay.name}" if b.barangay else ""
        
        row = f'''
        <tr data-beneficiary-id="{b.beneficiary_id}" data-pk="{b.pk}">
            <td><strong class="text-primary">{b.beneficiary_id}</strong></td>
            <td>
                <div class="d-flex align-items-center">
                    <div class="avatar avatar-sm bg-primary me-2">{initials}</div>
                    <div>
                        <div>{b.last_name}, {b.first_name}{middle_initial}</div>
                        <small class="text-muted">{b.street_house or "N/A"}</small>
                    </div>
                </div>
            </td>
            <td><span class="badge bg-info">{district_name}</span></td>
            <td>{municipality_name}{barangay_name}</td>
            <td>
                <a href="/beneficiaries/{b.id_number}/" class="btn btn-outline-primary btn-sm" title="View Details">
                    <i class="fas fa-eye"></i>
                </a>
            </td>
            <td>
                <a href="#" class="btn btn-outline-success btn-sm" title="Financial Records">
                    <i class="fas fa-file-invoice-dollar"></i>
                </a>
            </td>
        </tr>
        '''
        html_rows.append(row)
    
    html = ''.join(html_rows)
    if not html:
        html = '<tr><td colspan="6" class="text-center py-4 text-muted"><i class="fas fa-search me-2"></i>No beneficiaries match your filters</td></tr>'
    
    return JsonResponse({'html': html})

# 🔥 YOUR AJAX endpoints (keep them)
def api_districts(request):
    districts = District.objects.all().values('id', 'name')
    return JsonResponse(list(districts), safe=False)

def api_municipalities(request):
    district_id = request.GET.get('district')
    municipalities = Municipality.objects.filter(district_id=district_id) if district_id else Municipality.objects.none()
    return JsonResponse(list(municipalities.values('id', 'name')), safe=False)

def api_barangays(request):
    municipality_id = request.GET.get('municipality')
    barangays = Barangay.objects.filter(municipality_id=municipality_id) if municipality_id else Barangay.objects.none()
    return JsonResponse(list(barangays.values('id', 'name')), safe=False)


logger = logging.getLogger(__name__)
import logging

from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.utils import timezone
from users.models import UserActivity, CustomUser  # ✅ Activity import
from .models import Beneficiary, BeneficiaryDocument  # Your models

@login_required
def add_beneficiary(request):
    if request.method == 'POST':
        try:
            # ✅ COMPLETE FORM DATA - ALL FIELDS
            beneficiary_data = {
                # Personal Info (REQUIRED)
                'last_name': request.POST.get('last_name', '').strip(),
                'first_name': request.POST.get('first_name', '').strip(),
                'sex': request.POST.get('sex', 'M'),
                'contact': request.POST.get('contact', '').strip(),
                'street_house': request.POST.get('street_house', '').strip(),
                'category': request.POST.get('category', 'Choose'),
                'project': request.POST.get('project', '').strip(),
                
                # Personal additions
                'middle_name': request.POST.get('middle_name', '').strip() or None,
                'civil_status': request.POST.get('civil_status', '').strip() or None,
                'date_of_birth': request.POST.get('date_of_birth') or None,
                'age': request.POST.get('age') or None,
                'email': request.POST.get('email', '').strip() or None,
                
                # Address FKs
                'district_id': request.POST.get('district') or None,
                'municipality_id': request.POST.get('municipality') or None,
                'barangay_id': request.POST.get('barangay') or None,
                
                # Family
                'num_of_dependents': request.POST.get('num_of_dependents') or None,
                'ages_of_dependents': request.POST.get('ages_of_dependents', '').strip() or None,
                
                # Education
                'education_level': request.POST.get('education_level', '').strip() or None,
                
                # Business/Livelihood
                'business_status': request.POST.get('business_status', '').strip() or None,
                'nature_of_business': request.POST.get('nature_of_business', '').strip() or None,
                'type_of_business': request.POST.get('type_of_business', '').strip() or None,
                'business_name': request.POST.get('business_name', '').strip() or None,
                'business_address': request.POST.get('business_address', '').strip() or None,
                'years_in_operation': request.POST.get('years_in_operation') or None,
                
                # Loan
                'loan_purpose': request.POST.get('loan_purpose', '').strip() or None,
                'loan_purpose_other': request.POST.get('loan_purpose_other', '').strip() or None,
                
                # Assets
                'owned_assets': request.POST.get('owned_assets', '').strip() or None,
                'other_assets': request.POST.get('other_assets', '').strip() or None,
                'outstanding_loans': request.POST.get('outstanding_loans', '').strip() or None,
                
                # Community
                'is_member_of_org': request.POST.get('is_member_of_org') == 'on',
                'organization_name': request.POST.get('organization_name', '').strip() or None,
                
                # Status
                'declaration_signed': request.POST.get('declaration_signed') == 'on',
                'application_source': request.POST.get('application_source', 'walkin'),
                'application_status': 'Approved',  # ✅ AUTO-APPROVED
            }
            
            # 🔥 NET INCOME
            income_str = request.POST.get('avg_monthly_income', '0').strip()
            expenses_str = request.POST.get('avg_monthly_expenses', '0').strip()
            
            try:
                income = Decimal(income_str) if income_str else Decimal('0.00')
                expenses = Decimal(expenses_str) if expenses_str else Decimal('0.00')
                net_income = income - expenses
                
                beneficiary_data.update({
                    'avg_monthly_income': income,
                    'avg_monthly_expenses': expenses,
                    'net_income': net_income,
                })
            except:
                beneficiary_data.update({
                    'avg_monthly_income': Decimal('0.00'),
                    'avg_monthly_expenses': Decimal('0.00'),
                    'net_income': Decimal('0.00'),
                })
            
            # ✅ VALIDATE REQUIRED
            required = ['last_name', 'first_name', 'sex', 'contact', 'street_house', 'category', 'project']
            missing = [k.replace('_', ' ').title() for k, v in beneficiary_data.items() 
                      if k in required and not v]
            
            if missing:
                messages.error(request, f'Missing required fields: {", ".join(missing)}')
                return render(request, 'beneficiaries/add_beneficiaries.html', {
                    'errors': missing,
                    'post_data': dict(request.POST)
                })
            
            # 🔥 DUPLICATE CHECKS - NEW! 🛡️
            duplicate_email = (beneficiary_data['email'] and 
                              Beneficiary.objects.filter(email=beneficiary_data['email']).exists())
            duplicate_contact = Beneficiary.objects.filter(contact=beneficiary_data['contact']).exists()
            duplicate_name_contact = Beneficiary.objects.filter(
                first_name=beneficiary_data['first_name'],
                last_name=beneficiary_data['last_name'],
                contact=beneficiary_data['contact']
            ).exists()
            
            if duplicate_email:
                messages.error(request, f"❌ Email '{beneficiary_data['email']}' already registered!")
                return render(request, 'beneficiaries/add_beneficiaries.html', {'post_data': dict(request.POST)})
            
            if duplicate_contact:
                messages.error(request, f"❌ Contact '{beneficiary_data['contact']}' already registered!")
                return render(request, 'beneficiaries/add_beneficiaries.html', {'post_data': dict(request.POST)})
            
            if duplicate_name_contact:
                messages.error(request, f"❌ Beneficiary '{beneficiary_data['first_name']} {beneficiary_data['last_name']}' with this contact already exists!")
                return render(request, 'beneficiaries/add_beneficiaries.html', {'post_data': dict(request.POST)})
            
            # ✅ SAVE BENEFICIARY
            with transaction.atomic():
                beneficiary = Beneficiary(**beneficiary_data)
                beneficiary.save()
                
                # 🔥 SAVE DOCUMENTS TO BeneficiaryDocument MODEL
                documents_submitted_in_person = request.POST.get('documents_submitted_in_person') == 'on'
                beneficiary.documents_submitted_in_person = documents_submitted_in_person
                beneficiary.save()
                
                # Map checkboxes → Document records
                doc_mapping = {
                    'doc_Liham_kahilingan': 'Liham_kahilingan',
                    'doc_Cert_barangay_indigency': 'Cert_barangay_indigency',
                    'doc_Project_proposal': 'Project_proposal',
                    'doc_Repayment_schema': 'Repayment_schema',
                    'doc_Marriage_contract': 'Marriage_contract',
                    'doc_Birth_certificate': 'Birth_certificate',
                    'doc_Valid_ID': 'Valid_ID',
                    'doc_Community_Tax': 'Community_Tax',
                    'doc_Training_certificate': 'Training_certificate',
                }
                
                for checkbox_name, doc_type in doc_mapping.items():
                    if request.POST.get(checkbox_name) == 'on':
                        BeneficiaryDocument.objects.update_or_create(
                            beneficiary=beneficiary,
                            doc_type=doc_type,
                            defaults={
                                'note': 'Checklist confirmed' + (' (In person)' if documents_submitted_in_person else ''),
                                'uploaded_at': timezone.now()
                            }
                        )
            
            # 🔥 LOG ACTIVITY - OUTSIDE TRANSACTION (Fixed!) ✅
            try:
                current_user = request.user
                UserActivity.objects.create(
                    user=current_user,
                    action="Add Beneficiary",
                    details=f"Added new beneficiary (ID: {beneficiary.beneficiary_id}) - {beneficiary_data['first_name']} {beneficiary_data['last_name']}"
                )
            except Exception:
                pass
            
            messages.success(
                request,
                f'✅ New Beneficiary AUTO-APPROVED! ID: {beneficiary.beneficiary_id}',
                extra_tags='new-beneficiary'
            )
            
            request.session['last_beneficiary_id'] = str(beneficiary.beneficiary_id)
            return redirect('beneficiaries')
            
        except Exception as e:
            messages.error(request, f'❌ Save failed: {str(e)}')
    
    return render(request, 'beneficiaries/add_beneficiaries.html', {
        'recent_id': request.session.get('last_beneficiary_id', None)
    })



def online_application(request):
    if request.method == 'POST':
        try:
            # ✅ EMAIL IS REQUIRED FOR ONLINE
            email = request.POST.get('email', '').strip()
            if not email:
                messages.error(request, '❌ Email is REQUIRED for online applications!')
                return render(request, 'beneficiaries/online_application.html', {
                    'post_data': dict(request.POST),
                    'errors': ['Email']
                })
            
            # 🔥 DUPLICATE EMAIL CHECK (CRITICAL FOR ONLINE)
            if Beneficiary.objects.filter(email=email).exists():
                messages.error(request, f"❌ Email '{email}' already registered! Use different email or contact admin.")
                return render(request, 'beneficiaries/online_application.html', {
                    'post_data': dict(request.POST)
                })
            
            # ✅ COMPLETE FORM DATA - IDENTICAL TO ADD
            beneficiary_data = {
                # Personal Info (REQUIRED)
                'last_name': request.POST.get('last_name', '').strip(),
                'first_name': request.POST.get('first_name', '').strip(),
                'sex': request.POST.get('sex', ''),
                'contact': request.POST.get('contact', '').strip(),
                'street_house': request.POST.get('street_house', '').strip(),
                'category': request.POST.get('category', ''),
                'project': request.POST.get('project', '').strip(),
                'email': email,  # ✅ REQUIRED & UNIQUE
                
                # Personal additions
                'middle_name': request.POST.get('middle_name', '').strip() or None,
                'civil_status': request.POST.get('civil_status', '') or None,
                'date_of_birth': request.POST.get('date_of_birth') or None,
                'age': request.POST.get('age') or None,
                
                # Address FKs
                'district_id': request.POST.get('district') or None,
                'municipality_id': request.POST.get('municipality') or None,
                'barangay_id': request.POST.get('barangay') or None,
                
                # Family
                'num_of_dependents': request.POST.get('num_of_dependents') or None,
                'ages_of_dependents': request.POST.get('ages_of_dependents', '').strip() or None,
                
                # Education
                'education_level': request.POST.get('education_level', '').strip() or None,
                
                # Business/Livelihood
                'business_status': request.POST.get('business_status', '').strip() or None,
                'nature_of_business': request.POST.get('nature_of_business', '').strip() or None,
                'type_of_business': request.POST.get('type_of_business', '').strip() or None,
                'business_name': request.POST.get('business_name', '').strip() or None,
                'business_address': request.POST.get('business_address', '').strip() or None,
                'years_in_operation': request.POST.get('years_in_operation') or None,
                
                # Loan
                'loan_purpose': request.POST.get('loan_purpose', '').strip() or None,
                'loan_purpose_other': request.POST.get('loan_purpose_other', '').strip() or None,
                
                # Assets
                'owned_assets': request.POST.get('owned_assets', '').strip() or None,
                'other_assets': request.POST.get('other_assets', '').strip() or None,
                'outstanding_loans': request.POST.get('outstanding_loans', '').strip() or None,
                
                # Community
                'is_member_of_org': request.POST.get('is_member_of_org') == 'on',
                'organization_name': request.POST.get('organization_name', '').strip() or None,
                
                # ONLINE SPECIFIC - PENDING STATUS! 🔥
                'declaration_signed': request.POST.get('declaration_signed') == 'on',
                'application_source': 'online',
                'application_status': 'Pending',  # ✅ PENDING REVIEW
            }
            
            # 🔥 NET INCOME CALCULATION
            income_str = request.POST.get('avg_monthly_income', '0').strip()
            expenses_str = request.POST.get('avg_monthly_expenses', '0').strip()
            
            try:
                income = Decimal(income_str) if income_str else Decimal('0.00')
                expenses = Decimal(expenses_str) if expenses_str else Decimal('0.00')
                net_income = income - expenses
                
                beneficiary_data.update({
                    'avg_monthly_income': income,
                    'avg_monthly_expenses': expenses,
                    'net_income': net_income,
                })
            except:
                beneficiary_data.update({
                    'avg_monthly_income': Decimal('0.00'),
                    'avg_monthly_expenses': Decimal('0.00'),
                    'net_income': Decimal('0.00'),
                })
            
            # ✅ VALIDATE REQUIRED FIELDS (Email + basics)
            required = ['last_name', 'first_name', 'sex', 'contact', 'street_house', 'category', 'project', 'email']
            missing = [k.replace('_', ' ').title() for k, v in beneficiary_data.items() 
                      if k in required and not v]
            
            if missing:
                messages.error(request, f'Missing required fields: {", ".join(missing)}')
                return render(request, 'beneficiaries/online_application.html', {
                    'errors': missing,
                    'post_data': dict(request.POST)
                })
            
            # 🔥 DUPLICATE CHECKS (Contact + Name combo)
            duplicate_contact = Beneficiary.objects.filter(contact=beneficiary_data['contact']).exists()
            duplicate_name_contact = Beneficiary.objects.filter(
                first_name=beneficiary_data['first_name'],
                last_name=beneficiary_data['last_name'],
                contact=beneficiary_data['contact']
            ).exists()
            
            if duplicate_contact:
                messages.error(request, f"❌ Contact '{beneficiary_data['contact']}' already registered!")
                return render(request, 'beneficiaries/online_application.html', {'post_data': dict(request.POST)})
            
            if duplicate_name_contact:
                messages.error(request, f"❌ '{beneficiary_data['first_name']} {beneficiary_data['last_name']}' with this contact already exists!")
                return render(request, 'beneficiaries/online_application.html', {'post_data': dict(request.POST)})
            
            # ✅ TRANSACTION: Save Beneficiary + Documents
            with transaction.atomic():
                # 1. CREATE BENEFICIARY
                beneficiary = Beneficiary(**beneficiary_data)
                beneficiary.save()
                
                # 🔥 2. SAVE ALL PHOTO UPLOADS to BeneficiaryDocument
                document_fields = [
                    'doc_Liham_kahilingan', 'doc_Cert_barangay_indigency', 'doc_Project_proposal',
                    'doc_Repayment_schema', 'doc_Marriage_contract', 'doc_Birth_certificate',
                    'doc_Valid_ID', 'doc_Community_Tax', 'doc_Training_certificate'
                ]
                
                uploaded_count = 0
                for field_name in document_fields:
                    if field_name in request.FILES and request.FILES[field_name]:
                        doc_file = request.FILES[field_name]
                        
                        # Create document record
                        BeneficiaryDocument.objects.update_or_create(
                            beneficiary=beneficiary,
                            doc_type=field_name,  # ✅ Exact match to your DOC_TYPE_CHOICES
                            defaults={
                                'file': doc_file,
                                'note': f'Online upload: {doc_file.name} ({doc_file.size} bytes)',
                                'uploaded_at': timezone.now()
                            }
                        )
                        uploaded_count += 1
                
                # Update documents count in remarks
                if uploaded_count > 0:
                    beneficiary.remarks_admin = f"Online app: {uploaded_count} docs uploaded"
                    beneficiary.save()
            
            # 🔥 LOG ACTIVITY
            try:
                UserActivity.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action="Online Application",
                    details=f"New online application (ID: {beneficiary.beneficiary_id}) - {beneficiary_data['first_name']} {beneficiary_data['last_name']} (Email: {email}) - {uploaded_count} docs"
                )
            except:
                pass
            
            # ✅ SUCCESS - PENDING STATUS
            messages.success(
                request,
                f'✅ Application SUBMITTED SUCCESSFULLY! '
                f'ID: <strong>{beneficiary.beneficiary_id}</strong><br>'
                f'Email: <strong>{email}</strong><br>'
                f'Status: <strong style="color:orange">PENDING REVIEW</strong><br>'
                f'{uploaded_count} documents uploaded.',
                extra_tags='online-success'
            )
            
            # Clear session data
            request.session['last_beneficiary_id'] = str(beneficiary.beneficiary_id)
            return redirect('application_success')  # or success page
            
        except Exception as e:
            logger.error(f"Online application error: {str(e)}")
            messages.error(request, f'❌ Application failed: {str(e)}')
    
    return render(request, 'beneficiaries/online_application.html')

def success(request):
    return render(request, 'beneficiaries/success.html')   

@login_required
def online_applicants_list(request):
    if not (request.user.is_superuser or request.user.position == "Admin"):
        messages.error(request, "Access denied. Admin only.")
        return redirect('dashboard')
    
    from .models import Beneficiary, BeneficiaryDocument
    
    applicants = Beneficiary.objects.filter(
        application_source='online',
        application_status='Pending'
    ).select_related(
        'district', 'municipality', 'barangay', 'approved_by'
    ).prefetch_related('documents').order_by('-applied_at')
    
    context = {
        'applicants': applicants,
        'total_online': applicants.count(),
        'documents_uploaded': BeneficiaryDocument.objects.filter(
            beneficiary__application_source='online'
        ).count()
    }
    
    return render(request, 'beneficiaries/view_applicants.html', context)

@login_required
def applicant_detail(request, id_number):
    if not (request.user.is_superuser or request.user.position == "Admin"):
        messages.error(request, "Access denied.")
        return redirect('dashboard')
    
    applicant = get_object_or_404(
        Beneficiary.objects.prefetch_related('documents'),
        id_number=id_number,
        application_source='online'
    )
    
    context = {
        'applicant': applicant,
        'documents': applicant.documents.all()
    }
    return render(request, 'beneficiaries/view_applicants_detail.html', context)

@login_required
def beneficiary_details(request, id_number):
    beneficiary = get_object_or_404(Beneficiary, id_number=id_number)
    documents = beneficiary.documents.all()
    
    context = {
        'beneficiary': beneficiary,
        'documents': documents,
        'title': f'{beneficiary.beneficiary_id} Details',
    }
    return render(request, 'beneficiaries/beneficiaries_details.html', context)

@login_required
def update_beneficiary(request, id_number):
    beneficiary = get_object_or_404(Beneficiary, id_number=id_number)
    
    districts = District.objects.all()
    municipalities = Municipality.objects.filter(district=beneficiary.district)
    barangays = Barangay.objects.filter(municipality=beneficiary.municipality)
    
    # ✅ PRE-CALCULATE DOCUMENT STATUS
    doc_status = {}
    doc_types = [
        'Liham_kahilingan', 'Cert_barangay_indigency', 'Project_proposal',
        'Repayment_schema', 'Marriage_contract', 'Birth_certificate',
        'Valid_ID', 'Community_Tax', 'Training_certificate'
    ]
    
    for doc_type in doc_types:
        doc_status[doc_type] = beneficiary.documents.filter(doc_type=doc_type).exists()
    
    if request.method == 'POST':
        form = BeneficiaryForm(request.POST, instance=beneficiary)
        if form.is_valid():
            beneficiary = form.save(commit=False)  # 🔥 DON'T SAVE YET
            
            # 🔥 AUTO-CALCULATE NET INCOME (Backend protection)
            try:
                income = float(request.POST.get('avg_monthly_income', 0) or 0)
                expenses = float(request.POST.get('avg_monthly_expenses', 0) or 0)
                beneficiary.net_monthly_income = max(0, income - expenses)
            except (ValueError, TypeError):
                beneficiary.net_monthly_income = 0
            
            beneficiary.save()  # 🔥 NOW SAVE WITH CALCULATED NET INCOME
            
            # ✅ HANDLE DOCUMENT CHECKBOXES (unchanged)
            doc_fields = [
                'doc_Liham_kahilingan', 'doc_Cert_barangay_indigency', 'doc_Project_proposal',
                'doc_Repayment_schema', 'doc_Marriage_contract', 'doc_Birth_certificate',
                'doc_Valid_ID', 'doc_Community_Tax', 'doc_Training_certificate'
            ]
            
            # Remove existing document flags
            existing_doc_types = [field.replace('doc_', '') for field in doc_fields]
            BeneficiaryDocument.objects.filter(
                beneficiary=beneficiary,
                doc_type__in=existing_doc_types
            ).delete()
            
            # Create new document flags
            for field in doc_fields:
                if request.POST.get(field):
                    BeneficiaryDocument.objects.get_or_create(
                        beneficiary=beneficiary,
                        doc_type=field.replace('doc_', ''),
                        defaults={'file': None}
                    )
                    
            # 🔥 USER ACTIVITY LOG - UPDATE
            try:
                current_user = request.user
                UserActivity.objects.create(
                    user=current_user,
                    action="Update Beneficiary",
                    details=f"Updated beneficiary (ID: {beneficiary.beneficiary_id}) - {beneficiary.first_name} {beneficiary.last_name}"
                )
            except Exception as e:
                print(f"Activity log failed: {e}")
            
            messages.success(request, f'Beneficiary {beneficiary.beneficiary_id} updated successfully!')
            return redirect('beneficiary_details', id_number=beneficiary.id_number)
        else:
            # 🔥 DEBUG: Print form errors
            print("FORM ERRORS:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BeneficiaryForm(instance=beneficiary)
    
    context = {
        'beneficiary': beneficiary,
        'form': form,
        'doc_status': doc_status,
        'districts': districts,
        'municipalities': municipalities,
        'barangays': barangays,
    }
    return render(request, 'beneficiaries/update_details.html', context)

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@csrf_exempt
@require_http_methods(["POST"])
def mark_beneficiary_inactive(request, id_number):
    try:
        beneficiary = get_object_or_404(Beneficiary, id_number=id_number)
        remarks = request.POST.get('remarks', '').strip()
        
        if not remarks:
            return JsonResponse({'success': False, 'error': 'Remarks required'})
        
        beneficiary.application_status = 'Inactive'
        beneficiary.remarks_admin = remarks
        beneficiary.save()
        
        # ✅ DJANGO MESSAGE
        full_name = f"{beneficiary.first_name} {beneficiary.last_name}".strip()
        messages.success(request, f"'{full_name}' has been marked as Inactive successfully!")
        
        # Log activity...
        
        return JsonResponse({'success': True})
    except Exception as e:
        messages.error(request, f"Error marking beneficiary inactive: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

# Same for mark_beneficiary_active
@csrf_exempt
@require_http_methods(["POST"])
def mark_beneficiary_active(request, id_number):
    try:
        beneficiary = get_object_or_404(Beneficiary, id_number=id_number)
        remarks = request.POST.get('remarks', '').strip()
        
        if not remarks:
            return JsonResponse({'success': False, 'error': 'Remarks required'})
        
        beneficiary.application_status = 'Approved'
        beneficiary.remarks_admin = remarks
        beneficiary.save()
        
        # ✅ DJANGO MESSAGE
        full_name = f"{beneficiary.first_name} {beneficiary.last_name}".strip()
        messages.success(request, f"'{full_name}' has been marked as Active successfully!")
        
        return JsonResponse({'success': True})
    except Exception as e:
        messages.error(request, f"Error marking beneficiary active: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

import csv
from django.http import HttpResponse
import pandas as pd
import io
from django.db.models import Max

@login_required
@require_http_methods(["POST"])
def beneficiaries_import(request):
    print("🔥 AUTO-ID IMPORT STARTED")
    current_user = request.user
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    try:
        uploaded_file = request.FILES.get('csv_file')
        if not uploaded_file:
            return JsonResponse({'status': 'error', 'message': 'No file uploaded!'}, status=400)
        
        filename = uploaded_file.name.lower()
        print(f"📁 Processing file: {uploaded_file.name} ({filename})")
        
        # 🔥 EXCEL SUPPORT (.xlsx, .xls, .xlx)
        if filename.endswith(('.xlsx', '.xls', '.xlx')):
            try:
                import pandas as pd
                uploaded_file.seek(0)
                df = pd.read_excel(uploaded_file, nrows=1000)
                print(f"✅ Excel processed: {len(df)} rows | Columns: {list(df.columns)}")
            except Exception as excel_error:
                return JsonResponse({'status': 'error', 'message': f'Excel read error: {str(excel_error)}'}, status=400)
        
        # 🔥 CSV SUPPORT (.csv, .txt, etc.)
        else:
            raw_content = uploaded_file.read().decode('utf-8-sig')
            uploaded_file.seek(0)
            
            try:
                df = pd.read_csv(uploaded_file, nrows=1000, low_memory=False)
                print(f"✅ CSV processed: {len(df)} rows | Columns: {list(df.columns)}")
            except:
                uploaded_file.seek(0)
                csv_reader = csv.reader(io.StringIO(raw_content))
                rows = list(csv_reader)
                if len(rows) < 2:
                    return JsonResponse({'status': 'error', 'message': 'Empty or invalid file!'}, status=400)
                df = pd.DataFrame(rows[1:], columns=rows[0])
                print(f"✅ CSV (manual) processed: {len(df)} rows")
        
        # 🔥 Find ID column (matches export)
        id_col = None
        for col in df.columns:
            if 'beneficiary_id' in col.lower():
                id_col = col
                break
        
        if not id_col:
            return JsonResponse({'status': 'error', 'message': f"No 'beneficiary_id' column! Found: {list(df.columns)}"}, status=400)
        
        print(f"✅ Processing {len(df)} rows using ID column: '{id_col}'")
        
        # 🔥 GET NEXT AVAILABLE ID NUMBER
        max_id = Beneficiary.objects.aggregate(Max('beneficiary_id'))['beneficiary_id__max']
        next_number = 1
        
        if max_id:
            try:
                import re
                numbers = re.findall(r'\d+', max_id)
                if numbers:
                    next_number = max(int(x) for x in numbers) + 1
            except:
                next_number = 1
        
        print(f"🔥 Next available ID number: {next_number:07d}")
        
        # 🔥 Process rows (MATCHES EXPORT EXACTLY)
        created_count = skipped_count = error_count = updated_count = 0
        auto_id_count = 0
        
        for index, row in df.iterrows():
            try:
                beneficiary_id_raw = str(row[id_col]).strip().strip('"').strip()
                if not beneficiary_id_raw or beneficiary_id_raw.lower() in ['nan', 'null', '', 'none']:
                    beneficiary_id = f"{next_number:07d}"
                    next_number += 1
                    auto_id_count += 1
                    print(f"🔥 AUTO ID: {beneficiary_id}")
                else:
                    beneficiary_id = beneficiary_id_raw
                    print(f"🔥 Using provided ID: {beneficiary_id}")
                
                # 🔥 Check if exists (skip OR update option)
                beneficiary, created = Beneficiary.objects.get_or_create(
                    beneficiary_id=beneficiary_id,
                    defaults={
                        'last_name': str(row.get('last_name', 'Unknown')).strip().title(),
                        'first_name': str(row.get('first_name', 'Unknown')).strip().title(),
                        'middle_name': str(row.get('middle_name', '')).strip().title(),
                        'street_house': str(row.get('street_house', '')).strip(),
                        'contact': str(row.get('contact', '')).strip(),
                        'category': str(row.get('category', 'Indigent')),
                        'project': str(row.get('project', 'General')),
                        'sex': str(row.get('sex', 'M'))[:1].upper(),
                        'civil_status': str(row.get('civil_status', 'Single')),
                        'application_status': str(row.get('application_status', 'Approved'))
                    }
                )
                
                if created:
                    created_count += 1
                    print(f" NEW Created: {beneficiary_id}")
                else:
                    # 🔥 UPDATE existing record with location data
                    beneficiary.last_name = str(row.get('last_name', beneficiary.last_name)).strip().title()
                    beneficiary.first_name = str(row.get('first_name', beneficiary.first_name)).strip().title()
                    beneficiary.middle_name = str(row.get('middle_name', beneficiary.middle_name or '')).strip().title()
                    beneficiary.street_house = str(row.get('street_house', beneficiary.street_house or '')).strip()
                    beneficiary.contact = str(row.get('contact', beneficiary.contact or '')).strip()
                    beneficiary.category = str(row.get('category', beneficiary.category))
                    beneficiary.project = str(row.get('project', beneficiary.project))
                    beneficiary.sex = str(row.get('sex', beneficiary.sex))[:1].upper()
                    beneficiary.civil_status = str(row.get('civil_status', beneficiary.civil_status))
                    beneficiary.application_status = str(row.get('application_status', beneficiary.application_status))
                    beneficiary.save()
                    updated_count += 1
                    print(f"  🔄 UPDATED: {beneficiary_id}")
                    continue
                
                # 🔥 SET LOCATION FIELDS (matches export exactly)
                try:
                    district_name = str(row.get('district', '')).strip()
                    municipality_name = str(row.get('municipality', '')).strip()
                    barangay_name = str(row.get('barangay', '')).strip()
                    
                    # 🔥 Try to match by name (flexible)
                    if district_name:
                        district_obj, _ = District.objects.get_or_create(name=district_name)
                        beneficiary.district = district_obj
                    
                    if municipality_name:
                        municipality_obj, _ = Municipality.objects.get_or_create(name=municipality_name)
                        beneficiary.municipality = municipality_obj
                    
                    if barangay_name:
                        barangay_obj, _ = Barangay.objects.get_or_create(name=barangay_name)
                        beneficiary.barangay = barangay_obj
                    
                    beneficiary.save()
                    print(f"  📍 Location set: {barangay_name}, {municipality_name}")
                except Exception as loc_error:
                    print(f" Location error {beneficiary_id}: {loc_error}")
                
            except Exception as e:
                error_count += 1
                print(f"  ❌ Error row {index}: {e}")
                continue
        
        # 🔥 Activity log
        try:
            UserActivity.objects.create(
                user=current_user,
                action="Import Beneficiaries",
                details=f"Imported {created_count} new from {uploaded_file.name} ({updated_count} skipped, {error_count} errors)"
            )
        except Exception as log_error:
            print(f"Activity log failed: {log_error}")
        
        msg = (
            f"Import Complete!\n"
            f"File: {uploaded_file.name}\n"
            f"• {created_count} NEW created\n"
            f"• {updated_count} DUPLICATE (SKIPPED)\n"
            f"• {auto_id_count} auto IDs\n"
            f"• {error_count} errors\n"
            f"Total processed: {len(df)} rows"
        )
        
        return JsonResponse({
            'status': 'success',
            'message': msg,
            'summary': {
                'created': created_count,
                'updated': updated_count,
                'auto_ids': auto_id_count,
                'errors': error_count,
                'total': len(df),
                'filename': uploaded_file.name
            }
        })
        
    except Exception as e:
        print(f"💥 Import failed: {e}")
        return JsonResponse({'status': 'error', 'message': f'Import failed: {str(e)}'}, status=500)
            
@login_required
def beneficiaries_export(request):
    current_user = request.user  # 🔥 For logging
    
    # Get current filters (unchanged)
    district = request.GET.get('district')
    municipality = request.GET.get('municipality')
    barangay = request.GET.get('barangay')
    search = request.GET.get('search')
    tab = request.GET.get('tab', 'active')
    
    queryset = Beneficiary.objects.all()
    
    if tab == 'inactive':
        queryset = queryset.filter(application_status__in=['Inactive', 'Rejected'])
    else:
        queryset = queryset.filter(application_status='Approved')
    
    if district:
        queryset = queryset.filter(district_id=district)
    if municipality:
        queryset = queryset.filter(municipality_id=municipality)
    if barangay:
        queryset = queryset.filter(barangay_id=barangay)
    if search:
        queryset = queryset.filter(
            Q(last_name__icontains=search) | 
            Q(first_name__icontains=search) |
            Q(beneficiary_id__icontains=search)
        )
    
    count = queryset.count()
    
    # 🔥 LOG EXPORT ACTIVITY (BEFORE generating file)
    try:
        filters = []
        if district: filters.append(f"District={district}")
        if municipality: filters.append(f"Municipality={municipality}")
        if barangay: filters.append(f"Barangay={barangay}")
        if search: filters.append(f"Search={search}")
        if tab != 'active': filters.append(f"Tab={tab}")
        
        filter_details = f"[{', '.join(filters)}]" if filters else "[All]"
        
        UserActivity.objects.create(
            user=current_user,
            action="Export Beneficiaries",
            details=f"Exported {count} beneficiaries CSV {filter_details}"
        )
        print(f"✅ Activity logged: Export {count} beneficiaries")
    except Exception as log_error:
        print(f"⚠️ Export log failed: {log_error}")
    
    # 🔥 CSV response (unchanged)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="beneficiaries_{tab}_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'
    
    writer = csv.writer(response)
    
    writer.writerow([
        'beneficiary_id', 'last_name', 'first_name', 'middle_name', 'street_house',
        'contact', 'district', 'municipality', 'barangay', 'category', 'project',
        'sex', 'civil_status', 'application_status'
    ])
    
    for beneficiary in queryset:
        writer.writerow([
            f'"{beneficiary.beneficiary_id}"',  # ✅ Preserves leading zeros
            
            beneficiary.last_name or '',
            beneficiary.first_name or '',
            beneficiary.middle_name or '',
            beneficiary.street_house or '',
            beneficiary.contact or '',
            getattr(beneficiary.district, 'name', '') or '',
            getattr(beneficiary.municipality, 'name', '') or '',
            getattr(beneficiary.barangay, 'name', '') or '',
            beneficiary.category or '',
            beneficiary.project or '',
            beneficiary.sex or '',
            beneficiary.civil_status or '',
            beneficiary.application_status or ''
        ])
    
    print(f"✅ Exported {count} beneficiaries - beneficiary_id format preserved")
    return response

from django.conf import settings
from django.core.mail import send_mail
from beneficiaries.models import Beneficiary

def send_status_email(beneficiary, status):
    if status == "Approved":
        subject = "Notice of Application Approval"
        application_id = beneficiary.beneficiary_id
        message = (
            f"Magandang araw, {beneficiary.first_name},\n\n"
            "Ipinababatid po namin na ang inyong aplikasyon sa SEA o Pandagdag Puhunan ay *APPROVED*.\n\n"
            f"📌 Application Reference ID: {application_id}\n\n"
            "Ang nasabing Application Reference ID ay mahalagang tandaan at gamitin sa lahat ng susunod na transaksyon.\n\n"
            "Maari na po kayong magtungo sa aming tanggapan upang isumite ang mga kinakailangang dokumento:\n\n"
            "• Liham Kahilingan sa Punong Lalawigan\n"
            "• Certificate of Barangay Indigency\n"
            "• Project Proposal mula sa C/MSWDO\n"
            "• Repayment Schema mula sa C/MSWDO\n"
            "• Marriage Contract (kung kasal)\n"
            "• Birth Certificate (kung single)\n"
            "• Valid ID\n"
            "• Community Tax Certificate (Cedula)\n"
            "• Certificate of Training mula sa PCEDO\n\n"
            "Para sa anumang katanungan kay Ms. Pinky Valeriano mula sa Women Center (PSWDO).\n\n"
            "Maraming salamat."
        )
    else:
        subject = "Notice of Application Result"
        message = (
            f"Magandang araw, {beneficiary.first_name},\n\n"
            "Ipinapaabot po namin na ang inyong aplikasyon ay *HINDI APRUBADO*.\n\n"
            "Maraming salamat sa inyong pag-unawa."
        )
    
    send_mail(subject, message, settings.EMAIL_HOST_USER, [beneficiary.email], fail_silently=False)

@csrf_exempt
@require_http_methods(["POST"])
def approve_online_applicant(request, beneficiary_id):
    beneficiary = get_object_or_404(Beneficiary, beneficiary_id=beneficiary_id)
    beneficiary.application_status = "Approved"  # ← Add this field if missing
    beneficiary.save()
    send_status_email(beneficiary, "Approved")
    return JsonResponse({'success': True, 'message': 'Approved & Email Sent!'})

@csrf_exempt
@require_http_methods(["POST"])
def reject_online_applicant(request, beneficiary_id):
    beneficiary = get_object_or_404(Beneficiary, beneficiary_id=beneficiary_id)
    beneficiary.application_status = "Rejected"
    beneficiary.save()
    send_status_email(beneficiary, "Rejected")
    return JsonResponse({'success': True, 'message': 'Rejected & Email Sent!'})

def beneficiary_renewal(request, beneficiary_id):
    # Get beneficiary from URL
    beneficiary = get_object_or_404(Beneficiary, beneficiary_id=beneficiary_id)
    
    if request.method == 'POST':
        loan_amount = request.POST.get('loan_amount')
        docs_checked = request.POST.getlist('doc_')
        
        # Update
        beneficiary.loan_amount_requested = float(loan_amount)
        beneficiary.application_status = 'Renewal Submitted'
        beneficiary.save()
        
        messages.success(request, f'✅ Renewal OK! Loan: ₱{loan_amount:,}')
        return redirect('beneficiaries')
    
    return render(request, 'beneficiaries/renewal.html', {'beneficiary': beneficiary})