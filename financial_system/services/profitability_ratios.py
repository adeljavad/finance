# financial_system/services/profitability_ratios.py
"""
تسک ۶۳: پیاده‌سازی محاسبه نسبت‌های سودآوری
این سرویس برای محاسبه و تحلیل نسبت‌های سودآوری و کارایی شرکت طراحی شده است.
"""

from typing import Dict, List, Any
from decimal import Decimal
from users.models import Company, FinancialPeriod, FinancialFile, Document


class ProfitabilityRatioAnalyzer:
    """تحلیل‌گر نسبت‌های سودآوری"""
    
    def __init__(self, company: Company, period: FinancialPeriod):
        self.company = company
        self.period = period
    
    def calculate_all_profitability_ratios(self) -> Dict[str, Any]:
        """محاسبه تمام نسبت‌های سودآوری"""
        
        # جمع‌آوری داده‌های مورد نیاز
        financial_data = self._collect_financial_data()
        
        # محاسبه نسبت‌ها
        ratios = {
            'gross_profit_margin': self._calculate_gross_profit_margin(financial_data),
            'operating_profit_margin': self._calculate_operating_profit_margin(financial_data),
            'net_profit_margin': self._calculate_net_profit_margin(financial_data),
            'return_on_assets': self._calculate_return_on_assets(financial_data),
            'return_on_equity': self._calculate_return_on_equity(financial_data),
            'return_on_invested_capital': self._calculate_return_on_invested_capital(financial_data),
            'ebitda_margin': self._calculate_ebitda_margin(financial_data),
            'operating_ratio': self._calculate_operating_ratio(financial_data)
        }
        
        # تحلیل و ارزیابی
        analysis = self._analyze_profitability_ratios(ratios, financial_data)
        
        return {
            'company': self.company.name,
            'period': self.period.name,
            'financial_data': financial_data,
            'profitability_ratios': ratios,
            'analysis': analysis,
            'recommendations': self._generate_profitability_recommendations(ratios, analysis)
        }
    
    def _collect_financial_data(self) -> Dict[str, Any]:
        """جمع‌آوری داده‌های مالی مورد نیاز"""
        
        # این بخش باید با مدل‌های واقعی یکپارچه شود
        # فعلاً از داده‌های نمونه استفاده می‌کنیم
        
        return {
            'income_statement': {
                'revenue': Decimal('8000000000'),  # 8 میلیارد
                'cost_of_goods_sold': Decimal('5000000000'),  # 5 میلیارد
                'gross_profit': Decimal('3000000000'),  # 3 میلیارد
                'operating_expenses': Decimal('1500000000'),  # 1.5 میلیارد
                'operating_income': Decimal('1500000000'),  # 1.5 میلیارد
                'ebit': Decimal('1400000000'),  # 1.4 میلیارد
                'ebitda': Decimal('1600000000'),  # 1.6 میلیارد
                'interest_expense': Decimal('200000000'),  # 200 میلیون
                'tax_expense': Decimal('300000000'),  # 300 میلیون
                'net_income': Decimal('900000000')  # 900 میلیون
            },
            'balance_sheet': {
                'total_assets': Decimal('10000000000'),  # 10 میلیارد
                'total_equity': Decimal('4000000000'),  # 4 میلیارد
                'total_debt': Decimal('6000000000'),  # 6 میلیارد
                'current_assets': Decimal('2500000000'),  # 2.5 میلیارد
                'fixed_assets': Decimal('7500000000')  # 7.5 میلیارد
            },
            'market_data': {
                'market_capitalization': Decimal('12000000000'),  # 12 میلیارد
                'shares_outstanding': Decimal('100000000')  # 100 میلیون سهم
            }
        }
    
    def _calculate_gross_profit_margin(self, data: Dict) -> Dict[str, Any]:
        """محاسبه حاشیه سود ناخالص"""
        
        gross_profit = data['income_statement']['gross_profit']
        revenue = data['income_statement']['revenue']
        
        if revenue == 0:
            ratio = Decimal('0')
        else:
            ratio = gross_profit / revenue
        
        assessment = self._assess_gross_profit_margin(ratio)
        
        return {
            'ratio': float(ratio),
            'percentage': float(ratio * 100),
            'formula': 'سود ناخالص / درآمد',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 40.0,
            'calculation_details': {
                'gross_profit': float(gross_profit),
                'revenue': float(revenue)
            }
        }
    
    def _assess_gross_profit_margin(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی حاشیه سود ناخالص"""
        
        percentage = float(ratio * 100)
        
        if percentage >= 50:
            return {
                'level': 'عالی',
                'interpretation': 'حاشیه سود ناخالص بسیار قوی - شرکت کنترل خوبی بر هزینه‌های تولید دارد'
            }
        elif percentage >= 40:
            return {
                'level': 'خوب',
                'interpretation': 'حاشیه سود ناخالص مناسب - شرکت کارایی خوبی در تولید دارد'
            }
        elif percentage >= 30:
            return {
                'level': 'متوسط',
                'interpretation': 'حاشیه سود ناخالص قابل قبول - شرکت می‌تواند هزینه‌های تولید را مدیریت کند'
            }
        elif percentage >= 20:
            return {
                'level': 'ضعیف',
                'interpretation': 'حاشیه سود ناخالص محدود - شرکت ممکن است با فشار هزینه‌ها مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'حاشیه سود ناخالص بسیار پایین - شرکت در معرض ریسک زیان قرار دارد'
            }
    
    def _calculate_operating_profit_margin(self, data: Dict) -> Dict[str, Any]:
        """محاسبه حاشیه سود عملیاتی"""
        
        operating_income = data['income_statement']['operating_income']
        revenue = data['income_statement']['revenue']
        
        if revenue == 0:
            ratio = Decimal('0')
        else:
            ratio = operating_income / revenue
        
        assessment = self._assess_operating_profit_margin(ratio)
        
        return {
            'ratio': float(ratio),
            'percentage': float(ratio * 100),
            'formula': 'سود عملیاتی / درآمد',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 15.0,
            'calculation_details': {
                'operating_income': float(operating_income),
                'revenue': float(revenue)
            }
        }
    
    def _assess_operating_profit_margin(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی حاشیه سود عملیاتی"""
        
        percentage = float(ratio * 100)
        
        if percentage >= 20:
            return {
                'level': 'عالی',
                'interpretation': 'حاشیه سود عملیاتی بسیار قوی - شرکت کارایی عملیاتی ممتازی دارد'
            }
        elif percentage >= 15:
            return {
                'level': 'خوب',
                'interpretation': 'حاشیه سود عملیاتی مناسب - شرکت مدیریت هزینه‌های عملیاتی خوبی دارد'
            }
        elif percentage >= 10:
            return {
                'level': 'متوسط',
                'interpretation': 'حاشیه سود عملیاتی قابل قبول - شرکت می‌تواند هزینه‌های عملیاتی را مدیریت کند'
            }
        elif percentage >= 5:
            return {
                'level': 'ضعیف',
                'interpretation': 'حاشیه سود عملیاتی محدود - شرکت ممکن است با فشار هزینه‌های عملیاتی مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'حاشیه سود عملیاتی بسیار پایین - شرکت در معرض ریسک زیان عملیاتی قرار دارد'
            }
    
    def _calculate_net_profit_margin(self, data: Dict) -> Dict[str, Any]:
        """محاسبه حاشیه سود خالص"""
        
        net_income = data['income_statement']['net_income']
        revenue = data['income_statement']['revenue']
        
        if revenue == 0:
            ratio = Decimal('0')
        else:
            ratio = net_income / revenue
        
        assessment = self._assess_net_profit_margin(ratio)
        
        return {
            'ratio': float(ratio),
            'percentage': float(ratio * 100),
            'formula': 'سود خالص / درآمد',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 10.0,
            'calculation_details': {
                'net_income': float(net_income),
                'revenue': float(revenue)
            }
        }
    
    def _assess_net_profit_margin(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی حاشیه سود خالص"""
        
        percentage = float(ratio * 100)
        
        if percentage >= 15:
            return {
                'level': 'عالی',
                'interpretation': 'حاشیه سود خالص بسیار قوی - شرکت سودآوری ممتازی دارد'
            }
        elif percentage >= 10:
            return {
                'level': 'خوب',
                'interpretation': 'حاشیه سود خالص مناسب - شرکت سودآوری خوبی دارد'
            }
        elif percentage >= 5:
            return {
                'level': 'متوسط',
                'interpretation': 'حاشیه سود خالص قابل قبول - شرکت می‌تواند سودآوری خود را حفظ کند'
            }
        elif percentage >= 2:
            return {
                'level': 'ضعیف',
                'interpretation': 'حاشیه سود خالص محدود - شرکت ممکن است با فشار بر سودآوری مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'حاشیه سود خالص بسیار پایین - شرکت در معرض ریسک زیان قرار دارد'
            }
    
    def _calculate_return_on_assets(self, data: Dict) -> Dict[str, Any]:
        """محاسبه بازده دارایی‌ها (ROA)"""
        
        net_income = data['income_statement']['net_income']
        total_assets = data['balance_sheet']['total_assets']
        
        if total_assets == 0:
            ratio = Decimal('0')
        else:
            ratio = net_income / total_assets
        
        assessment = self._assess_return_on_assets(ratio)
        
        return {
            'ratio': float(ratio),
            'percentage': float(ratio * 100),
            'formula': 'سود خالص / کل دارایی‌ها',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 8.0,
            'calculation_details': {
                'net_income': float(net_income),
                'total_assets': float(total_assets)
            }
        }
    
    def _assess_return_on_assets(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی بازده دارایی‌ها"""
        
        percentage = float(ratio * 100)
        
        if percentage >= 12:
            return {
                'level': 'عالی',
                'interpretation': 'بازده دارایی‌ها بسیار قوی - شرکت استفاده بسیار کارآمدی از دارایی‌ها دارد'
            }
        elif percentage >= 8:
            return {
                'level': 'خوب',
                'interpretation': 'بازده دارایی‌ها مناسب - شرکت استفاده کارآمدی از دارایی‌ها دارد'
            }
        elif percentage >= 5:
            return {
                'level': 'متوسط',
                'interpretation': 'بازده دارایی‌ها قابل قبول - شرکت استفاده معقولی از دارایی‌ها دارد'
            }
        elif percentage >= 2:
            return {
                'level': 'ضعیف',
                'interpretation': 'بازده دارایی‌ها محدود - شرکت ممکن است با کارایی پایین دارایی‌ها مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'بازده دارایی‌ها بسیار پایین - شرکت استفاده ناکارآمدی از دارایی‌ها دارد'
            }
    
    def _calculate_return_on_equity(self, data: Dict) -> Dict[str, Any]:
        """محاسبه بازده سرمایه (ROE)"""
        
        net_income = data['income_statement']['net_income']
        total_equity = data['balance_sheet']['total_equity']
        
        if total_equity == 0:
            ratio = Decimal('0')
        else:
            ratio = net_income / total_equity
        
        assessment = self._assess_return_on_equity(ratio)
        
        return {
            'ratio': float(ratio),
            'percentage': float(ratio * 100),
            'formula': 'سود خالص / کل حقوق صاحبان سهام',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 15.0,
            'calculation_details': {
                'net_income': float(net_income),
                'total_equity': float(total_equity)
            }
        }
    
    def _assess_return_on_equity(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی بازده سرمایه"""
        
        percentage = float(ratio * 100)
        
        if percentage >= 20:
            return {
                'level': 'عالی',
                'interpretation': 'بازده سرمایه بسیار قوی - شرکت سودآوری ممتازی برای سهامداران ایجاد می‌کند'
            }
        elif percentage >= 15:
            return {
                'level': 'خوب',
                'interpretation': 'بازده سرمایه مناسب - شرکت سودآوری خوبی برای سهامداران ایجاد می‌کند'
            }
        elif percentage >= 10:
            return {
                'level': 'متوسط',
                'interpretation': 'بازده سرمایه قابل قبول - شرکت سودآوری معقولی برای سهامداران ایجاد می‌کند'
            }
        elif percentage >= 5:
            return {
                'level': 'ضعیف',
                'interpretation': 'بازده سرمایه محدود - شرکت ممکن است با چالش در سودآوری برای سهامداران مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'بازده سرمایه بسیار پایین - شرکت سودآوری ناکافی برای سهامداران ایجاد می‌کند'
            }
    
    def _calculate_return_on_invested_capital(self, data: Dict) -> Dict[str, Any]:
        """محاسبه بازده سرمایه سرمایه‌گذاری شده (ROIC)"""
        
        ebit = data['income_statement']['ebit']
        total_equity = data['balance_sheet']['total_equity']
        total_debt = data['balance_sheet']['total_debt']
        
        invested_capital = total_equity + total_debt
        
        if invested_capital == 0:
            ratio = Decimal('0')
        else:
            ratio = ebit / invested_capital
        
        assessment = self._assess_return_on_invested_capital(ratio)
        
        return {
            'ratio': float(ratio),
            'percentage': float(ratio * 100),
            'formula': 'EBIT / (حقوق صاحبان سهام + بدهی)',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 12.0,
            'calculation_details': {
                'ebit': float(ebit),
                'total_equity': float(total_equity),
                'total_debt': float(total_debt),
                'invested_capital': float(invested_capital)
            }
        }
    
    def _assess_return_on_invested_capital(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی بازده سرمایه سرمایه‌گذاری شده"""
        
        percentage = float(ratio * 100)
        
        if percentage >= 15:
            return {
                'level': 'عالی',
                'interpretation': 'بازده سرمایه سرمایه‌گذاری شده بسیار قوی - شرکت استفاده بسیار کارآمدی از کل سرمایه دارد'
            }
        elif percentage >= 12:
            return {
                'level': 'خوب',
                'interpretation': 'بازده سرمایه سرمایه‌گذاری شده مناسب - شرکت استفاده کارآمدی از کل سرمایه دارد'
            }
        elif percentage >= 8:
            return {
                'level': 'متوسط',
                'interpretation': 'بازده سرمایه سرمایه‌گذاری شده قابل قبول - شرکت استفاده معقولی از کل سرمایه دارد'
            }
        elif percentage >= 5:
            return {
                'level': 'ضعیف',
                'interpretation': 'بازده سرمایه سرمایه‌گذاری شده محدود - شرکت ممکن است با کارایی پایین سرمایه مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'بازده سرمایه سرمایه‌گذاری شده بسیار پایین - شرکت استفاده ناکارآمدی از کل سرمایه دارد'
            }
    
    def _calculate_ebitda_margin(self, data: Dict) -> Dict[str, Any]:
        """محاسبه حاشیه EBITDA"""
        
        ebitda = data['income_statement']['ebitda']
        revenue = data['income_statement']['revenue']
        
        if revenue == 0:
            ratio = Decimal('0')
        else:
            ratio = ebitda / revenue
        
        assessment = self._assess_ebitda_margin(ratio)
        
        return {
            'ratio': float(ratio),
            'percentage': float(ratio * 100),
            'formula': 'EBITDA / درآمد',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 20.0,
            'calculation_details': {
                'ebitda': float(ebitda),
                'revenue': float(revenue)
            }
        }
    
    def _assess_ebitda_margin(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی حاشیه EBITDA"""
        
        percentage = float(ratio * 100)
        
        if percentage >= 25:
            return {
                'level': 'عالی',
                'interpretation': 'حاشیه EBITDA بسیار قوی - شرکت جریان نقدی عملیاتی ممتازی دارد'
            }
        elif percentage >= 20:
            return {
                'level': 'خوب',
                'interpretation': 'حاشیه EBITDA مناسب - شرکت جریان نقدی عملیاتی خوبی دارد'
            }
        elif percentage >= 15:
            return {
                'level': 'متوسط',
                'interpretation': 'حاشیه EBITDA قابل قبول - شرکت جریان نقدی عملیاتی معقولی دارد'
            }
        elif percentage >= 10:
            return {
                'level': 'ضعیف',
                'interpretation': 'حاشیه EBITDA محدود - شرکت ممکن است با فشار بر جریان نقدی مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'حاشیه EBITDA بسیار پایین - شرکت در معرض ریسک نقدینگی قرار دارد'
            }
    
    def _calculate_operating_ratio(self, data: Dict) -> Dict[str, Any]:
        """محاسبه نسبت عملیاتی"""
        
        operating_expenses = data['income_statement']['operating_expenses']
        revenue = data['income_statement']['revenue']
        
        if revenue == 0:
            ratio = Decimal('0')
        else:
            ratio = operating_expenses / revenue
        
        assessment = self._assess_operating_ratio(ratio)
        
        return {
            'ratio': float(ratio),
            'percentage': float(ratio * 100),
            'formula': 'هزینه‌های عملیاتی / درآمد',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 85.0,
            'calculation_details': {
                'operating_expenses': float(operating_expenses),
                'revenue': float(revenue)
            }
        }
    
    def _assess_operating_ratio(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی نسبت عملیاتی"""
        
        percentage = float(ratio * 100)
        
        if percentage <= 70:
            return {
                'level': 'عالی',
                'interpretation': 'نسبت عملیاتی بسیار مطلوب - شرکت کنترل عالی بر هزینه‌های عملیاتی دارد'
            }
        elif percentage <= 80:
            return {
                'level': 'خوب',
                'interpretation': 'نسبت عملیاتی مناسب - شرکت کنترل خوبی بر هزینه‌های عملیاتی دارد'
            }
        elif percentage <= 90:
            return {
                'level': 'متوسط',
                'interpretation': 'نسبت عملیاتی قابل قبول - شرکت می‌تواند هزینه‌های عملیاتی را مدیریت کند'
            }
        elif percentage <= 95:
            return {
                'level': 'ضعیف',
                'interpretation': 'نسبت عملیاتی نامطلوب - شرکت ممکن است با فشار هزینه‌های عملیاتی مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'نسبت عملیاتی بسیار نامطلوب - شرکت در معرض ریسک زیان عملیاتی قرار دارد'
            }
    
    def _analyze_profitability_ratios(self, ratios: Dict, financial_data: Dict) -> Dict[str, Any]:
        """تحلیل جامع نسبت‌های سودآوری"""
        
        # ارزیابی کلی سودآوری
        overall_assessment = self._assess_overall_profitability(ratios)
        
        # شناسایی نقاط قوت و ضعف
        strengths = self._identify_profitability_strengths(ratios)
        weaknesses = self._identify_profitability_weaknesses(ratios)
        
        # تحلیل روند (در صورت وجود داده‌های تاریخی)
        trend_analysis = self._analyze_profitability_trend(ratios)
        
        return {
            'overall_assessment': overall_assessment,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'trend_analysis': trend_analysis,
            'risk_level': self._determine_profitability_risk_level(ratios)
        }
    
    def _assess_overall_profitability(self, ratios: Dict) -> Dict[str, Any]:
        """ارزیابی کلی سودآوری"""
        
        # امتیازدهی به هر نسبت
        scores = {
            'gross_profit_margin': self._score_profitability_ratio(ratios['gross_profit_margin']['percentage'], [30, 40, 50]),
            'operating_profit_margin': self._score_profitability_ratio(ratios['operating_profit_margin']['percentage'], [10, 15, 20]),
            'net_profit_margin': self._score_profitability_ratio(ratios['net_profit_margin']['percentage'], [5, 10, 15]),
            'return_on_assets': self._score_profitability_ratio(ratios['return_on_assets']['percentage'], [5, 8, 12]),
            'return_on_equity': self._score_profitability_ratio(ratios['return_on_equity']['percentage'], [10, 15, 20])
        }
        
        overall_score = sum(scores.values()) / len(scores)
        
        if overall_score >= 4.0:
            level = 'عالی'
            interpretation = 'سودآوری بسیار قوی - شرکت در موقعیت ممتازی از نظر سودآوری قرار دارد'
        elif overall_score >= 3.0:
            level = 'خوب'
            interpretation = 'سودآوری مناسب - شرکت سودآوری خوبی در تمام سطوح دارد'
        elif overall_score >= 2.0:
            level = 'متوسط'
            interpretation = 'سودآوری قابل قبول - شرکت می‌تواند سودآوری خود را حفظ کند'
        elif overall_score >= 1.0:
            level = 'ضعیف'
            interpretation = 'سودآوری نامناسب - شرکت ممکن است با چالش در سودآوری مواجه شود'
        else:
            level = 'بحرانی'
            interpretation = 'سودآوری بحرانی - شرکت در معرض ریسک زیان قرار دارد'
        
        return {
            'level': level,
            'score': overall_score,
            'interpretation': interpretation,
            'individual_scores': scores
        }
    
    def _score_profitability_ratio(self, value: float, thresholds: List[float]) -> float:
        """امتیازدهی به نسبت سودآوری (مقادیر بالاتر بهتر هستند)"""
        
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
    
    def _identify_profitability_strengths(self, ratios: Dict) -> List[str]:
        """شناسایی نقاط قوت سودآوری"""
        
        strengths = []
        
        if ratios['gross_profit_margin']['assessment'] in ['عالی', 'خوب']:
            strengths.append('حاشیه سود ناخالص قوی')
        
        if ratios['operating_profit_margin']['assessment'] in ['عالی', 'خوب']:
            strengths.append('کارایی عملیاتی بالا')
        
        if ratios['net_profit_margin']['assessment'] in ['عالی', 'خوب']:
            strengths.append('سودآوری کلی مناسب')
        
        if ratios['return_on_assets']['assessment'] in ['عالی', 'خوب']:
            strengths.append('استفاده کارآمد از دارایی‌ها')
        
        if ratios['return_on_equity']['assessment'] in ['عالی', 'خوب']:
            strengths.append('بازده سرمایه بالا')
        
        return strengths
    
    def _identify_profitability_weaknesses(self, ratios: Dict) -> List[str]:
        """شناسایی نقاط ضعف سودآوری"""
        
        weaknesses = []
        
        if ratios['gross_profit_margin']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('حاشیه سود ناخالص پایین')
        
        if ratios['operating_profit_margin']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('کارایی عملیاتی محدود')
        
        if ratios['net_profit_margin']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('سودآوری کلی ضعیف')
        
        if ratios['return_on_assets']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('استفاده ناکارآمد از دارایی‌ها')
        
        if ratios['return_on_equity']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('بازده سرمایه پایین')
        
        return weaknesses
    
    def _analyze_profitability_trend(self, ratios: Dict) -> Dict[str, Any]:
        """تحلیل روند سودآوری"""
        
        # این تحلیل نیاز به داده‌های تاریخی دارد
        # فعلاً تحلیل ساده ارائه می‌شود
        
        return {
            'trend': 'ثابت',  # نیاز به داده‌های تاریخی
            'improvement_areas': self._identify_profitability_improvement_areas(ratios),
            'historical_comparison': 'در دسترس نیست'  # نیاز به داده‌های تاریخی
        }
    
    def _identify_profitability_improvement_areas(self, ratios: Dict) -> List[str]:
        """شناسایی حوزه‌های بهبود سودآوری"""
        
        improvement_areas = []
        
        if ratios['gross_profit_margin']['percentage'] < 30:
            improvement_areas.append('بهبود حاشیه سود ناخالص')
        
        if ratios['operating_profit_margin']['percentage'] < 10:
            improvement_areas.append('بهبود کارایی عملیاتی')
        
        if ratios['net_profit_margin']['percentage'] < 5:
            improvement_areas.append('بهبود سودآوری کلی')
        
        if ratios['return_on_assets']['percentage'] < 5:
            improvement_areas.append('بهبود استفاده از دارایی‌ها')
        
        return improvement_areas
    
    def _determine_profitability_risk_level(self, ratios: Dict) -> str:
        """تعیین سطح ریسک سودآوری"""
        
        critical_ratios = 0
        weak_ratios = 0
        
        for ratio_name, ratio_data in ratios.items():
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
    
    def _generate_profitability_recommendations(self, ratios: Dict, analysis: Dict) -> List[Dict[str, Any]]:
        """تولید توصیه‌های بهبود سودآوری"""
        
        recommendations = []
        
        # توصیه‌های مبتنی بر نسبت‌ها
        if ratios['gross_profit_margin']['percentage'] < 30:
            recommendations.append({
                'priority': 'بالا',
                'category': 'حاشیه سود ناخالص',
                'recommendation': 'بهبود کنترل هزینه‌های تولید و افزایش قیمت‌گذاری',
                'action': 'بررسی فرآیندهای تولید و مذاکره با تامین‌کنندگان',
                'expected_impact': 'افزایش ۵-۱۰٪ حاشیه سود ناخالص'
            })
        
        if ratios['operating_profit_margin']['percentage'] < 10:
            recommendations.append({
                'priority': 'بالا',
                'category': 'کارایی عملیاتی',
                'recommendation': 'کاهش هزینه‌های عملیاتی و بهینه‌سازی فرآیندها',
                'action': 'بررسی ساختار سازمانی و حذف فعالیت‌های غیرضروری',
                'expected_impact': 'افزایش ۳-۷٪ حاشیه سود عملیاتی'
            })
        
        if ratios['return_on_assets']['percentage'] < 5:
            recommendations.append({
                'priority': 'متوسط',
                'category': 'کارایی دارایی‌ها',
                'recommendation': 'بهبود مدیریت دارایی‌ها و افزایش بهره‌وری',
                'action': 'بررسی گردش موجودی و مدیریت حساب‌های دریافتنی',
                'expected_impact': 'افزایش ۲-۵٪ بازده دارایی‌ها'
            })
        
        # توصیه‌های مبتنی بر تحلیل کلی
        if analysis['risk_level'] in ['بالا', 'بسیار بالا']:
            recommendations.append({
                'priority': 'فوری',
                'category': 'مدیریت ریسک',
                'recommendation': 'بازنگری مدل کسب‌وکار و استراتژی سودآوری',
                'action': 'تحلیل بازار، محصولات و کانال‌های توزیع',
                'expected_impact': 'کاهش ریسک سودآوری و بهبود پایداری'
            })
        
        return recommendations


# ابزار LangChain برای تحلیل نسبت‌های سودآوری
class ProfitabilityRatioTool:
    """ابزار تحلیل نسبت‌های سودآوری برای LangChain"""
    
    name = "profitability_ratios"
    description = "محاسبه و تحلیل نسبت‌های سودآوری و کارایی شرکت"
    
    def __init__(self):
        self.analyzer_class = ProfitabilityRatioAnalyzer
    
    def analyze_profitability(self, company_id: int, period_id: int) -> Dict:
        """تحلیل نسبت‌های سودآوری برای شرکت و دوره مشخص"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            analyzer = ProfitabilityRatioAnalyzer(company, period)
            result = analyzer.calculate_all_profitability_ratios()
            
            return {
                'success': True,
                'analysis': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
