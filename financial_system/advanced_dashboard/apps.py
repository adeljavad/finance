from django.apps import AppConfig


class AdvancedDashboardConfig(AppConfig):
    """پیکربندی اپلیکیشن داشبورد تحلیلی پیشرفته"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'financial_system.advanced_dashboard'
    verbose_name = 'داشبورد تحلیلی پیشرفته'
    
    def ready(self):
        """فعال کردن تنظیمات هنگام راه‌اندازی اپلیکیشن"""
        try:
            from .services import DashboardService
            # راه‌اندازی سرویس داشبورد
            DashboardService.initialize()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"خطا در راه‌اندازی سیستم داشبورد پیشرفته: {e}")
