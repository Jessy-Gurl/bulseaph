"""
URL configuration for MIS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from beneficiaries.views import approve_online_applicant, reject_online_applicant

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('beneficiaries/', include('beneficiaries.urls')),
    path('finance/', include('finance.urls')),
    path('report/', include('report.urls')),
    path('api/applicants/<str:beneficiary_id>/approve/', approve_online_applicant),
    path('api/applicants/<str:beneficiary_id>/reject/', reject_online_applicant),
]

# Media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)