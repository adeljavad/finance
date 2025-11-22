# financial_system/services/financial_alert_system.py
"""
تسک ۹۷: پیاده‌سازی سیستم هشدار مالی خودکار
این سرویس برای شناسایی سریع مشکلات مالی، ناهنجاری‌ها و ریسک‌ها طراحی شده است.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
from users.models import User, Company, FinancialPeriod
from financial_system.models import FinancialData, RatioAnalysis, TrendAnalysis


class FinancialAlertSystem:
    """سیستم هشدار مالی خودکار"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.alert_history = []
    
    def analyze_financial_data(self, company_id: int, period_id: int) -> Dict[str, Any]:
        """تحلیل داده‌های مالی و شناسایی هشدارها"""
        
        try:
            # دریافت داده‌های مالی
            financial_data = self._get_financial_data(company_id, period_id)
            
            if not financial_data:
                return {
                    'success': False,
                    'error': 'داده‌های مالی یافت نشد'
                }
            
            # تحلیل‌های مختلف
            ratio_alerts = self._analyze_ratios(financial_data)
            trend_alerts = self._analyze_trends(company_id, period_id)
            anomaly_alerts = self._detect_anomalies(financial_data)
            risk_alerts = self._assess_financial_risks(financial_data)
            
            # ترکیب هشدارها
            all_alerts = ratio_alerts + trend_alerts + anomaly_alerts + risk_alerts
            
            # اولویت‌بندی هشدارها
            prioritized_alerts = self._prioritize_alerts(all_alerts)
            
            # تولید گزارش هشدار
            alert_report = self._generate_alert_report(prioritized_alerts, company_id, period_id)
            
            # ذخیره تاریخچه هشدار
            self._save_alert_history(prioritized_alerts, company_id, period_id)
            
            return {
                'success': True,
                'company_id': company_id,
                'period_id': period_id,
                'total_alerts': len(prioritized_alerts),
                'high_priority_alerts': len([a for a in prioritized_alerts if a['severity'] == 'بسیار بالا']),
                'alert_report': alert_report,
                'alerts': prioritized_alerts,
                'recommendations': self._generate_recommendations(prioritized_alerts)
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل داده‌های مالی: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_financial_data(self, company_id: int, period_id: int) -> Optional[Dict[str, Any]]:
        """دریافت داده‌های مالی"""
        
        try:
            # دریافت داده‌های مالی از مدل
            financial_data = FinancialData.objects.filter(
                company_id=company_id,
                period_id=period_id
            ).first()
            
            if not financial_data:
                return None
            
            # محاسبه نسبت‌های مالی
            ratios = self._calculate_financial_ratios(financial_data)
            
            return {
                'company_id': company_id,
                'period_id': period_id,
                'balance_sheet': {
                    'total_assets': financial_data.total_assets,
                    'total_liabilities': financial_data.total_liabilities,
                    'equity': financial_data.equity,
                    'current_assets': financial_data.current_assets,
                    'current_liabilities': financial_data.current_liabilities
                },
                'income_statement': {
                    'revenue': financial_data.revenue,
                    'cost_of_goods_sold': financial_data.cost_of_goods_sold,
                    'gross_profit': financial_data.gross_profit,
                    'operating_expenses': financial_data.operating_expenses,
                    'net_income': financial_data.net_income
                },
                'cash_flow': {
                    'operating_cash_flow': financial_data.operating_cash_flow,
                    'investing_cash_flow': financial_data.investing_cash_flow,
                    'financing_cash_flow': financial_data.financing_cash_flow,
                    'net_cash_flow': financial_data.net_cash_flow
                },
                'ratios': ratios
            }
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده‌های مالی: {str(e)}")
            return None
    
    def _calculate_financial_ratios(self, financial_data) -> Dict[str, Decimal]:
        """محاسبه نسبت‌های مالی"""
        
        try:
            ratios = {}
            
            # نسبت‌های نقدینگی
            if financial_data.current_liabilities and financial_data.current_liabilities > 0:
                ratios['current_ratio'] = financial_data.current_assets / financial_data.current_liabilities
                ratios['quick_ratio'] = (financial_data.current_assets - financial_data.inventory) / financial_data.current_liabilities
            
            # نسبت‌های اهرمی
            if financial_data.total_assets and financial_data.total_assets > 0:
                ratios['debt_to_assets'] = financial_data.total_liabilities / financial_data.total_assets
                ratios['debt_to_equity'] = financial_data.total_liabilities / financial_data.equity if financial_data.equity else 0
            
            # نسبت‌های سودآوری
            if financial_data.revenue and financial_data.revenue > 0:
                ratios['gross_margin'] = financial_data.gross_profit / financial_data.revenue
                ratios['net_margin'] = financial_data.net_income / financial_data.revenue if financial_data.net_income else 0
            
            # نسبت‌های فعالیت
            if financial_data.total_assets and financial_data.total_assets > 0:
                ratios['asset_turnover'] = financial_data.revenue / financial_data.total_assets
            
            return ratios
            
        except Exception as e:
            self.logger.error(f"خطا در محاسبه نسبت‌ها: {str(e)}")
            return {}
    
    def _analyze_ratios(self, financial_data: Dict) -> List[Dict[str, Any]]:
        """تحلیل نسبت‌های مالی و شناسایی هشدارها"""
        
        alerts = []
        ratios = financial_data.get('ratios', {})
        
        # تحلیل نسبت جاری
        current_ratio = ratios.get('current_ratio')
        if current_ratio:
            if current_ratio < 1.0:
                alerts.append({
                    'type': 'نقدینگی',
                    'severity': 'بسیار بالا',
                    'title': 'ریسک نقدینگی بالا',
                    'description': f'نسبت جاری ({current_ratio:.2f}) کمتر از ۱ است، نشان‌دهنده مشکل در پرداخت بدهی‌های کوتاه‌مدت',
                    'metric': 'نسبت جاری',
                    'value': float(current_ratio),
                    'threshold': 1.0,
                    'deviation': 'پایین'
                })
            elif current_ratio < 1.5:
                alerts.append({
                    'type': 'نقدینگی',
                    'severity': 'متوسط',
                    'title': 'نقدینگی محدود',
                    'description': f'نسبت جاری ({current_ratio:.2f}) در محدوده قابل قبول اما نیاز به نظارت دارد',
                    'metric': 'نسبت جاری',
                    'value': float(current_ratio),
                    'threshold': 1.5,
                    'deviation': 'پایین'
                })
        
        # تحلیل نسبت بدهی به دارایی
        debt_to_assets = ratios.get('debt_to_assets')
        if debt_to_assets:
            if debt_to_assets > 0.7:
                alerts.append({
                    'type': 'اهرمی',
                    'severity': 'بسیار بالا',
                    'title': 'اهرم مالی بسیار بالا',
                    'description': f'نسبت بدهی به دارایی ({debt_to_assets:.2%}) بیشتر از ۷۰٪ است، ریسک ورشکستگی بالا',
                    'metric': 'نسبت بدهی به دارایی',
                    'value': float(debt_to_assets),
                    'threshold': 0.7,
                    'deviation': 'بالا'
                })
            elif debt_to_assets > 0.5:
                alerts.append({
                    'type': 'اهرمی',
                    'severity': 'بالا',
                    'title': 'اهرم مالی بالا',
                    'description': f'نسبت بدهی به دارایی ({debt_to_assets:.2%}) بین ۵۰-۷۰٪ است، نیاز به کاهش بدهی',
                    'metric': 'نسبت بدهی به دارایی',
                    'value': float(debt_to_assets),
                    'threshold': 0.5,
                    'deviation': 'بالا'
                })
        
        # تحلیل حاشیه سود خالص
        net_margin = ratios.get('net_margin')
        if net_margin:
            if net_margin < 0:
                alerts.append({
                    'type': 'سودآوری',
                    'severity': 'بسیار بالا',
                    'title': 'سودآوری منفی',
                    'description': f'حاشیه سود خالص ({net_margin:.2%}) منفی است، شرکت در حال زیان‌دهی',
                    'metric': 'حاشیه سود خالص',
                    'value': float(net_margin),
                    'threshold': 0.0,
                    'deviation': 'پایین'
                })
            elif net_margin < 0.05:
                alerts.append({
                    'type': 'سودآوری',
                    'severity': 'متوسط',
                    'title': 'سودآوری پایین',
                    'description': f'حاشیه سود خالص ({net_margin:.2%}) کمتر از ۵٪ است، نیاز به بهبود کارایی',
                    'metric': 'حاشیه سود خالص',
                    'value': float(net_margin),
                    'threshold': 0.05,
                    'deviation': 'پایین'
                })
        
        return alerts
    
    def _analyze_trends(self, company_id: int, period_id: int) -> List[Dict[str, Any]]:
        """تحلیل روندهای مالی"""
        
        alerts = []
        
        try:
            # دریافت داده‌های تاریخی
            historical_data = FinancialData.objects.filter(
                company_id=company_id,
                period_id__lt=period_id
            ).order_by('-period_id')[:4]  # ۴ دوره قبلی
            
            if len(historical_data) < 2:
                return alerts
            
            # تحلیل روند درآمد
            revenue_trend = self._analyze_revenue_trend(historical_data)
            if revenue_trend:
                alerts.append(revenue_trend)
            
            # تحلیل روند سود
            profit_trend = self._analyze_profit_trend(historical_data)
            if profit_trend:
                alerts.append(profit_trend)
            
            # تحلیل روند نقدینگی
            liquidity_trend = self._analyze_liquidity_trend(historical_data)
            if liquidity_trend:
                alerts.append(liquidity_trend)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل روندها: {str(e)}")
            return []
    
    def _analyze_revenue_trend(self, historical_data) -> Optional[Dict[str, Any]]:
        """تحلیل روند درآمد"""
        
        try:
            revenues = [data.revenue for data in historical_data if data.revenue]
            
            if len(revenues) < 2:
                return None
            
            # محاسبه رشد درآمد
            current_revenue = revenues[0]
            previous_revenue = revenues[1]
            
            if previous_revenue == 0:
                return None
            
            growth_rate = (current_revenue - previous_revenue) / previous_revenue
            
            if growth_rate < -0.2:  # کاهش بیش از ۲۰٪
                return {
                    'type': 'روند درآمد',
                    'severity': 'بالا',
                    'title': 'کاهش شدید درآمد',
                    'description': f'درآمد نسبت به دوره قبل {growth_rate:.1%} کاهش یافته است',
                    'metric': 'رشد درآمد',
                    'value': float(growth_rate),
                    'threshold': -0.2,
                    'deviation': 'پایین'
                }
            elif growth_rate < -0.1:  # کاهش ۱۰-۲۰٪
                return {
                    'type': 'روند درآمد',
                    'severity': 'متوسط',
                    'title': 'کاهش درآمد',
                    'description': f'درآمد نسبت به دوره قبل {growth_rate:.1%} کاهش یافته است',
                    'metric': 'رشد درآمد',
                    'value': float(growth_rate),
                    'threshold': -0.1,
                    'deviation': 'پایین'
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل روند درآمد: {str(e)}")
            return None
    
    def _analyze_profit_trend(self, historical_data) -> Optional[Dict[str, Any]]:
        """تحلیل روند سود"""
        
        try:
            profits = [data.net_income for data in historical_data if data.net_income is not None]
            
            if len(profits) < 2:
                return None
            
            # تحلیل تداوم زیان
            loss_periods = sum(1 for profit in profits if profit < 0)
            
            if loss_periods >= 2:
                return {
                    'type': 'روند سود',
                    'severity': 'بسیار بالا',
                    'title': 'تداوم زیان‌دهی',
                    'description': f'شرکت در {loss_periods} دوره متوالی زیان‌ده بوده است',
                    'metric': 'دوره‌های زیان',
                    'value': loss_periods,
                    'threshold': 2,
                    'deviation': 'بالا'
                }
            
            # تحلیل کاهش سود
            current_profit = profits[0]
            previous_profit = profits[1]
            
            if previous_profit > 0 and current_profit > 0:
                profit_decline = (previous_profit - current_profit) / previous_profit
                
                if profit_decline > 0.3:  # کاهش بیش از ۳۰٪
                    return {
                        'type': 'روند سود',
                        'severity': 'بالا',
                        'title': 'کاهش شدید سود',
                        'description': f'سود خالص نسبت به دوره قبل {profit_decline:.1%} کاهش یافته است',
                        'metric': 'کاهش سود',
                        'value': float(profit_decline),
                        'threshold': 0.3,
                        'deviation': 'بالا'
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل روند سود: {str(e)}")
            return None
    
    def _analyze_liquidity_trend(self, historical_data) -> Optional[Dict[str, Any]]:
        """تحلیل روند نقدینگی"""
        
        try:
            current_ratios = []
            
            for data in historical_data:
                if data.current_assets and data.current_liabilities and data.current_liabilities > 0:
                    current_ratio = data.current_assets / data.current_liabilities
                    current_ratios.append(current_ratio)
            
            if len(current_ratios) < 2:
                return None
            
            # تحلیل کاهش نقدینگی
            current_ratio = current_ratios[0]
            previous_ratio = current_ratios[1]
            
            if current_ratio < previous_ratio * 0.8:  # کاهش بیش از ۲۰٪
                return {
                    'type': 'روند نقدینگی',
                    'severity': 'بالا',
                    'title': 'کاهش شدید نقدینگی',
                    'description': f'نسبت جاری نسبت به دوره قبل {((current_ratio - previous_ratio) / previous_ratio):.1%} کاهش یافته است',
                    'metric': 'کاهش نسبت جاری',
                    'value': float(current_ratio),
                    'threshold': float(previous_ratio * 0.8),
                    'deviation': 'پایین'
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل روند نقدینگی: {str(e)}")
            return None
    
    def _detect_anomalies(self, financial_data: Dict) -> List[Dict[str, Any]]:
        """شناسایی ناهنجاری‌های مالی"""
        
        alerts = []
        
        try:
            balance_sheet = financial_data.get('balance_sheet', {})
            income_statement = financial_data.get('income_statement', {})
            cash_flow = financial_data.get('cash_flow', {})
            
            # شناسایی ناهنجاری در دارایی‌ها
            if balance_sheet.get('total_assets', 0) <= 0:
                alerts.append({
                    'type': 'ناهنجاری',
                    'severity': 'بسیار بالا',
                    'title': 'دارایی‌های صفر یا منفی',
                    'description': 'کل دارایی‌ها صفر یا منفی است، احتمال خطا در داده‌ها',
                    'metric': 'کل دارایی‌ها',
                    'value': float(balance_sheet.get('total_assets', 0)),
                    'threshold': 0.0,
                    'deviation': 'پایین'
                })
            
            # شناسایی ناهنجاری در جریان نقدی عملیاتی
            operating_cash_flow = cash_flow.get('operating_cash_flow', 0)
            net_income = income_statement.get('net_income', 0)
            
            if operating_cash_flow < 0 and net_income > 0:
                alerts.append({
                    'type': 'ناهنجاری',
                    'severity': 'بالا',
                    'title': 'جریان نقدی عملیاتی منفی با سود مثبت',
                    'description': 'شرکت سودآور است اما جریان نقدی عملیاتی منفی دارد، احتمال مشکل در مدیریت نقدینگی',
                    'metric': 'جریان نقدی عملیاتی',
                    'value': float(operating_cash_flow),
                    'threshold': 0.0,
                    'deviation': 'پایین'
                })
            
            # شناسایی ناهنجاری در نسبت‌ها
            ratios = financial_data.get('ratios', {})
            current_ratio = ratios.get('current_ratio')
            
            if current_ratio and current_ratio > 10:
                alerts.append({
                    'type': 'ناهنجاری',
                    'severity': 'متوسط',
                    'title': 'نسبت جاری بسیار بالا',
                    'description': f'نسبت جاری ({current_ratio:.2f}) بسیار بالا است، احتمال عدم استفاده بهینه از دارایی‌ها',
                    'metric': 'نسبت جاری',
                    'value': float(current_ratio),
                    'threshold': 10.0,
                    'deviation': 'بالا'
                })
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"خطا در شناسایی ناهنجاری‌ها: {str(e)}")
            return []
    
    def _assess_financial_risks(self, financial_data: Dict) -> List[Dict[str, Any]]:
        """ارزیابی ریسک‌های مالی"""
        
        alerts = []
        
        try:
            balance_sheet = financial_data.get('balance_sheet', {})
            income_statement = financial_data.get('income_statement', {})
            ratios = financial_data.get('ratios', {})
            
            # ارزیابی ریسک ورشکستگی
            equity = balance_sheet.get('equity', 0)
            total_liabilities = balance_sheet.get('total_liabilities', 0)
            
            if equity < 0 and total_liabilities > 0:
                alerts.append({
                    'type': 'ریسک',
                    'severity': 'بسیار بالا',
                    'title': 'ریسک ورشکستگی',
                    'description': 'حقوق صاحبان سهام منفی است، شرکت در معرض ورشکستگی قرار دارد',
                    'metric': 'حقوق صاحبان سهام',
                    'value': float(equity),
                    'threshold': 0.0,
                    'deviation': 'پایین'
                })
            
            # ارزیابی ریسک نقدینگی
            current_ratio = ratios.get('current_ratio')
            if current_ratio and current_ratio < 0.5:
                alerts.append({
                    'type': 'ریسک',
                    'severity': 'بسیار بالا',
                    'title': 'ریسک نقدینگی بحرانی',
                    'description': f'نسبت جاری ({current_ratio:.2f}) بسیار پایین است، شرکت ممکن است نتواند بدهی‌های کوتاه‌مدت را پرداخت کند',
                    'metric': 'نسبت جاری',
                    'value': float(current_ratio),
                    'threshold': 0.5,
                    'deviation': 'پایین'
                })
            
            # ارزیابی ریسک سودآوری
            net_income = income_statement.get('net_income', 0)
            revenue = income_statement.get('revenue', 0)
            
            if net_income < 0 and revenue > 0:
                alerts.append({
                    'type': 'ریسک',
                    'severity': 'بالا',
                    'title': 'ریسک سودآوری',
                    'description': 'شرکت با وجود درآمد مثبت، زیان‌ده است، احتمال مشکل در کنترل هزینه‌ها',
                    'metric': 'سود خالص',
                    'value': float(net_income),
                    'threshold': 0.0,
                    'deviation': 'پایین'
                })
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"خطا در ارزیابی ریسک‌ها: {str(e)}")
            return []
    
    def _prioritize_alerts(self, alerts: List[Dict]) -> List[Dict[str, Any]]:
        """اولویت‌بندی هشدارها"""
        
        if not alerts:
            return []
        
        # تعیین امتیاز اولویت برای هر هشدار
        severity_scores = {
            'بسیار بالا': 100,
            'بالا': 75,
            'متوسط': 50,
            'پایین': 25
        }
        
        for alert in alerts:
            severity = alert.get('severity', 'پایین')
            alert['priority_score'] = severity_scores.get(severity, 25)
            
            # اضافه کردن امتیاز بر اساس نوع هشدار
            alert_type = alert.get('type', '')
            if alert_type in ['ریسک', 'نقدینگی']:
                alert['priority_score'] += 10
            elif alert_type == 'سودآوری':
                alert['priority_score'] += 5
        
        # مرتب‌سازی بر اساس امتیاز اولویت
        prioritized_alerts = sorted(alerts, key=lambda x: x['priority_score'], reverse=True)
        
        return prioritized_alerts
    
    def _generate_alert_report(self, alerts: List[Dict], company_id: int, period_id: int) -> Dict[str, Any]:
        """تولید گزارش هشدار"""
        
        total_alerts = len(alerts)
        high_priority_count = len([a for a in alerts if a['severity'] in ['بسیار بالا', 'بالا']])
        
        # گروه‌بندی هشدارها بر اساس نوع
        alert_types = {}
        for alert in alerts:
            alert_type = alert.get('type', 'سایر')
            if alert_type not in alert_types:
                alert_types[alert_type] = []
            alert_types[alert_type].append(alert)
        
        # ارزیابی کلی وضعیت مالی
        overall_status = self._assess_overall_financial_status(alerts)
        
        return {
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'company_id': company_id,
            'period_id': period_id,
            'total_alerts': total_alerts,
            'high_priority_alerts': high_priority_count,
            'overall_status': overall_status,
            'alert_summary': {
                'by_type': {alert_type: len(alerts) for alert_type, alerts in alert_types.items()},
                'by_severity': {
                    'بسیار بالا': len([a for a in alerts if a['severity'] == 'بسیار بالا']),
                    'بالا': len([a for a in alerts if a['severity'] == 'بالا']),
                    'متوسط': len([a for a in alerts if a['severity'] == 'متوسط']),
                    'پایین': len([a for a in alerts if a['severity'] == 'پایین'])
                }
            },
            'key_findings': self._extract_key_findings(alerts),
            'immediate_actions': self._identify_immediate_actions(alerts)
        }
    
    def _assess_overall_financial_status(self, alerts: List[Dict]) -> str:
        """ارزیابی کلی وضعیت مالی"""
        
        if not alerts:
            return 'سالم'
        
        high_severity_count = len([a for a in alerts if a['severity'] in ['بسیار بالا', 'بالا']])
        total_alerts = len(alerts)
        
        if high_severity_count >= 3:
            return 'بحرانی'
        elif high_severity_count >= 1:
            return 'نیاز به توجه'
        elif total_alerts >= 5:
            return 'نیاز به نظارت'
        else:
            return 'سالم'
    
    def _extract_key_findings(self, alerts: List[Dict]) -> List[str]:
        """استخراج یافته‌های کلیدی"""
        
        findings = []
        
        # شناسایی مهم‌ترین هشدارها
        high_severity_alerts = [a for a in alerts if a['severity'] in ['بسیار بالا', 'بالا']]
        
        for alert in high_severity_alerts[:3]:  # فقط ۳ هشدار اول
            findings.append(f"{alert['title']}: {alert['description']}")
        
        # تحلیل کلی
        if len(high_severity_alerts) >= 2:
            findings.append("چندین مشکل مالی جدی شناسایی شده است")
        
        risk_alerts = [a for a in alerts if a['type'] == 'ریسک']
        if len(risk_alerts) >= 2:
            findings.append("ریسک‌های مالی متعددی شناسایی شده است")
        
        return findings
    
    def _identify_immediate_actions(self, alerts: List[Dict]) -> List[str]:
        """شناسایی اقدامات فوری"""
        
        actions = []
        
        # شناسایی اقدامات بر اساس هشدارهای با اولویت بالا
        high_priority_alerts = [a for a in alerts if a['severity'] in ['بسیار بالا', 'بالا']]
        
        for alert in high_priority_alerts:
            alert_type = alert.get('type', '')
            
            if alert_type == 'نقدینگی':
                actions.append('بررسی فوری وضعیت نقدینگی و برنامه‌ریزی برای تأمین مالی')
            
            if alert_type == 'ریسک':
                actions.append('بررسی جامع ریسک‌های مالی و تدوین برنامه کاهش ریسک')
            
            if alert_type == 'سودآوری':
                actions.append('تحلیل هزینه‌ها و شناسایی راه‌های بهبود سودآوری')
        
        # اقدامات عمومی
        if high_priority_alerts:
            actions.append('بررسی فوری توسط مدیریت ارشد مالی')
            actions.append('تدوین برنامه اقدام اضطراری')
        
        return list(set(actions))  # حذف موارد تکراری
    
    def _generate_recommendations(self, alerts: List[Dict]) -> List[Dict[str, Any]]:
        """تولید توصیه‌ها"""
        
        recommendations = []
        
        # تحلیل هشدارها برای تولید توصیه‌های هدفمند
        for alert in alerts:
            alert_type = alert.get('type', '')
            severity = alert.get('severity', '')
            
            if alert_type == 'نقدینگی' and severity in ['بسیار بالا', 'بالا']:
                recommendations.append({
                    'category': 'نقدینگی',
                    'priority': 'فوری',
                    'recommendation': 'بهبود مدیریت نقدینگی و برنامه‌ریزی برای تأمین مالی',
                    'expected_impact': 'کاهش ریسک نقدینگی و بهبود توان پرداخت بدهی‌ها',
                    'timeline': 'فوری'
                })
            
            if alert_type == 'اهرمی' and severity in ['بسیار بالا', 'بالا']:
                recommendations.append({
                    'category': 'ساختار سرمایه',
                    'priority': 'بالا',
                    'recommendation': 'بازنگری ساختار سرمایه و کاهش بدهی‌ها',
                    'expected_impact': 'کاهش ریسک مالی و بهبود ثبات مالی',
                    'timeline': '۳-۶ ماه'
                })
            
            if alert_type == 'سودآوری' and severity in ['بسیار بالا', 'بالا']:
                recommendations.append({
                    'category': 'سودآوری',
                    'priority': 'بالا',
                    'recommendation': 'تحلیل هزینه‌ها و شناسایی راه‌های بهبود کارایی',
                    'expected_impact': 'افزایش سودآوری و بهبود عملکرد مالی',
                    'timeline': '۱-۳ ماه'
                })
        
        # حذف توصیه‌های تکراری
        unique_recommendations = []
        seen_recommendations = set()
        
        for rec in recommendations:
            rec_key = rec['recommendation']
            if rec_key not in seen_recommendations:
                unique_recommendations.append(rec)
                seen_recommendations.add(rec_key)
        
        return unique_recommendations
    
    def _save_alert_history(self, alerts: List[Dict], company_id: int, period_id: int) -> None:
        """ذخیره تاریخچه هشدار"""
        
        history_entry = {
            'timestamp': datetime.now(),
            'company_id': company_id,
            'period_id': period_id,
            'alerts': alerts,
            'total_alerts': len(alerts),
            'high_priority_count': len([a for a in alerts if a['severity'] in ['بسیار بالا', 'بالا']])
        }
        
        self.alert_history.append(history_entry)
        
        # محدود کردن تاریخچه به ۵۰ ورودی
        if len(self.alert_history) > 50:
            self.alert_history = self.alert_history[-50:]
    
    def get_alert_history(self, company_id: Optional[int] = None, days_back: int = 90) -> List[Dict[str, Any]]:
        """دریافت تاریخچه هشدار"""
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        filtered_history = [
            entry for entry in self.alert_history
            if entry['timestamp'] >= cutoff_date
        ]
        
        if company_id:
            filtered_history = [
                entry for entry in filtered_history
                if entry['company_id'] == company_id
            ]
        
        return filtered_history


# ابزار LangChain برای سیستم هشدار مالی
class FinancialAlertTool:
    """ابزار سیستم هشدار مالی برای LangChain"""
    
    name = "financial_alert_system"
    description = "تحلیل داده‌های مالی و شناسایی هشدارها و ریسک‌ها"
    
    def __init__(self):
        self.alert_system = FinancialAlertSystem()
    
    def analyze_financial_data(self, company_id: int, period_id: int) -> Dict:
        """تحلیل داده‌های مالی و شناسایی هشدارها"""
        try:
            result = self.alert_system.analyze_financial_data(company_id, period_id)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_alert_history(self, company_id: Optional[int] = None, days_back: int = 90) -> Dict:
        """دریافت تاریخچه هشدار"""
        try:
            result = self.alert_system.get_alert_history(company_id, days_back)
            return {
                'success': True,
                'history': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
