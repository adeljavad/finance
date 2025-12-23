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
    
    @classmethod
    def bulk_map_to_standard(cls, company_id, company_codes_list):
        """
        تبدیل دسته‌ای کدهای شرکت به کد استاندارد
        
        Args:
            company_id: شناسه شرکت
            company_codes_list: لیستی از دیکشنری‌های company_codes
        
        Returns:
            لیست نتایج mapping
        """
        results = []
        for company_codes in company_codes_list:
            result = cls.map_to_standard(company_id, company_codes)
            results.append(result)
        
        return results
    
    @classmethod
    def create_mapping(cls, company_id, company_codes, standard_codes, user_id, mapping_type='MANUAL', confidence=1.0):
        """
        ایجاد mapping جدید
        
        Args:
            company_id: شناسه شرکت
            company_codes: کدهای شرکت
            standard_codes: کدهای استاندارد
            user_id: شناسه کاربر ایجاد کننده
            mapping_type: نوع mapping
            confidence: امتیاز اطمینان
        
        Returns:
            شیء CompanyAccountMapping ایجاد شده
        """
        # پیدا کردن اشیاء StandardAccountChart
        standard_main = StandardAccountChart.objects.get(standard_code=standard_codes['main_code'])
        standard_sub = None
        standard_detail = None
        
        if standard_codes.get('sub_code'):
            standard_sub = StandardAccountChart.objects.get(standard_code=standard_codes['sub_code'])
        
        if standard_codes.get('detail_code'):
            standard_detail = StandardAccountChart.objects.get(standard_code=standard_codes['detail_code'])
        
        # ایجاد mapping
        mapping = CompanyAccountMapping.objects.create(
            company_id=company_id,
            company_main_code=company_codes['main_code'],
            company_main_name=company_codes.get('main_name', ''),
            company_sub_code=company_codes.get('sub_code', ''),
            company_sub_name=company_codes.get('sub_name', ''),
            company_detail_code=company_codes.get('detail_code', ''),
            company_detail_name=company_codes.get('detail_name', ''),
            standard_main_code=standard_main,
            standard_sub_code=standard_sub,
            standard_detail_code=standard_detail,
            created_by_id=user_id,
            mapping_type=mapping_type,
            confidence_score=confidence
        )
        
        # پاکسازی cache مربوطه
        cache_key = f"{cls.CACHE_PREFIX}:{company_id}:{company_codes['main_code']}"
        cache.delete(cache_key)
        
        return mapping
    
    @classmethod
    def get_mapping_stats(cls, company_id):
        """
        دریافت آمار mappingهای یک شرکت
        
        Args:
            company_id: شناسه شرکت
        
        Returns:
            دیکشنری آمار
        """
        mappings = CompanyAccountMapping.objects.filter(company_id=company_id, is_active=True)
        
        total_mappings = mappings.count()
        manual_mappings = mappings.filter(mapping_type='MANUAL').count()
        auto_mappings = mappings.filter(mapping_type='AUTO_SUGGESTED').count()
        bulk_mappings = mappings.filter(mapping_type='BULK_IMPORT').count()
        
        # محاسبه coverage
        unique_company_codes = mappings.values('company_main_code').distinct().count()
        
        return {
            'total_mappings': total_mappings,
            'manual_mappings': manual_mappings,
            'auto_mappings': auto_mappings,
            'bulk_mappings': bulk_mappings,
            'unique_company_codes': unique_company_codes,
            'coverage_percentage': round((unique_company_codes / 100) * 100, 2) if unique_company_codes > 0 else 0.0
        }
