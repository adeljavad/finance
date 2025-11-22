# data_importer/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings
import os
import uuid
import pandas as pd
from pathlib import Path

from .models import FinancialFile, ImportJob
from .analyzers.excel_structure_analyzer import ExcelStructureAnalyzer
import time
import gc
import logging

logger = logging.getLogger(__name__)

def _safe_delete_file(file_path):
    """حذف ایمن فایل با مدیریت خطای قفل فایل در ویندوز"""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            if file_path.exists():
                file_path.unlink()
                return True
        except PermissionError:
            if attempt < max_attempts - 1:
                # صبر کردن و تلاش مجدد
                time.sleep(0.5)
                gc.collect()  # آزاد کردن حافظه
                continue
            else:
                # آخرین تلاش ناموفق
                print(f"⚠️ نتوانست فایل را حذف کند: {file_path}")
                return False
        except Exception as e:
            print(f"⚠️ خطا در حذف فایل {file_path}: {e}")
            return False
    return False

@login_required
def data_import_dashboard(request):
    """داشبورد اصلی ایمپورت داده"""
    company_id = request.session.get('current_company_id')
    
    if not company_id:
        messages.warning(request, "لطفاً ابتدا یک شرکت انتخاب کنید")
        return redirect('users:company_selection')
    
    # دریافت شرکت از دیتابیس
    from users.models import Company, FinancialPeriod
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        messages.error(request, "شرکت انتخاب شده یافت نشد")
        return redirect('users:company_selection')
    
    # دریافت دوره مالی فعال (اگر وجود دارد)
    current_period = FinancialPeriod.objects.filter(
        company=company, 
        is_active=True
    ).first()
    
    # ذخیره در سشن برای استفاده در سایر ویوها
    request.session['current_company'] = company.id
    if current_period:
        request.session['current_period'] = current_period.id
    
    # آمار کلی - با مدیریت خطا
    try:
        recent_files = FinancialFile.objects.filter(
            company_id=company.id
        ).order_by('-uploaded_at')[:5]
        
        active_jobs = ImportJob.objects.filter(
            financial_file__company_id=company.id,
            status__in=['PENDING', 'PROCESSING']
        ).count()
        
        total_files = FinancialFile.objects.filter(company_id=company.id).count()
        successful_imports = FinancialFile.objects.filter(
            company_id=company.id, 
            status='IMPORTED'
        ).count()
    except Exception as e:
        # در صورت خطا، مقادیر پیش‌فرض تنظیم می‌شود
        recent_files = []
        active_jobs = 0
        total_files = 0
        successful_imports = 0
        messages.warning(request, f"خطا در بارگذاری آمار: {str(e)}")
    
    context = {
        'recent_files': recent_files,
        'active_jobs': active_jobs,
        'total_files': total_files,
        'successful_imports': successful_imports,
        'company': company,
        'current_period': current_period,
    }
    
    return render(request, 'data_importer/dashboard.html', context)

@login_required
def upload_excel_file(request):
    """آپلود فایل اکسل - نسخه بهبود یافته"""
    company_id = request.session.get('current_company_id')
    
    if not company_id:
        messages.error(request, "لطفاً ابتدا یک شرکت انتخاب کنید")
        return redirect('data_importer:dashboard')
    
    # دریافت شرکت از دیتابیس
    from users.models import Company, FinancialPeriod
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        messages.error(request, "شرکت انتخاب شده یافت نشد")
        return redirect('data_importer:dashboard')
    
    # دریافت دوره مالی فعال (اگر وجود دارد)
    current_period = FinancialPeriod.objects.filter(
        company=company, 
        is_active=True
    ).first()
    
    if not current_period:
        messages.error(request, "هیچ دوره مالی فعالی برای این شرکت یافت نشد")
        return redirect('data_importer:dashboard')
    
    # ذخیره در سشن برای استفاده در سایر ویوها
    request.session['current_company'] = company.id
    request.session['current_period'] = current_period.id
    
    if request.method == 'POST':
        if not request.FILES.get('excel_file'):
            messages.error(request, "لطفاً یک فایل اکسل انتخاب کنید")
            return render(request, 'data_importer/upload.html')
        
        excel_file = request.FILES['excel_file']
        
        # اعتبارسنجی نوع فایل
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, "فقط فایل‌های اکسل با پسوند .xlsx یا .xls قابل قبول هستند")
            return render(request, 'data_importer/upload.html')
        
        # اعتبارسنجی حجم فایل (حداکثر 50 مگابایت)
        if excel_file.size > 50 * 1024 * 1024:
            messages.error(request, "حجم فایل نباید بیشتر از 50 مگابایت باشد")
            return render(request, 'data_importer/upload.html')
        
        try:
            # ایجاد پوشه temp_uploads اگر وجود ندارد
            upload_dir = Path('temp_uploads')
            upload_dir.mkdir(exist_ok=True)
            
            # ذخیره فایل
            file_name = f"{uuid.uuid4()}_{excel_file.name}"
            file_path = upload_dir / file_name
            
            with open(file_path, 'wb+') as destination:
                for chunk in excel_file.chunks():
                    destination.write(chunk)
            
            # تحلیل ساختار فایل - با مدیریت صحیح فایل
            analyzer = ExcelStructureAnalyzer()
            analysis_result = analyzer.analyze_excel_structure(str(file_path))
            
            if 'error' in analysis_result:
                messages.error(request, f"خطا در تحلیل فایل: {analysis_result['error']}")
                # حذف فایل در صورت خطا - با مدیریت بهتر
                _safe_delete_file(file_path)
                return render(request, 'data_importer/upload.html')
            
            # اطمینان از معتبر بودن داده‌های JSON و تبدیل numpy types
            def convert_numpy_types(obj):
                """تبدیل انواع numpy به انواع استاندارد پایتون برای JSON"""
                import numpy as np
                if isinstance(obj, (np.integer, np.floating)):
                    return obj.item()
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(item) for item in obj]
                else:
                    return obj
            
            safe_analysis_result = convert_numpy_types(analysis_result) if analysis_result and isinstance(analysis_result, dict) else {}
            safe_columns_mapping = convert_numpy_types(analysis_result.get('columns_mapping', {})) if analysis_result and isinstance(analysis_result, dict) else {}
            
            # اطمینان از معتبر بودن تمام فیلدها
            software_type = str(safe_analysis_result.get('software_type', 'UNKNOWN'))
            confidence_score = float(safe_analysis_result.get('confidence', 0.0))
            
            # ایجاد رکورد فایل در دیتابیس
            financial_file = FinancialFile.objects.create(
                file_name=file_name,
                original_name=excel_file.name,
                file_path=str(file_path),
                file_size=excel_file.size,
                company_id=company.id,
                financial_period_id=current_period.id,
                uploaded_by=request.user,
                analysis_result=safe_analysis_result,
                software_type=software_type,
                confidence_score=confidence_score,
                columns_mapping=safe_columns_mapping
            )
            
            messages.success(request, f"فایل '{excel_file.name}' با موفقیت آپلود و تحلیل شد")
            return redirect('data_importer:preview', file_id=financial_file.id)
            
        except Exception as e:
            messages.error(request, f"خطا در پردازش فایل: {str(e)}")
            # حذف فایل در صورت خطا - با مدیریت ایمن
            if 'file_path' in locals() and file_path.exists():
                _safe_delete_file(file_path)
            return render(request, 'data_importer/upload.html')
    
    return render(request, 'data_importer/upload.html')

@login_required
def import_preview(request, file_id):
    """پیش‌نمایش و تأیید داده‌ها قبل از ایمپورت"""
    financial_file = get_object_or_404(FinancialFile, id=file_id, uploaded_by=request.user)
    
    # بررسی دسترسی کاربر به شرکت
    if not financial_file.company.can_user_access(request.user):
        messages.error(request, "شما دسترسی به این شرکت را ندارید")
        return redirect('data_importer:dashboard')
    
    # بررسی وجود داده‌های ایمپورت شده قبلی
    from .services.data_cleanup_service import DataCleanupService
    cleanup_service = DataCleanupService(financial_file.company, financial_file.financial_period)
    imported_data_stats = cleanup_service.get_imported_data_stats()
    
    context = {
        'financial_file': financial_file,
        'file_id': file_id,  # اضافه کردن file_id به context
        'original_filename': financial_file.original_name,
        'analysis_result': financial_file.analysis_result,
        'sample_data': financial_file.analysis_result.get('sample_data', {}),
        'issues': financial_file.analysis_result.get('issues', []),
        'imported_data_stats': imported_data_stats,
        'has_existing_data': imported_data_stats['has_data']
    }
    
    return render(request, 'data_importer/preview.html', context)

@login_required
def start_import(request, file_id):
    """شروع عملیات ایمپورت با استفاده از سرویس یکپارچه‌سازی"""
    if request.method == 'POST':
        financial_file = get_object_or_404(FinancialFile, id=file_id, uploaded_by=request.user)
        
        # بررسی دسترسی کاربر به شرکت
        if not financial_file.company.can_user_access(request.user):
            messages.error(request, "شما دسترسی به این شرکت را ندارید")
            return redirect('data_importer:dashboard')
        
        try:
            # استفاده از سرویس یکپارچه‌سازی جدید
            from .services.data_integration_service import import_financial_data
            
            # دریافت گزینه حذف داده‌های قبلی
            delete_existing_data = request.POST.get('delete_existing_data') == 'on'
            
            # لاگ وضعیت checkbox و تمام پارامترهای POST
            logger.info(f"🔍 شروع ایمپورت فایل {file_id}")
            logger.info(f"🔍 delete_existing_data checkbox: {request.POST.get('delete_existing_data')}")
            logger.info(f"🔍 delete_existing_data boolean: {delete_existing_data}")
            logger.info(f"🔍 تمام پارامترهای POST: {dict(request.POST)}")
            
            # اجرای عملیات وارد کردن
            result = import_financial_data(file_id, delete_existing_data=delete_existing_data)
            
            if result['status'] == 'success':
                success_message = f"عملیات وارد کردن با موفقیت انجام شد: {result['document_count']} سند، {result['item_count']} آرتیکل"
                if delete_existing_data:
                    success_message += " (داده‌های قبلی حذف شدند)"
                messages.success(request, success_message)
            else:
                error_message = "خطا در وارد کردن داده‌ها: " + ", ".join(result['errors'])
                messages.error(request, error_message)
            
            return redirect('data_importer:dashboard')
            
        except Exception as e:
            messages.error(request, f"خطا در شروع عملیات: {str(e)}")
            return redirect('data_importer:preview', file_id=file_id)
    
    return redirect('data_importer:dashboard')

@login_required
def import_status(request, job_id):
    """نمایش وضعیت عملیات ایمپورت"""
    import_job = get_object_or_404(ImportJob, job_id=job_id, financial_file__uploaded_by=request.user)
    
    context = {
        'import_job': import_job,
        'financial_file': import_job.financial_file
    }
    
    return render(request, 'data_importer/status.html', context)

@login_required
def get_import_progress(request, job_id):
    """دریافت وضعیت پیشرفت (AJAX)"""
    import_job = get_object_or_404(ImportJob, job_id=job_id, financial_file__uploaded_by=request.user)
    
    return JsonResponse({
        'job_id': import_job.job_id,
        'status': import_job.status,
        'progress': import_job.progress,
        'current_step': import_job.current_step,
        'error_message': import_job.error_message,
        'result_data': import_job.result_data
    })

@login_required
def cancel_import(request, job_id):
    """لغو عملیات ایمپورت"""
    import_job = get_object_or_404(ImportJob, job_id=job_id, financial_file__uploaded_by=request.user)
    
    if import_job.status in ['PENDING', 'PROCESSING']:
        import_job.cancel()
        messages.success(request, "عملیات ایمپورت لغو شد")
    else:
        messages.error(request, "امکان لغو این عملیات وجود ندارد")
    
    return redirect('data_importer:dashboard')

@login_required
def file_list(request):
    """لیست فایل‌های آپلود شده"""
    company_id = request.session.get('current_company_id')
    
    if not company_id:
        messages.warning(request, "لطفاً ابتدا یک شرکت انتخاب کنید")
        return redirect('data_importer:dashboard')
    
    # دریافت شرکت از دیتابیس
    from users.models import Company, FinancialPeriod
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        messages.error(request, "شرکت انتخاب شده یافت نشد")
        return redirect('data_importer:dashboard')
    
    # دریافت دوره مالی فعال (اگر وجود دارد)
    current_period = FinancialPeriod.objects.filter(
        company=company, 
        is_active=True
    ).first()
    
    if not current_period:
        messages.error(request, "هیچ دوره مالی فعالی برای این شرکت یافت نشد")
        return redirect('data_importer:dashboard')
    
    files = FinancialFile.objects.filter(
        company_id=company.id,
        financial_period_id=current_period.id
    ).order_by('-uploaded_at')
    
    context = {
        'files': files,
        'company': company,
        'current_period': current_period,
    }
    
    return render(request, 'data_importer/file_list.html', context)

@login_required
def delete_file(request, file_id):
    """حذف فایل"""
    financial_file = get_object_or_404(FinancialFile, id=file_id, uploaded_by=request.user)
    
    try:
        # حذف فایل فیزیکی
        file_path = Path(financial_file.file_path)
        if file_path.exists():
            file_path.unlink()
        
        # حذف رکورد دیتابیس
        financial_file.delete()
        
        messages.success(request, "فایل با موفقیت حذف شد")
    except Exception as e:
        messages.error(request, f"خطا در حذف فایل: {str(e)}")
    
    return redirect('data_importer:file_list')

@login_required
def cleanup_all_data(request):
    """پاک کردن کامل تمام داده‌های چهار جدول اصلی"""
    company_id = request.session.get('current_company_id')
    period_id = request.session.get('current_period')
    
    if not company_id or not period_id:
        messages.error(request, "لطفاً ابتدا یک شرکت و دوره مالی انتخاب کنید")
        return redirect('data_importer:dashboard')
    
    if request.method == 'POST':
        try:
            # استفاده از سرویس پاک کردن کامل داده‌ها
            from .services.data_cleanup_service import cleanup_all_data
            
            result = cleanup_all_data(company_id, period_id)
            
            if result['status'] == 'success':
                messages.success(request, result['message'])
                logger.info(f"✅ تمام داده‌ها حذف شدند: {result['deleted_data']}")
            else:
                messages.error(request, result['message'])
                logger.error(f"❌ خطا در حذف داده‌ها: {result['message']}")
            
            return redirect('data_importer:dashboard')
            
        except Exception as e:
            messages.error(request, f"خطا در پاک کردن داده‌ها: {str(e)}")
            logger.error(f"❌ خطا در پاک کردن داده‌ها: {e}")
            return redirect('data_importer:dashboard')
    
    # اگر GET باشد، به داشبورد برگرد
    return redirect('data_importer:dashboard')

@login_required
def extract_chart_of_accounts(request):
    """استخراج کدینگ از فایل‌های ایمپورت شده"""
    company_id = request.session.get('current_company_id')
    period_id = request.session.get('current_period')
    
    if not company_id or not period_id:
        messages.error(request, "لطفاً ابتدا یک شرکت و دوره مالی انتخاب کنید")
        return redirect('data_importer:dashboard')
    
    if request.method == 'POST':
        try:
            # دریافت شرکت و دوره مالی
            from users.models import Company, FinancialPeriod
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            # پیدا کردن آخرین فایل ایمپورت شده
            latest_file = FinancialFile.objects.filter(
                company=company,
                financial_period=period,
                status='IMPORTED'
            ).order_by('-uploaded_at').first()
            
            if not latest_file:
                messages.error(request, "هیچ فایل ایمپورت شده‌ای برای استخراج کدینگ یافت نشد")
                return redirect('data_importer:dashboard')
            
            # استفاده از سرویس یکپارچه‌سازی برای استخراج کدینگ
            from .services.data_integration_service import DataIntegrationService
            
            service = DataIntegrationService(latest_file)
            
            # خواندن داده‌های اکسل
            df = service.read_excel_data()
            
            # استخراج سلسله مراتب حساب‌ها
            logger.info(f"🚀 شروع استخراج کدینگ از فایل: {latest_file.original_name}")
            hierarchy_results = service.create_complete_chart_of_accounts_hierarchy(df)
            
            if hierarchy_results['errors']:
                messages.warning(request, f"استخراج کدینگ با خطا همراه بود: {', '.join(hierarchy_results['errors'])}")
            else:
                messages.success(request, 
                    f"کدینگ با موفقیت استخراج شد: "
                    f"CLASS={hierarchy_results['created_levels']['CLASS']}, "
                    f"SUBCLASS={hierarchy_results['created_levels']['SUBCLASS']}, "
                    f"DETAIL={hierarchy_results['created_levels']['DETAIL']} "
                    f"(مجموع: {sum(hierarchy_results['created_levels'].values())} حساب)"
                )
                logger.info(f"✅ کدینگ استخراج شد: {hierarchy_results['created_levels']}")
            
            return redirect('data_importer:dashboard')
            
        except Exception as e:
            messages.error(request, f"خطا در استخراج کدینگ: {str(e)}")
            logger.error(f"❌ خطا در استخراج کدینگ: {e}")
            return redirect('data_importer:dashboard')
    
    # اگر GET باشد، به داشبورد برگرد
    return redirect('data_importer:dashboard')
