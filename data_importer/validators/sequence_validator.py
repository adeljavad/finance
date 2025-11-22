# data_importer/validators/sequence_validator.py
from typing import List, Dict, Tuple
import pandas as pd
from datetime import datetime

class DocumentSequenceValidator:
    def __init__(self, company_id: int, period_id: int):
        self.company_id = company_id
        self.period_id = period_id
    
    def validate_document_sequence(self, document_data_list: List[Dict]) -> Dict[str, List]:
        """اعتبارسنجی توالی شماره اسناد"""
        sequence_issues = {
            'gaps': [],           # شکاف در شماره اسناد
            'duplicates': [],     # شماره‌های تکراری
            'out_of_order': [],   # اسناد خارج از ترتیب
            'invalid_format': []  # فرمت نامعتبر شماره سند
        }
        
        if not document_data_list:
            return sequence_issues
        
        # مرتب‌سازی اسناد بر اساس شماره سند
        sorted_docs = self._sort_documents_by_number(document_data_list)
        
        # بررسی توالی
        self._check_sequence_gaps(sorted_docs, sequence_issues)
        self._check_duplicates(sorted_docs, sequence_issues)
        self._check_number_format(sorted_docs, sequence_issues)
        
        return sequence_issues
    
    def _sort_documents_by_number(self, document_data_list: List[Dict]) -> List[Dict]:
        """مرتب‌سازی اسناد بر اساس شماره سند"""
        def extract_numeric_part(doc_number):
            try:
                # استخراج قسمت عددی از شماره سند
                if isinstance(doc_number, (int, float)):
                    return int(doc_number)
                elif isinstance(doc_number, str):
                    # حذف کاراکترهای غیرعددی
                    numeric_part = ''.join(filter(str.isdigit, doc_number))
                    return int(numeric_part) if numeric_part else 0
                else:
                    return 0
            except (ValueError, TypeError):
                return 0
        
        return sorted(document_data_list, key=lambda x: extract_numeric_part(x.get('document_number')))
    
    def _check_sequence_gaps(self, sorted_docs: List[Dict], issues: Dict):
        """بررسی شکاف در توالی شماره اسناد"""
        if len(sorted_docs) < 2:
            return
        
        for i in range(1, len(sorted_docs)):
            current_num = self._extract_numeric(sorted_docs[i].get('document_number'))
            previous_num = self._extract_numeric(sorted_docs[i-1].get('document_number'))
            
            if current_num - previous_num > 1:
                issues['gaps'].append({
                    'gap_start': previous_num,
                    'gap_end': current_num,
                    'missing_count': current_num - previous_num - 1,
                    'before_document': sorted_docs[i-1].get('document_number'),
                    'after_document': sorted_docs[i].get('document_number')
                })
    
    def _check_duplicates(self, sorted_docs: List[Dict], issues: Dict):
        """بررسی شماره‌های تکراری"""
        seen_numbers = {}
        
        for doc in sorted_docs:
            doc_number = doc.get('document_number')
            if doc_number in seen_numbers:
                issues['duplicates'].append({
                    'document_number': doc_number,
                    'first_occurrence': seen_numbers[doc_number],
                    'duplicate_document': doc
                })
            else:
                seen_numbers[doc_number] = doc
    
    def _check_number_format(self, sorted_docs: List[Dict], issues: Dict):
        """بررسی فرمت شماره سند"""
        for doc in sorted_docs:
            doc_number = doc.get('document_number')
            if not self._is_valid_document_number(doc_number):
                issues['invalid_format'].append({
                    'document': doc,
                    'document_number': doc_number,
                    'reason': 'فرمت شماره سند نامعتبر'
                })
    
    def _extract_numeric(self, doc_number) -> int:
        """استخراج قسمت عددی از شماره سند"""
        try:
            if isinstance(doc_number, (int, float)):
                return int(doc_number)
            elif isinstance(doc_number, str):
                numeric_part = ''.join(filter(str.isdigit, doc_number))
                return int(numeric_part) if numeric_part else 0
            else:
                return 0
        except (ValueError, TypeError):
            return 0
    
    def _is_valid_document_number(self, doc_number) -> bool:
        """اعتبارسنجی فرمت شماره سند"""
        if doc_number is None:
            return False
        
        if isinstance(doc_number, (int, float)):
            return doc_number > 0
        
        if isinstance(doc_number, str):
            # بررسی وجود حداقل یک عدد
            return any(char.isdigit() for char in doc_number)
        
        return False
    
    def generate_sequence_report(self, document_data_list: List[Dict]) -> Dict:
        """تولید گزارش توالی اسناد"""
        sequence_issues = self.validate_document_sequence(document_data_list)
        
        total_documents = len(document_data_list)
        numeric_numbers = [self._extract_numeric(doc.get('document_number')) for doc in document_data_list]
        
        if numeric_numbers:
            min_number = min(numeric_numbers)
            max_number = max(numeric_numbers)
            expected_count = max_number - min_number + 1 if max_number > min_number else 1
            gap_percentage = (expected_count - total_documents) / expected_count * 100 if expected_count > 0 else 0
        else:
            min_number = max_number = expected_count = gap_percentage = 0
        
        return {
            'summary': {
                'total_documents': total_documents,
                'min_document_number': min_number,
                'max_document_number': max_number,
                'expected_document_count': expected_count,
                'gap_percentage': round(gap_percentage, 2),
                'completeness_score': max(0, 100 - gap_percentage)
            },
            'issues': sequence_issues,
            'recommendations': self._generate_recommendations(sequence_issues)
        }
    
    def _generate_recommendations(self, sequence_issues: Dict) -> List[str]:
        """تولید توصیه‌ها بر اساس مشکلات توالی"""
        recommendations = []
        
        if sequence_issues['gaps']:
            recommendations.append("شکاف در توالی شماره اسناد مشاهده شد. بررسی کنید آیا اسناد مفقودی وجود دارد.")
        
        if sequence_issues['duplicates']:
            recommendations.append("شماره اسناد تکراری وجود دارد. باید یکی از اسناد حذف یا شماره‌گذاری اصلاح شود.")
        
        if sequence_issues['out_of_order']:
            recommendations.append("اسناد خارج از ترتیب تاریخی هستند. بهتر است بر اساس تاریخ مرتب شوند.")
        
        if sequence_issues['invalid_format']:
            recommendations.append("برخی اسناد فرمت شماره نامعتبر دارند.")
        
        if not any(sequence_issues.values()):
            recommendations.append("توالی اسناد صحیح است.")
        
        return recommendations