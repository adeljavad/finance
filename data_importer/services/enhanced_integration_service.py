# data_importer/services/enhanced_integration_service.py
"""
سرویس یکپارچه‌سازی پیشرفته برای اتصال داده‌های ایمپورت شده به سیستم مالی
این سرویس بهبودهای اضافی بر روی سرویس اصلی ارائه می‌دهد
"""

import pandas as pd
import logging
from pathlib import Path
from django.db import transaction
from django.utils import timezone
from typing import Dict, List, Optional
from datetime import datetime

from financial_system.models.document_models import DocumentHeader, DocumentItem
from financial_system.models.coding_models import ChartOfAccounts
from financial_system.services.balance_control_service import BalanceControlService
from ..models import FinancialFile, ImportJob
from ..analyzers.advanced_excel_analyzer import AdvancedExcelAnalyzer
from ..validators.staged_validation_service import StagedValidationService

logger = logging.getLogger(__name__)

class EnhancedIntegrationService:
    """سرویس یکپارچه‌سازی پیشرفته با قابلیت‌های بهبود یافته"""
    
    def __init__(self, financial_file: FinancialFile):
        self.financial_file = financial_file
        self.company = financial_file.company
        self.period = financial_file.financial_period
        self.import_job = None
        self.balance_service = BalanceControlService()
        self.advanced_analyzer = AdvancedExcelAnalyzer()
        self.validation_service = StagedValidationService()
    
    def create_enhanced_import_job(self) -> ImportJob:
        """ایجاد کار وارد کردن پیشرفته با اطلاعات بیشتر"""
        job_id = f"enhanced_import_{self.company.id}_{int(timezone.now().timestamp())}"
        
        self.import_job = ImportJob.objects.create(
            job_id=job_id,
            financial_file=self.financial_file,
            status='PENDING',
            metadata={
                'enhanced_features': True,
                'analysis_depth': 'ADVANCED',
                'validation_level': 'COMPREHENSIVE',
                'created_at': timezone.now().isoformat()
            }
        )
        return self.import_job
    
    def perform_comprehensive_analysis(self, df: pd.DataFrame) -> Dict:
        """انجام تحلیل جامع بر روی داده‌ها"""
        analysis_results = {}
        
        try:
            # تحلیل ساختار پیشرفته
            structure_analysis = self.advanced_analyzer.analyze_excel_structure(
                self.financial_file.file_path
            )
            analysis_results['structure'] = structure_analysis
            
            # اعتبارسنجی مرحله‌ای
            validation_results = self.validation_service.validate_dataframe(df)
            analysis_results['validation'] = validation_results
            
            # تحلیل توازن پیشرفته
            balance_analysis = self._perform_advanced_balance_analysis(df)
            analysis_results['balance'] = balance_analysis
            
            # تحلیل کیفیت داده
            quality_analysis = self._analyze_data_quality(df)
            analysis_results['quality'] = quality_analysis
            
            # تولید امتیاز کلی
            overall_score = self._calculate_overall_score(analysis_results)
            analysis_results['overall_score'] = overall_score
            
            logger.info(f"تحلیل جامع انجام شد - امتیاز کلی: {overall_score}")
            
        except Exception as e:
            logger.error(f"خطا در تحلیل جامع: {e}")
            analysis_results['error'] = str(e)
        
        return analysis_results
    
    def _perform_advanced_balance_analysis(self, df: pd.DataFrame) -> Dict:
        """تحلیل پیشرفته توازن با جزئیات بیشتر"""
        balance_analysis = {
            'document_level_balance': [],
            'account_level_balance': {},
            'period_balance': {},
            'anomalies': []
        }
        
        try:
            # تحلیل توازن در سطح سند
            grouped_by_doc = df.groupby('شماره سند')
            
            for doc_number, group_df in grouped_by_doc:
                doc_debit = group_df['بدهکار'].sum()
                doc_credit = group_df['بستانکار'].sum()
                doc_difference = abs(doc_debit - doc_credit)
                is_balanced = doc_difference <= 0.01
                
                balance_analysis['document_level_balance'].append({
                    'document_number': doc_number,
                    'debit': doc_debit,
                    'credit': doc_credit,
                    'difference': doc_difference,
                    'is_balanced': is_balanced,
                    'row_count': len(group_df)
                })
                
                # شناسایی اسناد نامتوازن
                if not is_balanced and doc_difference > 1000:  # تفاوت قابل توجه
                    balance_analysis['anomalies'].append({
                        'type': 'UNBALANCED_DOCUMENT',
                        'document_number': doc_number,
                        'difference': doc_difference,
                        'severity': 'HIGH' if doc_difference > 10000 else 'MEDIUM'
                    })
            
            # تحلیل توازن در سطح حساب
            if 'کد حساب' in df.columns:
                grouped_by_account = df.groupby('کد حساب')
                
                for account_code, group_df in grouped_by_account:
                    account_debit = group_df['بدهکار'].sum()
                    account_credit = group_df['بستانکار'].sum()
                    account_balance = account_debit - account_credit
                    
                    balance_analysis['account_level_balance'][account_code] = {
                        'debit': account_debit,
                        'credit': account_credit,
                        'balance': account_balance,
                        'transaction_count': len(group_df)
                    }
            
            # تحلیل توازن دوره
            total_debit = df['بدهکار'].sum()
            total_credit = df['بستانکار'].sum()
            total_difference = abs(total_debit - total_credit)
            
            balance_analysis['period_balance'] = {
                'total_debit': total_debit,
                'total_credit': total_credit,
                'total_difference': total_difference,
                'is_period_balanced': total_difference <= 0.01,
                'document_count': len(grouped_by_doc),
                'total_rows': len(df)
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل پیشرفته توازن: {e}")
            balance_analysis['error'] = str(e)
        
        return balance_analysis
    
    def _analyze_data_quality(self, df: pd.DataFrame) -> Dict:
        """تحلیل کیفیت داده‌ها"""
        quality_metrics = {
            'completeness_score': 0,
            'consistency_score': 0,
            'accuracy_score': 0,
            'timeliness_score': 0,
            'overall_quality_score': 0,
            'issues': []
        }
        
        try:
            # امتیاز کامل بودن
            total_cells = len(df) * len(df.columns)
            non_null_cells = df.count().sum()
            completeness_score = (non_null_cells / total_cells) * 100 if total_cells > 0 else 0
            quality_metrics['completeness_score'] = round(completeness_score, 2)
            
            # امتیاز سازگاری
            consistency_issues = self._check_consistency(df)
            consistency_score = max(0, 100 - len(consistency_issues) * 5)
            quality_metrics['consistency_score'] = consistency_score
            quality_metrics['issues'].extend(consistency_issues)
            
            # امتیاز دقت
            accuracy_issues = self._check_accuracy(df)
            accuracy_score = max(0, 100 - len(accuracy_issues) * 10)
            quality_metrics['accuracy_score'] = accuracy_score
            quality_metrics['issues'].extend(accuracy_issues)
            
            # امتیاز به‌موقع بودن
            timeliness_score = self._check_timeliness(df)
            quality_metrics['timeliness_score'] = timeliness_score
            
            # امتیاز کلی کیفیت
            overall_quality = (
                completeness_score * 0.3 +
                consistency_score * 0.3 +
                accuracy_score * 0.3 +
                timeliness_score * 0.1
            )
            quality_metrics['overall_quality_score'] = round(overall_quality, 2)
            
        except Exception as e:
            logger.error(f"خطا در تحلیل کیفیت داده: {e}")
            quality_metrics['error'] = str(e)
        
        return quality_metrics
    
    def _check_consistency(self, df: pd.DataFrame) -> List[Dict]:
        """بررسی سازگاری داده‌ها"""
        issues = []
        
        try:
            # بررسی سازگاری تاریخ‌ها
            if 'تاریخ سند' in df.columns:
                date_column = df['تاریخ سند']
                if pd.api.types.is_datetime64_any_dtype(date_column):
                    min_date = date_column.min()
                    max_date = date_column.max()
                    
                    if (max_date - min_date).days > 365:
                        issues.append({
                            'type': 'DATE_RANGE_TOO_WIDE',
                            'description': f'بازه زمانی داده‌ها بسیار گسترده است: از {min_date} تا {max_date}',
                            'severity': 'MEDIUM'
                        })
            
            # بررسی سازگاری مقادیر عددی
            if 'بدهکار' in df.columns and 'بستانکار' in df.columns:
                negative_debits = df[df['بدهکار'] < 0]
                negative_credits = df[df['بستانکار'] < 0]
                
                if len(negative_debits) > 0:
                    issues.append({
                        'type': 'NEGATIVE_DEBIT_VALUES',
                        'description': f'{len(negative_debits)} مقدار منفی در ستون بدهکار',
                        'severity': 'MEDIUM'
                    })
                
                if len(negative_credits) > 0:
                    issues.append({
                        'type': 'NEGATIVE_CREDIT_VALUES',
                        'description': f'{len(negative_credits)} مقدار منفی در ستون بستانکار',
                        'severity': 'MEDIUM'
                    })
            
        except Exception as e:
            logger.error(f"خطا در بررسی سازگاری: {e}")
        
        return issues
    
    def _check_accuracy(self, df: pd.DataFrame) -> List[Dict]:
        """بررسی دقت داده‌ها"""
        issues = []
        
        try:
            # بررسی مقادیر غیرعادی
            if 'بدهکار' in df.columns:
                debit_stats = df['بدهکار'].describe()
                q75 = debit_stats['75%']
                q25 = debit_stats['25%']
                iqr = q75 - q25
                upper_bound = q75 + 1.5 * iqr
                
                outliers = df[df['بدهکار'] > upper_bound]
                if len(outliers) > 0:
                    issues.append({
                        'type': 'DEBIT_OUTLIERS',
                        'description': f'{len(outliers)} مقدار غیرعادی در ستون بدهکار',
                        'severity': 'LOW'
                    })
            
            # بررسی کدهای حساب نامعتبر
            if 'کد حساب' in df.columns:
                invalid_accounts = df[~df['کد حساب'].astype(str).str.match(r'^\d+$')]
                if len(invalid_accounts) > 0:
                    issues.append({
                        'type': 'INVALID_ACCOUNT_CODES',
                        'description': f'{len(invalid_accounts)} کد حساب نامعتبر',
                        'severity': 'HIGH'
                    })
            
        except Exception as e:
            logger.error(f"خطا در بررسی دقت: {e}")
        
        return issues
    
    def _check_timeliness(self, df: pd.DataFrame) -> float:
        """بررسی به‌موقع بودن داده‌ها"""
        try:
            if 'تاریخ سند' in df.columns:
                date_column = df['تاریخ سند']
                if pd.api.types.is_datetime64_any_dtype(date_column):
                    latest_date = date_column.max()
                    days_since_latest = (datetime.now().date() - latest_date.date()).days
                    
                    if days_since_latest <= 30:
                        return 100  # بسیار به‌روز
                    elif days_since_latest <= 90:
                        return 80   # نسبتاً به‌روز
                    elif days_since_latest <= 180:
                        return 60   # قدیمی
                    else:
                        return 40   # بسیار قدیمی
            
            return 50  # وضعیت نامشخص
        
        except Exception as e:
            logger.error(f"خطا در بررسی به‌موقع بودن: {e}")
            return 50
    
    def _calculate_overall_score(self, analysis_results: Dict) -> float:
        """محاسبه امتیاز کلی بر اساس تحلیل‌های انجام شده"""
        try:
            scores = []
            weights = {
                'structure': 0.2,
                'validation': 0.3,
                'balance': 0.3,
                'quality': 0.2
            }
            
            # امتیاز ساختار
            if 'structure' in analysis_results and 'confidence' in analysis_results['structure']:
                structure_score = analysis_results['structure']['confidence'] * 100
                scores.append(structure_score * weights['structure'])
            
            # امتیاز اعتبارسنجی
            if 'validation' in analysis_results:
                validation_passed = len([r for r in analysis_results['validation'] if r.severity != 'ERROR'])
                validation_total = len(analysis_results['validation'])
                validation_score = (validation_passed / validation_total) * 100 if validation_total > 0 else 100
                scores.append(validation_score * weights['validation'])
            
            # امتیاز توازن
            if 'balance' in analysis_results and 'period_balance' in analysis_results['balance']:
                period_balance = analysis_results['balance']['period_balance']
                if period_balance.get('is_period_balanced', False):
                    balance_score = 100
                else:
                    # کاهش امتیاز بر اساس میزان عدم توازن
                    total_amount = max(period_balance['total_debit'], period_balance['total_credit'])
                    if total_amount > 0:
                        imbalance_ratio = period_balance['total_difference'] / total_amount
                        balance_score = max(0, 100 - (imbalance_ratio * 1000))  # ضریب تنبیه
                    else:
                        balance_score = 50
                scores.append(balance_score * weights['balance'])
            
            # امتیاز کیفیت
            if 'quality' in analysis_results and 'overall_quality_score' in analysis_results['quality']:
                quality_score = analysis_results['quality']['overall_quality_score']
                scores.append(quality_score * weights['quality'])
            
            overall_score = sum(scores) if scores else 0
            return round(overall_score, 2)
            
        except Exception as e:
            logger.error(f"خطا در محاسبه امتیاز کلی: {e}")
            return 0
    
    def create_documents_with_metadata(self, df: pd.DataFrame) -> Dict:
        """ایجاد اسناد با متادیتای پیشرفته"""
        created_documents = 0
        created_items = 0
        document_metadata = []
        
        try:
            with transaction.atomic():
                # تحلیل جامع قبل از ایجاد اسناد
                comprehensive_analysis = self.perform_comprehensive_analysis(df)
                
                # گروه‌بندی داده‌ها بر اساس شماره سند
                grouped_data = df.groupby('شماره سند')
                
                for document_number, group_df in grouped_data:
                    # ایجاد سربرگ سند با متادیتای پیشرفته
                    document_header = self._create_enhanced_document_header(document_number, group_df, comprehensive_analysis)
                    created_documents += 1
                    
                    # ایجاد آرتیکل‌های سند
                    item_count = 0
                    for index, row in group_df.iterrows():
                        self._create_document_item(document_header, row, index + 1)
                        item_count += 1
                        created_items += 1
                    
                    # ذخیره متادیتای سند
                    document_metadata.append({
                        'document_number': document_number,
                        'document_id': document_header.id,
                        'item_count': item_count,
                        'analysis_quality': comprehensive_analysis.get('overall_score', 0),
                        'created_at': timezone.now().isoformat()
                    })
                
                return {
                    'document_count': created_documents,
                    'item_count': created_items,
                    'status': 'success',
                    'comprehensive_analysis': comprehensive_analysis,
                    'document_metadata': document_metadata
                }
                
        except Exception as e:
            logger.error(f"خطا در ایجاد اسناد با متادیتا: {e}")
            raise
    
    def _create_enhanced_document_header(self, document_number: str, group_df: pd.DataFrame, analysis: Dict) -> DocumentHeader:
        """ایجاد سربرگ سند با متادیتای پیشرفته"""
        try:
            # محاسبه جمع بدهکار و بستانکار
            total_debit = float(group_df['بدهکار'].sum())
            total_credit = float(group_df['بستانکار'].sum())
            
            # بررسی توازن
            is_balanced = abs(total_debit - total_credit) <= 0.01
            
            # محاسبه کیفیت سند
            document_quality = self._calculate_document_quality(group_df, analysis)
            
            # ایجاد سند
            document_header = DocumentHeader.objects.create(
                document_number=document_number,
                document_type='SANAD',
                document_date=group_df['تاریخ سند'].iloc[0],
                description=group_df['شرح سند'].iloc[0] if 'شرح سند' in group_df.columns else 'بدون شرح',
                company=self.company,
                period=self.period,
                total_debit=total_debit,
                total_credit=total_credit,
                is_balanced=is_balanced
            )
            
            return document_header
            
        except Exception as e:
            logger.error(f"خطا در ایجاد سربرگ سند پیشرفته {document_number}: {e}")
            raise
    
    def _calculate_document_quality(self, group_df: pd.DataFrame, analysis: Dict) -> float:
        """محاسبه کیفیت سند"""
        try:
            quality_score = 100.0
            
            # کاهش کیفیت بر اساس مقادیر خالی
            for col in ['کد حساب', 'بدهکار', 'بستانکار']:
                if col in group_df.columns and group_df[col].isna().any():
                    quality_score -= 10
            
            # کاهش کیفیت بر اساس عدم توازن
            if 'balance' in analysis:
                for doc_balance in analysis['balance'].get('document_level_balance', []):
                    if doc_balance['document_number'] == group_df['شماره سند'].iloc[0]:
                        if not doc_balance['is_balanced']:
                            quality_score -= 20
                        break
            
            return max(0, quality_score)
            
        except Exception as e:
            logger.error(f"خطا در محاسبه کیفیت سند: {e}")
            return 50.0
    
    def _create_document_item(self, document_header: DocumentHeader, row: pd.Series, row_number: int):
        """ایجاد آرتیکل سند"""
        try:
            # مپ کردن حساب
            account_code = str(row['کد حساب'])
            account = self.map_account_code(account_code)
            
            # ایجاد آرتیکل
            DocumentItem.objects.create(
                document=document_header,
                row_number=row_number,
                account=account,
                debit=row['بدهکار'] if pd.notna(row['بدهکار']) else 0,
                credit=row['بستانکار'] if pd.notna(row['بستانکار']) else 0,
                description=row.get('شرح', '') if pd.notna(row.get('شرح')) else '',
                cost_center=row.get('مرکز هزینه', '') if pd.notna(row.get('مرکز هزینه')) else '',
                project_code=row.get('کد پروژه', '') if pd.notna(row.get('کد پروژه')) else ''
            )
            
        except Exception as e:
            logger.error(f"خطا در ایجاد آرتیکل سند {document_header.document_number} ردیف {row_number}: {e}")
            raise
    
    def map_account_code(self, account_code: str) -> ChartOfAccounts:
        """مپ کردن کد حساب به مدل ChartOfAccounts"""
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
                    level='DETAIL'  # پیش‌فرض
                )
                logger.info(f"حساب جدید ایجاد شد: {account_code}")
            
            return account
            
        except Exception as e:
            logger.error(f"خطا در مپ کردن حساب {account_code}: {e}")
            raise
    
    def process_enhanced_import(self) -> Dict:
        """پردازش کامل وارد کردن داده‌ها با قابلیت‌های پیشرفته"""
        try:
            # ایجاد کار وارد کردن پیشرفته
            self.create_enhanced_import_job()
            self.import_job.start_processing()
            
            # مرحله 1: خواندن داده‌ها
            self.update_job_progress(20, 'خواندن داده‌های اکسل')
            df = self.read_excel_data()
            
            # مرحله 2: تحلیل جامع
            self.update_job_progress(40, 'تحلیل جامع داده‌ها')
            comprehensive_analysis = self.perform_comprehensive_analysis(df)
            
            # مرحله 3: اعتبارسنجی پیشرفته
            self.update_job_progress(60, 'اعتبارسنجی پیشرفته')
            validation_results = self.validation_service.validate_dataframe(df)
            
            # بررسی خطاهای بحرانی
            critical_errors = [r for r in validation_results['validation_results'] if r.severity.value == 'error']
            if critical_errors:
                error_messages = [r.message for r in critical_errors]
                self.import_job.fail(f"خطاهای اعتبارسنجی: {', '.join(error_messages)}")
                return {
                    'status': 'failed',
                    'errors': error_messages,
                    'warnings': [r.message for r in validation_results['validation_results'] if r.severity.value == 'warning'],
                    'comprehensive_analysis': comprehensive_analysis,
                    'document_count': 0,
                    'item_count': 0
                }
            
            # مرحله 4: ایجاد اسناد با متادیتا
            self.update_job_progress(80, 'ایجاد اسناد مالی پیشرفته')
            result = self.create_documents_with_metadata(df)
            
            # مرحله 5: تکمیل
            self.update_job_progress(100, 'تکمیل عملیات پیشرفته')
            self.import_job.complete({
                'document_count': result['document_count'],
                'item_count': result['item_count'],
                'comprehensive_analysis': result['comprehensive_analysis'],
                'overall_quality_score': comprehensive_analysis.get('overall_score', 0)
            })
            
            # علامت‌گذاری فایل به عنوان وارد شده با متادیتای پیشرفته
            self.financial_file.mark_as_imported({
                'document_count': result['document_count'],
                'item_count': result['item_count'],
                'comprehensive_analysis': comprehensive_analysis,
                'validation_results': [r.to_dict() for r in validation_results],
                'enhanced_import': True
            })
            
            logger.info(f"عملیات وارد کردن پیشرفته با موفقیت انجام شد: {result['document_count']} سند، {result['item_count']} آرتیکل")
            
            return {
                'status': 'success',
                'document_count': result['document_count'],
                'item_count': result['item_count'],
                'comprehensive_analysis': comprehensive_analysis,
                'overall_quality_score': comprehensive_analysis.get('overall_score', 0),
                'warnings': [r.message for r in validation_results if r.severity == 'WARNING']
            }
            
        except Exception as e:
            logger.error(f"خطا در پردازش وارد کردن پیشرفته: {e}")
            if self.import_job:
                self.import_job.fail(str(e))
            raise
    
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


def enhanced_import_financial_data(financial_file_id: int) -> Dict:
    """تابع اصلی برای وارد کردن داده‌های مالی با قابلیت‌های پیشرفته"""
    try:
        financial_file = FinancialFile.objects.get(id=financial_file_id)
        service = EnhancedIntegrationService(financial_file)
        return service.process_enhanced_import()
        
    except FinancialFile.DoesNotExist:
        logger.error(f"فایل مالی با شناسه {financial_file_id} یافت نشد")
        return {
            'status': 'failed',
            'errors': ['فایل مالی یافت نشد'],
            'document_count': 0,
            'item_count': 0
        }
    except Exception as e:
        logger.error(f"خطا در وارد کردن داده‌ها با قابلیت‌های پیشرفته: {e}")
        return {
            'status': 'failed',
            'errors': [str(e)],
            'document_count': 0,
            'item_count': 0
        }
