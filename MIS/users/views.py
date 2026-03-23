from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.utils import timezone
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Message
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.conf import settings
import logging
from django.core.mail import send_mail
from django.db import transaction
from datetime import timedelta
from django.core.paginator import Paginator
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import update_session_auth_hash
from .models import HomepageHeader, HomepageContent, HomepageFooter
import json
from django.shortcuts import render, redirect, get_object_or_404
from .forms import HomepageContentForm
from django.db import models 
from .utils import log_activity
from .models import CustomUser, OTPCode, UserActivity
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.crypto import constant_time_compare
from . import views 
from beneficiaries.models import Beneficiary


logger = logging.getLogger(__name__)

User = get_user_model()

def login_view(request):
    if request.method == "POST":
        id_number = request.POST.get("id_number")
        password = request.POST.get("password")

        user = authenticate(request, id_number=id_number, password=password)

        if user is not None:
            login(request, user)
            user.is_logged_in = True  # ✅ Mark as logged in
            user.last_activity = timezone.now()
            user.save()
            return redirect('dashboard')
        else:
            return render(request, "login.html", {"error": "Invalid ID Number or Password"})

    return render(request, "login.html")


@login_required
def dashboard(request):
    user = request.user
    from beneficiaries.models import Beneficiary
    
    context = {
        'user': user,
        
        # 🔥 YOUR EXISTING COUNTS
        'applicants_count': Beneficiary.objects.filter(application_status='Pending').count(),
        'active_count': Beneficiary.objects.filter(application_status='Approved').count(),
        'inactive_count': Beneficiary.objects.filter(application_status__in=['Rejected', 'Inactive']).count(),
        
        # 🆕 ONLINE APPLICANTS
        'online_applicants_count': Beneficiary.objects.filter(
            application_source='online',
            application_status='Pending'
        ).count(),
    }
    
    return render(request, 'dashboard.html', context)

def custom_logout(request):
    request.user.is_logged_in = False  # ✅ Mark as logged OUT
    request.user.last_logout_time = timezone.now()
    request.user.save()
    logout(request)
    return redirect('login')

@login_required
def send_message(request):
    if request.method == "POST":
        receiver_id = request.POST.get("receiver")
        text = request.POST.get("text", "").strip()
        uploaded_file = request.FILES.get("file")

        if not receiver_id:
            return JsonResponse({"error": "No receiver selected"}, status=400)

        try:
            receiver = User.objects.get(id=int(receiver_id))
        except (User.DoesNotExist, ValueError):
            return JsonResponse({"error": "Invalid receiver"}, status=400)

        if not text and not uploaded_file:
            return JsonResponse({"error": "Empty message"}, status=400)

        try:
            msg = Message.objects.create(
                sender=request.user,
                receiver=receiver,
                text=text,
                file=uploaded_file,
                timestamp=timezone.now()
            )
            logger.info(f"Message sent from {request.user.id} to {receiver.id}")
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

        image_ext = ('png', 'jpg', 'jpeg', 'gif')
        is_image = uploaded_file.name.lower().endswith(image_ext) if uploaded_file else False

        file_url = None
        if uploaded_file:
            # Safely handle MEDIA_URL
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            file_url = f"{media_url}{msg.file.name}"

        return JsonResponse({
            "text": msg.text,
            "file": file_url,
            "image": file_url if is_image else None,
            "timestamp": msg.timestamp.strftime("%B %d, %Y %I:%M %p"),
            "timestamp_raw": msg.timestamp.isoformat(),
        })
    return JsonResponse({"error": "Invalid method"}, status=405)

@login_required
def get_messages(request, receiver_id):
    """Get messages between current user and receiver"""
    try:
        receiver_id = int(receiver_id)
        receiver = User.objects.get(id=receiver_id)
    except (User.DoesNotExist, ValueError, TypeError):
        logger.warning(f"Invalid receiver_id: {receiver_id}")
        return JsonResponse({"messages": []}, status=200)

    try:
        messages = Message.objects.filter(
            (Q(sender=request.user, receiver=receiver) | Q(sender=receiver, receiver=request.user))
        ).order_by('timestamp')
        
        msg_list = []
        for msg in messages:
            image_ext = ('png', 'jpg', 'jpeg', 'gif')
            is_image = msg.file and msg.file.name.lower().endswith(image_ext) if msg.file else False
            
            file_url = None
            if msg.file:
                media_url = getattr(settings, 'MEDIA_URL', '/media/')
                file_url = f"{media_url}{msg.file.name}"

            # Safely handle is_read field
            is_read = getattr(msg, 'is_read', False)

            msg_list.append({
                "id": msg.id,
                "sender_id": str(msg.sender.id),
                "text": msg.text,
                "image": file_url if is_image else None,
                "file": file_url if not is_image else None,
                "timestamp": msg.timestamp.strftime("%B %d, %Y %I:%M %p"),
                "timestamp_raw": msg.timestamp.isoformat(),
                "is_read": is_read
            })

        return JsonResponse({"messages": msg_list}, status=200)
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        return JsonResponse({"messages": []}, status=200)

@login_required
def get_unread_count(request):
    """Count unread messages for the logged-in user"""
    try:
        unread_count = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
        
        logger.info(f"Unread count for user {request.user.id}: {unread_count}")
        return JsonResponse({"unread_count": unread_count}, status=200)
    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        return JsonResponse({"unread_count": 0}, status=200)

@login_required
def get_user_unread_count(request, user_id):
    """Count unread messages from a specific user"""
    try:
        user = User.objects.get(id=user_id)
    except (User.DoesNotExist, ValueError):
        return JsonResponse({"unread_count": 0}, status=200)
    
    try:
        unread_count = Message.objects.filter(
            sender=user,
            receiver=request.user,
            is_read=False
        ).count()
        
        logger.info(f"Unread count for user {user_id}: {unread_count}")
        return JsonResponse({"unread_count": unread_count}, status=200)
    except Exception as e:
        logger.error(f"Error checking user unread count: {str(e)}")
        return JsonResponse({"unread_count": 0}, status=200)

@login_required
def mark_messages_read(request, receiver_id):
    """Mark all messages from a specific user as read"""
    try:
        receiver = User.objects.get(id=receiver_id)
    except (User.DoesNotExist, ValueError):
        return JsonResponse({"status": "success", "updated": 0}, status=200)

    try:
        updated = Message.objects.filter(
            sender=receiver,
            receiver=request.user,
            is_read=False
        ).update(is_read=True)
        
        logger.info(f"Marked {updated} messages as read for user {request.user.id}")
        return JsonResponse({"status": "success", "updated": updated}, status=200)
    except Exception as e:
        logger.error(f"Error marking messages as read: {str(e)}")
        return JsonResponse({"status": "error", "updated": 0}, status=200)

@login_required
def user_settings(request):
    """Settings page view"""
    user = request.user
    
    logger.info(f"User {user.id} accessed settings page")
    
    return render(request, "settings.html", {"user": user})

@login_required
def profile_settings(request):
    if request.method == "POST":
        fullname = request.POST.get('fullname', '').strip()
        id_number = request.POST.get('id_number', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        
        errors = []
        
        if not fullname:
            errors.append("Full Name is required.")
        elif len(fullname) < 3:
            errors.append("Full Name must be at least 3 characters.")
        
        if not id_number:
            errors.append("ID Number is required.")
        
        if not email:
            errors.append("Email is required.")
        else:
            try:
                validate_email(email)
            except ValidationError:
                errors.append("Please enter a valid email address.")
        
        if phone and len(phone) < 11:
            errors.append("Phone number must be at least 11 digits.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('profile_settings')
        
        request.user.fullname = fullname
        request.user.id_number = id_number
        request.user.email = email
        request.user.number = phone
        
        request.user.save()
        
        messages.success(request, "Profile updated successfully!")
        return redirect('profile_settings')
    
    return render(request, "profile_settings.html", {"user": request.user})

@login_required
def security_settings(request):
    if request.method == "POST":
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        errors = []
        
        # Validate current password
        if not request.user.check_password(current_password):
            errors.append("Current password is incorrect.")
        
        # Validate new password length
        if len(new_password) < 8:
            errors.append("New password must be at least 8 characters long.")
        
        # Validate password match
        if new_password != confirm_password:
            errors.append("New passwords do not match.")
        
        # Check password strength
        if len(new_password) >= 8:
            has_upper = any(c.isupper() for c in new_password)
            has_lower = any(c.islower() for c in new_password)
            has_digit = any(c.isdigit() for c in new_password)
            has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in new_password)
            
            if not (has_upper and has_lower and has_digit and has_special):
                errors.append("Password must contain uppercase, lowercase, number, and special character.")
        
        # If there are errors, show them
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('security_settings')
        
        # If all validations pass, update password
        try:
            request.user.set_password(new_password)
            request.user.save()
            
            # Keep the user logged in after password change
            update_session_auth_hash(request, request.user)
            
            messages.success(request, "Password changed successfully!")
            return redirect('security_settings')
            
        except Exception as e:
            messages.error(request, f"Error changing password: {str(e)}")
            return redirect('security_settings')
    
    # GET request - show the form
    return render(request, "security_settings.html", {"user": request.user})

@login_required
def manage_homepage(request):
    return render(request, "manage_homepage.html", {"user": request.user})

# users/views.py - Fix template name
def edit_hp_contents(request):
    homepage_contents = HomepageContent.objects.filter(is_active=True).order_by('order')
    return render(request, 'edit_hp_contents.html', {'homepage_contents': homepage_contents})  # No 'admin/' folder needed

def homepage(request):
    homepage_contents = HomepageContent.objects.filter(is_active=True).order_by('order')
    return render(request, 'landingpage.html', {'homepage_contents': homepage_contents})

from django.views.decorators.http import require_http_methods

@require_http_methods(["POST"])
def update_homepage_content(request):
    section_name = request.POST.get('section_name')
    try:
        section = get_object_or_404(HomepageContent, section_name=section_name)
        
        section.title = request.POST.get('title', section.title)
        section.content = request.POST.get('content', section.content)
        
        if 'image' in request.FILES:
            section.image = request.FILES['image']
        
        section.save()
        
        return JsonResponse({'success': True, 'message': 'Section updated successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
from .models import CustomUser

@login_required
def user_management(request):
    # START with ALL users
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Update current user activity - ✅ ADDED is_logged_in
    request.user.is_logged_in = True
    request.user.last_activity = timezone.now()
    request.user.save(update_fields=['is_logged_in', 'last_activity'])
    
    # GET FILTER VALUES
    search_query = request.GET.get('search', '').strip()
    position_filter = request.GET.get('position', '')
    status_filter = request.GET.get('status', '')
    
    # 1️⃣ SEARCH FILTER
    if search_query:
        users = users.filter(
            Q(fullname__icontains=search_query) |
            Q(id_number__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    # 2️⃣ POSITION FILTER
    if position_filter == 'Admin':
        users = users.filter(position='Admin')
    elif position_filter == 'Personnel':
        users = users.filter(position='Personnel')
    
    # 🔥 3️⃣ STATUS FILTER - UPDATED for is_logged_in
    if status_filter == 'active':
        users = users.filter(is_logged_in=True)  # ✅ Currently logged in
    elif status_filter == 'inactive':
        users = users.filter(is_logged_in=False, last_activity__isnull=False)
    elif status_filter == 'never':
        users = users.filter(last_activity__isnull=True)
    
    # Pagination
    paginator = Paginator(users, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    # 🔥 STATS - UPDATED for is_logged_in
    stats = {
        'total': CustomUser.objects.count(),
        'active': CustomUser.objects.filter(is_logged_in=True).count(),  # ✅ Currently logged in
        'inactive': CustomUser.objects.filter(is_logged_in=False, last_activity__isnull=False).count(),
        'never_active': CustomUser.objects.filter(last_activity__isnull=True).count(),
    }
    
    print(f"STATS DEBUG: Active={stats['active']}, Inactive={stats['inactive']}, Never={stats['never_active']}, Total={stats['total']}")
    
    # Table data - 🔥 NEW LOGIC: Active until PROPER logout
    users_with_status = []
    now = timezone.now()
    for user in page_obj:
        user_data = {
            'id': user.id,
            'id_number': user.id_number,
            'fullname': user.fullname,
            'email': user.email,
            'number': user.number,
            'position': user.position,
            'last_activity': getattr(user, 'last_activity', None),
        }
        
        # ✅ PERFECT LOGIC: Active FOREVER until logout!
        if user_data['last_activity']:
            if user.is_logged_in:  # ✅ Still logged in = Active FOREVER
                user_data['activity_status'] = "Active Now"
            else:  # ✅ Properly logged out - count time
                if hasattr(user, 'last_logout_time') and user.last_logout_time:
                    time_diff = now - user.last_logout_time
                else:
                    time_diff = now - user_data['last_activity']
                
                minutes = time_diff.total_seconds() / 60
                if minutes < 60:
                    user_data['activity_status'] = f"Offline ({int(minutes)} mins)"
                elif minutes < 1440:
                    hours = int(minutes / 60)
                    user_data['activity_status'] = f"Offline ({hours} hrs)"
                else:
                    days = int(minutes / 1440)
                    user_data['activity_status'] = f"Offline ({days} days)"
        else:
            user_data['activity_status'] = "Never Active"
        
        users_with_status.append(user_data)
    
    page_obj.object_list = users_with_status
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'search_query': search_query,
        'position_filter': position_filter,
        'status_filter': status_filter,
    }
    return render(request, 'user_management.html', context)

from django.contrib.auth.hashers import make_password

@login_required
def add_user(request):
    if request.method == 'POST':
        id_number = request.POST.get('id_number')
        fullname = request.POST.get('fullname')
        email = request.POST.get('email')
        number = request.POST.get('number', '')
        position = request.POST.get('position')
        
        # Default passwords
        if position == 'Admin':
            password = '@Admin01'
        elif position == 'Personnel':
            password = '@Personnel01'
        else:
            password = '@User01'
        
        try:
            # Check duplicates
            if CustomUser.objects.filter(id_number=id_number).exists():
                messages.error(request, 'ID Number already exists!')
                return redirect('user_management')
            
            if CustomUser.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists!')
                return redirect('user_management')
            
            # Create user
            user = CustomUser(
                id_number=id_number,
                fullname=fullname,
                email=email,
                number=number,
                position=position,
                password=make_password(password)
            )
            user.save()
            
            # ✅ Success with HTML in message
            messages.success(request, 'User successfully created')
            return redirect('user_management')
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('user_management')
    
    return redirect('user_management')

def personnel_activity(request, id_number):
    """
    FLEXIBLE Personnel Activity View - Works with ANY UserActivity actions
    """
    personnel = get_object_or_404(CustomUser, id_number=id_number)
    
    # 🔥 FLEXIBLE FILTERING - Show ALL activities
    activities = personnel.activities.all().order_by('-created_at')[:100]
    
    # 🔥 SMART STATS - Auto-detect common actions
    stats = {
        'total_activities': personnel.activities.count(),
        'recent_30days': personnel.activities.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=30)
        ).count(),
    }
    
    # 🔥 AUTO-CATEGORIZE by action type
    action_stats = {}
    for activity in personnel.activities.all()[:50]:  # Sample for stats
        action = activity.action
        action_stats[action] = action_stats.get(action, 0) + 1
    
    # 🔥 HIGHLIGHT beneficiary-related activities
    beneficiary_actions = [a for a in activities if 'BENEFICIARY' in a.action.upper()]
    
    context = {
        'personnel': personnel,
        'activities': activities,
        'stats': stats,
        'action_stats': action_stats,
        'beneficiary_actions': beneficiary_actions,
        'total_actions': len(action_stats),
    }
    return render(request, 'personnel_activity.html', context)

@login_required
def delete_user(request, id_number):
    # Prevent self-deletion
    if id_number == request.user.id_number:
        messages.error(request, 'Cannot delete your own account!')
        return redirect('user_management')
    
    try:
        # Get user (404 if not found)
        user = get_object_or_404(CustomUser, id_number=id_number)
        
        # Double-check not current user
        if user.id == request.user.id:
            messages.error(request, 'Cannot delete your own account!')
            return redirect('user_management')
        
        # Delete user
        username = user.fullname
        user.delete()
        
        messages.success(request, f'User "{username}" deleted successfully')
        return redirect('user_management')
        
    except Exception as e:
        messages.error(request, 'Error deleting user')
        return redirect('user_management')
    
@login_required
def user_activities(request, id_number):
    user = get_object_or_404(CustomUser, id_number=id_number)
    activities = user.activities.all()[:100]  # Last 100
    
    context = {'user': user, 'activities': activities}
    return render(request, 'user_activity.html', context)

from django.conf import settings as django_settings  # ✅ Fix settings conflict

def forgot_password(request):
    if request.method == 'POST':
        id_number = request.POST.get('id_number')
        email = request.POST.get('email').lower().strip()
        
        try:
            user = CustomUser.objects.get(id_number=id_number)
            
            # Wrong email? Send security warning
            if user.email != email:
                print(f"⚠️ SECURITY ALERT: {user.email} vs {email}")
                
                warning_html = render_to_string('security_warning_email.html', {
                    'user': user,
                    'suspicious_email': email,
                    'domain': get_current_site(request).domain,
                    'now': timezone.now(),  # ✅ FIX: Add current time
                })
                
                send_mail(
                    subject='⚠️ Security Alert: Suspicious Login Attempt',
                    message='Security alert for your account. Please check your email for details.',
                    # ✅ FIX: Add html_message parameter!
                    html_message=warning_html,
                    from_email=django_settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
                print(f"📧 WARNING SENT to {user.email}")
                
                messages.error(request, 'Invalid credentials.')
                return render(request, 'forgot_password.html')
            
            # ✅ Correct credentials - Send OTP
            otp_code = OTPCode.create_otp(user)
            
            otp_html = render_to_string('forgot_password_email.html', {
                'user': user,
                'otp': otp_code,
                'domain': get_current_site(request).domain,
            })
            
            send_mail(
                subject='Your Password Reset OTP',
                message=f'Your OTP is: {otp_code}',  # Plain text fallback
                # ✅ FIX: HTML version!
                html_message=otp_html,
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            request.session['reset_id_number'] = id_number
            request.session['reset_email'] = email
            messages.success(request, 'OTP sent to your email!')
            return redirect('verify_otp')
            
        except CustomUser.DoesNotExist:
            messages.error(request, 'Invalid ID Number or Email.')
    
    return render(request, 'forgot_password.html')

def verify_otp(request):
    if 'reset_id_number' not in request.session:
        return redirect('forgot_password')
    
    if request.method == 'POST':
        otp = request.POST.get('otp')
        
        try:
            id_number = request.session['reset_id_number']
            user = CustomUser.objects.get(id_number=id_number)
            
            otp_obj = OTPCode.objects.filter(
                user=user, used=False, expires_at__gt=timezone.now()
            ).last()
            
            if otp_obj and constant_time_compare(otp, otp_obj.code):
                request.session['reset_user_id'] = user.id
                messages.success(request, 'OTP verified successfully!')
                return redirect('reset_password')
            else:
                messages.error(request, 'Invalid or expired OTP!')
                
        except CustomUser.DoesNotExist:
            messages.error(request, 'Session expired. Start over.')
    
    return render(request, 'verify_otp.html')

def reset_password(request):
    if 'reset_user_id' not in request.session:
        return redirect('forgot_password')
    
    if request.method == 'POST':
        user_id = request.session['reset_user_id']
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match!')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters!')
        else:
            try:
                user = CustomUser.objects.get(id=user_id)
                user.set_password(new_password)
                user.save()
                
                # Mark OTP as used
                OTPCode.objects.filter(user=user, used=False).update(used=True)
                
                # Clear session
                del request.session['reset_user_id']
                del request.session['reset_id_number']
                del request.session['reset_email']
                
                messages.success(request, 'Password reset successfully! Please login.')
                return redirect('login')
                
            except CustomUser.DoesNotExist:
                messages.error(request, 'Session expired!')
    
    return render(request, 'reset_password.html')

