# تحلیل جامع فایل اکسل همکاران سیستم و طراحی سیستم استخراج سرفصل‌ها

## 🔍 تحلیل ساختار فایل اکسل نمونه

### ستون‌های کلیدی شناسایی شده:

1. **ستون‌های کدینگ سلسله مراتبی:**
   - `Code1`, `Title1` → سطح کل
   - `Code2`, `Title2` → سطح معین  
   - `Code3`, `Title3` → سطح تفصیلی
   - `Code4`, `Title4` → سطح پروژه/مرکز هزینه

2. **ستون‌های شناسه سند:**
   - `شناسه سند`, `شماره سند`, `تاریخ سند`

3. **ستون‌های مالی:**
   - `بدهکار`, `بستانکار`, `مانده`

## 🎯 طراحی سیستم استخراج هوشمند سرفصل‌ها

### **تسک‌های جدید برای استخراج سرفصل‌ها** (تسک‌های ۲۰۱-۲۲۰)

```
201. **طراحی الگوریتم شناسایی خودکار سطوح کدینگ از فایل اکسل**
202. **پیاده‌سازی سیستم استخراج سرفصل‌های کل از Title1/Code1**
203. **ایجاد سیستم استخراج سرفصل‌های معین از Title2/Code2**
204. **پیاده‌سازی سیستم استخراج سرفصل‌های تفصیلی از Title3/Code3**
205. **ایجاد کنترل ارتباط سلسله مراتبی بین سطوح کدینگ**
206. **پیاده‌سازی تشخیص خودکار کدینگ‌های جدید در فایل‌های ماهانه**
207. **ایجاد سیستم پیشنهاد نام برای سرفصل‌های مشابه**
208. **پیاده‌سازی الگوریتم تطبیق کدینگ‌های موجود با کدینگ‌های جدید**
209. **ایجاد گزارش تغییرات ساختار کدینگ بین دوره‌های مالی**
210. **پیاده‌سازی تأیید کاربر قبل از ایجاد سرفصل‌های جدید**
```

### **تسک‌های ابزار LangChain** (تسک‌های ۲۱۱-۲۲۰)

```
211. **طراحی CodingExtractorTool برای استخراج سرفصل‌ها**
212. **پیاده‌سازی CodingValidatorTool برای اعتبارسنجی سرفصل‌ها**
213. **ایجاد CodingHierarchyTool برای تحلیل سلسله مراتب**
214. **پیاده‌سازی NewCodingDetectionTool برای شناسایی سرفصل‌های جدید**
215. **ایجاد CodingSuggestionTool برای پیشنهاد نام‌های بهینه**
216. **پیاده‌سازی AutomatedCodingCreationTool برای ایجاد خودکار**
217. **ایجاد CodingChangeReportTool برای گزارش تغییرات**
218. **پیاده‌سازی BulkCodingProcessorTool برای پردازش گروهی**
219. **ایجاد CodingIntegrationTool برای یکپارچه‌سازی با اسناد**
220. **پیاده‌سازی CodingAuditTool برای حسابرسی ساختار کدینگ**
```

## 🗃️ طراحی مدل‌های پیشرفته برای کدینگ

```python
# models.py - توسعه مدل CodingStructure

class CodingStructure(models.Model):
    ACCOUNT_LEVELS = [
        ('CLASS', 'کل'),
        ('SUBCLASS', 'معین'), 
        ('DETAIL', 'تفصیلی'),
        ('PROJECT', 'پروژه'),
        ('COST_CENTER', 'مرکز هزینه'),
    ]
    
    code = models.CharField(max_length=50, verbose_name='کد')
    name = models.CharField(max_length=200, verbose_name='نام فارسی')
    name_en = models.CharField(max_length=200, blank=True, verbose_name='نام انگلیسی')
    level = models.CharField(max_length=20, choices=ACCOUNT_LEVELS)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    created_from_excel = models.BooleanField(default=False)
    source_file = models.ForeignKey(FinancialFile, on_delete=models.SET_NULL, null=True)
    first_seen_date = models.DateField(verbose_name='تاریخ اولین مشاهده')
    last_seen_date = models.DateField(verbose_name='تاریخ آخرین مشاهده')
    
    class Meta:
        unique_together = ('code', 'level')
        verbose_name = 'ساختار کدینگ'
        verbose_name_plural = 'ساختارهای کدینگ'

class CodingChangeLog(models.Model):
    """ثبت تغییرات ساختار کدینگ"""
    CHANGE_TYPES = [
        ('NEW', 'سرفصل جدید'),
        ('MODIFIED', 'تغییر نام'),
        ('DEACTIVATED', 'غیرفعال شده'),
        ('REACTIVATED', 'فعال شده'),
    ]
    
    coding = models.ForeignKey(CodingStructure, on_delete=models.CASCADE)
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    change_date = models.DateTimeField(auto_now_add=True)
    source_file = models.ForeignKey(FinancialFile, on_delete=models.SET_NULL, null=True)
```

## 🔧 طراحی سیستم استخراج هوشمند

```python
# coding_extractor.py

class IntelligentCodingExtractor:
    def __init__(self):
        self.cache = {}
        
    def extract_hierarchical_coding(self, df):
        """استخراج سلسله مراتب کدینگ از DataFrame"""
        codings = {
            'classes': set(),
            'subclasses': set(), 
            'details': set(),
            'projects': set()
        }
        
        for index, row in df.iterrows():
            self._extract_from_row(row, codings)
            
        return self._validate_and_structure(codings)
    
    def _extract_from_row(self, row, codings):
        """استخراج کدینگ از یک ردیف"""
        # استخراج سطح کل
        if pd.notna(row.get('Code1')) and pd.notna(row.get('Title1')):
            class_code = self._clean_code(row['Code1'])
            class_name = self._clean_name(row['Title1'])
            codings['classes'].add((class_code, class_name))
        
        # استخراج سطح معین
        if pd.notna(row.get('Code2')) and pd.notna(row.get('Title2')):
            subclass_code = self._clean_code(row['Code2'])
            subclass_name = self._clean_name(row['Title2'])
            parent_class = self._find_parent_class(subclass_code, codings['classes'])
            codings['subclasses'].add((subclass_code, subclass_name, parent_class))
        
        # استخراج سطح تفصیلی
        if pd.notna(row.get('Code3')) and pd.notna(row.get('Title3')):
            detail_code = self._clean_code(row['Code3'])
            detail_name = self._clean_name(row['Title3'])
            parent_subclass = self._find_parent_subclass(detail_code, codings['subclasses'])
            codings['details'].add((detail_code, detail_name, parent_subclass))
    
    def _clean_code(self, code):
        """پاکسازی کد"""
        if isinstance(code, (int, float)):
            return str(int(code))
        return str(code).strip()
    
    def _clean_name(self, name):
        """پاکسازی نام"""
        return str(name).strip()
    
    def _find_parent_class(self, subclass_code, classes):
        """پیدا کردن والد کل برای معین"""
        for class_code, class_name in classes:
            if subclass_code.startswith(class_code):
                return class_code
        return None
    
    def _find_parent_subclass(self, detail_code, subclasses):
        """پیدا کردن والد معین برای تفصیلی"""
        for subclass_code, subclass_name, parent_class in subclasses:
            if detail_code.startswith(subclass_code):
                return subclass_code
        return None
```

## 🤖 طراحی ابزار LangChain برای استخراج سرفصل‌ها

```python
# langchain_tools/coding_tools.py

class CodingExtractorTool(BaseTool):
    name = "coding_extractor"
    description = "استخراج سرفصل‌های کل، معین و تفصیلی از فایل اکسل مالی"
    
    def _run(self, file_path: str) -> Dict:
        """استخراج سرفصل‌ها از فایل اکسل"""
        extractor = IntelligentCodingExtractor()
        df = pd.read_excel(file_path)
        
        # استخراج سرفصل‌ها
        extracted_codings = extractor.extract_hierarchical_coding(df)
        
        # تشخیص سرفصل‌های جدید
        new_codings = self._detect_new_codings(extracted_codings)
        
        return {
            'extracted_codings': extracted_codings,
            'new_codings': new_codings,
            'total_count': self._count_codings(extracted_codings)
        }
    
    def _detect_new_codings(self, extracted_codings):
        """تشخیص سرفصل‌های جدید"""
        new_codings = {
            'classes': [],
            'subclasses': [],
            'details': []
        }
        
        for level, codings in extracted_codings.items():
            for coding in codings:
                code = coding[0]  # کد اولین عنصر است
                if not self._coding_exists(code, level):
                    new_codings[level].append(coding)
                    
        return new_codings
    
    def _coding_exists(self, code, level):
        """بررسی وجود کدینگ در دیتابیس"""
        return CodingStructure.objects.filter(
            code=code, 
            level=level.upper()
        ).exists()

class NewCodingDetectionTool(BaseTool):
    name = "new_coding_detector"
    description = "تشخیص سرفصل‌های جدید در فایل اکسل ماهانه"
    
    def _run(self, file_path: str, previous_month_file: str = None) -> Dict:
        """مقایسه با فایل ماه قبل و تشخیص سرفصل‌های جدید"""
        current_codings = self._extract_codings(file_path)
        
        if previous_month_file:
            previous_codings = self._extract_codings(previous_month_file)
            new_codings = self._compare_codings(current_codings, previous_codings)
        else:
            # اگر فایل ماه قبل نبود، با دیتابیس مقایسه کن
            new_codings = self._compare_with_database(current_codings)
            
        return {
            'new_codings': new_codings,
            'change_analysis': self._analyze_changes(new_codings)
        }
```

## 🚀 گردش کار پیشنهادی برای پردازش فایل ماهانه

```python
# monthly_processing.py

class MonthlyFileProcessor:
    def process_monthly_file(self, file_path, company_id, month, year):
        """پردازش کامل فایل ماهانه"""
        
        # 1. استخراج سرفصل‌ها
        coding_tool = CodingExtractorTool()
        coding_result = coding_tool._run(file_path)
        
        # 2. تشخیص سرفصل‌های جدید
        detection_tool = NewCodingDetectionTool()
        new_codings = detection_tool._run(file_path)
        
        # 3. ایجاد سرفصل‌های جدید (با تأیید کاربر)
        created_codings = self._create_new_codings(
            new_codings, 
            company_id, 
            f"{year}-{month:02d}-01"
        )
        
        # 4. پردازش اسناد مالی
        documents = self._process_financial_documents(
            file_path, 
            company_id, 
            month, 
            year
        )
        
        return {
            'new_codings_created': len(created_codings),
            'documents_processed': len(documents),
            'processing_summary': self._generate_summary()
        }
```

## 📊 گزارش‌های تحلیلی پیشنهادی

```python
# گزارش‌های خروجی سیستم
reports = {
    'coding_changes': 'گزارش تغییرات ساختار کدینگ',
    'new_accounts': 'گزارش حساب‌های جدید ایجاد شده', 
    'hierarchy_issues': 'گزارش مشکلات سلسله مراتب',
    'naming_inconsistencies': 'گزارش ناسازگاری‌های نامگذاری',
    'monthly_comparison': 'گزارش مقایسه‌ای ماهانه'
}
```

## 🎯 اولویت‌بندی اجرا

### **هفته ۱: استخراج پایه**
```python
# روز ۱-۳:
201. **طراحی الگوریتم شناسایی خودکار سطوح کدینگ**
202. **پیاده‌سازی سیستم استخراج سرفصل‌های کل**

# روز ۴-۷:  
203. **ایجاد سیستم استخراج سرفصل‌های معین و تفصیلی**
211. **طراحی CodingExtractorTool برای LangChain**
```

### **هفته ۲: تشخیص و یکپارچه‌سازی**
```python
# روز ۸-۱۰:
206. **پیاده‌سازی تشخیص خودکار کدینگ‌های جدید**
214. **ایجاد NewCodingDetectionTool**

# روز ۱۱-۱۴:
207. **ایجاد سیستم پیشنهاد نام برای سرفصل‌ها**
220. **پیاده‌سازی CodingAuditTool**
```

**آیا مایلید با تسک ۲۰۱ (طراحی الگوریتم شناسایی خودکار سطوح کدینگ) شروع کنیم؟** می‌توانم کدهای اولیه استخراج از فایل نمونه شما را پیاده‌سازی کنم.