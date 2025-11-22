# data_importer/services/rollback_manager.py
from django.db import transaction
from django.db.models import Q
from financial_system.models import DocumentHeader, DocumentItem, ChartOfAccounts
from typing import List, Dict, Set
import logging
from datetime import datetime

class RollbackManager:
    def __init__(self, company_id: int, period_id: int):
        self.company_id = company_id
        self.period_id = period_id
        self.import_batch = None
        self.backup_data = {}
        self.logger = logging.getLogger(__name__)
    
    def start_import_session(self, import_batch: str):
        """شروع یک سشن وارد کردن با قابلیت rollback"""
        self.import_batch = import_batch
        self.backup_data = {
            'documents_backup': [],
            'items_backup': [],
            'created_accounts': set(),
            'session_start': datetime.now()
        }
        
        self.logger.info(f"شروع سشن وارد کردن: {import_batch}")
    
    def backup_existing_data(self, document_numbers: List[str]):
        """پشتیبان‌گیری از داده‌های موجود"""
        existing_documents = DocumentHeader.objects.filter(
            company_id=self.company_id,
            period_id=self.period_id,
            document_number__in=document_numbers
        )
        
        for doc in existing_documents:
            # پشتیبان‌گیری از سربرگ سند
            doc_backup = {
                'document': doc,
                'fields': {
                    'document_number': doc.document_number,
                    'document_date': doc.document_date,
                    'description': doc.description,
                    'total_debit': doc.total_debit,
                    'total_credit': doc.total_credit
                }
            }
            self.backup_data['documents_backup'].append(doc_backup)
            
            # پشتیبان‌گیری از آرتیکل‌ها
            items = DocumentItem.objects.filter(document=doc)
            for item in items:
                item_backup = {
                    'item': item,
                    'fields': {
                        'row_number': item.row_number,
                        'account_id': item.account_id,
                        'debit': item.debit,
                        'credit': item.credit,
                        'description': item.description
                    }
                }
                self.backup_data['items_backup'].append(item_backup)
    
    def track_created_accounts(self, account_codes: List[str]):
        """ردیابی حساب‌های ایجاد شده در این سشن"""
        self.backup_data['created_accounts'].update(account_codes)
    
    @transaction.atomic
    def rollback_import(self, reason: str = "خطا در پردازش") -> Dict[str, Any]:
        """انجام rollback برای سشن جاری"""
        try:
            rollback_stats = {
                'documents_rolled_back': 0,
                'items_rolled_back': 0,
                'accounts_deleted': 0,
                'errors': []
            }
            
            # حذف اسناد ایجاد شده در این سشن
            if self.import_batch:
                imported_documents = DocumentHeader.objects.filter(
                    company_id=self.company_id,
                    period_id=self.period_id,
                    import_batch=self.import_batch
                )
                
                rollback_stats['documents_rolled_back'] = imported_documents.count()
                
                # حذف آرتیکل‌های مرتبط
                for doc in imported_documents:
                    items_count = DocumentItem.objects.filter(document=doc).count()
                    DocumentItem.objects.filter(document=doc).delete()
                    rollback_stats['items_rolled_back'] += items_count
                
                imported_documents.delete()
            
            # حذف حساب‌های ایجاد شده در این سشن
            if self.backup_data['created_accounts']:
                created_accounts = ChartOfAccounts.objects.filter(
                    code__in=self.backup_data['created_accounts'],
                    created_from_excel=True  # فقط حساب‌های ایجاد شده از اکسل
                )
                
                rollback_stats['accounts_deleted'] = created_accounts.count()
                created_accounts.delete()
            
            # بازگرداندن داده‌های پشتیبان‌گیری شده
            self._restore_backup_data()
            
            self.logger.info(f"Rollback انجام شد: {reason}. آمار: {rollback_stats}")
            
            return {
                'success': True,
                'rollback_stats': rollback_stats,
                'reason': reason
            }
            
        except Exception as e:
            self.logger.error(f"خطا در حین rollback: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'rollback_stats': rollback_stats
            }
    
    def _restore_backup_data(self):
        """بازگردانی داده‌های پشتیبان‌گیری شده"""
        # بازگردانی اسناد
        for doc_backup in self.backup_data['documents_backup']:
            doc = doc_backup['document']
            for field, value in doc_backup['fields'].items():
                setattr(doc, field, value)
            doc.save()
        
        # بازگردانی آرتیکل‌ها
        for item_backup in self.backup_data['items_backup']:
            item = item_backup['item']
            for field, value in item_backup['fields'].items():
                setattr(item, field, value)
            item.save()
    
    def commit_import(self) -> Dict[str, Any]:
        """تأیید نهایی وارد کردن داده‌ها"""
        try:
            # پاک کردن پشتیبان‌ها
            self.backup_data.clear()
            
            # به‌روزرسانی وضعیت اسناد وارد شده
            if self.import_batch:
                imported_docs = DocumentHeader.objects.filter(
                    company_id=self.company_id,
                    period_id=self.period_id,
                    import_batch=self.import_batch
                )
                
                imported_docs.update(import_status='COMPLETED')
            
            self.logger.info(f"وارد کردن داده‌ها با موفقیت تأیید شد: {self.import_batch}")
            
            return {
                'success': True,
                'imported_count': imported_docs.count() if self.import_batch else 0,
                'import_batch': self.import_batch
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تأیید وارد کردن: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_rollback_point(self, description: str) -> str:
        """ایجاد نقطه بازگشت در طول پردازش"""
        rollback_point = f"RP_{int(datetime.now().timestamp())}"
        
        self.backup_data['rollback_points'] = self.backup_data.get('rollback_points', {})
        self.backup_data['rollback_points'][rollback_point] = {
            'description': description,
            'timestamp': datetime.now(),
            'document_count': DocumentHeader.objects.filter(
                company_id=self.company_id,
                import_batch=self.import_batch
            ).count(),
            'item_count': DocumentItem.objects.filter(
                document__company_id=self.company_id,
                document__import_batch=self.import_batch
            ).count()
        }
        
        return rollback_point

# استفاده در سرویس وارد کردن داده‌ها
class DataImportService:
    def __init__(self, company_id: int, period_id: int):
        self.company_id = company_id
        self.period_id = period_id
        self.rollback_manager = RollbackManager(company_id, period_id)
    
    @transaction.atomic
    def import_documents(self, document_data_list: List[Dict]) -> Dict[str, Any]:
        """وارد کردن اسناد با قابلیت rollback"""
        import_batch = f"IMP_{int(datetime.now().timestamp())}"
        
        try:
            # شروع سشن با قابلیت rollback
            self.rollback_manager.start_import_session(import_batch)
            
            # پشتیبان‌گیری از اسناد موجود با شماره‌های تکراری
            existing_doc_numbers = self._get_existing_document_numbers(document_data_list)
            if existing_doc_numbers:
                self.rollback_manager.backup_existing_data(existing_doc_numbers)
            
            created_accounts = []
            imported_docs = []
            
            for doc_data in document_data_list:
                # ایجاد سند
                document = self._create_document_header(doc_data, import_batch)
                imported_docs.append(document)
                
                # ایجاد آرتیکل‌ها
                for item_data in doc_data.get('items', []):
                    item = self._create_document_item(document, item_data)
                    
                    # ردیابی حساب‌های جدید
                    account_code = item_data.get('account_code')
                    if account_code and not self._account_exists(account_code):
                        created_accounts.append(account_code)
            
            # ردیابی حساب‌های ایجاد شده
            if created_accounts:
                self.rollback_manager.track_created_accounts(created_accounts)
            
            # تأیید نهایی
            commit_result = self.rollback_manager.commit_import()
            
            return {
                'success': True,
                'imported_count': len(imported_docs),
                'items_count': sum(len(doc_data.get('items', [])) for doc_data in document_data_list),
                'created_accounts_count': len(created_accounts),
                'import_batch': import_batch
            }
            
        except Exception as e:
            # انجام rollback در صورت خطا
            rollback_result = self.rollback_manager.rollback_import(str(e))
            
            return {
                'success': False,
                'error': str(e),
                'rollback_result': rollback_result
            }