# data_importer/services/auto_detection_service.py
import pandas as pd
from financial_system.models.software_mapping import FinancialSoftware, ExcelColumnMapping

class AutoDetectionService:
    def __init__(self):
        self.analyzer = ExcelStructureAnalyzer()
    
    def detect_and_map_columns(self, file_path: str, company_id: int) -> Dict[str, Any]:
        """کشف خودکار ساختار و ایجاد نگاشت"""
        # تحلیل ساختار
        analysis = self.analyzer.analyze_excel_structure(file_path)
        
        if analysis.get('error'):
            return {'success': False, 'error': analysis['error']}
        
        # ایجاد یا به‌روزرسانی نگاشت
        mapping_result = self._create_mapping(analysis, company_id)
        
        return {
            'success': True,
            'software_type': analysis['software_type'],
            'confidence': analysis['confidence'],
            'mapping': mapping_result,
            'sample_data': analysis['sample_data'],
            'issues': analysis['issues']
        }
    
    def _create_mapping(self, analysis: Dict, company_id: int) -> Dict:
        """ایجاد نگاشت در دیتابیس"""
        software_name = analysis['software_type']
        
        # پیدا کردن یا ایجاد نرم‌افزار
        software, created = FinancialSoftware.objects.get_or_create(
            name=software_name,
            defaults={'description': f'نرم‌افزار {software_name} - کشف خودکار'}
        )
        
        # ایجاد نگاشت‌های ستونی
        mappings_created = 0
        for std_field, excel_col in analysis['columns_mapping'].items():
            mapping, created = ExcelColumnMapping.objects.get_or_create(
                software=software,
                excel_column=excel_col,
                defaults={
                    'standard_field': std_field,
                    'data_type': self._infer_data_type(std_field),
                    'is_required': std_field in ['document_number', 'document_date', 'debit', 'credit']
                }
            )
            if created:
                mappings_created += 1
        
        return {
            'software_id': software.id,
            'software_name': software.name,
            'mappings_created': mappings_created,
            'total_mappings': len(analysis['columns_mapping'])
        }
    
    def _infer_data_type(self, field_name: str) -> str:
        """تشخیص نوع داده بر اساس نام فیلد"""
        data_types = {
            'document_number': 'STRING',
            'document_date': 'DATE',
            'debit': 'DECIMAL',
            'credit': 'DECIMAL', 
            'description': 'TEXT',
            'account_code': 'STRING',
            'class_code': 'STRING',
            'class_name': 'STRING'
        }
        return data_types.get(field_name, 'STRING')