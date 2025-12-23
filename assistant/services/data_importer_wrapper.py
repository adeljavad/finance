"""
سرویس wrapper برای استفاده از data_importer در assistant
"""
import os
import uuid
import logging
from typing import Dict, Any, Optional
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

class DataImporterWrapper:
    """Wrapper برای استفاده از data_importer در assistant"""
    
    def __init__(self):
        self.default_company = None
        self.default_period = None
        self.default_user = None
        
    def _ensure_default_company_and_period(self):
        """ایجاد company و financial_period پیش‌فرض در صورت عدم وجود"""
        try:
            from users.models import Company, FinancialPeriod
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            # پیدا کردن یا ایجاد کاربر سیستم
            self.default_user, created = User.objects.get_or_create(
                username='system_user',
                defaults={
                    'email': 'system@example.com',
                    'is_active': True,
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            
            if created:
                logger.info("✅ کاربر سیستم ایجاد شد")
            
            # پیدا کردن یا ایجاد company پیش‌فرض
            self.default_company, created = Company.objects.get_or_create(
                name='Anonymous Users',
                defaults={
                    'economic_code': '0000000000',
                    'national_code': '0000000000',
                    'company_type': 'SERVICE',
                    'address': 'سیستم',
                    'phone': '00000000000',
                    'currency': 'IRR',
                    'created_by': self.default_user,
                    'is_active': True,
                    'is_verified': True
                }
            )
            
            if created:
                logger.info(f"✅ شرکت پیش‌فرض ایجاد شد: {self.default_company.name}")
            
            # پیدا کردن یا ایجاد financial_period پیش‌فرض
            current_year = timezone.now().year
            start_date = timezone.datetime(current_year, 1, 1).date()
            end_date = timezone.datetime(current_year, 12, 29).date()
            
            self.default_period, created = FinancialPeriod.objects.get_or_create(
                company=self.default_company,
                name=f'دوره {current_year}',
                defaults={
                    'start_date': start_date,
                    'end_date': end_date,
                    'is_active': True,
                    'created_by': self.default_user
                }
            )
            
            if created:
                logger.info(f"✅ دوره مالی پیش‌فرض ایجاد شد: {self.default_period.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در ایجاد company و period پیش‌فرض: {e}")
            return False
    
    def process_file(self, file_content, filename: str, user_id: str = None) -> Dict[str, Any]:
        """پردازش فایل با استفاده از data_importer"""
        try:
            # اطمینان از وجود company و period پیش‌فرض
            if not self._ensure_default_company_and_period():
                return {
                    'success': False,
                    'error': 'خطا در ایجاد company و period پیش‌فرض'
                }
            
            # ذخیره فایل در temp_uploads
            import tempfile
            from pathlib import Path
            
            upload_dir = Path('temp_uploads')
            upload_dir.mkdir(exist_ok=True)
            
            file_name = f"{uuid.uuid4()}_{filename}"
            file_path = upload_dir / file_name
            
            # نوشتن محتوای فایل
            if hasattr(file_content, 'read'):
                # اگر file_content یک فایل آپلود شده است
                with open(file_path, 'wb+') as destination:
                    for chunk in file_content.chunks():
                        destination.write(chunk)
            else:
                # اگر file_content بایت‌ها است
                with open(file_path, 'wb') as f:
                    f.write(file_content)
            
            logger.info(f"📁 فایل ذخیره شد: {file_path}")
            
            # تحلیل ساختار فایل
            from data_importer.analyzers.excel_structure_analyzer import ExcelStructureAnalyzer
            
            analyzer = ExcelStructureAnalyzer()
            analysis_result = analyzer.analyze_excel_structure(str(file_path))
            
            if 'error' in analysis_result:
                # حذف فایل در صورت خطا
                if file_path.exists():
                    file_path.unlink()
                
                return {
                    'success': False,
                    'error': f"خطا در تحلیل فایل: {analysis_result['error']}"
                }
            
            # ایجاد رکورد FinancialFile
            from data_importer.models import FinancialFile
            
            # تبدیل numpy types برای JSON
            def convert_numpy_types(obj):
                import numpy as np
                if isinstance(obj, (np.integer, np.floating)):
                    return obj.item()
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(item) for item in obj]
                else:
                    return obj
            
            safe_analysis_result = convert_numpy_types(analysis_result) if analysis_result and isinstance(analysis_result, dict) else {}
            safe_columns_mapping = convert_numpy_types(analysis_result.get('columns_mapping', {})) if analysis_result and isinstance(analysis_result, dict) else {}
            
            software_type = str(safe_analysis_result.get('software_type', 'UNKNOWN'))
            confidence_score = float(safe_analysis_result.get('confidence', 0.0))
            
            # ایجاد FinancialFile
            financial_file = FinancialFile.objects.create(
                file_name=file_name,
                original_name=filename,
                file_path=str(file_path),
                file_size=file_path.stat().st_size,
                company=self.default_company,
                financial_period=self.default_period,
                uploaded_by=self.default_user,
                analysis_result=safe_analysis_result,
                software_type=software_type,
                confidence_score=confidence_score,
                columns_mapping=safe_columns_mapping,
                status='ANALYZED'
            )
            
            logger.info(f"✅ فایل مالی ایجاد شد: {financial_file.id}")
            
            # وارد کردن داده‌ها
            from data_importer.services.data_integration_service import import_financial_data
            
            result = import_financial_data(financial_file.id, delete_existing_data=False)
            
            if result['status'] == 'success':
                return {
                    'success': True,
                    'message': f'فایل {filename} با موفقیت پردازش شد',
                    'file_id': financial_file.id,
                    'document_count': result['document_count'],
                    'item_count': result['item_count'],
                    'analysis_result': safe_analysis_result
                }
            else:
                return {
                    'success': False,
                    'error': f"خطا در وارد کردن داده‌ها: {', '.join(result.get('errors', []))}",
                    'file_id': financial_file.id
                }
            
        except Exception as e:
            logger.error(f"❌ خطا در پردازش فایل: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                'success': False,
                'error': f'خطا در پردازش فایل: {str(e)}'
            }
    
    def get_file_info(self, file_id: int) -> Optional[Dict[str, Any]]:
        """دریافت اطلاعات فایل"""
        try:
            from data_importer.models import FinancialFile
            
            financial_file = FinancialFile.objects.get(id=file_id)
            
            return {
                'id': financial_file.id,
                'filename': financial_file.original_name,
                'status': financial_file.status,
                'uploaded_at': financial_file.uploaded_at,
                'document_count': financial_file.total_documents,
                'item_count': financial_file.total_items,
                'software_type': financial_file.software_type
            }
            
        except FinancialFile.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"❌ خطا در دریافت اطلاعات فایل: {e}")
            return None
    
    def cleanup_file(self, file_id: int) -> bool:
        """پاک کردن فایل و داده‌های مرتبط"""
        try:
            from data_importer.models import FinancialFile
            from pathlib import Path
            
            financial_file = FinancialFile.objects.get(id=file_id)
            
            # حذف فایل فیزیکی
            file_path = Path(financial_file.file_path)
            if file_path.exists():
                file_path.unlink()
            
            # حذف رکورد دیتابیس
            financial_file.delete()
            
            logger.info(f"🗑️ فایل و داده‌های مرتبط حذف شدند: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در پاک کردن فایل: {e}")
            return False
