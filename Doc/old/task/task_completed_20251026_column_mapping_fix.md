# Task Completed: رفع مشکل شناسایی ستون‌های ضروری در فایل اکسل

**تاریخ:** 2025-10-26  
**وضعیت:** ✅ تکمیل شده

## شرح مشکل
سیستم قادر به شناسایی ستون‌های ضروری در فایل اکسل نبود و خطای زیر را نمایش می‌داد:
```
خطا در وارد کردن داده‌ها: ستون‌های ضروری یافت نشد: شرح سند, کد حساب, شرح حساب
```

## علت مشکل
- سیستم فقط به دنبال نام‌های خاص ستون‌ها بود
- فایل اکسل کاربر دارای نام‌های ستون متفاوت بود:
  - `توضیحات` به جای `شرح سند`
  - `معین` به جای `کد حساب`  
  - `Title1`, `Title2` به جای `شرح حساب`
- منطق مپینگ ستون‌ها به اندازه کافی هوشمند نبود

## راه‌حل پیاده‌سازی شده

### 1. گسترش الگوهای ستون‌های استاندارد
```python
self.standard_columns = {
    'document_number': ['شماره سند', 'ش سند', 'سند', 'شماره', 'کد سند', 'شناسه سند'],
    'document_date': ['تاریخ سند', 'تاریخ', 'ت سند', 'تاریخ صدور'],
    'document_description': ['شرح سند', 'شرح', 'توضیحات', 'شرح عملیات', 'توضیحات', 'شرح به زبان انگلیسی'],
    'account_code': ['کد حساب', 'کد', 'حساب', 'کد معین', 'کد تفصیلی', 'معین', 'کد1', 'کد2', 'کد3', 'کد4'],
    'account_description': ['شرح حساب', 'شرح معین', 'شرح تفصیلی', 'نام حساب', 'title1', 'title2', 'title3', 'title4'],
    'debit': ['بدهکار', 'بده', 'مبلغ بدهکار', 'گردش بدهکار'],
    'credit': ['بستانکار', 'بستان', 'مبلغ بستانکار', 'گردش بستانکار'],
    # ...
}
```

### 2. پیاده‌سازی مپینگ هوشمند با اولویت‌بندی
```python
def _map_columns(self, columns: List[str]) -> Dict[str, str]:
    """مپینگ ستون‌ها به ستون‌های استاندارد"""
    mapping = {}
    used_columns = set()
    
    # اولویت‌بندی برای تطابق دقیق‌تر
    priority_mappings = [
        # تطابق دقیق
        lambda col, pattern: str(col).lower().strip() == pattern.lower(),
        # تطابق شامل
        lambda col, pattern: pattern.lower() in str(col).lower().strip(),
        # تطابق با حذف فاصله
        lambda col, pattern: pattern.lower().replace(' ', '') in str(col).lower().strip().replace(' ', ''),
        # تطابق با کلمات کلیدی
        lambda col, pattern: self._contains_keywords(str(col).lower().strip(), pattern.lower())
    ]
    
    # ...
```

### 3. افزودن مپینگ هوشمند برای ستون‌های خاص
```python
def _apply_smart_mapping(self, columns: List[str], mapping: Dict[str, str], used_columns: set):
    """اعمال مپینگ هوشمند برای ستون‌های خاص"""
    smart_patterns = {
        'document_description': ['توضیحات', 'شرح به زبان انگلیسی'],
        'account_code': ['معین', 'کد1', 'کد2', 'کد3', 'کد4'],
        'account_description': ['title1', 'title2', 'title3', 'title4']
    }
    
    for standard_col, patterns in smart_patterns.items():
        if standard_col not in mapping:
            for col in columns:
                if col in used_columns:
                    continue
                if any(pattern.lower() in str(col).lower() for pattern in patterns):
                    mapping[standard_col] = col
                    used_columns.add(col)
                    break
```

## فایل‌های تغییر یافته
- `data_importer/analyzers/excel_structure_analyzer.py` - بهبود منطق مپینگ ستون‌ها

## نتیجه
- سیستم اکنون قادر به شناسایی ستون‌های ضروری در فایل‌های اکسل با نام‌های مختلف است
- ستون `توضیحات` به عنوان `شرح سند` شناسایی می‌شود
- ستون `معین` به عنوان `کد حساب` شناسایی می‌شود  
- ستون‌های `Title1`, `Title2` به عنوان `شرح حساب` شناسایی می‌شوند
- خطای "ستون‌های ضروری یافت نشد" برطرف شده است

## تست
- آپلود فایل اکسل با نام‌های ستون متفاوت باید بدون مشکل انجام شود
- سیستم باید ستون‌های ضروری را به درستی شناسایی کند
- عملیات وارد کردن داده‌ها باید با موفقیت انجام شود
