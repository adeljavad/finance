# financial_system/models/software_mapping.py
from django.db import models

class FinancialSoftware(models.Model):
    """مدل برای نرم‌افزارهای مالی مختلف"""
    name = models.CharField(max_length=100, verbose_name='نام نرم‌افزار')
    version = models.CharField(max_length=50, verbose_name='نسخه', blank=True)
    description = models.TextField(verbose_name='توضیحات', blank=True)
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    
    class Meta:
        verbose_name = 'نرم‌افزار مالی'
        verbose_name_plural = 'نرم‌افزارهای مالی'
    
    def __str__(self):
        return self.name

class ExcelColumnMapping(models.Model):
    """نگاشت ستون‌های اکسل به فیلدهای استاندارد"""
    software = models.ForeignKey(FinancialSoftware, on_delete=models.CASCADE, verbose_name='نرم‌افزار')
    excel_column = models.CharField(max_length=100, verbose_name='ستون اکسل')
    standard_field = models.CharField(max_length=100, verbose_name='فیلد استاندارد')
    data_type = models.CharField(max_length=50, verbose_name='نوع داده')
    is_required = models.BooleanField(default=False, verbose_name='الزامی')
    
    class Meta:
        verbose_name = 'نگاشت ستون'
        verbose_name_plural = 'نگاشت ستون‌ها'
        unique_together = ('software', 'excel_column')
    
    def __str__(self):
        return f"{self.software.name} - {self.excel_column}"

# به‌روزرسانی مدل DocumentHeader برای ذخیره منبع داده
class DocumentHeader(models.Model):
    # فیلدهای موجود...
    imported_from = models.ForeignKey(FinancialSoftware, on_delete=models.SET_NULL, 
                                    null=True, blank=True, verbose_name='وارد شده از')
    original_document_id = models.CharField(max_length=100, blank=True, verbose_name='شناسه سند در سیستم مبدأ')
    import_batch = models.CharField(max_length=50, blank=True, verbose_name='دسته وارداتی')
    
    class Meta:
        indexes = [
            models.Index(fields=['import_batch', 'company']),
            models.Index(fields=['original_document_id', 'imported_from']),
        ]