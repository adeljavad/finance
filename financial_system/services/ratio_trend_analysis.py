# financial_system/services/ratio_trend_analysis.py
"""
تسک ۶۵: پیاده‌سازی تحلیل روند نسبت‌ها
این سرویس برای تحلیل روند تغییرات نسبت‌های مالی در دوره‌های مختلف طراحی شده است.
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from users.models import Company, FinancialPeriod, FinancialFile, Document


class RatioTrendAnalyzer:
    """تحلیل‌گر روند نسبت‌های مالی"""
    
    def __init__(self, company: Company):
        self.company = company
    
    def analyze_ratio_trends(self, periods: List[FinancialPeriod]) -> Dict[str, Any]:
        """تحلیل روند نسبت‌های مالی در دوره‌های مختلف"""
        
        # جمع‌آوری داده‌های تاریخی
        historical_data = self._collect_historical_data(periods)
        
        # تحلیل روند برای هر گروه از نسبت‌ها
        trend_analysis = {
            'liquidity_trends': self._analyze_liquidity_trends(historical_data),
            'leverage_trends': self._analyze_leverage_trends(historical_data),
            'profitability_trends': self._analyze_profitability_trends(historical_data),
            'activity_trends': self._analyze_activity_trends(historical_data),
            'overall_trends': self._analyze_overall_trends(historical_data)
        }
        
        # شناسایی الگوها و پیش‌بینی
        patterns = self._identify_patterns(trend_analysis)
        forecasts = self._generate_forecasts(trend_analysis)
        
        return {
            'company': self.company.name,
            'periods': [period.name for period in periods],
            'historical_data': historical_data,
            'trend_analysis': trend_analysis,
            'patterns': patterns,
            'forecasts': forecasts,
            'recommendations': self._generate_trend_recommendations(trend_analysis, patterns)
        }
    
    def _collect_historical_data(self, periods: List[FinancialPeriod]) -> Dict[str, Any]:
        """جمع‌آوری داده‌های تاریخی برای دوره‌های مختلف"""
        
        historical_data = {}
        
        for period in periods:
            # این بخش باید با مدل‌های واقعی یکپارچه شود
            # فعلاً از داده‌های نمونه استفاده می‌کنیم
            
            historical_data[period.name] = {
                'period': period.name,
                'date': period.start_date if period.start_date else datetime.now(),
                'ratios': {
                    # نسبت‌های نقدینگی
                    'current_ratio': Decimal('1.8') + Decimal(str(0.1 * periods.index(period))),
                    'quick_ratio': Decimal('1.2') + Decimal(str(0.05 * periods.index(period))),
                    'cash_ratio': Decimal('0.3') + Decimal(str(0.02 * periods.index(period))),
                    
                    # نسبت‌های اهرمی
                    'debt_ratio': Decimal('0.6') - Decimal(str(0.02 * periods.index(period))),
                    'debt_to_equity': Decimal('1.5') - Decimal(str(0.05 * periods.index(period))),
                    'interest_coverage': Decimal('4.0') + Decimal(str(0.3 * periods.index(period))),
                    
                    # نسبت‌های سودآوری
                    'gross_profit_margin': Decimal('0.35') + Decimal(str(0.01 * periods.index(period))),
                    'operating_profit_margin': Decimal('0.18') + Decimal(str(0.005 * periods.index(period))),
                    'net_profit_margin': Decimal('0.12') + Decimal(str(0.003 * periods.index(period))),
                    'return_on_assets': Decimal('0.08') + Decimal(str(0.002 * periods.index(period))),
                    'return_on_equity': Decimal('0.15') + Decimal(str(0.004 * periods.index(period))),
                    
                    # نسبت‌های فعالیت
                    'inventory_turnover': Decimal('6.0') + Decimal(str(0.2 * periods.index(period))),
                    'receivables_turnover': Decimal('8.0') + Decimal(str(0.3 * periods.index(period))),
                    'asset_turnover': Decimal('0.7') + Decimal(str(0.05 * periods.index(period))),
                    'cash_conversion_cycle': Decimal('50.0') - Decimal(str(2.0 * periods.index(period)))
                },
                'financial_data': {
                    'revenue': Decimal('8000000000') * Decimal(str(1.1 ** periods.index(period))),
                    'net_income': Decimal('900000000') * Decimal(str(1.08 ** periods.index(period))),
                    'total_assets': Decimal('10000000000') * Decimal(str(1.05 ** periods.index(period))),
                    'total_equity': Decimal('4000000000') * Decimal(str(1.06 ** periods.index(period)))
                }
            }
        
        return historical_data
    
    def _analyze_liquidity_trends(self, historical_data: Dict) -> Dict[str, Any]:
        """تحلیل روند نسبت‌های نقدینگی"""
        
        trends = {}
        periods = list(historical_data.keys())
        
        # تحلیل روند برای هر نسبت نقدینگی
        liquidity_ratios = ['current_ratio', 'quick_ratio', 'cash_ratio']
        
        for ratio_name in liquidity_ratios:
            values = [historical_data[period]['ratios'][ratio_name] for period in periods]
            trend = self._calculate_trend(values)
            
            trends[ratio_name] = {
                'values': [float(value) for value in values],
                'trend': trend['direction'],
                'slope': float(trend['slope']),
                'r_squared': float(trend['r_squared']),
                'interpretation': self._interpret_liquidity_trend(ratio_name, trend)
            }
        
        # تحلیل کلی روند نقدینگی
        overall_trend = self._assess_overall_liquidity_trend(trends)
        
        return {
            'individual_trends': trends,
            'overall_trend': overall_trend,
            'periods': periods
        }
    
    def _analyze_leverage_trends(self, historical_data: Dict) -> Dict[str, Any]:
        """تحلیل روند نسبت‌های اهرمی"""
        
        trends = {}
        periods = list(historical_data.keys())
        
        # تحلیل روند برای هر نسبت اهرمی
        leverage_ratios = ['debt_ratio', 'debt_to_equity', 'interest_coverage']
        
        for ratio_name in leverage_ratios:
            values = [historical_data[period]['ratios'][ratio_name] for period in periods]
            trend = self._calculate_trend(values)
            
            trends[ratio_name] = {
                'values': [float(value) for value in values],
                'trend': trend['direction'],
                'slope': float(trend['slope']),
                'r_squared': float(trend['r_squared']),
                'interpretation': self._interpret_leverage_trend(ratio_name, trend)
            }
        
        # تحلیل کلی روند اهرمی
        overall_trend = self._assess_overall_leverage_trend(trends)
        
        return {
            'individual_trends': trends,
            'overall_trend': overall_trend,
            'periods': periods
        }
    
    def _analyze_profitability_trends(self, historical_data: Dict) -> Dict[str, Any]:
        """تحلیل روند نسبت‌های سودآوری"""
        
        trends = {}
        periods = list(historical_data.keys())
        
        # تحلیل روند برای هر نسبت سودآوری
        profitability_ratios = [
            'gross_profit_margin', 'operating_profit_margin', 'net_profit_margin',
            'return_on_assets', 'return_on_equity'
        ]
        
        for ratio_name in profitability_ratios:
            values = [historical_data[period]['ratios'][ratio_name] for period in periods]
            trend = self._calculate_trend(values)
            
            trends[ratio_name] = {
                'values': [float(value) for value in values],
                'trend': trend['direction'],
                'slope': float(trend['slope']),
                'r_squared': float(trend['r_squared']),
                'interpretation': self._interpret_profitability_trend(ratio_name, trend)
            }
        
        # تحلیل کلی روند سودآوری
        overall_trend = self._assess_overall_profitability_trend(trends)
        
        return {
            'individual_trends': trends,
            'overall_trend': overall_trend,
            'periods': periods
        }
    
    def _analyze_activity_trends(self, historical_data: Dict) -> Dict[str, Any]:
        """تحلیل روند نسبت‌های فعالیت"""
        
        trends = {}
        periods = list(historical_data.keys())
        
        # تحلیل روند برای هر نسبت فعالیت
        activity_ratios = [
            'inventory_turnover', 'receivables_turnover', 
            'asset_turnover', 'cash_conversion_cycle'
        ]
        
        for ratio_name in activity_ratios:
            values = [historical_data[period]['ratios'][ratio_name] for period in periods]
            trend = self._calculate_trend(values)
            
            trends[ratio_name] = {
                'values': [float(value) for value in values],
                'trend': trend['direction'],
                'slope': float(trend['slope']),
                'r_squared': float(trend['r_squared']),
                'interpretation': self._interpret_activity_trend(ratio_name, trend)
            }
        
        # تحلیل کلی روند فعالیت
        overall_trend = self._assess_overall_activity_trend(trends)
        
        return {
            'individual_trends': trends,
            'overall_trend': overall_trend,
            'periods': periods
        }
    
    def _analyze_overall_trends(self, historical_data: Dict) -> Dict[str, Any]:
        """تحلیل روند کلی مالی"""
        
        periods = list(historical_data.keys())
        
        # محاسبه شاخص‌های کلیدی
        key_metrics = {
            'revenue_growth': self._calculate_growth_rate(
                [historical_data[period]['financial_data']['revenue'] for period in periods]
            ),
            'net_income_growth': self._calculate_growth_rate(
                [historical_data[period]['financial_data']['net_income'] for period in periods]
            ),
            'asset_growth': self._calculate_growth_rate(
                [historical_data[period]['financial_data']['total_assets'] for period in periods]
            ),
            'equity_growth': self._calculate_growth_rate(
                [historical_data[period]['financial_data']['total_equity'] for period in periods]
            )
        }
        
        # ارزیابی کلی روند مالی
        overall_assessment = self._assess_overall_financial_trend(key_metrics)
        
        return {
            'key_metrics': key_metrics,
            'overall_assessment': overall_assessment,
            'periods': periods
        }
    
    def _calculate_trend(self, values: List[Decimal]) -> Dict[str, Any]:
        """محاسبه روند خطی برای مجموعه‌ای از مقادیر"""
        
        if len(values) < 2:
            return {
                'direction': 'ثابت',
                'slope': Decimal('0'),
                'r_squared': Decimal('0')
            }
        
        # محاسبه شیب خط روند
        n = len(values)
        x_values = list(range(n))
        y_values = [float(value) for value in values]
        
        # محاسبه میانگین‌ها
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        
        # محاسبه شیب
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            slope = Decimal('0')
        else:
            slope = Decimal(str(numerator / denominator))
        
        # تعیین جهت روند
        if slope > Decimal('0.01'):
            direction = 'صعودی'
        elif slope < Decimal('-0.01'):
            direction = 'نزولی'
        else:
            direction = 'ثابت'
        
        # محاسبه ضریب تعیین (R-squared)
        if denominator == 0:
            r_squared = Decimal('0')
        else:
            y_pred = [y_mean + slope * (x - x_mean) for x in x_values]
            ss_res = sum((y - y_pred[i]) ** 2 for i, y in enumerate(y_values))
            ss_tot = sum((y - y_mean) ** 2 for y in y_values)
            
            if ss_tot == 0:
                r_squared = Decimal('1')
            else:
                r_squared = Decimal('1') - Decimal(str(ss_res / ss_tot))
        
        return {
            'direction': direction,
            'slope': slope,
            'r_squared': r_squared
        }
    
    def _calculate_growth_rate(self, values: List[Decimal]) -> Dict[str, Any]:
        """محاسبه نرخ رشد برای مجموعه‌ای از مقادیر"""
        
        if len(values) < 2:
            return {
                'average_growth': Decimal('0'),
                'volatility': Decimal('0'),
                'trend': 'ثابت'
            }
        
        # محاسبه نرخ رشد دوره‌ای
        growth_rates = []
        for i in range(1, len(values)):
            if values[i-1] != Decimal('0'):
                growth_rate = (values[i] - values[i-1]) / values[i-1]
                growth_rates.append(growth_rate)
        
        if not growth_rates:
            return {
                'average_growth': Decimal('0'),
                'volatility': Decimal('0'),
                'trend': 'ثابت'
            }
        
        # محاسبه میانگین و نوسان
        avg_growth = sum(growth_rates) / len(growth_rates)
        
        # محاسبه انحراف معیار
        if len(growth_rates) > 1:
            variance = sum((rate - avg_growth) ** 2 for rate in growth_rates) / (len(growth_rates) - 1)
            volatility = variance.sqrt()
        else:
            volatility = Decimal('0')
        
        # تعیین روند
        if avg_growth > Decimal('0.05'):
            trend = 'رشد قوی'
        elif avg_growth > Decimal('0.02'):
            trend = 'رشد متوسط'
        elif avg_growth > Decimal('0'):
            trend = 'رشد ضعیف'
        elif avg_growth < Decimal('-0.05'):
            trend = 'کاهش شدید'
        elif avg_growth < Decimal('-0.02'):
            trend = 'کاهش متوسط'
        else:
            trend = 'ثابت'
        
        return {
            'average_growth': float(avg_growth),
            'volatility': float(volatility),
            'trend': trend
        }
    
    def _interpret_liquidity_trend(self, ratio_name: str, trend: Dict) -> str:
        """تفسیر روند نسبت نقدینگی"""
        
        direction = trend['direction']
        
        interpretations = {
            'current_ratio': {
                'صعودی': 'بهبود تدریجی توانایی پرداخت بدهی‌های کوتاه‌مدت',
                'نزولی': 'کاهش تدریجی توانایی پرداخت بدهی‌های کوتاه‌مدت',
                'ثابت': 'پایداری در توانایی پرداخت بدهی‌های کوتاه‌مدت'
            },
            'quick_ratio': {
                'صعودی': 'بهبود تدریجی نقدینگی سریع',
                'نزولی': 'کاهش تدریجی نقدینگی سریع',
                'ثابت': 'پایداری در نقدینگی سریع'
            },
            'cash_ratio': {
                'صعودی': 'افزایش تدریجی نقدینگی فوری',
                'نزولی': 'کاهش تدریجی نقدینگی فوری',
                'ثابت': 'پایداری در نقدینگی فوری'
            }
        }
        
        return interpretations.get(ratio_name, {}).get(direction, 'روند قابل تفسیر نیست')
    
    def _interpret_leverage_trend(self, ratio_name: str, trend: Dict) -> str:
        """تفسیر روند نسبت اهرمی"""
        
        direction = trend['direction']
        
        interpretations = {
            'debt_ratio': {
                'صعودی': 'افزایش تدریجی وابستگی به بدهی',
                'نزولی': 'کاهش تدریجی وابستگی به بدهی',
                'ثابت': 'پایداری در ساختار سرمایه'
            },
            'debt_to_equity': {
                'صعودی': 'افزایش تدریجی اهرم مالی',
                'نزولی': 'کاهش تدریجی اهرم مالی',
                'ثابت': 'پایداری در اهرم مالی'
            },
            'interest_coverage': {
                'صعودی': 'بهبود تدریجی توانایی پرداخت بهره',
                'نزولی': 'کاهش تدریجی توانایی پرداخت بهره',
                'ثابت': 'پایداری در توانایی پرداخت بهره'
            }
        }
        
        return interpretations.get(ratio_name, {}).get(direction, 'روند قابل تفسیر نیست')
    
    def _interpret_profitability_trend(self, ratio_name: str, trend: Dict) -> str:
        """تفسیر روند نسبت سودآوری"""
        
        direction = trend['direction']
        
        interpretations = {
            'gross_profit_margin': {
                'صعودی': 'بهبود تدریجی حاشیه سود ناخالص',
                'نزولی': 'کاهش تدریجی حاشیه سود ناخالص',
                'ثابت': 'پایداری در حاشیه سود ناخالص'
            },
            'operating_profit_margin': {
                'صعودی': 'بهبود تدریجی کارایی عملیاتی',
                'نزولی': 'کاهش تدریجی کارایی عملیاتی',
                'ثابت': 'پایداری در کارایی عملیاتی'
            },
            'net_profit_margin': {
                'صعودی': 'بهبود تدریجی سودآوری کلی',
                'نزولی': 'کاهش تدریجی سودآوری کلی',
                'ثابت': 'پایداری در سودآوری کلی'
            },
            'return_on_assets': {
                'صعودی': 'بهبود تدریجی استفاده از دارایی‌ها',
                'نزولی': 'کاهش تدریجی استفاده از دارایی‌ها',
                'ثابت': 'پایداری در استفاده از دارایی‌ها'
            },
            'return_on_equity': {
                'صعودی': 'بهبود تدریجی بازده سرمایه',
                'نزولی': 'کاهش تدریجی بازده سرمایه',
                'ثابت': 'پایداری در بازده سرمایه'
            }
        }
        
        return interpretations.get(ratio_name, {}).get(direction, 'روند قابل تفسیر نیست')
    
    def _interpret_activity_trend(self, ratio_name: str, trend: Dict) -> str:
        """تفسیر روند نسبت فعالیت"""
        
        direction = trend['direction']
        
        interpretations = {
            'inventory_turnover': {
                'صعودی': 'بهبود تدریجی مدیریت موجودی',
                'نزولی': 'کاهش تدریجی مدیریت موجودی',
                'ثابت': 'پایداری در مدیریت موجودی'
            },
            'receivables_turnover': {
                'صعودی': 'بهبود تدریجی وصول مطالبات',
                'نزولی': 'کاهش تدریجی وصول مطالبات',
                'ثابت': 'پایداری در وصول مطالبات'
            },
            'asset_turnover': {
                'صعودی': 'بهبود تدریجی استفاده از دارایی‌ها',
                'نزولی': 'کاهش تدریجی استفاده از دارایی‌ها',
                'ثابت': 'پایداری در استفاده از دارایی‌ها'
            },
            'cash_conversion_cycle': {
                'صعودی': 'افزایش تدریجی چرخه تبدیل نقدی',
                'نزولی': 'کاهش تدریجی چرخه تبدیل نقدی',
                'ثابت': 'پایداری در چرخه تبدیل نقدی'
            }
        }
        
        return interpretations.get(ratio_name, {}).get(direction, 'روند قابل تفسیر نیست')
    
    def _assess_overall_liquidity_trend(self, trends: Dict) -> Dict[str, Any]:
        """ارزیابی کلی روند نقدینگی"""
        
        positive_trends = sum(1 for trend in trends.values() if trend['trend'] == 'صعودی')
        negative_trends = sum(1 for trend in trends.values() if trend['trend'] == 'نزولی')
        
        if positive_trends >= 2:
            level = 'بهبود'
            interpretation = 'روند کلی نقدینگی در حال بهبود است'
        elif negative_trends >= 2:
            level = 'کاهش'
            interpretation = 'روند کلی نقدینگی در حال کاهش است'
        else:
            level = 'پایدار'
            interpretation = 'روند کلی نقدینگی پایدار است'
        
        return {
            'level': level,
            'interpretation': interpretation,
            'positive_trends': positive_trends,
            'negative_trends': negative_trends,
            'stable_trends': len(trends) - positive_trends - negative_trends
        }
    
    def _assess_overall_leverage_trend(self, trends: Dict) -> Dict[str, Any]:
        """ارزیابی کلی روند اهرمی"""
        
        # برای نسبت‌های اهرمی، روند نزولی برای debt ratios و صعودی برای coverage ratios مطلوب است
        favorable_trends = 0
        unfavorable_trends = 0
        
        for ratio_name, trend in trends.items():
            if ratio_name in ['debt_ratio', 'debt_to_equity']:
                # برای نسبت‌های بدهی، روند نزولی مطلوب است
                if trend['trend'] == 'نزولی':
                    favorable_trends += 1
                elif trend['trend'] == 'صعودی':
                    unfavorable_trends += 1
            elif ratio_name == 'interest_coverage':
                # برای نسبت پوشش بهره، روند صعودی مطلوب است
                if trend['trend'] == 'صعودی':
                    favorable_trends += 1
                elif trend['trend'] == 'نزولی':
                    unfavorable_trends += 1
        
        if favorable_trends >= 2:
            level = 'بهبود'
            interpretation = 'روند کلی اهرمی در حال بهبود است'
        elif unfavorable_trends >= 2:
            level = 'کاهش'
            interpretation = 'روند کلی اهرمی در حال کاهش است'
        else:
            level = 'پایدار'
            interpretation = 'روند کلی اهرمی پایدار است'
        
        return {
            'level': level,
            'interpretation': interpretation,
            'favorable_trends': favorable_trends,
            'unfavorable_trends': unfavorable_trends
        }
    
    def _assess_overall_profitability_trend(self, trends: Dict) -> Dict[str, Any]:
        """ارزیابی کلی روند سودآوری"""
        
        positive_trends = sum(1 for trend in trends.values() if trend['trend'] == 'صعودی')
        negative_trends = sum(1 for trend in trends.values() if trend['trend'] == 'نزولی')
        
        if positive_trends >= 3:
            level = 'بهبود قوی'
            interpretation = 'روند کلی سودآوری در حال بهبود قوی است'
        elif positive_trends >= 2:
            level = 'بهبود'
            interpretation = 'روند کلی سودآوری در حال بهبود است'
        elif negative_trends >= 3:
            level = 'کاهش شدید'
            interpretation = 'روند کلی سودآوری در حال کاهش شدید است'
        elif negative_trends >= 2:
            level = 'کاهش'
            interpretation = 'روند کلی سودآوری در حال کاهش است'
        else:
            level = 'پایدار'
            interpretation = 'روند کلی سودآوری پایدار است'
        
        return {
            'level': level,
            'interpretation': interpretation,
            'positive_trends': positive_trends,
            'negative_trends': negative_trends
        }
    
    def _assess_overall_activity_trend(self, trends: Dict) -> Dict[str, Any]:
        """ارزیابی کلی روند فعالیت"""
        
        # برای نسبت‌های فعالیت، روند صعودی برای turnover ratios و نزولی برای cycle مطلوب است
        favorable_trends = 0
        unfavorable_trends = 0
        
        for ratio_name, trend in trends.items():
            if ratio_name in ['inventory_turnover', 'receivables_turnover', 'asset_turnover']:
                # برای نسبت‌های گردش، روند صعودی مطلوب است
                if trend['trend'] == 'صعودی':
                    favorable_trends += 1
                elif trend['trend'] == 'نزولی':
                    unfavorable_trends += 1
            elif ratio_name == 'cash_conversion_cycle':
                # برای چرخه تبدیل نقدی، روند نزولی مطلوب است
                if trend['trend'] == 'نزولی':
                    favorable_trends += 1
                elif trend['trend'] == 'صعودی':
                    unfavorable_trends += 1
        
        if favorable_trends >= 2:
            level = 'بهبود'
            interpretation = 'روند کلی کارایی در حال بهبود است'
        elif unfavorable_trends >= 2:
            level = 'کاهش'
            interpretation = 'روند کلی کارایی در حال کاهش است'
        else:
            level = 'پایدار'
            interpretation = 'روند کلی کارایی پایدار است'
        
        return {
            'level': level,
            'interpretation': interpretation,
            'favorable_trends': favorable_trends,
            'unfavorable_trends': unfavorable_trends
        }
    
    def _assess_overall_financial_trend(self, key_metrics: Dict) -> Dict[str, Any]:
        """ارزیابی کلی روند مالی"""
        
        # ارزیابی بر اساس شاخص‌های کلیدی
        positive_metrics = sum(1 for metric in key_metrics.values() if metric['trend'] in ['رشد قوی', 'رشد متوسط'])
        negative_metrics = sum(1 for metric in key_metrics.values() if metric['trend'] in ['کاهش شدید', 'کاهش متوسط'])
        
        if positive_metrics >= 3:
            level = 'رشد قوی'
            interpretation = 'شرکت در مسیر رشد قوی قرار دارد'
        elif positive_metrics >= 2:
            level = 'رشد متوسط'
            interpretation = 'شرکت در مسیر رشد متوسط قرار دارد'
        elif negative_metrics >= 3:
            level = 'کاهش شدید'
            interpretation = 'شرکت با کاهش شدید مواجه است'
        elif negative_metrics >= 2:
            level = 'کاهش متوسط'
            interpretation = 'شرکت با کاهش متوسط مواجه است'
        else:
            level = 'پایدار'
            interpretation = 'شرکت در وضعیت پایدار قرار دارد'
        
        return {
            'level': level,
            'interpretation': interpretation,
            'positive_metrics': positive_metrics,
            'negative_metrics': negative_metrics
        }
    
    def _identify_patterns(self, trend_analysis: Dict) -> Dict[str, Any]:
        """شناسایی الگوهای روند"""
        
        patterns = {
            'seasonal_patterns': self._identify_seasonal_patterns(trend_analysis),
            'cyclical_patterns': self._identify_cyclical_patterns(trend_analysis),
            'correlation_patterns': self._identify_correlation_patterns(trend_analysis),
            'anomalies': self._identify_anomalies(trend_analysis)
        }
        
        return patterns
    
    def _identify_seasonal_patterns(self, trend_analysis: Dict) -> List[str]:
        """شناسایی الگوهای فصلی"""
        # این بخش نیاز به داده‌های ماهانه دارد
        return ['الگوی فصلی شناسایی نشد - نیاز به داده‌های ماهانه']
    
    def _identify_cyclical_patterns(self, trend_analysis: Dict) -> List[str]:
        """شناسایی الگوهای دوره‌ای"""
        # این بخش نیاز به داده‌های بلندمدت دارد
        return ['الگوی دوره‌ای شناسایی نشد - نیاز به داده‌های بلندمدت']
    
    def _identify_correlation_patterns(self, trend_analysis: Dict) -> List[str]:
        """شناسایی الگوهای همبستگی"""
        
        patterns = []
        
        # بررسی همبستگی بین روندهای مختلف
        liquidity_trend = trend_analysis['liquidity_trends']['overall_trend']['level']
        profitability_trend = trend_analysis['profitability_trends']['overall_trend']['level']
        
        if liquidity_trend == 'بهبود' and profitability_trend == 'بهبود قوی':
            patterns.append('همبستگی مثبت قوی بین بهبود نقدینگی و سودآوری')
        
        if trend_analysis['leverage_trends']['overall_trend']['level'] == 'کاهش':
            patterns.append('کاهش اهرم مالی ممکن است بر رشد تأثیر گذاشته باشد')
        
        return patterns
    
    def _identify_anomalies(self, trend_analysis: Dict) -> List[str]:
        """شناسایی ناهنجاری‌ها"""
        
        anomalies = []
        
        # بررسی ناهنجاری در روندها
        for category, analysis in trend_analysis.items():
            if category != 'overall_trends':
                individual_trends = analysis['individual_trends']
                for ratio_name, trend in individual_trends.items():
                    if trend['r_squared'] < 0.5 and abs(trend['slope']) > 0.1:
                        anomalies.append(f'ناهنجاری در روند {ratio_name} - نوسان بالا')
        
        return anomalies
    
    def _generate_forecasts(self, trend_analysis: Dict) -> Dict[str, Any]:
        """تولید پیش‌بینی‌های آینده"""
        
        forecasts = {
            'liquidity_forecast': self._forecast_liquidity(trend_analysis['liquidity_trends']),
            'profitability_forecast': self._forecast_profitability(trend_analysis['profitability_trends']),
            'leverage_forecast': self._forecast_leverage(trend_analysis['leverage_trends']),
            'activity_forecast': self._forecast_activity(trend_analysis['activity_trends'])
        }
        
        return forecasts
    
    def _forecast_liquidity(self, liquidity_trends: Dict) -> Dict[str, Any]:
        """پیش‌بینی روند نقدینگی"""
        
        overall_trend = liquidity_trends['overall_trend']['level']
        
        if overall_trend == 'بهبود':
            forecast = 'ادامه بهبود نقدینگی در دوره آینده'
            confidence = 'بالا'
        elif overall_trend == 'کاهش':
            forecast = 'ادامه کاهش نقدینگی در دوره آینده'
            confidence = 'متوسط'
        else:
            forecast = 'پایداری نقدینگی در دوره آینده'
            confidence = 'بالا'
        
        return {
            'forecast': forecast,
            'confidence': confidence,
            'time_horizon': '۳-۶ ماه آینده'
        }
    
    def _forecast_profitability(self, profitability_trends: Dict) -> Dict[str, Any]:
        """پیش‌بینی روند سودآوری"""
        
        overall_trend = profitability_trends['overall_trend']['level']
        
        if 'قوی' in overall_trend:
            forecast = 'ادامه رشد قوی سودآوری'
            confidence = 'بالا'
        elif 'بهبود' in overall_trend:
            forecast = 'ادامه بهبود سودآوری'
            confidence = 'متوسط'
        elif 'کاهش' in overall_trend:
            forecast = 'ادامه کاهش سودآوری'
            confidence = 'متوسط'
        else:
            forecast = 'پایداری سودآوری'
            confidence = 'بالا'
        
        return {
            'forecast': forecast,
            'confidence': confidence,
            'time_horizon': '۶-۱۲ ماه آینده'
        }
    
    def _forecast_leverage(self, leverage_trends: Dict) -> Dict[str, Any]:
        """پیش‌بینی روند اهرمی"""
        
        overall_trend = leverage_trends['overall_trend']['level']
        
        if overall_trend == 'بهبود':
            forecast = 'ادامه بهبود ساختار سرمایه'
            confidence = 'متوسط'
        elif overall_trend == 'کاهش':
            forecast = 'ادامه افزایش اهرم مالی'
            confidence = 'متوسط'
        else:
            forecast = 'پایداری ساختار سرمایه'
            confidence = 'بالا'
        
        return {
            'forecast': forecast,
            'confidence': confidence,
            'time_horizon': '۱۲ ماه آینده'
        }
    
    def _forecast_activity(self, activity_trends: Dict) -> Dict[str, Any]:
        """پیش‌بینی روند فعالیت"""
        
        overall_trend = activity_trends['overall_trend']['level']
        
        if overall_trend == 'بهبود':
            forecast = 'ادامه بهبود کارایی عملیاتی'
            confidence = 'متوسط'
        elif overall_trend == 'کاهش':
            forecast = 'ادامه کاهش کارایی عملیاتی'
            confidence = 'متوسط'
        else:
            forecast = 'پایداری کارایی عملیاتی'
            confidence = 'بالا'
        
        return {
            'forecast': forecast,
            'confidence': confidence,
            'time_horizon': '۶-۹ ماه آینده'
        }
    
    def _generate_trend_recommendations(self, trend_analysis: Dict, patterns: Dict) -> List[Dict[str, Any]]:
        """تولید توصیه‌های مبتنی بر تحلیل روند"""
        
        recommendations = []
        
        # توصیه‌های مبتنی بر روند کلی
        overall_trend = trend_analysis['overall_trends']['overall_assessment']['level']
        
        if overall_trend == 'رشد قوی':
            recommendations.append({
                'priority': 'پایین',
                'category': 'استراتژی رشد',
                'recommendation': 'ادامه استراتژی فعلی و سرمایه‌گذاری در رشد',
                'action': 'حفظ مسیر رشد و بررسی فرصت‌های توسعه',
                'expected_impact': 'تداوم رشد قوی'
            })
        elif overall_trend == 'کاهش شدید':
            recommendations.append({
                'priority': 'فوری',
                'category': 'مدیریت بحران',
                'recommendation': 'بازنگری فوری استراتژی و کاهش هزینه‌ها',
                'action': 'تحلیل علل کاهش و اجرای برنامه بهبود',
                'expected_impact': 'توقف کاهش و شروع بهبود'
            })
        
        # توصیه‌های مبتنی بر روندهای خاص
        liquidity_trend = trend_analysis['liquidity_trends']['overall_trend']['level']
        if liquidity_trend == 'کاهش':
            recommendations.append({
                'priority': 'بالا',
                'category': 'مدیریت نقدینگی',
                'recommendation': 'بهبود مدیریت نقدینگی و کاهش بدهی‌های کوتاه‌مدت',
                'action': 'بررسی جریان نقدی و بهینه‌سازی منابع',
                'expected_impact': 'بهبود وضعیت نقدینگی'
            })
        
        profitability_trend = trend_analysis['profitability_trends']['overall_trend']['level']
        if 'کاهش' in profitability_trend:
            recommendations.append({
                'priority': 'بالا',
                'category': 'بهبود سودآوری',
                'recommendation': 'افزایش کارایی عملیاتی و کاهش هزینه‌ها',
                'action': 'تحلیل حاشیه سود و بهینه‌سازی فرآیندها',
                'expected_impact': 'افزایش سودآوری'
            })
        
        return recommendations


# ابزار LangChain برای تحلیل روند نسبت‌ها
class RatioTrendTool:
    """ابزار تحلیل روند نسبت‌های مالی برای LangChain"""
    
    name = "ratio_trend_analysis"
    description = "تحلیل روند تغییرات نسبت‌های مالی در دوره‌های مختلف"
    
    def __init__(self):
        self.analyzer_class = RatioTrendAnalyzer
    
    def analyze_trends(self, company_id: int, period_ids: List[int]) -> Dict:
        """تحلیل روند نسبت‌ها برای شرکت و دوره‌های مشخص"""
        try:
            company = Company.objects.get(id=company_id)
            periods = FinancialPeriod.objects.filter(id__in=period_ids).order_by('start_date')
            
            if len(periods) < 2:
                return {
                    'success': False,
                    'error': 'برای تحلیل روند حداقل ۲ دوره مالی مورد نیاز است'
                }
            
            analyzer = RatioTrendAnalyzer(company)
            result = analyzer.analyze_ratio_trends(periods)
            
            return {
                'success': True,
                'analysis': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
