from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class CustomUserManager(BaseUserManager):
    def create_user(self, id_number, fullname, email, number, position, password=None):
        if not id_number:
            raise ValueError("Users must have an ID Number")

        email = self.normalize_email(email)

        user = self.model(
            id_number=id_number,
            fullname=fullname,
            email=email,
            number=number,
            position=position
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, id_number, fullname, email, number, position, password):
        user = self.create_user(
            id_number=id_number,
            fullname=fullname,
            email=email,
            number=number,
            position=position,
            password=password
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser, PermissionsMixin):

    POSITION_CHOICES = (
        ('Admin', 'Admin'),
        ('Personnel', 'Personnel'),
    )

    id_number = models.CharField(max_length=20, unique=True)
    fullname = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    number = models.CharField(max_length=15)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES)

    # status fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    is_logged_in = models.BooleanField(default=False)  # Key field!
    last_logout_time = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'id_number'
    REQUIRED_FIELDS = ['fullname', 'email', 'number', 'position']

    def __str__(self):
        return self.fullname
    
    @property
    def activity_status(self):
        """
        Returns user status:
        - 'Never Active' if never logged in
        - 'Active Now' if last_activity < 5 mins
        - 'Inactive (x mins ago)' if < 24 hours
        - 'Inactive (x days ago)' if > 24 hours
        """
        if not self.last_activity:
            return "Never Active"

        diff = timezone.now() - self.last_activity

        if diff < timedelta(minutes=5):
            return "Active Now"
        elif diff < timedelta(days=1):
            minutes = diff.seconds // 60
            return f"Inactive ({minutes} mins ago)"
        else:
            return f"Inactive ({diff.days} days ago)"
        
class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sent_messages",
        on_delete=models.CASCADE
    )

    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="received_messages",
        on_delete=models.CASCADE
    )

    text = models.TextField(blank=True)
    # FIX: Change upload_to from "chat_files/" to "messages/"
    file = models.FileField(upload_to="messages/", blank=True, null=True)
    # REMOVED: Separate image field - we handle images through the file field
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    edited = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.timestamp})"
    
    
class HomepageHeader(models.Model):
    """Homepage Header Content"""
    logo = models.ImageField(upload_to='homepage/logo/', null=True, blank=True)
    title = models.CharField(max_length=200, default="Self-Employment Assistance")
    subtitle = models.CharField(max_length=300, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Homepage Header"
        verbose_name_plural = "Homepage Header"

class HomepageContent(models.Model):
    """Homepage Main Content Sections"""
    SECTION_CHOICES = [
        ('mensahe_ng_pinuno', 'Mensahe ng Pinuno ng PSWDO'),
        ('department_head', 'Department Head'),
        ('vision', 'Vision'),
        ('mission', 'Mission'),
        ('mandates', 'Mandates'),
        ('functions', 'Functions'),
        ('programs_and_services', 'Programs and Services'),
        ('achievements', 'Achievements'),
        ('contact_information', 'Contact Information'),
    ]
    
    section_name = models.CharField(max_length=100, choices=SECTION_CHOICES, unique=True)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='homepage/content/', null=True, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Homepage Content"
        verbose_name_plural = "Homepage Content"
    
    def __str__(self):
        return self.title

class HomepageFooter(models.Model):
    """Homepage Footer Content"""
    logo = models.ImageField(upload_to='homepage/footer/logo/', null=True, blank=True)
    contact_info = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return "Homepage Footer"
    
    class Meta:
        verbose_name = "Homepage Footer"
        verbose_name_plural = "Homepage Footer"
        
class UserActivity(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} - {self.action}"
    
# models.py - ADD
import secrets
from django.utils.crypto import constant_time_compare

class OTPCode(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    def is_valid(self):
        return not self.used and timezone.now() < self.expires_at
    
    @classmethod
    def create_otp(cls, user):
        code = ''.join(secrets.choice('0123456789') for _ in range(6))
        otp = cls.objects.create(
            user=user,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=5)
        )
        return otp.code