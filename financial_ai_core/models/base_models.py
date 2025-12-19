# financial_system/models/base_models.py
from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=200, verbose_name='نام شرکت')
    economic_code = models.CharField(max_length=20, verbose_name='کد اقتصادی')
    national_code = models.CharField(max_length=20, verbose_name='شناسه ملی')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'شرکت'
        verbose_name_plural = 'شرکت‌ها'
    
    def __str__(self):
        return self.name

class FinancialPeriod(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name='نام دوره')
    start_date = models.DateField(verbose_name='تاریخ شروع')
    end_date = models.DateField(verbose_name='تاریخ پایان')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'دوره مالی'
        verbose_name_plural = 'دوره‌های مالی'
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"