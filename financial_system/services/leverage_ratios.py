# financial_system/services/leverage_ratios.py
"""
تسک ۶۲: ایجاد محاسبه نسبت‌های اهرمی
این سرویس برای محاسبه و تحلیل نسبت‌های اهرمی و ساختار سرمایه طراحی شده است.
"""

from typing import Dict, List, Any
from decimal import Decimal
from users.models import Company, FinancialPeriod, FinancialFile, Document


class LeverageRatioAnalyzer:
    """تحلیل‌گر نسبت‌های اهرمی"""
    
    def __init__(self, company: Company, period: FinancialPeriod):
        self.company = company
        self.period = period
    
    def calculate_all_leverage_ratios(self) -> Dict[str, Any]:
        """محاسبه تمام نسبت‌های اهرمی"""
        
        # جمع‌آوری داده‌های مورد نیاز
        financial_data = self._collect_financial_data()
        
        # محاسبه نسبت‌ها
        ratios = {
            'debt_ratio': self._calculate_debt_ratio(financial_data),
            'debt_to_equity_ratio': self._calculate_debt_to_equity_ratio(financial_data),
            'equity_multiplier': self._calculate_equity_multiplier(financial_data),
            'times_interest_earned': self._calculate_times_interest_earned(financial_data),
            'debt_service_coverage_ratio': self._calculate_debt_service_coverage_ratio(financial_data),
            'fixed_charge_coverage_ratio': self._calculate_fixed_charge_coverage_ratio(financial_data),
            'long_term_debt_to_equity': self._calculate_long_term_debt_to_equity(financial_data)
        }
        
        # تحلیل و ارزیابی
        analysis = self._analyze_leverage_ratios(ratios, financial_data)
        
        return {
            'company': self.company.name,
            'period': self.period.name,
            'financial_data': financial_data,
            'leverage_ratios': ratios,
            'analysis': analysis,
            'recommendations': self._generate_leverage_recommendations(ratios, analysis)
        }
    
    def _collect_financial_data(self) -> Dict[str, Any]:
        """جمع‌آوری داده‌های مالی مورد نیاز"""
        
        # این بخش باید با مدل‌های واقعی یکپارچه شود
        # فعلاً از داده‌های نمونه استفاده می‌کنیم
        
        return {
            'balance_sheet': {
                'total_assets': Decimal('10000000000'),  # 10 میلیارد
                'total_liabilities': Decimal('6000000000'),  # 6 میلیارد
                'total_equity': Decimal('4000000000'),  # 4 میلیارد
                'long_term_debt': Decimal('3000000000'),  # 3 میلیارد
                'short_term_debt': Decimal('1000000000'),  # 1 میلیارد
                'current_liabilities': Decimal('2000000000')  # 2 میلیارد
            },
            'income_statement': {
                'ebit': Decimal('1500000000'),  # 1.5 میلیارد
                'net_income': Decimal('900000000'),  # 900 میلیون
                'interest_expense': Decimal('300000000'),  # 300 میلیون
                'tax_expense': Decimal('300000000'),  # 300 میلیون
                'operating_income': Decimal('1800000000')  # 1.8 میلیارد
            },
            'cash_flow': {
                'operating_cash_flow': Decimal('1200000000'),  # 1.2 میلیارد
                'principal_payments': Decimal('400000000'),  # 400 میلیون
                'lease_payments': Decimal('100000000')  # 100 میلیون
            }
        }
    
    def _calculate_debt_ratio(self, data: Dict) -> Dict[str, Any]:
        """محاسبه نسبت بدهی"""
        
        total_liabilities = data['balance_sheet']['total_liabilities']
        total_assets = data['balance_sheet']['total_assets']
        
        if total_assets == 0:
            ratio = Decimal('0')
        else:
            ratio = total_liabilities / total_assets
        
        assessment = self._assess_debt_ratio(ratio)
        
        return {
            'ratio': float(ratio),
            'percentage': float(ratio * 100),
            'formula': 'کل بدهی‌ها / کل دارایی‌ها',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 0.6,
            'calculation_details': {
                'total_liabilities': float(total_liabilities),
                'total_assets': float(total_assets)
            }
        }
    
    def _assess_debt_ratio(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی نسبت بدهی"""
        
        ratio_float = float(ratio)
        
        if ratio_float <= 0.4:
            return {
                'level': 'عالی',
                'interpretation': 'ساختار سرمایه محافظه‌کارانه - شرکت وابستگی کمی به بدهی دارد'
            }
        elif ratio_float <= 0.6:
            return {
                'level': 'خوب',
                'interpretation': 'ساختار سرمایه متعادل - شرکت از ترکیب مناسبی از بدهی و سرمایه استفاده می‌کند'
            }
        elif ratio_float <= 0.8:
            return {
                'level': 'متوسط',
                'interpretation': 'ساختار سرمایه تهاجمی - شرکت وابستگی بالایی به بدهی دارد'
            }
        elif ratio_float <= 0.9:
            return {
                'level': 'ضعیف',
                'interpretation': 'ساختار سرمایه بسیار تهاجمی - شرکت در معرض ریسک مالی بالایی قرار دارد'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'ساختار سرمایه بحرانی - شرکت ممکن است با مشکلات مالی جدی مواجه شود'
            }
    
    def _calculate_debt_to_equity_ratio(self, data: Dict) -> Dict[str, Any]:
        """محاسبه نسبت بدهی به سرمایه"""
        
        total_liabilities = data['balance_sheet']['total_liabilities']
        total_equity = data['balance_sheet']['total_equity']
        
        if total_equity == 0:
            ratio = Decimal('0')
        else:
            ratio = total_liabilities / total_equity
        
        assessment = self._assess_debt_to_equity_ratio(ratio)
        
        return {
            'ratio': float(ratio),
            'formula': 'کل بدهی‌ها / کل حقوق صاحبان سهام',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 1.5,
            'calculation_details': {
                'total_liabilities': float(total_liabilities),
                'total_equity': float(total_equity)
            }
        }
    
    def _assess_debt_to_equity_ratio(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی نسبت بدهی به سرمایه"""
        
        ratio_float = float(ratio)
        
        if ratio_float <= 1.0:
            return {
                'level': 'عالی',
                'interpretation': 'اهرم مالی پایین - شرکت بیشتر از سرمایه خود استفاده می‌کند'
            }
        elif ratio_float <= 1.5:
            return {
                'level': 'خوب',
                'interpretation': 'اهرم مالی متعادل - شرکت از ترکیب مناسبی از بدهی و سرمایه استفاده می‌کند'
            }
        elif ratio_float <= 2.0:
            return {
                'level': 'متوسط',
                'interpretation': 'اهرم مالی بالا - شرکت وابستگی بیشتری به بدهی دارد'
            }
        elif ratio_float <= 3.0:
            return {
                'level': 'ضعیف',
                'interpretation': 'اهرم مالی بسیار بالا - شرکت در معرض ریسک مالی قرار دارد'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'اهرم مالی بحرانی - شرکت ممکن است با مشکلات بازپرداخت بدهی مواجه شود'
            }
    
    def _calculate_equity_multiplier(self, data: Dict) -> Dict[str, Any]:
        """محاسبه ضریب سرمایه"""
        
        total_assets = data['balance_sheet']['total_assets']
        total_equity = data['balance_sheet']['total_equity']
        
        if total_equity == 0:
            ratio = Decimal('0')
        else:
            ratio = total_assets / total_equity
        
        assessment = self._assess_equity_multiplier(ratio)
        
        return {
            'ratio': float(ratio),
            'formula': 'کل دارایی‌ها / کل حقوق صاحبان سهام',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 2.5,
            'calculation_details': {
                'total_assets': float(total_assets),
                'total_equity': float(total_equity)
            }
        }
    
    def _assess_equity_multiplier(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی ضریب سرمایه"""
        
        ratio_float = float(ratio)
        
        if ratio_float <= 2.0:
            return {
                'level': 'عالی',
                'interpretation': 'اهرم مالی پایین - شرکت بیشتر از سرمایه خود استفاده می‌کند'
            }
        elif ratio_float <= 2.5:
            return {
                'level': 'خوب',
                'interpretation': 'اهرم مالی متعادل - شرکت از ترکیب مناسبی از بدهی و سرمایه استفاده می‌کند'
            }
        elif ratio_float <= 3.0:
            return {
                'level': 'متوسط',
                'interpretation': 'اهرم مالی بالا - شرکت وابستگی بیشتری به بدهی دارد'
            }
        elif ratio_float <= 4.0:
            return {
                'level': 'ضعیف',
                'interpretation': 'اهرم مالی بسیار بالا - شرکت در معرض ریسک مالی قرار دارد'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'اهرم مالی بحرانی - شرکت ممکن است با مشکلات مالی جدی مواجه شود'
            }
    
    def _calculate_times_interest_earned(self, data: Dict) -> Dict[str, Any]:
        """محاسبه نسبت پوشش بهره"""
        
        ebit = data['income_statement']['ebit']
        interest_expense = data['income_statement']['interest_expense']
        
        if interest_expense == 0:
            ratio = Decimal('0')
        else:
            ratio = ebit / interest_expense
        
        assessment = self._assess_times_interest_earned(ratio)
        
        return {
            'ratio': float(ratio),
            'formula': 'سود قبل از بهره و مالیات (EBIT) / هزینه بهره',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 3.0,
            'calculation_details': {
                'ebit': float(ebit),
                'interest_expense': float(interest_expense)
            }
        }
    
    def _assess_times_interest_earned(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی نسبت پوشش بهره"""
        
        ratio_float = float(ratio)
        
        if ratio_float >= 8.0:
            return {
                'level': 'عالی',
                'interpretation': 'توانایی بسیار بالا در پرداخت بهره - شرکت می‌تواند بهره را به راحتی پرداخت کند'
            }
        elif ratio_float >= 5.0:
            return {
                'level': 'خوب',
                'interpretation': 'توانایی مناسب در پرداخت بهره - شرکت می‌تواند بهره را پرداخت کند'
            }
        elif ratio_float >= 3.0:
            return {
                'level': 'متوسط',
                'interpretation': 'توانایی قابل قبول در پرداخت بهره - شرکت می‌تواند بهره را پرداخت کند'
            }
        elif ratio_float >= 1.5:
            return {
                'level': 'ضعیف',
                'interpretation': 'توانایی محدود در پرداخت بهره - شرکت ممکن است با مشکل پرداخت بهره مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'عدم توانایی در پرداخت بهره - شرکت نمی‌تواند بهره را پرداخت کند'
            }
    
    def _calculate_debt_service_coverage_ratio(self, data: Dict) -> Dict[str, Any]:
        """محاسبه نسبت پوشش خدمات بدهی"""
        
        operating_cash_flow = data['cash_flow']['operating_cash_flow']
        principal_payments = data['cash_flow']['principal_payments']
        interest_expense = data['income_statement']['interest_expense']
        
        total_debt_service = principal_payments + interest_expense
        
        if total_debt_service == 0:
            ratio = Decimal('0')
        else:
            ratio = operating_cash_flow / total_debt_service
        
        assessment = self._assess_debt_service_coverage_ratio(ratio)
        
        return {
            'ratio': float(ratio),
            'formula': 'جریان نقدی عملیاتی / (اصل بدهی + بهره)',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 1.2,
            'calculation_details': {
                'operating_cash_flow': float(operating_cash_flow),
                'principal_payments': float(principal_payments),
                'interest_expense': float(interest_expense),
                'total_debt_service': float(total_debt_service)
            }
        }
    
    def _assess_debt_service_coverage_ratio(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی نسبت پوشش خدمات بدهی"""
        
        ratio_float = float(ratio)
        
        if ratio_float >= 2.0:
            return {
                'level': 'عالی',
                'interpretation': 'توانایی بسیار بالا در پرداخت خدمات بدهی - شرکت می‌تواند خدمات بدهی را به راحتی پرداخت کند'
            }
        elif ratio_float >= 1.5:
            return {
                'level': 'خوب',
                'interpretation': 'توانایی مناسب در پرداخت خدمات بدهی - شرکت می‌تواند خدمات بدهی را پرداخت کند'
            }
        elif ratio_float >= 1.2:
            return {
                'level': 'متوسط',
                'interpretation': 'توانایی قابل قبول در پرداخت خدمات بدهی - شرکت می‌تواند خدمات بدهی را پرداخت کند'
            }
        elif ratio_float >= 1.0:
            return {
                'level': 'ضعیف',
                'interpretation': 'توانایی محدود در پرداخت خدمات بدهی - شرکت ممکن است با مشکل پرداخت مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'عدم توانایی در پرداخت خدمات بدهی - شرکت نمی‌تواند خدمات بدهی را پرداخت کند'
            }
    
    def _calculate_fixed_charge_coverage_ratio(self, data: Dict) -> Dict[str, Any]:
        """محاسبه نسبت پوشش هزینه‌های ثابت"""
        
        ebit = data['income_statement']['ebit']
        lease_payments = data['cash_flow']['lease_payments']
        interest_expense = data['income_statement']['interest_expense']
        
        fixed_charges = interest_expense + lease_payments
        
        if fixed_charges == 0:
            ratio = Decimal('0')
        else:
            ratio = (ebit + lease_payments) / fixed_charges
        
        assessment = self._assess_fixed_charge_coverage_ratio(ratio)
        
        return {
            'ratio': float(ratio),
            'formula': '(EBIT + اجاره) / (بهره + اجاره)',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 2.0,
            'calculation_details': {
                'ebit': float(ebit),
                'lease_payments': float(lease_payments),
                'interest_expense': float(interest_expense),
                'fixed_charges': float(fixed_charges)
            }
        }
    
    def _assess_fixed_charge_coverage_ratio(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی نسبت پوشش هزینه‌های ثابت"""
        
        ratio_float = float(ratio)
        
        if ratio_float >= 3.0:
            return {
                'level': 'عالی',
                'interpretation': 'توانایی بسیار بالا در پرداخت هزینه‌های ثابت - شرکت می‌تواند هزینه‌های ثابت را به راحتی پرداخت کند'
            }
        elif ratio_float >= 2.0:
            return {
                'level': 'خوب',
                'interpretation': 'توانایی مناسب در پرداخت هزینه‌های ثابت - شرکت می‌تواند هزینه‌های ثابت را پرداخت کند'
            }
        elif ratio_float >= 1.5:
            return {
                'level': 'متوسط',
                'interpretation': 'توانایی قابل قبول در پرداخت هزینه‌های ثابت - شرکت می‌تواند هزینه‌های ثابت را پرداخت کند'
            }
        elif ratio_float >= 1.0:
            return {
                'level': 'ضعیف',
                'interpretation': 'توانایی محدود در پرداخت هزینه‌های ثابت - شرکت ممکن است با مشکل پرداخت مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'عدم توانایی در پرداخت هزینه‌های ثابت - شرکت نمی‌تواند هزینه‌های ثابت را پرداخت کند'
            }
    
    def _calculate_long_term_debt_to_equity(self, data: Dict) -> Dict[str, Any]:
        """محاسبه نسبت بدهی بلندمدت به سرمایه"""
        
        long_term_debt = data['balance_sheet']['long_term_debt']
        total_equity = data['balance_sheet']['total_equity']
        
        if total_equity == 0:
            ratio = Decimal('0')
        else:
            ratio = long_term_debt / total_equity
        
        assessment = self._assess_long_term_debt_to_equity(ratio)
        
        return {
            'ratio': float(ratio),
            'formula': 'بدهی بلندمدت / کل حقوق صاحبان سهام',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 0.8,
            'calculation_details': {
                'long_term_debt': float(long_term_debt),
                'total_equity': float(total_equity)
            }
        }
    
    def _assess_long_term_debt_to_equity(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی نسبت بدهی بلندمدت به سرمایه"""
        
        ratio_float = float(ratio)
        
        if ratio_float <= 0.5:
            return {
                'level': 'عالی',
                'interpretation': 'ساختار بدهی بلندمدت محافظه‌کارانه - شرکت وابستگی کمی به بدهی بلندمدت دارد'
            }
        elif ratio_float <= 0.8:
            return {
                'level': 'خوب',
                'interpretation': 'ساختار بدهی بلندمدت متعادل - شرکت از ترکیب مناسبی از بدهی بلندمدت و سرمایه استفاده می‌کند'
            }
        elif ratio_float <= 1.2:
            return {
                'level': 'متوسط',
                'interpretation': 'ساختار بدهی بلندمدت تهاجمی - شرکت وابستگی بالایی به بدهی بلندمدت دارد'
            }
        elif ratio_float <= 2.0:
            return {
                'level': 'ضعیف',
                'interpretation': 'ساختار بدهی بلندمدت بسیار تهاجمی - شرکت در معرض ریسک مالی بالایی قرار دارد'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'ساختار بدهی بلندمدت بحرانی - شرکت ممکن است با مشکلات بازپرداخت بدهی بلندمدت مواجه شود'
            }
    
    def _analyze_leverage_ratios(self, ratios: Dict, financial_data: Dict) -> Dict[str, Any]:
        """تحلیل جامع نسبت‌های اهرمی"""
        
        # ارزیابی کلی اهرم مالی
        overall_assessment = self._assess_overall_leverage(ratios)
        
        # شناسایی نقاط قوت و ضعف
        strengths = self._identify_leverage_strengths(ratios)
        weaknesses = self._identify_leverage_weaknesses(ratios)
        
        # تحلیل روند (در صورت وجود داده‌های تاریخی)
        trend_analysis = self._analyze_leverage_trend(ratios)
        
        return {
            'overall_assessment': overall_assessment,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'trend_analysis': trend_analysis,
            'risk_level': self._determine_leverage_risk_level(ratios)
        }
    
    def _assess_overall_leverage(self, ratios: Dict) -> Dict[str, Any]:
        """ارزیابی کلی اهرم مالی"""
        
        # امتیازدهی به هر نسبت
        scores = {
            'debt_ratio': self._score_leverage_ratio(ratios['debt_ratio']['ratio'], [0.4, 0.6, 0.8]),
            'debt_to_equity': self._score_leverage_ratio(ratios['debt_to_equity_ratio']['ratio'], [1.0, 1.5, 2.0]),
            'times_interest_earned': self._score_coverage_ratio(ratios['times_interest_earned']['ratio'], [3.0, 5.0, 8.0]),
            'debt_service_coverage': self._score_coverage_ratio(ratios['debt_service_coverage_ratio']['ratio'], [1.2, 1.5, 2.0]),
            'fixed_charge_coverage': self._score_coverage_ratio(ratios['fixed_charge_coverage_ratio']['ratio'], [1.5, 2.0, 3.0])
        }
        
        overall_score = sum(scores.values()) / len(scores)
        
        if overall_score >= 4.0:
            level = 'عالی'
            interpretation = 'ساختار سرمایه بسیار قوی - شرکت در موقعیت ممتازی از نظر اهرم مالی قرار دارد'
        elif overall_score >= 3.0:
            level = 'خوب'
            interpretation = 'ساختار سرمایه مناسب - شرکت از ترکیب متعادلی از بدهی و سرمایه استفاده می‌کند'
        elif overall_score >= 2.0:
            level = 'متوسط'
            interpretation = 'ساختار سرمایه قابل قبول - شرکت می‌تواند بدهی‌های خود را مدیریت کند'
        elif overall_score >= 1.0:
            level = 'ضعیف'
            interpretation = 'ساختار سرمایه نامناسب - شرکت ممکن است با مشکلات اهرم مالی مواجه شود'
        else:
            level = 'بحرانی'
            interpretation = 'ساختار سرمایه بحرانی - شرکت در معرض ریسک مالی جدی قرار دارد'
        
        return {
            'level': level,
            'score': overall_score,
            'interpretation': interpretation,
            'individual_scores': scores
        }
    
    def _score_leverage_ratio(self, value: float, thresholds: List[float]) -> float:
        """امتیازدهی به نسبت اهرمی (مقادیر پایین‌تر بهتر هستند)"""
        
        if value <= thresholds[0]:
            return 5.0
        elif value <= thresholds[1]:
            return 4.0
        elif value <= thresholds[2]:
            return 3.0
        elif value <= thresholds[2] * 1.5:
            return 2.0
        elif value <= thresholds[2] * 2.0:
            return 1.0
        else:
            return 0.0
    
    def _score_coverage_ratio(self, value: float, thresholds: List[float]) -> float:
        """امتیازدهی به نسبت پوشش (مقادیر بالاتر بهتر هستند)"""
        
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
    
    def _identify_leverage_strengths(self, ratios: Dict) -> List[str]:
        """شناسایی نقاط قوت اهرمی"""
        
        strengths = []
        
        if ratios['debt_ratio']['assessment'] in ['عالی', 'خوب']:
            strengths.append('ساختار سرمایه متعادل')
        
        if ratios['times_interest_earned']['assessment'] in ['عالی', 'خوب']:
            strengths.append('توانایی بالا در پرداخت بهره')
        
        if ratios['debt_service_coverage_ratio']['assessment'] in ['عالی', 'خوب']:
            strengths.append('توانایی بالا در پرداخت خدمات بدهی')
        
        if ratios['fixed_charge_coverage_ratio']['assessment'] in ['عالی', 'خوب']:
            strengths.append('توانایی بالا در پرداخت هزینه‌های ثابت')
        
        return strengths
    
    def _identify_leverage_weaknesses(self, ratios: Dict) -> List[str]:
        """شناسایی نقاط ضعف اهرمی"""
        
        weaknesses = []
        
        if ratios['debt_ratio']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('وابستگی بالا به بدهی')
        
        if ratios['times_interest_earned']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('توانایی محدود در پرداخت بهره')
        
        if ratios['debt_service_coverage_ratio']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('توانایی محدود در پرداخت خدمات بدهی')
        
        if ratios['fixed_charge_coverage_ratio']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('توانایی محدود در پرداخت هزینه‌های ثابت')
        
        return weaknesses
    
    def _analyze_leverage_trend(self, ratios: Dict) -> Dict[str, Any]:
        """تحلیل روند اهرمی"""
        
        # این تحلیل نیاز به داده‌های تاریخی دارد
        # فعلاً تحلیل ساده ارائه می‌شود
        
        return {
            'trend': 'ثابت',  # نیاز به داده‌های تاریخی
            'improvement_areas': self._identify_leverage_improvement_areas(ratios),
            'historical_comparison': 'در دسترس نیست'  # نیاز به داده‌های تاریخی
        }
    
    def _identify_leverage_improvement_areas(self, ratios: Dict) -> List[str]:
        """شناسایی حوزه‌های بهبود اهرمی"""
        
        improvement_areas = []
        
        if ratios['debt_ratio']['ratio'] > 0.6:
            improvement_areas.append('کاهش وابستگی به بدهی')
        
        if ratios['times_interest_earned']['ratio'] < 3.0:
            improvement_areas.append('بهبود توانایی پرداخت بهره')
        
        if ratios['debt_service_coverage_ratio']['ratio'] < 1.2:
            improvement_areas.append('بهبود توانایی پرداخت خدمات بدهی')
        
        return improvement_areas
    
    def _determine_leverage_risk_level(self, ratios: Dict) -> str:
        """تعیین سطح ریسک اهرمی"""
        
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
    
    def _generate_leverage_recommendations(self, ratios: Dict, analysis: Dict) -> List[Dict[str, Any]]:
        """تولید توصیه‌های بهبود اهرمی"""
        
        recommendations = []
        
        # توصیه‌های مبتنی بر نسبت‌ها
        if ratios['debt_ratio']['ratio'] > 0.6:
            recommendations.append({
                'priority': 'بالا',
                'category': 'ساختار سرمایه',
                'recommendation': 'کاهش وابستگی به بدهی و افزایش سرمایه',
                'action': 'برنامه‌ریزی برای جذب سرمایه جدید و کاهش بدهی‌های غیرضروری',
                'expected_impact': 'کاهش نسبت بدهی به ۰.۶ یا کمتر'
            })
        
        if ratios['times_interest_earned']['ratio'] < 3.0:
            recommendations.append({
                'priority': 'بالا',
                'category': 'پوشش بهره',
                'recommendation': 'بهبود سودآوری عملیاتی برای افزایش پوشش بهره',
                'action': 'افزایش درآمدها و کاهش هزینه‌های غیرضروری',
                'expected_impact': 'افزایش نسبت پوشش بهره به ۳.۰ یا بیشتر'
            })
        
        if ratios['debt_service_coverage_ratio']['ratio'] < 1.2:
            recommendations.append({
                'priority': 'متوسط',
                'category': 'پوشش خدمات بدهی',
                'recommendation': 'بهبود جریان نقدی عملیاتی',
                'action': 'بهینه‌سازی مدیریت نقدینگی و دوره وصول',
                'expected_impact': 'افزایش نسبت پوشش خدمات بدهی به ۱.۲ یا بیشتر'
            })
        
        # توصیه‌های مبتنی بر تحلیل کلی
        if analysis['risk_level'] in ['بالا', 'بسیار بالا']:
            recommendations.append({
                'priority': 'فوری',
                'category': 'مدیریت ریسک',
                'recommendation': 'بازنگری ساختار سرمایه و برنامه کاهش بدهی',
                'action': 'تجدید ساختار بدهی و جذب سرمایه جدید',
                'expected_impact': 'کاهش ریسک مالی و بهبود پایداری'
            })
        
        return recommendations


# ابزار LangChain برای تحلیل نسبت‌های اهرمی
class LeverageRatioTool:
    """ابزار تحلیل نسبت‌های اهرمی برای LangChain"""
    
    name = "leverage_ratios"
    description = "محاسبه و تحلیل نسبت‌های اهرمی و ساختار سرمایه شرکت"
    
    def __init__(self):
        self.analyzer_class = LeverageRatioAnalyzer
    
    def analyze_leverage(self, company_id: int, period_id: int) -> Dict:
        """تحلیل نسبت‌های اهرمی برای شرکت و دوره مشخص"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            analyzer = LeverageRatioAnalyzer(company, period)
            result = analyzer.calculate_all_leverage_ratios()
            
            return {
                'success': True,
                'analysis': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
