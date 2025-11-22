# Task Completed: رفع مشکل اسناد تکراری در عملیات ایمپورت

**تاریخ:** 2025-10-26  
**وضعیت:** ✅ تکمیل شده

## شرح مشکل
سیستم با خطای زیر در هنگام ایمپورت داده‌ها مواجه می‌شد:
```
خطا در وارد کردن داده‌ها: ('23000', "[23000] [Microsoft][ODBC Driver 17 for SQL Server][SQL Server]Cannot insert duplicate key row in object 'dbo.financial_system_documentheader' with unique index 'financial_system_documentheader_company_id_period_id_document_number_83121727_uniq'. The duplicate key value is (1, 1, 1002). (2601) (SQLExecDirectW)")
```

## علت مشکل
- سیستم دارای محدودیت `unique_together` برای فیلدهای `(company, period, document_number)` است
- فایل اکسل حاوی اسناد تکراری بود
- عدم وجود منطق مدیریت اسناد تکراری در سرویس یکپارچه‌سازی

## راه‌حل پیاده‌سازی شده

### افزودن منطق مدیریت اسناد تکراری
```python
def create_documents_from_dataframe(self, df: pd.DataFrame) -> dict:
    """ایجاد اسناد مالی از داده‌های DataFrame"""
    created_documents = 0
    created_items = 0
    duplicate_documents = 0
    errors = []
    
    try:
        with transaction.atomic():
            # ...
            
            for document_number, group_df in grouped_data:
                try:
                    # بررسی وجود سند تکراری
                    existing_document = DocumentHeader.objects.filter(
                        company=self.company,
                        period=self.period,
                        document_number=document_number
                    ).first()
                    
                    if existing_document:
                        duplicate_documents += 1
                        logger.warning(f"سند تکراری نادیده گرفته شد: {document_number}")
                        continue
                    
                    # ایجاد سربرگ سند
                    document_header = self._create_document_header(document_number, group_df, mapped_columns)
                    created_documents += 1
                    
                    # ایجاد آرتیکل‌های سند
                    for index, row in group_df.iterrows():
                        self._create_document_item(document_header, row, index + 1, mapped_columns)
                        created_items += 1
                        
                except Exception as e:
                    errors.append(f"خطا در ایجاد سند {document_number}: {str(e)}")
                    logger.error(f"خطا در ایجاد سند {document_number}: {e}")
                    continue
            
            result = {
                'document_count': created_documents,
                'item_count': created_items,
                'duplicate_documents': duplicate_documents,
                'status': 'success'
            }
            
            if errors:
                result['warnings'] = errors
                result['status'] = 'partial_success'
            
            return result
```

## ویژگی‌های راه‌حل جدید

### 1. بررسی پیش‌گیرانه
- بررسی وجود سند تکراری قبل از ایجاد
- جلوگیری از خطای محدودیت دیتابیس

### 2. مدیریت خطا
- ثبت اسناد تکراری در لاگ
- ادامه عملیات برای سایر اسناد
- گزارش تعداد اسناد تکراری

### 3. گزارش‌دهی
- تعداد اسناد ایجاد شده
- تعداد آرتیکل‌های ایجاد شده  
- تعداد اسناد تکراری نادیده گرفته شده
- وضعیت عملیات (success/partial_success)

### 4. انعطاف‌پذیری
- عملیات ایمپورت حتی در صورت وجود اسناد تکراری ادامه می‌یابد
- کاربر از وضعیت عملیات مطلع می‌شود
- امکان ایمپورت مجدد فایل بدون حذف اسناد قبلی

## فایل تغییر یافته
- `data_importer/services/data_integration_service.py` - افزودن منطق مدیریت اسناد تکراری

## نتیجه
- **خطای اسناد تکراری به طور کامل برطرف شده است**
- سیستم اکنون اسناد تکراری را شناسایی و نادیده می‌گیرد
- عملیات ایمپورت حتی در صورت وجود اسناد تکراری ادامه می‌یابد
- کاربر از تعداد اسناد تکراری مطلع می‌شود

## تست
- آپلود فایل اکسل با اسناد تکراری باید بدون خطا انجام شود
- اسناد تکراری باید نادیده گرفته شوند
- سایر اسناد باید با موفقیت ایجاد شوند
- گزارش وضعیت باید شامل تعداد اسناد تکراری باشد
