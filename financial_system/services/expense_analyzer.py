# financial_system/services/expense_analyzer.py
"""
تسک ۵۷: پیاده‌سازی تحلیل هزینه‌ها
این سرویس برای تحلیل حساب‌های هزینه‌ای طراحی شده است.
"""

from django.db.models import Sum, Q
from decimal import Decimal
from typing import Dict, List
from financial_system.models.document_models import DocumentHeader, DocumentItem
from financial_system.models.coding_models import ChartOfAccounts
from users.models import Company, FinancialPeriod


class ExpenseAnalyzer:
    """تحلیل‌گر حساب‌های هزینه‌ای"""
    
    def __init__(self, company: Company, period: FinancialPeriod):
        self.company = company
        self.period = period
        self.expense_account_codes = ['5']  # حساب‌های هزینه‌ای (معمولاً با ۵ شروع می‌شوند)
    
    def analyze_expenses(self) -> Dict:
        """تحلیل کامل حساب‌های هزینه‌ای"""
        
        total_expenses = self._calculate_total_expenses()
        expenses_by_type = self._analyze_expenses_by_type()
        monthly_trend = self._analyze_monthly_trend()
        expense_composition = self._analyze_expense_composition()
        cost_efficiency = self._analyze_cost_efficiency()
        budget_variance = self._analyze_budget_variance()
        
        return {
            'company': self.company.name,
            'period': self.period.name,
            'total_expenses': total_expenses,
            'expenses_by_type': expenses_by_type,
            'monthly_trend': monthly_trend,
            'expense_composition': expense_composition,
            'cost_efficiency': cost_efficiency,
            'budget_variance': budget_variance,
            'recommendations': self._generate_recommendations(total_expenses, expenses_by_type, cost_efficiency)
        }
    
    def _calculate_total_expenses(self) -> Dict:
        """محاسبه کل هزینه‌ها"""
        expense_accounts = ChartOfAccounts.objects.filter(
            code__startswith='5',
            is_active=True
        )
        
        total_expenses = Decimal('0')
        expense_details = {}
        
        for account in expense_accounts:
            items = DocumentItem.objects.filter(
                account=account,
                document__company=self.company,
                document__period=self.period
            )
            
            # برای حساب‌های هزینه‌ای: هزینه = بدهکار - بستانکار
            account_debit = items.aggregate(total=Sum('debit'))['total'] or Decimal('0')
            account_credit = items.aggregate(total=Sum('credit'))['total'] or Decimal('0')
            account_expense = account_debit - account_credit
            
            expense_details[account.code] = {
                'account_name': account.name,
                'expense': account_expense,
                'transaction_count': items.count()
            }
            
            total_expenses += account_expense
        
        return {
            'total': total_expenses,
            'details': expense_details
        }
    
    def _analyze_expenses_by_type(self) -> Dict:
        """تحلیل هزینه‌ها بر اساس نوع"""
        expense_types = {
            'هزینه‌های عملیاتی': ['51', '52'],  # بهای تمام شده، هزینه‌های فروش
            'هزینه‌های اداری': ['53'],          # هزینه‌های عمومی و اداری
            'هزینه‌های مالی': ['54'],           # هزینه‌های مالی
            'سایر هزینه‌ها': ['55', '56']       # سایر هزینه‌های عملیاتی و غیرعملیاتی
        }
        
        analysis = {}
        total = Decimal('0')
        
        for expense_type, codes in expense_types.items():
            type_expense = Decimal('0')
            type_details = {}
            
            for code_prefix in codes:
                accounts = ChartOfAccounts.objects.filter(
                    code__startswith=code_prefix,
                    is_active=True
                )
                
                for account in accounts:
                    items = DocumentItem.objects.filter(
                        account=account,
                        document__company=self.company,
                        document__period=self.period
                    )
                    
                    account_debit = items.aggregate(total=Sum('debit'))['total'] or Decimal('0')
                    account_credit = items.aggregate(total=Sum('credit'))['total'] or Decimal('0')
                    account_expense = account_debit - account_credit
                    
                    type_details[account.code] = {
                        'account_name': account.name,
                        'expense': account_expense
                    }
                    
                    type_expense += account_expense
            
            analysis[expense_type] = {
                'total': type_expense,
                'percentage': (type_expense / total * 100) if total > 0 else Decimal('0'),
                'details': type_details
            }
            
            total += type_expense
        
        # محاسبه درصدها
        for expense_type in analysis:
            if total > 0:
                analysis[expense_type]['percentage'] = (analysis[expense_type]['total'] / total * 100)
        
        analysis['total'] = total
        return analysis
    
    def _analyze_monthly_trend(self) -> Dict:
        """تحلیل روند ماهانه هزینه‌ها"""
        expense_accounts = ChartOfAccounts.objects.filter(
            code__startswith='5',
            is_active=True
        )
        
        monthly_data = {}
        
        for account in expense_accounts:
            items = DocumentItem.objects.filter(
                account=account,
                document__company=self.company,
                document__period=self.period
            ).select_related('document')
            
            for item in items:
                month_key = item.document.document_date.strftime('%Y-%m')
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        'expense': Decimal('0'),
                        'transactions': 0
                    }
                
                # برای هزینه: بدهکار منهای بستانکار
                monthly_data[month_key]['expense'] += (item.debit - item.credit)
                monthly_data[month_key]['transactions'] += 1
        
        # مرتب‌سازی بر اساس ماه
        sorted_months = sorted(monthly_data.keys())
        trend_analysis = {
            'monthly_data': {month: monthly_data[month] for month in sorted_months},
            'growth_rate': self._calculate_growth_rate(monthly_data),
            'seasonality': self._analyze_seasonality(monthly_data)
        }
        
        return trend_analysis
    
    def _calculate_growth_rate(self, monthly_data: Dict) -> Decimal:
        """محاسبه نرخ رشد هزینه‌ها"""
        if len(monthly_data) < 2:
            return Decimal('0')
        
        sorted_months = sorted(monthly_data.keys())
        first_month_expense = monthly_data[sorted_months[0]]['expense']
        last_month_expense = monthly_data[sorted_months[-1]]['expense']
        
        if first_month_expense > 0:
            growth_rate = ((last_month_expense - first_month_expense) / first_month_expense) * 100
            return growth_rate
        
        return Decimal('0')
    
    def _analyze_seasonality(self, monthly_data: Dict) -> Dict:
        """تحلیل فصلی بودن هزینه‌ها"""
        if len(monthly_data) < 3:
            return {'message': 'داده کافی برای تحلیل فصلی وجود ندارد'}
        
        # محاسبه میانگین ماهانه
        monthly_totals = [data['expense'] for data in monthly_data.values()]
        average_monthly = sum(monthly_totals) / len(monthly_totals)
        
        # شناسایی ماه‌های پیک و افت
        peak_month = max(monthly_data, key=lambda x: monthly_data[x]['expense'])
        low_month = min(monthly_data, key=lambda x: monthly_data[x]['expense'])
        
        peak_value = monthly_data[peak_month]['expense']
        low_value = monthly_data[low_month]['expense']
        
        return {
            'average_monthly': average_monthly,
            'peak_month': peak_month,
            'peak_value': peak_value,
            'low_month': low_month,
            'low_value': low_value,
            'seasonality_index': (peak_value - low_value) / average_monthly if average_monthly > 0 else Decimal('0')
        }
    
    def _analyze_expense_composition(self) -> Dict:
        """تحلیل ترکیب هزینه‌ها"""
        expenses_by_type = self._analyze_expenses_by_type()
        total_expenses = expenses_by_type['total']
        
        composition = {}
        for expense_type, data in expenses_by_type.items():
            if expense_type != 'total':
                composition[expense_type] = {
                    'amount': data['total'],
                    'percentage': (data['total'] / total_expenses * 100) if total_expenses > 0 else Decimal('0'),
                    'efficiency': self._assess_efficiency(expense_type, data['total'])
                }
        
        # تحلیل تمرکز هزینه
        concentration_analysis = self._analyze_expense_concentration(composition)
        
        return {
            'composition': composition,
            'concentration_analysis': concentration_analysis
        }
    
    def _assess_efficiency(self, expense_type: str, expense_amount: Decimal) -> str:
        """ارزیابی کارایی هزینه"""
        # این یک ارزیابی نمونه است - در نسخه کامل باید با استانداردهای صنعت مقایسه شود
        efficiency_thresholds = {
            'هزینه‌های عملیاتی': Decimal('1000000000'),  # 1 میلیارد
            'هزینه‌های اداری': Decimal('500000000'),     # 500 میلیون
            'هزینه‌های مالی': Decimal('200000000'),      # 200 میلیون
            'سایر هزینه‌ها': Decimal('100000000')        # 100 میلیون
        }
        
        threshold = efficiency_thresholds.get(expense_type, Decimal('0'))
        
        if expense_amount == 0:
            return "بدون هزینه"
        elif expense_amount > threshold * Decimal('1.5'):
            return "کارایی بسیار پایین"
        elif expense_amount > threshold:
            return "کارایی پایین"
        elif expense_amount > threshold * Decimal('0.7'):
            return "کارایی متوسط"
        else:
            return "کارایی بالا"
    
    def _analyze_expense_concentration(self, composition: Dict) -> Dict:
        """تحلیل تمرکز هزینه"""
        if not composition:
            return {'message': 'داده‌ای برای تحلیل وجود ندارد'}
        
        # محاسبه شاخص هرفیندال-هیرشمن (HHI)
        hhi_index = Decimal('0')
        for expense_type, data in composition.items():
            percentage = data['percentage'] / 100  # تبدیل به کسر
            hhi_index += percentage * percentage
        
        # ارزیابی شاخص HHI
        if hhi_index > Decimal('0.25'):
            concentration_level = "تمرکز بسیار بالا"
        elif hhi_index > Decimal('0.18'):
            concentration_level = "تمرکز بالا"
        elif hhi_index > Decimal('0.15'):
            concentration_level = "تمرکز متوسط"
        else:
            concentration_level = "تمرکز پایین"
        
        # شناسایی بزرگترین نوع هزینه
        largest_category = max(composition.items(), key=lambda x: x[1]['amount'])
        
        return {
            'hhi_index': hhi_index,
            'concentration_level': concentration_level,
            'largest_category': {
                'type': largest_category[0],
                'percentage': largest_category[1]['percentage'],
                'amount': largest_category[1]['amount'],
                'efficiency': largest_category[1]['efficiency']
            },
            'diversification_score': (1 - hhi_index) * 100  # امتیاز تنوع
        }
    
    def _analyze_cost_efficiency(self) -> Dict:
        """تحلیل کارایی هزینه"""
        total_expenses = self._calculate_total_expenses()['total']
        total_revenue = self._get_total_revenue()
        
        efficiency_ratios = {}
        
        # نسبت هزینه به درآمد
        if total_revenue > 0:
            efficiency_ratios['expense_to_revenue_ratio'] = (total_expenses / total_revenue) * 100
        else:
            efficiency_ratios['expense_to_revenue_ratio'] = Decimal('0')
        
        # تحلیل انواع هزینه
        expenses_by_type = self._analyze_expenses_by_type()
        type_efficiency = {}
        
        for expense_type, data in expenses_by_type.items():
            if expense_type != 'total':
                if total_revenue > 0:
                    type_ratio = (data['total'] / total_revenue) * 100
                else:
                    type_ratio = Decimal('0')
                
                type_efficiency[expense_type] = {
                    'ratio': type_ratio,
                    'assessment': self._assess_cost_ratio(expense_type, type_ratio)
                }
        
        return {
            'total_expenses': total_expenses,
            'total_revenue': total_revenue,
            'efficiency_ratios': efficiency_ratios,
            'type_efficiency': type_efficiency,
            'overall_efficiency': self._assess_overall_efficiency(efficiency_ratios['expense_to_revenue_ratio'])
        }
    
    def _get_total_revenue(self) -> Decimal:
        """دریافت کل درآمدها"""
        # این یک نمونه ساده است - در نسخه کامل باید از RevenueAnalyzer استفاده شود
        revenue_accounts = ChartOfAccounts.objects.filter(
            code__startswith='4',
            is_active=True
        )
        
        total_revenue = Decimal('0')
        for account in revenue_accounts:
            items = DocumentItem.objects.filter(
                account=account,
                document__company=self.company,
                document__period=self.period
            )
            
            account_debit = items.aggregate(total=Sum('debit'))['total'] or Decimal('0')
            account_credit = items.aggregate(total=Sum('credit'))['total'] or Decimal('0')
            account_revenue = account_credit - account_debit
            total_revenue += account_revenue
        
        return total_revenue
    
    def _assess_cost_ratio(self, expense_type: str, ratio: Decimal) -> str:
        """ارزیابی نسبت هزینه"""
        # این استانداردهای نمونه هستند - باید با صنعت تطبیق داده شوند
        standard_ratios = {
            'هزینه‌های عملیاتی': Decimal('60'),  # 60%
            'هزینه‌های اداری': Decimal('15'),    # 15%
            'هزینه‌های مالی': Decimal('5'),      # 5%
            'سایر هزینه‌ها': Decimal('5')        # 5%
        }
        
        standard = standard_ratios.get(expense_type, Decimal('0'))
        
        if ratio == 0:
            return "بدون هزینه"
        elif ratio > standard * Decimal('1.3'):
            return "بیش از حد استاندارد"
        elif ratio > standard * Decimal('1.1'):
            return "بالاتر از استاندارد"
        elif ratio > standard * Decimal('0.9'):
            return "در محدوده استاندارد"
        else:
            return "پایین‌تر از استاندارد"
    
    def _assess_overall_efficiency(self, expense_ratio: Decimal) -> str:
        """ارزیابی کارایی کلی"""
        if expense_ratio == 0:
            return "بدون هزینه"
        elif expense_ratio > 80:
            return "کارایی بسیار پایین"
        elif expense_ratio > 60:
            return "کارایی پایین"
        elif expense_ratio > 40:
            return "کارایی متوسط"
        else:
            return "کارایی بالا"
    
    def _analyze_budget_variance(self) -> Dict:
        """تحلیل انحراف از بودجه"""
        # این تحلیل نیاز به داده‌های بودجه دارد
        # فعلاً ساختار پایه ایجاد می‌شود
        total_expenses = self._calculate_total_expenses()['total']
        
        return {
            'actual_expenses': total_expenses,
            'budgeted_expenses': self._get_budgeted_expenses(),
            'variance_analysis': self._calculate_variance(total_expenses),
            'budget_compliance': self._assess_budget_compliance(total_expenses)
        }
    
    def _get_budgeted_expenses(self) -> Decimal:
        """دریافت بودجه هزینه‌ها"""
        # این یک نمونه ساده است - در نسخه کامل باید از سیستم بودجه‌بندی استفاده شود
        return Decimal('0')  # فعلاً بودجه صفر فرض می‌شود
    
    def _calculate_variance(self, actual_expenses: Decimal) -> Dict:
        """محاسبه انحراف از بودجه"""
        budgeted_expenses = self._get_budgeted_expenses()
        
        if budgeted_expenses == 0:
            return {
                'variance_amount': Decimal('0'),
                'variance_percentage': Decimal('0'),
                'message': 'بودجه تعریف نشده است'
            }
        
        variance_amount = actual_expenses - budgeted_expenses
        variance_percentage = (variance_amount / budgeted_expenses) * 100
        
        return {
            'variance_amount': variance_amount,
            'variance_percentage': variance_percentage,
            'is_favorable': variance_amount < 0  # هزینه کمتر از بودجه مطلوب است
        }
    
    def _assess_budget_compliance(self, actual_expenses: Decimal) -> str:
        """ارزیابی انطباق با بودجه"""
        variance = self._calculate_variance(actual_expenses)
        
        if 'message' in variance:
            return "بودجه تعریف نشده"
        
        variance_percentage = abs(variance['variance_percentage'])
        
        if variance_percentage > 20:
            return "انحراف شدید از بودجه"
        elif variance_percentage > 10:
            return "انحراف قابل توجه"
        elif variance_percentage > 5:
            return "انحراف جزئی"
        else:
            return "مطابق با بودجه"
