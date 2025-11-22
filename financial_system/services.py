"""
سرویس‌های اصلی سیستم مالی هوشمند

این ماژول سرویس‌های اصلی سیستم را ارائه می‌دهد
"""

import logging
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class AlertService:
    """سرویس هشدار حداقلی"""
    
    @classmethod
    def send_simple_alert(cls, title: str, message: str, priority: str = 'MEDIUM', category: str = 'SYSTEM'):
        """
        ارسال هشدار ساده
        
        Args:
            title: عنوان هشدار
            message: پیام هشدار
            priority: اولویت (LOW, MEDIUM, HIGH, CRITICAL)
            category: دسته‌بندی (SYSTEM, FINANCIAL, SECURITY, PERFORMANCE)
        """
        try:
            # ثبت در لاگ سیستم
            logger.warning(f"هشدار {priority}: {title} - {message}")
            
            # ارسال ایمیل اگر تنظیمات ایمیل فعال باشد
            if hasattr(settings, 'EMAIL_BACKEND') and settings.EMAIL_BACKEND:
                cls._send_email_alert(title, message, priority, category)
            
            # ثبت در سیستم مدیریت خطا
            cls._log_to_error_management(title, message, priority, category)
            
            # ثبت در سیستم امنیتی
            cls._log_to_security_system(title, message, priority, category)
            
            return True
            
        except Exception as e:
            logger.error(f"خطا در ارسال هشدار: {e}")
            return False
    
    @classmethod
    def _send_email_alert(cls, title: str, message: str, priority: str, category: str):
        """ارسال هشدار از طریق ایمیل"""
        try:
            if not hasattr(settings, 'ALERT_EMAILS') or not settings.ALERT_EMAILS:
                return
            
            subject = f"[{priority}] {title}"
            full_message = f"""
            هشدار سیستم مالی:
            
            عنوان: {title}
            پیام: {message}
            اولویت: {priority}
            دسته‌بندی: {category}
            زمان: {timezone.now()}
            
            لطفاً در اسرع وقت بررسی نمایید.
            """
            
            send_mail(
                subject=subject,
                message=full_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=settings.ALERT_EMAILS,
                fail_silently=True,
            )
            
        except Exception as e:
            logger.error(f"خطا در ارسال ایمیل هشدار: {e}")
    
    @classmethod
    def _log_to_error_management(cls, title: str, message: str, priority: str, category: str):
        """ثبت هشدار در سیستم مدیریت خطا"""
        try:
            from financial_system.error_management.services import ErrorService
            
            error_data = {
                'alert_title': title,
                'alert_message': message,
                'alert_priority': priority,
                'alert_category': category,
                'is_alert': True
            }
            
            ErrorService.log_error(
                error_type='ALERT',
                error_message=f"هشدار {priority}: {title}",
                severity=cls._priority_to_severity(priority),
                additional_data=error_data
            )
            
        except Exception as e:
            logger.debug(f"سیستم مدیریت خطا در دسترس نیست: {e}")
    
    @classmethod
    def _log_to_security_system(cls, title: str, message: str, priority: str, category: str):
        """ثبت هشدار در سیستم امنیتی"""
        try:
            from financial_system.security.services import SecurityService, SecurityEventType, SecurityLevel
            
            event_type = cls._category_to_event_type(category)
            security_level = cls._priority_to_security_level(priority)
            
            SecurityService.log_security_event(
                event_type=event_type,
                description=f"هشدار: {title} - {message}",
                security_level=security_level,
                additional_data={
                    'alert_priority': priority,
                    'alert_category': category
                }
            )
            
        except Exception as e:
            logger.debug(f"سیستم امنیتی در دسترس نیست: {e}")
    
    @classmethod
    def _priority_to_severity(cls, priority: str) -> str:
        """تبدیل اولویت به شدت خطا"""
        priority_map = {
            'LOW': 'LOW',
            'MEDIUM': 'MEDIUM', 
            'HIGH': 'HIGH',
            'CRITICAL': 'CRITICAL'
        }
        return priority_map.get(priority, 'MEDIUM')
    
    @classmethod
    def _priority_to_security_level(cls, priority: str) -> str:
        """تبدیل اولویت به سطح امنیتی"""
        priority_map = {
            'LOW': 'LOW',
            'MEDIUM': 'MEDIUM',
            'HIGH': 'HIGH', 
            'CRITICAL': 'CRITICAL'
        }
        return priority_map.get(priority, 'MEDIUM')
    
    @classmethod
    def _category_to_event_type(cls, category: str) -> str:
        """تبدیل دسته‌بندی به نوع رویداد امنیتی"""
        category_map = {
            'SYSTEM': 'SYSTEM_ALERT',
            'FINANCIAL': 'FINANCIAL_ALERT',
            'SECURITY': 'SECURITY_ALERT',
            'PERFORMANCE': 'PERFORMANCE_ALERT'
        }
        return category_map.get(category, 'SYSTEM_ALERT')


class FinancialAlertService:
    """سرویس هشدارهای مالی خاص"""
    
    @classmethod
    def alert_low_balance(cls, account_name: str, current_balance: float, threshold: float):
        """هشدار موجودی کم"""
        title = f"موجودی کم حساب: {account_name}"
        message = f"موجودی حساب {account_name} به {current_balance:,.0f} رسیده که کمتر از آستانه {threshold:,.0f} است."
        
        AlertService.send_simple_alert(
            title=title,
            message=message,
            priority='HIGH',
            category='FINANCIAL'
        )
    
    @classmethod
    def alert_unusual_transaction(cls, transaction_amount: float, average_amount: float, account_name: str):
        """هشدار تراکنش غیرعادی"""
        ratio = transaction_amount / average_amount if average_amount > 0 else float('inf')
        
        title = f"تراکنش غیرعادی در حساب: {account_name}"
        message = f"تراکنش به مبلغ {transaction_amount:,.0f} شناسایی شد که {ratio:.1f} برابر میانگین ({average_amount:,.0f}) است."
        
        AlertService.send_simple_alert(
            title=title,
            message=message,
            priority='MEDIUM',
            category='FINANCIAL'
        )
    
    @classmethod
    def alert_data_import_issue(cls, file_name: str, issue_description: str):
        """هشدار مشکل در ایمپورت داده"""
        title = f"مشکل در ایمپورت فایل: {file_name}"
        message = f"خطا در پردازش فایل {file_name}: {issue_description}"
        
        AlertService.send_simple_alert(
            title=title,
            message=message,
            priority='MEDIUM',
            category='SYSTEM'
        )


class SystemAlertService:
    """سرویس هشدارهای سیستمی"""
    
    @classmethod
    def alert_high_memory_usage(cls, usage_percent: float, threshold: float = 80):
        """هشدار مصرف بالای حافظه"""
        title = "مصرف بالای حافظه سیستم"
        message = f"مصرف حافظه سیستم به {usage_percent:.1f}% رسیده که بیش از آستانه {threshold}% است."
        
        AlertService.send_simple_alert(
            title=title,
            message=message,
            priority='HIGH',
            category='PERFORMANCE'
        )
    
    @classmethod
    def alert_database_connection_issue(cls, error_message: str):
        """هشدار مشکل اتصال به دیتابیس"""
        title = "مشکل اتصال به پایگاه داده"
        message = f"خطا در اتصال به پایگاه داده: {error_message}"
        
        AlertService.send_simple_alert(
            title=title,
            message=message,
            priority='CRITICAL',
            category='SYSTEM'
        )
    
    @classmethod
    def alert_external_service_down(cls, service_name: str, error_message: str):
        """هشدار قطعی سرویس خارجی"""
        title = f"سرویس خارجی قطع: {service_name}"
        message = f"سرویس {service_name} در دسترس نیست: {error_message}"
        
        AlertService.send_simple_alert(
            title=title,
            message=message,
            priority='HIGH',
            category='SYSTEM'
        )
