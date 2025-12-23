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
import pandas as pd

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
            raw_data_count = self._save_raw_data(financial_file, analysis_result, company_id)
            
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
    
    def _save_raw_data(self, financial_file, analysis_result, company_id):
        """ذخیره داده‌های خام"""
        try:
            analyzer = HierarchicalExcelAnalyzer()
            extracted_data = analyzer.extract_hierarchical_data(financial_file.file_path, analysis_result.get('hierarchical_mapping', {}))
            
            raw_data_objects = []
            
            for data_item in extracted_data:
                # تبدیل کدینگ به استاندارد
                company_codes = {
                    'main_code': data_item['main_account_code'],
                    'sub_code': data_item['sub_account_code'] if data_item['sub_account_code'] else None,
                    'detail_code': data_item['detail_account_code'] if data_item['detail_account_code'] else None,
                }
                
                standard_mapping = AccountMappingService.map_to_standard(company_id, company_codes)
                
                # ایجاد RawFinancialData
                raw_data = RawFinancialData(
                    financial_file=financial_file,
                    main_account_code=data_item['main_account_code'],
                    main_account_name=data_item['main_account_name'],
                    sub_account_code=data_item['sub_account_code'],
                    sub_account_name=data_item['sub_account_name'],
                    detail_account_code=data_item['detail_account_code'],
                    detail_account_name=data_item['detail_account_name'],
                    document_number=data_item['document_number'],
                    document_date=self._parse_date(data_item['document_date']),
                    description=data_item['description'],
                    debit_amount=data_item['debit_amount'],
                    credit_amount=data_item['credit_amount'],
                    row_index=data_item['row_index'],
                    standard_main_code=standard_mapping.get('standard_main_code', ''),
                    standard_main_name=standard_mapping.get('standard_main_name', ''),
                    standard_sub_code=standard_mapping.get('standard_sub_code', ''),
                    standard_sub_name=standard_mapping.get('standard_sub_name', ''),
                    standard_detail_code=standard_mapping.get('standard_detail_code', ''),
                    standard_detail_name=standard_mapping.get('standard_detail_name', ''),
                    mapping_applied=standard_mapping.get('is_suggested', False) == False
                )
                
                raw_data_objects.append(raw_data)
            
            # ذخیره دسته‌ای
            if raw_data_objects:
                RawFinancialData.objects.bulk_create(raw_data_objects)
            
            return len(raw_data_objects)
            
        except Exception as e:
            # لاگ خطا
            print(f"Error saving raw data: {e}")
            return 0
    
    def _get_sample_data(self, file_path, analysis_result):
        """دریافت نمونه داده‌ها"""
        try:
            analyzer = HierarchicalExcelAnalyzer()
            extracted_data = analyzer.extract_hierarchical_data(file_path, analysis_result.get('hierarchical_mapping', {}))
            
            # برگرداندن ۵ نمونه اول
            return extracted_data[:5]
            
        except Exception as e:
            print(f"Error getting sample data: {e}")
            return []
    
    def _parse_date(self, date_str):
        """تبدیل رشته تاریخ به شیء تاریخ"""
        if not date_str:
            return None
        
        try:
            # تلاش برای تبدیل به تاریخ
            if isinstance(date_str, str):
                # فرمت‌های مختلف تاریخ
                import datetime
                
                # فرمت شمسی
                if '/' in date_str:
                    parts = date_str.split('/')
                    if len(parts) == 3:
                        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                        # تبدیل شمسی به میلادی (ساده‌سازی شده)
                        # TODO: استفاده از کتابخانه‌های تبدیل تاریخ
                        return datetime.date(year + 621, month, day)
                
                # فرمت میلادی
                elif '-' in date_str:
                    return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            
            return None
            
        except Exception:
            return None


class AnalyzeOnlyView(APIView):
    """ویو تحلیل بدون ذخیره"""
    
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        serializer = HierarchicalUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'error': 'داده‌های ورودی نامعتبر', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        excel_file = serializer.validated_data['excel_file']
        
        try:
            # ذخیره موقت
            temp_file_path = self._save_temp_file(excel_file)
            
            # تحلیل
            analyzer = HierarchicalExcelAnalyzer()
            analysis_result = analyzer.analyze_hierarchical_structure(temp_file_path)
            
            if 'error' in analysis_result:
                return Response(
                    {'error': 'خطا در تحلیل فایل', 'details': analysis_result['error']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # اعتبارسنجی
            validation_result = analyzer.validate_hierarchy(temp_file_path)
            
            # استخراج نمونه داده‌ها
            sample_data = analyzer.extract_hierarchical_data(temp_file_path, analysis_result.get('hierarchical_mapping', {}))
            
            # پاکسازی
            os.remove(temp_file_path)
            
            return Response({
                'success': True,
                'analysis': analysis_result,
                'validation': validation_result,
                'sample_data': sample_data[:10],  # 10 نمونه اول
                'total_rows': len(sample_data),
                'message': 'فایل با موفقیت تحلیل شد'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': 'خطا در تحلیل فایل', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
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
