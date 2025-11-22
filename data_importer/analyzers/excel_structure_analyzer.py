# data_importer/analyzers/excel_structure_analyzer.py
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SoftwarePattern:
    """الگوی شناسایی نرم‌افزارهای مالی"""
    name: str
    display_name: str
    column_patterns: Dict[str, List[str]]
    header_patterns: List[str]
    confidence_threshold: float = 0.7


class ExcelStructureAnalyzer:
    """تحلیل‌گر پیشرفته فایل‌های اکسل مالی"""
    
    def __init__(self):
        self.software_patterns = self._initialize_software_patterns()
        self.standard_columns = {
            'document_number': ['شماره سند', 'ش سند', 'سند', 'شماره', 'کد سند', 'شناسه سند'],
            'document_date': ['تاریخ سند', 'تاریخ', 'ت سند', 'تاریخ صدور'],
            'document_description': ['شرح سند', 'شرح', 'توضیحات', 'شرح عملیات', 'توضیحات', 'شرح به زبان انگلیسی'],
            'account_code': ['کد حساب', 'کد', 'حساب', 'کد معین', 'کد تفصیلی', 'معین', 'کد1', 'کد2', 'کد3', 'کد4'],
            'account_description': ['شرح حساب', 'شرح معین', 'شرح تفصیلی', 'نام حساب', 'title1', 'title2', 'title3', 'title4'],
            'debit': ['بدهکار', 'بده', 'مبلغ بدهکار', 'گردش بدهکار'],
            'credit': ['بستانکار', 'بستان', 'مبلغ بستانکار', 'گردش بستانکار'],
            'cost_center': ['مرکز هزینه', 'مرکز', 'کد مرکز هزینه'],
            'project_code': ['کد پروژه', 'پروژه', 'شماره پروژه']
        }
    
    def _initialize_software_patterns(self) -> List[SoftwarePattern]:
        """ایجاد الگوهای شناسایی نرم‌افزارهای مالی"""
        return [
            SoftwarePattern(
                name='HAMKARAN',
                display_name='همکاران سیستم',
                column_patterns={
                    'document_number': ['شماره سند', 'ش سند'],
                    'document_date': ['تاریخ سند', 'تاریخ'],
                    'account_code': ['کد حساب', 'حساب'],
                    'debit': ['بدهکار'],
                    'credit': ['بستانکار']
                },
                header_patterns=['همکاران سیستم', 'نرم افزار همکاران'],
                confidence_threshold=0.8
            ),
            SoftwarePattern(
                name='RAHKARAN',
                display_name='راهکاران',
                column_patterns={
                    'document_number': ['شماره سند', 'ش سند'],
                    'document_date': ['تاریخ سند', 'تاریخ'],
                    'account_code': ['کد حساب', 'کد معین'],
                    'debit': ['بدهکار', 'مبلغ بدهکار'],
                    'credit': ['بستانکار', 'مبلغ بستانکار']
                },
                header_patterns=['راهکاران', 'نرم افزار راهکاران'],
                confidence_threshold=0.75
            ),
            SoftwarePattern(
                name='SEPIDAR',
                display_name='سپیدار',
                column_patterns={
                    'document_number': ['شماره سند', 'ش سند'],
                    'document_date': ['تاریخ سند', 'تاریخ'],
                    'account_code': ['کد حساب', 'کد تفصیلی'],
                    'debit': ['بدهکار', 'گردش بدهکار'],
                    'credit': ['بستانکار', 'گردش بستانکار']
                },
                header_patterns=['سپیدار', 'نرم افزار سپیدار'],
                confidence_threshold=0.7
            ),
            SoftwarePattern(
                name='NOOR',
                display_name='نور',
                column_patterns={
                    'document_number': ['شماره سند', 'ش سند'],
                    'document_date': ['تاریخ سند', 'تاریخ'],
                    'account_code': ['کد حساب', 'حساب'],
                    'debit': ['بدهکار'],
                    'credit': ['بستانکار']
                },
                header_patterns=['نور', 'نرم افزار نور'],
                confidence_threshold=0.7
            )
        ]
    
    def analyze_excel_structure(self, file_path: str) -> Dict:
        """تحلیل ساختار فایل اکسل"""
        try:
            logger.info(f"شروع تحلیل ساختار فایل: {file_path}")
            
            # خواندن فایل اکسل
            df = self._read_excel_file(file_path)
            if df is None:
                return {'error': 'خطا در خواندن فایل اکسل'}
            
            # شناسایی نرم‌افزار مبدأ
            software_detection = self._detect_software(df)
            
            # مپینگ ستون‌ها
            column_mapping = self._map_columns(df.columns.tolist())
            
            # اعتبارسنجی ساختار
            validation_results = self._validate_structure(df, column_mapping)
            
            # تحلیل داده‌ها
            data_analysis = self._analyze_data(df, column_mapping)
            
            return {
                'success': True,
                'software_type': software_detection['software_name'],
                'display_name': software_detection['display_name'],
                'confidence': software_detection['confidence_score'],
                'columns_mapping': column_mapping,
                'sample_data': self._get_sample_data(df, column_mapping),
                'analysis': data_analysis,
                'issues': validation_results['errors'] + validation_results['warnings'],
                'software_detection': software_detection,
                'validation_results': validation_results,
                'data_analysis': data_analysis,
                'file_info': {
                    'total_rows': len(df),
                    'total_columns': len(df.columns),
                    'columns_list': df.columns.tolist()
                }
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل ساختار فایل: {e}")
            return {'error': f'خطا در تحلیل ساختار: {str(e)}'}
    
    def _read_excel_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """خواندن فایل اکسل با مدیریت خطا"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"فایل {file_path} یافت نشد")
            
            # خواندن تمام شیت‌ها
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            # پیدا کردن شیت حاوی داده‌های مالی
            target_sheet = self._find_financial_sheet(excel_file, sheet_names)
            
            if target_sheet:
                df = pd.read_excel(file_path, sheet_name=target_sheet)
                logger.info(f"داده‌ها از شیت '{target_sheet}' خوانده شد")
                return self._clean_dataframe(df)
            else:
                raise ValueError("هیچ شیت حاوی داده‌های مالی یافت نشد")
                
        except Exception as e:
            logger.error(f"خطا در خواندن فایل اکسل: {e}")
            return None
    
    def _find_financial_sheet(self, excel_file, sheet_names: List[str]) -> Optional[str]:
        """پیدا کردن شیت حاوی داده‌های مالی"""
        financial_keywords = ['سند', 'حسابداری', 'دفتر کل', 'معین', 'تفصیلی', 'اسناد']
        
        for sheet_name in sheet_names:
            try:
                # خواندن چند ردیف اول برای بررسی
                df_sample = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=5)
                
                # بررسی وجود ستون‌های مالی
                columns_text = ' '.join(str(col) for col in df_sample.columns)
                if any(keyword in columns_text for keyword in financial_keywords):
                    return sheet_name
                    
                # بررسی وجود داده‌های عددی (بدهکار/بستانکار)
                numeric_columns = df_sample.select_dtypes(include=['number']).columns
                if len(numeric_columns) >= 2:
                    return sheet_name
                    
            except Exception:
                continue
        
        # اگر شیت مشخصی پیدا نشد، اولین شیت را برمی‌گرداند
        return sheet_names[0] if sheet_names else None
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """پاکسازی DataFrame"""
        # حذف ردیف‌های کاملاً خالی
        df = df.dropna(how='all')
        
        # حذف ستون‌های کاملاً خالی
        df = df.dropna(axis=1, how='all')
        
        # تبدیل نام ستون‌ها به رشته
        df.columns = [str(col).strip() for col in df.columns]
        
        return df.reset_index(drop=True)
    
    def _detect_software(self, df: pd.DataFrame) -> Dict:
        """شناسایی نرم‌افزار مبدأ فایل"""
        best_match = None
        highest_score = 0
        
        # بررسی الگوهای مختلف
        for pattern in self.software_patterns:
            score = self._calculate_software_score(df, pattern)
            
            if score > highest_score and score >= pattern.confidence_threshold:
                highest_score = score
                best_match = pattern
        
        if best_match:
            return {
                'software_name': best_match.name,
                'display_name': best_match.display_name,
                'confidence_score': highest_score,
                'detected': True
            }
        else:
            return {
                'software_name': 'UNKNOWN',
                'display_name': 'ناشناخته',
                'confidence_score': 0,
                'detected': False
            }
    
    def _calculate_software_score(self, df: pd.DataFrame, pattern: SoftwarePattern) -> float:
        """محاسبه امتیاز تطابق با الگوی نرم‌افزار"""
        score = 0
        total_possible = 0
        
        # بررسی ستون‌ها
        for col_type, patterns in pattern.column_patterns.items():
            total_possible += 1
            for col_pattern in patterns:
                if any(self._fuzzy_match(str(col), col_pattern) for col in df.columns):
                    score += 1
                    break
        
        # بررسی الگوهای هدر
        header_text = ' '.join(str(col) for col in df.columns)
        for header_pattern in pattern.header_patterns:
            if header_pattern in header_text:
                score += 2  # وزن بیشتر برای الگوهای هدر
                total_possible += 1
                break
        
        return score / total_possible if total_possible > 0 else 0
    
    def _map_columns(self, columns: List[str]) -> Dict[str, str]:
        """مپینگ ستون‌ها به ستون‌های استاندارد"""
        mapping = {}
        used_columns = set()
        
        # اولویت‌بندی برای تطابق دقیق‌تر
        priority_mappings = [
            # تطابق دقیق
            lambda col, pattern: str(col).lower().strip() == pattern.lower(),
            # تطابق شامل
            lambda col, pattern: pattern.lower() in str(col).lower().strip(),
            # تطابق با حذف فاصله
            lambda col, pattern: pattern.lower().replace(' ', '') in str(col).lower().strip().replace(' ', ''),
            # تطابق با کلمات کلیدی
            lambda col, pattern: self._contains_keywords(str(col).lower().strip(), pattern.lower())
        ]
        
        for standard_col, patterns in self.standard_columns.items():
            matched = False
            for priority_level, match_func in enumerate(priority_mappings):
                for col in columns:
                    if col in used_columns:
                        continue
                        
                    for pattern in patterns:
                        if match_func(col, pattern):
                            mapping[standard_col] = col
                            used_columns.add(col)
                            matched = True
                            break
                    if matched:
                        break
                if matched:
                    break
        
        # مپینگ هوشمند برای ستون‌های خاص
        self._apply_smart_mapping(columns, mapping, used_columns)
        
        return mapping
    
    def _contains_keywords(self, text: str, pattern: str) -> bool:
        """بررسی وجود کلمات کلیدی در متن"""
        keywords = {
            'document_description': ['شرح', 'توضیح', 'description'],
            'account_code': ['کد', 'حساب', 'code', 'account'],
            'account_description': ['شرح', 'حساب', 'title', 'name'],
            'debit': ['بدهکار', 'debit'],
            'credit': ['بستانکار', 'credit']
        }
        
        # پیدا کردن کلمات کلیدی مربوط به pattern
        for key, keyword_list in keywords.items():
            if pattern in self.standard_columns.get(key, []):
                return any(keyword in text for keyword in keyword_list)
        
        return False
    
    def _apply_smart_mapping(self, columns: List[str], mapping: Dict[str, str], used_columns: set):
        """اعمال مپینگ هوشمند برای ستون‌های خاص"""
        # مپینگ ستون‌های خاص بر اساس الگوهای رایج
        smart_patterns = {
            'document_description': ['توضیحات', 'شرح به زبان انگلیسی'],
            'account_code': ['معین', 'کد1', 'کد2', 'کد3', 'کد4'],
            'account_description': ['title1', 'title2', 'title3', 'title4']
        }
        
        for standard_col, patterns in smart_patterns.items():
            if standard_col not in mapping:
                for col in columns:
                    if col in used_columns:
                        continue
                    if any(pattern.lower() in str(col).lower() for pattern in patterns):
                        mapping[standard_col] = col
                        used_columns.add(col)
                        break
    
    def _validate_structure(self, df: pd.DataFrame, column_mapping: Dict) -> Dict:
        """اعتبارسنجی ساختار داده‌ها"""
        errors = []
        warnings = []
        
        # بررسی ستون‌های ضروری
        required_columns = ['document_number', 'account_code', 'debit', 'credit']
        missing_required = [col for col in required_columns if col not in column_mapping]
        
        if missing_required:
            persian_names = {
                'document_number': 'شماره سند',
                'account_code': 'کد حساب', 
                'debit': 'بدهکار',
                'credit': 'بستانکار'
            }
            missing_persian = [persian_names[col] for col in missing_required]
            errors.append(f"ستون‌های ضروری یافت نشد: {', '.join(missing_persian)}")
        
        # بررسی مقادیر خالی در ستون‌های کلیدی
        for col_type, col_name in column_mapping.items():
            if col_type in ['document_number', 'account_code', 'debit', 'credit']:
                if df[col_name].isna().any():
                    warnings.append(f"مقادیر خالی در ستون {col_name}")
        
        # بررسی فرمت داده‌ها
        if 'debit' in column_mapping and 'credit' in column_mapping:
            debit_col = column_mapping['debit']
            credit_col = column_mapping['credit']
            
            # بررسی نوع داده عددی
            if not pd.api.types.is_numeric_dtype(df[debit_col]):
                warnings.append(f"ستون {debit_col} باید شامل مقادیر عددی باشد")
            
            if not pd.api.types.is_numeric_dtype(df[credit_col]):
                warnings.append(f"ستون {credit_col} باید شامل مقادیر عددی باشد")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'required_columns_mapped': len([col for col in required_columns if col in column_mapping])
        }
    
    def _analyze_data(self, df: pd.DataFrame, column_mapping: Dict) -> Dict:
        """تحلیل داده‌ها"""
        analysis = {
            'document_count': 0,
            'total_debit': 0,
            'total_credit': 0,
            'balance_status': 'UNKNOWN',
            'account_variety': 0,
            'data_quality': {}
        }
        
        try:
            # شمارش اسناد منحصربه‌فرد
            if 'document_number' in column_mapping:
                doc_col = column_mapping['document_number']
                analysis['document_count'] = df[doc_col].nunique()
            
            # محاسبه جمع بدهکار و بستانکار
            if 'debit' in column_mapping and 'credit' in column_mapping:
                debit_col = column_mapping['debit']
                credit_col = column_mapping['credit']
                
                # تبدیل به عدد
                df[debit_col] = pd.to_numeric(df[debit_col], errors='coerce').fillna(0)
                df[credit_col] = pd.to_numeric(df[credit_col], errors='coerce').fillna(0)
                
                analysis['total_debit'] = float(df[debit_col].sum())
                analysis['total_credit'] = float(df[credit_col].sum())
                
                # بررسی توازن
                difference = abs(analysis['total_debit'] - analysis['total_credit'])
                if difference <= 0.01:
                    analysis['balance_status'] = 'BALANCED'
                else:
                    analysis['balance_status'] = 'UNBALANCED'
                    analysis['balance_difference'] = difference
            
            # تنوع حساب‌ها
            if 'account_code' in column_mapping:
                account_col = column_mapping['account_code']
                analysis['account_variety'] = df[account_col].nunique()
            
            # کیفیت داده‌ها
            total_rows = len(df)
            if total_rows > 0:
                analysis['data_quality'] = {
                    'total_rows': total_rows,
                    'empty_cells': df.isna().sum().sum(),
                    'empty_percentage': (df.isna().sum().sum() / (total_rows * len(df.columns))) * 100,
                    'duplicate_rows': df.duplicated().sum(),
                    'duplicate_percentage': (df.duplicated().sum() / total_rows) * 100
                }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل داده‌ها: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    def _get_sample_data(self, df: pd.DataFrame, column_mapping: Dict, sample_size: int = 5) -> List[Dict]:
        """دریافت نمونه داده‌ها"""
        if len(df) == 0:
            return []
        
        sample_df = df.head(sample_size)
        sample_data = []
        
        for _, row in sample_df.iterrows():
            sample_row = {}
            for standard_col, original_col in column_mapping.items():
                sample_row[standard_col] = row[original_col] if pd.notna(row[original_col]) else None
            sample_data.append(sample_row)
        
        return sample_data
    
    def _fuzzy_match(self, text1: str, text2: str) -> bool:
        """تطابق فازی بین دو رشته"""
        text1 = str(text1).lower().strip()
        text2 = str(text2).lower().strip()
        
        # تطابق دقیق
        if text1 == text2:
            return True
        
        # تطابق شامل
        if text2 in text1 or text1 in text2:
            return True
        
        # تطابق با حذف فاصله
        text1_no_space = text1.replace(' ', '')
        text2_no_space = text2.replace(' ', '')
        if text2_no_space in text1_no_space or text1_no_space in text2_no_space:
            return True
        
        return False
