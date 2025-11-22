# coding_manager/extractors/hierarchical_coding_extractor.py
import pandas as pd
from typing import Dict, List, Set, Tuple

class HierarchicalCodingExtractor:
    def __init__(self):
        self.extracted_codings = {
            'classes': set(),
            'subclasses': set(),
            'details': set()
        }
    
    def extract_coding_hierarchy(self, df: pd.DataFrame, mapping: Dict[str, str]) -> Dict[str, List]:
        """استخراج سلسله مراتب کدینگ از DataFrame"""
        
        # استخراج بر اساس نگاشت ستون‌ها
        for index, row in df.iterrows():
            self._extract_from_mapped_row(row, mapping)
        
        return self._structure_extracted_codings()
    
    def _extract_from_mapped_row(self, row: pd.Series, mapping: Dict[str, str]):
        """استخراج کدینگ از یک ردیف بر اساس نگاشت"""
        
        # استخراج سطح کل
        if 'class_code' in mapping and 'class_name' in mapping:
            class_code = self._clean_value(row.get(mapping['class_code']))
            class_name = self._clean_value(row.get(mapping['class_name']))
            if class_code and class_name:
                self.extracted_codings['classes'].add((class_code, class_name))
        
        # استخراج سطح معین
        if 'subclass_code' in mapping and 'subclass_name' in mapping:
            subclass_code = self._clean_value(row.get(mapping['subclass_code']))
            subclass_name = self._clean_value(row.get(mapping['subclass_name']))
            if subclass_code and subclass_name:
                parent_class = self._find_parent_class(subclass_code, self.extracted_codings['classes'])
                self.extracted_codings['subclasses'].add((subclass_code, subclass_name, parent_class))
        
        # استخراج سطح تفصیلی از حساب
        if 'account_code' in mapping:
            account_code = self._clean_value(row.get(mapping['account_code']))
            if account_code and len(account_code) >= 6:  # فرض: کد تفصیلی حداقل ۶ رقمی
                parent_subclass = self._find_parent_subclass(account_code, self.extracted_codings['subclasses'])
                if parent_subclass:
                    account_name = self._clean_value(row.get('توضیحات', ''))[:50]  # استفاده از شرح به عنوان نام
                    self.extracted_codings['details'].add((account_code, account_name, parent_subclass))
    
    def _clean_value(self, value) -> str:
        """پاکسازی مقدار"""
        if pd.isna(value) or value is None:
            return ""
        return str(value).strip()
    
    def _find_parent_class(self, subclass_code: str, classes: Set[Tuple]) -> str:
        """پیدا کردن والد کل برای معین"""
        if not subclass_code:
            return ""
        
        for class_code, class_name in classes:
            if subclass_code.startswith(class_code):
                return class_code
        
        # اگر والد مستقیم پیدا نشد، سعی کن والد بر اساس ساختار کد پیدا کنی
        if len(subclass_code) >= 2:
            potential_parent = subclass_code[:2]
            for class_code, class_name in classes:
                if class_code == potential_parent:
                    return class_code
        
        return ""
    
    def _find_parent_subclass(self, detail_code: str, subclasses: Set[Tuple]) -> str:
        """پیدا کردن والد معین برای تفصیلی"""
        if not detail_code:
            return ""
        
        for subclass_code, subclass_name, parent_class in subclasses:
            if detail_code.startswith(subclass_code):
                return subclass_code
        
        # اگر والد مستقیم پیدا نشد
        if len(detail_code) >= 4:
            potential_parent = detail_code[:4]
            for subclass_code, subclass_name, parent_class in subclasses:
                if subclass_code == potential_parent:
                    return subclass_code
        
        return ""
    
    def _structure_extracted_codings(self) -> Dict[str, List]:
        """ساختاردهی به کدینگ‌های استخراج شده"""
        return {
            'classes': [{'code': code, 'name': name} for code, name in self.extracted_codings['classes']],
            'subclasses': [{'code': code, 'name': name, 'parent_class': parent} 
                          for code, name, parent in self.extracted_codings['subclasses']],
            'details': [{'code': code, 'name': name, 'parent_subclass': parent} 
                       for code, name, parent in self.extracted_codings['details']]
        }