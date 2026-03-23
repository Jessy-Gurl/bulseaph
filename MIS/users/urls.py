from django.urls import path
from .views import login_view, dashboard
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('edit-homepage/', views.edit_hp_contents, name='edit_hp_contents'),
    path('update-homepage/', views.update_homepage_content, name='update_homepage_content'),
    path('login/', login_view, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', views.custom_logout, name='logout'),
     # Message Endpoints
    path('messages/send/', views.send_message, name='send_message'),
    path('messages/<int:receiver_id>/', views.get_messages, name='get_messages'),
    path('messages/unread-count/', views.get_unread_count, name='unread_count'),
    path('messages/unread-count/<int:user_id>/', views.get_user_unread_count, name='user_unread_count'),
    path('messages/mark-read/<int:receiver_id>/', views.mark_messages_read, name='mark_messages_read'),
    path('user_settings/', views.user_settings, name='user_settings'),
    path('user_settings/profile/', views.profile_settings, name='profile_settings'),
    path('user_settings/security/', views.security_settings, name='security_settings'),
    path('user_settings/manage-homepage/', views.manage_homepage, name='manage_homepage'),
    path('manage-homepage/', views.manage_homepage, name='manage_homepage'),
    path('user_management/', views.user_management, name='user_management'),
    path('add_user/', views.add_user, name='add_user'),
    path('delete_user/<str:id_number>/', views.delete_user, name='delete_user'),
    path('user/<str:id_number>/activities/', views.user_activities, name='user_activities'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),

    
]
# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)