from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json

User = get_user_model()


class SecurityLevel(models.TextChoices):
    """سطوح امنیتی"""
    LOW = 'LOW', 'کم'
    MEDIUM = 'MEDIUM', 'متوسط'
    HIGH = 'HIGH', 'بالا'
    CRITICAL = 'CRITICAL', 'بحرانی'


class SecurityEventType(models.TextChoices):
    """انواع رویدادهای امنیتی"""
    LOGIN_SUCCESS = 'LOGIN_SUCCESS', 'ورود موفق'
    LOGIN_FAILED = 'LOGIN_FAILED', 'ورود ناموفق'
    LOGOUT = 'LOGOUT', 'خروج'
    PASSWORD_CHANGE = 'PASSWORD_CHANGE', 'تغییر رمز عبور'
    ACCESS_DENIED = 'ACCESS_DENIED', 'دسترسی رد شد'
    DATA_ACCESS = 'DATA_ACCESS', 'دسترسی به داده'
    DATA_MODIFICATION = 'DATA_MODIFICATION', 'تغییر داده'
    ENCRYPTION = 'ENCRYPTION', 'رمزنگاری'
    DECRYPTION = 'DECRYPTION', 'رمزگشایی'
    SECURITY_ALERT = 'SECURITY_ALERT', 'هشدار امنیتی'
    SUSPICIOUS_ACTIVITY = 'SUSPICIOUS_ACTIVITY', 'فعالیت مشکوک'


class EncryptionAlgorithm(models.TextChoices):
    """الگوریتم‌های رمزنگاری"""
    AES_256 = 'AES_256', 'AES-256'
    RSA_2048 = 'RSA_2048', 'RSA-2048'
    RSA_4096 = 'RSA_4096', 'RSA-4096'
    CHACHA20 = 'CHACHA20', 'ChaCha20'


class SecurityPolicy(models.Model):
    """مدل برای ذخیره سیاست‌های امنیتی"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy_name = models.CharField(max_length=100, unique=True, help_text='نام سیاست')
    policy_description = models.TextField(help_text='شرح سیاست')
    
    # تنظیمات رمزنگاری
    default_encryption_algorithm = models.CharField(
        max_length=20,
        choices=EncryptionAlgorithm.choices,
        default=EncryptionAlgorithm.AES_256,
        help_text='الگوریتم رمزنگاری پیش‌فرض'
    )
    key_rotation_days = models.PositiveIntegerField(
        default=90,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        help_text='دوره گردش کلید (روز)'
    )
    
    # تنظیمات احراز هویت
    max_login_attempts = models.PositiveIntegerField(
        default=5,
        help_text='حداکثر تعداد تلاش برای ورود'
    )
    session_timeout_minutes = models.PositiveIntegerField(
        default=30,
        help_text='زمان انقضای جلسه (دقیقه)'
    )
    password_min_length = models.PositiveIntegerField(
        default=8,
        help_text='حداقل طول رمز عبور'
    )
    password_complexity = models.BooleanField(
        default=True,
        help_text='اجباری بودن پیچیدگی رمز عبور'
    )
    
    # تنظیمات لاگ‌گیری
    enable_security_audit = models.BooleanField(
        default=True,
        help_text='فعال بودن ممیزی امنیتی'
    )
    audit_retention_days = models.PositiveIntegerField(
        default=365,
        help_text='دوره نگهداری لاگ‌ها (روز)'
    )
    
    # فعال/غیرفعال
    is_active = models.BooleanField(default=True, help_text='فعال بودن سیاست')
    
    # متادیتا
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'سیاست امنیتی'
        verbose_name_plural = 'سیاست‌های امنیتی'
        ordering = ['-is_active', 'policy_name']
    
    def __str__(self):
        return self.policy_name


class EncryptionKey(models.Model):
    """مدل برای مدیریت کلیدهای رمزنگاری"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key_name = models.CharField(max_length=100, unique=True, help_text='نام کلید')
    key_description = models.TextField(help_text='شرح کلید')
    
    # اطلاعات کلید
    algorithm = models.CharField(
        max_length=20,
        choices=EncryptionAlgorithm.choices,
        help_text='الگوریتم رمزنگاری'
    )
    key_version = models.PositiveIntegerField(default=1, help_text='نسخه کلید')
    key_data = models.BinaryField(help_text='داده کلید (رمز شده)')
    key_checksum = models.CharField(max_length=64, help_text='چکسام کلید')
    
    # وضعیت کلید
    is_active = models.BooleanField(default=True, help_text='فعال بودن کلید')
    is_primary = models.BooleanField(default=False, help_text='کلید اصلی')
    
    # زمان‌ها
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(default=timezone.now, help_text='زمان فعال‌سازی')
    expires_at = models.DateTimeField(help_text='زمان انقضا')
    rotated_at = models.DateTimeField(blank=True, null=True, help_text='زمان آخرین گردش')
    
    # متادیتا
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_encryption_keys'
    )
    
    class Meta:
        verbose_name = 'کلید رمزنگاری'
        verbose_name_plural = 'کلیدهای رمزنگاری'
        ordering = ['-is_primary', '-is_active', '-activated_at']
        unique_together = ['key_name', 'key_version']
    
    def __str__(self):
        return f"{self.key_name} v{self.key_version}"
    
    def mark_rotated(self):
        """علامت‌گذاری کلید به عنوان گردش شده"""
        self.is_primary = False
        self.rotated_at = timezone.now()
        self.save()


class SecurityAuditLog(models.Model):
    """مدل برای ذخیره لاگ‌های امنیتی"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # اطلاعات رویداد
    event_type = models.CharField(
        max_length=20,
        choices=SecurityEventType.choices,
        help_text='نوع رویداد'
    )
    event_description = models.TextField(help_text='شرح رویداد')
    security_level = models.CharField(
        max_length=20,
        choices=SecurityLevel.choices,
        default=SecurityLevel.MEDIUM,
        help_text='سطح امنیتی رویداد'
    )
    
    # اطلاعات کاربر و جلسه
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='security_audit_logs'
    )
    session_id = models.CharField(max_length=100, blank=True, null=True, help_text='شناسه جلسه')
    
    # اطلاعات درخواست
    request_path = models.CharField(max_length=500, blank=True, null=True, help_text='مسیر درخواست')
    request_method = models.CharField(max_length=10, blank=True, null=True, help_text='متد درخواست')
    user_agent = models.TextField(blank=True, null=True, help_text='User Agent کاربر')
    ip_address = models.GenericIPAddressField(blank=True, null=True, help_text='آدرس IP')
    
    # داده‌های اضافی
    additional_data = models.JSONField(default=dict, blank=True, help_text='داده‌های اضافی رویداد')
    
    # نتیجه رویداد
    success = models.BooleanField(default=True, help_text='موفقیت رویداد')
    error_message = models.TextField(blank=True, null=True, help_text='پیام خطا')
    
    # متادیتا
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'لاگ امنیتی'
        verbose_name_plural = 'لاگ‌های امنیتی'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.user.username if self.user else 'ناشناس'} - {self.created_at}"


class DataAccessLog(models.Model):
    """مدل برای ذخیره لاگ‌های دسترسی به داده"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # اطلاعات دسترسی
    access_type = models.CharField(
        max_length=20,
        choices=[
            ('READ', 'خواندن'),
            ('WRITE', 'نوشتن'),
            ('UPDATE', 'به‌روزرسانی'),
            ('DELETE', 'حذف'),
            ('EXPORT', 'خروجی'),
        ],
        help_text='نوع دسترسی'
    )
    data_type = models.CharField(max_length=100, help_text='نوع داده')
    data_id = models.CharField(max_length=100, blank=True, null=True, help_text='شناسه داده')
    data_summary = models.TextField(blank=True, null=True, help_text='خلاصه داده')
    
    # اطلاعات کاربر
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='data_access_logs'
    )
    company_id = models.IntegerField(blank=True, null=True, help_text='شناسه شرکت')
    period_id = models.IntegerField(blank=True, null=True, help_text='شناسه دوره مالی')
    
    # اطلاعات درخواست
    request_path = models.CharField(max_length=500, blank=True, null=True, help_text='مسیر درخواست')
    ip_address = models.GenericIPAddressField(blank=True, null=True, help_text='آدرس IP')
    
    # داده‌های اضافی
    additional_data = models.JSONField(default=dict, blank=True, help_text='داده‌های اضافی')
    
    # متادیتا
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'لاگ دسترسی به داده'
        verbose_name_plural = 'لاگ‌های دسترسی به داده'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'data_type', 'created_at']),
            models.Index(fields=['company_id', 'period_id', 'created_at']),
            models.Index(fields=['access_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_access_type_display()} - {self.data_type} - {self.user.username if self.user else 'ناشناس'}"


class SuspiciousActivity(models.Model):
    """مدل برای ذخیره فعالیت‌های مشکوک"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # اطلاعات فعالیت
    activity_type = models.CharField(max_length=100, help_text='نوع فعالیت مشکوک')
    activity_description = models.TextField(help_text='شرح فعالیت مشکوک')
    severity = models.CharField(
        max_length=20,
        choices=SecurityLevel.choices,
        default=SecurityLevel.MEDIUM,
        help_text='شدت فعالیت مشکوک'
    )
    
    # اطلاعات کاربر
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='suspicious_activities'
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True, help_text='آدرس IP')
    
    # اطلاعات تشخیص
    detection_method = models.CharField(max_length=100, help_text='روش تشخیص')
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text='امتیاز اطمینان تشخیص'
    )
    
    # وضعیت
    is_investigated = models.BooleanField(default=False, help_text='بررسی شده')
    investigation_notes = models.TextField(blank=True, null=True, help_text='یادداشت‌های بررسی')
    investigated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='investigated_activities'
    )
    investigated_at = models.DateTimeField(blank=True, null=True, help_text='زمان بررسی')
    
    # داده‌های اضافی
    additional_data = models.JSONField(default=dict, blank=True, help_text='داده‌های اضافی')
    
    # متادیتا
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'فعالیت مشکوک'
        verbose_name_plural = 'فعالیت‌های مشکوک'
        ordering = ['-severity', '-created_at']
    
    def __str__(self):
        return f"{self.activity_type} - {self.get_severity_display()} - {self.created_at}"
    
    def mark_investigated(self, notes=None, investigator=None):
        """علامت‌گذاری فعالیت به عنوان بررسی شده"""
        self.is_investigated = True
        self.investigated_at = timezone.now()
        if notes:
            self.investigation_notes = notes
        if investigator:
            self.investigated_by = investigator
        self.save()


class SecurityAlertRule(models.Model):
    """مدل برای قوانین هشدار امنیتی"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule_name = models.CharField(max_length=100, unique=True, help_text='نام قانون هشدار')
    rule_description = models.TextField(help_text='شرح قانون هشدار')
    
    # شرایط هشدار
    event_type_filter = models.CharField(
        max_length=20,
        choices=SecurityEventType.choices,
        blank=True,
        null=True,
        help_text='فیلتر نوع رویداد (اختیاری)'
    )
    security_level_threshold = models.CharField(
        max_length=20,
        choices=SecurityLevel.choices,
        default=SecurityLevel.HIGH,
        help_text='آستانه سطح امنیتی'
    )
    
    # شرایط زمانی
    time_window_minutes = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
        help_text='بازه زمانی بر حسب دقیقه'
    )
    event_count_threshold = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1)],
        help_text='آستانه تعداد رویداد'
    )
    
    # تنظیمات هشدار
    alert_channel = models.CharField(
        max_length=50,
        choices=[
            ('EMAIL', 'ایمیل'),
            ('DASHBOARD', 'داشبورد'),
            ('SLACK', 'اسلک'),
            ('TELEGRAM', 'تلگرام'),
        ],
        default='DASHBOARD',
        help_text='کانال هشدار'
    )
    recipients = models.TextField(
        blank=True, 
        null=True, 
        help_text='لیست دریافت‌کنندگان (جدا شده با کاما)'
    )
    
    # فعال/غیرفعال
    is_active = models.BooleanField(default=True, help_text='فعال بودن قانون')
    
    # آمار
    trigger_count = models.PositiveIntegerField(default=0, help_text='تعداد فعال‌سازی‌ها')
    last_triggered = models.DateTimeField(blank=True, null=True, help_text='آخرین فعال‌سازی')
    
    # متادیتا
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'قانون هشدار امنیتی'
        verbose_name_plural = 'قوانین هشدار امنیتی'
        ordering = ['-is_active', '-trigger_count']
    
    def __str__(self):
        return self.rule_name
    
    def increment_trigger(self):
        """افزایش تعداد فعال‌سازی قانون"""
        self.trigger_count += 1
        self.last_triggered = timezone.now()
        self.save()
