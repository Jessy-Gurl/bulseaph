from django.db import models
from django.conf import settings
from django.utils import timezone


# Create your models here.
class District(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'district'  # exact table name in DB

    def __str__(self):
        return self.name


class Municipality(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='municipalities')
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'municipality'

    def __str__(self):
        return self.name


class Barangay(models.Model):
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE, related_name='barangays')
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'barangay'

    def __str__(self):
        return self.name


# Beneficiary model
class Beneficiary(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Inactive', 'Inactive'),
    ]
    application_status = models.CharField(
    max_length=20,
    choices=STATUS_CHOICES,
    default='Pending'
)

    SEX_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    CIVIL_STATUS_CHOICES = [
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Widowed', 'Widowed'),
        ('Divorced', 'Divorced'),
    ]
    CATEGORY_CHOICES = [
        ('Choose', 'Choose'),
        ('4ps', '4ps'),
        ('Senior', 'Senior'),
        ('PWD', 'PWD'),
        ('Solo Parent', 'Solo Parent'),
        ('Indigent', 'Indigent'),
    ]
    LOAN_PURPOSE_CHOICES = [
        ('Business Expansion', 'Business Expansion'),
        ('Start-up Capital', 'Start-up Capital'),
        ('Equipment', 'Equipment'),
        ('Inventory', 'Inventory'),
        ('Others', 'Others'),
    ]
    NATURE_BUSINESS_CHOICES = [
        ('Retail', 'Retail'),
        ('Service', 'Service'),
        ('Food', 'Food'),
        ('Others', 'Others'),
    ]
    ASSET_CHOICES = [
        ('House', 'House'),
        ('Lot', 'Lot'),
        ('Vehicle', 'Vehicle'),
        ('Livestock', 'Livestock'),
        ('Equipment', 'Equipment'),
    ]

    id_number = models.AutoField(primary_key=True)
    beneficiary_id = models.CharField(
        max_length=7,
        unique=True,
        editable=False,
        null=True,
        blank=True
    )

    # Personal Info
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    civil_status = models.CharField(max_length=10, choices=CIVIL_STATUS_CHOICES)
    contact = models.CharField(max_length=150)
    email = models.EmailField(max_length=254, unique=True, null=True, blank=True)
    district = models.ForeignKey('District', on_delete=models.SET_NULL, null=True)
    municipality = models.ForeignKey('Municipality', on_delete=models.SET_NULL, null=True)
    barangay = models.ForeignKey('Barangay', on_delete=models.SET_NULL, null=True)
    street_house = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Choose')
    project = models.CharField(max_length=100)

    # A. Personal additions
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.PositiveSmallIntegerField(null=True, blank=True)

    # B. Family
    spouse_name = models.CharField(max_length=200, null=True, blank=True)
    num_of_dependents = models.PositiveSmallIntegerField(null=True, blank=True)
    ages_of_dependents = models.CharField(max_length=200, null=True, blank=True,
                                          help_text="Comma-separated ages, e.g. '3,6,12'")

    # C. Education
    education_level = models.CharField(max_length=50, null=True, blank=True,
                                       help_text="Elementary/High School/Vocational/College/Others")

    # D. Livelihood / Business
    BUSINESS_STATUS_CHOICES = [
    ('existing', 'Existing Business'),
    ('starting', 'Starting Business'),
    ]

    business_status = models.CharField(
    max_length=20,
    choices=BUSINESS_STATUS_CHOICES,
    null=True,
    blank=True
    )

    type_of_business = models.CharField(max_length=200, null=True, blank=True)
    business_name = models.CharField(max_length=200, null=True, blank=True)
    business_address = models.CharField(max_length=255, null=True, blank=True)
    years_in_operation = models.PositiveSmallIntegerField(null=True, blank=True)
    nature_of_business = models.CharField(max_length=50, choices=NATURE_BUSINESS_CHOICES,
                                          null=True, blank=True)
    avg_monthly_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    avg_monthly_expenses = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    net_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # E. Loan
    loan_purpose = models.CharField(max_length=50, choices=LOAN_PURPOSE_CHOICES, null=True, blank=True)
    loan_purpose_other = models.CharField(max_length=200, null=True, blank=True)

    # F. Assets & liabilities
    owned_assets = models.CharField(max_length=255, null=True, blank=True,
                                    help_text="Comma-separated: House,Lot,Vehicle,...")
    other_assets = models.CharField(max_length=255, null=True, blank=True)
    outstanding_loans = models.TextField(null=True, blank=True,
                                         help_text="If any: source and balance, e.g. 'Sakura Bank - ₱5,000'")

    # G. Community involvement
    is_member_of_org = models.BooleanField(default=False)
    organization_name = models.CharField(max_length=255, null=True, blank=True)

    # 🟩 H. Documents — handled by BeneficiaryDocument model (no direct fields here)
    documents_submitted_in_person = models.BooleanField(default=False)

    # I. Declaration & status
    declaration_signed = models.BooleanField(default=False)
    application_status = models.CharField(max_length=30, default='Pending')
    
    application_source = models.CharField(
    max_length=20,
    default='walkin',
    choices=[('online', 'Online Application'), ('walkin', 'Walk-in')],
)
    
    applied_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='approved_beneficiaries')
    approved_at = models.DateTimeField(null=True, blank=True)
    remarks_admin = models.TextField(null=True, blank=True)

    # 🟩 Track last updated (for admin/logs)
    updated_at = models.DateTimeField(auto_now=True)
    renewal_count = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.beneficiary_id:
            last = Beneficiary.objects.order_by('-id_number').first()
            next_num = 1 if not last else last.id_number + 1
            self.beneficiary_id = str(next_num).zfill(7)
        if not self.applied_at:
            self.applied_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


# -------------------------------------------------------
# 🟩 Documents: multiple upload per beneficiary
# -------------------------------------------------------
def beneficiary_document_upload_to(instance, filename):
    bid = instance.beneficiary.beneficiary_id or f"id{instance.beneficiary.id_number}"
    safe_doc = instance.doc_type.replace(' ', '_')
    return f"beneficiary_docs/{bid}/{safe_doc}__{timezone.now().strftime('%Y%m%d%H%M%S')}__{filename}"

class BeneficiaryDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('Liham_kahilingan', 'Liham kahilingan sa Punong Lalawigan'),
        ('Cert_barangay_indigency', 'Certificate of Barangay Indigency'),
        ('Project_proposal', 'Project Proposal from C/MSWDO'),
        ('Repayment_schema', 'Repayment Schema from C/MSWDO'),
        ('Marriage_contract', 'Marriage Contract'),
        ('Birth_certificate', 'Birth Certificate'),
        ('Valid_ID', 'Valid ID'),
        ('Community_Tax', 'Community Tax Certificate (Cedula)'),
        ('Training_certificate', 'Certificate of training from PCEDO'),
        ('Other', 'Other'),
    ]

    beneficiary = models.ForeignKey(
        Beneficiary,
        on_delete=models.CASCADE,
        related_name='documents'
    )

    doc_type = models.CharField(
        max_length=50,
        choices=DOC_TYPE_CHOICES,
        default='Other'
    )

    file = models.FileField(
        upload_to=beneficiary_document_upload_to,
        null=True,
        blank=True
    )

    uploaded_at = models.DateTimeField(auto_now=True)
    note = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['beneficiary', 'doc_type'],
                name='unique_document_per_beneficiary'
            )
        ]

    @property
    def filename(self):
        if self.file:
            return self.file.name.split('/')[-1]
        return None

    def __str__(self):
        return f"{self.get_doc_type_display()} - {self.beneficiary}"