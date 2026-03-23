from django.urls import path
from . import views

urlpatterns = [
    path('beneficiaries/', views.beneficiaries, name='beneficiaries'),
    path('api/filters/districts/', views.api_districts, name='api_districts'),
    path('api/filters/municipalities/', views.api_municipalities, name='api_municipalities'),
    path('api/filters/barangays/', views.api_barangays, name='api_barangays'),
    path('add/', views.add_beneficiary, name='add_beneficiary'),
    path('details/<int:id_number>/', views.beneficiary_details, name='beneficiary_details'),
    path('details/<int:id_number>/update/', views.update_beneficiary, name='update_beneficiary'),
    path('api/table/', views.api_table, name='api_table'),
    path('<str:id_number>/mark-inactive/', views.mark_beneficiary_inactive, name='mark_beneficiary_inactive'),
    path('<str:id_number>/mark-active/', views.mark_beneficiary_active, name='mark_beneficiary_active'),
    path('import/', views.beneficiaries_import, name='beneficiaries_import'),
    path('export/', views.beneficiaries_export, name='beneficiaries_export'),
    path('online-application/', views.online_application, name='online_application'),
    path('application-success/', views.success, name='application_success'),
    path('online-applicants/', views.online_applicants_list, name='online_applicants'),
    path('online-applicants/<int:id_number>/', views.applicant_detail, name='applicant_detail'),
    path('renewal/', views.beneficiary_renewal, name='beneficiary_renewal'),
    path('renewal/<str:beneficiary_id>/', views.beneficiary_renewal, name='beneficiary_renewal'),
]