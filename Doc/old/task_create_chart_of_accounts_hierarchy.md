# تسک: ایجاد سلسله مراتب کامل حساب‌ها از فایل اکسل

## مشکل شناسایی شده
جدول `financial_system_chartofaccounts` خالی است زیرا متد فعلی فقط برای هر ردیف جداگانه کار می‌کند و سطوح کدینگ را به درستی ایجاد نمی‌کند.

## راه‌حل پیشنهادی
ایجاد یک متد جدید که تمام سطوح کدینگ را از فایل اکسل استخراج و در جدول ذخیره کند.

## مراحل پیاده‌سازی

### 1. ایجاد متد جدید در DataIntegrationService

```python
def create_complete_chart_of_accounts_hierarchy(self, df: pd.DataFrame) -> dict:
    """ایجاد سلسله مراتب کامل حساب‌ها از تمام داده‌های اکسل"""
```

### 2. استخراج سطوح مختلف

#### سطح 1: گروه (CLASS)
- پیدا کردن تمام `Code1, Title1` متمایز
- ایجاد حساب‌های سطح CLASS

#### سطح 2: کل (SUBCLASS)  
- پیدا کردن تمام `Code2, Title2` متمایز
- پیدا کردن والد مناسب بر اساس `Code1`
- ایجاد حساب‌های سطح SUBCLASS

#### سطح 3: معین (DETAIL)
- پیدا کردن تمام `Code3, Title3` متمایز
- پیدا کردن والد مناسب بر اساس `Code2`
- ایجاد حساب‌های سطح DETAIL

#### سطح 4: تفصیلی (DETAIL)
- پیدا کردن تمام `Code4, Title4` متمایز
- پیدا کردن والد مناسب بر اساس `Code3`
- ایجاد حساب‌های سطح DETAIL

### 3. الگوریتم پیاده‌سازی

```python
def create_complete_chart_of_accounts_hierarchy(self, df: pd.DataFrame) -> dict:
    results = {
        'created_levels': {
            'CLASS': 0,
            'SUBCLASS': 0, 
            'DETAIL': 0
        },
        'errors': []
    }
    
    try:
        # 1. استخراج سطوح CLASS (Code1, Title1)
        level1_accounts = self._extract_level1_accounts(df)
        
        # 2. استخراج سطوح SUBCLASS (Code2, Title2) با والد مناسب
        level2_accounts = self._extract_level2_accounts(df, level1_accounts)
        
        # 3. استخراج سطوح DETAIL (Code3, Title3) با والد مناسب  
        level3_accounts = self._extract_level3_accounts(df, level2_accounts)
        
        # 4. استخراج سطوح DETAIL (Code4, Title4) با والد مناسب
        level4_accounts = self._extract_level4_accounts(df, level3_accounts)
        
        return results
        
    except Exception as e:
        results['errors'].append(str(e))
        return results
```

### 4. متدهای کمکی

#### `_extract_level1_accounts(df)`
- پیدا کردن تمام `Code1, Title1` متمایز
- ایجاد حساب‌های سطح CLASS

#### `_extract_level2_accounts(df, level1_accounts)`
- پیدا کردن تمام `Code2, Title2` متمایز
- پیدا کردن والد مناسب بر اساس `Code1`
- ایجاد حساب‌های سطح SUBCLASS

#### `_extract_level3_accounts(df, level2_accounts)`
- پیدا کردن تمام `Code3, Title3` متمایز
- پیدا کردن والد مناسب بر اساس `Code2`
- ایجاد حساب‌های سطح DETAIL

#### `_extract_level4_accounts(df, level3_accounts)`
- پیدا کردن تمام `Code4, Title4` متمایز
- پیدا کردن والد مناسب بر اساس `Code3`
- ایجاد حساب‌های سطح DETAIL

### 5. یکپارچه‌سازی با جریان ایمپورت

```python
def process_import(self, delete_existing_data: bool = False) -> dict:
    # مرحله 0: حذف داده‌های قبلی
    # مرحله 1: خواندن داده‌ها
    # مرحله 2: اعتبارسنجی
    # مرحله 3: ایجاد سلسله مراتب کامل حساب‌ها  <-- جدید
    # مرحله 4: ایجاد اسناد
    # مرحله 5: تکمیل
```

## ساختار داده‌های مورد انتظار

### ستون‌های مورد نیاز در فایل اکسل:
- `Title1`, `Code1` - سطح گروه (CLASS)
- `Title2`, `Code2` - سطح کل (SUBCLASS)  
- `Title3`, `Code3` - سطح معین (DETAIL)
- `Title4`, `Code4` - سطح تفصیلی (DETAIL)

### مثال ساختار:
```
Title1      Code1  Title2           Code2  Title3   Code3  Title4        Code4
دارایی‌ها   1      دارایی‌های جاری  11     صندوق    111    صندوق اصلی    11101
دارایی‌ها   1      دارایی‌های جاری  11     بانک     112    بانک ملی      11201
```

## تست و اعتبارسنجی

### تست 1: استخراج سطوح CLASS
- ورودی: DataFrame با چندین ردیف
- خروجی: لیست متمایز `Code1, Title1`
- انتظار: ایجاد حساب‌های سطح CLASS

### تست 2: استخراج سطوح SUBCLASS
- ورودی: DataFrame + حساب‌های سطح CLASS
- خروجی: لیست متمایز `Code2, Title2` با والد مناسب
- انتظار: ایجاد حساب‌های سطح SUBCLASS

### تست 3: استخراج سطوح DETAIL
- ورودی: DataFrame + حساب‌های سطح SUBCLASS
- خروجی: لیست متمایز `Code3, Title3` با والد مناسب
- انتظار: ایجاد حساب‌های سطح DETAIL

### تست 4: استخراج سطوح تفصیلی
- ورودی: DataFrame + حساب‌های سطح DETAIL
- خروجی: لیست متمایز `Code4, Title4` با والد مناسب
- انتظار: ایجاد حساب‌های سطح DETAIL

## نتیجه مورد انتظار
پس از پیاده‌سازی، جدول `financial_system_chartofaccounts` باید با تمام سطوح کدینگ پر شود:
- سطح CLASS: گروه‌های اصلی (دارایی‌ها، بدهی‌ها، سرمایه، درآمد، هزینه)
- سطح SUBCLASS: کل‌های هر گروه
- سطح DETAIL: معین‌های هر کل
- سطح DETAIL: تفصیلی‌های هر معین
