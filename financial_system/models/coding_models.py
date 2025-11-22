# financial_system/models/coding_models.py
from django.db import models

class ChartOfAccounts(models.Model):
    ACCOUNT_LEVELS = [
        ('CLASS', 'کل'),
        ('SUBCLASS', 'معین'),
        ('DETAIL', 'تفصیلی'),
        ('PROJECT', 'پروژه'),
        ('COST_CENTER', 'مرکز هزینه'),
    ]
    
    code = models.CharField(max_length=50, verbose_name='کد حساب')
    name = models.CharField(max_length=200, verbose_name='نام حساب')
    level = models.CharField(max_length=20, choices=ACCOUNT_LEVELS)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, verbose_name='توضیحات')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'سرفصل حساب'
        verbose_name_plural = 'سرفصل‌های حساب'
        unique_together = ('code', 'level')
    
    def __str__(self):
        return f"{self.code} - {self.name}"