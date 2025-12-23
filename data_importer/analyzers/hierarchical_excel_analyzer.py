"""
تحلیل‌گر پیشرفته برای شناسایی سلسله‌مراتب حساب‌ها
"""
from .excel_structure_analyzer import ExcelStructureAnalyzer
import pandas as pd
import re


class HierarchicalExcelAnalyzer(ExcelStructureAnalyzer):
    """تحلیل‌گر با قابلیت شناسایی سلسله‌مراتب"""
    
    def __init__(self):
        super().__init__()
        self.hierarchical_patterns = {
            'main_account_code': ['کد کل', 'کل', 'سطح ۱', 'کد1', 'account_code_1', 'کد حساب کل'],
            'main_account_name': ['نام کل', 'شرح کل', 'title1', 'شرح حساب کل'],
            'sub_account_code': ['کد معین', 'معین', 'سطح ۲', 'کد2', 'account_code_2', 'کد حساب معین'],
            'sub_account_name': ['نام معین', 'شرح معین', 'title2', 'شرح حساب معین'],
            'detail_account_code': ['کد تفصیلی', 'تفصیلی', 'سطح ۳', 'کد3', 'account_code_3', 'کد حساب تفصیلی'],
            'detail_account_name': ['نام تفصیلی', 'شرح تفصیلی', 'title3', 'شرح حساب تفصیلی'],
        }
    
    def analyze_hierarchical_structure(self, file_path):
        """تحلیل ساختار سلسله‌مراتبی"""
        result = self.analyze_excel_structure(file_path)
        
        if 'error' in result:
            return result
        
        # خواندن DataFrame
        df = self._read_excel_file(file_path)
        
        # شناسایی ستون‌های سلسله‌مراتبی
        hierarchical_mapping = self._map_hierarchical_columns(df.columns.tolist())
        
        # تحلیل سلسله‌مراتب
        hierarchy_analysis = self._analyze_hierarchy(df, hierarchical_mapping)
        
        # ترکیب نتایج
        result.update({
            'hierarchical_mapping': hierarchical_mapping,
            'hierarchy_analysis': hierarchy_analysis,
            'has_hierarchy': len(hierarchical_mapping) > 0
        })
        
        return result
    
    def _map_hierarchical_columns(self, columns):
        """مپینگ ستون‌های سلسله‌مراتبی"""
        mapping = {}
        used_columns = set()
        
        for level, patterns in self.hierarchical_patterns.items():
            for col in columns:
                if col in used_columns:
                    continue
                    
                for pattern in patterns:
                    if self._fuzzy_match(str(col), pattern):
                        mapping[level] = col
                        used_columns.add(col)
                        break
                if level in mapping:
                    break
        
        return mapping
    
    def _analyze_hierarchy(self, df, mapping):
        """تحلیل سلسله‌مراتب داده‌ها"""
        analysis = {
            'levels_detected': len(mapping) // 2,  # هر سطح شامل code و name
            'hierarchy_depth': 0,
            'account_distribution': {},
            'hierarchy_quality': 'UNKNOWN'
        }
        
        if not mapping:
            return analysis
        
        # محاسبه عمق سلسله‌مراتب
        if 'detail_account_code' in mapping:
            analysis['hierarchy_depth'] = 3
        elif 'sub_account_code' in mapping:
            analysis['hierarchy_depth'] = 2
        elif 'main_account_code' in mapping:
            analysis['hierarchy_depth'] = 1
        
        # توزیع حساب‌ها
        for level_code, level_name in [('main', 'main'), ('sub', 'sub'), ('detail', 'detail')]:
            code_key = f'{level_code}_account_code'
            name_key = f'{level_code}_account_name'
            
            if code_key in mapping and name_key in mapping:
                unique_codes = df[mapping[code_key]].nunique()
                unique_names = df[mapping[name_key]].nunique()
                
                analysis['account_distribution'][level_code] = {
                    'unique_codes': int(unique_codes),
                    'unique_names': int(unique_names),
                    'completeness': self._calculate_completeness(df, mapping[code_key], mapping[name_key])
                }
        
        # کیفیت سلسله‌مراتب
        completeness_scores = []
        for level_data in analysis['account_distribution'].values():
            completeness_scores.append(level_data['completeness'])
        
        if completeness_scores:
            avg_completeness = sum(completeness_scores) / len(completeness_scores)
            if avg_completeness > 0.9:
                analysis['hierarchy_quality'] = 'EXCELLENT'
            elif avg_completeness > 0.7:
                analysis['hierarchy_quality'] = 'GOOD'
            elif avg_completeness > 0.5:
                analysis['hierarchy_quality'] = 'FAIR'
            else:
                analysis['hierarchy_quality'] = 'POOR'
        
        return analysis
    
    def _calculate_completeness(self, df, code_col, name_col):
        """محاسبه کامل بودن داده‌ها"""
        total_rows = len(df)
        if total_rows == 0:
            return 0.0
        
        # ردیف‌هایی که هم کد و هم نام دارند
        complete_rows = df[df[code_col].notna() & df[name_col].notna()].shape[0]
        
        return complete_rows / total_rows
    
    def extract_hierarchical_data(self, file_path, mapping=None):
        """
        استخراج داده‌های سلسله‌مراتبی از فایل
        
        Args:
            file_path: مسیر فایل
            mapping: mapping اختیاری ستون‌ها
        
        Returns:
            لیست دیکشنری‌های داده‌های استخراج شده
        """
        df = self._read_excel_file(file_path)
        
        if df is None or len(df) == 0:
            return []
        
        # اگر mapping ارائه نشده، شناسایی خودکار
        if not mapping:
            analysis = self.analyze_hierarchical_structure(file_path)
            if 'hierarchical_mapping' in analysis:
                mapping = analysis['hierarchical_mapping']
            else:
                mapping = {}
        
        # استخراج داده‌ها
        extracted_data = []
        
        for idx, row in df.iterrows():
            data_item = {
                'row_index': idx + 1,
                'main_account_code': self._get_value(row, mapping.get('main_account_code')),
                'main_account_name': self._get_value(row, mapping.get('main_account_name')),
                'sub_account_code': self._get_value(row, mapping.get('sub_account_code')),
                'sub_account_name': self._get_value(row, mapping.get('sub_account_name')),
                'detail_account_code': self._get_value(row, mapping.get('detail_account_code')),
                'detail_account_name': self._get_value(row, mapping.get('detail_account_name')),
                'document_number': self._get_value(row, mapping.get('document_number')),
                'document_date': self._get_value(row, mapping.get('document_date')),
                'description': self._get_value(row, mapping.get('document_description')),
                'debit_amount': self._parse_numeric(self._get_value(row, mapping.get('debit'))),
                'credit_amount': self._parse_numeric(self._get_value(row, mapping.get('credit'))),
            }
            
            # فقط ردیف‌هایی که حداقل کد کل دارند را اضافه کن
            if data_item['main_account_code']:
                extracted_data.append(data_item)
        
        return extracted_data
    
    def _get_value(self, row, column_name):
        """دریافت مقدار از ردیف"""
        if not column_name or column_name not in row:
            return ''
        
        value = row[column_name]
        if pd.isna(value):
            return ''
        
        return str(value).strip()
    
    def _parse_numeric(self, value):
        """تبدیل مقدار به عدد"""
        if not value:
            return 0.0
        
        try:
            # حذف کاما و سایر نویسه‌های غیرعددی
            cleaned = str(value).replace(',', '').replace(' ', '')
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    
    def validate_hierarchy(self, file_path):
        """
        اعتبارسنجی سلسله‌مراتب داده‌ها
        
        Args:
            file_path: مسیر فایل
        
        Returns:
            دیکشنری نتایج اعتبارسنجی
        """
        analysis = self.analyze_hierarchical_structure(file_path)
        
        if 'error' in analysis:
            return {'valid': False, 'error': analysis['error']}
        
        validation_results = {
            'valid': True,
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # بررسی وجود حداقل ساختار
        if not analysis.get('has_hierarchy', False):
            validation_results['valid'] = False
            validation_results['issues'].append('ساختار سلسله‌مراتبی شناسایی نشد')
        
        # بررسی کیفیت سلسله‌مراتب
        hierarchy_quality = analysis.get('hierarchy_analysis', {}).get('hierarchy_quality', 'UNKNOWN')
        if hierarchy_quality in ['POOR', 'UNKNOWN']:
            validation_results['warnings'].append(f'کیفیت سلسله‌مراتب: {hierarchy_quality}')
        
        # بررسی کامل بودن داده‌ها
        account_distribution = analysis.get('hierarchy_analysis', {}).get('account_distribution', {})
        for level, stats in account_distribution.items():
            completeness = stats.get('completeness', 0)
            if completeness < 0.5:
                validation_results['warnings'].append(
                    f'کامل‌بودن داده‌های سطح {level}: {completeness*100:.1f}%'
                )
        
        # پیشنهادات
        if analysis.get('hierarchy_depth', 0) < 2:
            validation_results['recommendations'].append(
                'ساختار سلسله‌مراتبی کامل‌تری (کل/معین) توصیه می‌شود'
            )
        
        return validation_results
