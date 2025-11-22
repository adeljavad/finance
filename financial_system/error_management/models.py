from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()


class ErrorSeverity(models.TextChoices):
    """سطوح شدت خطا"""
    LOW = 'LOW', 'کم'
    MEDIUM = 'MEDIUM', 'متوسط'
    HIGH = 'HIGH', 'بالا'
    CRITICAL = 'CRITICAL', 'بحرانی'


class ErrorStatus(models.TextChoices):
    """وضعیت خطا"""
    NEW = 'NEW', 'جدید'
    IN_PROGRESS = 'IN_PROGRESS', 'در حال بررسی'
    RESOLVED = 'RESOLVED', 'حل شده'
    IGNORED = 'IGNORED', 'نادیده گرفته شده'


class ErrorCategory(models.TextChoices):
    """دسته‌بندی خطاها"""
    DATABASE = 'DATABASE', 'خطای پایگاه داده'
    VALIDATION = 'VALIDATION', 'خطای اعتبارسنجی'
    INTEGRATION = 'INTEGRATION', 'خطای یکپارچه‌سازی'
    SECURITY = 'SECURITY', 'خطای امنیتی'
    PERFORMANCE = 'PERFORMANCE', 'خطای عملکردی'
    AI_SERVICE = 'AI_SERVICE', 'خطای سرویس هوش مصنوعی'
    FILE_PROCESSING = 'FILE_PROCESSING', 'خطای پردازش فایل'
    USER_INPUT = 'USER_INPUT', 'خطای ورودی کاربر'
    SYSTEM = 'SYSTEM', 'خطای سیستم'
    OTHER = 'OTHER', 'سایر'


class SystemError(models.Model):
    """مدل برای ذخیره خطاهای سیستم"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    error_code = models.CharField(max_length=50, unique=True, help_text='کد یکتای خطا')
    title = models.CharField(max_length=255, help_text='عنوان خطا')
    description = models.TextField(help_text='شرح کامل خطا')
    stack_trace = models.TextField(blank=True, null=True, help_text='ردیابی استک خطا')
    
    # اطلاعات خطا
    severity = models.CharField(
        max_length=20,
        choices=ErrorSeverity.choices,
        default=ErrorSeverity.MEDIUM,
        help_text='شدت خطا'
    )
    category = models.CharField(
        max_length=20,
        choices=ErrorCategory.choices,
        default=ErrorCategory.OTHER,
        help_text='دسته‌بندی خطا'
    )
    status = models.CharField(
        max_length=20,
        choices=ErrorStatus.choices,
        default=ErrorStatus.NEW,
        help_text='وضعیت خطا'
    )
    
    # اطلاعات فنی
    module = models.CharField(max_length=100, help_text='ماژول یا کامپوننت خطا')
    function_name = models.CharField(max_length=100, help_text='نام تابع یا متد خطا')
    line_number = models.IntegerField(blank=True, null=True, help_text='شماره خط کد')
    
    # اطلاعات کاربر و جلسه
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='system_errors'
    )
    company_id = models.IntegerField(blank=True, null=True, help_text='شناسه شرکت')
    period_id = models.IntegerField(blank=True, null=True, help_text='شناسه دوره مالی')
    session_id = models.CharField(max_length=100, blank=True, null=True, help_text='شناسه جلسه')
    
    # اطلاعات درخواست
    request_path = models.CharField(max_length=500, blank=True, null=True, help_text='مسیر درخواست')
    request_method = models.CharField(max_length=10, blank=True, null=True, help_text='متد درخواست')
    user_agent = models.TextField(blank=True, null=True, help_text='User Agent کاربر')
    ip_address = models.GenericIPAddressField(blank=True, null=True, help_text='آدرس IP')
    
    # داده‌های اضافی
    additional_data = models.JSONField(default=dict, blank=True, help_text='داده‌های اضافی خطا')
    
    # زمان‌ها
    first_occurred = models.DateTimeField(default=timezone.now, help_text='اولین بار که خطا رخ داده')
    last_occurred = models.DateTimeField(default=timezone.now, help_text='آخرین بار که خطا رخ داده')
    resolved_at = models.DateTimeField(blank=True, null=True, help_text='زمان حل خطا')
    
    # آمار تکرار
    occurrence_count = models.PositiveIntegerField(default=1, help_text='تعداد تکرار خطا')
    
    # مدیریت
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_errors'
    )
    resolution_notes = models.TextField(blank=True, null=True, help_text='یادداشت‌های حل خطا')
    
    # متادیتا
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'خطای سیستم'
        verbose_name_plural = 'خطاهای سیستم'
        ordering = ['-last_occurred', '-severity']
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['category', 'module']),
            models.Index(fields=['user', 'company_id']),
            models.Index(fields=['first_occurred', 'last_occurred']),
        ]
    
    def __str__(self):
        return f"{self.error_code} - {self.title}"
    
    def mark_resolved(self, notes=None, resolved_by=None):
        """علامت‌گذاری خطا به عنوان حل شده"""
        self.status = ErrorStatus.RESOLVED
        self.resolved_at = timezone.now()
        if notes:
            self.resolution_notes = notes
        if resolved_by:
            self.assigned_to = resolved_by
        self.save()
    
    def increment_occurrence(self):
        """افزایش تعداد تکرار خطا"""
        self.occurrence_count += 1
        self.last_occurred = timezone.now()
        self.save()


class ErrorRecoveryAction(models.Model):
    """مدل برای ذخیره اقدامات بازیابی خطا"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    error = models.ForeignKey(
        SystemError, 
        on_delete=models.CASCADE, 
        related_name='recovery_actions'
    )
    
    # اطلاعات اقدام
    action_name = models.CharField(max_length=100, help_text='نام اقدام بازیابی')
    action_description = models.TextField(help_text='شرح اقدام بازیابی')
    action_code = models.TextField(help_text='کد اجرایی اقدام')
    
    # نتیجه اقدام
    executed_at = models.DateTimeField(default=timezone.now, help_text='زمان اجرای اقدام')
    executed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='executed_recovery_actions'
    )
    success = models.BooleanField(default=False, help_text='موفقیت اقدام')
    execution_time = models.DurationField(blank=True, null=True, help_text='زمان اجرای اقدام')
    
    # لاگ اجرا
    execution_log = models.TextField(blank=True, null=True, help_text='لاگ اجرای اقدام')
    error_output = models.TextField(blank=True, null=True, help_text='خروجی خطا در صورت شکست')
    
    # متادیتا
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'اقدام بازیابی خطا'
        verbose_name_plural = 'اقدامات بازیابی خطا'
        ordering = ['-executed_at']
    
    def __str__(self):
        return f"{self.action_name} - {self.error.error_code}"


class ErrorPattern(models.Model):
    """مدل برای شناسایی الگوهای خطا"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pattern_name = models.CharField(max_length=100, unique=True, help_text='نام الگو')
    pattern_description = models.TextField(help_text='شرح الگوی خطا')
    
    # مشخصات الگو
    category = models.CharField(
        max_length=20,
        choices=ErrorCategory.choices,
        help_text='دسته‌بندی خطا'
    )
    module_pattern = models.CharField(max_length=100, help_text='الگوی ماژول')
    function_pattern = models.CharField(max_length=100, help_text='الگوی تابع')
    message_pattern = models.TextField(help_text='الگوی پیام خطا')
    
    # تنظیمات
    auto_resolve = models.BooleanField(default=False, help_text='حل خودکار خطا')
    recovery_action = models.TextField(blank=True, null=True, help_text='اقدام بازیابی خودکار')
    severity_override = models.CharField(
        max_length=20,
        choices=ErrorSeverity.choices,
        blank=True,
        null=True,
        help_text='شدت پیش‌فرض برای این الگو'
    )
    
    # آمار
    match_count = models.PositiveIntegerField(default=0, help_text='تعداد تطابق‌ها')
    last_matched = models.DateTimeField(blank=True, null=True, help_text='آخرین تطابق')
    
    # فعال/غیرفعال
    is_active = models.BooleanField(default=True, help_text='فعال بودن الگو')
    
    # متادیتا
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'الگوی خطا'
        verbose_name_plural = 'الگوهای خطا'
        ordering = ['-match_count']
    
    def __str__(self):
        return self.pattern_name
    
    def increment_match(self):
        """افزایش تعداد تطابق الگو"""
        self.match_count += 1
        self.last_matched = timezone.now()
        self.save()


class ErrorAlertRule(models.Model):
    """مدل برای قوانین هشدار خطا"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule_name = models.CharField(max_length=100, unique=True, help_text='نام قانون هشدار')
    rule_description = models.TextField(help_text='شرح قانون هشدار')
    
    # شرایط هشدار
    severity_threshold = models.CharField(
        max_length=20,
        choices=ErrorSeverity.choices,
        help_text='آستانه شدت خطا'
    )
    category_filter = models.CharField(
        max_length=20,
        choices=ErrorCategory.choices,
        blank=True,
        null=True,
        help_text='فیلتر دسته‌بندی (اختیاری)'
    )
    module_filter = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text='فیلتر ماژول (اختیاری)'
    )
    
    # شرایط زمانی
    time_window_minutes = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
        help_text='بازه زمانی بر حسب دقیقه'
    )
    error_count_threshold = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1)],
        help_text='آستانه تعداد خطا'
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
        verbose_name = 'قانون هشدار خطا'
        verbose_name_plural = 'قوانین هشدار خطا'
        ordering = ['-is_active', '-trigger_count']
    
    def __str__(self):
        return self.rule_name
    
    def increment_trigger(self):
        """افزایش تعداد فعال‌سازی قانون"""
        self.trigger_count += 1
        self.last_triggered = timezone.now()
        self.save()
