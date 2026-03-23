from django.urls import path
from . import views

# 🔥 Add these URL patterns
urlpatterns = [
    # ... your existing urls
    
    # 🔥 REPORT API ENDPOINTS (exact match for JS)
    path('api/districts/', views.api_districts, name='api_districts'),
    path('api/municipalities/', views.api_municipalities, name='api_municipalities'),
    path('api/barangays/', views.api_barangays, name='api_barangays'),
    path('api/report-summary/', views.report_summary_api, name='report_summary_api'),
    path('report/', views.report_page, name='report_page'),
    path('api/reports/cashflow/', views.cashflow_report, name='cashflow_report'),
    path('export/excel/cashflow/', views.export_cashflow_excel, name='export_excel'),
]