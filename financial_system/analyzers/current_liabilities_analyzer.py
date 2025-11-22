# financial_system/analyzers/current_liabilities_analyzer.py
from django.db.models import Sum, Q
from financial_system.models import DocumentItem, ChartOfAccounts
from decimal import Decimal
from typing import Dict, List, Any

class CurrentLiabilitiesAnalyzer:
    def __init__(self, company_id: int, period_id: int):
        self.company_id = company_id
        self.period_id = period_id
        self.current_liability_codes = ['31', '32', '33']  # کدهای بدهی‌های جاری
    
    def analyze_current_liabilities(self) -> Dict[str, Any]:
        """تحلیل جامع بدهی‌های جاری"""
        analysis = {
            'structure_analysis': self._analyze_structure(),
            'maturity_analysis': self._analyze_maturity(),
            'cost_analysis': self._analyze_costs(),
            'coverage_analysis': self._analyze_coverage(),
            'risk_assessment': self._assess_risks(),
            'recommendations': []
        }
        
        analysis['recommendations'] = self._generate_recommendations(analysis)
        return analysis
    
    def _analyze_structure(self) -> Dict[str, Any]:
        """تحلیل ساختار بدهی‌های جاری"""
        structure = {}
        total_current_liabilities = Decimal('0')
        
        for liability_code in self.current_liability_codes:
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=liability_code,
                is_active=True
            )
            
            for account in accounts:
                balance = abs(self._get_account_balance(account.code))  # بدهی‌ها معمولاً مانده بستانکار دارند
                structure[account.name] = {
                    'code': account.code,
                    'balance': balance,
                    'percentage': Decimal('0'),
                    'type': self._classify_liability_type(account.code)
                }
                total_current_liabilities += balance
        
        # محاسبه درصد هر جزء
        for liability_name, data in structure.items():
            if total_current_liabilities > 0:
                data['percentage'] = (data['balance'] / total_current_liabilities) * 100
        
        return {
            'components': structure,
            'total_current_liabilities': total_current_liabilities,
            'structure_health': self._assess_structure_health(structure)
        }
    
    def _analyze_maturity(self) -> Dict[str, Any]:
        """تحلیل سررسید بدهی‌های جاری"""
        maturity_profile = {
            'within_30_days': Decimal('0'),
            '31_60_days': Decimal('0'),
            '61_90_days': Decimal('0'),
            'over_90_days': Decimal('0')
        }
        
        # این بخش نیاز به داده‌های تاریخ سررسید دارد
        # برای نمونه، مقادیر نمونه استفاده می‌شود
        maturity_profile = {
            'within_30_days': Decimal('40000000'),
            '31_60_days': Decimal('25000000'),
            '61_90_days': Decimal('15000000'),
            'over_90_days': Decimal('8000000'),
            'total': Decimal('88000000')
        }
        
        return {
            'maturity_profile': maturity_profile,
            'immediate_pressure': maturity_profile['within_30_days'],
            'pressure_ratio': maturity_profile['within_30_days'] / maturity_profile['total'] 
                            if maturity_profile['total'] > 0 else Decimal('0')
        }
    
    def _analyze_costs(self) -> Dict[str, Any]:
        """تحلیل هزینه‌های بدهی‌های جاری"""
        interest_bearing_liabilities = ['311', '312']  # تسهیلات، وام‌های کوتاه مدت
        total_interest_bearing = Decimal('0')
        estimated_interest_cost = Decimal('0')
        
        for code in interest_bearing_liabilities:
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=code,
                is_active=True
            )
            for account in accounts:
                balance = abs(self._get_account_balance(account.code))
                total_interest_bearing += balance
                # فرض نرخ سود ۱۵٪ سالانه
                estimated_interest_cost += balance * Decimal('0.15') / Decimal('12')
        
        return {
            'interest_bearing_liabilities': total_interest_bearing,
            'estimated_monthly_interest': estimated_interest_cost,
            'interest_coverage': self._calculate_interest_coverage(estimated_interest_cost),
            'cost_of_debt': Decimal('15.0')  # نرخ سود فرضی
        }
    
    def _analyze_coverage(self) -> Dict[str, Any]:
        """تحلیل پوشش بدهی‌های جاری"""
        current_assets = self._get_current_assets()
        current_liabilities = self._get_total_current_liabilities()
        operating_cash_flow = self._estimate_operating_cash_flow()
        
        return {
            'current_ratio': current_assets / current_liabilities if current_liabilities > 0 else Decimal('0'),
            'quick_ratio': (self._get_quick_assets() / current_liabilities) if current_liabilities > 0 else Decimal('0'),
            'cash_flow_coverage': (operating_cash_flow / current_liabilities) if current_liabilities > 0 else Decimal('0'),
            'working_capital': current_assets - current_liabilities
        }
    
    def _assess_risks(self) -> List[Dict[str, Any]]:
        """ارزیابی ریسک‌های بدهی‌های جاری"""
        risks = []
        
        coverage = self._analyze_coverage()
        if coverage['current_ratio'] < Decimal('1.0'):
            risks.append({
                'type': 'LIQUIDITY_RISK',
                'severity': 'HIGH',
                'description': 'نسبت جاری کمتر از ۱ نشان‌دهنده ریسک نقدینگی است',
                'current_ratio': coverage['current_ratio'],
                'recommendation': 'کاهش بدهی‌های جاری یا افزایش دارایی‌های جاری'
            })
        
        maturity = self._analyze_maturity()
        if maturity['pressure_ratio'] > Decimal('0.4'):
            risks.append({
                'type': 'MATURITY_RISK',
                'severity': 'MEDIUM',
                'description': 'تمرکز بالای بدهی‌های با سررسید کوتاه‌مدت',
                'pressure_ratio': maturity['pressure_ratio'],
                'recommendation': 'تعدیل ساختار سررسید بدهی‌ها'
            })
        
        costs = self._analyze_costs()
        if costs['interest_coverage'] < Decimal('3.0'):
            risks.append({
                'type': 'INTEREST_RISK',
                'severity': 'MEDIUM',
                'description': 'توانایی کم برای پوشش هزینه‌های مالی',
                'interest_coverage': costs['interest_coverage'],
                'recommendation': 'بازنگری در ساختار تأمین مالی'
            })
        
        return risks
    
    def _get_account_balance(self, account_code: str) -> Decimal:
        """دریافت مانده یک حساب"""
        transactions = DocumentItem.objects.filter(
            document__company_id=self.company_id,
            document__period_id=self.period_id,
            account__code=account_code
        ).aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        
        debit = transactions['total_debit'] or Decimal('0')
        credit = transactions['total_credit'] or Decimal('0')
        
        # برای حساب‌های بدهی: مانده = بستانکار - بدهکار
        return credit - debit
    
    def _classify_liability_type(self, account_code: str) -> str:
        """طبقه‌بندی نوع بدهی"""
        type_mapping = {
            '311': 'تسهیلات مالی',
            '312': 'وام‌های کوتاه مدت',
            '321': 'حساب‌های پرداختنی',
            '322': 'اسناد پرداختنی',
            '331': 'پیش‌دریافت‌ها',
            '332': 'ذخایر'
        }
        
        for code_prefix, liability_type in type_mapping.items():
            if account_code.startswith(code_prefix):
                return liability_type
        
        return 'سایر بدهی‌ها'
    
    def _assess_structure_health(self, structure: Dict) -> str:
        """ارزیابی سلامت ساختار بدهی‌ها"""
        interest_bearing_ratio = sum(
            data['balance'] for data in structure.values() 
            if data['type'] in ['تسهیلات مالی', 'وام‌های کوتاه مدت']
        ) / sum(data['balance'] for data in structure.values()) if structure else Decimal('0')
        
        if interest_bearing_ratio > Decimal('0.6'):
            return 'HIGH_COST'
        elif interest_bearing_ratio > Decimal('0.4'):
            return 'MODERATE'
        else:
            return 'HEALTHY'
    
    def _get_current_assets(self) -> Decimal:
        """دریافت مجموع دارایی‌های جاری"""
        current_asset_codes = ['11', '12', '13']
        total_assets = Decimal('0')
        
        for code in current_asset_codes:
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=code,
                is_active=True
            )
            for account in accounts:
                total_assets += self._get_account_balance(account.code)
        
        return total_assets
    
    def _get_quick_assets(self) -> Decimal:
        """دریافت دارایی‌های سریع‌الوصول"""
        quick_asset_codes = ['111', '112', '121']  # صندوق، بانک، اسناد دریافتنی
        total_quick_assets = Decimal('0')
        
        for code in quick_asset_codes:
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=code,
                is_active=True
            )
            for account in accounts:
                total_quick_assets += self._get_account_balance(account.code)
        
        return total_quick_assets
    
    def _get_total_current_liabilities(self) -> Decimal:
        """دریافت مجموع بدهی‌های جاری"""
        total = Decimal('0')
        for liability_code in self.current_liability_codes:
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=liability_code,
                is_active=True
            )
            for account in accounts:
                total += abs(self._get_account_balance(account.code))
        
        return total
    
    def _estimate_operating_cash_flow(self) -> Decimal:
        """تخمین جریان نقدی عملیاتی"""
        # این یک تخمین ساده است - در عمل باید از صورت جریان وجوه نقد استفاده شود
        net_income = Decimal('120000000')  # سود خالص
        depreciation = Decimal('30000000')  # استهلاک
        changes_in_working_capital = Decimal('-15000000')  # تغییر در سرمایه در گردش
        
        return net_income + depreciation + changes_in_working_capital
    
    def _calculate_interest_coverage(self, estimated_interest: Decimal) -> Decimal:
        """محاسبه پوشش هزینه بهره"""
        if estimated_interest == 0:
            return Decimal('999')  # عدد بزرگ برای نشان دادن عدم وجود هزینه بهره
        
        ebit = Decimal('180000000')  # سود قبل از بهره و مالیات - باید از صورت سود و زیان گرفته شود
        return ebit / estimated_interest
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """تولید توصیه‌های مدیریتی"""
        recommendations = []
        
        # توصیه‌های مبتنی بر ریسک
        for risk in analysis['risk_assessment']:
            recommendations.append(risk['recommendation'])
        
        # توصیه‌های مبتنی بر ساختار
        structure = analysis['structure_analysis']
        if structure['structure_health'] == 'HIGH_COST':
            recommendations.append("کاهش سهم بدهی‌های دارای بهره در ساختار تأمین مالی")
        
        # توصیه‌های مبتنی بر سررسید
        maturity = analysis['maturity_analysis']
        if maturity['pressure_ratio'] > Decimal('0.3'):
            recommendations.append("تعدیل سررسید بدهی‌ها برای کاهش فشار کوتاه‌مدت")
        
        # توصیه‌های مبتنی بر پوشش
        coverage = analysis['coverage_analysis']
        if coverage['current_ratio'] < Decimal('1.2'):
            recommendations.append("بهبود نسبت جاری از طریق مدیریت بهینه سرمایه در گردش")
        
        if not recommendations:
            recommendations.append("ساختار بدهی‌های جاری مطلوب است. ادامه روند فعلی توصیه می‌شود.")
        
        return recommendations
    
    def generate_current_liabilities_report(self) -> Dict[str, Any]:
        """تولید گزارش کامل بدهی‌های جاری"""
        analysis = self.analyze_current_liabilities()
        
        return {
            'executive_summary': {
                'total_current_liabilities': analysis['structure_analysis']['total_current_liabilities'],
                'current_ratio': analysis['coverage_analysis']['current_ratio'],
                'risk_count': len(analysis['risk_assessment']),
                'structure_health': analysis['structure_analysis']['structure_health']
            },
            'detailed_analysis': analysis,
            'report_date': datetime.now().isoformat()
        }