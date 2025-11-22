from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import secrets
from datetime import timedelta

class CustomUser(AbstractUser):
    """مدل کاربر سفارشی - تسک ۳۰۱"""
    phone = models.CharField(max_length=15, blank=True, verbose_name='تلفن')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='تصویر پروفایل')
    email_verified = models.BooleanField(default=False, verbose_name='ایمیل تأیید شده')
    
    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'
        db_table = 'users_customuser'
    
    def __str__(self):
        return f"{self.username} ({self.email})"

class Company(models.Model):
    """مدل شرکت - تسک ۳۰۶ - ✅ تقریباً کامل"""
    
    COMPANY_TYPES = [
        ('MANUFACTURING', 'تولیدی'),
        ('TRADING', 'بازرگانی'),
        ('SERVICE', 'خدماتی'),
        ('CONSTRUCTION', 'پیمانکاری'),
        ('HOLDING', 'هلدینگ'),
        ('OTHER', 'سایر'),
    ]
    
    CURRENCY_CHOICES = [
        ('IRR', 'ریال'),
        ('USD', 'دلار'),
        ('EUR', 'یورو'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='نام شرکت')
    economic_code = models.CharField(max_length=20, verbose_name='کد اقتصادی', unique=True)
    national_code = models.CharField(max_length=20, verbose_name='شناسه ملی', unique=True)
    company_type = models.CharField(
        max_length=20, 
        choices=COMPANY_TYPES, 
        verbose_name='نوع شرکت',
        default='SERVICE'
    )
    
    # اطلاعات تماس
    address = models.TextField(verbose_name='آدرس', blank=True)
    phone = models.CharField(max_length=15, verbose_name='تلفن', blank=True)
    website = models.URLField(blank=True, verbose_name='وبسایت')
    email = models.EmailField(blank=True, verbose_name='ایمیل')
    
    # اطلاعات مالی
    fiscal_year_start = models.DateField(
        default=timezone.now().replace(month=1, day=1),
        verbose_name='شروع سال مالی'
    )
    fiscal_year_end = models.DateField(
        default=timezone.now().replace(month=12, day=29),
        verbose_name='پایان سال مالی'
    )
    currency = models.CharField(
        max_length=10, 
        default='IRR',
        verbose_name='واحد پول',
        choices=CURRENCY_CHOICES
    )
    
    logo = models.ImageField(
        upload_to='company_logos/', 
        null=True, 
        blank=True, 
        verbose_name='لوگو'
    )
    description = models.TextField(blank=True, verbose_name='توضیحات')
    
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_verified = models.BooleanField(default=False, verbose_name='تأیید شده')
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='created_companies',
        verbose_name='ایجاد شده توسط'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'شرکت'
        verbose_name_plural = 'شرکت‌ها'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['economic_code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_active_members_count(self):
        return self.user_roles.filter(is_active=True).count()
    
    def can_user_access(self, user):
        return self.user_roles.filter(user=user, is_active=True).exists()

class UserCompanyRole(models.Model):
    """مدل نقش کاربر در شرکت - تسک ۳۰۷ - 🔄 نیاز به تکمیل"""
    
    ROLE_CHOICES = [
        ('OWNER', 'مالک'),
        ('ADMIN', 'مدیر'),
        ('ACCOUNTANT', 'حسابدار'),
        ('AUDITOR', 'حسابرس'),
        ('VIEWER', 'مشاهده‌کننده'),
        ('DATA_ENTRY', 'تکمیل کننده داده'),
    ]
    
    PERMISSION_LEVELS = {
        'OWNER': 100,
        'ADMIN': 90,
        'ACCOUNTANT': 80,
        'AUDITOR': 70,
        'DATA_ENTRY': 60,
        'VIEWER': 50,
    }
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='company_roles',
        verbose_name='کاربر'
    )
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='user_roles',
        verbose_name='شرکت'
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        verbose_name='نقش'
    )
    
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_primary = models.BooleanField(default=False, verbose_name='شرکت اصلی')
    
    invited_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='sent_invitations',
        verbose_name='دعوت شده توسط'
    )
    invited_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ دعوت')  # اصلاح شده
    joined_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ پیوستن')
    
    # دسترسی‌ها
    can_manage_users = models.BooleanField(default=False, verbose_name='مدیریت کاربران')
    can_manage_financial_data = models.BooleanField(default=False, verbose_name='مدیریت داده مالی')
    can_view_reports = models.BooleanField(default=True, verbose_name='مشاهده گزارش‌ها')
    can_export_data = models.BooleanField(default=False, verbose_name='خروجی گرفتن')
    
    class Meta:
        verbose_name = 'نقش کاربر در شرکت'
        verbose_name_plural = 'نقش‌های کاربران در شرکت‌ها'
        unique_together = ['user', 'company']
        ordering = ['company', '-is_primary', 'role']
    
    def __str__(self):
        return f"{self.user.username} - {self.company.name} - {self.get_role_display()}"
    
    def save(self, *args, **kwargs):
        """اتوماتیک کردن دسترسی‌ها بر اساس نقش"""
        self._set_permissions_based_on_role()
        super().save(*args, **kwargs)
    
    def _set_permissions_based_on_role(self):
        """تنظیم دسترسی‌ها بر اساس نقش"""
        permission_map = {
            'OWNER': (True, True, True, True),
            'ADMIN': (True, True, True, True),
            'ACCOUNTANT': (False, True, True, True),
            'AUDITOR': (False, False, True, True),
            'DATA_ENTRY': (False, True, False, False),
            'VIEWER': (False, False, True, False),
        }
        
        perms = permission_map.get(self.role, (False, False, True, False))
        self.can_manage_users, self.can_manage_financial_data, self.can_view_reports, self.can_export_data = perms
    
    def get_permission_level(self):
        return self.PERMISSION_LEVELS.get(self.role, 0)
    
    def has_permission(self, required_level):
        return self.get_permission_level() >= required_level

class FinancialPeriod(models.Model):
    """مدل دوره مالی - تسک ۳۰۸"""
    
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='financial_periods',
        verbose_name='شرکت'
    )
    name = models.CharField(max_length=100, verbose_name='نام دوره')
    start_date = models.DateField(verbose_name='تاریخ شروع')
    end_date = models.DateField(verbose_name='تاریخ پایان')
    
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_closed = models.BooleanField(default=False, verbose_name='بسته شده')
    is_locked = models.BooleanField(default=False, verbose_name='قفل شده')
    
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        verbose_name='ایجاد شده توسط'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    class Meta:
        verbose_name = 'دوره مالی'
        verbose_name_plural = 'دوره‌های مالی'
        unique_together = ['company', 'name']
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"
    
    def is_current_period(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

class CompanyInvitation(models.Model):
    """مدل دعوتنامه شرکت - تسک ۳۱۰"""
    
    STATUS_CHOICES = [
        ('PENDING', 'در انتظار'),
        ('ACCEPTED', 'پذیرفته شده'),
        ('REJECTED', 'رد شده'),
        ('EXPIRED', 'منقضی شده'),
    ]
    
    email = models.EmailField(verbose_name='ایمیل دعوت شده')
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='invitations',
        verbose_name='شرکت'
    )
    role = models.CharField(
        max_length=20, 
        choices=UserCompanyRole.ROLE_CHOICES, 
        verbose_name='نقش'
    )
    
    invited_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='company_invitations',
        verbose_name='دعوت کننده'
    )
    token = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name='توکن دعوت'
    )
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        verbose_name='وضعیت'
    )
    expires_at = models.DateTimeField(verbose_name='تاریخ انقضا')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ پاسخ')
    
    class Meta:
        verbose_name = 'دعوتنامه شرکت'
        verbose_name_plural = 'دعوتنامه‌های شرکت'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['status']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.email} - {self.company.name} - {self.get_role_display()}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def can_be_accepted(self):
        return self.status == 'PENDING' and not self.is_expired()
    
    def mark_as_accepted(self):
        self.status = 'ACCEPTED'
        self.responded_at = timezone.now()
        self.save()
    
    def mark_as_rejected(self):
        self.status = 'REJECTED'
        self.responded_at = timezone.now()
        self.save()
    
    @classmethod
    def create_invitation(cls, email, company, role, invited_by, days_valid=7):
        """ایجاد دعوتنامه جدید"""
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(days=days_valid)
        
        return cls.objects.create(
            email=email,
            company=company,
            role=role,
            invited_by=invited_by,
            token=token,
            expires_at=expires_at
        )

class UserSession(models.Model):
    """مدل برای مدیریت session کاربر - تسک ۳۱۶"""
    user = models.OneToOneField(  # تغییر به OneToOneField
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='user_session'
    )
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    financial_period = models.ForeignKey(
        FinancialPeriod, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'سشن کاربر'
        verbose_name_plural = 'سشن‌های کاربران'
    
    def __str__(self):
        return f"{self.user.username} - {self.company.name if self.company else 'No Company'}"