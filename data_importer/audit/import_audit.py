# data_importer/audit/import_audit.py
from django.db import models
from django.contrib.auth.models import User
from financial_system.models import Company, FinancialPeriod
import json
from typing import Dict, Any, List
from enum import Enum

class AuditActionType(Enum):
    FILE_UPLOAD = "FILE_UPLOAD"
    STRUCTURE_ANALYSIS = "STRUCTURE_ANALYSIS"
    VALIDATION = "VALIDATION"
    DATA_IMPORT = "DATA_IMPORT"
    ROLLBACK = "ROLLBACK"
    CODE_CREATION = "CODE_CREATION"

class ImportAuditTrail(models.Model):
    """مدل برای ثبت audit trail عملیات وارد کردن داده"""
    
    ACTION_TYPES = [
        (action.value, action.name) for action in AuditActionType
    ]
    
    SEVERITY_LEVELS = [
        ('INFO', 'اطلاعات'),
        ('WARNING', 'هشدار'),
        ('ERROR', 'خطا'),
        ('CRITICAL', 'بحرانی')
    ]
    
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='زمان')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name='شرکت')
    period = models.ForeignKey(FinancialPeriod, on_delete=models.CASCADE, verbose_name='دوره مالی')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES, verbose_name='نوع عمل')
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='INFO', verbose_name='سطح شدت')
    
    # شناسه‌های مرتبط
    import_batch = models.CharField(max_length=100, blank=True, verbose_name='دسته وارداتی')
    document_number = models.CharField(max_length=50, blank=True, verbose_name='شماره سند')
    account_code = models.CharField(max_length=50, blank=True, verbose_name='کد حساب')
    
    # جزئیات عمل
    description = models.TextField(verbose_name='شرح عمل')
    old_values = models.JSONField(null=True, blank=True, verbose_name='مقادیر قبلی')
    new_values = models.JSONField(null=True, blank=True, verbose_name='مقادیر جدید')
    metadata = models.JSONField(null=True, blank=True, verbose_name='متادیتا')
    
    # نتیجه عمل
    success = models.BooleanField(default=True, verbose_name='موفقیت‌آمیز')
    error_message = models.TextField(blank=True, verbose_name='پیغام خطا')
    processing_time_ms = models.IntegerField(null=True, blank=True, verbose_name='زمان پردازش (میلی‌ثانیه)')
    
    class Meta:
        verbose_name = 'ردیابی حسابرسی وارد کردن'
        verbose_name_plural = 'ردیابی‌های حسابرسی وارد کردن'
        indexes = [
            models.Index(fields=['timestamp', 'company']),
            models.Index(fields=['import_batch', 'action_type']),
            models.Index(fields=['user', 'timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_action_type_display()} - {self.company.name} - {self.timestamp}"

class AuditTrailManager:
    def __init__(self, user: User, company: Company, period: FinancialPeriod):
        self.user = user
        self.company = company
        self.period = period
        self.import_batch = None
    
    def set_import_batch(self, import_batch: str):
        """تنظیم دسته وارداتی برای audit trail"""
        self.import_batch = import_batch
    
    def log_action(self, 
                   action_type: AuditActionType,
                   description: str,
                   old_values: Dict = None,
                   new_values: Dict = None,
                   metadata: Dict = None,
                   success: bool = True,
                   error_message: str = "",
                   severity: str = 'INFO',
                   document_number: str = "",
                   account_code: str = "",
                   processing_time_ms: int = None):
        """ثبت یک عمل در audit trail"""
        
        audit_record = ImportAuditTrail(
            user=self.user,
            company=self.company,
            period=self.period,
            action_type=action_type.value,
            description=description,
            old_values=old_values,
            new_values=new_values,
            metadata=metadata,
            success=success,
            error_message=error_message,
            severity=severity,
            document_number=document_number,
            account_code=account_code,
            processing_time_ms=processing_time_ms,
            import_batch=self.import_batch
        )
        
        audit_record.save()
        return audit_record
    
    def log_file_upload(self, file_name: str, file_size: int, software_type: str):
        """ثبت آپلود فایل"""
        return self.log_action(
            action_type=AuditActionType.FILE_UPLOAD,
            description=f"آپلود فایل '{file_name}' برای نرم‌افزار {software_type}",
            metadata={
                'file_name': file_name,
                'file_size': file_size,
                'software_type': software_type
            }
        )
    
    def log_validation_result(self, validation_results: Dict[str, Any], document_count: int):
        """ثبت نتایج اعتبارسنجی"""
        critical_issues = sum(
            len(issues) for validator in validation_results.values() 
            for severity, issues in validator.get('issues', {}).items() 
            if severity in ['CRITICAL', 'critical']
        )
        
        return self.log_action(
            action_type=AuditActionType.VALIDATION,
            description=f"اعتبارسنجی {document_count} سند - {critical_issues} خطای بحرانی",
            metadata={
                'document_count': document_count,
                'validation_results': validation_results,
                'critical_issues_count': critical_issues
            },
            severity='ERROR' if critical_issues > 0 else 'INFO'
        )
    
    def log_data_import(self, imported_count: int, items_count: int, created_accounts: List[str]):
        """ثبت وارد کردن داده‌ها"""
        return self.log_action(
            action_type=AuditActionType.DATA_IMPORT,
            description=f"وارد کردن {imported_count} سند با {items_count} آرتیکل",
            metadata={
                'imported_documents': imported_count,
                'imported_items': items_count,
                'created_accounts': created_accounts,
                'created_accounts_count': len(created_accounts)
            }
        )
    
    def log_rollback(self, reason: str, rollback_stats: Dict[str, Any]):
        """ثبت عملیات rollback"""
        return self.log_action(
            action_type=AuditActionType.ROLLBACK,
            description=f"Rollback به دلیل: {reason}",
            metadata={
                'reason': reason,
                'rollback_stats': rollback_stats
            },
            success=False,
            severity='CRITICAL'
        )
    
    def log_code_creation(self, account_code: str, account_name: str, level: str):
        """ثبت ایجاد کدینگ جدید"""
        return self.log_action(
            action_type=AuditActionType.CODE_CREATION,
            description=f"ایجاد کدینگ جدید: {account_code} - {account_name}",
            new_values={
                'account_code': account_code,
                'account_name': account_name,
                'level': level
            },
            account_code=account_code
        )
    
    def get_import_audit_report(self, import_batch: str = None) -> Dict[str, Any]:
        """دریافت گزارش audit برای یک دسته وارداتی"""
        filters = {
            'company': self.company,
            'period': self.period
        }
        
        if import_batch:
            filters['import_batch'] = import_batch
        
        audit_records = ImportAuditTrail.objects.filter(**filters)
        
        # آمار کلی
        total_actions = audit_records.count()
        successful_actions = audit_records.filter(success=True).count()
        error_actions = audit_records.filter(success=False).count()
        
        # گروه‌بندی بر اساس نوع عمل
        actions_by_type = {}
        for action_type, _ in ImportAuditTrail.ACTION_TYPES:
            count = audit_records.filter(action_type=action_type).count()
            if count > 0:
                actions_by_type[action_type] = count
        
        # گروه‌بندی بر اساس سطح شدت
        severity_stats = {}
        for severity, _ in ImportAuditTrail.SEVERITY_LEVELS:
            count = audit_records.filter(severity=severity).count()
            if count > 0:
                severity_stats[severity] = count
        
        return {
            'summary': {
                'total_actions': total_actions,
                'successful_actions': successful_actions,
                'error_actions': error_actions,
                'success_rate': (successful_actions / total_actions * 100) if total_actions > 0 else 0
            },
            'by_action_type': actions_by_type,
            'by_severity': severity_stats,
            'timeline': self._generate_audit_timeline(audit_records),
            'recent_activities': list(audit_records[:10].values(
                'timestamp', 'action_type', 'description', 'success', 'severity'
            ))
        }
    
    def _generate_audit_timeline(self, audit_records) -> List[Dict]:
        """تولید جدول زمانی عملیات"""
        timeline = []
        
        for record in audit_records.order_by('timestamp'):
            timeline.append({
                'timestamp': record.timestamp,
                'action': record.get_action_type_display(),
                'description': record.description,
                'success': record.success,
                'severity': record.get_severity_display()
            })
        
        return timeline

# دکوراتور برای ثبت خودکار audit trail
def audit_trail(action_type: AuditActionType, description: str = None):
    """دکوراتور برای ثبت خودکار audit trail"""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(self, *args, **kwargs)
                
                # محاسبه زمان پردازش
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                # ثبت در audit trail
                if hasattr(self, 'audit_manager'):
                    self.audit_manager.log_action(
                        action_type=action_type,
                        description=description or f"اجرای {func.__name__}",
                        metadata={
                            'function': func.__name__,
                            'args': str(args),
                            'kwargs': str(kwargs)
                        },
                        success=True,
                        processing_time_ms=processing_time_ms
                    )
                
                return result
                
            except Exception as e:
                # ثبت خطا در audit trail
                if hasattr(self, 'audit_manager'):
                    self.audit_manager.log_action(
                        action_type=action_type,
                        description=f"خطا در اجرای {func.__name__}",
                        metadata={
                            'function': func.__name__,
                            'error': str(e)
                        },
                        success=False,
                        error_message=str(e),
                        severity='ERROR',
                        processing_time_ms=int((time.time() - start_time) * 1000)
                    )
                raise
        
        return wrapper
    return decorator