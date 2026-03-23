from django.db import models

class ReportSummary(models.Model):
    date = models.DateField()
    period_type = models.CharField(max_length=20)
    total_loans = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_count = models.IntegerField(default=0)
    total_payments = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_count = models.IntegerField(default=0)
    net_cashflow = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'report_summary'