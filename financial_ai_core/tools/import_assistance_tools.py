# financial_system/tools/import_assistance_tools.py
"""
ابزارهای کمک‌رسانی چت بات برای سیستم ایمپورت
"""

import logging
from typing import Dict, List, Optional
from django.db.models import Q
from data_importer.models import FinancialFile
from data_importer.validators.staged_validation_service import StagedValidationService
from financial_ai_core.services.balance_control_service import BalanceControlService
from users.models import Company, FinancialPeriod

logger = logging.getLogger(__name__)


def get_import_guidance_tool(company_id: int, file_path: str = None) -> Dict:
    """
    دریافت راهنمایی هوشمند برای ایمپورت داده‌ها
    
    Args:
        company_id: شناسه شرکت
        file_path: مسیر فایل (اختیاری)
    
    Returns:
        Dict: راهنمایی‌ها و پیشنهادات
    """
    try:
        logger.info(f"دریافت راهنمایی ایمپورت برای شرکت {company_id}")
        
        company = Company.objects.get(id=company_id)
        guidance = {
            'company_name': company.name,
            'suggestions': [],
            'common_issues': [],
            'best_practices': [],
            'file_preparation': []
        }
        
        # راهنمایی‌های عمومی
        guidance['suggestions'].extend([
            "قبل از آپلود، فایل را در اکسل بررسی کنید",
            "از فرمت استاندارد ستون‌ها استفاده کنید",
            "اطمینان حاصل کنید که جمع بدهکار و بستانکار برابر است",
            "تاریخ‌ها را به فرمت شمسی وارد کنید"
        ])
        
        # مسائل رایج
        guidance['common_issues'].extend([
            "عدم توازن بدهکار و بستانکار",
            "ستون‌های ضروری وجود ندارد",
            "مقادیر خالی در ستون‌های کلیدی",
            "فرمت تاریخ نامعتبر",
            "کد حساب‌های نامعتبر"
        ])
        
        # بهترین روش‌ها
        guidance['best_practices'].extend([
            "از نمونه فایل استاندارد استفاده کنید",
            "داده‌ها را قبل از آپلود اعتبارسنجی کنید",
            "اسناد را به صورت گروهی آپلود کنید",
            "از ابزار پیش‌نمایش برای بررسی استفاده کنید"
        ])
        
        # آماده‌سازی فایل
        guidance['file_preparation'].extend([
            "ستون‌های ضروری: شماره سند، کد حساب، بدهکار، بستانکار",
            "فرمت تاریخ: YYYY/MM/DD (شمسی)",
            "فرمت اعداد: بدون جداکننده هزارگان",
            "کد حساب: فقط حروف و اعداد انگلیسی/فارسی"
        ])
        
        # اگر فایل مشخص شده، تحلیل دقیق‌تر
        if file_path:
            file_analysis = _analyze_file_structure(file_path)
            guidance['file_analysis'] = file_analysis
        
        return guidance
        
    except Company.DoesNotExist:
        return {'error': 'شرکت یافت نشد'}
    except Exception as e:
        logger.error(f"خطا در دریافت راهنمایی ایمپورت: {e}")
        return {'error': f'خطا در دریافت راهنمایی: {str(e)}'}


def analyze_import_errors_tool(company_id: int, file_id: int = None) -> Dict:
    """
    تحلیل خطاهای ایمپورت و ارائه راهکار
    
    Args:
        company_id: شناسه شرکت
        file_id: شناسه فایل (اختیاری)
    
    Returns:
        Dict: تحلیل خطاها و راهکارها
    """
    try:
        logger.info(f"تحلیل خطاهای ایمپورت برای شرکت {company_id}")
        
        company = Company.objects.get(id=company_id)
        analysis = {
            'company_name': company.name,
            'recent_issues': [],
            'solutions': [],
            'prevention_tips': []
        }
        
        # دریافت آخرین فایل‌های مشکل‌دار
        problematic_files = FinancialFile.objects.filter(
            company=company,
            status__in=['FAILED', 'PARTIAL']
        ).order_by('-created_at')[:5]
        
        for file in problematic_files:
            file_analysis = {
                'file_name': file.file_name,
                'status': file.status,
                'error_count': getattr(file, 'error_count', 0),
                'common_issues': _extract_common_issues(file)
            }
            analysis['recent_issues'].append(file_analysis)
        
        # راهکارهای عمومی
        analysis['solutions'].extend([
            {
                'issue': 'عدم توازن اسناد',
                'solution': 'استفاده از ابزار اصلاح خودکار توازن',
                'steps': [
                    'بررسی تفاوت جمع بدهکار و بستانکار',
                    'افزودن ردیف تنظیمی',
                    'تقسیم سند به چند سند کوچک‌تر'
                ]
            },
            {
                'issue': 'ستون‌های ناقص',
                'solution': 'استفاده از نمونه فایل استاندارد',
                'steps': [
                    'دانلود نمونه فایل از سیستم',
                    'کپی کردن ساختار ستون‌ها',
                    'اطمینان از وجود ستون‌های ضروری'
                ]
            },
            {
                'issue': 'مقادیر خالی',
                'solution': 'پر کردن مقادیر ضروری',
                'steps': [
                    'بررسی ستون‌های با مقادیر خالی',
                    'استفاده از مقادیر پیش‌فرض',
                    'حذف ردیف‌های کاملاً خالی'
                ]
            }
        ])
        
        # نکات پیشگیری
        analysis['prevention_tips'].extend([
            "قبل از آپلود، فایل را در اکسل اعتبارسنجی کنید",
            "از ابزار پیش‌نمایش سیستم استفاده کنید",
            "داده‌ها را به تدریج آپلود کنید",
            "از نمونه فایل استاندارد پیروی کنید"
        ])
        
        return analysis
        
    except Company.DoesNotExist:
        return {'error': 'شرکت یافت نشد'}
    except Exception as e:
        logger.error(f"خطا در تحلیل خطاهای ایمپورت: {e}")
        return {'error': f'خطا در تحلیل: {str(e)}'}


def get_accounting_concepts_tool(company_id: int, concept_type: str = None) -> Dict:
    """
    آموزش مفاهیم حسابداری مرتبط با ایمپورت
    
    Args:
        company_id: شناسه شرکت
        concept_type: نوع مفهوم (اختیاری)
    
    Returns:
        Dict: مفاهیم و آموزش‌ها
    """
    try:
        logger.info(f"دریافت مفاهیم حسابداری برای شرکت {company_id}")
        
        company = Company.objects.get(id=company_id)
        concepts = {
            'company_name': company.name,
            'basic_concepts': [],
            'import_specific': [],
            'troubleshooting': []
        }
        
        # مفاهیم پایه
        concepts['basic_concepts'].extend([
            {
                'concept': 'معادله حسابداری',
                'explanation': 'دارایی = بدهی + سرمایه. این معادله پایه تمام معاملات حسابداری است.',
                'example': 'خرید کالا: افزایش دارایی (موجودی کالا) و افزایش بدهی (حساب‌های پرداختنی)'
            },
            {
                'concept': 'سیستم دوطرفه',
                'explanation': 'هر معامله حداقل دو اثر دارد: یک بدهکار و یک بستانکار.',
                'example': 'فروش نقدی: بدهکار به صندوق، بستانکار به فروش'
            },
            {
                'concept': 'توازن اسناد',
                'explanation': 'جمع مبالغ بدهکار باید برابر جمع مبالغ بستانکار باشد.',
                'example': 'اگر جمع بدهکار ۱,۰۰۰,۰۰۰ باشد، جمع بستانکار نیز باید ۱,۰۰۰,۰۰۰ باشد'
            }
        ])
        
        # مفاهیم مرتبط با ایمپورت
        concepts['import_specific'].extend([
            {
                'concept': 'سند حسابداری',
                'explanation': 'سند شامل یک یا چند آرتیکل است که یک معامله مالی را ثبت می‌کند.',
                'structure': 'شماره سند، تاریخ، شرح، کد حساب، بدهکار، بستانکار'
            },
            {
                'concept': 'کد حساب',
                'explanation': 'کد منحصربه‌فرد برای شناسایی هر حساب در چارت حساب.',
                'format': 'می‌تواند شامل اعداد، حروف و خط تیره باشد'
            },
            {
                'concept': 'مرکز هزینه',
                'explanation': 'برای ردیابی هزینه‌ها در بخش‌های مختلف سازمان استفاده می‌شود.',
                'usage': 'اختیاری - برای تحلیل هزینه‌های بخشی'
            }
        ])
        
        # عیب‌یابی
        concepts['troubleshooting'].extend([
            {
                'problem': 'سند نامتوازن',
                'cause': 'تفاوت بین جمع بدهکار و بستانکار',
                'solution': 'بررسی آرتیکل‌ها و افزودن ردیف تنظیمی'
            },
            {
                'problem': 'کد حساب نامعتبر',
                'cause': 'کد حساب در چارت حساب شرکت وجود ندارد',
                'solution': 'بررسی چارت حساب و استفاده از کدهای معتبر'
            },
            {
                'problem': 'تاریخ نامعتبر',
                'cause': 'فرمت تاریخ صحیح نیست یا خارج از دوره مالی است',
                'solution': 'استفاده از فرمت شمسی و اطمینان از قرارگیری در دوره مالی'
            }
        ])
        
        # اگر نوع مفهوم مشخص شده
        if concept_type:
            filtered_concepts = {
                concept_type: [c for c in concepts.get(concept_type, [])]
            }
            return filtered_concepts
        
        return concepts
        
    except Company.DoesNotExist:
        return {'error': 'شرکت یافت نشد'}
    except Exception as e:
        logger.error(f"خطا در دریافت مفاهیم حسابداری: {e}")
        return {'error': f'خطا در دریافت مفاهیم: {str(e)}'}


def validate_file_before_import_tool(file_path: str, company_id: int) -> Dict:
    """
    اعتبارسنجی فایل قبل از ایمپورت
    
    Args:
        file_path: مسیر فایل
        company_id: شناسه شرکت
    
    Returns:
        Dict: نتایج اعتبارسنجی و پیشنهادات
    """
    try:
        logger.info(f"اعتبارسنجی فایل قبل از ایمپورت: {file_path}")
        
        import pandas as pd
        
        # خواندن فایل
        df = pd.read_excel(file_path)
        
        # اعتبارسنجی مرحله‌ای
        validator = StagedValidationService()
        validation_result = validator.validate_dataframe(df)
        
        # تحلیل نتایج
        analysis = {
            'file_info': {
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns)
            },
            'validation_summary': validator.get_validation_summary(validation_result),
            'detailed_results': [],
            'recommendations': []
        }
        
        # نتایج تفصیلی
        for result in validation_result['validation_results']:
            detailed_result = {
                'level': result.level.value,
                'severity': result.severity.value,
                'message': result.message,
                'suggestions': result.suggestions or []
            }
            analysis['detailed_results'].append(detailed_result)
        
        # پیشنهادات کلی
        if validation_result['is_valid']:
            analysis['recommendations'].append({
                'type': 'success',
                'message': 'فایل معتبر است. می‌توانید ایمپورت را انجام دهید.',
                'action': 'proceed_with_import'
            })
        else:
            analysis['recommendations'].append({
                'type': 'warning',
                'message': 'فایل دارای خطا است. قبل از ایمپورت خطاها را اصلاح کنید.',
                'action': 'fix_errors_first'
            })
            
            # پیشنهادات خاص بر اساس نوع خطا
            for result in validation_result['validation_results']:
                if result.severity.value == 'error':
                    analysis['recommendations'].extend([
                        {
                            'type': 'error',
                            'message': f'خطای بحرانی: {result.message}',
                            'action': 'must_fix'
                        }
                    ])
        
        return analysis
        
    except Exception as e:
        logger.error(f"خطا در اعتبارسنجی فایل: {e}")
        return {'error': f'خطا در اعتبارسنجی: {str(e)}'}


def get_import_troubleshooting_tool(company_id: int, error_description: str) -> Dict:
    """
    عیب‌یابی خطاهای ایمپورت
    
    Args:
        company_id: شناسه شرکت
        error_description: توضیح خطا
    
    Returns:
        Dict: راهکارهای عیب‌یابی
    """
    try:
        logger.info(f"عیب‌یابی خطای ایمپورت: {error_description}")
        
        company = Company.objects.get(id=company_id)
        troubleshooting = {
            'company_name': company.name,
            'error_description': error_description,
            'possible_causes': [],
            'solutions': [],
            'prevention_tips': []
        }
        
        # تشخیص علل احتمالی بر اساس توضیح خطا
        error_lower = error_description.lower()
        
        if 'توازن' in error_lower or 'بدهکار' in error_lower or 'بستانکار' in error_lower:
            troubleshooting['possible_causes'].extend([
                'تفاوت بین جمع بدهکار و بستانکار',
                'آرتیکل‌های حذف شده',
                'مقادیر منفی در ستون‌های عددی',
                'خطا در محاسبات'
            ])
            troubleshooting['solutions'].extend([
                'استفاده از ابزار اصلاح خودکار توازن',
                'بررسی تفاوت و افزودن ردیف تنظیمی',
                'تقسیم سند به چند سند کوچک‌تر'
            ])
        
        if 'ستون' in error_lower or 'column' in error_lower:
            troubleshooting['possible_causes'].extend([
                'ستون‌های ضروری وجود ندارد',
                'نام ستون‌ها استاندارد نیست',
                'ترتیب ستون‌ها تغییر کرده'
            ])
            troubleshooting['solutions'].extend([
                'استفاده از نمونه فایل استاندارد',
                'بررسی نام ستون‌ها در راهنمای سیستم',
                'کپی کردن ساختار از فایل نمونه'
            ])
        
        if 'تاریخ' in error_lower or 'date' in error_lower:
            troubleshooting['possible_causes'].extend([
                'فرمت تاریخ نامعتبر',
                'تاریخ خارج از دوره مالی',
                'تاریخ‌های خالی'
            ])
            troubleshooting['solutions'].extend([
                'استفاده از فرمت شمسی (YYYY/MM/DD)',
                'تبدیل تاریخ‌های میلادی به شمسی',
                'پر کردن تاریخ‌های خالی'
            ])
        
        if 'حساب' in error_lower or 'account' in error_lower:
            troubleshooting['possible_causes'].extend([
                'کد حساب در چارت حساب وجود ندارد',
                'فرمت کد حساب نامعتبر',
                'کد حساب خالی'
            ])
            troubleshooting['solutions'].extend([
                'بررسی چارت حساب شرکت',
                'استفاده از کدهای حساب معتبر',
                'پر کردن کد حساب‌های خالی'
            ])
        
        # نکات پیشگیری
        troubleshooting['prevention_tips'].extend([
            "قبل از آپلود از ابزار اعتبارسنجی استفاده کنید",
            "از نمونه فایل استاندارد پیروی کنید",
            "داده‌ها را به تدریج آپلود کنید",
            "خطاها را بلافاصله پس از شناسایی اصلاح کنید"
        ])
        
        return troubleshooting
        
    except Company.DoesNotExist:
        return {'error': 'شرکت یافت نشد'}
    except Exception as e:
        logger.error(f"خطا در عیب‌یابی ایمپورت: {e}")
        return {'error': f'خطا در عیب‌یابی: {str(e)}'}


# توابع کمکی داخلی
def _analyze_file_structure(file_path: str) -> Dict:
    """تحلیل ساختار فایل"""
    try:
        import pandas as pd
        df = pd.read_excel(file_path)
        
        return {
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'sample_data': df.head(3).to_dict('records')
        }
    except Exception as e:
        return {'error': f'خطا در تحلیل فایل: {str(e)}'}


def _extract_common_issues(financial_file: FinancialFile) -> List[str]:
    """استخراج مسائل رایج از فایل مالی"""
    issues = []
    
    # این تابع می‌تواند مسائل رایج را از لاگ‌ها یا metadata استخراج کند
    # فعلاً نمونه‌ای از مسائل رایج برگردانده می‌شود
    
    common_issues = [
        "عدم توازن اسناد",
        "ستون‌های ضروری وجود ندارد", 
        "مقادیر خالی",
        "فرمت تاریخ نامعتبر"
    ]
    
    return common_issues[:2]  # فقط ۲ مورد اول


# ثبت ابزارها در سیستم چت بات
IMPORT_ASSISTANCE_TOOLS = {
    'get_import_guidance': get_import_guidance_tool,
    'analyze_import_errors': analyze_import_errors_tool,
    'get_accounting_concepts': get_accounting_concepts_tool,
    'validate_file_before_import': validate_file_before_import_tool,
    'get_import_troubleshooting': get_import_troubleshooting_tool
}
