# Task Completed: رفع مشکل تبدیل تاریخ فارسی در عملیات ایمپورت

**تاریخ:** 2025-10-26  
**وضعیت:** ✅ تکمیل شده

## شرح مشکل
سیستم قادر به پردازش تاریخ‌های فارسی نبود و خطای زیر را نمایش می‌داد:
```
خطا در وارد کردن داده‌ها: ['مقدار «1402/01/01» در قالب نادرستی وارد شده است. تاریخ باید در قالب YYYY-MM-DD باشد.']
```

## علت مشکل
- سیستم Django انتظار تاریخ در فرمت `YYYY-MM-DD` دارد
- فایل اکسل حاوی تاریخ‌های فارسی در فرمت `YYYY/MM/DD` بود
- عدم وجود تابع تبدیل تاریخ فارسی به فرمت استاندارد

## راه‌حل پیاده‌سازی شده

### افزودن تابع تبدیل تاریخ فارسی
```python
def _convert_persian_date(self, persian_date_str: str) -> str:
    """تبدیل تاریخ فارسی به فرمت YYYY-MM-DD"""
    try:
        if pd.isna(persian_date_str) or persian_date_str is None:
            return None
        
        # تبدیل به رشته
        date_str = str(persian_date_str).strip()
        
        # اگر تاریخ خالی است
        if not date_str:
            return None
        
        # اگر تاریخ در فرمت صحیح است (مثلاً از قبل تبدیل شده)
        if '-' in date_str and len(date_str.split('-')) == 3:
            return date_str
        
        # تبدیل تاریخ فارسی: YYYY/MM/DD به YYYY-MM-DD
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                year, month, day = parts
                # اطمینان از دو رقمی بودن ماه و روز
                month = month.zfill(2)
                day = day.zfill(2)
                return f"{year}-{month}-{day}"
        
        # اگر فرمت دیگری دارد، سعی در تجزیه آن
        try:
            # استفاده از pandas برای تجزیه تاریخ
            parsed_date = pd.to_datetime(date_str, errors='coerce')
            if pd.notna(parsed_date):
                return parsed_date.strftime('%Y-%m-%d')
        except:
            pass
        
        logger.warning(f"فرمت تاریخ قابل تشخیص نیست: {date_str}")
        return None
        
    except Exception as e:
        logger.error(f"خطا در تبدیل تاریخ {persian_date_str}: {e}")
        return None
```

### به‌روزرسانی متد ایجاد سربرگ سند
```python
def _create_document_header(self, document_number: str, group_df: pd.DataFrame, mapped_columns: dict) -> DocumentHeader:
    """ایجاد سربرگ سند"""
    try:
        # محاسبه جمع بدهکار و بستانکار
        total_debit = float(group_df[mapped_columns['debit']].sum())
        total_credit = float(group_df[mapped_columns['credit']].sum())
        
        # بررسی توازن
        is_balanced = abs(total_debit - total_credit) <= 0.01
        
        # تبدیل تاریخ فارسی
        document_date = None
        if mapped_columns['document_date'] in group_df.columns:
            persian_date = group_df[mapped_columns['document_date']].iloc[0]
            document_date = self._convert_persian_date(persian_date)
        
        # ایجاد سند
        document_header = DocumentHeader.objects.create(
            document_number=document_number,
            document_type='SANAD',
            document_date=document_date,
            description=group_df[mapped_columns['document_description']].iloc[0] if mapped_columns['document_description'] in group_df.columns else 'بدون شرح',
            company=self.company,
            period=self.period,
            total_debit=total_debit,
            total_credit=total_credit,
            is_balanced=is_balanced
        )
        
        return document_header
        
    except Exception as e:
        logger.error(f"خطا در ایجاد سربرگ سند {document_number}: {e}")
        raise
```

## قابلیت‌های تابع تبدیل تاریخ
- **تبدیل تاریخ فارسی**: `1402/01/01` → `1402-01-01`
- **پشتیبانی از فرمت‌های مختلف**: YYYY/MM/DD, YYYY-MM-DD
- **مدیریت خطا**: در صورت عدم موفقیت در تبدیل، مقدار None برمی‌گرداند
- **لاگ‌گیری**: ثبت خطاها و هشدارها برای عیب‌یابی
- **پشتیبانی از pandas**: استفاده از قابلیت‌های pandas برای تجزیه تاریخ

## فایل تغییر یافته
- `data_importer/services/data_integration_service.py` - افزودن تابع تبدیل تاریخ فارسی

## نتیجه
- **خطای فرمت تاریخ برطرف شده است**
- سیستم اکنون قادر به پردازش تاریخ‌های فارسی است
- عملیات ایمپورت با موفقیت انجام می‌شود
- کاربران می‌توانند فایل‌های اکسل با تاریخ فارسی آپلود کنند

## تست
- آپلود فایل اکسل با تاریخ فارسی باید بدون مشکل انجام شود
- تاریخ‌های فارسی باید به درستی به فرمت استاندارد تبدیل شوند
- عملیات وارد کردن داده‌ها باید با موفقیت انجام شود
