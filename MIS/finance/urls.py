from django.urls import path
from . import views

urlpatterns = [
    path('finance/<str:id_number>/', views.finance, name='finance'),
    path('loan/<int:loan_id>/', views.loan_records, name='loan_records'),
]