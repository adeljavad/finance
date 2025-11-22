# data_importer/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

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
