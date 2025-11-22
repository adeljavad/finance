from django.apps import AppConfig


class OptimizationConfig(AppConfig):
    """پیکربندی اپلیکیشن بهینه‌سازی عملکرد"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'financial_system.optimization'
    verbose_name = 'بهینه‌سازی عملکرد'
    
    def ready(self):
        """فعال کردن تنظیمات هنگام راه‌اندازی اپلیکیشن"""
        try:
            from .services import CacheService
            # راه‌اندازی سرویس کش
            CacheService.initialize()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"خطا در راه‌اندازی سیستم بهینه‌سازی: {e}")
