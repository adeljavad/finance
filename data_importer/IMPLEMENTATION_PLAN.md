# طرح اجرایی سیستم Data Importer پیشرفته

## 📋 وضعیت فعلی (۱۴۰۴/۱۰/۰۳)

### ✅ کارهای انجام شده:
1. **تحلیل کامل نیازمندی‌ها** در `ANALYSIS_SUMMARY.md`
2. **ایجاد مدل‌های جدید** در دیتابیس:
   - `RawFinancialData` - داده‌های خام با ساختار سلسله‌مراتبی
   - `StandardAccountChart` - چارت حساب استاندارد
   - `CompanyAccountMapping` - نگاشت کدهای شرکت به استاندارد
3. **اعمال migrations** با موفقیت

### ⏳ کارهای در انتظار:

---

## 🛠️ فاز ۲: سرویس‌ها و ویوهای جدید

### ۱. سرویس AccountMappingService

#### فایل: `data_importer/services/account_mapping_service.py`

```python
"""
سرویس تبدیل کدهای شرکت به کد استاندارد
"""
from django.core.cache import cache
from django.db.models import Q
from ..models import StandardAccountChart, CompanyAccountMapping

class AccountMappingService:
    
    CACHE_PREFIX = "account_mapping"
    CACHE_TIMEOUT = 3600  # 1 ساعت
    
    @classmethod
    def map_to_standard(cls, company_id, company_codes):
        """
        تبدیل کدهای شرکت به کد استاندارد
        
        Args:
            company_id: شناسه شرکت
            company_codes: دیکشنری با کلیدهای:
                - main_code: کد کل شرکت
                - sub_code: کد معین شرکت (اختیاری)
                - detail_code: کد تفصیلی شرکت (اختیاری)
        
        Returns:
            دیکشنری با کدهای استاندارد
        """
        cache_key = f"{cls.CACHE_PREFIX}:{company_id}:{company_codes['main_code']}"
        
        # بررسی cache
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # جستجوی mapping دقیق
        mapping = cls._find_exact_mapping(company_id, company_codes)
        
        if mapping:
            result = cls._format_mapping_result(mapping)
        else:
            # پیشنهاد خودکار
            result = cls._suggest_standard_codes(company_codes)
        
        # ذخیره در cache
        cache.set(cache_key, result, cls.CACHE_TIMEOUT)
        
        return result
    
    @classmethod
    def _find_exact_mapping(cls, company_id, company_codes):
        """پیدا کردن mapping دقیق"""
        query = Q(company_id=company_id, company_main_code=company_codes['main_code'])
        
        if company_codes.get('sub_code'):
            query &= Q(company_sub_code=company_codes['sub_code'])
        else:
            query &= Q(company_sub_code='') | Q(company_sub_code__isnull=True)
            
        if company_codes.get('detail_code'):
            query &= Q(company_detail_code=company_codes['detail_code'])
        else:
            query &= Q(company_detail_code='') | Q(company_detail_code__isnull=True)
        
        return CompanyAccountMapping.objects.filter(query).first()
    
    @classmethod
    def _suggest_standard_codes(cls, company_codes):
        """پیشنهاد خودکار کدهای استاندارد"""
        # الگوریتم پیشنهاد بر اساس similarity matching
        suggestions = {
            'standard_main_code': '',
            'standard_main_name': '',
            'standard_sub_code': '',
            'standard_sub_name': '',
            'standard_detail_code': '',
            'standard_detail_name': '',
            'confidence_score': 0.0,
            'is_suggested': True
        }
        
        # TODO: پیاده‌سازی الگوریتم پیشنهاد هوشمند
        return suggestions
    
    @classmethod
    def _format_mapping_result(cls, mapping):
        """فرمت‌دهی نتیجه mapping"""
        return {
            'standard_main_code': mapping.standard_main_code.standard_code,
            'standard_main_name': mapping.standard_main_code.standard_name,
            'standard_sub_code': mapping.standard_sub_code.standard_code if mapping.standard_sub_code else '',
            'standard_sub_name': mapping.standard_sub_code.standard_name if mapping.standard_sub_code else '',
            'standard_detail_code': mapping.standard_detail_code.standard_code if mapping.standard_detail_code else '',
            'standard_detail_name': mapping.standard_detail_code.standard_name if mapping.standard_detail_code else '',
            'confidence_score': mapping.confidence_score,
            'is_suggested': False,
            'mapping_id': mapping.id
        }
```

### ۲. بهبود ExcelStructureAnalyzer

#### فایل: `data_importer/analyzers/hierarchical_excel_analyzer.py`

```python
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
```

### ۳. ویو FlexibleFileUploadView

#### فایل: `data_importer/api_views/flexible_upload.py`

```python
"""
ویو واحد برای پشتیبانی از دو مدل ایمپورت
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid
import os

from ..serializers import HierarchicalUploadSerializer
from ..services.account_mapping_service import AccountMappingService
from ..analyzers.hierarchical_excel_analyzer import HierarchicalExcelAnalyzer
from ..models import FinancialFile, RawFinancialData

class FlexibleFileUploadView(APIView):
    """ویو آپلود با پشتیبانی از دو مدل"""
    
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        # تشخیص مدل بر اساس پارامترهای ورودی
        serializer = HierarchicalUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'داده‌های ورودی نامعتبر', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        excel_file = serializer.validated_data['excel_file']
        company_id = serializer.validated_data.get('company_id')
        financial_period_id = serializer.validated_data.get('financial_period_id')
        
        # تشخیص مدل
        if company_id and financial_period_id:
            # مدل A: با context شرکت و دوره مالی
            return self._upload_with_context(
                excel_file, company_id, financial_period_id, request.user
            )
        else:
            # مدل B: عمومی بدون context
            return self._upload_generic(excel_file, request.user)
    
    def _upload_with_context(self, excel_file, company_id, period_id, user):
        """آپلود با context شرکت و دوره مالی"""
        try:
            # ذخیره فایل
            file_path = self._save_uploaded_file(excel_file)
            
            # تحلیل ساختار
            analyzer = HierarchicalExcelAnalyzer()
            analysis_result = analyzer.analyze_hierarchical_structure(file_path)
            
            if 'error' in analysis_result:
                return Response(
                    {'error': 'خطا در تحلیل فایل', 'details': analysis_result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ایجاد رکورد FinancialFile
            financial_file = FinancialFile.objects.create(
                file_name=excel_file.name,
                original_name=excel_file.name,
                file_path=file_path,
                file_size=excel_file.size,
                company_id=company_id,
                financial_period_id=period_id,
                uploaded_by=user,
                analysis_result=analysis_result,
                software_type=analysis_result.get('software_type', 'UNKNOWN'),
                confidence_score=analysis_result.get('confidence', 0.0),
                columns_mapping=analysis_result.get('columns_mapping', {}),
                status='ANALYZED'
            )
            
            # ذخیره داده‌های خام
            raw_data_count = self._save_raw_data(financial_file, analysis_result)
            
            return Response({
                'success': True,
                'file_id': financial_file.id,
                'analysis': analysis_result,
                'raw_data_count': raw_data_count,
                'model_type': 'WITH_CONTEXT',
                'message': 'فایل با موفقیت آپلود و تحلیل شد'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': 'خطا در پردازش فایل', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _upload_generic(self, excel_file, user):
        """آپلود عمومی بدون context"""
        try:
            # ذخیره موقت فایل
            temp_file_path = self._save_temp_file(excel_file)
            
            # تحلیل ساختار
            analyzer = HierarchicalExcelAnalyzer()
            analysis_result = analyzer.analyze_hierarchical_structure(temp_file_path)
            
            if 'error' in analysis_result:
                return Response(
                    {'error': 'خطا در تحلیل فایل', 'details': analysis_result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # خواندن نمونه داده‌ها
            sample_data = self._get_sample_data(temp_file_path, analysis_result)
            
            # پاکسازی فایل موقت
            os.remove(temp_file_path)
            
            return Response({
                'success': True,
                'analysis': analysis_result,
                'sample_data': sample_data,
                'model_type': 'GENERIC',
                'message': 'فایل با موفقیت تحلیل شد (بدون ذخیره دیتابیس)'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': 'خطا در پردازش فایل', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _save_uploaded_file(self, excel_file):
        """ذخیره فایل آپلود شده"""
        file_name = f"{uuid.uuid4()}_{excel_file.name}"
        file_path = default_storage.save(f"financial_files/{file_name}", ContentFile(excel_file.read()))
        return file_path
    
    def _save_temp_file(self, excel_file):
        """ذخیره فایل موقت"""
        temp_dir = 'temp_uploads'
        os.makedirs(temp_dir, exist_ok=True)
        
        file_name = f"{uuid.uuid4()}_{excel_file.name}"
        file_path = os.path.join(temp_dir, file_name)
        
        with open(file_path, 'wb+') as destination:
            for chunk in excel_file.chunks():
                destination.write(chunk)
        
        return file_path
    
    def _save_raw_data(self, financial_file, analysis_result):
        """ذخیره داده‌های خام"""
        # TODO: پیاده‌سازی خواندن فایل و ذخیره در RawFinancialData
        return 0
    
    def _get_sample_data(self, file_path, analysis_result):
        """دریافت نمونه داده‌ها"""
        # TODO: پیاده‌سازی خواندن نمونه داده‌ها
        return []
```

---

## 🔄 تغییرات لازم در اپ financial_system

### ۱. اضافه کردن dependency به data_importer

#### فایل: `financial_system/services/__init__.py`

```python
"""
سرویس‌های مالی - یکپارچه با data_importer
"""
from data_importer.services.account_mapping_service import AccountMappingService
from data_importer.analyzers.hierarchical_excel_analyzer import HierarchicalExcelAnalyzer

class FinancialDataService:
    """سرویس یکپارچه داده‌های مالی"""
    
    @staticmethod
    def import_financial_data(file_path, company_id, period_id, user_id):
        """
        وارد کردن داده‌های مالی با استفاده از سیستم data_importer
        
        Args:
            file_path: مسیر فایل اکسل
            company_id: شناسه شرکت
            period_id: شناسه دوره مالی
            user_id: شناسه کاربر
            
        Returns:
            نتیجه import
        """
        # استفاده از تحلیل‌گر سلسله‌مراتبی
        analyzer = HierarchicalExcelAnalyzer()
        analysis = analyzer.analyze_hierarchical_structure(file_path)
        
        if 'error' in analysis:
            return {'success': False, 'error': analysis['error']}
        
        # تبدیل کدینگ
        mapping_service
