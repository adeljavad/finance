# data_importer/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class FinancialFile(models.Model):
    """مدل برای ذخیره فایل‌های اکسل مالی"""
    
    FILE_STATUS_CHOICES = [
        ('UPLOADED', 'آپلود شده'),
        ('ANALYZED', 'تحلیل شده'),
        ('VALIDATED', 'اعتبارسنجی شده'),
        ('IMPORTED', 'وارد شده'),
        ('FAILED', 'خطا'),
        ('CANCELLED', 'لغو شده'),
    ]
    
    SOFTWARE_TYPES = [
        ('HAMKARAN', 'همکاران سیستم'),
        ('RAHKARAN', 'راهکاران'),
        ('SEPIDAR', 'سپیدار'),
        ('UNKNOWN', 'ناشناخته'),
    ]
    
    # اطلاعات فایل
    file_name = models.CharField(max_length=255, verbose_name='نام فایل')
    original_name = models.CharField(max_length=255, verbose_name='نام اصلی فایل')
    file_path = models.CharField(max_length=500, verbose_name='مسیر فایل')
    file_size = models.BigIntegerField(verbose_name='حجم فایل (بایت)')
    
    # اطلاعات شرکت و دوره
    company = models.ForeignKey(
        'users.Company',
        on_delete=models.CASCADE,
        related_name='financial_files',
        verbose_name='شرکت'
    )
    financial_period = models.ForeignKey(
        'users.FinancialPeriod',
        on_delete=models.CASCADE,
        related_name='financial_files',
        verbose_name='دوره مالی'
    )
    
    # تحلیل فایل
    software_type = models.CharField(
        max_length=20,
        choices=SOFTWARE_TYPES,
        default='UNKNOWN',
        verbose_name='نوع نرم‌افزار'
    )
    confidence_score = models.FloatField(default=0.0, verbose_name='امتیاز اطمینان')
    columns_mapping = models.JSONField(default=dict, verbose_name='نگاشت ستون‌ها')
    analysis_result = models.JSONField(default=dict, blank=True, null=True, verbose_name='نتایج تحلیل')
    
    # وضعیت و مدیریت
    status = models.CharField(
        max_length=20,
        choices=FILE_STATUS_CHOICES,
        default='UPLOADED',
        verbose_name='وضعیت'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploaded_files',
        verbose_name='آپلود شده توسط'
    )
    
    # آمار و اطلاعات
    total_documents = models.IntegerField(default=0, verbose_name='تعداد اسناد')
    total_items = models.IntegerField(default=0, verbose_name='تعداد اقلام')
    validation_errors = models.JSONField(default=list, verbose_name='خطاهای اعتبارسنجی')
    
    # تاریخ‌ها
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ آپلود')
    analyzed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تحلیل')
    imported_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ وارد کردن')
    
    class Meta:
        verbose_name = 'فایل مالی'
        verbose_name_plural = 'فایل‌های مالی'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['uploaded_by', 'uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.original_name} - {self.company.name}"
    
    @property
    def file_size_mb(self):
        """حجم فایل به مگابایت"""
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def is_processable(self):
        """آیا فایل قابل پردازش است؟"""
        return self.status in ['UPLOADED', 'ANALYZED']
    
    def mark_as_analyzed(self, analysis_data):
        """علامت‌گذاری فایل به عنوان تحلیل شده"""
        self.status = 'ANALYZED'
        self.analyzed_at = timezone.now()
        self.analysis_result = analysis_data
        self.software_type = analysis_data.get('software_type', 'UNKNOWN')
        self.confidence_score = analysis_data.get('confidence', 0.0)
        self.columns_mapping = analysis_data.get('columns_mapping', {})
        self.save()
    
    def mark_as_imported(self, import_stats):
        """علامت‌گذاری فایل به عنوان وارد شده"""
        self.status = 'IMPORTED'
        self.imported_at = timezone.now()
        self.total_documents = import_stats.get('document_count', 0)
        self.total_items = import_stats.get('item_count', 0)
        self.save()


class ImportJob(models.Model):
    """مدل برای مدیریت کارهای وارد کردن"""
    
    JOB_STATUS_CHOICES = [
        ('PENDING', 'در انتظار'),
        ('PROCESSING', 'در حال پردازش'),
        ('COMPLETED', 'تکمیل شده'),
        ('FAILED', 'خطا'),
        ('CANCELLED', 'لغو شده'),
    ]
    
    # اطلاعات کار
    job_id = models.CharField(max_length=100, unique=True, verbose_name='شناسه کار')
    financial_file = models.ForeignKey(
        FinancialFile,
        on_delete=models.CASCADE,
        related_name='import_jobs',
        verbose_name='فایل مالی'
    )
    
    # وضعیت کار
    status = models.CharField(
        max_length=20,
        choices=JOB_STATUS_CHOICES,
        default='PENDING',
        verbose_name='وضعیت'
    )
    progress = models.IntegerField(default=0, verbose_name='پیشرفت (درصد)')
    current_step = models.CharField(max_length=200, default='آماده‌سازی', verbose_name='مرحله جاری')
    
    # نتایج و خطاها
    result_data = models.JSONField(default=dict, verbose_name='داده‌های نتیجه')
    error_message = models.TextField(blank=True, verbose_name='پیام خطا')
    stack_trace = models.TextField(blank=True, verbose_name='ردیابی خطا')
    
    # زمان‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ شروع')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تکمیل')
    
    class Meta:
        verbose_name = 'کار وارد کردن'
        verbose_name_plural = 'کارهای وارد کردن'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.job_id} - {self.financial_file.original_name}"
    
    def start_processing(self):
        """شروع پردازش کار"""
        self.status = 'PROCESSING'
        self.started_at = timezone.now()
        self.save()
    
    def complete(self, result_data=None):
        """تکمیل کار"""
        self.status = 'COMPLETED'
        self.progress = 100
        self.completed_at = timezone.now()
        if result_data:
            self.result_data = result_data
        self.save()
    
    def fail(self, error_message, stack_trace=''):
        """علامت‌گذاری کار به عنوان خطا"""
        self.status = 'FAILED'
        self.error_message = error_message
        self.stack_trace = stack_trace
        self.completed_at = timezone.now()
        self.save()
    
    def cancel(self):
        """لغو کار"""
        self.status = 'CANCELLED'
        self.completed_at = timezone.now()
        self.save()


class RawFinancialData(models.Model):
    """مدل برای ذخیره داده‌های خام با ساختار سلسله‌مراتبی"""
    
    financial_file = models.ForeignKey(
        FinancialFile,
        on_delete=models.CASCADE,
        related_name='raw_data',
        verbose_name='فایل مالی'
    )
    
    # سلسله مراتب حساب
    main_account_code = models.CharField(max_length=50, verbose_name='کد کل')
    main_account_name = models.CharField(max_length=200, verbose_name='نام کل')
    sub_account_code = models.CharField(max_length=50, verbose_name='کد معین', blank=True)
    sub_account_name = models.CharField(max_length=200, verbose_name='نام معین', blank=True)
    detail_account_code = models.CharField(max_length=50, verbose_name='کد تفصیلی', blank=True)
    detail_account_name = models.CharField(max_length=200, verbose_name='نام تفصیلی', blank=True)
    
    # اطلاعات سند
    document_number = models.CharField(max_length=50, verbose_name='شماره سند')
    document_date = models.DateField(verbose_name='تاریخ سند')
    description = models.TextField(verbose_name='شرح سند', blank=True)
    
    # مقادیر مالی
    debit_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.0,
        verbose_name='مبلغ بدهکار',
        validators=[MinValueValidator(0)]
    )
    credit_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0.0,
        verbose_name='مبلغ بستانکار',
        validators=[MinValueValidator(0)]
    )
    
    # اطلاعات اضافی
    row_index = models.IntegerField(verbose_name='شماره ردیف در فایل')
    imported = models.BooleanField(default=False, verbose_name='وارد شده')
    mapping_applied = models.BooleanField(default=False, verbose_name='نگاشت اعمال شده')
    
    # کدهای استاندارد (پس از اعمال mapping)
    standard_main_code = models.CharField(max_length=50, verbose_name='کد کل استاندارد', blank=True)
    standard_main_name = models.CharField(max_length=200, verbose_name='نام کل استاندارد', blank=True)
    standard_sub_code = models.CharField(max_length=50, verbose_name='کد معین استاندارد', blank=True)
    standard_sub_name = models.CharField(max_length=200, verbose_name='نام معین استاندارد', blank=True)
    standard_detail_code = models.CharField(max_length=50, verbose_name='کد تفصیلی استاندارد', blank=True)
    standard_detail_name = models.CharField(max_length=200, verbose_name='نام تفصیلی استاندارد', blank=True)
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    
    class Meta:
        verbose_name = 'داده مالی خام'
        verbose_name_plural = 'داده‌های مالی خام'
        ordering = ['financial_file', 'row_index']
        indexes = [
            models.Index(fields=['financial_file', 'imported']),
            models.Index(fields=['main_account_code']),
            models.Index(fields=['document_number', 'document_date']),
        ]
    
    def __str__(self):
        return f"{self.document_number} - {self.main_account_code} - ردیف {self.row_index}"
    
    @property
    def net_amount(self):
        """مبلغ خالص (بدهکار - بستانکار)"""
        return self.debit_amount - self.credit_amount
    
    @property
    def has_hierarchy(self):
        """آیا داده سلسله‌مراتبی کامل دارد؟"""
        return bool(self.sub_account_code or self.detail_account_code)
    
    def mark_as_imported(self):
        """علامت‌گذاری به عنوان وارد شده"""
        self.imported = True
        self.save()
    
    def apply_standard_mapping(self, mapping_data):
        """اعمال نگاشت کدینگ استاندارد"""
        self.standard_main_code = mapping_data.get('standard_main_code', '')
        self.standard_main_name = mapping_data.get('standard_main_name', '')
        self.standard_sub_code = mapping_data.get('standard_sub_code', '')
        self.standard_sub_name = mapping_data.get('standard_sub_name', '')
        self.standard_detail_code = mapping_data.get('standard_detail_code', '')
        self.standard_detail_name = mapping_data.get('standard_detail_name', '')
        self.mapping_applied = True
        self.save()


class StandardAccountChart(models.Model):
    """چارت حساب استاندارد سیستم"""
    
    ACCOUNT_TYPES = [
        ('ASSET', 'دارایی'),
        ('LIABILITY', 'بدهی'),
        ('EQUITY', 'حقوق صاحبان سهام'),
        ('REVENUE', 'درآمد'),
        ('EXPENSE', 'هزینه'),
        ('CONTRA_ASSET', 'دارایی متقابل'),
        ('CONTRA_LIABILITY', 'بدهی متقابل'),
    ]
    
    LEVEL_CHOICES = [
        (1, 'کل'),
        (2, 'معین'),
        (3, 'تفصیلی'),
        (4, 'زیر تفصیلی'),
    ]
    
    standard_code = models.CharField(max_length=50, unique=True, verbose_name='کد استاندارد')
    standard_name = models.CharField(max_length=200, verbose_name='نام استاندارد')
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
        verbose_name='نوع حساب'
    )
    level = models.IntegerField(
        choices=LEVEL_CHOICES,
        verbose_name='سطح',
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
        verbose_name='حساب والد'
    )
    
    # ویژگی‌های اضافی
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    natural_balance = models.CharField(
        max_length=10,
        choices=[('DEBIT', 'بدهکار'), ('CREDIT', 'بستانکار')],
        verbose_name='تراز طبیعی'
    )
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    
    class Meta:
        verbose_name = 'چارت حساب استاندارد'
        verbose_name_plural = 'چارت حساب‌های استاندارد'
        ordering = ['level', 'standard_code']
        indexes = [
            models.Index(fields=['standard_code']),
            models.Index(fields=['level', 'account_type']),
            models.Index(fields=['parent']),
        ]
    
    def __str__(self):
        return f"{self.standard_code} - {self.standard_name}"
    
    @property
    def full_path(self):
        """مسیر کامل سلسله‌مراتب"""
        if self.parent:
            return f"{self.parent.full_path} > {self.standard_code}"
        return self.standard_code
    
    @property
    def is_leaf(self):
        """آیا این حساب برگ است (فرزندی ندارد)؟"""
        return not self.children.exists()


class CompanyAccountMapping(models.Model):
    """نگاشت کدهای شرکت به کد استاندارد"""
    
    company = models.ForeignKey(
        'users.Company',
        on_delete=models.CASCADE,
        related_name='account_mappings',
        verbose_name='شرکت'
    )
    
    # کد شرکت
    company_main_code = models.CharField(max_length=50, verbose_name='کد کل شرکت')
    company_main_name = models.CharField(max_length=200, verbose_name='نام کل شرکت')
    company_sub_code = models.CharField(max_length=50, verbose_name='کد معین شرکت', blank=True)
    company_sub_name = models.CharField(max_length=200, verbose_name='نام معین شرکت', blank=True)
    company_detail_code = models.CharField(max_length=50, verbose_name='کد تفصیلی شرکت', blank=True)
    company_detail_name = models.CharField(max_length=200, verbose_name='نام تفصیلی شرکت', blank=True)
    
    # کد استاندارد
    standard_main_code = models.ForeignKey(
        StandardAccountChart,
        on_delete=models.CASCADE,
        related_name='main_mappings',
        verbose_name='کد کل استاندارد'
    )
    standard_sub_code = models.ForeignKey(
        StandardAccountChart,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_mappings',
        verbose_name='کد معین استاندارد'
    )
    standard_detail_code = models.ForeignKey(
        StandardAccountChart,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='detail_mappings',
        verbose_name='کد تفصیلی استاندارد'
    )
    
    # وضعیت
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    confidence_score = models.FloatField(
        default=1.0,
        verbose_name='امتیاز اطمینان',
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    mapping_type = models.CharField(
        max_length=20,
        choices=[
            ('MANUAL', 'دستی'),
            ('AUTO_SUGGESTED', 'پیشنهاد خودکار'),
            ('BULK_IMPORT', 'وارد کردن دسته‌ای'),
        ],
        default='MANUAL',
        verbose_name='نوع نگاشت'
    )
    
    # اطلاعات ایجاد
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_mappings',
        verbose_name='ایجاد شده توسط'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    
    class Meta:
        verbose_name = 'نگاشت حساب شرکت'
        verbose_name_plural = 'نگاشت‌های حساب شرکت'
        ordering = ['company', 'company_main_code']
        unique_together = [
            ('company', 'company_main_code', 'company_sub_code', 'company_detail_code')
        ]
        indexes = [
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['company_main_code']),
            models.Index(fields=['standard_main_code']),
        ]
    
    def __str__(self):
        return f"{self.company.name}: {self.company_main_code} → {self.standard_main_code.standard_code}"
    
    @property
    def company_full_code(self):
        """کد کامل شرکت"""
        parts = [self.company_main_code]
        if self.company_sub_code:
            parts.append(self.company_sub_code)
        if self.company_detail_code:
            parts.append(self.company_detail_code)
        return '.'.join(parts)
    
    @property
    def standard_full_code(self):
        """کد کامل استاندارد"""
        parts = [self.standard_main_code.standard_code]
        if self.standard_sub_code:
            parts.append(self.standard_sub_code.standard_code)
        if self.standard_detail_code:
            parts.append(self.standard_detail_code.standard_code)
        return '.'.join(parts)
    
    def get_mapping_for_level(self, level):
        """دریافت نگاشت برای سطح مشخص"""
        if level == 1:
            return {
                'company_code': self.company_main_code,
                'company_name': self.company_main_name,
                'standard_code': self.standard_main_code.standard_code,
                'standard_name': self.standard_main_code.standard_name,
            }
        elif level == 2 and self.standard_sub_code:
            return {
                'company_code': self.company_sub_code,
                'company_name': self.company_sub_name,
                'standard_code': self.standard_sub_code.standard_code,
                'standard_name': self.standard_sub_code.standard_name,
            }
        elif level == 3 and self.standard_detail_code:
            return {
                'company_code': self.company_detail_code,
                'company_name': self.company_detail_name,
                'standard_code': self.standard_detail_code.standard_code,
                'standard_name': self.standard_detail_code.standard_name,
            }
        return None
