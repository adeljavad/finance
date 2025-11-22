# ✅ تسک تکمیل شده: بهبود سیستم ایمپورت داده و مدیریت خطاهای توازن اسناد

**تاریخ تکمیل**: ۳۱ مهر ۱۴۰۴  
**وضعیت**: ✅ تکمیل شده

## وضعیت فعلی و مشکل

در حال حاضر سیستم ایمپورت داده با خطای زیر مواجه می‌شود:
```
خطا در وارد کردن داده‌ها: ستون‌های ضروری یافت نشد: شرح سند, کد حساب, شرح حساب, عدم توازن: جمع بدهکار=21500447387030, جمع بستانکار=29838952255839
```

## تحلیل مشکل

### 1. خطاهای شناسایی شده:
- **ستون‌های ضروری مفقود**: شرح سند، کد حساب، شرح حساب
- **عدم توازن اسناد**: تفاوت قابل توجه بین جمع بدهکار و بستانکار
- **سیستم بازخورد ضعیف**: کاربران نمی‌توانند مشکلات را درک و اصلاح کنند

### 2. علل ریشه‌ای:
- اعتبارسنجی سخت‌گیرانه که کل فرآیند را متوقف می‌کند
- عدم امکان اصلاح داده‌ها قبل از ایمپورت
- نبود راهنمایی تعاملی برای کاربران
- عدم یکپارچگی با چت بات برای ارائه راهنمایی

## راه‌حل پیشنهادی

### فاز 1: بهبود سیستم اعتبارسنجی و مدیریت خطا

#### 1.1 اعتبارسنجی مرحله‌ای
- **اعتبارسنجی ساختاری**: بررسی وجود ستون‌های ضروری
- **اعتبارسنجی داده‌ای**: بررسی مقادیر خالی و فرمت‌ها
- **اعتبارسنجی توازن**: بررسی توازن بدهکار و بستانکار

#### 1.2 مدیریت خطاهای توازن
- **شناسایی اسناد نامتوازن**: تشخیص دقیق اسناد مشکل‌دار
- **پیشنهاد اصلاح خودکار**: محاسبه تفاوت و پیشنهاد اصلاح
- **گزینه‌های کاربر**: امکان اصلاح دستی یا خودکار

### فاز 2: سیستم بازخورد تعاملی

#### 2.1 داشبورد پیش‌نمایش پیشرفته
- نمایش مشکلات به صورت بصری
- امکان فیلتر و جستجو در خطاها
- پیشنهادات اصلاح خودکار

#### 2.2 ویرایشگر آنلاین داده‌ها
- امکان ویرایش مستقیم در مرورگر
- اعتبارسنجی لحظه‌ای
- ذخیره تغییرات موقت

### فاز 3: یکپارچه‌سازی با چت بات

#### 3.1 سرویس مشاوره مالی
- تحلیل خطاها و ارائه راهنمایی
- پیشنهاد راه‌حل‌های عملی
- آموزش مفاهیم حسابداری

#### 3.2 گزارش‌دهی هوشمند
- تولید گزارش تحلیل خطاها
- پیشنهاد بهبود فرآیندها
- یادگیری از خطاهای تکراری

## الزامات فنی

### 1. مدل‌های جدید

#### ImportValidationResult
```python
class ImportValidationResult(models.Model):
    financial_file = models.ForeignKey(FinancialFile, on_delete=models.CASCADE)
    validation_type = models.CharField(max_length=50)  # STRUCTURAL, DATA, BALANCE
    severity = models.CharField(max_length=20)  # ERROR, WARNING, INFO
    message = models.TextField()
    affected_rows = models.JSONField(default=list)
    suggested_fix = models.JSONField(default=dict)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    resolved_at = models.DateTimeField(null=True)
```

#### DocumentBalanceCorrection
```python
class DocumentBalanceCorrection(models.Model):
    validation_result = models.ForeignKey(ImportValidationResult, on_delete=models.CASCADE)
    document_number = models.CharField(max_length=50)
    current_debit = models.DecimalField(max_digits=15, decimal_places=2)
    current_credit = models.DecimalField(max_digits=15, decimal_places=2)
    difference = models.DecimalField(max_digits=15, decimal_places=2)
    correction_type = models.CharField(max_length=20)  # AUTO, MANUAL, SUGGESTED
    correction_data = models.JSONField(default=dict)
    applied = models.BooleanField(default=False)
```

### 2. سرویس‌های جدید

#### AdvancedValidationService
- اعتبارسنجی ساختاری پیشرفته
- تشخیص الگوهای خطا
- پیشنهاد اصلاح خودکار

#### BalanceCorrectionService
- محاسبه تفاوت توازن
- پیشنهاد روش‌های اصلاح
- اعمال اصلاحات

#### ChatbotIntegrationService
- تحلیل خطاها برای چت بات
- تولید راهنمایی‌های متنی
- مدیریت مکالمات کاربر

### 3. ویوهای جدید

#### EnhancedPreviewView
- نمایش پیش‌نمایش تعاملی
- مدیریت خطاها
- ویرایش آنلاین

#### BalanceCorrectionView
- نمایش اسناد نامتوازن
- پیشنهاد اصلاحات
- اعمال تغییرات

#### ChatbotAssistanceView
- یکپارچه‌سازی با چت بات
- ارائه راهنمایی
- مدیریت سوالات

## پیاده‌سازی

### مرحله 1: بهبود اعتبارسنجی موجود

#### 1.1 اصلاح DataIntegrationService
```python
def validate_data_structure_advanced(self, df: pd.DataFrame) -> dict:
    """اعتبارسنجی پیشرفته با مدیریت خطاهای جزئی"""
    results = {
        'errors': [],
        'warnings': [],
        'suggestions': [],
        'balance_issues': []
    }
    
    # اعتبارسنجی ساختاری
    structural_errors = self._validate_structure(df)
    results['errors'].extend(structural_errors)
    
    # اعتبارسنجی داده‌ای
    data_warnings = self._validate_data_quality(df)
    results['warnings'].extend(data_warnings)
    
    # اعتبارسنجی توازن
    balance_issues = self._validate_balance(df)
    results['balance_issues'].extend(balance_issues)
    
    return results
```

#### 1.2 سرویس اصلاح توازن
```python
class BalanceCorrectionService:
    def analyze_balance_issues(self, df: pd.DataFrame) -> list:
        """تحلیل مشکلات توازن در داده‌ها"""
        issues = []
        
        # گروه‌بندی بر اساس شماره سند
        grouped = df.groupby('شماره سند')
        
        for doc_number, group in grouped:
            total_debit = group['بدهکار'].sum()
            total_credit = group['بستانکار'].sum()
            difference = abs(total_debit - total_credit)
            
            if difference > 0.01:
                issues.append({
                    'document_number': doc_number,
                    'total_debit': float(total_debit),
                    'total_credit': float(total_credit),
                    'difference': float(difference),
                    'suggested_fixes': self._suggest_fixes(group, difference)
                })
        
        return issues
    
    def _suggest_fixes(self, group_df: pd.DataFrame, difference: float) -> list:
        """پیشنهاد روش‌های اصلاح"""
        fixes = []
        
        # پیشنهاد 1: اضافه کردن ردیف تنظیمی
        fixes.append({
            'type': 'ADD_ADJUSTMENT_ROW',
            'description': 'افزودن ردیف تنظیمی برای تفاوت',
            'adjustment_amount': difference
        })
        
        # پیشنهاد 2: اصلاح بزرگترین مقادیر
        largest_debit = group_df.nlargest(3, 'بدهکار')
        largest_credit = group_df.nlargest(3, 'بستانکار')
        
        fixes.append({
            'type': 'ADJUST_LARGEST_VALUES',
            'description': 'اصلاح بزرگترین مقادیر بدهکار/بستانکار',
            'candidates': {
                'debit': largest_debit[['بدهکار']].to_dict('records'),
                'credit': largest_credit[['بستانکار']].to_dict('records')
            }
        })
        
        return fixes
```

### مرحله 2: رابط کاربری پیشرفته

#### 2.1 تمپلیت پیش‌نمایش بهبود یافته
```html
<!-- data_importer/templates/data_importer/enhanced_preview.html -->
<div class="validation-results">
    <div class="error-section" v-if="errors.length">
        <h4>خطاهای بحرانی</h4>
        <div v-for="error in errors" class="alert alert-danger">
            {{ error }}
        </div>
    </div>
    
    <div class="balance-issues" v-if="balanceIssues.length">
        <h4>مشکلات توازن</h4>
        <div v-for="issue in balanceIssues" class="balance-issue-card">
            <h5>سند {{ issue.document_number }}</h5>
            <p>تفاوت: {{ issue.difference }} ریال</p>
            <div class="suggested-fixes">
                <h6>پیشنهادات اصلاح:</h6>
                <div v-for="fix in issue.suggested_fixes" class="fix-option">
                    <button @click="applyFix(issue.document_number, fix)">
                        {{ fix.description }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="data-editor">
    <h4>ویرایشگر داده‌ها</h4>
    <table class="table table-bordered">
        <thead>
            <tr>
                <th v-for="col in columns">{{ col }}</th>
            </tr>
        </thead>
        <tbody>
            <tr v-for="(row, index) in sampleData" :class="getRowClass(row)">
                <td v-for="col in columns">
                    <editable-cell 
                        :value="row[col]" 
                        :column="col"
                        :row-index="index"
                        @update="updateCellValue">
                    </editable-cell>
                </td>
            </tr>
        </tbody>
    </table>
</div>
```

### مرحله 3: یکپارچه‌سازی چت بات

#### 3.1 سرویس مشاوره مالی
```python
class FinancialAdvisoryService:
    def __init__(self):
        self.chatbot_client = ChatbotClient()
    
    def analyze_import_issues(self, validation_results: dict) -> str:
        """تحلیل خطاها و تولید راهنمایی"""
        analysis = []
        
        if validation_results['errors']:
            analysis.append(self._analyze_errors(validation_results['errors']))
        
        if validation_results['balance_issues']:
            analysis.append(self._analyze_balance_issues(validation_results['balance_issues']))
        
        if validation_results['warnings']:
            analysis.append(self._analyze_warnings(validation_results['warnings']))
        
        return self._generate_advice(analysis)
    
    def _analyze_balance_issues(self, balance_issues: list) -> dict:
        """تحلیل مشکلات توازن"""
        total_difference = sum(issue['difference'] for issue in balance_issues)
        document_count = len(balance_issues)
        
        return {
            'type': 'BALANCE_ISSUES',
            'severity': 'HIGH' if total_difference > 1000000 else 'MEDIUM',
            'summary': f'{document_count} سند نامتوازن با تفاوت کل {total_difference} ریال',
            'suggestions': [
                'بررسی مقادیر بزرگ بدهکار/بستانکار',
                'افزودن ردیف‌های تنظیمی',
                'بررسی تکراری بودن اسناد'
            ]
        }
```

## مزایای پیاده‌سازی

### 1. برای کاربران
- **تجربه کاربری بهتر**: امکان اصلاح خطاها قبل از ایمپورت
- **یادگیری**: درک بهتر مفاهیم حسابداری از طریق راهنمایی‌ها
- **صرفه‌جویی در زمان**: کاهش نیاز به اصلاح دستی فایل‌ها

### 2. برای سیستم
- **کیفیت داده بهتر**: کاهش خطاهای وارد شده به سیستم
- **یادگیری مستمر**: بهبود الگوریتم‌ها بر اساس تجربیات
- **قابلیت توسعه**: معماری ماژولار برای افزودن قابلیت‌های جدید

### 3. برای مدیریت
- **گزارش‌دهی**: تحلیل الگوهای خطا و بهبود فرآیندها
- **نظارت**: امکان پیگیری وضعیت اصلاح خطاها
- **بهینه‌سازی**: شناسایی نقاط ضعف در فرآیند ایمپورت

## جدول زمانی پیشنهادی

| فاز | مدت زمان | تحویل‌پذیرها |
|-----|----------|-------------|
| فاز 1 | 2 هفته | سرویس‌های اعتبارسنجی پیشرفته |
| فاز 2 | 3 هفته | رابط کاربری تعاملی |
| فاز 3 | 2 هفته | یکپارچه‌سازی چت بات |
| تست و بهینه‌سازی | 1 هفته | تست کامل و رفع اشکالات |

## معیارهای موفقیت

### کمی
- کاهش 80٪ خطاهای ایمپورت
- کاهش 50٪ زمان اصلاح داده‌ها
- افزایش 90٪ رضایت کاربران

### کیفی
- بهبود تجربه کاربری
- افزایش دانش مالی کاربران
- کاهش نیاز به پشتیبانی فنی

این تسک سیستم ایمپورت داده را از یک فرآیند سخت‌گیرانه به یک سیستم تعاملی و آموزشی تبدیل می‌کند که هم کیفیت داده‌ها را بهبود می‌بخشد و هم تجربه کاربری را ارتقا می‌دهد.
