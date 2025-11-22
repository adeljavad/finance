# data_importer/services/data_integration_service.py
import pandas as pd
import logging
from pathlib import Path
from django.db import transaction
from django.utils import timezone
from financial_system.models.document_models import DocumentHeader, DocumentItem
from financial_system.models.coding_models import ChartOfAccounts
from financial_system.services.balance_control_service import BalanceControlService
from .data_cleanup_service import DataCleanupService
from ..models import FinancialFile, ImportJob

logger = logging.getLogger(__name__)

class DataIntegrationService:
    """سرویس یکپارچه‌سازی داده‌های اکسل با سیستم مالی"""
    
    def __init__(self, financial_file: FinancialFile):
        self.financial_file = financial_file
        self.company = financial_file.company
        self.period = financial_file.financial_period
        self.import_job = None
        self.balance_service = BalanceControlService()
    
    def create_import_job(self) -> ImportJob:
        """ایجاد کار وارد کردن"""
        job_id = f"import_{self.company.id}_{int(timezone.now().timestamp())}"
        self.import_job = ImportJob.objects.create(
            job_id=job_id,
            financial_file=self.financial_file,
            status='PENDING'
        )
        return self.import_job
    
    def update_job_progress(self, progress: int, step: str):
        """به‌روزرسانی وضعیت کار"""
        if self.import_job:
            self.import_job.progress = progress
            self.import_job.current_step = step
            self.import_job.save()
    
    def read_excel_data(self) -> pd.DataFrame:
        """خواندن داده‌های اکسل"""
        try:
            file_path = Path(self.financial_file.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"فایل {file_path} یافت نشد")
            
            # خواندن فایل اکسل
            df = pd.read_excel(file_path)
            logger.info(f"فایل اکسل با {len(df)} ردیف خوانده شد")
            return df
            
        except Exception as e:
            logger.error(f"خطا در خواندن فایل اکسل: {e}")
            raise
    
    def validate_data_structure(self, df: pd.DataFrame) -> dict:
        """اعتبارسنجی ساختار داده‌ها با تحلیل پیشرفته"""
        results = {
            'errors': [],
            'warnings': [],
            'balance_analysis': {},
            'suggestions': []
        }
        
        # استفاده از نگاشت ستون‌ها از تحلیل فایل
        column_mapping = self.financial_file.columns_mapping or {}
        
        # ترجمه نام‌های استاندارد به نام‌های واقعی ستون‌ها
        mapped_columns = {
            'document_number': column_mapping.get('document_number', 'شماره سند'),
            'document_date': column_mapping.get('document_date', 'تاریخ سند'),
            'document_description': column_mapping.get('document_description', 'شرح سند'),
            'account_code': column_mapping.get('account_code', 'کد حساب'),
            'account_description': column_mapping.get('account_description', 'شرح حساب'),
            'debit': column_mapping.get('debit', 'بدهکار'),
            'credit': column_mapping.get('credit', 'بستانکار')
        }
        
        # بررسی ستون‌های ضروری با استفاده از نام‌های واقعی
        required_columns = [
            mapped_columns['document_number'],
            mapped_columns['account_code'], 
            mapped_columns['debit'],
            mapped_columns['credit']
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            # نمایش نام‌های استاندارد برای کاربر
            persian_names = {
                'document_number': 'شماره سند',
                'account_code': 'کد حساب',
                'debit': 'بدهکار',
                'credit': 'بستانکار'
            }
            missing_standard = []
            for col in missing_columns:
                for standard_name, actual_name in mapped_columns.items():
                    if actual_name == col:
                        missing_standard.append(persian_names.get(standard_name, standard_name))
                        break
            
            results['errors'].append(f"ستون‌های ضروری یافت نشد: {', '.join(missing_standard)}")
        
        # بررسی مقادیر خالی در ستون‌های کلیدی
        for col_type, col_name in mapped_columns.items():
            if col_type in ['document_number', 'account_code', 'debit', 'credit']:
                if col_name in df.columns and df[col_name].isna().any():
                    results['warnings'].append(f"مقادیر خالی در ستون {col_name}")
        
        # تحلیل پیشرفته توازن
        if mapped_columns['debit'] in df.columns and mapped_columns['credit'] in df.columns:
            balance_analysis = self._analyze_balance_advanced(df, mapped_columns)
            results['balance_analysis'] = balance_analysis
            
            if not balance_analysis['is_balanced']:
                results['warnings'].append(
                    f"عدم توازن: جمع بدهکار={balance_analysis['total_debit']}, "
                    f"جمع بستانکار={balance_analysis['total_credit']}, "
                    f"تفاوت={balance_analysis['difference']}"
                )
                
                # اضافه کردن پیشنهادات برای اصلاح
                results['suggestions'].extend(balance_analysis['suggestions'])
        
        return results
    
    def _analyze_balance_advanced(self, df: pd.DataFrame, mapped_columns: dict) -> dict:
        """تحلیل پیشرفته توازن داده‌ها"""
        total_debit = df[mapped_columns['debit']].sum()
        total_credit = df[mapped_columns['credit']].sum()
        difference = abs(total_debit - total_credit)
        is_balanced = difference <= 0.01
        
        # تحلیل اسناد نامتوازن
        unbalanced_documents = []
        suggestions = []
        
        if not is_balanced:
            # گروه‌بندی بر اساس شماره سند برای تحلیل دقیق‌تر
            grouped_data = df.groupby(mapped_columns['document_number'])
            
            for doc_number, group_df in grouped_data:
                doc_debit = group_df[mapped_columns['debit']].sum()
                doc_credit = group_df[mapped_columns['credit']].sum()
                doc_difference = abs(doc_debit - doc_credit)
                
                if doc_difference > 0.01:
                    unbalanced_documents.append({
                        'document_number': doc_number,
                        'debit': doc_debit,
                        'credit': doc_credit,
                        'difference': doc_difference,
                        'row_count': len(group_df)
                    })
            
            # تولید پیشنهادات
            suggestions = self._generate_balance_suggestions(df, difference, unbalanced_documents, mapped_columns)
        
        return {
            'is_balanced': is_balanced,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'difference': difference,
            'unbalanced_documents': unbalanced_documents,
            'suggestions': suggestions,
            'document_count': len(df.groupby(mapped_columns['document_number'])),
            'total_rows': len(df)
        }
    
    def _generate_balance_suggestions(self, df: pd.DataFrame, difference: float, unbalanced_docs: list, mapped_columns: dict) -> list:
        """تولید پیشنهادات برای اصلاح توازن"""
        suggestions = []
        
        # پیشنهاد 1: اضافه کردن ردیف تنظیمی
        suggestions.append({
            'type': 'ADD_ADJUSTMENT_ROW',
            'description': f'افزودن ردیف تنظیمی برای تفاوت {difference} ریال',
            'implementation': 'AUTO',
            'impact': 'LOW'
        })
        
        # پیشنهاد 2: بررسی بزرگترین مقادیر
        largest_debit = df.nlargest(3, mapped_columns['debit'])[[mapped_columns['document_number'], mapped_columns['debit']]]
        largest_credit = df.nlargest(3, mapped_columns['credit'])[[mapped_columns['document_number'], mapped_columns['credit']]]
        
        suggestions.append({
            'type': 'REVIEW_LARGE_VALUES',
            'description': 'بررسی بزرگترین مقادیر بدهکار و بستانکار',
            'implementation': 'MANUAL',
            'impact': 'MEDIUM',
            'details': {
                'largest_debit': largest_debit.to_dict('records'),
                'largest_credit': largest_credit.to_dict('records')
            }
        })
        
        # پیشنهاد 3: تمرکز بر اسناد مشکل‌دار
        if unbalanced_docs:
            problematic_docs = sorted(unbalanced_docs, key=lambda x: x['difference'], reverse=True)[:3]
            suggestions.append({
                'type': 'FOCUS_PROBLEMATIC_DOCUMENTS',
                'description': 'تمرکز بر اسناد با بیشترین تفاوت توازن',
                'implementation': 'MANUAL',
                'impact': 'HIGH',
                'details': {
                    'problematic_documents': problematic_docs
                }
            })
        
        return suggestions
    
    def create_chart_of_accounts_hierarchy(self, row: pd.Series) -> ChartOfAccounts:
        """ایجاد سلسله مراتب کامل حساب‌ها از داده‌های راهکاران"""
        try:
            # استفاده از نگاشت ستون‌ها
            column_mapping = self.financial_file.columns_mapping or {}
            mapped_columns = {
                'title1': column_mapping.get('title1', 'Title1'),
                'code1': column_mapping.get('code1', 'Code1'),
                'title2': column_mapping.get('title2', 'Title2'),
                'code2': column_mapping.get('code2', 'Code2'),
                'title3': column_mapping.get('title3', 'Title3'),
                'code3': column_mapping.get('code3', 'Code3'),
                'title4': column_mapping.get('title4', 'Title4'),
                'code4': column_mapping.get('code4', 'Code4'),
            }
            
            # استخراج داده‌های کدینگ
            code1 = str(row[mapped_columns['code1']]) if pd.notna(row[mapped_columns['code1']]) else None
            title1 = str(row[mapped_columns['title1']]) if pd.notna(row[mapped_columns['title1']]) else None
            code2 = str(row[mapped_columns['code2']]) if pd.notna(row[mapped_columns['code2']]) else None
            title2 = str(row[mapped_columns['title2']]) if pd.notna(row[mapped_columns['title2']]) else None
            code3 = str(row[mapped_columns['code3']]) if pd.notna(row[mapped_columns['code3']]) else None
            title3 = str(row[mapped_columns['title3']]) if pd.notna(row[mapped_columns['title3']]) else None
            code4 = str(row[mapped_columns['code4']]) if pd.notna(row[mapped_columns['code4']]) else None
            title4 = str(row[mapped_columns['title4']]) if pd.notna(row[mapped_columns['title4']]) else None
            
            # ایجاد حساب‌های سلسله مراتب از بالا به پایین
            parent_account = None
            
            # سطح 1: گروه (CLASS)
            if code1 and title1:
                parent_account = self._get_or_create_account(
                    code=code1,
                    name=title1,
                    level='CLASS',
                    parent=None
                )
            
            # سطح 2: کل (SUBCLASS)
            if code2 and title2 and parent_account:
                parent_account = self._get_or_create_account(
                    code=code2,
                    name=title2,
                    level='SUBCLASS',
                    parent=parent_account
                )
            
            # سطح 3: معین (DETAIL)
            if code3 and title3 and parent_account:
                parent_account = self._get_or_create_account(
                    code=code3,
                    name=title3,
                    level='DETAIL',
                    parent=parent_account
                )
            
            # سطح 4: تفصیلی (DETAIL)
            if code4 and title4 and parent_account:
                final_account = self._get_or_create_account(
                    code=code4,
                    name=title4,
                    level='DETAIL',
                    parent=parent_account
                )
                return final_account
            
            # اگر سطح تفصیلی وجود نداشت، از سطح معین استفاده کن
            if parent_account:
                return parent_account
            
            # اگر هیچ سطحی وجود نداشت، حساب موقت ایجاد کن
            return self._get_or_create_account(
                code='99999',
                name='حساب موقت',
                level='DETAIL',
                parent=None
            )
            
        except Exception as e:
            logger.error(f"خطا در ایجاد سلسله مراتب حساب‌ها: {e}")
            raise
    
    def _get_or_create_account(self, code: str, name: str, level: str, parent: ChartOfAccounts = None) -> ChartOfAccounts:
        """ایجاد یا بازیابی حساب با مدیریت تکراری بودن"""
        try:
            # جستجوی حساب بر اساس کد و سطح
            account = ChartOfAccounts.objects.filter(
                code=code,
                level=level
            ).first()
            
            if not account:
                # ایجاد حساب جدید
                account = ChartOfAccounts.objects.create(
                    code=code,
                    name=name,
                    level=level,
                    parent=parent
                )
                logger.info(f"حساب جدید ایجاد شد: {code} - {name} ({level})")
            else:
                # به‌روزرسانی حساب موجود
                if account.name != name or account.parent != parent:
                    account.name = name
                    account.parent = parent
                    account.save()
                    logger.info(f"حساب به‌روزرسانی شد: {code} - {name}")
            
            return account
            
        except Exception as e:
            logger.error(f"خطا در ایجاد/بازیابی حساب {code}: {e}")
            raise
    
    def map_account_code(self, account_code: str) -> ChartOfAccounts:
        """مپ کردن کد حساب به مدل ChartOfAccounts (برای سازگاری با کد قدیمی)"""
        try:
            # جستجوی حساب بر اساس کد
            account = ChartOfAccounts.objects.filter(
                code=account_code
            ).first()
            
            if not account:
                # اگر حساب پیدا نشد، یک حساب موقت ایجاد می‌کنیم
                account = ChartOfAccounts.objects.create(
                    code=account_code,
                    name=f"حساب {account_code}",
                    level='DETAIL'
                )
                logger.info(f"حساب موقت ایجاد شد: {account_code}")
            
            return account
            
        except Exception as e:
            logger.error(f"خطا در مپ کردن حساب {account_code}: {e}")
            raise
    
    def create_documents_from_dataframe(self, df: pd.DataFrame, delete_existing_data: bool = False) -> dict:
        """ایجاد اسناد مالی از داده‌های DataFrame"""
        created_documents = 0
        created_items = 0
        duplicate_documents = 0
        errors = []
        
        try:
            # استفاده از نگاشت ستون‌ها
            column_mapping = self.financial_file.columns_mapping or {}
            mapped_columns = {
                'document_number': column_mapping.get('document_number', 'شماره سند'),
                'document_date': column_mapping.get('document_date', 'تاریخ سند'),
                'document_description': column_mapping.get('document_description', 'شرح سند'),
                'account_code': column_mapping.get('account_code', 'کد حساب'),
                'debit': column_mapping.get('debit', 'بدهکار'),
                'credit': column_mapping.get('credit', 'بستانکار')
            }
            
            # گروه‌بندی داده‌ها بر اساس شماره سند
            grouped_data = df.groupby(mapped_columns['document_number'])
            
            for document_number, group_df in grouped_data:
                try:
                    # لاگ وضعیت حذف داده‌ها - با جزئیات بیشتر
                    logger.info(f"🔍 پردازش سند {document_number}")
                    logger.info(f"🔍 delete_existing_data در create_documents_from_dataframe: {delete_existing_data}")
                    logger.info(f"🔍 نوع delete_existing_data: {type(delete_existing_data)}")
                    
                    # بررسی وجود سند تکراری
                    existing_document = DocumentHeader.objects.filter(
                        company=self.company,
                        period=self.period,
                        document_number=document_number
                    ).first()
                    
                    logger.info(f"🔍 سند {document_number} در دیتابیس وجود دارد: {existing_document is not None}")
                    
                    if existing_document:
                        if delete_existing_data:
                            # اگر delete_existing_data=True باشد، سند تکراری حذف می‌شود
                            logger.info(f"🗑️ حذف سند تکراری: {document_number}")
                            existing_document.delete()
                            logger.info(f"✅ سند تکراری حذف شد: {document_number}")
                            
                            # ایجاد سربرگ سند جدید
                            document_header = self._create_document_header(document_number, group_df, mapped_columns)
                            created_documents += 1
                            
                            # ایجاد آرتیکل‌های سند
                            for index, row in group_df.iterrows():
                                self._create_document_item(document_header, row, index + 1, mapped_columns)
                                created_items += 1
                            
                        else:
                            # اگر delete_existing_data=False باشد، سند تکراری نادیده گرفته می‌شود
                            duplicate_documents += 1
                            logger.warning(f"❌ سند تکراری نادیده گرفته شد: {document_number}")
                            continue
                    else:
                        logger.info(f"✅ سند جدید: {document_number} (سند تکراری وجود ندارد)")
                        
                        # ایجاد سربرگ سند جدید
                        document_header = self._create_document_header(document_number, group_df, mapped_columns)
                        created_documents += 1
                        
                        # ایجاد آرتیکل‌های سند
                        for index, row in group_df.iterrows():
                            self._create_document_item(document_header, row, index + 1, mapped_columns)
                            created_items += 1
                    
                    # اگر delete_existing_data=True باشد، لاگ بزن که سند ایجاد می‌شود
                    if delete_existing_data:
                        logger.info(f"✅ ایجاد سند جدید: {document_number} (داده‌های قبلی حذف شده‌اند)")
                        
                except Exception as e:
                    errors.append(f"خطا در ایجاد سند {document_number}: {str(e)}")
                    logger.error(f"خطا در ایجاد سند {document_number}: {e}")
                    continue
            
            result = {
                'document_count': created_documents,
                'item_count': created_items,
                'duplicate_documents': duplicate_documents,
                'status': 'success'
            }
            
            if errors:
                result['warnings'] = errors
                result['status'] = 'partial_success'
            
            return result
            
        except Exception as e:
            logger.error(f"خطا در ایجاد اسناد: {e}")
            raise
    
    def _create_document_header(self, document_number: str, group_df: pd.DataFrame, mapped_columns: dict) -> DocumentHeader:
        """ایجاد سربرگ سند"""
        try:
            # محاسبه جمع بدهکار و بستانکار
            total_debit = float(group_df[mapped_columns['debit']].sum())
            total_credit = float(group_df[mapped_columns['credit']].sum())
            
            # بررسی توازن
            is_balanced = abs(total_debit - total_credit) <= 0.01
            
            # ذخیره تاریخ فارسی به صورت مستقیم (بدون تبدیل)
            document_date = None
            if mapped_columns['document_date'] in group_df.columns:
                persian_date = group_df[mapped_columns['document_date']].iloc[0]
                # تبدیل به رشته و حذف فاصله‌های اضافی
                if pd.notna(persian_date):
                    document_date = str(persian_date).strip()
            
            # ایجاد سند با توضیحات خالی (توضیحات به آیتم‌ها منتقل می‌شود)
            document_header = DocumentHeader.objects.create(
                document_number=document_number,
                document_type='SANAD',
                document_date=document_date,
                description='',  # توضیحات خالی - به آیتم‌ها منتقل می‌شود
                company=self.company,
                period=self.period,
                total_debit=total_debit,
                total_credit=total_credit,
                is_balanced=is_balanced
            )
            
            return document_header
            
        except Exception as e:
            logger.error(f"خطا در ایجاد سربرگ سند {document_number}: {e}")
            raise
    
    def _create_document_item(self, document_header: DocumentHeader, row: pd.Series, row_number: int, mapped_columns: dict):
        """ایجاد آرتیکل سند با استفاده از سلسله مراتب حساب‌ها و انتقال توضیحات"""
        try:
            # استفاده از سلسله مراتب حساب‌ها برای مپ کردن حساب
            # اگر سطوح کدینگ وجود نداشت، از متد قدیمی استفاده کن
            try:
                account = self.create_chart_of_accounts_hierarchy(row)
            except Exception as hierarchy_error:
                logger.warning(f"خطا در ایجاد سلسله مراتب حساب‌ها، استفاده از متد قدیمی: {hierarchy_error}")
                # استفاده از متد قدیمی به عنوان fallback
                if mapped_columns['account_code'] in row and pd.notna(row[mapped_columns['account_code']]):
                    account_code = str(row[mapped_columns['account_code']])
                    account = self.map_account_code(account_code)
                else:
                    # اگر کد حساب هم وجود نداشت، حساب موقت ایجاد کن
                    account = self.map_account_code('99999')
            
            # استخراج توضیحات از ستون شرح سند برای آیتم
            item_description = ''
            if mapped_columns['document_description'] in row and pd.notna(row[mapped_columns['document_description']]):
                item_description = str(row[mapped_columns['document_description']]).strip()
            
            # ایجاد آرتیکل با توضیحات منتقل شده
            DocumentItem.objects.create(
                document=document_header,
                row_number=row_number,
                account=account,
                debit=row[mapped_columns['debit']] if pd.notna(row[mapped_columns['debit']]) else 0,
                credit=row[mapped_columns['credit']] if pd.notna(row[mapped_columns['credit']]) else 0,
                description=item_description,
                cost_center=row.get('مرکز هزینه', '') if pd.notna(row.get('مرکز هزینه')) else '',
                project_code=row.get('کد پروژه', '') if pd.notna(row.get('کد پروژه')) else ''
            )
            
        except Exception as e:
            logger.error(f"خطا در ایجاد آرتیکل سند {document_header.document_number} ردیف {row_number}: {e}")
            raise
    
    def process_import(self, delete_existing_data: bool = False) -> dict:
        """پردازش کامل وارد کردن داده‌ها با امکان حذف داده‌های قبلی"""
        try:
            # لاگ وضعیت delete_existing_data
            logger.info(f"🔍 DataIntegrationService.process_import - delete_existing_data: {delete_existing_data}")
            
            # ایجاد کار وارد کردن
            self.create_import_job()
            self.import_job.start_processing()
            
            # مرحله 0: حذف داده‌های قبلی (در صورت درخواست)
            if delete_existing_data:
                logger.info("🔍 شروع حذف داده‌های قبلی")
                self.update_job_progress(10, 'حذف داده‌های قبلی')
                cleanup_result = self._delete_existing_data()
                
                if cleanup_result['status'] == 'failed':
                    logger.error(f"❌ خطا در حذف داده‌های قبلی: {cleanup_result['message']}")
                    self.import_job.fail(f"خطا در حذف داده‌های قبلی: {cleanup_result['message']}")
                    return {
                        'status': 'failed',
                        'errors': [f"خطا در حذف داده‌های قبلی: {cleanup_result['message']}"],
                        'document_count': 0,
                        'item_count': 0
                    }
                
                logger.info(f"✅ داده‌های قبلی حذف شدند: {cleanup_result['deleted_documents']} سند، {cleanup_result['deleted_items']} آرتیکل")
            else:
                logger.info("🔍 حذف داده‌های قبلی درخواست نشده است")
            
            # مرحله 1: خواندن داده‌ها
            self.update_job_progress(25, 'خواندن داده‌های اکسل')
            df = self.read_excel_data()
            
            # مرحله 2: اعتبارسنجی پیشرفته
            self.update_job_progress(50, 'اعتبارسنجی داده‌ها')
            validation_results = self.validate_data_structure(df)
            
            # بررسی خطاهای بحرانی
            if validation_results['errors']:
                self.import_job.fail(f"خطاهای اعتبارسنجی: {', '.join(validation_results['errors'])}")
                return {
                    'status': 'failed',
                    'errors': validation_results['errors'],
                    'warnings': validation_results['warnings'],
                    'balance_analysis': validation_results['balance_analysis'],
                    'suggestions': validation_results['suggestions'],
                    'document_count': 0,
                    'item_count': 0
                }
            
            # مرحله 3: ایجاد سلسله مراتب کامل حساب‌ها
            self.update_job_progress(60, 'ایجاد سلسله مراتب حساب‌ها')
            
            # لاگ دیباگ: بررسی ستون‌های موجود در DataFrame
            logger.info(f"🔍 ستون‌های موجود در DataFrame: {list(df.columns)}")
            
            # لاگ دیباگ: بررسی نگاشت ستون‌ها
            column_mapping = self.financial_file.columns_mapping or {}
            logger.info(f"🔍 نگاشت ستون‌ها: {column_mapping}")
            
            # لاگ دیباگ: بررسی ستون‌های کدینگ
            coding_columns = ['Title1', 'Code1', 'Title2', 'Code2', 'Title3', 'Code3', 'Title4', 'Code4']
            for col in coding_columns:
                exists = col in df.columns
                logger.info(f"🔍 ستون {col}: {'✅ موجود' if exists else '❌ موجود نیست'}")
            
            hierarchy_results = self.create_complete_chart_of_accounts_hierarchy(df)
            
            if hierarchy_results['errors']:
                logger.warning(f"خطا در ایجاد سلسله مراتب حساب‌ها: {', '.join(hierarchy_results['errors'])}")
            else:
                logger.info(f"✅ سلسله مراتب حساب‌ها ایجاد شد: {hierarchy_results['created_levels']}")
            
            # مرحله 4: ایجاد اسناد
            self.update_job_progress(75, 'ایجاد اسناد مالی')
            result = self.create_documents_from_dataframe(df, delete_existing_data=delete_existing_data)
            
            # مرحله 4: تکمیل
            self.update_job_progress(100, 'تکمیل عملیات')
            self.import_job.complete(result)
            
            # علامت‌گذاری فایل به عنوان وارد شده
            self.financial_file.mark_as_imported({
                'document_count': result['document_count'],
                'item_count': result['item_count'],
                'validation_results': validation_results,
                'delete_existing_data': delete_existing_data
            })
            
            logger.info(f"عملیات وارد کردن با موفقیت انجام شد: {result['document_count']} سند، {result['item_count']} آرتیکل")
            
            return {
                'status': 'success',
                'document_count': result['document_count'],
                'item_count': result['item_count'],
                'warnings': validation_results['warnings'],
                'balance_analysis': validation_results['balance_analysis'],
                'suggestions': validation_results['suggestions'],
                'delete_existing_data': delete_existing_data
            }
            
        except Exception as e:
            logger.error(f"خطا در پردازش وارد کردن: {e}")
            if self.import_job:
                self.import_job.fail(str(e))
            raise
    
    def create_complete_chart_of_accounts_hierarchy(self, df: pd.DataFrame) -> dict:
        """ایجاد سلسله مراتب کامل حساب‌ها از تمام داده‌های اکسل"""
        results = {
            'created_levels': {
                'CLASS': 0,
                'SUBCLASS': 0, 
                'DETAIL': 0
            },
            'total_rows_processed': 0,
            'errors': []
        }
        
        try:
            logger.info("🚀 شروع ایجاد سلسله مراتب حساب‌ها")
            
            # استفاده از نگاشت ستون‌ها
            column_mapping = self.financial_file.columns_mapping or {}
            logger.info(f"🔍 نگاشت ستون‌های کدینگ: {column_mapping}")
            
            mapped_columns = {
                'title1': column_mapping.get('title1', 'Title1'),
                'code1': column_mapping.get('code1', 'Code1'),
                'title2': column_mapping.get('title2', 'Title2'),
                'code2': column_mapping.get('code2', 'Code2'),
                'title3': column_mapping.get('title3', 'Title3'),
                'code3': column_mapping.get('code3', 'Code3'),
                'title4': column_mapping.get('title4', 'Title4'),
                'code4': column_mapping.get('code4', 'Code4'),
            }
            
            logger.info(f"🔍 ستون‌های نگاشت شده: {mapped_columns}")
            
            # بررسی وجود ستون‌های کدینگ در DataFrame
            for col_name, col_value in mapped_columns.items():
                exists = col_value in df.columns
                logger.info(f"🔍 ستون {col_name} ({col_value}): {'✅ موجود' if exists else '❌ موجود نیست'}")
            
            # پردازش تمام رکوردهای فایل اکسل
            logger.info(f"📊 شروع پردازش تمام {len(df)} رکورد فایل اکسل")
            
            # دیکشنری‌ها برای ذخیره حساب‌های ایجاد شده
            level1_accounts = {}
            level2_accounts = {}
            level3_accounts = {}
            level4_accounts = {}
            
            for index, row in df.iterrows():
                try:
                    results['total_rows_processed'] += 1
                    
                    # پردازش سطوح کدینگ برای این رکورد
                    self._process_account_hierarchy_for_row(row, mapped_columns, level1_accounts, level2_accounts, level3_accounts, level4_accounts)
                    
                    # لاگ پیشرفت هر 100 رکورد
                    if (index + 1) % 100 == 0:
                        logger.info(f"📊 پردازش رکورد {index + 1} از {len(df)}")
                        
                except Exception as e:
                    error_msg = f"خطا در پردازش رکورد {index + 1}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    continue
            
            # شمارش حساب‌های ایجاد شده
            results['created_levels']['CLASS'] = len(level1_accounts)
            results['created_levels']['SUBCLASS'] = len(level2_accounts)
            results['created_levels']['DETAIL'] = len(level3_accounts) + len(level4_accounts)
            
            total_accounts = len(level1_accounts) + len(level2_accounts) + len(level3_accounts) + len(level4_accounts)
            logger.info(f"🎉 سلسله مراتب حساب‌ها ایجاد شد: CLASS={len(level1_accounts)}, SUBCLASS={len(level2_accounts)}, DETAIL={len(level3_accounts) + len(level4_accounts)} (مجموع: {total_accounts} حساب)")
            logger.info(f"📊 تعداد رکوردهای پردازش شده: {results['total_rows_processed']} از {len(df)}")
            
            return results
            
        except Exception as e:
            error_msg = f"خطا در ایجاد سلسله مراتب حساب‌ها: {e}"
            logger.error(error_msg)
            import traceback
            logger.error(f"🔍 جزئیات خطا: {traceback.format_exc()}")
            results['errors'].append(error_msg)
            return results
    
    def _process_account_hierarchy_for_row(self, row: pd.Series, mapped_columns: dict, 
                                         level1_accounts: dict, level2_accounts: dict, 
                                         level3_accounts: dict, level4_accounts: dict):
        """پردازش سلسله مراتب حساب‌ها برای یک رکورد خاص"""
        try:
            # استخراج داده‌های کدینگ از رکورد
            code1 = str(row[mapped_columns['code1']]) if pd.notna(row[mapped_columns['code1']]) and str(row[mapped_columns['code1']]).strip() != '' else None
            title1 = str(row[mapped_columns['title1']]) if pd.notna(row[mapped_columns['title1']]) and str(row[mapped_columns['title1']]).strip() != '' else None
            code2 = str(row[mapped_columns['code2']]) if pd.notna(row[mapped_columns['code2']]) and str(row[mapped_columns['code2']]).strip() != '' else None
            title2 = str(row[mapped_columns['title2']]) if pd.notna(row[mapped_columns['title2']]) and str(row[mapped_columns['title2']]).strip() != '' else None
            code3 = str(row[mapped_columns['code3']]) if pd.notna(row[mapped_columns['code3']]) and str(row[mapped_columns['code3']]).strip() != '' else None
            title3 = str(row[mapped_columns['title3']]) if pd.notna(row[mapped_columns['title3']]) and str(row[mapped_columns['title3']]).strip() != '' else None
            code4 = str(row[mapped_columns['code4']]) if pd.notna(row[mapped_columns['code4']]) and str(row[mapped_columns['code4']]).strip() != '' else None
            title4 = str(row[mapped_columns['title4']]) if pd.notna(row[mapped_columns['title4']]) and str(row[mapped_columns['title4']]).strip() != '' else None
            
            # ایجاد حساب‌های سلسله مراتب از بالا به پایین
            parent_account = None
            
            # سطح 1: گروه (CLASS)
            if code1 and title1:
                if code1 not in level1_accounts:
                    account = self._get_or_create_account(
                        code=code1,
                        name=title1,
                        level='CLASS',
                        parent=None
                    )
                    level1_accounts[code1] = account
                parent_account = level1_accounts[code1]
            
            # سطح 2: کل (SUBCLASS)
            if code2 and title2 and parent_account:
                if code2 not in level2_accounts:
                    account = self._get_or_create_account(
                        code=code2,
                        name=title2,
                        level='SUBCLASS',
                        parent=parent_account
                    )
                    level2_accounts[code2] = account
                parent_account = level2_accounts[code2]
            
            # سطح 3: معین (DETAIL)
            if code3 and title3 and parent_account:
                if code3 not in level3_accounts:
                    account = self._get_or_create_account(
                        code=code3,
                        name=title3,
                        level='DETAIL',
                        parent=parent_account
                    )
                    level3_accounts[code3] = account
                parent_account = level3_accounts[code3]
            
            # سطح 4: تفصیلی (DETAIL)
            if code4 and title4 and parent_account:
                if code4 not in level4_accounts:
                    account = self._get_or_create_account(
                        code=code4,
                        name=title4,
                        level='DETAIL',
                        parent=parent_account
                    )
                    level4_accounts[code4] = account
            
        except Exception as e:
            logger.error(f"خطا در پردازش سلسله مراتب حساب‌ها برای رکورد: {e}")
            raise
    
    def _extract_level1_accounts(self, df: pd.DataFrame, mapped_columns: dict) -> dict:
        """استخراج حساب‌های سطح CLASS (Code1, Title1)"""
        level1_accounts = {}
        
        try:
            # پیدا کردن تمام Code1, Title1 متمایز
            if mapped_columns['code1'] in df.columns and mapped_columns['title1'] in df.columns:
                level1_data = df[[mapped_columns['code1'], mapped_columns['title1']]].dropna().drop_duplicates()
                
                for _, row in level1_data.iterrows():
                    code1 = str(row[mapped_columns['code1']])
                    title1 = str(row[mapped_columns['title1']])
                    
                    # ایجاد حساب سطح CLASS
                    account = self._get_or_create_account(
                        code=code1,
                        name=title1,
                        level='CLASS',
                        parent=None
                    )
                    
                    level1_accounts[code1] = account
                    logger.debug(f"حساب CLASS ایجاد شد: {code1} - {title1}")
            
            return level1_accounts
            
        except Exception as e:
            logger.error(f"خطا در استخراج حساب‌های سطح CLASS: {e}")
            return level1_accounts
    
    def _extract_level2_accounts(self, df: pd.DataFrame, mapped_columns: dict, level1_accounts: dict) -> dict:
        """استخراج حساب‌های سطح SUBCLASS (Code2, Title2) با والد مناسب"""
        level2_accounts = {}
        
        try:
            # پیدا کردن تمام Code2, Title2 متمایز
            if mapped_columns['code2'] in df.columns and mapped_columns['title2'] in df.columns:
                level2_data = df[[mapped_columns['code1'], mapped_columns['code2'], mapped_columns['title2']]].dropna().drop_duplicates()
                
                for _, row in level2_data.iterrows():
                    code1 = str(row[mapped_columns['code1']]) if pd.notna(row[mapped_columns['code1']]) else None
                    code2 = str(row[mapped_columns['code2']])
                    title2 = str(row[mapped_columns['title2']])
                    
                    # پیدا کردن والد مناسب (سطح CLASS)
                    parent_account = level1_accounts.get(code1) if code1 else None
                    
                    if parent_account:
                        # ایجاد حساب سطح SUBCLASS
                        account = self._get_or_create_account(
                            code=code2,
                            name=title2,
                            level='SUBCLASS',
                            parent=parent_account
                        )
                        
                        level2_accounts[code2] = account
                        logger.debug(f"حساب SUBCLASS ایجاد شد: {code2} - {title2} (والد: {code1})")
                    else:
                        logger.warning(f"والد یافت نشد برای حساب SUBCLASS: {code2} - {title2}")
            
            return level2_accounts
            
        except Exception as e:
            logger.error(f"خطا در استخراج حساب‌های سطح SUBCLASS: {e}")
            return level2_accounts
    
    def _extract_level3_accounts(self, df: pd.DataFrame, mapped_columns: dict, level2_accounts: dict) -> dict:
        """استخراج حساب‌های سطح DETAIL (Code3, Title3) با والد مناسب"""
        level3_accounts = {}
        
        try:
            # پیدا کردن تمام Code3, Title3 متمایز
            if mapped_columns['code3'] in df.columns and mapped_columns['title3'] in df.columns:
                level3_data = df[[mapped_columns['code2'], mapped_columns['code3'], mapped_columns['title3']]].dropna().drop_duplicates()
                
                for _, row in level3_data.iterrows():
                    code2 = str(row[mapped_columns['code2']]) if pd.notna(row[mapped_columns['code2']]) else None
                    code3 = str(row[mapped_columns['code3']])
                    title3 = str(row[mapped_columns['title3']])
                    
                    # پیدا کردن والد مناسب (سطح SUBCLASS)
                    parent_account = level2_accounts.get(code2) if code2 else None
                    
                    if parent_account:
                        # ایجاد حساب سطح DETAIL
                        account = self._get_or_create_account(
                            code=code3,
                            name=title3,
                            level='DETAIL',
                            parent=parent_account
                        )
                        
                        level3_accounts[code3] = account
                        logger.debug(f"حساب DETAIL ایجاد شد: {code3} - {title3} (والد: {code2})")
                    else:
                        logger.warning(f"والد یافت نشد برای حساب DETAIL: {code3} - {title3}")
            
            return level3_accounts
            
        except Exception as e:
            logger.error(f"خطا در استخراج حساب‌های سطح DETAIL: {e}")
            return level3_accounts
    
    def _extract_level4_accounts(self, df: pd.DataFrame, mapped_columns: dict, level3_accounts: dict) -> dict:
        """استخراج حساب‌های سطح DETAIL (Code4, Title4) با والد مناسب"""
        level4_accounts = {}
        
        try:
            # پیدا کردن تمام Code4, Title4 متمایز
            if mapped_columns['code4'] in df.columns and mapped_columns['title4'] in df.columns:
                level4_data = df[[mapped_columns['code3'], mapped_columns['code4'], mapped_columns['title4']]].dropna().drop_duplicates()
                
                for _, row in level4_data.iterrows():
                    code3 = str(row[mapped_columns['code3']]) if pd.notna(row[mapped_columns['code3']]) else None
                    code4 = str(row[mapped_columns['code4']])
                    title4 = str(row[mapped_columns['title4']])
                    
                    # پیدا کردن والد مناسب (سطح DETAIL)
                    parent_account = level3_accounts.get(code3) if code3 else None
                    
                    if parent_account:
                        # ایجاد حساب سطح DETAIL
                        account = self._get_or_create_account(
                            code=code4,
                            name=title4,
                            level='DETAIL',
                            parent=parent_account
                        )
                        
                        level4_accounts[code4] = account
                        logger.debug(f"حساب DETAIL ایجاد شد: {code4} - {title4} (والد: {code3})")
                    else:
                        logger.warning(f"والد یافت نشد برای حساب DETAIL: {code4} - {title4}")
            
            return level4_accounts
            
        except Exception as e:
            logger.error(f"خطا در استخراج حساب‌های سطح DETAIL: {e}")
            return level4_accounts

    def _delete_existing_data(self) -> dict:
        """حذف داده‌های ایمپورت شده قبلی"""
        try:
            cleanup_service = DataCleanupService(self.company, self.period)
            return cleanup_service.delete_imported_data()
            
        except Exception as e:
            logger.error(f"خطا در حذف داده‌های قبلی: {e}")
            return {
                'deleted_documents': 0,
                'deleted_items': 0,
                'status': 'failed',
                'message': str(e)
            }


def import_financial_data(financial_file_id: int, delete_existing_data: bool = False) -> dict:
    """تابع اصلی برای وارد کردن داده‌های مالی با امکان حذف داده‌های قبلی"""
    try:
        financial_file = FinancialFile.objects.get(id=financial_file_id)
        service = DataIntegrationService(financial_file)
        return service.process_import(delete_existing_data=delete_existing_data)
        
    except FinancialFile.DoesNotExist:
        logger.error(f"فایل مالی با شناسه {financial_file_id} یافت نشد")
        return {
            'status': 'failed',
            'errors': ['فایل مالی یافت نشد'],
            'document_count': 0,
            'item_count': 0
        }
    except Exception as e:
        logger.error(f"خطا در وارد کردن داده‌ها: {e}")
        return {
            'status': 'failed',
            'errors': [str(e)],
            'document_count': 0,
            'item_count': 0
        }
