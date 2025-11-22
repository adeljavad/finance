# financial_system/services/liquidity_ratios.py
"""
تسک ۶۱: پیاده‌سازی محاسبه نسبت‌های نقدینگی
این سرویس برای محاسبه و تحلیل نسبت‌های نقدینگی طراحی شده است.
"""

from typing import Dict, List, Any
from decimal import Decimal
from users.models import Company, FinancialPeriod, FinancialFile, Document


class LiquidityRatioAnalyzer:
    """تحلیل‌گر نسبت‌های نقدینگی"""
    
    def __init__(self, company: Company, period: FinancialPeriod):
        self.company = company
        self.period = period
    
    def calculate_all_liquidity_ratios(self) -> Dict[str, Any]:
        """محاسبه تمام نسبت‌های نقدینگی"""
        
        # جمع‌آوری داده‌های مورد نیاز
        financial_data = self._collect_financial_data()
        
        # محاسبه نسبت‌ها
        ratios = {
            'current_ratio': self._calculate_current_ratio(financial_data),
            'quick_ratio': self._calculate_quick_ratio(financial_data),
            'cash_ratio': self._calculate_cash_ratio(financial_data),
            'net_working_capital': self._calculate_net_working_capital(financial_data),
            'operating_cash_flow_ratio': self._calculate_operating_cash_flow_ratio(financial_data),
            'defensive_interval_ratio': self._calculate_defensive_interval_ratio(financial_data)
        }
        
        # تحلیل و ارزیابی
        analysis = self._analyze_liquidity_ratios(ratios, financial_data)
        
        return {
            'company': self.company.name,
            'period': self.period.name,
            'financial_data': financial_data,
            'liquidity_ratios': ratios,
            'analysis': analysis,
            'recommendations': self._generate_liquidity_recommendations(ratios, analysis)
        }
    
    def _collect_financial_data(self) -> Dict[str, Any]:
        """جمع‌آوری داده‌های مالی مورد نیاز"""
        
        # این بخش باید با مدل‌های واقعی یکپارچه شود
        # فعلاً از داده‌های نمونه استفاده می‌کنیم
        
        return {
            'current_assets': {
                'cash': Decimal('500000000'),  # 500 میلیون
                'cash_equivalents': Decimal('200000000'),  # 200 میلیون
                'accounts_receivable': Decimal('800000000'),  # 800 میلیون
                'inventory': Decimal('600000000'),  # 600 میلیون
                'prepaid_expenses': Decimal('100000000'),  # 100 میلیون
                'marketable_securities': Decimal('300000000'),  # 300 میلیون
                'total': Decimal('2500000000')  # 2.5 میلیارد
            },
            'current_liabilities': {
                'accounts_payable': Decimal('700000000'),  # 700 میلیون
                'short_term_debt': Decimal('400000000'),  # 400 میلیون
                'accrued_expenses': Decimal('200000000'),  # 200 میلیون
                'unearned_revenue': Decimal('100000000'),  # 100 میلیون
                'total': Decimal('1400000000')  # 1.4 میلیارد
            },
            'operating_data': {
                'operating_cash_flow': Decimal('900000000'),  # 900 میلیون
                'daily_operating_expenses': Decimal('5000000'),  # 5 میلیون
                'annual_operating_expenses': Decimal('1825000000')  # 1.825 میلیارد
            }
        }
    
    def _calculate_current_ratio(self, data: Dict) -> Dict[str, Any]:
        """محاسبه نسبت جاری"""
        
        current_assets = data['current_assets']['total']
        current_liabilities = data['current_liabilities']['total']
        
        if current_liabilities == 0:
            ratio = Decimal('0')
        else:
            ratio = current_assets / current_liabilities
        
        assessment = self._assess_current_ratio(ratio)
        
        return {
            'ratio': float(ratio),
            'formula': 'دارایی‌های جاری / بدهی‌های جاری',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 1.5,
            'calculation_details': {
                'current_assets': float(current_assets),
                'current_liabilities': float(current_liabilities)
            }
        }
    
    def _assess_current_ratio(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی نسبت جاری"""
        
        ratio_float = float(ratio)
        
        if ratio_float >= 2.0:
            return {
                'level': 'عالی',
                'interpretation': 'نقدینگی بسیار قوی - شرکت توانایی بالایی در پرداخت بدهی‌های کوتاه‌مدت دارد'
            }
        elif ratio_float >= 1.5:
            return {
                'level': 'خوب',
                'interpretation': 'نقدینگی مناسب - شرکت در وضعیت مطلوبی برای پرداخت بدهی‌های جاری قرار دارد'
            }
        elif ratio_float >= 1.0:
            return {
                'level': 'متوسط',
                'interpretation': 'نقدینگی قابل قبول - شرکت می‌تواند بدهی‌های جاری را پرداخت کند'
            }
        elif ratio_float >= 0.5:
            return {
                'level': 'ضعیف',
                'interpretation': 'نقدینگی پایین - شرکت ممکن است در پرداخت بدهی‌های جاری با مشکل مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'نقدینگی بسیار پایین - شرکت در معرض ریسک ورشکستگی قرار دارد'
            }
    
    def _calculate_quick_ratio(self, data: Dict) -> Dict[str, Any]:
        """محاسبه نسبت سریع (اسید تست)"""
        
        # دارایی‌های سریع = نقد + معادل نقد + حساب‌های دریافتنی + اوراق بهادار قابل فروش
        quick_assets = (
            data['current_assets']['cash'] +
            data['current_assets']['cash_equivalents'] +
            data['current_assets']['accounts_receivable'] +
            data['current_assets']['marketable_securities']
        )
        
        current_liabilities = data['current_liabilities']['total']
        
        if current_liabilities == 0:
            ratio = Decimal('0')
        else:
            ratio = quick_assets / current_liabilities
        
        assessment = self._assess_quick_ratio(ratio)
        
        return {
            'ratio': float(ratio),
            'formula': '(نقد + معادل نقد + حساب‌های دریافتنی + اوراق بهادار قابل فروش) / بدهی‌های جاری',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 1.0,
            'calculation_details': {
                'quick_assets': float(quick_assets),
                'current_liabilities': float(current_liabilities),
                'components': {
                    'cash': float(data['current_assets']['cash']),
                    'cash_equivalents': float(data['current_assets']['cash_equivalents']),
                    'accounts_receivable': float(data['current_assets']['accounts_receivable']),
                    'marketable_securities': float(data['current_assets']['marketable_securities'])
                }
            }
        }
    
    def _assess_quick_ratio(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی نسبت سریع"""
        
        ratio_float = float(ratio)
        
        if ratio_float >= 1.2:
            return {
                'level': 'عالی',
                'interpretation': 'توانایی بسیار بالا در پرداخت بدهی‌های فوری بدون وابستگی به فروش موجودی'
            }
        elif ratio_float >= 1.0:
            return {
                'level': 'خوب',
                'interpretation': 'توانایی مناسب در پرداخت بدهی‌های فوری'
            }
        elif ratio_float >= 0.8:
            return {
                'level': 'متوسط',
                'interpretation': 'توانایی قابل قبول در پرداخت بدهی‌های فوری'
            }
        elif ratio_float >= 0.5:
            return {
                'level': 'ضعیف',
                'interpretation': 'توانایی محدود در پرداخت بدهی‌های فوری'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'ریسک بالای ناتوانی در پرداخت بدهی‌های فوری'
            }
    
    def _calculate_cash_ratio(self, data: Dict) -> Dict[str, Any]:
        """محاسبه نسبت نقدی"""
        
        cash_assets = (
            data['current_assets']['cash'] +
            data['current_assets']['cash_equivalents'] +
            data['current_assets']['marketable_securities']
        )
        
        current_liabilities = data['current_liabilities']['total']
        
        if current_liabilities == 0:
            ratio = Decimal('0')
        else:
            ratio = cash_assets / current_liabilities
        
        assessment = self._assess_cash_ratio(ratio)
        
        return {
            'ratio': float(ratio),
            'formula': '(نقد + معادل نقد + اوراق بهادار قابل فروش) / بدهی‌های جاری',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 0.2,
            'calculation_details': {
                'cash_assets': float(cash_assets),
                'current_liabilities': float(current_liabilities),
                'components': {
                    'cash': float(data['current_assets']['cash']),
                    'cash_equivalents': float(data['current_assets']['cash_equivalents']),
                    'marketable_securities': float(data['current_assets']['marketable_securities'])
                }
            }
        }
    
    def _assess_cash_ratio(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی نسبت نقدی"""
        
        ratio_float = float(ratio)
        
        if ratio_float >= 0.5:
            return {
                'level': 'عالی',
                'interpretation': 'ذخایر نقدی بسیار قوی - شرکت می‌تواند تمام بدهی‌های جاری را فقط با دارایی‌های نقدی پرداخت کند'
            }
        elif ratio_float >= 0.3:
            return {
                'level': 'خوب',
                'interpretation': 'ذخایر نقدی مناسب - شرکت ذخایر کافی برای شرایط اضطراری دارد'
            }
        elif ratio_float >= 0.2:
            return {
                'level': 'متوسط',
                'interpretation': 'ذخایر نقدی قابل قبول - شرکت ذخایر معقولی دارد'
            }
        elif ratio_float >= 0.1:
            return {
                'level': 'ضعیف',
                'interpretation': 'ذخایر نقدی محدود - شرکت ممکن است در شرایط اضطراری با مشکل مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'ذخایر نقدی ناکافی - شرکت در معرض ریسک نقدینگی شدید قرار دارد'
            }
    
    def _calculate_net_working_capital(self, data: Dict) -> Dict[str, Any]:
        """محاسبه سرمایه در گردش خالص"""
        
        current_assets = data['current_assets']['total']
        current_liabilities = data['current_liabilities']['total']
        
        net_working_capital = current_assets - current_liabilities
        
        assessment = self._assess_net_working_capital(net_working_capital, current_assets)
        
        return {
            'amount': float(net_working_capital),
            'formula': 'دارایی‌های جاری - بدهی‌های جاری',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'calculation_details': {
                'current_assets': float(current_assets),
                'current_liabilities': float(current_liabilities)
            }
        }
    
    def _assess_net_working_capital(self, nwc: Decimal, current_assets: Decimal) -> Dict[str, Any]:
        """ارزیابی سرمایه در گردش خالص"""
        
        nwc_float = float(nwc)
        current_assets_float = float(current_assets)
        
        if nwc_float <= 0:
            return {
                'level': 'بحرانی',
                'interpretation': 'سرمایه در گردش منفی - شرکت ممکن است نتواند بدهی‌های جاری را پرداخت کند'
            }
        elif nwc_float < current_assets_float * 0.1:
            return {
                'level': 'ضعیف',
                'interpretation': 'سرمایه در گردش بسیار کم - شرکت حاشیه ایمنی کمی دارد'
            }
        elif nwc_float < current_assets_float * 0.2:
            return {
                'level': 'متوسط',
                'interpretation': 'سرمایه در گردش قابل قبول - شرکت حاشیه ایمنی معقولی دارد'
            }
        elif nwc_float < current_assets_float * 0.3:
            return {
                'level': 'خوب',
                'interpretation': 'سرمایه در گردش مناسب - شرکت حاشیه ایمنی خوبی دارد'
            }
        else:
            return {
                'level': 'عالی',
                'interpretation': 'سرمایه در گردش قوی - شرکت حاشیه ایمنی بسیار خوبی دارد'
            }
    
    def _calculate_operating_cash_flow_ratio(self, data: Dict) -> Dict[str, Any]:
        """محاسبه نسبت جریان نقدی عملیاتی"""
        
        operating_cash_flow = data['operating_data']['operating_cash_flow']
        current_liabilities = data['current_liabilities']['total']
        
        if current_liabilities == 0:
            ratio = Decimal('0')
        else:
            ratio = operating_cash_flow / current_liabilities
        
        assessment = self._assess_operating_cash_flow_ratio(ratio)
        
        return {
            'ratio': float(ratio),
            'formula': 'جریان نقدی عملیاتی / بدهی‌های جاری',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 0.4,
            'calculation_details': {
                'operating_cash_flow': float(operating_cash_flow),
                'current_liabilities': float(current_liabilities)
            }
        }
    
    def _assess_operating_cash_flow_ratio(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی نسبت جریان نقدی عملیاتی"""
        
        ratio_float = float(ratio)
        
        if ratio_float >= 0.6:
            return {
                'level': 'عالی',
                'interpretation': 'جریان نقدی عملیاتی بسیار قوی - شرکت می‌تواند بدهی‌های جاری را به راحتی از عملیات پرداخت کند'
            }
        elif ratio_float >= 0.4:
            return {
                'level': 'خوب',
                'interpretation': 'جریان نقدی عملیاتی مناسب - شرکت توانایی خوبی در پرداخت بدهی‌های جاری از عملیات دارد'
            }
        elif ratio_float >= 0.2:
            return {
                'level': 'متوسط',
                'interpretation': 'جریان نقدی عملیاتی قابل قبول - شرکت می‌تواند بخشی از بدهی‌های جاری را از عملیات پرداخت کند'
            }
        elif ratio_float >= 0.1:
            return {
                'level': 'ضعیف',
                'interpretation': 'جریان نقدی عملیاتی محدود - شرکت برای پرداخت بدهی‌های جاری به منابع دیگر نیاز دارد'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'جریان نقدی عملیاتی ناکافی - شرکت نمی‌تواند بدهی‌های جاری را از عملیات پرداخت کند'
            }
    
    def _calculate_defensive_interval_ratio(self, data: Dict) -> Dict[str, Any]:
        """محاسبه نسبت فاصله دفاعی"""
        
        defensive_assets = (
            data['current_assets']['cash'] +
            data['current_assets']['cash_equivalents'] +
            data['current_assets']['marketable_securities'] +
            data['current_assets']['accounts_receivable']
        )
        
        daily_operating_expenses = data['operating_data']['daily_operating_expenses']
        
        if daily_operating_expenses == 0:
            ratio = Decimal('0')
        else:
            ratio = defensive_assets / daily_operating_expenses
        
        assessment = self._assess_defensive_interval_ratio(ratio)
        
        return {
            'days': float(ratio),
            'formula': 'دارایی‌های دفاعی / هزینه‌های عملیاتی روزانه',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 90,  # 90 روز
            'calculation_details': {
                'defensive_assets': float(defensive_assets),
                'daily_operating_expenses': float(daily_operating_expenses),
                'components': {
                    'cash': float(data['current_assets']['cash']),
                    'cash_equivalents': float(data['current_assets']['cash_equivalents']),
                    'marketable_securities': float(data['current_assets']['marketable_securities']),
                    'accounts_receivable': float(data['current_assets']['accounts_receivable'])
                }
            }
        }
    
    def _assess_defensive_interval_ratio(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی نسبت فاصله دفاعی"""
        
        days = float(ratio)
        
        if days >= 180:
            return {
                'level': 'عالی',
                'interpretation': 'ذخایر دفاعی بسیار قوی - شرکت می‌تواند بیش از ۶ ماه بدون درآمد به فعالیت ادامه دهد'
            }
        elif days >= 120:
            return {
                'level': 'خوب',
                'interpretation': 'ذخایر دفاعی مناسب - شرکت می‌تواند ۴-۶ ماه بدون درآمد به فعالیت ادامه دهد'
            }
        elif days >= 90:
            return {
                'level': 'متوسط',
                'interpretation': 'ذخایر دفاعی قابل قبول - شرکت می‌تواند ۳ ماه بدون درآمد به فعالیت ادامه دهد'
            }
        elif days >= 60:
            return {
                'level': 'ضعیف',
                'interpretation': 'ذخایر دفاعی محدود - شرکت فقط ۲ ماه بدون درآمد می‌تواند فعالیت کند'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'ذخایر دفاعی ناکافی - شرکت نمی‌تواند بیش از ۲ ماه بدون درآمد فعالیت کند'
            }
    
    def _analyze_liquidity_ratios(self, ratios: Dict, financial_data: Dict) -> Dict[str, Any]:
        """تحلیل جامع نسبت‌های نقدینگی"""
        
        # ارزیابی کلی نقدینگی
        overall_assessment = self._assess_overall_liquidity(ratios)
        
        # شناسایی نقاط قوت و ضعف
        strengths = self._identify_liquidity_strengths(ratios)
        weaknesses = self._identify_liquidity_weaknesses(ratios)
        
        # تحلیل روند (در صورت وجود داده‌های تاریخی)
        trend_analysis = self._analyze_liquidity_trend(ratios)
        
        return {
            'overall_assessment': overall_assessment,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'trend_analysis': trend_analysis,
            'risk_level': self._determine_liquidity_risk_level(ratios)
        }
    
    def _assess_overall_liquidity(self, ratios: Dict) -> Dict[str, Any]:
        """ارزیابی کلی نقدینگی"""
        
        # امتیازدهی به هر نسبت
        scores = {
            'current_ratio': self._score_ratio(ratios['current_ratio']['ratio'], [1.0, 1.5, 2.0]),
            'quick_ratio': self._score_ratio(ratios['quick_ratio']['ratio'], [0.8, 1.0, 1.2]),
            'cash_ratio': self._score_ratio(ratios['cash_ratio']['ratio'], [0.1, 0.2, 0.3]),
            'operating_cash_flow_ratio': self._score_ratio(ratios['operating_cash_flow_ratio']['ratio'], [0.2, 0.4, 0.6]),
            'defensive_interval': self._score_ratio(ratios['defensive_interval_ratio']['days'], [60, 90, 120])
        }
        
        overall_score = sum(scores.values()) / len(scores)
        
        if overall_score >= 4.0:
            level = 'عالی'
            interpretation = 'وضعیت نقدینگی بسیار قوی - شرکت در موقعیت ممتازی قرار دارد'
        elif overall_score >= 3.0:
            level = 'خوب'
            interpretation = 'وضعیت نقدینگی مناسب - شرکت نقدینگی کافی برای فعالیت‌های جاری دارد'
        elif overall_score >= 2.0:
            level = 'متوسط'
            interpretation = 'وضعیت نقدینگی قابل قبول - شرکت می‌تواند بدهی‌های جاری را پرداخت کند'
        elif overall_score >= 1.0:
            level = 'ضعیف'
            interpretation = 'وضعیت نقدینگی نامناسب - شرکت ممکن است با مشکلات نقدینگی مواجه شود'
        else:
            level = 'بحرانی'
            interpretation = 'وضعیت نقدینگی بحرانی - شرکت در معرض ریسک ورشکستگی قرار دارد'
        
        return {
            'level': level,
            'score': overall_score,
            'interpretation': interpretation,
            'individual_scores': scores
        }
    
    def _score_ratio(self, value: float, thresholds: List[float]) -> float:
        """امتیازدهی به یک نسبت بر اساس آستانه‌ها"""
        
        if value >= thresholds[2]:
            return 5.0
        elif value >= thresholds[1]:
            return 4.0
        elif value >= thresholds[0]:
            return 3.0
        elif value >= thresholds[0] * 0.5:
            return 2.0
        elif value >= thresholds[0] * 0.25:
            return 1.0
        else:
            return 0.0
    
    def _identify_liquidity_strengths(self, ratios: Dict) -> List[str]:
        """شناسایی نقاط قوت نقدینگی"""
        
        strengths = []
        
        if ratios['current_ratio']['assessment'] in ['عالی', 'خوب']:
            strengths.append('نسبت جاری قوی')
        
        if ratios['quick_ratio']['assessment'] in ['عالی', 'خوب']:
            strengths.append('توانایی بالا در پرداخت بدهی‌های فوری')
        
        if ratios['cash_ratio']['assessment'] in ['عالی', 'خوب']:
            strengths.append('ذخایر نقدی مناسب')
        
        if ratios['defensive_interval_ratio']['assessment'] in ['عالی', 'خوب']:
            strengths.append('ذخایر دفاعی کافی')
        
        if ratios['operating_cash_flow_ratio']['assessment'] in ['عالی', 'خوب']:
            strengths.append('جریان نقدی عملیاتی قوی')
        
        return strengths
    
    def _identify_liquidity_weaknesses(self, ratios: Dict) -> List[str]:
        """شناسایی نقاط ضعف نقدینگی"""
        
        weaknesses = []
        
        if ratios['current_ratio']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('نسبت جاری ضعیف')
        
        if ratios['quick_ratio']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('توانایی محدود در پرداخت بدهی‌های فوری')
        
        if ratios['cash_ratio']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('ذخایر نقدی ناکافی')
        
        if ratios['defensive_interval_ratio']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('ذخایر دفاعی محدود')
        
        if ratios['operating_cash_flow_ratio']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('جریان نقدی عملیاتی ضعیف')
        
        return weaknesses
    
    def _analyze_liquidity_trend(self, ratios: Dict) -> Dict[str, Any]:
        """تحلیل روند نقدینگی"""
        
        # این تحلیل نیاز به داده‌های تاریخی دارد
        # فعلاً تحلیل ساده ارائه می‌شود
        
        return {
            'trend': 'ثابت',  # نیاز به داده‌های تاریخی
            'improvement_areas': self._identify_trend_improvement_areas(ratios),
            'historical_comparison': 'در دسترس نیست'  # نیاز به داده‌های تاریخی
        }
    
    def _identify_trend_improvement_areas(self, ratios: Dict) -> List[str]:
        """شناسایی حوزه‌های بهبود بر اساس روند"""
        
        improvement_areas = []
        
        if ratios['cash_ratio']['ratio'] < 0.2:
            improvement_areas.append('افزایش ذخایر نقدی')
        
        if ratios['quick_ratio']['ratio'] < 1.0:
            improvement_areas.append('بهبود مدیریت حساب‌های دریافتنی')
        
        if ratios['operating_cash_flow_ratio']['ratio'] < 0.4:
            improvement_areas.append('بهبود جریان نقدی عملیاتی')
        
        return improvement_areas
    
    def _determine_liquidity_risk_level(self, ratios: Dict) -> str:
        """تعیین سطح ریسک نقدینگی"""
        
        critical_ratios = 0
        weak_ratios = 0
        
        for ratio_name, ratio_data in ratios.items():
            if ratio_name != 'net_working_capital':  # این نسبت امتیاز جداگانه ندارد
                assessment = ratio_data['assessment']
                if assessment == 'بحرانی':
                    critical_ratios += 1
                elif assessment == 'ضعیف':
                    weak_ratios += 1
        
        if critical_ratios >= 2:
            return 'بسیار بالا'
        elif critical_ratios >= 1 or weak_ratios >= 2:
            return 'بالا'
        elif weak_ratios >= 1:
            return 'متوسط'
        else:
            return 'پایین'
    
    def _generate_liquidity_recommendations(self, ratios: Dict, analysis: Dict) -> List[Dict[str, Any]]:
        """تولید توصیه‌های بهبود نقدینگی"""
        
        recommendations = []
        
        # توصیه‌های مبتنی بر نسبت‌ها
        if ratios['current_ratio']['ratio'] < 1.5:
            recommendations.append({
                'priority': 'بالا',
                'category': 'نسبت جاری',
                'recommendation': 'افزایش دارایی‌های جاری یا کاهش بدهی‌های جاری',
                'action': 'بررسی مدیریت موجودی و حساب‌های دریافتنی',
                'expected_impact': 'افزایش ۰.۲-۰.۵ واحدی نسبت جاری'
            })
        
        if ratios['cash_ratio']['ratio'] < 0.2:
            recommendations.append({
                'priority': 'بالا',
                'category': 'ذخایر نقدی',
                'recommendation': 'افزایش موجودی نقدی و معادل نقد',
                'action': 'برنامه‌ریزی برای نگهداری حداقل ۲۰٪ بدهی‌های جاری به صورت نقد',
                'expected_impact': 'بهبود توانایی پرداخت فوری'
            })
        
        if ratios['operating_cash_flow_ratio']['ratio'] < 0.4:
            recommendations.append({
                'priority': 'متوسط',
                'category': 'جریان نقدی',
                'recommendation': 'بهبود مدیریت جریان نقدی عملیاتی',
                'action': 'بهینه‌سازی دوره وصول و دوره پرداخت',
                'expected_impact': 'افزایش جریان نقدی عملیاتی'
            })
        
        # توصیه‌های مبتنی بر تحلیل کلی
        if analysis['risk_level'] in ['بالا', 'بسیار بالا']:
            recommendations.append({
                'priority': 'فوری',
                'category': 'مدیریت ریسک',
                'recommendation': 'ایجاد برنامه اضطراری نقدینگی',
                'action': 'تعیین خطوط اعتباری اضطراری و برنامه کاهش هزینه‌ها',
                'expected_impact': 'کاهش ریسک ورشکستگی'
            })
        
        return recommendations


# ابزار LangChain برای تحلیل نسبت‌های نقدینگی
class LiquidityRatioTool:
    """ابزار تحلیل نسبت‌های نقدینگی برای LangChain"""
    
    name = "liquidity_ratios"
    description = "محاسبه و تحلیل نسبت‌های نقدینگی شرکت"
    
    def __init__(self):
        self.analyzer_class = LiquidityRatioAnalyzer
    
    def analyze_liquidity(self, company_id: int, period_id: int) -> Dict:
        """تحلیل نسبت‌های نقدینگی برای شرکت و دوره مشخص"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            analyzer = LiquidityRatioAnalyzer(company, period)
            result = analyzer.calculate_all_liquidity_ratios()
            
            return {
                'success': True,
                'analysis': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
