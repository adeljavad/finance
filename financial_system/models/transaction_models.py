# financial_system/models/transaction_models.py
from django.db import models
from .base_models import Company, FinancialPeriod
from .coding_models import ChartOfAccounts

class FinancialTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('PAYMENT', 'پرداخت'),
        ('RECEIPT', 'دریافت'),
        ('INVOICE', 'فاکتور'),
        ('WAREHOUSE', 'رسید انبار'),
    ]
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    period = models.ForeignKey(FinancialPeriod, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_date = models.DateField()
    description = models.TextField()
    account = models.ForeignKey(ChartOfAccounts, on_delete=models.CASCADE)
    reference_number = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = 'تراکنش مالی'
        verbose_name_plural = 'تراکنش‌های مالی'
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"