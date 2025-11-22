# data_importer/queues/import_queue.py
# from celery import Celery
from django.conf import settings
# import redis
from typing import Dict, Any, List
import json
import time
from datetime import datetime, timedelta

# پیکربندی Celery (موقتاً غیرفعال شده)
# app = Celery('data_importer')
# app.config_from_object('django.conf:settings', namespace='CELERY')
# app.autodiscover_tasks()

# اتصال به Redis برای مدیریت صف (موقتاً غیرفعال شده)
# redis_client = redis.Redis(
#     host=settings.REDIS_HOST,
#     port=settings.REDIS_PORT,
#     db=settings.REDIS_DB,
#     decode_responses=True
# )

class ImportQueueManager:
    def __init__(self):
        self.redis = redis_client
    
    def submit_import_job(self, file_path: str, company_id: int, period_id: int, user_id: int) -> str:
        """ثبت کار وارد کردن در صف"""
        job_id = f"import_{company_id}_{int(time.time())}"
        
        job_data = {
            'job_id': job_id,
            'file_path': file_path,
            'company_id': company_id,
            'period_id': period_id,
            'user_id': user_id,
            'status': 'PENDING',
            'submitted_at': datetime.now().isoformat(),
            'progress': 0,
            'estimated_time_remaining': None,
            'current_step': 'آماده‌سازی'
        }
        
        # ذخیره اطلاعات کار
        self.redis.set(f"import_job:{job_id}", json.dumps(job_data))
        self.redis.lpush('import_queue', job_id)
        
        # راه‌اندازی پردازش غیرهمزمان
        process_import_task.delay(job_id)
        
        return job_id
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """دریافت وضعیت کار"""
        job_data = self.redis.get(f"import_job:{job_id}")
        if job_data:
            return json.loads(job_data)
        return {'error': 'Job not found'}
    
    def update_job_progress(self, job_id: str, progress: int, current_step: str, 
                          details: Dict[str, Any] = None):
        """به‌روزرسانی پیشرفت کار"""
        job_data = self.get_job_status(job_id)
        if 'error' not in job_data:
            job_data['progress'] = progress
            job_data['current_step'] = current_step
            job_data['last_updated'] = datetime.now().isoformat()
            
            if details:
                job_data['details'] = details
            
            # محاسبه زمان باقی‌مانده تخمینی
            if progress > 0:
                elapsed = (datetime.now() - datetime.fromisoformat(
                    job_data['submitted_at'].replace('Z', '+00:00')
                )).total_seconds()
                total_estimated = elapsed / (progress / 100)
                remaining = total_estimated - elapsed
                job_data['estimated_time_remaining'] = max(0, int(remaining))
            
            self.redis.set(f"import_job:{job_id}", json.dumps(job_data))
    
    def cancel_job(self, job_id: str) -> bool:
        """لغو کار"""
        job_data = self.get_job_status(job_id)
        if 'error' not in job_data and job_data['status'] in ['PENDING', 'PROCESSING']:
            job_data['status'] = 'CANCELLED'
            job_data['cancelled_at'] = datetime.now().isoformat()
            self.redis.set(f"import_job:{job_id}", json.dumps(job_data))
            
            # حذف از صف
            self.redis.lrem('import_queue', 0, job_id)
            return True
        return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """دریافت آمار صف"""
        queue_length = self.redis.llen('import_queue')
        pending_jobs = []
        
        for job_id in self.redis.lrange('import_queue', 0, -1):
            job_data = self.get_job_status(job_id)
            if job_data.get('status') == 'PENDING':
                pending_jobs.append(job_data)
        
        active_jobs = []
        for key in self.redis.keys('import_job:*'):
            job_data = json.loads(self.redis.get(key))
            if job_data.get('status') == 'PROCESSING':
                active_jobs.append(job_data)
        
        return {
            'queue_length': queue_length,
            'pending_jobs': len(pending_jobs),
            'active_jobs': len(active_jobs),
            'estimated_wait_time': self._calculate_wait_time(pending_jobs)
        }
    
    def _calculate_wait_time(self, pending_jobs: List[Dict]) -> int:
        """محاسبه زمان انتظار تخمینی"""
        if not pending_jobs:
            return 0
        
        # میانگین زمان پردازش بر اساس تاریخچه (ثانیه)
        avg_processing_time = 300  # 5 دقیقه
        
        return len(pending_jobs) * avg_processing_time

@app.task(bind=True)
def process_import_task(self, job_id: str):
    """وظیفه پردازش وارد کردن داده‌ها"""
    queue_manager = ImportQueueManager()
    
    try:
        # به‌روزرسانی وضعیت به در حال پردازش
        queue_manager.update_job_progress(job_id, 5, 'دریافت فایل')
        
        # دریافت اطلاعات کار
        job_data = queue_manager.get_job_status(job_id)
        file_path = job_data['file_path']
        company_id = job_data['company_id']
        period_id = job_data['period_id']
        
        # پردازش فایل
        from .services.auto_detection_service import AutoDetectionService
        from .validators.duplicate_validator import DuplicateDocumentValidator
        from .validators.sequence_validator import DocumentSequenceValidator
        from .validators.coding_validator import CodingExistenceValidator
        
        # مرحله ۱: تحلیل ساختار
        queue_manager.update_job_progress(job_id, 20, 'تحلیل ساختار فایل')
        detection_service = AutoDetectionService()
        analysis_result = detection_service.detect_and_map_columns(file_path, company_id)
        
        if not analysis_result['success']:
            queue_manager.update_job_progress(job_id, 100, 'خطا در تحلیل', {
                'error': analysis_result['error']
            })
            return
        
        # مرحله ۲: اعتبارسنجی
        queue_manager.update_job_progress(job_id, 40, 'اعتبارسنجی داده‌ها')
        
        # اعتبارسنجی تکراری
        duplicate_validator = DuplicateDocumentValidator(company_id, period_id)
        duplicate_results = duplicate_validator.check_duplicate_documents(
            analysis_result['document_data']
        )
        
        # اعتبارسنجی توالی
        sequence_validator = DocumentSequenceValidator(company_id, period_id)
        sequence_results = sequence_validator.validate_document_sequence(
            analysis_result['document_data']
        )
        
        # اعتبارسنجی کدینگ
        coding_validator = CodingExistenceValidator(company_id)
        coding_results = coding_validator.validate_coding_existence(
            analysis_result['document_data']
        )
        
        # مرحله ۳: تولید گزارش
        queue_manager.update_job_progress(job_id, 60, 'تولید گزارش اعتبارسنجی')
        
        from .reports.validation_report import ValidationReportGenerator
        report_generator = ValidationReportGenerator(
            company_name="شرکت نمونه",  # باید از دیتابیس گرفته شود
            period_name="دوره نمونه"    # باید از دیتابیس گرفته شود
        )
        
        validation_results = {
            'duplicate': duplicate_results,
            'sequence': sequence_results,
            'coding': coding_results,
            'document_count': len(analysis_result['document_data']),
            'item_count': sum(len(doc.get('items', [])) for doc in analysis_result['document_data'])
        }
        
        report = report_generator.generate_comprehensive_report(validation_results)
        
        # مرحله ۴: وارد کردن داده‌ها (اگر خطای بحرانی وجود ندارد)
        queue_manager.update_job_progress(job_id, 80, 'وارد کردن داده‌ها')
        
        critical_errors = any(
            len(results.get('exact_duplicates', [])) > 0 
            for results in [duplicate_results]
        )
        
        if not critical_errors:
            from .services.data_import_service import DataImportService
            import_service = DataImportService(company_id, period_id)
            import_result = import_service.import_documents(analysis_result['document_data'])
            
            queue_manager.update_job_progress(job_id, 100, 'تکمیل شده', {
                'imported_count': import_result['imported_count'],
                'report': report
            })
        else:
            queue_manager.update_job_progress(job_id, 100, 'تکمیل شده با خطا', {
                'report': report,
                'reason': 'خطاهای بحرانی مانع از وارد کردن داده‌ها شد'
            })
    
    except Exception as e:
        queue_manager.update_job_progress(job_id, 100, 'خطای سیستمی', {
            'error': str(e),
            'traceback': self.request.chain
        })
