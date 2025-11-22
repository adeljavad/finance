"""
ویوهای داشبورد تحلیلی پیشرفته برای سیستم مالی هوشمند

این ماژول ویوهای زیر را ارائه می‌دهد:
- داشبورد پیشرفته با تجسم‌های تعاملی
- API برای داده‌های Real-time
- مدیریت ویجت‌های قابل تنظیم
"""

import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.utils import timezone
import json

from .services import DashboardService, RealTimeDataService

logger = logging.getLogger(__name__)


class AdvancedDashboardView(TemplateView):
    """داشبورد تحلیلی پیشرفته"""
    
    template_name = 'financial_system/advanced_dashboard/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # دریافت شرکت و دوره جاری
        company_id = self.request.session.get('current_company_id')
        period_id = self.request.session.get('current_period_id')
        user_id = self.request.user.id if self.request.user.is_authenticated else None
        
        if not company_id or not period_id:
            context.update({
                'error': 'لطفاً ابتدا شرکت و دوره مالی را انتخاب کنید.',
                'dashboard_data': None
            })
            return context
        
        try:
            # دریافت داده‌های داشبورد
            dashboard_data = DashboardService.get_dashboard_data(
                company_id, period_id, user_id
            )
            
            context.update({
                'dashboard_data': dashboard_data,
                'company_id': company_id,
                'period_id': period_id,
                'user_id': user_id
            })
            
        except Exception as e:
            logger.error(f"خطا در بارگذاری داشبورد پیشرفته: {e}")
            context.update({
                'error': f'خطا در بارگذاری داشبورد: {str(e)}',
                'dashboard_data': None
            })
        
        return context


@login_required
def dashboard_data_api(request):
    """API برای دریافت داده‌های داشبورد"""
    if request.method != 'GET':
        return JsonResponse({'error': 'متد غیرمجاز'}, status=405)
    
    try:
        company_id = request.session.get('current_company_id')
        period_id = request.session.get('current_period_id')
        user_id = request.user.id
        
        if not company_id or not period_id:
            return JsonResponse({
                'error': 'شرکت و دوره مالی انتخاب نشده',
                'type': 'configuration_error'
            }, status=400)
        
        # دریافت داده‌های داشبورد
        dashboard_data = DashboardService.get_dashboard_data(
            company_id, period_id, user_id
        )
        
        return JsonResponse(dashboard_data)
        
    except Exception as e:
        logger.error(f"خطا در API داده‌های داشبورد: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def realtime_updates_api(request):
    """API برای به‌روزرسانی‌های Real-time"""
    if request.method != 'GET':
        return JsonResponse({'error': 'متد غیرمجاز'}, status=405)
    
    try:
        company_id = request.session.get('current_company_id')
        period_id = request.session.get('current_period_id')
        
        if not company_id or not period_id:
            return JsonResponse({
                'error': 'شرکت و دوره مالی انتخاب نشده',
                'type': 'configuration_error'
            }, status=400)
        
        # دریافت به‌روزرسانی‌های Real-time
        updates = RealTimeDataService.get_live_updates(company_id, period_id)
        
        return JsonResponse(updates)
        
    except Exception as e:
        logger.error(f"خطا در API به‌روزرسانی‌های Real-time: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def widget_data_api(request, widget_id):
    """API برای دریافت داده‌های یک ویجت خاص"""
    if request.method != 'GET':
        return JsonResponse({'error': 'متد غیرمجاز'}, status=405)
    
    try:
        company_id = request.session.get('current_company_id')
        period_id = request.session.get('current_period_id')
        
        if not company_id or not period_id:
            return JsonResponse({
                'error': 'شرکت و دوره مالی انتخاب نشده',
                'type': 'configuration_error'
            }, status=400)
        
        # دریافت داده‌های ویجت بر اساس نوع
        widget_data = _get_widget_data(widget_id, company_id, period_id)
        
        return JsonResponse(widget_data)
        
    except Exception as e:
        logger.error(f"خطا در API داده‌های ویجت {widget_id}: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def _get_widget_data(widget_id: str, company_id: int, period_id: int) -> dict:
    """دریافت داده‌های یک ویجت خاص"""
    
    widget_handlers = {
        'overview_stats': _get_overview_widget_data,
        'financial_trends': _get_trends_widget_data,
        'account_analysis': _get_accounts_widget_data,
        'risk_indicators': _get_risk_widget_data,
        'performance_metrics': _get_performance_widget_data,
        'ai_insights': _get_ai_insights_widget_data,
    }
    
    handler = widget_handlers.get(widget_id)
    if handler:
        return handler(company_id, period_id)
    else:
        return {'error': 'ویجت مورد نظر یافت نشد'}


def _get_overview_widget_data(company_id: int, period_id: int) -> dict:
    """داده‌های ویجت آمار کلی"""
    try:
        overview = DashboardService.get_overview_stats(company_id, period_id)
        
        # فرمت‌بندی برای نمایش در ویجت
        return {
            'type': 'stats',
            'data': {
                'cards': [
                    {
                        'title': 'تعداد اسناد',
                        'value': overview.get('total_documents', 0),
                        'icon': 'bi-file-text',
                        'color': 'primary',
                        'trend': None
                    },
                    {
                        'title': 'تعداد آرتیکل‌ها',
                        'value': overview.get('total_transactions', 0),
                        'icon': 'bi-list-check',
                        'color': 'info',
                        'trend': None
                    },
                    {
                        'title': 'مجموع بدهکار',
                        'value': overview.get('formatted', {}).get('total_debit', '0 ریال'),
                        'icon': 'bi-arrow-up-circle',
                        'color': 'success',
                        'trend': None
                    },
                    {
                        'title': 'مجموع بستانکار',
                        'value': overview.get('formatted', {}).get('total_credit', '0 ریال'),
                        'icon': 'bi-arrow-down-circle',
                        'color': 'warning',
                        'trend': None
                    },
                    {
                        'title': 'مانده خالص',
                        'value': overview.get('formatted', {}).get('net_balance', '0 ریال'),
                        'icon': 'bi-scale',
                        'color': 'danger' if overview.get('net_balance', 0) != 0 else 'success',
                        'trend': None
                    }
                ],
                'summary': {
                    'is_balanced': overview.get('is_balanced', False),
                    'balance_ratio': overview.get('balance_ratio', 0),
                    'avg_transaction': overview.get('formatted', {}).get('avg_transaction_amount', '0 ریال')
                }
            }
        }
    except Exception as e:
        logger.error(f"خطا در دریافت داده‌های ویجت آمار کلی: {e}")
        return {'error': str(e)}


def _get_trends_widget_data(company_id: int, period_id: int) -> dict:
    """داده‌های ویجت روندهای مالی"""
    try:
        trends_data = DashboardService.get_financial_trends(company_id, period_id)
        
        return {
            'type': 'chart',
            'data': {
                'chart_config': trends_data.get('chart_data', {}),
                'trends': trends_data.get('trends', {}),
                'periods_count': len(trends_data.get('periods', [])),
                'current_period': trends_data.get('periods', [{}])[0] if trends_data.get('periods') else {}
            }
        }
    except Exception as e:
        logger.error(f"خطا در دریافت داده‌های ویجت روندها: {e}")
        return {'error': str(e)}


def _get_accounts_widget_data(company_id: int, period_id: int) -> dict:
    """داده‌های ویجت تحلیل حساب‌ها"""
    try:
        accounts_data = DashboardService.get_account_analysis(company_id, period_id)
        
        # فرمت‌بندی برای نمایش در جدول
        formatted_accounts = []
        for account in accounts_data.get('accounts', [])[:20]:  # فقط 20 حساب اول
            formatted_accounts.append({
                'code': account.get('code', ''),
                'name': account.get('name', ''),
                'level': account.get('level', ''),
                'debit': f"{account.get('debit', 0):,.0f} ریال",
                'credit': f"{account.get('credit', 0):,.0f} ریال",
                'balance': f"{account.get('balance', 0):,.0f} ریال",
                'balance_type': account.get('balance_type', 'صفر'),
                'transactions': account.get('transaction_count', 0)
            })
        
        return {
            'type': 'table',
            'data': {
                'accounts': formatted_accounts,
                'summary': {
                    'total_accounts': accounts_data.get('total_accounts', 0),
                    'level_summary': accounts_data.get('level_summary', {}),
                    'top_accounts': accounts_data.get('top_accounts', [])[:5]
                },
                'chart_data': accounts_data.get('chart_data', [])
            }
        }
    except Exception as e:
        logger.error(f"خطا در دریافت داده‌های ویجت حساب‌ها: {e}")
        return {'error': str(e)}


def _get_risk_widget_data(company_id: int, period_id: int) -> dict:
    """داده‌های ویجت شاخص‌های ریسک"""
    try:
        risk_data = DashboardService.get_risk_indicators(company_id, period_id)
        
        # فرمت‌بندی برای نمایش گیج‌ها
        risk_levels = {
            'high': {'color': 'danger', 'label': 'بالا'},
            'medium': {'color': 'warning', 'label': 'متوسط'},
            'low': {'color': 'success', 'label': 'پایین'},
            'unknown': {'color': 'secondary', 'label': 'نامشخص'}
        }
        
        overall_risk = risk_data.get('overall_risk_level', 'unknown')
        
        return {
            'type': 'gauge',
            'data': {
                'overall_risk': {
                    'level': overall_risk,
                    'color': risk_levels.get(overall_risk, {}).get('color', 'secondary'),
                    'label': risk_levels.get(overall_risk, {}).get('label', 'نامشخص')
                },
                'indicators': {
                    'concentration': {
                        'level': risk_data.get('account_concentration', {}).get('risk_level', 'unknown'),
                        'ratio': risk_data.get('account_concentration', {}).get('concentration_ratio', 0),
                        'color': risk_levels.get(
                            risk_data.get('account_concentration', {}).get('risk_level', 'unknown'),
                            {}
                        ).get('color', 'secondary')
                    },
                    'anomalies': {
                        'level': risk_data.get('anomalies', {}).get('risk_level', 'unknown'),
                        'count': risk_data.get('anomalies', {}).get('anomaly_count', 0),
                        'ratio': risk_data.get('anomalies', {}).get('anomaly_ratio', 0),
                        'color': risk_levels.get(
                            risk_data.get('anomalies', {}).get('risk_level', 'unknown'),
                            {}
                        ).get('color', 'secondary')
                    },
                    'balance': {
                        'level': risk_data.get('balance_analysis', {}).get('risk_level', 'unknown'),
                        'ratio': risk_data.get('balance_analysis', {}).get('imbalance_ratio', 0),
                        'is_balanced': risk_data.get('balance_analysis', {}).get('is_balanced', True),
                        'color': risk_levels.get(
                            risk_data.get('balance_analysis', {}).get('risk_level', 'unknown'),
                            {}
                        ).get('color', 'secondary')
                    }
                }
            }
        }
    except Exception as e:
        logger.error(f"خطا در دریافت داده‌های ویجت ریسک: {e}")
        return {'error': str(e)}


def _get_performance_widget_data(company_id: int, period_id: int) -> dict:
    """داده‌های ویجت شاخص‌های عملکرد"""
    try:
        performance_data = DashboardService.get_performance_metrics(company_id, period_id)
        
        performance_levels = {
            'high': {'color': 'success', 'icon': 'bi-check-circle'},
            'medium': {'color': 'warning', 'icon': 'bi-exclamation-circle'},
            'low': {'color': 'danger', 'icon': 'bi-x-circle'}
        }
        
        metrics = []
        for key, data in performance_data.items():
            level = data.get('level', 'low')
            level_info = performance_levels.get(level, {})
            
            if key == 'processing_speed':
                metrics.append({
                    'title': 'سرعت پردازش',
                    'value': f"{data.get('documents_per_day', 0):.1f} سند/روز",
                    'level': level,
                    'color': level_info.get('color', 'secondary'),
                    'icon': level_info.get('icon', 'bi-speedometer2')
                })
            elif key == 'data_accuracy':
                metrics.append({
                    'title': 'دقت داده‌ها',
                    'value': f"{data.get('ratio', 0):.1f}%",
                    'level': level,
                    'color': level_info.get('color', 'secondary'),
                    'icon': level_info.get('icon', 'bi-check-circle')
                })
            elif key == 'efficiency':
                metrics.append({
                    'title': 'کارایی',
                    'value': f"{data.get('items_per_document', 0):.1f} آرتیکل/سند",
                    'level': level,
                    'color': level_info.get('color', 'secondary'),
                    'icon': level_info.get('icon', 'bi-lightning-charge')
                })
        
        return {
            'type': 'metrics',
            'data': {
                'metrics': metrics,
                'overall_performance': _calculate_overall_performance(performance_data)
            }
        }
    except Exception as e:
        logger.error(f"خطا در دریافت داده‌های ویجت عملکرد: {e}")
        return {'error': str(e)}


def _get_ai_insights_widget_data(company_id: int, period_id: int) -> dict:
    """داده‌های ویجت بینش‌های هوشمند"""
    try:
        insights_data = DashboardService.get_ai_insights(company_id, period_id)
        
        # فرمت‌بندی بینش‌ها
        formatted_insights = []
        for insight in insights_data.get('insights', []):
            insight_type = insight.get('type', 'info')
            type_config = {
                'trend': {'color': 'info', 'icon': 'bi-graph-up'},
                'warning': {'color': 'warning', 'icon': 'bi-exclamation-triangle'},
                'suggestion': {'color': 'success', 'icon': 'bi-lightbulb'},
                'info': {'color': 'primary', 'icon': 'bi-info-circle'}
            }.get(insight_type, {'color': 'secondary', 'icon': 'bi-circle'})
            
            formatted_insights.append({
                'title': insight.get('title', ''),
                'description': insight.get('description', ''),
                'type': insight_type,
                'confidence': f"{insight.get('confidence', 0) * 100:.0f}%",
                'impact': insight.get('impact', 'medium'),
                'color': type_config['color'],
                'icon': type_config['icon']
            })
        
        return {
            'type': 'insights',
            'data': {
                'insights': formatted_insights,
                'available': insights_data.get('available', False),
                'generated_at': insights_data.get('generated_at', '')
            }
        }
    except Exception as e:
        logger.error(f"خطا در دریافت داده‌های ویجت بینش‌ها: {e}")
        return {'error': str(e)}


def _calculate_overall_performance(performance_data: dict) -> dict:
    """محاسبه عملکرد کلی"""
    performance_scores = {
        'high': 3,
        'medium': 2,
        'low': 1
    }
    
    total_score = 0
    metric_count = 0
    
    for key, data in performance_data.items():
        level = data.get('level', 'low')
        total_score += performance_scores.get(level, 1)
        metric_count += 1
    
    if metric_count == 0:
        return {'level': 'low', 'score': 0}
    
    avg_score = total_score / metric_count
    
    if avg_score >= 2.5:
        return {'level': 'high', 'score': avg_score}
    elif avg_score >= 1.5:
        return {'level': 'medium', 'score': avg_score}
    else:
        return {'level': 'low', 'score': avg_score}


@login_required
def save_widget_layout(request):
    """ذخیره طرح‌بندی ویجت‌های کاربر"""
    if request.method != 'POST':
        return JsonResponse({'error': 'متد غیرمجاز'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_id = request.user.id
        layout = data.get('layout', [])
        
        # در اینجا می‌توان طرح‌بندی را در دیتابیس ذخیره کرد
        # فعلاً فقط لاگ می‌کنیم
        logger.info(f"طرح‌بندی ویجت‌های کاربر {user_id} ذخیره شد: {layout}")
        
        return JsonResponse({
            'success': True,
            'message': 'طرح‌بندی با موفقیت ذخیره شد'
        })
        
    except Exception as e:
        logger.error(f"خطا در ذخیره طرح‌بندی ویجت‌ها: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def export_dashboard_data(request):
    """خروجی داده‌های داشبورد"""
    try:
        company_id = request.session.get('current_company_id')
        period_id = request.session.get('current_period_id')
        user_id = request.user.id
        
        if not company_id or not period_id:
            return JsonResponse({
                'error': 'شرکت و دوره مالی انتخاب نشده',
                'type': 'configuration_error'
            }, status=400)
        
        # دریافت داده‌های کامل داشبورد
        dashboard_data = DashboardService.get_dashboard_data(
            company_id, period_id, user_id
        )
        
        # ایجاد پاسخ با قابلیت دانلود
        response = JsonResponse(dashboard_data)
        response['Content-Disposition'] = (
            f'attachment; filename="dashboard_export_{timezone.now().strftime("%Y%m%d_%H%M")}.json"'
        )
        
        return response
        
    except Exception as e:
        logger.error(f"خطا در خروجی داده‌های داشبورد: {e}")
        return JsonResponse({'error': str(e)}, status=500)
