# financial_system/services/activity_ratios.py
"""
تسک ۶۴: پیاده‌سازی محاسبه نسبت‌های فعالیت
این سرویس برای محاسبه و تحلیل نسبت‌های فعالیت و کارایی شرکت طراحی شده است.
"""

from typing import Dict, List, Any
from decimal import Decimal
from users.models import Company, FinancialPeriod, FinancialFile, Document


class ActivityRatioAnalyzer:
    """تحلیل‌گر نسبت‌های فعالیت"""
    
    def __init__(self, company: Company, period: FinancialPeriod):
        self.company = company
        self.period = period
    
    def calculate_all_activity_ratios(self) -> Dict[str, Any]:
        """محاسبه تمام نسبت‌های فعالیت"""
        
        # جمع‌آوری داده‌های مورد نیاز
        financial_data = self._collect_financial_data()
        
        # محاسبه نسبت‌ها
        ratios = {
            'inventory_turnover': self._calculate_inventory_turnover(financial_data),
            'days_inventory_outstanding': self._calculate_days_inventory_outstanding(financial_data),
            'receivables_turnover': self._calculate_receivables_turnover(financial_data),
            'days_sales_outstanding': self._calculate_days_sales_outstanding(financial_data),
            'payables_turnover': self._calculate_payables_turnover(financial_data),
            'days_payables_outstanding': self._calculate_days_payables_outstanding(financial_data),
            'cash_conversion_cycle': self._calculate_cash_conversion_cycle(financial_data),
            'asset_turnover': self._calculate_asset_turnover(financial_data),
            'fixed_asset_turnover': self._calculate_fixed_asset_turnover(financial_data),
            'working_capital_turnover': self._calculate_working_capital_turnover(financial_data)
        }
        
        # تحلیل و ارزیابی
        analysis = self._analyze_activity_ratios(ratios, financial_data)
        
        return {
            'company': self.company.name,
            'period': self.period.name,
            'financial_data': financial_data,
            'activity_ratios': ratios,
            'analysis': analysis,
            'recommendations': self._generate_activity_recommendations(ratios, analysis)
        }
    
    def _collect_financial_data(self) -> Dict[str, Any]:
        """جمع‌آوری داده‌های مالی مورد نیاز"""
        
        # این بخش باید با مدل‌های واقعی یکپارچه شود
        # فعلاً از داده‌های نمونه استفاده می‌کنیم
        
        return {
            'income_statement': {
                'revenue': Decimal('8000000000'),  # 8 میلیارد
                'cost_of_goods_sold': Decimal('5000000000'),  # 5 میلیارد
            },
            'balance_sheet': {
                'total_assets': Decimal('10000000000'),  # 10 میلیارد
                'fixed_assets': Decimal('7500000000'),  # 7.5 میلیارد
                'current_assets': Decimal('2500000000'),  # 2.5 میلیارد
                'inventory': Decimal('800000000'),  # 800 میلیون
                'accounts_receivable': Decimal('600000000'),  # 600 میلیون
                'accounts_payable': Decimal('400000000'),  # 400 میلیون
                'current_liabilities': Decimal('1500000000'),  # 1.5 میلیارد
            },
            'operating_data': {
                'average_inventory': Decimal('750000000'),  # 750 میلیون
                'average_receivables': Decimal('550000000'),  # 550 میلیون
                'average_payables': Decimal('380000000'),  # 380 میلیون
            }
        }
    
    def _calculate_inventory_turnover(self, data: Dict) -> Dict[str, Any]:
        """محاسبه گردش موجودی"""
        
        cost_of_goods_sold = data['income_statement']['cost_of_goods_sold']
        average_inventory = data['operating_data']['average_inventory']
        
        if average_inventory == 0:
            ratio = Decimal('0')
        else:
            ratio = cost_of_goods_sold / average_inventory
        
        assessment = self._assess_inventory_turnover(ratio)
        
        return {
            'ratio': float(ratio),
            'formula': 'بهای تمام شده کالای فروش رفته / میانگین موجودی',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 8.0,
            'calculation_details': {
                'cost_of_goods_sold': float(cost_of_goods_sold),
                'average_inventory': float(average_inventory)
            }
        }
    
    def _assess_inventory_turnover(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی گردش موجودی"""
        
        value = float(ratio)
        
        if value >= 12:
            return {
                'level': 'عالی',
                'interpretation': 'گردش موجودی بسیار بالا - شرکت مدیریت موجودی ممتازی دارد'
            }
        elif value >= 8:
            return {
                'level': 'خوب',
                'interpretation': 'گردش موجودی مناسب - شرکت مدیریت موجودی خوبی دارد'
            }
        elif value >= 5:
            return {
                'level': 'متوسط',
                'interpretation': 'گردش موجودی قابل قبول - شرکت می‌تواند موجودی را مدیریت کند'
            }
        elif value >= 3:
            return {
                'level': 'ضعیف',
                'interpretation': 'گردش موجودی محدود - شرکت ممکن است با انباشت موجودی مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'گردش موجودی بسیار پایین - شرکت در معرض ریسک موجودی‌های راکد قرار دارد'
            }
    
    def _calculate_days_inventory_outstanding(self, data: Dict) -> Dict[str, Any]:
        """محاسبه دوره گردش موجودی (روز)"""
        
        inventory_turnover = self._calculate_inventory_turnover(data)['ratio']
        
        if inventory_turnover == 0:
            days = Decimal('0')
        else:
            days = Decimal('365') / Decimal(str(inventory_turnover))
        
        assessment = self._assess_days_inventory_outstanding(days)
        
        return {
            'ratio': float(days),
            'formula': '۳۶۵ / گردش موجودی',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 45.0,
            'calculation_details': {
                'inventory_turnover': inventory_turnover
            }
        }
    
    def _assess_days_inventory_outstanding(self, days: Decimal) -> Dict[str, Any]:
        """ارزیابی دوره گردش موجودی"""
        
        value = float(days)
        
        if value <= 30:
            return {
                'level': 'عالی',
                'interpretation': 'دوره گردش موجودی بسیار کوتاه - شرکت مدیریت موجودی بسیار کارآمدی دارد'
            }
        elif value <= 45:
            return {
                'level': 'خوب',
                'interpretation': 'دوره گردش موجودی مناسب - شرکت مدیریت موجودی خوبی دارد'
            }
        elif value <= 60:
            return {
                'level': 'متوسط',
                'interpretation': 'دوره گردش موجودی قابل قبول - شرکت می‌تواند موجودی را مدیریت کند'
            }
        elif value <= 90:
            return {
                'level': 'ضعیف',
                'interpretation': 'دوره گردش موجودی طولانی - شرکت ممکن است با انباشت موجودی مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'دوره گردش موجودی بسیار طولانی - شرکت در معرض ریسک موجودی‌های راکد قرار دارد'
            }
    
    def _calculate_receivables_turnover(self, data: Dict) -> Dict[str, Any]:
        """محاسبه گردش حساب‌های دریافتنی"""
        
        revenue = data['income_statement']['revenue']
        average_receivables = data['operating_data']['average_receivables']
        
        if average_receivables == 0:
            ratio = Decimal('0')
        else:
            ratio = revenue / average_receivables
        
        assessment = self._assess_receivables_turnover(ratio)
        
        return {
            'ratio': float(ratio),
            'formula': 'فروش خالص / میانگین حساب‌های دریافتنی',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 10.0,
            'calculation_details': {
                'revenue': float(revenue),
                'average_receivables': float(average_receivables)
            }
        }
    
    def _assess_receivables_turnover(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی گردش حساب‌های دریافتنی"""
        
        value = float(ratio)
        
        if value >= 15:
            return {
                'level': 'عالی',
                'interpretation': 'گردش حساب‌های دریافتنی بسیار بالا - شرکت مدیریت اعتباری ممتازی دارد'
            }
        elif value >= 10:
            return {
                'level': 'خوب',
                'interpretation': 'گردش حساب‌های دریافتنی مناسب - شرکت مدیریت اعتباری خوبی دارد'
            }
        elif value >= 6:
            return {
                'level': 'متوسط',
                'interpretation': 'گردش حساب‌های دریافتنی قابل قبول - شرکت می‌تواند حساب‌های دریافتنی را مدیریت کند'
            }
        elif value >= 4:
            return {
                'level': 'ضعیف',
                'interpretation': 'گردش حساب‌های دریافتنی محدود - شرکت ممکن است با مشکل وصول مطالبات مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'گردش حساب‌های دریافتنی بسیار پایین - شرکت در معرض ریسک مطالبات معوق قرار دارد'
            }
    
    def _calculate_days_sales_outstanding(self, data: Dict) -> Dict[str, Any]:
        """محاسبه دوره وصول مطالبات (روز)"""
        
        receivables_turnover = self._calculate_receivables_turnover(data)['ratio']
        
        if receivables_turnover == 0:
            days = Decimal('0')
        else:
            days = Decimal('365') / Decimal(str(receivables_turnover))
        
        assessment = self._assess_days_sales_outstanding(days)
        
        return {
            'ratio': float(days),
            'formula': '۳۶۵ / گردش حساب‌های دریافتنی',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 36.0,
            'calculation_details': {
                'receivables_turnover': receivables_turnover
            }
        }
    
    def _assess_days_sales_outstanding(self, days: Decimal) -> Dict[str, Any]:
        """ارزیابی دوره وصول مطالبات"""
        
        value = float(days)
        
        if value <= 30:
            return {
                'level': 'عالی',
                'interpretation': 'دوره وصول مطالبات بسیار کوتاه - شرکت مدیریت اعتباری بسیار کارآمدی دارد'
            }
        elif value <= 45:
            return {
                'level': 'خوب',
                'interpretation': 'دوره وصول مطالبات مناسب - شرکت مدیریت اعتباری خوبی دارد'
            }
        elif value <= 60:
            return {
                'level': 'متوسط',
                'interpretation': 'دوره وصول مطالبات قابل قبول - شرکت می‌تواند مطالبات را مدیریت کند'
            }
        elif value <= 90:
            return {
                'level': 'ضعیف',
                'interpretation': 'دوره وصول مطالبات طولانی - شرکت ممکن است با مشکل وصول مطالبات مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'دوره وصول مطالبات بسیار طولانی - شرکت در معرض ریسک مطالبات معوق قرار دارد'
            }
    
    def _calculate_payables_turnover(self, data: Dict) -> Dict[str, Any]:
        """محاسبه گردش حساب‌های پرداختنی"""
        
        cost_of_goods_sold = data['income_statement']['cost_of_goods_sold']
        average_payables = data['operating_data']['average_payables']
        
        if average_payables == 0:
            ratio = Decimal('0')
        else:
            ratio = cost_of_goods_sold / average_payables
        
        assessment = self._assess_payables_turnover(ratio)
        
        return {
            'ratio': float(ratio),
            'formula': 'بهای تمام شده کالای فروش رفته / میانگین حساب‌های پرداختنی',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 8.0,
            'calculation_details': {
                'cost_of_goods_sold': float(cost_of_goods_sold),
                'average_payables': float(average_payables)
            }
        }
    
    def _assess_payables_turnover(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی گردش حساب‌های پرداختنی"""
        
        value = float(ratio)
        
        if value <= 6:
            return {
                'level': 'عالی',
                'interpretation': 'گردش حساب‌های پرداختنی بسیار پایین - شرکت از شرایط اعتباری ممتازی برخوردار است'
            }
        elif value <= 8:
            return {
                'level': 'خوب',
                'interpretation': 'گردش حساب‌های پرداختنی مناسب - شرکت از شرایط اعتباری خوبی برخوردار است'
            }
        elif value <= 10:
            return {
                'level': 'متوسط',
                'interpretation': 'گردش حساب‌های پرداختنی قابل قبول - شرکت می‌تواند حساب‌های پرداختنی را مدیریت کند'
            }
        elif value <= 12:
            return {
                'level': 'ضعیف',
                'interpretation': 'گردش حساب‌های پرداختنی بالا - شرکت ممکن است با فشار پرداخت مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'گردش حساب‌های پرداختنی بسیار بالا - شرکت در معرض ریسک نقدینگی قرار دارد'
            }
    
    def _calculate_days_payables_outstanding(self, data: Dict) -> Dict[str, Any]:
        """محاسبه دوره پرداخت بدهی‌ها (روز)"""
        
        payables_turnover = self._calculate_payables_turnover(data)['ratio']
        
        if payables_turnover == 0:
            days = Decimal('0')
        else:
            days = Decimal('365') / Decimal(str(payables_turnover))
        
        assessment = self._assess_days_payables_outstanding(days)
        
        return {
            'ratio': float(days),
            'formula': '۳۶۵ / گردش حساب‌های پرداختنی',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 45.0,
            'calculation_details': {
                'payables_turnover': payables_turnover
            }
        }
    
    def _assess_days_payables_outstanding(self, days: Decimal) -> Dict[str, Any]:
        """ارزیابی دوره پرداخت بدهی‌ها"""
        
        value = float(days)
        
        if value >= 60:
            return {
                'level': 'عالی',
                'interpretation': 'دوره پرداخت بدهی‌ها بسیار طولانی - شرکت از شرایط اعتباری ممتازی برخوردار است'
            }
        elif value >= 45:
            return {
                'level': 'خوب',
                'interpretation': 'دوره پرداخت بدهی‌ها مناسب - شرکت از شرایط اعتباری خوبی برخوردار است'
            }
        elif value >= 30:
            return {
                'level': 'متوسط',
                'interpretation': 'دوره پرداخت بدهی‌ها قابل قبول - شرکت می‌تواند حساب‌های پرداختنی را مدیریت کند'
            }
        elif value >= 15:
            return {
                'level': 'ضعیف',
                'interpretation': 'دوره پرداخت بدهی‌ها کوتاه - شرکت ممکن است با فشار پرداخت مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'دوره پرداخت بدهی‌ها بسیار کوتاه - شرکت در معرض ریسک نقدینگی قرار دارد'
            }
    
    def _calculate_cash_conversion_cycle(self, data: Dict) -> Dict[str, Any]:
        """محاسبه چرخه تبدیل نقدی"""
        
        dio = self._calculate_days_inventory_outstanding(data)['ratio']
        dso = self._calculate_days_sales_outstanding(data)['ratio']
        dpo = self._calculate_days_payables_outstanding(data)['ratio']
        
        ccc = Decimal(str(dio)) + Decimal(str(dso)) - Decimal(str(dpo))
        
        assessment = self._assess_cash_conversion_cycle(ccc)
        
        return {
            'ratio': float(ccc),
            'formula': 'دوره گردش موجودی + دوره وصول مطالبات - دوره پرداخت بدهی‌ها',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 45.0,
            'calculation_details': {
                'days_inventory_outstanding': dio,
                'days_sales_outstanding': dso,
                'days_payables_outstanding': dpo
            }
        }
    
    def _assess_cash_conversion_cycle(self, ccc: Decimal) -> Dict[str, Any]:
        """ارزیابی چرخه تبدیل نقدی"""
        
        value = float(ccc)
        
        if value <= 30:
            return {
                'level': 'عالی',
                'interpretation': 'چرخه تبدیل نقدی بسیار کوتاه - شرکت مدیریت کارایی عملیاتی ممتازی دارد'
            }
        elif value <= 45:
            return {
                'level': 'خوب',
                'interpretation': 'چرخه تبدیل نقدی مناسب - شرکت مدیریت کارایی عملیاتی خوبی دارد'
            }
        elif value <= 60:
            return {
                'level': 'متوسط',
                'interpretation': 'چرخه تبدیل نقدی قابل قبول - شرکت می‌تواند کارایی عملیاتی را مدیریت کند'
            }
        elif value <= 90:
            return {
                'level': 'ضعیف',
                'interpretation': 'چرخه تبدیل نقدی طولانی - شرکت ممکن است با فشار نقدینگی مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'چرخه تبدیل نقدی بسیار طولانی - شرکت در معرض ریسک نقدینگی جدی قرار دارد'
            }
    
    def _calculate_asset_turnover(self, data: Dict) -> Dict[str, Any]:
        """محاسبه گردش دارایی‌ها"""
        
        revenue = data['income_statement']['revenue']
        total_assets = data['balance_sheet']['total_assets']
        
        if total_assets == 0:
            ratio = Decimal('0')
        else:
            ratio = revenue / total_assets
        
        assessment = self._assess_asset_turnover(ratio)
        
        return {
            'ratio': float(ratio),
            'formula': 'فروش خالص / کل دارایی‌ها',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 0.8,
            'calculation_details': {
                'revenue': float(revenue),
                'total_assets': float(total_assets)
            }
        }
    
    def _assess_asset_turnover(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی گردش دارایی‌ها"""
        
        value = float(ratio)
        
        if value >= 1.2:
            return {
                'level': 'عالی',
                'interpretation': 'گردش دارایی‌ها بسیار بالا - شرکت استفاده بسیار کارآمدی از دارایی‌ها دارد'
            }
        elif value >= 0.8:
            return {
                'level': 'خوب',
                'interpretation': 'گردش دارایی‌ها مناسب - شرکت استفاده کارآمدی از دارایی‌ها دارد'
            }
        elif value >= 0.5:
            return {
                'level': 'متوسط',
                'interpretation': 'گردش دارایی‌ها قابل قبول - شرکت استفاده معقولی از دارایی‌ها دارد'
            }
        elif value >= 0.3:
            return {
                'level': 'ضعیف',
                'interpretation': 'گردش دارایی‌ها محدود - شرکت ممکن است با کارایی پایین دارایی‌ها مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'گردش دارایی‌ها بسیار پایین - شرکت استفاده ناکارآمدی از دارایی‌ها دارد'
            }
    
    def _calculate_fixed_asset_turnover(self, data: Dict) -> Dict[str, Any]:
        """محاسبه گردش دارایی‌های ثابت"""
        
        revenue = data['income_statement']['revenue']
        fixed_assets = data['balance_sheet']['fixed_assets']
        
        if fixed_assets == 0:
            ratio = Decimal('0')
        else:
            ratio = revenue / fixed_assets
        
        assessment = self._assess_fixed_asset_turnover(ratio)
        
        return {
            'ratio': float(ratio),
            'formula': 'فروش خالص / دارایی‌های ثابت',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 1.5,
            'calculation_details': {
                'revenue': float(revenue),
                'fixed_assets': float(fixed_assets)
            }
        }
    
    def _assess_fixed_asset_turnover(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی گردش دارایی‌های ثابت"""
        
        value = float(ratio)
        
        if value >= 2.0:
            return {
                'level': 'عالی',
                'interpretation': 'گردش دارایی‌های ثابت بسیار بالا - شرکت استفاده بسیار کارآمدی از دارایی‌های ثابت دارد'
            }
        elif value >= 1.5:
            return {
                'level': 'خوب',
                'interpretation': 'گردش دارایی‌های ثابت مناسب - شرکت استفاده کارآمدی از دارایی‌های ثابت دارد'
            }
        elif value >= 1.0:
            return {
                'level': 'متوسط',
                'interpretation': 'گردش دارایی‌های ثابت قابل قبول - شرکت استفاده معقولی از دارایی‌های ثابت دارد'
            }
        elif value >= 0.5:
            return {
                'level': 'ضعیف',
                'interpretation': 'گردش دارایی‌های ثابت محدود - شرکت ممکن است با کارایی پایین دارایی‌های ثابت مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'گردش دارایی‌های ثابت بسیار پایین - شرکت استفاده ناکارآمدی از دارایی‌های ثابت دارد'
            }
    
    def _calculate_working_capital_turnover(self, data: Dict) -> Dict[str, Any]:
        """محاسبه گردش سرمایه در گردش"""
        
        revenue = data['income_statement']['revenue']
        current_assets = data['balance_sheet']['current_assets']
        current_liabilities = data['balance_sheet']['current_liabilities']
        
        working_capital = current_assets - current_liabilities
        
        if working_capital == 0:
            ratio = Decimal('0')
        else:
            ratio = revenue / working_capital
        
        assessment = self._assess_working_capital_turnover(ratio)
        
        return {
            'ratio': float(ratio),
            'formula': 'فروش خالص / سرمایه در گردش',
            'interpretation': assessment['interpretation'],
            'assessment': assessment['level'],
            'industry_benchmark': 8.0,
            'calculation_details': {
                'revenue': float(revenue),
                'current_assets': float(current_assets),
                'current_liabilities': float(current_liabilities),
                'working_capital': float(working_capital)
            }
        }
    
    def _assess_working_capital_turnover(self, ratio: Decimal) -> Dict[str, Any]:
        """ارزیابی گردش سرمایه در گردش"""
        
        value = float(ratio)
        
        if value >= 12:
            return {
                'level': 'عالی',
                'interpretation': 'گردش سرمایه در گردش بسیار بالا - شرکت استفاده بسیار کارآمدی از سرمایه در گردش دارد'
            }
        elif value >= 8:
            return {
                'level': 'خوب',
                'interpretation': 'گردش سرمایه در گردش مناسب - شرکت استفاده کارآمدی از سرمایه در گردش دارد'
            }
        elif value >= 5:
            return {
                'level': 'متوسط',
                'interpretation': 'گردش سرمایه در گردش قابل قبول - شرکت استفاده معقولی از سرمایه در گردش دارد'
            }
        elif value >= 2:
            return {
                'level': 'ضعیف',
                'interpretation': 'گردش سرمایه در گردش محدود - شرکت ممکن است با کارایی پایین سرمایه در گردش مواجه شود'
            }
        else:
            return {
                'level': 'بحرانی',
                'interpretation': 'گردش سرمایه در گردش بسیار پایین - شرکت استفاده ناکارآمدی از سرمایه در گردش دارد'
            }
    
    def _analyze_activity_ratios(self, ratios: Dict, financial_data: Dict) -> Dict[str, Any]:
        """تحلیل جامع نسبت‌های فعالیت"""
        
        # ارزیابی کلی کارایی
        overall_assessment = self._assess_overall_activity(ratios)
        
        # شناسایی نقاط قوت و ضعف
        strengths = self._identify_activity_strengths(ratios)
        weaknesses = self._identify_activity_weaknesses(ratios)
        
        # تحلیل روند (در صورت وجود داده‌های تاریخی)
        trend_analysis = self._analyze_activity_trend(ratios)
        
        return {
            'overall_assessment': overall_assessment,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'trend_analysis': trend_analysis,
            'risk_level': self._determine_activity_risk_level(ratios)
        }
    
    def _assess_overall_activity(self, ratios: Dict) -> Dict[str, Any]:
        """ارزیابی کلی کارایی"""
        
        # امتیازدهی به هر نسبت
        scores = {
            'inventory_turnover': self._score_activity_ratio(ratios['inventory_turnover']['ratio'], [5, 8, 12]),
            'receivables_turnover': self._score_activity_ratio(ratios['receivables_turnover']['ratio'], [6, 10, 15]),
            'payables_turnover': self._score_activity_ratio(ratios['payables_turnover']['ratio'], [6, 8, 10], reverse=True),
            'cash_conversion_cycle': self._score_activity_ratio(ratios['cash_conversion_cycle']['ratio'], [30, 45, 60], reverse=True),
            'asset_turnover': self._score_activity_ratio(ratios['asset_turnover']['ratio'], [0.5, 0.8, 1.2])
        }
        
        overall_score = sum(scores.values()) / len(scores)
        
        if overall_score >= 4.0:
            level = 'عالی'
            interpretation = 'کارایی عملیاتی بسیار قوی - شرکت در مدیریت عملیات ممتاز است'
        elif overall_score >= 3.0:
            level = 'خوب'
            interpretation = 'کارایی عملیاتی مناسب - شرکت مدیریت عملیات خوبی دارد'
        elif overall_score >= 2.0:
            level = 'متوسط'
            interpretation = 'کارایی عملیاتی قابل قبول - شرکت می‌تواند عملیات را مدیریت کند'
        elif overall_score >= 1.0:
            level = 'ضعیف'
            interpretation = 'کارایی عملیاتی نامناسب - شرکت ممکن است با چالش در مدیریت عملیات مواجه شود'
        else:
            level = 'بحرانی'
            interpretation = 'کارایی عملیاتی بحرانی - شرکت در معرض ریسک عملیاتی قرار دارد'
        
        return {
            'level': level,
            'score': overall_score,
            'interpretation': interpretation,
            'individual_scores': scores
        }
    
    def _score_activity_ratio(self, value: float, thresholds: List[float], reverse: bool = False) -> float:
        """امتیازدهی به نسبت فعالیت"""
        
        if reverse:
            # برای نسبت‌هایی که مقادیر پایین‌تر بهتر هستند
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
        else:
            # برای نسبت‌هایی که مقادیر بالاتر بهتر هستند
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
    
    def _identify_activity_strengths(self, ratios: Dict) -> List[str]:
        """شناسایی نقاط قوت کارایی"""
        
        strengths = []
        
        if ratios['inventory_turnover']['assessment'] in ['عالی', 'خوب']:
            strengths.append('مدیریت موجودی قوی')
        
        if ratios['receivables_turnover']['assessment'] in ['عالی', 'خوب']:
            strengths.append('مدیریت اعتباری مناسب')
        
        if ratios['payables_turnover']['assessment'] in ['عالی', 'خوب']:
            strengths.append('شرایط اعتباری مطلوب')
        
        if ratios['cash_conversion_cycle']['assessment'] in ['عالی', 'خوب']:
            strengths.append('کارایی چرخه نقدی بالا')
        
        if ratios['asset_turnover']['assessment'] in ['عالی', 'خوب']:
            strengths.append('استفاده کارآمد از دارایی‌ها')
        
        return strengths
    
    def _identify_activity_weaknesses(self, ratios: Dict) -> List[str]:
        """شناسایی نقاط ضعف کارایی"""
        
        weaknesses = []
        
        if ratios['inventory_turnover']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('مدیریت موجودی ضعیف')
        
        if ratios['receivables_turnover']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('مدیریت اعتباری محدود')
        
        if ratios['payables_turnover']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('شرایط اعتباری نامطلوب')
        
        if ratios['cash_conversion_cycle']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('کارایی چرخه نقدی پایین')
        
        if ratios['asset_turnover']['assessment'] in ['ضعیف', 'بحرانی']:
            weaknesses.append('استفاده ناکارآمد از دارایی‌ها')
        
        return weaknesses
    
    def _analyze_activity_trend(self, ratios: Dict) -> Dict[str, Any]:
        """تحلیل روند کارایی"""
        
        # این تحلیل نیاز به داده‌های تاریخی دارد
        # فعلاً تحلیل ساده ارائه می‌شود
        
        return {
            'trend': 'ثابت',  # نیاز به داده‌های تاریخی
            'improvement_areas': self._identify_activity_improvement_areas(ratios),
            'historical_comparison': 'در دسترس نیست'  # نیاز به داده‌های تاریخی
        }
    
    def _identify_activity_improvement_areas(self, ratios: Dict) -> List[str]:
        """شناسایی حوزه‌های بهبود کارایی"""
        
        improvement_areas = []
        
        if ratios['inventory_turnover']['ratio'] < 5:
            improvement_areas.append('بهبود گردش موجودی')
        
        if ratios['receivables_turnover']['ratio'] < 6:
            improvement_areas.append('بهبود وصول مطالبات')
        
        if ratios['cash_conversion_cycle']['ratio'] > 60:
            improvement_areas.append('کاهش چرخه تبدیل نقدی')
        
        if ratios['asset_turnover']['ratio'] < 0.5:
            improvement_areas.append('بهبود استفاده از دارایی‌ها')
        
        return improvement_areas
    
    def _determine_activity_risk_level(self, ratios: Dict) -> str:
        """تعیین سطح ریسک کارایی"""
        
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
    
    def _generate_activity_recommendations(self, ratios: Dict, analysis: Dict) -> List[Dict[str, Any]]:
        """تولید توصیه‌های بهبود کارایی"""
        
        recommendations = []
        
        # توصیه‌های مبتنی بر نسبت‌ها
        if ratios['inventory_turnover']['ratio'] < 5:
            recommendations.append({
                'priority': 'بالا',
                'category': 'مدیریت موجودی',
                'recommendation': 'بهبود گردش موجودی و کاهش دوره نگهداری کالا',
                'action': 'بررسی سطح سفارش مجدد و حذف موجودی‌های راکد',
                'expected_impact': 'افزایش ۲-۴ بار گردش موجودی'
            })
        
        if ratios['receivables_turnover']['ratio'] < 6:
            recommendations.append({
                'priority': 'بالا',
                'category': 'مدیریت اعتباری',
                'recommendation': 'بهبود وصول مطالبات و کاهش دوره وصول',
                'action': 'بررسی سیاست‌های اعتباری و پیگیری مطالبات معوق',
                'expected_impact': 'کاهش ۱۰-۲۰ روز دوره وصول مطالبات'
            })
        
        if ratios['cash_conversion_cycle']['ratio'] > 60:
            recommendations.append({
                'priority': 'متوسط',
                'category': 'کارایی نقدی',
                'recommendation': 'کاهش چرخه تبدیل نقدی و بهبود مدیریت نقدینگی',
                'action': 'بهینه‌سازی مدیریت موجودی، مطالبات و حساب‌های پرداختنی',
                'expected_impact': 'کاهش ۱۵-۳۰ روز چرخه تبدیل نقدی'
            })
        
        if ratios['asset_turnover']['ratio'] < 0.5:
            recommendations.append({
                'priority': 'متوسط',
                'category': 'کارایی دارایی‌ها',
                'recommendation': 'بهبود استفاده از دارایی‌ها و افزایش بهره‌وری',
                'action': 'بررسی دارایی‌های غیرضروری و افزایش فروش',
                'expected_impact': 'افزایش ۲۰-۴۰٪ گردش دارایی‌ها'
            })
        
        # توصیه‌های مبتنی بر تحلیل کلی
        if analysis['risk_level'] in ['بالا', 'بسیار بالا']:
            recommendations.append({
                'priority': 'فوری',
                'category': 'مدیریت عملیاتی',
                'recommendation': 'بازنگری فرآیندهای عملیاتی و بهبود کارایی',
                'action': 'تحلیل فرآیندهای اصلی و شناسایی گلوگاه‌ها',
                'expected_impact': 'کاهش ریسک عملیاتی و بهبود کارایی کلی'
            })
        
        return recommendations


# ابزار LangChain برای تحلیل نسبت‌های فعالیت
class ActivityRatioTool:
    """ابزار تحلیل نسبت‌های فعالیت برای LangChain"""
    
    name = "activity_ratios"
    description = "محاسبه و تحلیل نسبت‌های فعالیت و کارایی شرکت"
    
    def __init__(self):
        self.analyzer_class = ActivityRatioAnalyzer
    
    def analyze_activity(self, company_id: int, period_id: int) -> Dict:
        """تحلیل نسبت‌های فعالیت برای شرکت و دوره مشخص"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            analyzer = ActivityRatioAnalyzer(company, period)
            result = analyzer.calculate_all_activity_ratios()
            
            return {
                'success': True,
                'analysis': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
