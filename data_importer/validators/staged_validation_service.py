# data_importer/validators/staged_validation_service.py
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """سطوح مختلف اعتبارسنجی"""
    STRUCTURAL = "structural"      # اعتبارسنجی ساختاری
    DATA_QUALITY = "data_quality"  # اعتبارسنجی کیفیت داده
    BALANCE = "balance"            # اعتبارسنجی توازن
    BUSINESS_RULES = "business"    # اعتبارسنجی قوانین کسب‌وکار


class ValidationSeverity(Enum):
    """سطوح شدت خطا"""
    ERROR = "error"      # خطای بحرانی - توقف فرآیند
    WARNING = "warning"  # هشدار - ادامه فرآیند با اطلاع
    INFO = "info"        # اطلاعات - فقط اطلاع‌رسانی


@dataclass
class ValidationResult:
    """نتیجه اعتبارسنجی"""
    level: ValidationLevel
    severity: ValidationSeverity
    message: str
    details: Dict
    affected_rows: List[int] = None
    suggestions: List[str] = None


class StagedValidationService:
    """سرویس اعتبارسنجی مرحله‌ای"""
    
    def __init__(self):
        self.required_columns = {
            'document_number': ['شماره سند', 'ش سند', 'سند', 'شماره'],
            'account_code': ['کد حساب', 'کد', 'حساب', 'کد معین'],
            'debit': ['بدهکار', 'بده', 'مبلغ بدهکار'],
            'credit': ['بستانکار', 'بستان', 'مبلغ بستانکار']
        }
        
        self.validation_rules = self._initialize_validation_rules()
    
    def _initialize_validation_rules(self) -> Dict:
        """مقداردهی اولیه قوانین اعتبارسنجی"""
        return {
            ValidationLevel.STRUCTURAL: [
                self._validate_required_columns,
                self._validate_column_data_types,
                self._validate_document_structure
            ],
            ValidationLevel.DATA_QUALITY: [
                self._validate_missing_values,
                self._validate_duplicate_records,
                self._validate_account_codes,
                self._validate_numeric_ranges
            ],
            ValidationLevel.BALANCE: [
                self._validate_document_balance,
                self._validate_overall_balance
            ],
            ValidationLevel.BUSINESS_RULES: [
                self._validate_business_rules,
                self._validate_financial_period,
                self._validate_account_relationships
            ]
        }
    
    def validate_dataframe(self, df: pd.DataFrame, validation_levels: List[ValidationLevel] = None) -> Dict:
        """اعتبارسنجی مرحله‌ای DataFrame"""
        if validation_levels is None:
            validation_levels = list(ValidationLevel)
        
        results = {
            'is_valid': True,
            'total_errors': 0,
            'total_warnings': 0,
            'validation_results': [],
            'summary': {}
        }
        
        try:
            logger.info(f"شروع اعتبارسنجی مرحله‌ای برای {len(df)} ردیف")
            
            for level in validation_levels:
                level_results = self._execute_validation_level(df, level)
                results['validation_results'].extend(level_results)
                
                # شمارش خطاها و هشدارها
                level_errors = len([r for r in level_results if r.severity == ValidationSeverity.ERROR])
                level_warnings = len([r for r in level_results if r.severity == ValidationSeverity.WARNING])
                
                results['total_errors'] += level_errors
                results['total_warnings'] += level_warnings
                
                results['summary'][level.value] = {
                    'errors': level_errors,
                    'warnings': level_warnings,
                    'passed': len([r for r in level_results if r.severity == ValidationSeverity.INFO])
                }
            
            # بررسی نهایی اعتبار
            results['is_valid'] = results['total_errors'] == 0
            
            logger.info(f"اعتبارسنجی تکمیل شد: {results['total_errors']} خطا, {results['total_warnings']} هشدار")
            
            return results
            
        except Exception as e:
            logger.error(f"خطا در اعتبارسنجی مرحله‌ای: {e}")
            return {
                'is_valid': False,
                'total_errors': 1,
                'total_warnings': 0,
                'validation_results': [ValidationResult(
                    level=ValidationLevel.STRUCTURAL,
                    severity=ValidationSeverity.ERROR,
                    message=f"خطا در فرآیند اعتبارسنجی: {str(e)}",
                    details={'exception': str(e)}
                )],
                'summary': {}
            }
    
    def _execute_validation_level(self, df: pd.DataFrame, level: ValidationLevel) -> List[ValidationResult]:
        """اجرای اعتبارسنجی در یک سطح خاص"""
        results = []
        
        if level in self.validation_rules:
            for validation_func in self.validation_rules[level]:
                try:
                    func_results = validation_func(df)
                    if isinstance(func_results, list):
                        results.extend(func_results)
                    elif func_results:
                        results.append(func_results)
                except Exception as e:
                    logger.error(f"خطا در اجرای تابع اعتبارسنجی {validation_func.__name__}: {e}")
                    results.append(ValidationResult(
                        level=level,
                        severity=ValidationSeverity.ERROR,
                        message=f"خطا در اعتبارسنجی {level.value}",
                        details={'function': validation_func.__name__, 'error': str(e)}
                    ))
        
        return results
    
    # --- توابع اعتبارسنجی ساختاری ---
    
    def _validate_required_columns(self, df: pd.DataFrame) -> List[ValidationResult]:
        """اعتبارسنجی ستون‌های ضروری"""
        results = []
        missing_columns = []
        
        for std_col, patterns in self.required_columns.items():
            found = False
            for col in df.columns:
                col_lower = str(col).lower().strip()
                for pattern in patterns:
                    if pattern.lower() in col_lower or col_lower in pattern.lower():
                        found = True
                        break
                if found:
                    break
            
            if not found:
                missing_columns.append(std_col)
        
        if missing_columns:
            persian_names = {
                'document_number': 'شماره سند',
                'account_code': 'کد حساب',
                'debit': 'بدهکار',
                'credit': 'بستانکار'
            }
            missing_persian = [persian_names[col] for col in missing_columns]
            
            results.append(ValidationResult(
                level=ValidationLevel.STRUCTURAL,
                severity=ValidationSeverity.ERROR,
                message=f"ستون‌های ضروری یافت نشد: {', '.join(missing_persian)}",
                details={'missing_columns': missing_columns},
                suggestions=[
                    "بررسی نام ستون‌ها در فایل اکسل",
                    "استفاده از نام‌های استاندارد مانند 'شماره سند', 'کد حساب'",
                    "مشاهده نمونه فایل استاندارد"
                ]
            ))
        
        return results
    
    def _validate_column_data_types(self, df: pd.DataFrame) -> List[ValidationResult]:
        """اعتبارسنجی نوع داده ستون‌ها"""
        results = []
        
        # پیدا کردن ستون‌های عددی
        debit_col = self._find_column(df, 'debit')
        credit_col = self._find_column(df, 'credit')
        
        if debit_col:
            if not pd.api.types.is_numeric_dtype(df[debit_col]):
                results.append(ValidationResult(
                    level=ValidationLevel.STRUCTURAL,
                    severity=ValidationSeverity.ERROR,
                    message=f"ستون {debit_col} باید شامل مقادیر عددی باشد",
                    details={'column': debit_col, 'expected_type': 'numeric'},
                    suggestions=["تبدیل مقادیر متنی به عدد", "حذف کاراکترهای غیرعددی"]
                ))
        
        if credit_col:
            if not pd.api.types.is_numeric_dtype(df[credit_col]):
                results.append(ValidationResult(
                    level=ValidationLevel.STRUCTURAL,
                    severity=ValidationSeverity.ERROR,
                    message=f"ستون {credit_col} باید شامل مقادیر عددی باشد",
                    details={'column': credit_col, 'expected_type': 'numeric'},
                    suggestions=["تبدیل مقادیر متنی به عدد", "حذف کاراکترهای غیرعددی"]
                ))
        
        return results
    
    def _validate_document_structure(self, df: pd.DataFrame) -> List[ValidationResult]:
        """اعتبارسنجی ساختار اسناد"""
        results = []
        doc_col = self._find_column(df, 'document_number')
        
        if doc_col:
            # بررسی اسناد با تنها یک آرتیکل
            doc_counts = df[doc_col].value_counts()
            single_item_docs = doc_counts[doc_counts == 1].index.tolist()
            
            if single_item_docs:
                results.append(ValidationResult(
                    level=ValidationLevel.STRUCTURAL,
                    severity=ValidationSeverity.WARNING,
                    message=f"{len(single_item_docs)} سند تنها دارای یک آرتیکل هستند",
                    details={'single_item_documents': single_item_docs[:5]},  # فقط ۵ سند اول
                    suggestions=[
                        "بررسی اسناد با یک آرتیکل",
                        "اطمینان از صحت شماره سندها",
                        "ادغام اسناد تکراری"
                    ]
                ))
        
        return results
    
    # --- توابع اعتبارسنجی کیفیت داده ---
    
    def _validate_missing_values(self, df: pd.DataFrame) -> List[ValidationResult]:
        """اعتبارسنجی مقادیر خالی"""
        results = []
        
        critical_columns = [
            self._find_column(df, 'document_number'),
            self._find_column(df, 'account_code'),
            self._find_column(df, 'debit'),
            self._find_column(df, 'credit')
        ]
        
        for col in critical_columns:
            if col and df[col].isna().any():
                missing_count = df[col].isna().sum()
                missing_percentage = (missing_count / len(df)) * 100
                
                severity = ValidationSeverity.ERROR if missing_percentage > 10 else ValidationSeverity.WARNING
                
                results.append(ValidationResult(
                    level=ValidationLevel.DATA_QUALITY,
                    severity=severity,
                    message=f"{missing_count} مقدار خالی در ستون {col} ({missing_percentage:.1f}%)",
                    details={
                        'column': col,
                        'missing_count': missing_count,
                        'missing_percentage': missing_percentage,
                        'affected_rows': df[df[col].isna()].index.tolist()[:10]  # فقط ۱۰ ردیف اول
                    },
                    suggestions=[
                        "پر کردن مقادیر خالی",
                        "حذف ردیف‌های با مقادیر خالی",
                        "استفاده از مقادیر پیش‌فرض"
                    ]
                ))
        
        return results
    
    def _validate_duplicate_records(self, df: pd.DataFrame) -> List[ValidationResult]:
        """اعتبارسنجی رکوردهای تکراری"""
        results = []
        
        duplicate_mask = df.duplicated()
        duplicate_count = duplicate_mask.sum()
        
        if duplicate_count > 0:
            duplicate_percentage = (duplicate_count / len(df)) * 100
            
            results.append(ValidationResult(
                level=ValidationLevel.DATA_QUALITY,
                severity=ValidationSeverity.WARNING,
                message=f"{duplicate_count} رکورد تکراری ({duplicate_percentage:.1f}%)",
                details={
                    'duplicate_count': duplicate_count,
                    'duplicate_percentage': duplicate_percentage,
                    'sample_duplicates': df[duplicate_mask].head(3).to_dict('records')
                },
                suggestions=[
                    "حذف رکوردهای تکراری",
                    "بررسی علت تکرار",
                    "ادغام رکوردهای تکراری"
                ]
            ))
        
        return results
    
    def _validate_account_codes(self, df: pd.DataFrame) -> List[ValidationResult]:
        """اعتبارسنجی کدهای حساب"""
        results = []
        account_col = self._find_column(df, 'account_code')
        
        if account_col:
            # بررسی کدهای حساب نامعتبر
            invalid_accounts = []
            
            for idx, value in df[account_col].items():
                if pd.notna(value):
                    account_str = str(value).strip()
                    # بررسی کدهای خیلی کوتاه یا خیلی طولانی
                    if len(account_str) < 2 or len(account_str) > 20:
                        invalid_accounts.append((idx, account_str))
                    # بررسی کدهای با کاراکترهای غیرمجاز
                    elif not re.match(r'^[0-9a-zA-Z\u0600-\u06FF\-_\.]+$', account_str):
                        invalid_accounts.append((idx, account_str))
            
            if invalid_accounts:
                results.append(ValidationResult(
                    level=ValidationLevel.DATA_QUALITY,
                    severity=ValidationSeverity.WARNING,
                    message=f"{len(invalid_accounts)} کد حساب نامعتبر",
                    details={
                        'invalid_accounts': invalid_accounts[:10],  # فقط ۱۰ مورد اول
                        'total_invalid': len(invalid_accounts)
                    },
                    suggestions=[
                        "اصلاح کدهای حساب نامعتبر",
                        "استفاده از فرمت استاندارد برای کد حساب",
                        "بررسی چارت حساب شرکت"
                    ]
                ))
        
        return results
    
    def _validate_numeric_ranges(self, df: pd.DataFrame) -> List[ValidationResult]:
        """اعتبارسنجی محدوده مقادیر عددی"""
        results = []
        debit_col = self._find_column(df, 'debit')
        credit_col = self._find_column(df, 'credit')
        
        for col_name, col in [('بدهکار', debit_col), ('بستانکار', credit_col)]:
            if col:
                # تبدیل به عدد
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                
                # بررسی مقادیر منفی
                negative_values = numeric_col[numeric_col < 0]
                if len(negative_values) > 0:
                    results.append(ValidationResult(
                        level=ValidationLevel.DATA_QUALITY,
                        severity=ValidationSeverity.WARNING,
                        message=f"{len(negative_values)} مقدار منفی در ستون {col_name}",
                        details={
                            'column': col,
                            'negative_count': len(negative_values),
                            'sample_negative': negative_values.head(3).tolist()
                        },
                        suggestions=[
                            "بررسی مقادیر منفی",
                            "اصلاح مقادیر منفی به مثبت",
                            "تغییر ستون برای مقادیر منفی"
                        ]
                    ))
                
                # بررسی مقادیر بسیار بزرگ
                large_values = numeric_col[numeric_col > 1e12]  # بیشتر از ۱ تریلیون
                if len(large_values) > 0:
                    results.append(ValidationResult(
                        level=ValidationLevel.DATA_QUALITY,
                        severity=ValidationSeverity.WARNING,
                        message=f"{len(large_values)} مقدار بسیار بزرگ در ستون {col_name}",
                        details={
                            'column': col,
                            'large_count': len(large_values),
                            'sample_large': large_values.head(3).tolist()
                        },
                        suggestions=[
                            "بررسی صحت مقادیر بسیار بزرگ",
                            "تقسیم مقادیر بزرگ به چند سند",
                            "تأیید واحد پولی (ریال/تومان)"
                        ]
                    ))
        
        return results
    
    # --- توابع اعتبارسنجی توازن ---
    
    def _validate_document_balance(self, df: pd.DataFrame) -> List[ValidationResult]:
        """اعتبارسنجی توازن اسناد"""
        results = []
        doc_col = self._find_column(df, 'document_number')
        debit_col = self._find_column(df, 'debit')
        credit_col = self._find_column(df, 'credit')
        
        if doc_col and debit_col and credit_col:
            # تبدیل به عدد
            df_numeric = df.copy()
            df_numeric[debit_col] = pd.to_numeric(df[debit_col], errors='coerce').fillna(0)
            df_numeric[credit_col] = pd.to_numeric(df[credit_col], errors='coerce').fillna(0)
            
            # گروه‌بندی بر اساس شماره سند
            grouped = df_numeric.groupby(doc_col)
            unbalanced_docs = []
            
            for doc_number, group in grouped:
                total_debit = group[debit_col].sum()
                total_credit = group[credit_col].sum()
                difference = abs(total_debit - total_credit)
                
                if difference > 0.01:  # تحمل خطای کوچک
                    unbalanced_docs.append({
                        'document_number': doc_number,
                        'debit': total_debit,
                        'credit': total_credit,
                        'difference': difference,
                        'row_count': len(group)
                    })
            
            if unbalanced_docs:
                results.append(ValidationResult(
                    level=ValidationLevel.BALANCE,
                    severity=ValidationSeverity.ERROR,
                    message=f"{len(unbalanced_docs)} سند نامتوازن",
                    details={
                        'unbalanced_documents': unbalanced_docs[:5],  # فقط ۵ سند اول
                        'total_unbalanced': len(unbalanced_docs)
                    },
                    suggestions=[
                        "استفاده از ابزار اصلاح خودکار توازن",
                        "بررسی آرتیکل‌های بزرگ",
                        "افزودن ردیف تنظیمی"
                    ]
                ))
        
        return results
    
    def _validate_overall_balance(self, df: pd.DataFrame) -> List[ValidationResult]:
        """اعتبارسنجی توازن کلی"""
        results = []
        debit_col = self._find_column(df, 'debit')
        credit_col = self._find_column(df, 'credit')
        
        if debit_col and credit_col:
            # تبدیل به عدد
            total_debit = pd.to_numeric(df[debit_col], errors='coerce').fillna(0).sum()
            total_credit = pd.to_numeric(df[credit_col], errors='coerce').fillna(0).sum()
            difference = abs(total_debit - total_credit)
            
            if difference > 0.01:
                results.append(ValidationResult(
                    level=ValidationLevel.BALANCE,
                    severity=ValidationSeverity.ERROR,
                    message=f"عدم توازن کلی: جمع بدهکار={total_debit:,.0f}, جمع بستانکار={total_credit:,.0f}, تفاوت={difference:,.0f}",
                    details={
                        'total_debit': total_debit,
                        'total_credit': total_credit,
                        'difference': difference
                    },
                    suggestions=[
                        f"افزودن ردیف تنظیمی برای تفاوت {difference:,.0f} ریال",
                        "بررسی اسناد با بیشترین تفاوت",
                        "استفاده از پیشنهادات سیستم برای اصلاح"
                    ]
                ))
        
        return results
    
    # --- توابع اعتبارسنجی قوانین کسب‌وکار ---
    
    def _validate_business_rules(self, df: pd.DataFrame) -> List[ValidationResult]:
        """اعتبارسنجی قوانین کسب‌وکار"""
        results = []
        
        # این تابع می‌تواند شامل قوانین خاص کسب‌وکار باشد
        # مانند: محدودیت‌های مبلغ، قوانین مالیاتی، etc.
        
        return results
    
    def _validate_financial_period(self, df: pd.DataFrame) -> List[ValidationResult]:
        """اعتبارسنجی دوره مالی"""
        results = []
        date_col = self._find_column(df, 'document_date')
        
        if date_col:
            # بررسی تاریخ‌های نامعتبر
            invalid_dates = []
            for idx, date_value in df[date_col].items():
                if pd.notna(date_value):
                    date_str = str(date_value)
                    # بررسی فرمت تاریخ شمسی
                    if not re.match(r'\d{4}/\d{2}/\d{2}', date_str):
                        invalid_dates.append((idx, date_str))
            
            if invalid_dates:
                results.append(ValidationResult(
                    level=ValidationLevel.BUSINESS_RULES,
                    severity=ValidationSeverity.WARNING,
                    message=f"{len(invalid_dates)} تاریخ نامعتبر",
                    details={
                        'invalid_dates': invalid_dates[:10],
                        'total_invalid': len(invalid_dates)
                    },
                    suggestions=[
                        "استفاده از فرمت تاریخ شمسی (YYYY/MM/DD)",
                        "تبدیل تاریخ‌های میلادی به شمسی",
                        "بررسی صحت تاریخ‌ها"
                    ]
                ))
        
        return results
    
    def _validate_account_relationships(self, df: pd.DataFrame) -> List[ValidationResult]:
        """اعتبارسنجی روابط حساب‌ها"""
        results = []
        
        # این تابع می‌تواند شامل اعتبارسنجی روابط بین حساب‌ها باشد
        # مانند: حساب‌های متقابل، حساب‌های مادر و فرعی، etc.
        
        return results
    
    # --- توابع کمکی ---
    
    def _find_column(self, df: pd.DataFrame, column_type: str) -> Optional[str]:
        """پیدا کردن ستون بر اساس نوع"""
        if column_type in self.required_columns:
            patterns = self.required_columns[column_type]
            for col in df.columns:
                col_lower = str(col).lower().strip()
                for pattern in patterns:
                    if pattern.lower() in col_lower or col_lower in pattern.lower():
                        return col
        return None
    
    def get_validation_summary(self, validation_results: Dict) -> str:
        """دریافت خلاصه اعتبارسنجی"""
        if not validation_results.get('is_valid'):
            return "❌ فایل دارای خطاهای بحرانی است و قابل وارد کردن نیست"
        
        total_errors = validation_results['total_errors']
        total_warnings = validation_results['total_warnings']
        
        if total_errors == 0 and total_warnings == 0:
            return "✅ فایل کاملاً معتبر است"
        elif total_errors == 0:
            return f"⚠️ فایل معتبر است اما دارای {total_warnings} هشدار"
        else:
            return f"❌ فایل دارای {total_errors} خطا و {total_warnings} هشدار"


# نمونه استفاده
def validate_financial_data(df: pd.DataFrame) -> Dict:
    """تابع اصلی برای اعتبارسنجی داده‌های مالی"""
    validator = StagedValidationService()
    return validator.validate_dataframe(df)
