from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    SystemError, ErrorRecoveryAction, ErrorPattern, ErrorAlertRule,
    ErrorSeverity, ErrorStatus, ErrorCategory
)


class SeverityFilter(admin.SimpleListFilter):
    """فیلتر بر اساس شدت خطا"""
    title = 'شدت خطا'
    parameter_name = 'severity'

    def lookups(self, request, model_admin):
        return ErrorSeverity.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(severity=self.value())
        return queryset


class CategoryFilter(admin.SimpleListFilter):
    """فیلتر بر اساس دسته‌بندی خطا"""
    title = 'دسته‌بندی'
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        return ErrorCategory.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category=self.value())
        return queryset


class StatusFilter(admin.SimpleListFilter):
    """فیلتر بر اساس وضعیت خطا"""
    title = 'وضعیت'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return ErrorStatus.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset


class RecentErrorsFilter(admin.SimpleListFilter):
    """فیلتر خطاهای اخیر"""
    title = 'خطاهای اخیر'
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


@admin.register(SystemError)
class SystemErrorAdmin(admin.ModelAdmin):
    """مدیریت خطاهای سیستم در پنل ادمین"""
    
    list_display = [
        'error_code', 'severity_badge', 'category_display', 'title_truncated',
        'module', 'user_display', 'company_id', 'occurrence_count',
        'last_occurred', 'status_badge', 'actions'
    ]
    
    list_filter = [
        SeverityFilter,
        CategoryFilter,
        StatusFilter,
        RecentErrorsFilter,
        'module',
        'created_at',
    ]
    
    search_fields = [
        'error_code', 'title', 'description', 'module', 'function_name'
    ]
    
    readonly_fields = [
        'id', 'error_code', 'created_at', 'updated_at', 'first_occurred', 'last_occurred',
        'occurrence_count', 'stack_trace_preview'
    ]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'error_code', 'title', 'description', 'severity', 'category', 'status'
            )
        }),
        ('اطلاعات فنی', {
            'fields': (
                'module', 'function_name', 'line_number', 'stack_trace_preview'
            )
        }),
        ('اطلاعات کاربر و جلسه', {
            'fields': (
                'user', 'company_id', 'period_id', 'session_id'
            )
        }),
        ('اطلاعات درخواست', {
            'fields': (
                'request_path', 'request_method', 'user_agent', 'ip_address'
            )
        }),
        ('داده‌های اضافی', {
            'fields': ('additional_data',),
            'classes': ('collapse',)
        }),
        ('آمار و مدیریت', {
            'fields': (
                'occurrence_count', 'first_occurred', 'last_occurred',
                'assigned_to', 'resolution_notes', 'resolved_at'
            )
        }),
        ('متادیتا', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_resolved', 'mark_as_in_progress', 'assign_to_me']
    
    def severity_badge(self, obj):
        """نمایش شدت خطا به صورت بدج"""
        colors = {
            ErrorSeverity.LOW: 'green',
            ErrorSeverity.MEDIUM: 'orange',
            ErrorSeverity.HIGH: 'red',
            ErrorSeverity.CRITICAL: 'darkred',
        }
        color = colors.get(obj.severity, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">{}</span>',
            color, obj.get_severity_display()
        )
    severity_badge.short_description = 'شدت'
    
    def status_badge(self, obj):
        """نمایش وضعیت خطا به صورت بدج"""
        colors = {
            ErrorStatus.NEW: 'blue',
            ErrorStatus.IN_PROGRESS: 'orange',
            ErrorStatus.RESOLVED: 'green',
            ErrorStatus.IGNORED: 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'وضعیت'
    
    def category_display(self, obj):
        """نمایش دسته‌بندی"""
        return obj.get_category_display()
    category_display.short_description = 'دسته‌بندی'
    
    def title_truncated(self, obj):
        """نمایش عنوان کوتاه شده"""
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_truncated.short_description = 'عنوان'
    
    def user_display(self, obj):
        """نمایش کاربر"""
        if obj.user:
            return obj.user.username
        return 'ناشناس'
    user_display.short_description = 'کاربر'
    
    def stack_trace_preview(self, obj):
        """پیش‌نمایش ردیابی استک"""
        if obj.stack_trace:
            lines = obj.stack_trace.split('\n')[:10]  # فقط 10 خط اول
            return format_html('<pre style="max-height: 200px; overflow: auto;">{}</pre>', '\n'.join(lines))
        return '-'
    stack_trace_preview.short_description = 'پیش‌نمایش ردیابی استک'
    
    def actions(self, obj):
        """دکمه‌های عملیات"""
        links = []
        
        # دکمه مشاهده جزئیات
        url = reverse('admin:error_management_systemerror_change', args=[obj.id])
        links.append(f'<a href="{url}" class="button">مشاهده</a>')
        
        # دکمه حل خطا
        if obj.status != ErrorStatus.RESOLVED:
            resolve_url = reverse('admin:error_management_systemerror_resolve', args=[obj.id])
            links.append(f'<a href="{resolve_url}" class="button" style="background-color: green; color: white;">حل شده</a>')
        
        return format_html(' '.join(links))
    actions.short_description = 'عملیات'
    
    def mark_as_resolved(self, request, queryset):
        """علامت‌گذاری خطاها به عنوان حل شده"""
        updated = queryset.update(
            status=ErrorStatus.RESOLVED,
            resolved_at=timezone.now(),
            assigned_to=request.user
        )
        self.message_user(request, f'{updated} خطا به عنوان حل شده علامت‌گذاری شد.')
    mark_as_resolved.short_description = 'علامت‌گذاری به عنوان حل شده'
    
    def mark_as_in_progress(self, request, queryset):
        """علامت‌گذاری خطاها به عنوان در حال بررسی"""
        updated = queryset.update(
            status=ErrorStatus.IN_PROGRESS,
            assigned_to=request.user
        )
        self.message_user(request, f'{updated} خطا به عنوان در حال بررسی علامت‌گذاری شد.')
    mark_as_in_progress.short_description = 'علامت‌گذاری به عنوان در حال بررسی'
    
    def assign_to_me(self, request, queryset):
        """اختصاص خطاها به کاربر فعلی"""
        updated = queryset.update(assigned_to=request.user)
        self.message_user(request, f'{updated} خطا به شما اختصاص داده شد.')
    assign_to_me.short_description = 'اختصاص به من'
    
    def get_queryset(self, request):
        """بهینه‌سازی کوئری‌ست"""
        return super().get_queryset(request).select_related('user', 'assigned_to')


@admin.register(ErrorRecoveryAction)
class ErrorRecoveryActionAdmin(admin.ModelAdmin):
    """مدیریت اقدامات بازیابی خطا"""
    
    list_display = [
        'action_name', 'error_link', 'executed_at', 'success_badge',
        'execution_time', 'executed_by_display'
    ]
    
    list_filter = ['success', 'executed_at']
    search_fields = ['action_name', 'error__error_code', 'error__title']
    readonly_fields = ['id', 'executed_at', 'created_at']
    
    def error_link(self, obj):
        """لینک به خطای مرتبط"""
        url = reverse('admin:error_management_systemerror_change', args=[obj.error.id])
        return format_html('<a href="{}">{}</a>', url, obj.error.error_code)
    error_link.short_description = 'خطا'
    
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
    
    def executed_by_display(self, obj):
        """نمایش کاربر اجراکننده"""
        if obj.executed_by:
            return obj.executed_by.username
        return 'سیستم'
    executed_by_display.short_description = 'اجرا کننده'


@admin.register(ErrorPattern)
class ErrorPatternAdmin(admin.ModelAdmin):
    """مدیریت الگوهای خطا"""
    
    list_display = [
        'pattern_name', 'category_display', 'module_pattern', 'function_pattern',
        'auto_resolve_badge', 'match_count', 'last_matched', 'is_active_badge'
    ]
    
    list_filter = ['category', 'auto_resolve', 'is_active']
    search_fields = ['pattern_name', 'pattern_description']
    readonly_fields = ['match_count', 'last_matched', 'created_at', 'updated_at']
    
    def category_display(self, obj):
        """نمایش دسته‌بندی"""
        return obj.get_category_display()
    category_display.short_description = 'دسته‌بندی'
    
    def auto_resolve_badge(self, obj):
        """نمایش وضعیت حل خودکار"""
        if obj.auto_resolve:
            return format_html(
                '<span style="background-color: green; color: white; padding: 2px 6px; border-radius: 3px;">فعال</span>'
            )
        else:
            return format_html(
                '<span style="background-color: gray; color: white; padding: 2px 6px; border-radius: 3px;">غیرفعال</span>'
            )
    auto_resolve_badge.short_description = 'حل خودکار'
    
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


@admin.register(ErrorAlertRule)
class ErrorAlertRuleAdmin(admin.ModelAdmin):
    """مدیریت قوانین هشدار خطا"""
    
    list_display = [
        'rule_name', 'severity_threshold_display', 'category_filter_display',
        'time_window_minutes', 'error_count_threshold', 'alert_channel_display',
        'trigger_count', 'last_triggered', 'is_active_badge'
    ]
    
    list_filter = ['severity_threshold', 'category_filter', 'alert_channel', 'is_active']
    search_fields = ['rule_name', 'rule_description']
    readonly_fields = ['trigger_count', 'last_triggered', 'created_at', 'updated_at']
    
    def severity_threshold_display(self, obj):
        """نمایش آستانه شدت"""
        return obj.get_severity_threshold_display()
    severity_threshold_display.short_description = 'آستانه شدت'
    
    def category_filter_display(self, obj):
        """نمایش فیلتر دسته‌بندی"""
        if obj.category_filter:
            return obj.get_category_filter_display()
        return 'همه'
    category_filter_display.short_description = 'فیلتر دسته‌بندی'
    
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


class ErrorManagementAdminSite(admin.AdminSite):
    """سایت ادمین اختصاصی برای مدیریت خطاها"""
    
    site_header = 'مدیریت خطاهای سیستم مالی'
    site_title = 'مدیریت خطاها'
    index_title = 'داشبورد مدیریت خطاها'
    
    def get_app_list(self, request):
        """
        سفارشی‌سازی لیست اپلیکیشن‌ها برای نمایش بهتر
        """
        app_list = super().get_app_list(request)
        
        # اضافه کردن آمار به داشبورد
        error_stats = self._get_error_stats()
        
        return app_list
    
    def _get_error_stats(self):
        """دریافت آمار خطاها"""
        today = timezone.now().date()
        week_ago = timezone.now() - timedelta(days=7)
        
        stats = {
            'total_errors': SystemError.objects.count(),
            'unresolved_errors': SystemError.objects.filter(
                status__in=[ErrorStatus.NEW, ErrorStatus.IN_PROGRESS]
            ).count(),
            'today_errors': SystemError.objects.filter(created_at__date=today).count(),
            'week_errors': SystemError.objects.filter(created_at__gte=week_ago).count(),
            'critical_errors': SystemError.objects.filter(severity=ErrorSeverity.CRITICAL).count(),
        }
        
        return stats


# ثبت ماژول‌ها در ادمین اصلی
# این کد در apps.py ادمین اصلی باید اضافه شود
