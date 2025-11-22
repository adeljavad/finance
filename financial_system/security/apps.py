from django.apps import AppConfig


class SecurityConfig(AppConfig):
    """پیکربندی اپلیکیشن امنیتی"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'financial_system.security'
    verbose_name = 'امنیت سیستم مالی'
    
    def ready(self):
        """فعال کردن سیگنال‌ها و تنظیمات هنگام راه‌اندازی اپلیکیشن"""
        try:
            from . import signals  # noqa
            from .services import SecurityService
            # راه‌اندازی سرویس امنیتی
            SecurityService.initialize()
        except Exception as e:
            # استفاده از لاگ پایه برای جلوگیری از خطاهای دور
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"خطا در راه‌اندازی سیستم امنیتی: {e}")
