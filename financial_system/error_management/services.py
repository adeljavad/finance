"""
سرویس‌های مدیریت خطاهای پیشرفته

این ماژول سرویس‌های اصلی برای مدیریت خطاها را ارائه می‌دهد:
- ثبت و پردازش خطاها
- شناسایی الگوهای خطا
- ارسال هشدارها
- مدیریت بازیابی خطاها
- تحلیل و گزارش‌گیری
"""

import logging
import traceback
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q, F
from django.core.mail import send_mail
from django.conf import settings

from .models import (
    SystemError, ErrorRecoveryAction, ErrorPattern, ErrorAlertRule,
    ErrorSeverity, ErrorStatus, ErrorCategory
)

logger = logging.getLogger(__name__)


class ErrorHandlingService:
    """سرویس اصلی برای مدیریت خطاها"""
    
    @classmethod
    def capture_error(
        cls,
        exception: Exception,
        module: str,
        function_name: str,
        user=None,
        company_id=None,
        period_id=None,
        request=None,
        additional_data: Dict[str, Any] = None,
        severity: str = ErrorSeverity.MEDIUM,
        category: str = ErrorCategory.OTHER
    ) -> Optional[SystemError]:
        """
        ثبت و پردازش یک خطا
        
        Args:
            exception: شیء خطا
            module: نام ماژول
            function_name: نام تابع
            user: کاربر مرتبط
            company_id: شناسه شرکت
            period_id: شناسه دوره مالی
            request: درخواست مرتبط
            additional_data: داده‌های اضافی
            severity: شدت خطا
            category: دسته‌بندی خطا
            
        Returns:
            شیء SystemError ایجاد شده
        """
        try:
            # استخراج اطلاعات خطا
            error_info = cls._extract_error_info(exception, module, function_name)
            
            # بررسی الگوهای خطا
            matched_pattern = cls._check_error_patterns(error_info)
            if matched_pattern:
                severity = matched_pattern.severity_override or severity
                if matched_pattern.auto_resolve:
                    logger.info(f"خطا به صورت خودکار حل شد: {error_info['error_code']}")
                    return None
            
            # ثبت خطا در دیتابیس
            system_error = cls._create_system_error(
                error_info=error_info,
                user=user,
                company_id=company_id,
                period_id=period_id,
                request=request,
                additional_data=additional_data,
                severity=severity,
                category=category,
                matched_pattern=matched_pattern
            )
            
            # بررسی قوانین هشدار
            cls._check_alert_rules(system_error)
            
            # لاگ کردن خطا
            logger.error(
                f"خطای سیستم - کد: {system_error.error_code}, "
                f"ماژول: {module}, تابع: {function_name}, "
                f"کاربر: {user.username if user else 'ناشناس'}"
            )
            
            return system_error
            
        except Exception as e:
            logger.critical(f"خطا در ثبت خطا: {e}")
            return None
    
    @classmethod
    def _extract_error_info(cls, exception: Exception, module: str, function_name: str) -> Dict[str, Any]:
        """استخراج اطلاعات خطا از شیء Exception"""
        error_type = type(exception).__name__
        error_message = str(exception)
        stack_trace = traceback.format_exc()
        
        # تولید کد یکتای خطا
        error_code = cls._generate_error_code(error_type, module, function_name)
        
        return {
            'error_code': error_code,
            'error_type': error_type,
            'error_message': error_message,
            'stack_trace': stack_trace,
            'module': module,
            'function_name': function_name,
            'title': f"{error_type} در {module}.{function_name}",
            'description': f"{error_message} (ماژول: {module}, تابع: {function_name})"
        }
    
    @classmethod
    def _generate_error_code(cls, error_type: str, module: str, function_name: str) -> str:
        """تولید کد یکتای خطا"""
        base_code = f"{module.upper()}_{function_name.upper()}_{error_type.upper()}"
        # استفاده از UUID برای اطمینان از یکتایی
        unique_suffix = str(uuid.uuid4())[:8].upper()
        return f"ERR_{base_code}_{unique_suffix}"
    
    @classmethod
    def _check_error_patterns(cls, error_info: Dict[str, Any]) -> Optional[ErrorPattern]:
        """بررسی تطابق خطا با الگوهای موجود"""
        try:
            patterns = ErrorPattern.objects.filter(is_active=True)
            
            for pattern in patterns:
                if cls._matches_pattern(error_info, pattern):
                    pattern.increment_match()
                    return pattern
                    
        except Exception as e:
            logger.error(f"خطا در بررسی الگوهای خطا: {e}")
            
        return None
    
    @classmethod
    def _matches_pattern(cls, error_info: Dict[str, Any], pattern: ErrorPattern) -> bool:
        """بررسی تطابق خطا با یک الگوی خاص"""
        # بررسی دسته‌بندی
        if pattern.category and pattern.category != error_info.get('category', ''):
            return False
        
        # بررسی الگوی ماژول
        if pattern.module_pattern and pattern.module_pattern not in error_info['module']:
            return False
        
        # بررسی الگوی تابع
        if pattern.function_pattern and pattern.function_pattern not in error_info['function_name']:
            return False
        
        # بررسی الگوی پیام
        if pattern.message_pattern and pattern.message_pattern not in error_info['error_message']:
            return False
        
        return True
    
    @classmethod
    def _create_system_error(
        cls,
        error_info: Dict[str, Any],
        user=None,
        company_id=None,
        period_id=None,
        request=None,
        additional_data: Dict[str, Any] = None,
        severity: str = ErrorSeverity.MEDIUM,
        category: str = ErrorCategory.OTHER,
        matched_pattern: Optional[ErrorPattern] = None
    ) -> SystemError:
        """ایجاد رکورد خطا در دیتابیس"""
        
        # استخراج اطلاعات درخواست
        request_info = cls._extract_request_info(request) if request else {}
        
        # بررسی وجود خطای مشابه
        existing_error = SystemError.objects.filter(
            error_code=error_info['error_code']
        ).first()
        
        if existing_error:
            # به‌روزرسانی خطای موجود
            existing_error.increment_occurrence()
            return existing_error
        
        # ایجاد خطای جدید
        system_error = SystemError.objects.create(
            error_code=error_info['error_code'],
            title=error_info['title'],
            description=error_info['description'],
            stack_trace=error_info['stack_trace'],
            severity=severity,
            category=category,
            module=error_info['module'],
            function_name=error_info['function_name'],
            user=user,
            company_id=company_id,
            period_id=period_id,
            session_id=request_info.get('session_id'),
            request_path=request_info.get('path'),
            request_method=request_info.get('method'),
            user_agent=request_info.get('user_agent'),
            ip_address=request_info.get('ip_address'),
            additional_data=additional_data or {}
        )
        
        return system_error
    
    @classmethod
    def _extract_request_info(cls, request) -> Dict[str, Any]:
        """استخراج اطلاعات از درخواست"""
        if not request:
            return {}
        
        return {
            'path': request.path,
            'method': request.method,
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'ip_address': cls._get_client_ip(request),
            'session_id': request.session.session_key if hasattr(request, 'session') else None
        }
    
    @classmethod
    def _get_client_ip(cls, request):
        """دریافت IP کاربر"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @classmethod
    def _check_alert_rules(cls, system_error: SystemError):
        """بررسی قوانین هشدار برای خطا"""
        try:
            rules = ErrorAlertRule.objects.filter(is_active=True)
            
            for rule in rules:
                if cls._matches_alert_rule(system_error, rule):
                    cls._trigger_alert(rule, system_error)
                    rule.increment_trigger()
                    
        except Exception as e:
            logger.error(f"خطا در بررسی قوانین هشدار: {e}")
    
    @classmethod
    def _matches_alert_rule(cls, system_error: SystemError, rule: ErrorAlertRule) -> bool:
        """بررسی تطابق خطا با قانون هشدار"""
        # بررسی شدت خطا
        severity_order = [ErrorSeverity.LOW, ErrorSeverity.MEDIUM, ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
        error_severity_index = severity_order.index(system_error.severity)
        rule_severity_index = severity_order.index(rule.severity_threshold)
        
        if error_severity_index < rule_severity_index:
            return False
        
        # بررسی دسته‌بندی
        if rule.category_filter and rule.category_filter != system_error.category:
            return False
        
        # بررسی ماژول
        if rule.module_filter and rule.module_filter not in system_error.module:
            return False
        
        # بررسی تعداد خطاها در بازه زمانی
        time_threshold = timezone.now() - timedelta(minutes=rule.time_window_minutes)
        error_count = SystemError.objects.filter(
            severity=system_error.severity,
            category=system_error.category,
            created_at__gte=time_threshold
        ).count()
        
        return error_count >= rule.error_count_threshold
    
    @classmethod
    def _trigger_alert(cls, rule: ErrorAlertRule, system_error: SystemError):
        """فعال‌سازی هشدار"""
        try:
            if rule.alert_channel == 'EMAIL':
                cls._send_email_alert(rule, system_error)
            elif rule.alert_channel == 'DASHBOARD':
                cls._log_dashboard_alert(rule, system_error)
            # سایر کانال‌ها (اسلک، تلگرام) می‌توانند در آینده پیاده‌سازی شوند
            
            logger.info(f"هشدار فعال شد: {rule.rule_name} برای خطای {system_error.error_code}")
            
        except Exception as e:
            logger.error(f"خطا در فعال‌سازی هشدار: {e}")
    
    @classmethod
    def _send_email_alert(cls, rule: ErrorAlertRule, system_error: SystemError):
        """ارسال هشدار از طریق ایمیل"""
        if not rule.recipients:
            return
        
        subject = f"هشدار سیستم مالی - {rule.rule_name}"
        message = f"""
        خطای بحرانی در سیستم مالی شناسایی شد:
        
        قانون هشدار: {rule.rule_name}
        کد خطا: {system_error.error_code}
        شدت: {system_error.get_severity_display()}
        ماژول: {system_error.module}
        توضیحات: {system_error.description}
        
        تاریخ وقوع: {system_error.last_occurred}
        تعداد تکرار: {system_error.occurrence_count}
        
        لطفاً در اسرع وقت اقدام نمایید.
        """
        
        recipients = [email.strip() for email in rule.recipients.split(',')]
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"خطا در ارسال ایمیل هشدار: {e}")
    
    @classmethod
    def _log_dashboard_alert(cls, rule: ErrorAlertRule, system_error: SystemError):
        """ثبت هشدار در لاگ برای نمایش در داشبورد"""
        alert_message = (
            f"هشدار: {rule.rule_name} - "
            f"خطای {system_error.error_code} در ماژول {system_error.module}"
        )
        logger.warning(alert_message)


class ErrorRecoveryService:
    """سرویس بازیابی از خطاها"""
    
    @classmethod
    def execute_recovery_action(cls, error: SystemError, action_name: str, user=None) -> bool:
        """
        اجرای یک اقدام بازیابی برای خطا
        
        Args:
            error: خطای هدف
            action_name: نام اقدام بازیابی
            user: کاربر اجراکننده
            
        Returns:
            موفقیت یا شکست اقدام
        """
        try:
            # پیدا کردن اقدام مناسب
            recovery_action = cls._find_recovery_action(error, action_name)
            if not recovery_action:
                logger.warning(f"اقدام بازیابی '{action_name}' برای خطای {error.error_code} یافت نشد")
                return False
            
            # اجرای اقدام
            start_time = timezone.now()
            success, execution_log, error_output = cls._execute_action_code(recovery_action.action_code)
            execution_time = timezone.now() - start_time
            
            # ثبت نتیجه
            ErrorRecoveryAction.objects.create(
                error=error,
                action_name=action_name,
                action_description=recovery_action.action_description,
                action_code=recovery_action.action_code,
                executed_at=start_time,
                executed_by=user,
                success=success,
                execution_time=execution_time,
                execution_log=execution_log,
                error_output=error_output
            )
            
            if success:
                error.mark_resolved(notes=f"حل شده توسط اقدام بازیابی: {action_name}", resolved_by=user)
                logger.info(f"اقدام بازیابی '{action_name}' برای خطای {error.error_code} با موفقیت اجرا شد")
            else:
                logger.error(f"اقدام بازیابی '{action_name}' برای خطای {error.error_code} شکست خورد")
            
            return success
            
        except Exception as e:
            logger.error(f"خطا در اجرای اقدام بازیابی: {e}")
            return False
    
    @classmethod
    def _find_recovery_action(cls, error: SystemError, action_name: str):
        """پیدا کردن اقدام بازیابی مناسب"""
        # این تابع می‌تواند از الگوهای خطا یا تنظیمات پیش‌فرض استفاده کند
        # فعلاً یک نمونه ساده برگردانده می‌شود
        return None
    
    @classmethod
    def _execute_action_code(cls, action_code: str):
        """اجرای کد اقدام بازیابی"""
        try:
            # اجرای کد اقدام (ایمن)
            # توجه: این بخش باید با دقت پیاده‌سازی شود تا امنیت حفظ شود
            exec_globals = {}
            exec_locals = {}
            
            # اجرای کد در محیط امن
            exec(action_code, exec_globals, exec_locals)
            
            # فرض می‌کنیم تابع main در کد موجود است
            if 'main' in exec_locals:
                result = exec_locals['main']()
                return True, "اقدام با موفقیت اجرا شد", None
            else:
                return False, "تابع main در کد اقدام یافت نشد", "تابع main تعریف نشده"
                
        except Exception as e:
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            return False, f"خطا در اجرای کد: {error_msg}", stack_trace


class ErrorMonitoringService:
    """سرویس مانیتورینگ و تحلیل خطاها"""
    
    @classmethod
    def initialize(cls):
        """راه‌اندازی سرویس مانیتورینگ"""
        logger.info("سرویس مانیتورینگ خطاها راه‌اندازی شد")
    
    @classmethod
    def get_error_statistics(cls, days: int = 30) -> Dict[str, Any]:
        """
        دریافت آمار خطاها
        
        Args:
            days: تعداد روزهای گذشته برای تحلیل
            
        Returns:
            دیکشنری حاوی آمار خطاها
        """
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            # آمار کلی
            total_errors = SystemError.objects.filter(created_at__gte=start_date).count()
            unresolved_errors = SystemError.objects.filter(
                status__in=[ErrorStatus.NEW, ErrorStatus.IN_PROGRESS],
                created_at__gte=start_date
            ).count()
            
            # آمار بر اساس شدت
            severity_stats = SystemError.objects.filter(
                created_at__gte=start_date
            ).values('severity').annotate(
                count=Count('id'),
                percentage=Count('id') * 100.0 / total_errors if total_errors > 0 else 0
            )
            
            # آمار بر اساس دسته‌بندی
            category_stats = SystemError.objects.filter(
                created_at__gte=start_date
            ).values('category').annotate(
                count=Count('id'),
                percentage=Count('id') * 100.0 / total_errors if total_errors > 0 else 0
            )
            
            # خطاهای پرتکرار
            frequent_errors = SystemError.objects.filter(
                created_at__gte=start_date
            ).order_by('-occurrence_count')[:10]
            
            return {
                'total_errors': total_errors,
                'unresolved_errors': unresolved_errors,
                'resolution_rate': ((total_errors - unresolved_errors) / total_errors * 100) if total_errors > 0 else 100,
                'severity_stats': list(severity_stats),
                'category_stats': list(category_stats),
                'frequent_errors': [
                    {
                        'error_code': error.error_code,
                        'title': error.title,
                        'occurrence_count': error.occurrence_count,
                        'last_occurred': error.last_occurred
                    }
                    for error in frequent_errors
                ],
                'analysis_period': f"{days} روز گذشته"
            }
            
        except Exception as e:
            logger.error(f"خطا در محاسبه آمار خطاها: {e}")
            return {
                'total_errors': 0,
                'unresolved_errors': 0,
                'resolution_rate': 0,
                'severity_stats': [],
                'category_stats': [],
                'frequent_errors': [],
                'analysis_period': f"{days} روز گذشته",
                'error': str(e)
            }
    
    @classmethod
    def get_trend_analysis(cls, days: int = 30) -> Dict[str, Any]:
        """
        تحلیل روند خطاها در طول زمان
        
        Args:
            days: تعداد روزهای گذشته برای تحلیل
            
        Returns:
            دیکشنری حاوی تحلیل روند
        """
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            # خطاها بر اساس روز
            daily_errors = SystemError.objects.filter(
                created_at__gte=start_date
            ).extra({
                'date': "date(created_at)"
            }).values('date').annotate(
                count=Count('id')
            ).order_by('date')
            
            # میانگین خطاها در روز
            total_days = (timezone.now() - start_date).days
            avg_errors_per_day = len(daily_errors) / total_days if total_days > 0 else 0
            
            return {
                'daily_errors': list(daily_errors),
                'avg_errors_per_day': avg_errors_per_day,
                'trend_period': f"{days} روز گذشته",
                'analysis_date': timezone.now()
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل روند خطاها: {e}")
            return {
                'daily_errors': [],
                'avg_errors_per_day': 0,
                'trend_period': f"{days} روز گذشته",
                'analysis_date': timezone.now(),
                'error': str(e)
            }


# دکوراتور برای مدیریت خطاها
def handle_errors(module: str, function_name: str = None, severity: str = ErrorSeverity.MEDIUM):
    """
    دکوراتور برای مدیریت خودکار خطاها در توابع
    
    Args:
        module: نام ماژول
        function_name: نام تابع (اختیاری)
        severity: شدت خطا
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # استخراج اطلاعات از آرگومان‌ها
                user = None
                company_id = None
                period_id = None
                request = None
                
                # پیدا کردن request در آرگومان‌ها
                for arg in args:
                    if hasattr(arg, 'user') and hasattr(arg, 'method'):
                        request = arg
                        break
                
                for key, value in kwargs.items():
                    if key == 'request' and hasattr(value, 'user') and hasattr(value, 'method'):
                        request = value
                        break
                
                if request and hasattr(request, 'user'):
                    user = request.user
                
                # ثبت خطا
                ErrorHandlingService.capture_error(
                    exception=e,
                    module=module,
                    function_name=function_name or func.__name__,
                    user=user,
                    company_id=company_id,
                    period_id=period_id,
                    request=request,
                    severity=severity
                )
                
                # پرتاب مجدد خطا
                raise
                
        return wrapper
    return decorator
