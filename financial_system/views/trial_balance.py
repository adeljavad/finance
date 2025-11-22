# financial_system/views/trial_balance.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from django.utils import timezone
import json
from datetime import datetime

from users.models import Company, FinancialPeriod
from financial_system.models.document_models import DocumentItem
from financial_system.models.coding_models import ChartOfAccounts

@login_required
def trial_balance_report(request):
    """گزارش تراز آزمایشی با قابلیت انتخاب سطح و فیلتر تاریخ"""
    company_id = request.session.get('current_company_id')
    period_id = request.session.get('current_period_id')
    
    if not company_id or not period_id:
        messages.error(request, 'لطفاً ابتدا شرکت و دوره مالی را انتخاب کنید.')
        return redirect('financial_system:dashboard')
    
    company = get_object_or_404(Company, id=company_id)
    period = get_object_or_404(FinancialPeriod, id=period_id)
    
    # دریافت پارامترهای فیلتر
    level_filter = request.GET.get('level', 'ALL')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # اعتبارسنجی تاریخ‌ها
    try:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date = None
        end_date = None
        messages.warning(request, 'فرمت تاریخ نامعتبر است. از فرمت YYYY-MM-DD استفاده کنید.')
    
    # تولید گزارش
    try:
        report_data = _generate_trial_balance_with_filters(
            company_id, period_id, level_filter, start_date, end_date
        )
        
        context = {
            'company': company,
            'period': period,
            'report_name': 'تراز آزمایشی',
            'report_slug': 'trial_balance',
            'report_data': report_data,
            'level_filter': level_filter,
            'start_date': start_date.strftime('%Y-%m-%d') if start_date else '',
            'end_date': end_date.strftime('%Y-%m-%d') if end_date else '',
            'account_levels': [
                {'value': 'ALL', 'label': 'همه سطوح'},
                {'value': 'CLASS', 'label': 'گروه (کل)'},
                {'value': 'SUBCLASS', 'label': 'معین'},
                {'value': 'DETAIL', 'label': 'تفصیلی'},
                {'value': 'PROJECT', 'label': 'پروژه'},
                {'value': 'COST_CENTER', 'label': 'مرکز هزینه'},
            ],
            'generated_at': timezone.now(),
        }
        
        return render(request, 'financial_system/trial_balance_report.html', context)
        
    except Exception as e:
        logger.error(f"خطا در تولید تراز آزمایشی: {e}")
        messages.error(request, f'خطا در تولید گزارش: {str(e)}')
        return redirect('financial_system:reports')

def _generate_trial_balance_with_filters(company_id, period_id, level_filter='ALL', start_date=None, end_date=None):
    """تولید تراز آزمایشی با فیلترهای سطح و تاریخ"""
    try:
        # ساخت کوئری پایه
        base_query = DocumentItem.objects.filter(
            document__company_id=company_id,
            document__period_id=period_id
        )
        
        # اعمال فیلتر تاریخ
        if start_date:
            base_query = base_query.filter(document__document_date__gte=start_date)
        if end_date:
            base_query = base_query.filter(document__document_date__lte=end_date)
        
        # اگر سطح خاصی انتخاب شده، فیلتر سطح حساب
        if level_filter != 'ALL':
            base_query = base_query.filter(account__level=level_filter)
        
        # جمع‌بندی گردش حساب‌ها
        account_turnover = base_query.values(
            'account__code',
            'account__name',
            'account__level'
        ).annotate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit'),
            transaction_count=Count('id')
        ).order_by('account__code')
        
        # محاسبه مانده هر حساب
        accounts_data = []
        total_debit = 0
        total_credit = 0
        
        for account in account_turnover:
            debit = account['total_debit'] or 0
            credit = account['total_credit'] or 0
            balance = debit - credit
            
            # تعیین نوع مانده
            balance_type = 'بدهکار' if balance > 0 else 'بستانکار' if balance < 0 else 'صفر'
            
            accounts_data.append({
                'account_code': account['account__code'],
                'account_name': account['account__name'] or 'بدون نام',
                'account_level': account['account__level'],
                'account_level_display': _get_level_display(account['account__level']),
                'debit': debit,
                'credit': credit,
                'balance': abs(balance),
                'balance_type': balance_type,
                'transaction_count': account['transaction_count'],
                'formatted_debit': f"{debit:,.0f} ریال",
                'formatted_credit': f"{credit:,.0f} ریال",
                'formatted_balance': f"{abs(balance):,.0f} ریال",
                'balance_display': f"{abs(balance):,.0f} ریال ({balance_type})"
            })
            
            total_debit += debit
            total_credit += credit
        
        # محاسبه مانده کل
        total_balance = total_debit - total_credit
        total_balance_type = 'بدهکار' if total_balance > 0 else 'بستانکار' if total_balance < 0 else 'صفر'
        
        # آمار سطح‌های حساب
        level_stats = _calculate_level_statistics(accounts_data)
        
        trial_balance_data = {
            'accounts': accounts_data,
            'summary': {
                'total_accounts': len(accounts_data),
                'total_debit': total_debit,
                'total_credit': total_credit,
                'total_balance': abs(total_balance),
                'total_balance_type': total_balance_type,
                'is_balanced': total_balance == 0,
                'formatted_total_debit': f"{total_debit:,.0f} ریال",
                'formatted_total_credit': f"{total_credit:,.0f} ریال",
                'formatted_total_balance': f"{abs(total_balance):,.0f} ریال ({total_balance_type})",
                'balance_status': 'متوازن' if total_balance == 0 else 'نامتوازن'
            },
            'filters': {
                'level_filter': level_filter,
                'start_date': start_date,
                'end_date': end_date,
                'level_filter_display': _get_level_display(level_filter) if level_filter != 'ALL' else 'همه سطوح'
            },
            'level_statistics': level_stats
        }
        
        return {
            'type': 'trial_balance',
            'title': 'تراز آزمایشی',
            'data': trial_balance_data
        }
        
    except Exception as e:
        logger.error(f"خطا در تولید تراز آزمایشی با فیلتر: {e}")
        return {
            'type': 'trial_balance',
            'title': 'تراز آزمایشی',
            'data': {'error': f'خطا در تولید گزارش: {str(e)}'}
        }

def _get_level_display(level_code):
    """نمایش فارسی سطح حساب"""
    level_map = {
        'CLASS': 'گروه (کل)',
        'SUBCLASS': 'معین',
        'DETAIL': 'تفصیلی',
        'PROJECT': 'پروژه',
        'COST_CENTER': 'مرکز هزینه',
        'ALL': 'همه سطوح'
    }
    return level_map.get(level_code, level_code)

def _calculate_level_statistics(accounts_data):
    """محاسبه آمار سطح‌های حساب"""
    level_stats = {}
    
    for account in accounts_data:
        level = account['account_level']
        if level not in level_stats:
            level_stats[level] = {
                'count': 0,
                'total_debit': 0,
                'total_credit': 0,
                'display_name': account['account_level_display']
            }
        
        level_stats[level]['count'] += 1
        level_stats[level]['total_debit'] += account['debit']
        level_stats[level]['total_credit'] += account['credit']
    
    # محاسبه مانده برای هر سطح
    for level in level_stats:
        stats = level_stats[level]
        balance = stats['total_debit'] - stats['total_credit']
        stats['total_balance'] = abs(balance)
        stats['balance_type'] = 'بدهکار' if balance > 0 else 'بستانکار' if balance < 0 else 'صفر'
        stats['formatted_balance'] = f"{abs(balance):,.0f} ریال ({stats['balance_type']})"
        stats['formatted_debit'] = f"{stats['total_debit']:,.0f} ریال"
        stats['formatted_credit'] = f"{stats['total_credit']:,.0f} ریال"
    
    return level_stats

@login_required
def trial_balance_api(request):
    """API برای دریافت تراز آزمایشی"""
    if request.method == 'GET':
        try:
            company_id = request.session.get('current_company_id')
            period_id = request.session.get('current_period_id')
            
            if not company_id or not period_id:
                return JsonResponse({'error': 'شرکت و دوره مالی انتخاب نشده'}, status=400)
            
            # دریافت پارامترهای فیلتر
            level_filter = request.GET.get('level', 'ALL')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # اعتبارسنجی تاریخ‌ها
            try:
                if start_date:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                if end_date:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = None
                end_date = None
            
            # تولید گزارش
            report_data = _generate_trial_balance_with_filters(
                company_id, period_id, level_filter, start_date, end_date
            )
            
            return JsonResponse(report_data)
            
        except Exception as e:
            logger.error(f"خطا در API تراز آزمایشی: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'متد غیرمجاز'}, status=405)

@login_required
def export_trial_balance(request):
    """خروجی تراز آزمایشی"""
    company_id = request.session.get('current_company_id')
    period_id = request.session.get('current_period_id')
    
    if not company_id or not period_id:
        messages.error(request, 'لطفاً ابتدا شرکت و دوره مالی را انتخاب کنید.')
        return redirect('financial_system:trial_balance')
    
    # دریافت پارامترهای فیلتر
    level_filter = request.GET.get('level', 'ALL')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    try:
        # تولید گزارش
        report_data = _generate_trial_balance_with_filters(
            company_id, period_id, level_filter, start_date, end_date
        )
        
        # در اینجا می‌توانید خروجی Excel یا PDF تولید کنید
        # فعلاً فقط JSON برمی‌گردانیم
        response = JsonResponse(report_data)
        response['Content-Disposition'] = f'attachment; filename="trial_balance_{timezone.now().strftime("%Y%m%d_%H%M")}.json"'
        return response
        
    except Exception as e:
        logger.error(f"خطا در خروجی تراز آزمایشی: {e}")
        messages.error(request, f'خطا در تولید خروجی: {str(e)}')
        return redirect('financial_system:trial_balance')
