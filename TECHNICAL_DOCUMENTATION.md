# مستندات فنی پروژه سیستم مالی هوشمند

## 📋 فهرست مطالب
1. [معماری سیستم](#معماری-سیستم)
2. [مدل‌های داده](#مدل‌های-داده)
3. [ابزارهای مالی](#ابزارهای-مالی)
4. [API‌ها و Endpoints](#apiها-و-endpoints)
5. [فرآیند ایمپورت Excel](#فرآیند-ایمپورت-excel)
6. [محاسبات مالی](#محاسبات-مالی)
7. [چالش‌های فنی](#چالش‌های-فنی)

---

## 🏗️ معماری سیستم

### ساختار کلی
```
financial_system/
├── core/           # هسته مرکزی
├── models/         # مدل‌های داده
├── tools/          # ابزارهای مالی
├── views/          # ویوهای Django
└── templates/      # قالب‌های HTML
```

### جریان داده
```
Excel File → data_importer → DocumentHeader/DocumentItem → financial_system → Chat API → User
```

---

## 💾 مدل‌های داده

### 1. DocumentHeader (سربرگ اسناد)
```python
class DocumentHeader(models.Model):
    document_number = CharField()      # شماره سند
    document_type = CharField()        # نوع سند (سند حسابداری، فاکتور، ...)
    document_date = CharField()        # تاریخ سند (رشته)
    description = TextField()          # شرح سند
    company = ForeignKey(Company)      # شرکت
    period = ForeignKey(FinancialPeriod) # دوره مالی
    total_debit = DecimalField()       # مجموع بدهکار
    total_credit = DecimalField()      # مجموع بستانکار
    is_balanced = BooleanField()       # وضعیت تراز
```

### 2. DocumentItem (آرتیکل‌های اسناد)
```python
class DocumentItem(models.Model):
    document = ForeignKey(DocumentHeader)  # سربرگ سند
    row_number = IntegerField()            # ردیف
    account = ForeignKey(ChartOfAccounts)  # حساب
    debit = DecimalField()                 # بدهکار
    credit = DecimalField()               # بستانکار
    description = TextField()             # شرح
    cost_center = CharField()             # مرکز هزینه
    project_code = CharField()            # کد پروژه
```

### 3. ChartOfAccounts (سرفصل حساب‌ها)
```python
class ChartOfAccounts(models.Model):
    code = CharField()        # کد حساب
    name = CharField()        # نام حساب
    level = CharField()       # سطح (کل/معین/تفصیلی/پروژه/مرکز هزینه)
    parent = ForeignKey('self') # حساب والد
    is_active = BooleanField() # وضعیت فعال
```

### 4. FinancialFile (فایل‌های Excel)
```python
class FinancialFile(models.Model):
    file_name = CharField()           # نام فایل
    company = ForeignKey(Company)     # شرکت
    financial_period = ForeignKey(FinancialPeriod) # دوره مالی
    software_type = CharField()       # نوع نرم‌افزار (همکاران، راهکاران، ...)
    status = CharField()              # وضعیت (آپلود شده، تحلیل شده، ...)
    columns_mapping = JSONField()     # نگاشت ستون‌ها
```

---

## 🛠️ ابزارهای مالی

### 1. generate_report (تولید گزارش)
**ورودی**: company_id, period_id, report_type
**خروجی**: گزارش مالی فرمت‌شده

**انواع گزارش**:
- `balance_sheet`: ترازنامه
- `income_statement`: صورت سود و زیان  
- `cash_flow`: صورت جریان نقدی

### 2. analyze_ratios (تحلیل نسبت‌ها)
**ورودی**: company_id, period_id
**خروجی**: نسبت‌های مالی محاسبه شده

**نسبت‌های محاسبه‌شده**:
- نسبت جاری = دارایی‌های جاری / بدهی‌های جاری
- نسبت آنی = (دارایی‌های جاری - موجودی) / بدهی‌های جاری
- بازده دارایی‌ها = سود خالص / میانگین دارایی‌ها
- بازده حقوق صاحبان سهام = سود خالص / میانگین حقوق صاحبان سهام

### 3. detect_anomalies (شناسایی انحرافات)
**ورودی**: company_id, period_id
**خروجی**: لیست انحرافات شناسایی شده

**انواع انحرافات**:
- اسناد نامتعادل (total_debit ≠ total_credit)
- حساب‌های با مانده منفی
- گردش‌های غیرعادی

### 4. compare_ratios (مقایسه نسبت‌ها)
**ورودی**: company_id, period1_id, period2_id, ratio_type
**خروجی**: جدول مقایسه و تحلیل تغییرات

### 5. analyze_trend (تحلیل روند)
**ورودی**: company_id, metric, periods
**خروجی**: تحلیل روند و پیش‌بینی

### 6. seasonal_analysis (تحلیل فصلی)
**ورودی**: company_id, period_id, season
**خروجی**: تحلیل عملکرد فصلی

### 7. four_column_balance (تراز چهارستونی)
**ورودی**: company_id, period_id, season
**خروجی**: تراز چهارستونی

### 8. comprehensive_report (گزارش جامع)
**ورودی**: company_id, period_id
**خروجی**: گزارش کامل مالی

---

## 🌐 API‌ها و Endpoints

### چت بات مالی
```
POST /financial/api/chat/
{
    "message": "سوال مالی کاربر"
}
```

**پاسخ**:
```json
{
    "answer": "پاسخ سیستم",
    "type": "financial_answer|general_answer|error",
    "is_financial": true|false
}
```

### تحلیل سریع
```
POST /financial/api/quick-analysis/
{
    "analysis_type": "balance_sheet|current_assets|..."
}
```

---

## 📊 فرآیند ایمپورت Excel

### مراحل پردازش:
1. **آپلود فایل** → `FinancialFile` ایجاد می‌شود
2. **تحلیل فایل** → شناسایی ساختار و نگاشت ستون‌ها
3. **اعتبارسنجی** → بررسی صحت داده‌ها
4. **ایمپورت** → ایجاد `DocumentHeader` و `DocumentItem`
5. **تکمیل** → بروزرسانی وضعیت فایل

### نگاشت ستون‌ها:
```json
{
    "document_number": "شماره سند",
    "document_date": "تاریخ سند", 
    "account_code": "کد حساب",
    "debit": "بدهکار",
    "credit": "بستانکار",
    "description": "شرح"
}
```

---

## 🧮 محاسبات مالی

### ترازنامه
```python
def calculate_balance_sheet(company_id, period_id):
    # جمع‌بندی حساب‌های دارایی
    total_assets = DocumentItem.objects.filter(
        document__company_id=company_id,
        document__period_id=period_id,
        account__code__startswith='1'  # حساب‌های دارایی
    ).aggregate(
        total=Sum('debit') - Sum('credit')
    )['total'] or 0

    # جمع‌بندی حساب‌های بدهی
    total_liabilities = DocumentItem.objects.filter(
        document__company_id=company_id,
        document__period_id=period_id, 
        account__code__startswith='2'  # حساب‌های بدهی
    ).aggregate(
        total=Sum('credit') - Sum('debit')
    )['total'] or 0

    # حقوق صاحبان سهام
    equity = total_assets - total_liabilities
    
    return {
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'equity': equity
    }
```

### نسبت‌های مالی
```python
def calculate_current_ratio(company_id, period_id):
    # دارایی‌های جاری (حساب‌های با کد 11xxx)
    current_assets = aggregate_accounts(company_id, period_id, '11')
    
    # بدهی‌های جاری (حساب‌های با کد 21xxx)  
    current_liabilities = aggregate_accounts(company_id, period_id, '21')
    
    return current_assets / current_liabilities if current_liabilities != 0 else 0
```

---

## ⚠️ چالش‌های فنی

### 1. ساختار سلسله‌مراتبی حساب‌ها
- نیاز به جمع‌بندی سطوح مختلف (کل → معین → تفصیلی)
- الگوریتم بازگشتی برای محاسبه مانده حساب‌ها

### 2. اعتبارسنجی داده‌ها
- بررسی تراز اسناد
- شناسایی حساب‌های نامعتبر
- کنترل یکپارچگی داده‌ها

### 3. کارایی
- بهینه‌سازی کوئری‌های دیتابیس
- کش‌گیری نتایج محاسبات
- پردازش دسته‌ای داده‌های حجیم

### 4. فرمت تاریخ
- تبدیل تاریخ‌های شمسی به میلادی برای محاسبات
- مدیریت فرمت‌های مختلف تاریخ

---

## 🔧 نکات فنی مهم

### 1. مدیریت Session
- نیاز به انتخاب شرکت و دوره مالی قبل از استفاده
- ذخیره در session برای دسترسی آسان

### 2. خطایابی
- لاگ‌گیری کامل فرآیندها
- مدیریت خطاهای محاسباتی
- پیام‌های خطای کاربرپسند

### 3. توسعه‌پذیری
- ساختار ماژولار برای اضافه کردن ابزارهای جدید
- API استاندارد برای تمام ابزارها
- مستندات کامل برای توسعه دهندگان

---

## 🚀 راهنمای توسعه

### اضافه کردن ابزار جدید:
1. ایجاد تابع در `financial_system/tools/`
2. اضافه کردن به `SimpleFinancialAgent._setup_tools()`
3. به‌روزرسانی منطق انتخاب ابزار در `_select_tool()`
4. تست کامل عملکرد

### فرمت تابع ابزار:
```python
def new_tool_tool(company_id: int, period_id: int, **kwargs) -> str:
    """شرح عملکرد ابزار"""
    # محاسبات و منطق
    return "نتیجه فرمت‌شده"
```

---

*آخرین به‌روزرسانی: ۱۴۰۴/۰۸/۰۷*
