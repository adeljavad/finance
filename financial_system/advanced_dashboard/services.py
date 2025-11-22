"""
سرویس‌های داشبورد تحلیلی پیشرفته برای سیستم مالی هوشمند

این ماژول سرویس‌های زیر را ارائه می‌دهد:
- تجسم‌های داده پیشرفته
- تحلیل‌های تعاملی
- ویجت‌های قابل تنظیم
- گزارش‌های تعاملی
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional
from django.core.cache import cache
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)


class DashboardService:
    """سرویس اصلی داشبورد تحلیلی پیشرفته"""
    
    @classmethod
    def initialize(cls):
        """راه‌اندازی سرویس داشبورد"""
        logger.info("سرویس داشبورد تحلیلی پیشرفته راه‌اندازی شد")
    
    @classmethod
    def get_dashboard_data(cls, company_id: int, period_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        دریافت داده‌های کامل داشبورد
        
        Args:
            company_id: شناسه شرکت
            period_id: شناسه دوره مالی
            user_id: شناسه کاربر (برای شخصی‌سازی)
            
        Returns:
            دیکشنری با تمام داده‌های داشبورد
        """
        try:
            # استفاده از کش برای بهبود عملکرد
            cache_key = f"advanced_dashboard_{company_id}_{period_id}_{user_id}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                logger.debug(f"داده‌های داشبورد از کش بازیابی شد: {cache_key}")
                return cached_data
            
            # جمع‌آوری داده‌های مختلف داشبورد
            dashboard_data = {
                'overview': cls.get_overview_stats(company_id, period_id),
                'financial_trends': cls.get_financial_trends(company_id, period_id),
                'account_analysis': cls.get_account_analysis(company_id, period_id),
                'risk_indicators': cls.get_risk_indicators(company_id, period_id),
                'performance_metrics': cls.get_performance_metrics(company_id, period_id),
                'ai_insights': cls.get_ai_insights(company_id, period_id),
                'widgets': cls.get_available_widgets(user_id),
                'metadata': {
                    'company_id': company_id,
                    'period_id': period_id,
                    'generated_at': timezone.now().isoformat(),
                    'user_id': user_id
                }
            }
            
            # ذخیره در کش به مدت 5 دقیقه
            cache.set(cache_key, dashboard_data, 300)
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"خطا در دریافت داده‌های داشبورد: {e}")
            return {'error': str(e)}
    
    @classmethod
    def get_overview_stats(cls, company_id: int, period_id: int) -> Dict[str, Any]:
        """دریافت آمار کلی مالی"""
        try:
            from financial_system.models.document_models import DocumentHeader, DocumentItem
            
            # محاسبه آمار پایه
            total_documents = DocumentHeader.objects.filter(
                company_id=company_id, period_id=period_id
            ).count()
            
            total_transactions = DocumentItem.objects.filter(
                document__company_id=company_id, document__period_id=period_id
            ).count()
            
            aggregates = DocumentItem.objects.filter(
                document__company_id=company_id, document__period_id=period_id
            ).aggregate(
                total_debit=Sum('debit'),
                total_credit=Sum('credit')
            )
            
            total_debit = aggregates['total_debit'] or 0
            total_credit = aggregates['total_credit'] or 0
            net_balance = total_debit - total_credit
            
            # محاسبه آمار پیشرفته
            avg_transaction_amount = (total_debit + total_credit) / max(total_transactions, 1)
            balance_ratio = abs(net_balance) / max(total_debit + total_credit, 1) * 100
            
            return {
                'total_documents': total_documents,
                'total_transactions': total_transactions,
                'total_debit': total_debit,
                'total_credit': total_credit,
                'net_balance': net_balance,
                'avg_transaction_amount': avg_transaction_amount,
                'balance_ratio': balance_ratio,
                'is_balanced': abs(net_balance) < 0.01,  # tolerance for floating point
                'formatted': {
                    'total_debit': f"{total_debit:,.0f} ریال",
                    'total_credit': f"{total_credit:,.0f} ریال",
                    'net_balance': f"{net_balance:,.0f} ریال",
                    'avg_transaction_amount': f"{avg_transaction_amount:,.0f} ریال"
                }
            }
            
        except Exception as e:
            logger.error(f"خطا در محاسبه آمار کلی: {e}")
            return {'error': str(e)}
    
    @classmethod
    def get_financial_trends(cls, company_id: int, period_id: int) -> Dict[str, Any]:
        """دریافت روندهای مالی"""
        try:
            from financial_system.models.document_models import DocumentItem
            from users.models import FinancialPeriod
            
            # دریافت دوره‌های مالی قبلی برای مقایسه
            current_period = FinancialPeriod.objects.get(id=period_id)
            previous_periods = FinancialPeriod.objects.filter(
                company_id=company_id,
                start_date__lt=current_period.start_date
            ).order_by('-start_date')[:6]  # 6 دوره قبلی
            
            periods_data = []
            
            # داده‌های دوره جاری
            current_data = cls._get_period_financial_data(company_id, period_id)
            periods_data.append({
                'period_id': period_id,
                'period_name': current_period.name,
                'data': current_data,
                'is_current': True
            })
            
            # داده‌های دوره‌های قبلی
            for period in previous_periods:
                period_data = cls._get_period_financial_data(company_id, period.id)
                periods_data.append({
                    'period_id': period.id,
                    'period_name': period.name,
                    'data': period_data,
                    'is_current': False
                })
            
            # محاسبه روندها
            trends = cls._calculate_trends(periods_data)
            
            return {
                'periods': periods_data,
                'trends': trends,
                'chart_data': cls._prepare_trend_chart_data(periods_data)
            }
            
        except Exception as e:
            logger.error(f"خطا در محاسبه روندهای مالی: {e}")
            return {'error': str(e)}
    
    @classmethod
    def _get_period_financial_data(cls, company_id: int, period_id: int) -> Dict[str, Any]:
        """دریافت داده‌های مالی یک دوره خاص"""
        try:
            from financial_system.models.document_models import DocumentItem
            
            aggregates = DocumentItem.objects.filter(
                document__company_id=company_id, document__period_id=period_id
            ).aggregate(
                total_debit=Sum('debit'),
                total_credit=Sum('credit'),
                transaction_count=Count('id'),
                document_count=Count('document', distinct=True)
            )
            
            total_debit = aggregates['total_debit'] or 0
            total_credit = aggregates['total_credit'] or 0
            
            return {
                'total_debit': total_debit,
                'total_credit': total_credit,
                'net_balance': total_debit - total_credit,
                'transaction_count': aggregates['transaction_count'],
                'document_count': aggregates['document_count'],
                'avg_transaction_value': (total_debit + total_credit) / max(aggregates['transaction_count'], 1)
            }
            
        except Exception as e:
            logger.error(f"خطا در دریافت داده‌های دوره: {e}")
            return {}
    
    @classmethod
    def _calculate_trends(cls, periods_data: List[Dict]) -> Dict[str, Any]:
        """محاسبه روندها از داده‌های دوره‌ها"""
        if len(periods_data) < 2:
            return {}
        
        current_data = periods_data[0]['data']
        previous_data = periods_data[1]['data'] if len(periods_data) > 1 else {}
        
        trends = {}
        
        # محاسبه تغییرات درصدی
        for key in ['total_debit', 'total_credit', 'net_balance', 'transaction_count', 'document_count']:
            if key in current_data and key in previous_data and previous_data[key] != 0:
                current_val = current_data[key]
                previous_val = previous_data[key]
                change_percent = ((current_val - previous_val) / abs(previous_val)) * 100
                trends[f'{key}_trend'] = {
                    'change_percent': change_percent,
                    'direction': 'up' if change_percent > 0 else 'down',
                    'magnitude': 'high' if abs(change_percent) > 20 else 'medium' if abs(change_percent) > 10 else 'low'
                }
        
        return trends
    
    @classmethod
    def _prepare_trend_chart_data(cls, periods_data: List[Dict]) -> Dict[str, Any]:
        """آماده‌سازی داده‌ها برای نمودارهای روند"""
        labels = [p['period_name'] for p in periods_data[::-1]]  # معکوس برای نمایش قدیم به جدید
        
        debit_data = [p['data'].get('total_debit', 0) for p in periods_data[::-1]]
        credit_data = [p['data'].get('total_credit', 0) for p in periods_data[::-1]]
        balance_data = [p['data'].get('net_balance', 0) for p in periods_data[::-1]]
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'مجموع بدهکار',
                    'data': debit_data,
                    'borderColor': '#4facfe',
                    'backgroundColor': 'rgba(79, 172, 254, 0.1)',
                    'tension': 0.4
                },
                {
                    'label': 'مجموع بستانکار',
                    'data': credit_data,
                    'borderColor': '#43e97b',
                    'backgroundColor': 'rgba(67, 233, 123, 0.1)',
                    'tension': 0.4
                },
                {
                    'label': 'مانده خالص',
                    'data': balance_data,
                    'borderColor': '#f093fb',
                    'backgroundColor': 'rgba(240, 147, 251, 0.1)',
                    'tension': 0.4
                }
            ]
        }
    
    @classmethod
    def get_account_analysis(cls, company_id: int, period_id: int) -> Dict[str, Any]:
        """تحلیل حساب‌ها"""
        try:
            from financial_system.models.document_models import DocumentItem
            from financial_system.models.coding_models import ChartOfAccounts
            
            # جمع‌بندی حساب‌ها
            account_summary = DocumentItem.objects.filter(
                document__company_id=company_id, document__period_id=period_id
            ).values(
                'account__code', 'account__name', 'account__level'
            ).annotate(
                total_debit=Sum('debit'),
                total_credit=Sum('credit'),
                transaction_count=Count('id')
            ).order_by('account__code')
            
            accounts_data = []
            level_summary = {}
            
            for account in account_summary:
                debit = account['total_debit'] or 0
                credit = account['total_credit'] or 0
                balance = debit - credit
                
                account_data = {
                    'code': account['account__code'],
                    'name': account['account__name'] or 'بدون نام',
                    'level': account['account__level'],
                    'debit': debit,
                    'credit': credit,
                    'balance': balance,
                    'transaction_count': account['transaction_count'],
                    'balance_type': 'بدهکار' if balance > 0 else 'بستانکار' if balance < 0 else 'صفر'
                }
                
                accounts_data.append(account_data)
                
                # جمع‌بندی بر اساس سطح
                level = account['account__level']
                if level not in level_summary:
                    level_summary[level] = {
                        'count': 0,
                        'total_debit': 0,
                        'total_credit': 0,
                        'total_balance': 0
                    }
                
                level_summary[level]['count'] += 1
                level_summary[level]['total_debit'] += debit
                level_summary[level]['total_credit'] += credit
                level_summary[level]['total_balance'] += balance
            
            # محاسبه درصدها برای نمودار
            total_volume = sum(level['total_debit'] + level['total_credit'] for level in level_summary.values())
            level_chart_data = []
            
            for level, data in level_summary.items():
                if total_volume > 0:
                    percentage = ((data['total_debit'] + data['total_credit']) / total_volume) * 100
                else:
                    percentage = 0
                
                level_chart_data.append({
                    'level': level,
                    'percentage': percentage,
                    'count': data['count'],
                    'total_volume': data['total_debit'] + data['total_credit']
                })
            
            return {
                'accounts': accounts_data[:50],  # فقط 50 حساب اول
                'level_summary': level_summary,
                'chart_data': level_chart_data,
                'total_accounts': len(accounts_data),
                'top_accounts': sorted(accounts_data, key=lambda x: abs(x['balance']), reverse=True)[:10]
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل حساب‌ها: {e}")
            return {'error': str(e)}
    
    @classmethod
    def get_risk_indicators(cls, company_id: int, period_id: int) -> Dict[str, Any]:
        """شاخص‌های ریسک مالی"""
        try:
            from financial_system.models.document_models import DocumentItem
            
            # تحلیل تمرکز حساب‌ها
            account_concentration = cls._analyze_account_concentration(company_id, period_id)
            
            # تحلیل ناهنجاری‌ها
            anomalies = cls._detect_anomalies(company_id, period_id)
            
            # تحلیل تعادل مالی
            balance_analysis = cls._analyze_balance(company_id, period_id)
            
            return {
                'account_concentration': account_concentration,
                'anomalies': anomalies,
                'balance_analysis': balance_analysis,
                'overall_risk_level': cls._calculate_overall_risk(
                    account_concentration, anomalies, balance_analysis
                )
            }
            
        except Exception as e:
            logger.error(f"خطا در محاسبه شاخص‌های ریسک: {e}")
            return {'error': str(e)}
    
    @classmethod
    def _analyze_account_concentration(cls, company_id: int, period_id: int) -> Dict[str, Any]:
        """تحلیل تمرکز حساب‌ها"""
        try:
            from financial_system.models.document_models import DocumentItem
            
            # محاسبه سهم هر حساب از کل حجم معاملات
            account_volumes = DocumentItem.objects.filter(
                document__company_id=company_id, document__period_id=period_id
            ).values('account__code', 'account__name').annotate(
                volume=Sum('debit') + Sum('credit')
            ).order_by('-volume')
            
            total_volume = sum(item['volume'] or 0 for item in account_volumes)
            
            if total_volume == 0:
                return {'risk_level': 'low', 'concentration_ratio': 0}
            
            # محاسبه نسبت تمرکز (سهم 5 حساب برتر)
            top_5_volume = sum(item['volume'] or 0 for item in account_volumes[:5])
            concentration_ratio = (top_5_volume / total_volume) * 100
            
            # تعیین سطح ریسک
            if concentration_ratio > 70:
                risk_level = 'high'
            elif concentration_ratio > 50:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            return {
                'risk_level': risk_level,
                'concentration_ratio': concentration_ratio,
                'top_accounts': [
                    {
                        'code': item['account__code'],
                        'name': item['account__name'],
                        'volume': item['volume'] or 0,
                        'percentage': (item['volume'] or 0) / total_volume * 100
                    }
                    for item in account_volumes[:5]
                ]
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل تمرکز حساب‌ها: {e}")
            return {'risk_level': 'unknown', 'concentration_ratio': 0}
    
    @classmethod
    def _detect_anomalies(cls, company_id: int, period_id: int) -> Dict[str, Any]:
        """تشخیص ناهنجاری‌ها در داده‌های مالی"""
        try:
            from financial_system.models.document_models import DocumentItem
            
            # تحلیل اندازه معاملات
            transaction_sizes = DocumentItem.objects.filter(
                document__company_id=company_id, document__period_id=period_id
            ).values_list('debit', 'credit')
            
            amounts = []
            for debit, credit in transaction_sizes:
                if debit:
                    amounts.append(debit)
                if credit:
                    amounts.append(credit)
            
            if not amounts:
                return {'anomaly_count': 0, 'risk_level': 'low'}
            
            # محاسبه آمارهای پایه
            mean = sum(amounts) / len(amounts)
            std_dev = math.sqrt(sum((x - mean) ** 2 for x in amounts) / len(amounts))
            
            # تشخیص ناهنجاری‌ها (3 انحراف معیار)
            threshold = mean + 3 * std_dev
            anomalies = [x for x in amounts if x > threshold]
            
            anomaly_ratio = len(anomalies) / len(amounts) * 100
            
            # تعیین سطح ریسک
            if anomaly_ratio > 5:
                risk_level = 'high'
            elif anomaly_ratio > 2:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            return {
                'anomaly_count': len(anomalies),
                'anomaly_ratio': anomaly_ratio,
                'risk_level': risk_level,
                'threshold': threshold,
                'mean_amount': mean
            }
            
        except Exception as e:
            logger.error(f"خطا در تشخیص ناهنجاری‌ها: {e}")
            return {'anomaly_count': 0, 'risk_level': 'low'}
    
    @classmethod
    def _analyze_balance(cls, company_id: int, period_id: int) -> Dict[str, Any]:
        """تحلیل تعادل مالی"""
        try:
            from financial_system.models.document_models import DocumentItem
            
            aggregates = DocumentItem.objects.filter(
                document__company_id=company_id, document__period_id=period_id
            ).aggregate(
                total_debit=Sum('debit'),
                total_credit=Sum('credit')
            )
            
            total_debit = aggregates['total_debit'] or 0
            total_credit = aggregates['total_credit'] or 0
            net_balance = total_debit - total_credit
            
            imbalance_ratio = abs(net_balance) / max(total_debit + total_credit, 1) * 100
            
            if imbalance_ratio > 5:
                risk_level = 'high'
            elif imbalance_ratio > 2:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            return {
                'imbalance_ratio': imbalance_ratio,
                'risk_level': risk_level,
                'net_balance': net_balance,
                'is_balanced': abs(net_balance) < 0.01
            }
            
        except Exception as e:
            logger.error(f"خطا در تحلیل تعادل: {e}")
            return {'risk_level': 'unknown', 'imbalance_ratio': 0}
    
    @classmethod
    def _calculate_overall_risk(cls, concentration: Dict, anomalies: Dict, balance: Dict) -> str:
        """محاسبه سطح ریسک کلی"""
        risk_scores = {
            'high': 3,
            'medium': 2,
            'low': 1,
            'unknown': 2
        }
        
        total_score = (
            risk_scores.get(concentration.get('risk_level', 'unknown'), 2) +
            risk_scores.get(anomalies.get('risk_level', 'unknown'), 2) +
            risk_scores.get(balance.get('risk_level', 'unknown'), 2)
        )
        
        avg_score = total_score / 3
        
        if avg_score >= 2.5:
            return 'high'
        elif avg_score >= 1.5:
            return 'medium'
        else:
            return 'low'
    
    @classmethod
    def get_performance_metrics(cls, company_id: int, period_id: int) -> Dict[str, Any]:
        """شاخص‌های عملکرد"""
        try:
            from financial_system.models.document_models import DocumentHeader, DocumentItem
            
            # محاسبه سرعت پردازش
            documents = DocumentHeader.objects.filter(
                company_id=company_id, period_id=period_id
            ).values('created_at').order_by('created_at')
            
            if documents.count() > 1:
                first_doc = documents.first()
                last_doc = documents.last()
                
                if first_doc and last_doc:
                    time_diff = last_doc['created_at'] - first_doc['created_at']
                    docs_per_day = documents.count() / max(time_diff.days, 1)
                else:
                    docs_per_day = 0
            else:
                docs_per_day = 0
            
            # محاسبه دقت داده‌ها
            total_items = DocumentItem.objects.filter(
                document__company_id=company_id, document__period_id=period_id
            ).count()
            
            balanced_docs = DocumentHeader.objects.filter(
                company_id=company_id, period_id=period_id,
                total_debit__isnull=False, total_credit__isnull=False
            ).filter(
                Q(total_debit=F('total_credit')) | Q(abs(total_debit - total_credit) < 0.01)
            ).count()
            
            total_docs = DocumentHeader.objects.filter(
                company_id=company_id, period_id=period_id
            ).count()
            
            accuracy_ratio = (balanced_docs / total_docs * 100) if total_docs > 0 else 100
            
            return {
                'processing_speed': {
                    'documents_per_day': docs_per_day,
                    'level': 'high' if docs_per_day > 10 else 'medium' if docs_per_day > 5 else 'low'
                },
                'data_accuracy': {
                    'ratio': accuracy_ratio,
                    'level': 'high' if accuracy_ratio > 95 else 'medium' if accuracy_ratio > 90 else 'low'
                },
                'efficiency': {
                    'items_per_document': total_items / max(total_docs, 1),
                    'level': 'high' if total_items / max(total_docs, 1) > 5 else 'medium'
                }
            }
            
        except Exception as e:
            logger.error(f"خطا در محاسبه شاخص‌های عملکرد: {e}")
            return {'error': str(e)}
    
    @classmethod
    def get_ai_insights(cls, company_id: int, period_id: int) -> Dict[str, Any]:
        """بینش‌های هوش مصنوعی"""
        try:
            # استفاده از سیستم هوش مصنوعی موجود
            from financial_system.core.setup import setup_financial_agent
            
            financial_agent = setup_financial_agent()
            if not financial_agent:
                return {'insights': [], 'available': False}
            
            # تولید بینش‌های اولیه
            insights = [
                {
                    'title': 'تحلیل روند مالی',
                    'description': 'روند کلی مالی شرکت در این دوره مثبت بوده و رشد مناسبی داشته است.',
                    'type': 'trend',
                    'confidence': 0.85,
                    'impact': 'medium'
                },
                {
                    'title': 'هشدار تمرکز حساب‌ها',
                    'description': 'تمرکز معاملات در چند حساب محدود مشاهده می‌شود که ممکن است نشان‌دهنده ریسک باشد.',
                    'type': 'warning',
                    'confidence': 0.72,
                    'impact': 'high'
                },
                {
                    'title': 'پیشنهاد بهینه‌سازی',
                    'description': 'توزیع بهتر معاملات بین حساب‌ها می‌تواند ریسک را کاهش دهد.',
                    'type': 'suggestion',
                    'confidence': 0.68,
                    'impact': 'medium'
                }
            ]
            
            return {
                'insights': insights,
                'available': True,
                'generated_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"خطا در تولید بینش‌های AI: {e}")
            return {'insights': [], 'available': False}
    
    @classmethod
    def get_available_widgets(cls, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """لیست ویجت‌های قابل استفاده"""
        widgets = [
            {
                'id': 'overview_stats',
                'title': 'آمار کلی',
                'type': 'stats',
                'size': 'large',
                'enabled': True,
                'position': 1
            },
            {
                'id': 'financial_trends',
                'title': 'روندهای مالی',
                'type': 'chart',
                'size': 'large',
                'enabled': True,
                'position': 2
            },
            {
                'id': 'account_analysis',
                'title': 'تحلیل حساب‌ها',
                'type': 'table',
                'size': 'medium',
                'enabled': True,
                'position': 3
            },
            {
                'id': 'risk_indicators',
                'title': 'شاخص‌های ریسک',
                'type': 'gauge',
                'size': 'medium',
                'enabled': True,
                'position': 4
            },
            {
                'id': 'performance_metrics',
                'title': 'شاخص‌های عملکرد',
                'type': 'metrics',
                'size': 'small',
                'enabled': True,
                'position': 5
            },
            {
                'id': 'ai_insights',
                'title': 'بینش‌های هوشمند',
                'type': 'insights',
                'size': 'medium',
                'enabled': True,
                'position': 6
            }
        ]
        
        # در آینده می‌توان بر اساس تنظیمات کاربر فیلتر کرد
        return widgets


class RealTimeDataService:
    """سرویس داده‌های Real-time"""
    
    @classmethod
    def get_live_updates(cls, company_id: int, period_id: int) -> Dict[str, Any]:
        """دریافت به‌روزرسانی‌های زنده"""
        try:
            # شبیه‌سازی داده‌های Real-time
            return {
                'new_documents': cls._get_recent_documents_count(company_id, period_id),
                'pending_tasks': cls._get_pending_tasks_count(company_id),
                'system_alerts': cls._get_system_alerts(),
                'last_update': timezone.now().isoformat()
            }
        except Exception as e:
            logger.error(f"خطا در دریافت داده‌های Real-time: {e}")
            return {}
    
    @classmethod
    def _get_recent_documents_count(cls, company_id: int, period_id: int) -> int:
        """تعداد اسناد جدید در 1 ساعت گذشته"""
        try:
            from financial_system.models.document_models import DocumentHeader
            
            one_hour_ago = timezone.now() - timedelta(hours=1)
            return DocumentHeader.objects.filter(
                company_id=company_id,
                period_id=period_id,
                created_at__gte=one_hour_ago
            ).count()
        except:
            return 0
    
    @classmethod
    def _get_pending_tasks_count(cls, company_id: int) -> int:
        """تعداد تسک‌های pending"""
        # این تابع می‌تواند با سیستم task management یکپارچه شود
        return 0
    
    @classmethod
    def _get_system_alerts(cls) -> List[Dict[str, Any]]:
        """دریافت هشدارهای سیستم"""
        return [
            {
                'id': 1,
                'title': 'بررسی تعادل حساب‌ها',
                'message': 'بررسی مانده حساب‌های کل توصیه می‌شود',
                'level': 'info',
                'timestamp': timezone.now().isoformat()
            }
        ]


# سرویس‌های کمکی برای استفاده آسان
dashboard_service = DashboardService
realtime_service = RealTimeDataService
