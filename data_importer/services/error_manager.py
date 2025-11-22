# data_importer/services/error_manager.py
from django.db import transaction
from django.utils import timezone
from typing import List, Dict, Any, Optional
import logging
from enum import Enum

class ErrorSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM" 
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class DataImportErrorManager:
    def __init__(self, import_batch: str, company_id: int):
        self.import_batch = import_batch
        self.company_id = company_id
        self.errors = []
        self.logger = logging.getLogger(__name__)
    
    def add_error(self, 
                  error_type: str,
                  message: str, 
                  severity: ErrorSeverity,
                  document_data: Optional[Dict] = None,
                  field_name: Optional[str] = None,
                  original_value: Any = None,
                  suggested_fix: Optional[str] = None):
        """ثبت خطای جدید"""
        error_record = {
            'timestamp': timezone.now(),
            'error_type': error_type,
            'message': message,
            'severity': severity.value,
            'document_data': document_data,
            'field_name': field_name,
            'original_value': original_value,
            'suggested_fix': suggested_fix,
            'import_batch': self.import_batch,
            'company_id': self.company_id
        }
        
        self.errors.append(error_record)
        
        # لاگ کردن بر اساس سطح شدت
        log_message = f"[{self.import_batch}] {error_type}: {message}"
        if severity == ErrorSeverity.CRITICAL:
            self.logger.error(log_message)
        elif severity == ErrorSeverity.HIGH:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def has_errors(self, min_severity: ErrorSeverity = ErrorSeverity.LOW) -> bool:
        """بررسی وجود خطا با سطح شدت مشخص"""
        severity_order = {e.value: i for i, e in enumerate(ErrorSeverity)}
        min_level = severity_order[min_severity.value]
        
        return any(severity_order[error['severity']] >= min_level for error in self.errors)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """دریافت خلاصه خطاها"""
        if not self.errors:
            return {'total_errors': 0, 'by_severity': {}, 'by_type': {}}
        
        by_severity = {}
        by_type = {}
        
        for error in self.errors:
            # گروه‌بندی بر اساس شدت
            severity = error['severity']
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            # گروه‌بندی بر اساس نوع
            error_type = error['error_type']
            by_type[error_type] = by_type.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.errors),
            'by_severity': by_severity,
            'by_type': by_type,
            'has_critical_errors': any(e['severity'] == ErrorSeverity.CRITICAL.value for e in self.errors),
            'import_batch': self.import_batch
        }
    
    def can_proceed_with_import(self) -> bool:
        """تعیین امکان ادامه عملیات وارد کردن"""
        critical_errors = [e for e in self.errors if e['severity'] == ErrorSeverity.CRITICAL.value]
        return len(critical_errors) == 0
    
    def generate_error_report(self) -> Dict[str, Any]:
        """تولید گزارش کامل خطاها"""
        summary = self.get_error_summary()
        
        return {
            'summary': summary,
            'errors_by_severity': self._group_errors_by_severity(),
            'recommended_actions': self._generate_recommended_actions(),
            'successful_import_possible': self.can_proceed_with_import()
        }
    
    def _group_errors_by_severity(self) -> Dict[str, List]:
        """گروه‌بندی خطاها بر اساس شدت"""
        grouped = {severity.value: [] for severity in ErrorSeverity}
        
        for error in self.errors:
            grouped[error['severity']].append({
                'error_type': error['error_type'],
                'message': error['message'],
                'timestamp': error['timestamp'],
                'suggested_fix': error.get('suggested_fix'),
                'field_name': error.get('field_name')
            })
        
        return grouped
    
    def _generate_recommended_actions(self) -> List[str]:
        """تولید اقدامات توصیه شده بر اساس خطاها"""
        actions = []
        
        critical_errors = [e for e in self.errors if e['severity'] == ErrorSeverity.CRITICAL.value]
        high_errors = [e for e in self.errors if e['severity'] == ErrorSeverity.HIGH.value]
        
        if critical_errors:
            actions.append("به دلیل وجود خطاهای بحرانی، وارد کردن داده‌ها متوقف شد.")
            actions.append("لطفاً خطاهای بحرانی را برطرف کنید و مجدداً تلاش کنید.")
        
        if high_errors:
            actions.append("خطاهای مهم وجود دارد. توصیه می‌شود قبل از ادامه، این خطاها بررسی شوند.")
        
        # پیشنهادات خاص بر اساس نوع خطا
        error_types = set(e['error_type'] for e in self.errors)
        
        if 'DUPLICATE_DOCUMENT' in error_types:
            actions.append("اسناد تکراری شناسایی شد. لطفاً بررسی کنید آیا باید حذف شوند.")
        
        if 'MISSING_CODING' in error_types:
            actions.append("کدینگ‌های مفقود شناسایی شد. سیستم می‌تواند به صورت خودکار ایجاد کند.")
        
        if 'SEQUENCE_GAP' in error_types:
            actions.append("شکاف در توالی اسناد مشاهده شد. بررسی کنید اسناد مفقودی وجود دارد.")
        
        if not self.errors:
            actions.append("هیچ خطایی شناسایی نشد. می‌توانید با اطمینان ادامه دهید.")
        
        return actions

# استفاده عملی از سیستم مدیریت خطا
class DataImportOrchestrator:
    def __init__(self, company_id: int, period_id: int, file_path: str):
        self.company_id = company_id
        self.period_id = period_id
        self.file_path = file_path
        self.import_batch = f"IMP_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        self.error_manager = DataImportErrorManager(self.import_batch, company_id)
    
    def import_financial_data(self) -> Dict[str, Any]:
        """وارد کردن داده‌های مالی با مدیریت خطا"""
        try:
            with transaction.atomic():
                # 1. تحلیل ساختار فایل
                analysis_result = self._analyze_file_structure()
                if self.error_manager.has_errors(ErrorSeverity.HIGH):
                    return self.error_manager.generate_error_report()
                
                # 2. اعتبارسنجی داده‌ها
                validation_result = self._validate_data(analysis_result['document_data'])
                if self.error_manager.has_errors(ErrorSeverity.CRITICAL):
                    return self.error_manager.generate_error_report()
                
                # 3. وارد کردن داده‌ها
                if self.error_manager.can_proceed_with_import():
                    import_result = self._import_data(analysis_result['document_data'])
                    result = self.error_manager.generate_error_report()
                    result['import_result'] = import_result
                    return result
                else:
                    return self.error_manager.generate_error_report()
                    
        except Exception as e:
            self.error_manager.add_error(
                error_type="SYSTEM_ERROR",
                message=f"خطای سیستمی در هنگام وارد کردن داده‌ها: {str(e)}",
                severity=ErrorSeverity.CRITICAL
            )
            return self.error_manager.generate_error_report()