# تحلیل جامع برای ساختار دیتابیس سیستم مالی و ورود اکسل

## 🎯 نیازمندی‌های اصلی شناسایی شده:

### ۱. **ساختار استاندارد اسناد حسابداری ایرانی**
### ۲. **سیستم کشف و تطبیق خودکار ستون‌های اکسل**
### ۳. **کنترل‌های یکپارچگی داده‌ها**
### ۴. **پردازش افزایشی (Incremental)**
### ۵. **مدیریت کدینگ سلسله مراتبی**

## 📋 تسک‌های جدید مورد نیاز (اضافه به ۱۴۰ تسک قبلی)

### **فاز ۲-الف: استانداردسازی ساختار داده‌های مالی** (تسک‌های ۱۴۱-۱۶۰)

```
141. **تحلیل ساختار خروجی اکسل نرم‌افزارهای همکاران سیستم، راهکاران، سپیدار**
142. **طراحی مدل استاندارد اسناد حسابداری ایرانی**
143. **ایجاد مدل DocumentHeader برای سربرگ اسناد**
144. **پیاده‌سازی مدل DocumentItem برای آرتیکل‌های سند**
145. **تعریف مدل CodingStructure برای کدینگ کل-معین-تفصیلی**
146. **ایجاد سیستم کشف خودکار ساختار اکسل (Auto-Detection)**
147. **پیاده‌سازی الگوریتم تطبیق ستون‌های اکسل با مدل‌های دیتابیس**
148. **ایجاد mapping table برای نگاشت فیلدهای مختلف نرم‌افزارها**
149. **پیاده‌سازی validator برای فرمت تاریخ‌های شمسی**
150. **ایجاد کنترل یکپارچگی ارزی (ریال، ارز)**
```

### **فاز ۲-ب: کنترل‌های یکپارچگی و پیش‌پردازش** (تسک‌های ۱۶۱-۱۸۰)

```
161. **پیاده‌سازی سیستم تشخیص اسناد تکراری**
162. **ایجاد کنترل توالی شماره اسناد**
163. **پیاده‌سازی کنترل وجود کدینگ قبل از درج سند**
164. **ایجاد سیستم مدیریت خطا در ورود داده**
165. **پیاده‌سازی گزارش خطاهای اعتبارسنجی**
166. **ایجاد queue system برای پردازش فایل‌های بزرگ**
167. **پیاده‌سازی rollback mechanism برای داده‌های ناقص**
168. **ایجاد سیستم audit trail برای تمام عملیات ورود داده**
169. **پیاده‌سازی کنترل توازن بدهکار و بستانکار اسناد**
170. **ایجاد سیستم تعمیر خودکار داده‌های ناقص**
```

### **فاز ۲-ج: پردازش افزایشی و بهینه‌سازی** (تسک‌های ۱۸۱-۲۰۰)

```
181. **پیاده‌سازی سیستم تشخیص آخرین سند وارد شده**
182. **ایجاد مکانیزم incremental loading بر اساس تاریخ**
183. **پیاده‌سازی کنترل تغییرات داده‌های قبلی**
184. **ایجاد سیستم versioning برای داده‌های مالی**
185. **پیاده‌سازی بهینه‌سازی bulk insert برای داده‌های حجیم**
186. **ایجاد indexهای بهینه برای جستجوی سریع**
187. **پیاده‌سازی سیستم cache برای داده‌های پرکاربرد**
188. **ایجاد background task برای پردازش فایل‌های بزرگ**
189. **پیاده‌سازی سیستم pause/resume برای آپلودهای طولانی**
190. **ایجاد گزارش پیشرفت عملیات ورود داده**
```

## 🗃️ طراحی مدل‌های دیتابیس پیشنهادی

```python
# models.py - مدل‌های جدید برای ساختار مالی

class FinancialSoftware(models.Model):
    """مدل برای نگاشت نرم‌افزارهای مالی مختلف"""
    name = models.CharField(max_length=100, verbose_name='نام نرم‌افزار')
    version = models.CharField(max_length=50, verbose_name='نسخه')
    description = models.TextField(verbose_name='توضیحات')
    is_active = models.BooleanField(default=True)

class ExcelColumnMapping(models.Model):
    """نگاشت ستون‌های اکسل به فیلدهای دیتابیس"""
    software = models.ForeignKey(FinancialSoftware, on_delete=models.CASCADE)
    excel_column = models.CharField(max_length=100, verbose_name='ستون اکسل')
    db_field = models.CharField(max_length=100, verbose_name='فیلد دیتابیس')
    data_type = models.CharField(max_length=50, verbose_name='نوع داده')
    is_required = models.BooleanField(default=False)

class DocumentHeader(models.Model):
    """سربرگ اسناد حسابداری"""
    DOCUMENT_TYPES = [
        ('SANAD', 'سند'),
        ('FACTOR', 'فاکتور'),
        ('DARVAGOZAR', 'دریافت و پرداخت'),
        ('ANBAR', 'انبار'),
    ]
    
    document_id = models.CharField(max_length=50, unique=True, verbose_name='شماره سند')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_date = models.DateField(verbose_name='تاریخ سند')
    description = models.TextField(verbose_name='شرح سند')
    total_debit = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='مجموع بدهکار')
    total_credit = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='مجموع بستانکار')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    imported_from = models.ForeignKey(FinancialSoftware, on_delete=models.SET_NULL, null=True)

class DocumentItem(models.Model):
    """آرتیکل‌های سند"""
    document = models.ForeignKey(DocumentHeader, on_delete=models.CASCADE, related_name='items')
    row_number = models.IntegerField(verbose_name='ردیف')
    account_code = models.CharField(max_length=50, verbose_name='کد حساب')
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='بدهکار')
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='بستانکار')
    description = models.TextField(verbose_name='شرح')
    cost_center = models.CharField(max_length=50, blank=True, verbose_name='مرکز هزینه')
    project_code = models.CharField(max_length=50, blank=True, verbose_name='کد پروژه')

class CodingStructure(models.Model):
    """ساختار کدینگ حسابداری"""
    ACCOUNT_LEVELS = [
        ('CLASS', 'کل'),
        ('SUBCLASS', 'معین'),
        ('DETAIL', 'تفصیلی'),
        ('COST_CENTER', 'مرکز هزینه'),
        ('PROJECT', 'پروژه'),
    ]
    
    code = models.CharField(max_length=50, unique=True, verbose_name='کد')
    name = models.CharField(max_length=200, verbose_name='نام')
    level = models.CharField(max_length=20, choices=ACCOUNT_LEVELS)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
```

## 🔧 طراحی سیستم کشف خودکار ساختار اکسل

```python
# excel_auto_detector.py
class ExcelStructureDetector:
    def detect_software_pattern(self, file_path):
        """تشخیص الگوی نرم‌افزار مالی بر اساس ساختار فایل"""
        pass
        
    def map_columns_automatically(self, df):
        """نگاشت خودکار ستون‌های اکسل"""
        pass
        
    def validate_mapping(self, mapping):
        """اعتبارسنجی نگاشت انجام شده"""
        pass
        
    def suggest_corrections(self, detected_mapping):
        """پیشنهاد تصحیح برای نگاشت‌های مشکوک"""
        pass
```

## 🛡️ طراحی سیستم کنترل یکپارچگی

```python
# data_integrity_controller.py
class DataIntegrityController:
    def check_duplicate_documents(self, document_data):
        """کنترل تکراری نبودن اسناد"""
        pass
        
    def validate_coding_structure(self, account_codes):
        """اعتبارسنجی وجود کدینگ در دیتابیس"""
        pass
        
    def check_document_balance(self, items):
        """کنترل توازن بدهکار و بستانکار سند"""
        pass
        
    def validate_sequence(self, document_numbers):
        """کنترل توالی شماره اسناد"""
        pass
```

## 📊 طراحی پردازش افزایشی

```python
# incremental_processor.py
class IncrementalDataProcessor:
    def find_last_imported_document(self, company_id):
        """یافتن آخرین سند وارد شده"""
        pass
        
    def filter_new_data(self, df, last_document_date):
        """فیلتر کردن داده‌های جدید"""
        pass
        
    def detect_changes(self, existing_data, new_data):
        """تشخیص تغییرات در داده‌های قبلی"""
        pass
        
    def create_import_batch(self, data):
        """ایجاد بسته‌های داده برای درج"""
        pass
```

## 🚀 اولویت‌بندی اجرا برای هفته آینده

### **هفته ۱: استانداردسازی و مدل‌سازی**
```python
# روز ۱-۲:
141. **تحلیل ساختار خروجی اکسل نرم‌افزارهای ایرانی**
142. **طراحی مدل استاندارد اسناد حسابداری**

# روز ۳-۴:
143. **پیاده‌سازی مدل‌های DocumentHeader و DocumentItem**
144. **ایجاد مدل CodingStructure برای کدینگ**

# روز ۵-۷:
145. **پیاده‌سازی سیستم کشف خودکار ساختار اکسل**
146. **ایجاد mapping table برای نرم‌افزارهای مختلف**
```

### **هفته ۲: کنترل‌های یکپارچگی**
```python
# روز ۸-۱۰:
161. **پیاده‌سازی سیستم تشخیص اسناد تکراری**
162. **ایجاد کنترل وجود کدینگ قبل از درج**

# روز ۱۱-۱۴:
163. **پیاده‌سازی کنترل توازن اسناد**
164. **ایجاد سیستم مدیریت خطا و گزارش‌گیری**
```

## 💡 نکات فنی مهم:

1. **از UUID برای کلیدهای اصلی استفاده شود**
2. **ایجاد ایندکس برای فیلدهای جستجوی پرتکرار**
3. **پیاده‌سازی soft delete برای داده‌های مالی**
4. **استفاده از transaction برای عملیات گروهی**
5. **ایجاد سیستم backup خودکار قبل از عملیات ورود داده**

**آیا مایلید با تسک ۱۴۱ (تحلیل ساختار خروجی اکسل نرم‌افزارهای ایرانی) شروع کنیم؟** نیاز دارم نمونه‌ای از خروجی اکسل این نرم‌افزارها را ببینم تا تحلیل دقیق‌تری ارائه دهم.