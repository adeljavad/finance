# data_importer/services/data_cleanup_service.py
import logging
from django.db import transaction
from financial_system.models.document_models import DocumentHeader, DocumentItem
from financial_system.models.coding_models import ChartOfAccounts
from ..models import FinancialFile, ImportJob
from users.models import Company, FinancialPeriod

logger = logging.getLogger(__name__)

class DataCleanupService:
    """سرویس پاک کردن داده‌های ایمپورت شده"""
    
    def __init__(self, company: Company, period: FinancialPeriod):
        self.company = company
        self.period = period
    
    def delete_imported_data(self) -> dict:
        """حذف داده‌های ایمپورت شده قبلی برای شرکت و دوره مشخص"""
        try:
            with transaction.atomic():
                # شمارش داده‌های قبل از حذف
                document_count = DocumentHeader.objects.filter(
                    company=self.company,
                    period=self.period
                ).count()
                
                item_count = DocumentItem.objects.filter(
                    document__company=self.company,
                    document__period=self.period
                ).count()
                
                # حذف آرتیکل‌ها
                deleted_items = DocumentItem.objects.filter(
                    document__company=self.company,
                    document__period=self.period
                ).delete()[0]
                
                # حذف اسناد
                deleted_documents = DocumentHeader.objects.filter(
                    company=self.company,
                    period=self.period
                ).delete()[0]
                
                logger.info(f"داده‌های ایمپورت شده حذف شدند: {deleted_documents} سند، {deleted_items} آرتیکل")
                
                return {
                    'deleted_documents': deleted_documents,
                    'deleted_items': deleted_items,
                    'status': 'success',
                    'message': f'داده‌های ایمپورت شده حذف شدند: {deleted_documents} سند، {deleted_items} آرتیکل'
                }
                
        except Exception as e:
            logger.error(f"خطا در حذف داده‌های ایمپورت شده: {e}")
            return {
                'deleted_documents': 0,
                'deleted_items': 0,
                'status': 'failed',
                'message': str(e)
            }
    
    def get_imported_data_stats(self) -> dict:
        """دریافت آمار داده‌های ایمپورت شده"""
        try:
            document_count = DocumentHeader.objects.filter(
                company=self.company,
                period=self.period
            ).count()
            
            item_count = DocumentItem.objects.filter(
                document__company=self.company,
                document__period=self.period
            ).count()
            
            return {
                'document_count': document_count,
                'item_count': item_count,
                'has_data': document_count > 0 or item_count > 0
            }
            
        except Exception as e:
            logger.error(f"خطا در دریافت آمار داده‌ها: {e}")
            return {
                'document_count': 0,
                'item_count': 0,
                'has_data': False
            }
    
    def delete_all_data(self) -> dict:
        """حذف کامل تمام داده‌های چهار جدول اصلی"""
        try:
            with transaction.atomic():
                # شمارش داده‌های قبل از حذف
                stats_before = self._get_all_data_stats()
                
                # 1. حذف آرتیکل‌های سند
                deleted_items = DocumentItem.objects.filter(
                    document__company=self.company,
                    document__period=self.period
                ).delete()[0]
                
                # 2. حذف اسناد
                deleted_documents = DocumentHeader.objects.filter(
                    company=self.company,
                    period=self.period
                ).delete()[0]
                
                # 3. حذف فایل‌های ایمپورت شده
                deleted_files = FinancialFile.objects.filter(
                    company=self.company,
                    financial_period=self.period
                ).delete()[0]
                
                # 4. حذف کدینگ‌ها
                deleted_accounts = ChartOfAccounts.objects.filter(
                    # حذف تمام حساب‌های مربوط به این شرکت
                    # توجه: این ممکن است حساب‌های مشترک با شرکت‌های دیگر را حذف کند
                    # در صورت نیاز می‌توانید شرط شرکت اضافه کنید
                ).delete()[0]
                
                # شمارش داده‌های بعد از حذف
                stats_after = self._get_all_data_stats()
                
                logger.info(f"✅ تمام داده‌ها حذف شدند:")
                logger.info(f"   - اسناد: {deleted_documents}")
                logger.info(f"   - آرتیکل‌ها: {deleted_items}")
                logger.info(f"   - فایل‌ها: {deleted_files}")
                logger.info(f"   - حساب‌ها: {deleted_accounts}")
                
                return {
                    'status': 'success',
                    'message': 'تمام داده‌ها با موفقیت حذف شدند',
                    'deleted_data': {
                        'documents': deleted_documents,
                        'items': deleted_items,
                        'files': deleted_files,
                        'accounts': deleted_accounts
                    },
                    'stats_before': stats_before,
                    'stats_after': stats_after
                }
                
        except Exception as e:
            logger.error(f"❌ خطا در حذف کامل داده‌ها: {e}")
            return {
                'status': 'failed',
                'message': f'خطا در حذف داده‌ها: {str(e)}',
                'deleted_data': {
                    'documents': 0,
                    'items': 0,
                    'files': 0,
                    'accounts': 0
                }
            }
    
    def _get_all_data_stats(self) -> dict:
        """دریافت آمار تمام داده‌ها"""
        return {
            'documents': DocumentHeader.objects.filter(
                company=self.company,
                period=self.period
            ).count(),
            'items': DocumentItem.objects.filter(
                document__company=self.company,
                document__period=self.period
            ).count(),
            'files': FinancialFile.objects.filter(
                company=self.company,
                financial_period=self.period
            ).count(),
            'accounts': ChartOfAccounts.objects.count()  # تعداد کل حساب‌ها
        }


def cleanup_all_data(company_id: int, period_id: int) -> dict:
    """تابع اصلی برای پاک کردن کامل تمام داده‌ها"""
    try:
        company = Company.objects.get(id=company_id)
        period = FinancialPeriod.objects.get(id=period_id)
        
        cleanup_service = DataCleanupService(company, period)
        return cleanup_service.delete_all_data()
        
    except Company.DoesNotExist:
        logger.error(f"شرکت با شناسه {company_id} یافت نشد")
        return {
            'status': 'failed',
            'message': 'شرکت یافت نشد'
        }
    except FinancialPeriod.DoesNotExist:
        logger.error(f"دوره مالی با شناسه {period_id} یافت نشد")
        return {
            'status': 'failed',
            'message': 'دوره مالی یافت نشد'
        }
    except Exception as e:
        logger.error(f"خطا در پاک کردن داده‌ها: {e}")
        return {
            'status': 'failed',
            'message': str(e)
        }
