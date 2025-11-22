# financial_system/models/document_models.py
from django.db import models
from users.models import Company, FinancialPeriod
from .coding_models import ChartOfAccounts

class DocumentHeader(models.Model):
    DOCUMENT_TYPES = [
        ('SANAD', 'سند حسابداری'),
        ('FACTOR', 'فاکتور'),
        ('BANK', 'دریافت و پرداخت بانکی'),
        ('CASH', 'دریافت و پرداخت نقدی'),
    ]
    
    document_number = models.CharField(max_length=50, verbose_name='شماره سند')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_date = models.CharField(max_length=10, verbose_name='تاریخ سند')
    description = models.TextField(verbose_name='شرح سند')
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    period = models.ForeignKey(FinancialPeriod, on_delete=models.CASCADE)
    total_debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_balanced = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'سربرگ سند'
        verbose_name_plural = 'سربرگ اسناد'
        unique_together = ('company', 'period', 'document_number')
    
    def __str__(self):
        return f"{self.document_number} - {self.document_date}"

class DocumentItem(models.Model):
    document = models.ForeignKey(DocumentHeader, on_delete=models.CASCADE, related_name='items')
    row_number = models.IntegerField(verbose_name='ردیف')
    account = models.ForeignKey(ChartOfAccounts, on_delete=models.CASCADE, verbose_name='حساب')
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='بدهکار')
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='بستانکار')
    description = models.TextField(verbose_name='شرح')
    cost_center = models.CharField(max_length=50, blank=True, verbose_name='مرکز هزینه')
    project_code = models.CharField(max_length=50, blank=True, verbose_name='کد پروژه')
    
    class Meta:
        verbose_name = 'آرتیکل سند'
        verbose_name_plural = 'آرتیکل‌های اسناد'
    
    def __str__(self):
        return f"{self.document.document_number} - ردیف {self.row_number}"
