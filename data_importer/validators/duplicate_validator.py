# data_importer/validators/duplicate_validator.py
from django.db import models
from django.db.models import Q
from financial_system.models import DocumentHeader, Company, FinancialPeriod
import hashlib
from typing import List, Dict, Optional

class DuplicateDocumentValidator:
    def __init__(self, company: Company, period: FinancialPeriod):
        self.company = company
        self.period = period
    
    def check_duplicate_documents(self, document_data_list: List[Dict]) -> Dict[str, List]:
        """بررسی اسناد تکراری در بین داده‌های جدید و موجود"""
        duplicates = {
            'exact_duplicates': [],      # اسناد کاملاً تکراری
            'similar_duplicates': [],    # اسناد مشابه
            'same_number_different_content': []  # همان شماره سند اما محتوای متفاوت
        }
        
        # بررسی تکراری در بین داده‌های جدید
        self._check_internal_duplicates(document_data_list, duplicates)
        
        # بررسی تکراری با داده‌های موجود در دیتابیس
        self._check_existing_duplicates(document_data_list, duplicates)
        
        return duplicates
    
    def _check_internal_duplicates(self, document_data_list: List[Dict], duplicates: Dict):
        """بررسی تکراری در بین داده‌های جدید"""
        seen_hashes = {}
        
        for i, doc_data in enumerate(document_data_list):
            doc_hash = self._calculate_document_hash(doc_data)
            
            if doc_hash in seen_hashes:
                duplicates['exact_duplicates'].append({
                    'document': doc_data,
                    'duplicate_of_index': seen_hashes[doc_hash],
                    'reason': 'سند کاملاً تکراری در فایل ورودی'
                })
            else:
                seen_hashes[doc_hash] = i
            
            # بررسی اسناد با شماره سند تکراری اما محتوای متفاوت
            self._check_same_number_different_content(doc_data, document_data_list, i, duplicates)
    
    def _check_existing_duplicates(self, document_data_list: List[Dict], duplicates: Dict):
        """بررسی تکراری با داده‌های موجود در دیتابیس"""
        existing_documents = DocumentHeader.objects.filter(
            company=self.company,
            period=self.period
        ).select_related('company', 'period')
        
        existing_docs_dict = {
            doc.document_number: doc for doc in existing_documents
        }
        
        for doc_data in document_data_list:
            doc_number = doc_data.get('document_number')
            
            if doc_number in existing_docs_dict:
                existing_doc = existing_docs_dict[doc_number]
                if self._is_similar_document(existing_doc, doc_data):
                    duplicates['exact_duplicates'].append({
                        'document': doc_data,
                        'existing_document': {
                            'id': existing_doc.id,
                            'document_number': existing_doc.document_number,
                            'document_date': existing_doc.document_date,
                            'description': existing_doc.description
                        },
                        'reason': 'سند با این شماره از قبل در سیستم وجود دارد'
                    })
                else:
                    duplicates['same_number_different_content'].append({
                        'document': doc_data,
                        'existing_document': {
                            'id': existing_doc.id,
                            'document_number': existing_doc.document_number,
                            'document_date': existing_doc.document_date
                        },
                        'reason': 'شماره سند تکراری اما محتوای متفاوت'
                    })
    
    def _calculate_document_hash(self, doc_data: Dict) -> str:
        """محاسبه هش برای شناسایی اسناد کاملاً تکراری"""
        hash_content = f"{doc_data.get('document_number')}-{doc_data.get('document_date')}-{doc_data.get('total_debit')}-{doc_data.get('total_credit')}"
        return hashlib.md5(hash_content.encode()).hexdigest()
    
    def _check_same_number_different_content(self, current_doc: Dict, all_docs: List[Dict], current_index: int, duplicates: Dict):
        """بررسی اسناد با شماره یکسان اما محتوای متفاوت"""
        current_number = current_doc.get('document_number')
        
        for i, other_doc in enumerate(all_docs):
            if i != current_index and other_doc.get('document_number') == current_number:
                if not self._is_similar_document(current_doc, other_doc):
                    duplicates['same_number_different_content'].append({
                        'document': current_doc,
                        'conflicting_document': other_doc,
                        'reason': 'شماره سند تکراری با محتوای متفاوت در فایل ورودی'
                    })
    
    def _is_similar_document(self, doc1, doc2) -> bool:
        """بررسی شباهت دو سند"""
        if isinstance(doc1, DocumentHeader):
            doc1_data = {
                'document_number': doc1.document_number,
                'document_date': doc1.document_date,
                'total_debit': float(doc1.total_debit),
                'total_credit': float(doc1.total_credit)
            }
            doc2_data = doc2
        else:
            doc1_data = doc1
            doc2_data = doc2
        
        tolerance = 0.01  # تحمل ۱ ریال
        
        return (
            doc1_data.get('document_number') == doc2_data.get('document_number') and
            doc1_data.get('document_date') == doc2_data.get('document_date') and
            abs(doc1_data.get('total_debit', 0) - doc2_data.get('total_debit', 0)) <= tolerance and
            abs(doc1_data.get('total_credit', 0) - doc2_data.get('total_credit', 0)) <= tolerance
        )