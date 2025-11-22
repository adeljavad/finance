# تسک تکمیلی - رفع خطای SQL Server Constraint

## تاریخ
۲۵ مهر ۱۴۰۴

## موضوع
رفع خطای پایگاه داده SQL Server هنگام آپلود فایل اکسل

## مشکل
خطای زیر هنگام آپلود فایل اکسل:
```
خطا در پردازش فایل: ('23000', '[23000] [Microsoft][ODBC Driver 17 for SQL Server][SQL Server]The INSERT statement conflicted with the CHECK constraint "data_importer_financialfile_analysis_result_f829de1e_check". The conflict occurred in database "chatbot", table "dbo.data_importer_financialfile", column \'analysis_result\'. (547) (SQLParamData); [23000] [Microsoft][ODBC Driver 17 for SQL Server][SQL Server]The statement has been terminated. (3621)')
```

## علت مشکل
- فیلد `analysis_result` در مدل `FinancialFile` از نوع JSONField است
- SQL Server دارای CHECK constraint است که مقادیر نامعتبر JSON را رد می‌کند
- تحلیلگر فایل اکسل ممکن است `None` یا داده‌های نامعتبر برگرداند

## راه‌حل پیاده‌سازی شده

### ۱. بهبود ExcelStructureAnalyzer
- افزودن تابع `_ensure_valid_json` برای اطمینان از معتبر بودن تمام فیلدها
- افزودن تابع `_get_default_analysis_result` برای برگرداندن نتیجه پیش‌فرض در صورت خطا
- اطمینان از وجود تمام فیلدهای ضروری در نتیجه تحلیل
- تبدیل انواع داده به فرمت معتبر (str, float, list, dict)

### ۲. بهبود ویو آپلود
- افزودن بررسی‌های اضافی برای اطمینان از معتبر بودن داده‌های JSON
- تبدیل اجباری فیلدها به انواع معتبر قبل از ذخیره‌سازی
- مدیریت خطاهای احتمالی در تحلیل فایل

### ۳. تغییرات فنی

#### فایل‌های ویرایش شده
1. `data_importer/analyzers/excel_structure_analyzer.py`
   - افزودن مدیریت خطا و داده‌های پیش‌فرض
   - اطمینان از معتبر بودن JSON

2. `data_importer/views.py`
   - افزودن بررسی‌های اضافی برای داده‌های JSON
   - تبدیل اجباری انواع داده

## تست‌های انجام شده
- ✅ سرور بدون خطا اجرا می‌شود
- ✅ تحلیلگر فایل اکسل همیشه داده‌های معتبر برمی‌گرداند
- ✅ آپلود فایل اکسل بدون خطای constraint انجام می‌شود

## نتیجه
خطای SQL Server constraint به طور کامل رفع شده است. کاربران می‌توانند فایل‌های اکسل مالی را بدون مشکل آپلود کنند.

---
**توسعه‌دهنده**: سیستم هوشمند  
**تاریخ**: ۲۵ مهر ۱۴۰۴
