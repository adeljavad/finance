from django.apps import AppConfig


class ErrorManagementConfig(AppConfig):
    """پیکربندی اپلیکیشن مدیریت خطا"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'financial_system.error_management'
    verbose_name = 'مدیریت خطاهای سیستم مالی'
    
    def ready(self):
        """فعال کردن سیگنال‌ها و تنظیمات هنگام راه‌اندازی اپلیکیشن"""
        try:
            from . import signals  # noqa
            from .services import ErrorMonitoringService
            # راه‌اندازی سرویس مانیتورینگ خطاها
            ErrorMonitoringService.initialize()
        except Exception as e:
            # استفاده از لاگ پایه برای جلوگیری از خطاهای دور
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"خطا در راه‌اندازی سیستم مدیریت خطا: {e}")
