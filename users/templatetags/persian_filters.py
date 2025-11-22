from django import template
import jdatetime
from datetime import datetime

register = template.Library()

@register.filter
def to_persian_date(value, format_string="Y/m/d"):
    """
    تبدیل تاریخ میلادی به تاریخ فارسی (شمسی)
    
    پارامترها:
    value: تاریخ میلادی (datetime, date, یا رشته قابل تبدیل)
    format_string: فرمت خروجی (پیش‌فرض: Y/m/d)
    
    فرمت‌های قابل استفاده:
    Y: سال چهار رقمی (۱۴۰۳)
    y: سال دو رقمی (۰۳)
    m: ماه دو رقمی (۰۸)
    n: ماه یک رقمی (۸)
    d: روز دو رقمی (۰۳)
    j: روز یک رقمی (۳)
    """
    if not value:
        return ""
    
    try:
        # اگر رشته است، ابتدا به datetime تبدیل کن
        if isinstance(value, str):
            # فرمت‌های مختلف تاریخ
            formats_to_try = [
                '%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d',
                '%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S',
                '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y'
            ]
            
            for fmt in formats_to_try:
                try:
                    value = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue
            
            # اگر هنوز رشته است و نتوانستیم تبدیل کنیم
            if isinstance(value, str):
                return value
        
        # تبدیل به تاریخ فارسی
        if hasattr(value, 'year'):
            persian_date = jdatetime.datetime.fromgregorian(
                year=value.year,
                month=value.month,
                day=value.day,
                hour=getattr(value, 'hour', 0),
                minute=getattr(value, 'minute', 0),
                second=getattr(value, 'second', 0)
            )
        else:
            return value
        
        # فرمت‌دهی تاریخ فارسی
        if format_string == "Y/m/d":
            return f"{persian_date.year:04d}/{persian_date.month:02d}/{persian_date.day:02d}"
        elif format_string == "y/m/d":
            return f"{persian_date.year % 100:02d}/{persian_date.month:02d}/{persian_date.day:02d}"
        else:
            return persian_date.strftime(format_string)
            
    except Exception as e:
        # در صورت خطا، مقدار اصلی برگردانده شود
        return str(value)

@register.filter
def to_persian_number(value):
    """
    تبدیل اعداد انگلیسی به فارسی
    """
    if value is None:
        return ""
    
    persian_numbers = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }
    
    value_str = str(value)
    for eng, per in persian_numbers.items():
        value_str = value_str.replace(eng, per)
    
    return value_str

@register.filter
def persian_date_format(value, format_type="short"):
    """
    فرمت‌های مختلف تاریخ فارسی
    """
    if not value:
        return ""
    
    try:
        if hasattr(value, 'year'):
            persian_date = jdatetime.datetime.fromgregorian(
                year=value.year,
                month=value.month,
                day=value.day
            )
        else:
            return value
        
        if format_type == "short":
            return f"{persian_date.year:04d}/{persian_date.month:02d}/{persian_date.day:02d}"
        elif format_type == "long":
            month_names = {
                1: 'فروردین', 2: 'اردیبهشت', 3: 'خرداد',
                4: 'تیر', 5: 'مرداد', 6: 'شهریور',
                7: 'مهر', 8: 'آبان', 9: 'آذر',
                10: 'دی', 11: 'بهمن', 12: 'اسفند'
            }
            return f"{persian_date.day} {month_names[persian_date.month]} {persian_date.year}"
        elif format_type == "numeric":
            return f"{persian_date.year:04d}{persian_date.month:02d}{persian_date.day:02d}"
        else:
            return f"{persian_date.year:04d}/{persian_date.month:02d}/{persian_date.day:02d}"
            
    except Exception as e:
        return str(value)

@register.simple_tag
def current_persian_date(format_string="Y/m/d"):
    """
    دریافت تاریخ جاری به فارسی
    """
    now = jdatetime.datetime.now()
    if format_string == "Y/m/d":
        return f"{now.year:04d}/{now.month:02d}/{now.day:02d}"
    else:
        return now.strftime(format_string)
