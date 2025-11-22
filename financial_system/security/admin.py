from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    SecurityPolicy, EncryptionKey, SecurityAuditLog, DataAccessLog,
    SuspiciousActivity, SecurityAlertRule, SecurityLevel, SecurityEventType
)


class SecurityLevelFilter(admin.SimpleListFilter):
    """فیلتر بر اساس سطح امنیتی"""
    title = 'سطح امنیتی'
    parameter_name = 'security_level'

    def lookups(self, request, model_admin):
        return SecurityLevel.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(security_level=self.value())
        return queryset


class EventTypeFilter(admin.SimpleListFilter):
    """فیلتر بر اساس نوع رویداد"""
    title = 'نوع رویداد'
    parameter_name = 'event_type'

    def lookups(self, request, model_admin):
        return SecurityEventType.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(event_type=self.value())
        return queryset


class RecentEventsFilter(admin.SimpleListFilter):
    """فیلتر رویدادهای اخیر"""
    title = 'رویدادهای اخیر'
    parameter_name = 'recent'

    def lookups(self, request, model_admin):
        return [
            ('today', 'امروز'),
            ('week', 'هفته جاری'),
            ('month', 'ماه جاری'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'today':
            today = timezone.now().date()
            return queryset.filter(created_at__date=today)
        elif self.value() == 'week':
            week_ago = timezone.now() - timedelta(days=7)
            return queryset.filter(created_at__gte=week_ago)
        elif self.value() == 'month':
            month_ago = timezone.now() - timedelta(days=30)
            return queryset.filter(created_at__gte=month_ago)
        return queryset


@admin.register(SecurityPolicy)
class SecurityPolicyAdmin(admin.ModelAdmin):
    """مدیریت سیاست‌های امنیتی"""
    
    list_display = [
        'policy_name', 'default_encryption_algorithm', 'key_rotation_days',
        'max_login_attempts', 'session_timeout_minutes', 'is_active_badge'
    ]
    
    list_filter = ['is_active', 'default_encryption_algorithm']
    search_fields = ['policy_name', 'policy_description']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'policy_name', 'policy_description', 'is_active'
            )
        }),
        ('تنظیمات رمزنگاری', {
            'fields': (
                'default_encryption_algorithm', 'key_rotation_days'
            )
        }),
        ('تنظیمات احراز هویت', {
            'fields': (
                'max_login_attempts', 'session_timeout_minutes',
                'password_min_length', 'password_complexity'
            )
        }),
        ('تنظیمات لاگ‌گیری', {
            'fields': (
                'enable_security_audit', 'audit_retention_days'
            )
        }),
        ('متادیتا', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def is_active_badge(self, obj):
        """نمایش وضعیت فعال بودن"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: green; color: white; padding: 2px 6px; border-radius: 3px;">فعال</span>'
            )
        else:
            return format_html(
                '<span style="background-color: gray; color: white; padding: 2px 6px; border-radius: 3px;">غیرفعال</span>'
            )
    is_active_badge.short_description = 'وضعیت'


@admin.register(EncryptionKey)
class EncryptionKeyAdmin(admin.ModelAdmin):
    """مدیریت کلیدهای رمزنگاری"""
    
    list_display = [
        'key_name', 'key_version', 'algorithm_display', 'is_active_badge',
        'is_primary_badge', 'activated_at', 'expires_at', 'status'
    ]
    
    list_filter = ['algorithm', 'is_active', 'is_primary']
    search_fields = ['key_name', 'key_description']
    readonly_fields = ['created_at', 'activated_at', 'rotated_at']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'key_name', 'key_description', 'algorithm', 'key_version'
            )
        }),
        ('وضعیت کلید', {
            'fields': (
                'is_active', 'is_primary', 'activated_at', 'expires_at', 'rotated_at'
            )
        }),
        ('داده کلید', {
            'fields': ('key_data', 'key_checksum'),
            'classes': ('collapse',)
        }),
        ('متادیتا', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def algorithm_display(self, obj):
        """نمایش الگوریتم"""
        return obj.get_algorithm_display()
    algorithm_display.short_description = 'الگوریتم'
    
    def is_active_badge(self, obj):
        """نمایش وضعیت فعال بودن"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: green; color: white; padding: 2px 6px; border-radius: 3px;">فعال</span>'
            )
        else:
            return format_html(
                '<span style="background-color: gray; color: white; padding: 2px 6px; border-radius: 3px;">غیرفعال</span>'
            )
    is_active_badge.short_description = 'فعال'
    
    def is_primary_badge(self, obj):
        """نمایش وضعیت اصلی بودن"""
        if obj.is_primary:
            return format_html(
                '<span style="background-color: blue; color: white; padding: 2px 6px; border-radius: 3px;">اصلی</span>'
            )
        else:
            return format_html(
                '<span style="background-color: gray; color: white; padding: 2px 6px; border-radius: 3px;">پشتیبان</span>'
            )
    is_primary_badge.short_description = 'نوع'
    
    def status(self, obj):
        """نمایش وضعیت کلی کلید"""
        now = timezone.now()
        
        if not obj.is_active:
            return format_html(
                '<span style="background-color: red; color: white; padding: 2px 6px; border-radius: 3px;">غیرفعال</span>'
            )
        elif obj.expires_at <= now:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 2px 6px; border-radius: 3px;">منقضی شده</span>'
            )
        elif (obj.expires_at - now).days <= 7:
            return format_html(
                '<span style="background-color: yellow; color: black; padding: 2px 6px; border-radius: 3px;">نزدیک انقضا</span>'
            )
        else:
            return format_html(
                '<span style="background-color: green; color: white; padding: 2px 6px; border-radius: 3px;">فعال</span>'
            )
    status.short_description = 'وضعیت'


@admin.register(SecurityAuditLog)
class SecurityAuditLogAdmin(admin.ModelAdmin):
    """مدیریت لاگ‌های امنیتی"""
    
    list_display = [
        'event_type_display', 'security_level_badge', 'user_display',
        'ip_address', 'success_badge', 'created_at'
    ]
    
    list_filter = [
        EventTypeFilter,
        SecurityLevelFilter,
        RecentEventsFilter,
        'success',
        'created_at',
    ]
    
    search_fields = [
        'event_description', 'user__username', 'ip_address', 'request_path'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'event_type', 'security_level', 'user',
        'session_id', 'request_path', 'request_method', 'user_agent',
        'ip_address', 'success', 'error_message', 'additional_data_preview'
    ]
    
    fieldsets = (
        ('اطلاعات رویداد', {
            'fields': (
                'event_type', 'event_description', 'security_level', 'success'
            )
        }),
        ('اطلاعات کاربر', {
            'fields': ('user', 'session_id')
        }),
        ('اطلاعات درخواست', {
            'fields': (
                'request_path', 'request_method', 'user_agent', 'ip_address'
            )
        }),
        ('اطلاعات خطا', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('داده‌های اضافی', {
            'fields': ('additional_data_preview',),
            'classes': ('collapse',)
        }),
        ('متادیتا', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def event_type_display(self, obj):
        """نمایش نوع رویداد"""
        return obj.get_event_type_display()
    event_type_display.short_description = 'نوع رویداد'
    
    def security_level_badge(self, obj):
        """نمایش سطح امنیتی"""
        colors = {
            SecurityLevel.LOW: 'green',
            SecurityLevel.MEDIUM: 'orange',
            SecurityLevel.HIGH: 'red',
            SecurityLevel.CRITICAL: 'darkred',
        }
        color = colors.get(obj.security_level, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">{}</span>',
            color, obj.get_security_level_display()
        )
    security_level_badge.short_description = 'سطح امنیتی'
    
    def user_display(self, obj):
        """نمایش کاربر"""
        if obj.user:
            return obj.user.username
        return 'ناشناس'
    user_display.short_description = 'کاربر'
    
    def success_badge(self, obj):
        """نمایش وضعیت موفقیت"""
        if obj.success:
            return format_html(
                '<span style="background-color: green; color: white; padding: 2px 6px; border-radius: 3px;">موفق</span>'
            )
        else:
            return format_html(
                '<span style="background-color: red; color: white; padding: 2px 6px; border-radius: 3px;">شکست</span>'
            )
    success_badge.short_description = 'موفقیت'
    
    def additional_data_preview(self, obj):
        """پیش‌نمایش داده‌های اضافی"""
        if obj.additional_data:
            return format_html('<pre>{}</pre>', json.dumps(obj.additional_data, indent=2, ensure_ascii=False))
        return '-'
    additional_data_preview.short_description = 'پیش‌نمایش داده اضافی'


@admin.register(DataAccessLog)
class DataAccessLogAdmin(admin.ModelAdmin):
    """مدیریت لاگ‌های دسترسی به داده"""
    
    list_display = [
        'access_type_display', 'data_type', 'user_display',
        'company_id', 'period_id', 'created_at'
    ]
    
    list_filter = ['access_type', 'data_type', 'created_at']
    search_fields = ['data_type', 'user__username', 'data_id', 'request_path']
    
    readonly_fields = [
        'id', 'created_at', 'access_type', 'data_type', 'data_id',
        'data_summary', 'user', 'company_id', 'period_id',
        'request_path', 'ip_address', 'additional_data_preview'
    ]
    
    fieldsets = (
        ('اطلاعات دسترسی', {
            'fields': (
                'access_type', 'data_type', 'data_id', 'data_summary'
            )
        }),
        ('اطلاعات کاربر', {
            'fields': ('user', 'company_id', 'period_id')
        }),
        ('اطلاعات درخواست', {
            'fields': ('request_path', 'ip_address')
        }),
        ('داده‌های اضافی', {
            'fields': ('additional_data_preview',),
            'classes': ('collapse',)
        }),
        ('متادیتا', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def access_type_display(self, obj):
        """نمایش نوع دسترسی"""
        return obj.get_access_type_display()
    access_type_display.short_description = 'نوع دسترسی'
    
    def user_display(self, obj):
        """نمایش کاربر"""
        if obj.user:
            return obj.user.username
        return 'ناشناس'
    user_display.short_description = 'کاربر'
    
    def additional_data_preview(self, obj):
        """پیش‌نمایش داده‌های اضافی"""
        if obj.additional_data:
            return format_html('<pre>{}</pre>', json.dumps(obj.additional_data, indent=2, ensure_ascii=False))
        return '-'
    additional_data_preview.short_description = 'پیش‌نمایش داده اضافی'


@admin.register(SuspiciousActivity)
class SuspiciousActivityAdmin(admin.ModelAdmin):
    """مدیریت فعالیت‌های مشکوک"""
    
    list_display = [
        'activity_type', 'severity_badge', 'user_display', 'ip_address',
        'confidence_score_display', 'is_investigated_badge', 'created_at'
    ]
    
    list_filter = [
        SecurityLevelFilter,
        'is_investigated',
        'detection_method',
        'created_at',
    ]
    
    search_fields = [
        'activity_type', 'activity_description', 'user__username', 'ip_address'
    ]
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'activity_type', 'activity_description',
        'severity', 'user', 'ip_address', 'detection_method', 'confidence_score',
        'additional_data_preview'
    ]
    
    fieldsets = (
        ('اطلاعات فعالیت', {
            'fields': (
                'activity_type', 'activity_description', 'severity'
            )
        }),
        ('اطلاعات تشخیص', {
            'fields': ('detection_method', 'confidence_score')
        }),
        ('اطلاعات کاربر', {
            'fields': ('user', 'ip_address')
        }),
        ('وضعیت بررسی', {
            'fields': (
                'is_investigated', 'investigation_notes',
                'investigated_by', 'investigated_at'
            )
        }),
        ('داده‌های اضافی', {
            'fields': ('additional_data_preview',),
            'classes': ('collapse',)
        }),
        ('متادیتا', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_investigated', 'mark_as_false_positive']
    
    def severity_badge(self, obj):
        """نمایش شدت فعالیت"""
        colors = {
            SecurityLevel.LOW: 'green',
            SecurityLevel.MEDIUM: 'orange',
            SecurityLevel.HIGH: 'red',
            SecurityLevel.CRITICAL: 'darkred',
        }
        color = colors.get(obj.severity, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">{}</span>',
            color, obj.get_severity_display()
        )
    severity_badge.short_description = 'شدت'
    
    def user_display(self, obj):
        """نمایش کاربر"""
        if obj.user:
            return obj.user.username
        return 'ناشناس'
    user_display.short_description = 'کاربر'
    
    def confidence_score_display(self, obj):
        """نمایش امتیاز اطمینان"""
        if obj.confidence_score >= 0.8:
            color = 'red'
        elif obj.confidence_score >= 0.6:
            color = 'orange'
        else:
            color = 'yellow'
        
        return format_html(
            '<span style="background-color: {}; color: black; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">{:.2f}</span>',
            color, obj.confidence_score
        )
    confidence_score_display.short_description = 'امتیاز اطمینان'
    
    def is_investigated_badge(self, obj):
        """نمایش وضعیت بررسی"""
        if obj.is_investigated:
            return format_html(
                '<span style="background-color: green; color: white; padding: 2px 6px; border-radius: 3px;">بررسی شده</span>'
            )
        else:
            return format_html(
                '<span style="background-color: orange; color: white; padding: 2px 6px; border-radius: 3px;">در انتظار بررسی</span>'
            )
    is_investigated_badge.short_description = 'وضعیت بررسی'
    
    def additional_data_preview(self, obj):
        """پیش‌نمایش داده‌های اضافی"""
        if obj.additional_data:
            return format_html('<pre>{}</pre>', json.dumps(obj.additional_data, indent=2, ensure_ascii=False))
        return '-'
    additional_data_preview.short_description = 'پیش‌نمایش داده اضافی'
    
    def mark_as_investigated(self, request, queryset):
        """علامت‌گذاری فعالیت‌ها به عنوان بررسی شده"""
        updated = queryset.update(
            is_investigated=True,
            investigated_at=timezone.now(),
            investigated_by=request.user
        )
        self.message_user(request, f'{updated} فعالیت به عنوان بررسی شده علامت‌گذاری شد.')
    mark_as_investigated.short_description = 'علامت‌گذاری به عنوان بررسی شده'
    
    def mark_as_false_positive(self, request, queryset):
        """علامت‌گذاری فعالیت‌ها به عنوان مثبت کاذب"""
        for activity in queryset:
            activity.mark_investigated(
                notes="مثبت کاذب - فعالیت طبیعی تشخیص داده شد",
                investigator=request.user
            )
        self.message_user(request, f'{queryset.count()} فعالیت به عنوان مثبت کاذب علامت‌گذاری شد.')
    mark_as_false_positive.short_description = 'علامت‌گذاری به عنوان مثبت کاذب'


@admin.register(SecurityAlertRule)
class SecurityAlertRuleAdmin(admin.ModelAdmin):
    """مدیریت قوانین هشدار امنیتی"""
    
    list_display = [
        'rule_name', 'security_level_threshold_display', 'event_type_filter_display',
        'time_window_minutes', 'error_count_threshold', 'alert_channel_display',
        'trigger_count', 'is_active_badge'
    ]
    
    list_filter = [
        'security_level_threshold', 'alert_channel', 'is_active'
    ]
    
    search_fields = ['rule_name', 'rule_description']
    readonly_fields = ['trigger_count', 'last_triggered', 'created_at', 'updated_at']
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'rule_name', 'rule_description', 'is_active'
            )
        }),
        ('شرایط هشدار', {
            'fields': (
                'event_type_filter', 'security_level_threshold',
                'time_window_minutes', 'error_count_threshold'
            )
        }),
        ('تنظیمات هشدار', {
            'fields': ('alert_channel', 'recipients')
        }),
        ('آمار', {
            'fields': ('trigger_count', 'last_triggered'),
            'classes': ('collapse',)
        }),
        ('متادیتا', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def security_level_threshold_display(self, obj):
        """نمایش آستانه سطح امنیتی"""
        return obj.get_security_level_threshold_display()
    security_level_threshold_display.short_description = 'آستانه سطح'
    
    def event_type_filter_display(self, obj):
        """نمایش فیلتر نوع رویداد"""
        if obj.event_type_filter:
            return obj.get_event_type_filter_display()
        return 'همه'
    event_type_filter_display.short_description = 'فیلتر رویداد'
    
    def alert_channel_display(self, obj):
        """نمایش کانال هشدار"""
        channel_names = {
            'EMAIL': 'ایمیل',
            'DASHBOARD': 'داشبورد',
            'SLACK': 'اسلک',
            'TELEGRAM': 'تلگرام',
        }
        return channel_names.get(obj.alert_channel, obj.alert_channel)
    alert_channel_display.short_description = 'کانال هشدار'
    
    def is_active_badge(self, obj):
        """نمایش وضعیت فعال بودن"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: green; color: white; padding: 2px 6px; border-radius: 3px;">فعال</span>'
            )
        else:
            return format_html(
                '<span style="background-color: gray; color: white; padding: 2px 6px; border-radius: 3px;">غیرفعال</span>'
            )
    is_active_badge.short_description = 'وضعیت'


class SecurityAdminSite(admin.AdminSite):
    """سایت ادمین اختصاصی برای مدیریت امنیت"""
    
    site_header = 'مدیریت امنیت سیستم مالی'
    site_title = 'مدیریت امنیت'
    index_title = 'داشبورد امنیتی'
    
    def get_app_list(self, request):
        """
        سفارشی‌سازی لیست اپلیکیشن‌ها برای نمایش بهتر
        """
        app_list = super().get_app_list(request)
        
        # اضافه کردن آمار به داشبورد
        security_stats = self._get_security_stats()
        
        return app_list
    
    def _get_security_stats(self):
        """دریافت آمار امنیتی"""
        today = timezone.now().date()
        week_ago = timezone.now() - timedelta(days=7)
        
        stats = {
            'total_audit_logs': SecurityAuditLog.objects.count(),
            'today_audit_logs': SecurityAuditLog.objects.filter(created_at__date=today).count(),
            'week_audit_logs': SecurityAuditLog.objects.filter(created_at__gte=week_ago).count(),
            'suspicious_activities': SuspiciousActivity.objects.filter(is_investigated=False).count(),
            'failed_logins': SecurityAuditLog.objects.filter(
                event_type=SecurityEventType.LOGIN_FAILED,
                created_at__gte=week_ago
            ).count(),
            'access_denied': SecurityAuditLog.objects.filter(
                event_type=SecurityEventType.ACCESS_DENIED,
                created_at__gte=week_ago
            ).count(),
        }
        
        return stats


# برای استفاده از این سایت ادمین اختصاصی، باید در urls.py ثبت شود
# security_admin_site = SecurityAdminSite(name='security_admin')
