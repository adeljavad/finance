# users/adapters.py (اختیاری - برای سفارشی‌سازی)
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings

class CustomAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        """
        تعیین اینکه آیا ثبت‌نام معمولی فعال باشد یا فقط از طریق شبکه‌های اجتماعی
        """
        return True  # تغییر به False اگر فقط می‌خواهید از Google استفاده کنید