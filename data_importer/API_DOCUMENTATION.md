# مستندات API سیستم Data Importer پیشرفته

## 📋 معرفی

سیستم Data Importer پیشرفته با قابلیت‌های جدید زیر:

### ✅ ویژگی‌های اصلی:
1. **پشتیبانی از دو مدل ایمپورت** در یک ویو واحد
2. **شناسایی سلسله‌مراتبی حساب‌ها** (کل/معین/تفصیلی)
3. **تبدیل خودکار کدینگ** به استاندارد سیستم
4. **تحلیل بدون ذخیره** برای پیش‌نمایش
5. **اعتبارسنجی هوشمند** ساختار داده‌ها

---

## 🚀 APIهای جدید

### ۱. آپلود فایل با پشتیبانی از دو مدل

**Endpoint:** `POST /api/flexible-upload/`

#### پارامترهای ورودی:
```json
{
  "excel_file": "فایل اکسل (اجباری)",
  "company_id": "شناسه شرکت (اختیاری)",
  "financial_period_id": "شناسه دوره مالی (اختیاری)",
  "main_account_code_column": "نام ستون کد کل (اختیاری)",
  "main_account_name_column": "نام ستون نام کل (اختیاری)",
  "sub_account_code_column": "نام ستون کد معین (اختیاری)",
  "sub_account_name_column": "نام ستون نام معین (اختیاری)",
  "detail_account_code_column": "نام ستون کد تفصیلی (اختیاری)",
  "detail_account_name_column": "نام ستون نام تفصیلی (اختیاری)"
}
```

#### دو مدل عملکرد:

##### مدل A: با context شرکت و دوره مالی
- **شرایط:** ارسال `company_id` و `financial_period_id`
- **عملکرد:** 
  - ذخیره فایل در دیتابیس
  - تحلیل ساختار سلسله‌مراتبی
  - تبدیل کدینگ به استاندارد
  - ذخیره داده‌های خام در `RawFinancialData`

##### مدل B: عمومی بدون context
- **شرایط:** عدم ارسال `company_id` و `financial_period_id`
- **عملکرد:**
  - تحلیل ساختار بدون ذخیره
  - برگرداندن نمونه داده‌ها
  - اعتبارسنجی ساختار

#### پاسخ موفق (مدل A):
```json
{
  "success": true,
  "file_id": 123,
  "analysis": {...},
  "raw_data_count": 1500,
  "model_type": "WITH_CONTEXT",
  "message": "فایل با موفقیت آپلود و تحلیل شد"
}
```

#### پاسخ موفق (مدل B):
```json
{
  "success": true,
  "analysis": {...},
  "sample_data": [...],
  "model_type": "GENERIC",
  "message": "فایل با موفقیت تحلیل شد (بدون ذخیره دیتابیس)"
}
```

---

### ۲. تحلیل بدون ذخیره

**Endpoint:** `POST /api/analyze-only/`

#### پارامترهای ورودی:
```json
{
  "excel_file": "فایل اکسل (اجباری)"
}
```

#### پاسخ:
```json
{
  "success": true,
  "analysis": {
    "hierarchical_mapping": {...},
    "hierarchy_analysis": {
      "levels_detected": 3,
      "hierarchy_depth": 3,
      "account_distribution": {...},
      "hierarchy_quality": "EXCELLENT"
    },
    "has_hierarchy": true
  },
  "validation": {
    "valid": true,
    "issues": [],
    "warnings": [],
    "recommendations": []
  },
  "sample_data": [...],
  "total_rows": 1500,
  "message": "فایل با موفقیت تحلیل شد"
}
```

---

## 🏗️ مدل‌های جدید

### ۱. `RawFinancialData`
```python
# داده‌های خام با ساختار سلسله‌مراتبی
class RawFinancialData(models.Model):
    financial_file = ForeignKey(FinancialFile)
    
    # سلسله مراتب حساب
    main_account_code = CharField()
    main_account_name = CharField()
    sub_account_code = CharField()
    sub_account_name = CharField()
    detail_account_code = CharField()
    detail_account_name = CharField()
    
    # اطلاعات سند
    document_number = CharField()
    document_date = DateField()
    description = TextField()
    
    # مقادیر مالی
    debit_amount = DecimalField()
    credit_amount = DecimalField()
    
    # کدهای استاندارد
    standard_main_code = CharField()
    standard_main_name = CharField()
    standard_sub_code = CharField()
    standard_sub_name = CharField()
    standard_detail_code = CharField()
    standard_detail_name = CharField()
```

### ۲. `StandardAccountChart`
```python
# چارت حساب استاندارد سیستم
class StandardAccountChart(models.Model):
    standard_code = CharField(unique=True)
    standard_name = CharField()
    account_type = ChoiceField(choices=ACCOUNT_TYPES)
    level = IntegerField(choices=LEVEL_CHOICES)
    parent = ForeignKey('self')
    is_active = BooleanField(default=True)
```

### ۳. `CompanyAccountMapping`
```python
# نگاشت کدهای شرکت به کد استاندارد
class CompanyAccountMapping(models.Model):
    company = ForeignKey('users.Company')
    
    # کد شرکت
    company_main_code = CharField()
    company_main_name = CharField()
    company_sub_code = CharField()
    company_sub_name = CharField()
    company_detail_code = CharField()
    company_detail_name = CharField()
    
    # کد استاندارد
    standard_main_code = ForeignKey(StandardAccountChart)
    standard_sub_code = ForeignKey(StandardAccountChart)
    standard_detail_code = ForeignKey(StandardAccountChart)
    
    # وضعیت
    is_active = BooleanField(default=True)
    confidence_score = FloatField()
    mapping_type = ChoiceField(choices=MAPPING_TYPES)
```

---

## 🔧 سرویس‌های جدید

### ۱. `AccountMappingService`
```python
class AccountMappingService:
    @classmethod
    def map_to_standard(cls, company_id, company_codes):
        """تبدیل کدهای شرکت به کد استاندارد"""
    
    @classmethod
    def bulk_map_to_standard(cls, company_id, company_codes_list):
        """تبدیل دسته‌ای کدهای شرکت"""
    
    @classmethod
    def create_mapping(cls, company_id, company_codes, standard_codes, user_id):
        """ایجاد mapping جدید"""
    
    @classmethod
    def get_mapping_stats(cls, company_id):
        """دریافت آمار mappingهای یک شرکت"""
```

### ۲. `HierarchicalExcelAnalyzer`
```python
class HierarchicalExcelAnalyzer(ExcelStructureAnalyzer):
    def analyze_hierarchical_structure(self, file_path):
        """تحلیل ساختار سلسله‌مراتبی"""
    
    def extract_hierarchical_data(self, file_path, mapping=None):
        """استخراج داده‌های سلسله‌مراتبی"""
    
    def validate_hierarchy(self, file_path):
        """اعتبارسنجی سلسله‌مراتب داده‌ها"""
```

---

## 🔄 تغییرات در اپ financial_system

### ۱. یکپارچه‌سازی با Data Importer
```python
# financial_system/services/__init__.py
from data_importer.services.account_mapping_service import AccountMappingService
from data_importer.analyzers.hierarchical_excel_analyzer import HierarchicalExcelAnalyzer

class FinancialDataService:
    @staticmethod
    def import_financial_data(file_path, company_id, period_id, user_id):
        """وارد کردن داده‌های مالی با استفاده از سیستم data_importer"""
```

### ۲. APIهای جدید در financial_system
```
POST   /financial-system/api/import-with-mapping/    # ایمپورت با mapping خودکار
GET    /financial-system/api/mapping-stats/          # آمار mappingها
POST   /financial-system/api/bulk-mapping-import/    # وارد کردن دسته‌ای mapping
```

---

## 🧪 تست‌های نمونه

### ۱. تست آپلود فایل
```python
# test_api_upload.py
import requests

# مدل A: با context
files = {'excel_file': open('test.xlsx', 'rb')}
data = {
    'company_id': 1,
    'financial_period_id': 1
}
response = requests.post('http://localhost:8000/api/flexible-upload/', files=files, data=data)

# مدل B: بدون context
files = {'excel_file': open('test.xlsx', 'rb')}
response = requests.post('http://localhost:8000/api/flexible-upload/', files=files)
```

### ۲. تست تحلیل بدون ذخیره
```python
files = {'excel_file': open('test.xlsx', 'rb')}
response = requests.post('http://localhost:8000/api/analyze-only/', files=files)
```

---

## 📊 وضعیت فعلی

### ✅ کارهای انجام شده:
1. **مدل‌های جدید** ایجاد و migrations اعمال شده
2. **سرویس AccountMappingService** پیاده‌سازی شده
3. **تحلیل‌گر HierarchicalExcelAnalyzer** ایجاد شده
4. **ویو FlexibleFileUploadView** با پشتیبانی از دو مدل
5. **ویو AnalyzeOnlyView** برای تحلیل بدون ذخیره
6. **Serializers جدید** برای مدل‌های جدید
7. **URLهای API** اضافه شده
8. **مستندات کامل** ایجاد شده

### ⏳ کارهای در انتظار:
1. **ایجاد تست‌های واحد** برای سرویس‌های جدید
2. **یکپارچه‌سازی با frontend**
3. **ایجاد رابط کاربری** برای مدیریت mappingها
4. **بهینه‌سازی performance** برای فایل‌های بزرگ
5. **افزودن قابلیت bulk import** برای mappingها

---

## 🔗 منابع

1. **فایل تحلیل:** `data_importer/ANALYSIS_SUMMARY.md`
2. **طرح اجرایی:** `data_importer/IMPLEMENTATION_PLAN.md`
3. **کد سرویس:** `data_importer/services/account_mapping_service.py`
4. **کد تحلیل‌گر:** `data_importer/analyzers/hierarchical_excel_analyzer.py`
5. **کد ویوها:** `data_importer/api_views/flexible_upload.py`
6. **کد serializers:** `data_importer/serializers.py`
7. **کد URLs:** `data_importer/urls.py`

---

## 📞 پشتیبانی

برای گزارش مشکلات یا پیشنهادات:
1. **ایجاد Issue** در مخزن GitHub
2. **ارسال ایمیل** به تیم توسعه
3. **مستندات API** در Swagger UI (در حال توسعه)

---

**آخرین به‌روزرسانی:** ۱۴۰۴/۱۰/۰۳  
**نسخه:** ۲.۰.۰  
**وضعیت:** آماده برای تست‌های یکپارچه‌سازی
