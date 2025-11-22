# financial_system/services/balance_sheet_analyzer.py
"""
تسک ۵۰: ایجاد کنترل توازن ترازنامه
این سرویس برای تحلیل و کنترل توازن ترازنامه طراحی شده است.
"""

from django.db.models import Sum, Q
from decimal import Decimal
from typing import Dict, List, Tuple
from financial_system.models.document_models import DocumentHeader, DocumentItem
from financial_system.models.coding_models import ChartOfAccounts
from users.models import Company, FinancialPeriod


class BalanceSheetAnalyzer:
    """تحلیل‌گر توازن ترازنامه"""
    
    def __init__(self, company: Company, period: FinancialPeriod):
        self.company = company
        self.period = period
        self.analysis_result = {}
    
    def analyze_balance_sheet(self) -> Dict:
        """تحلیل کامل توازن ترازنامه"""
        
        # ۱. محاسبه جمع دارایی‌ها
        total_assets = self._calculate_total_assets()
        
        # ۲. محاسبه جمع بدهی‌ها و حقوق صاحبان سهام
        total_liabilities_equity = self._calculate_total_liabilities_equity()
        
        # ۳. کنترل توازن
        balance_status = self._check_balance(total_assets, total_liabilities_equity)
        
        # ۴. تحلیل جزئیات
        detailed_analysis = self._detailed_analysis()
        
        self.analysis_result = {
            'company': self.company.name,
            'period': self.period.name,
            'total_assets': total_assets,
            'total_liabilities_equity': total_liabilities_equity,
            'balance_status': balance_status,
            'detailed_analysis': detailed_analysis,
            'is_balanced': balance_status['is_balanced'],
            'difference': balance_status['difference']
        }
        
        return self.analysis_result
    
    def _calculate_total_assets(self) -> Dict:
        """محاسبه جمع دارایی‌ها"""
        
        # کدهای حساب‌های دارایی (معمولاً با ۱ شروع می‌شوند)
        asset_accounts = ChartOfAccounts.objects.filter(
            code__startswith='1',
            is_active=True
        )
        
        # محاسبه مانده دارایی‌ها
        asset_balance = self._calculate_accounts_balance(asset_accounts)
        
        return {
            'current_assets': self._calculate_current_assets(),
            'non_current_assets': self._calculate_non_current_assets(),
            'total': asset_balance
        }
    
    def _calculate_current_assets(self) -> Dict:
        """محاسبه دارایی‌های جاری"""
        current_asset_codes = ['101', '102', '103', '104', '105', '106']  # صندوق، بانک، اسناد دریافتنی، ...
        
        current_assets = {}
        total = Decimal('0')
        
        for code in current_asset_codes:
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=code,
                is_active=True
            )
            balance = self._calculate_accounts_balance(accounts)
            current_assets[code] = balance
            total += balance
        
        current_assets['total'] = total
        return current_assets
    
    def _calculate_non_current_assets(self) -> Dict:
        """محاسبه دارایی‌های غیرجاری"""
        non_current_asset_codes = ['11', '12', '13']  # دارایی‌های ثابت، سرمایه‌گذاری‌ها، ...
        
        non_current_assets = {}
        total = Decimal('0')
        
        for code_prefix in non_current_asset_codes:
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=code_prefix,
                is_active=True
            )
            balance = self._calculate_accounts_balance(accounts)
            non_current_assets[code_prefix] = balance
            total += balance
        
        non_current_assets['total'] = total
        return non_current_assets
    
    def _calculate_total_liabilities_equity(self) -> Dict:
        """محاسبه جمع بدهی‌ها و حقوق صاحبان سهام"""
        
        liabilities = self._calculate_liabilities()
        equity = self._calculate_equity()
        
        total = liabilities['total'] + equity['total']
        
        return {
            'liabilities': liabilities,
            'equity': equity,
            'total': total
        }
    
    def _calculate_liabilities(self) -> Dict:
        """محاسبه بدهی‌ها"""
        # کدهای حساب‌های بدهی (معمولاً با ۲ شروع می‌شوند)
        liability_accounts = ChartOfAccounts.objects.filter(
            code__startswith='2',
            is_active=True
        )
        
        liability_balance = self._calculate_accounts_balance(liability_accounts)
        
        return {
            'current_liabilities': self._calculate_current_liabilities(),
            'non_current_liabilities': self._calculate_non_current_liabilities(),
            'total': liability_balance
        }
    
    def _calculate_current_liabilities(self) -> Dict:
        """محاسبه بدهی‌های جاری"""
        current_liability_codes = ['21', '22']  # اسناد پرداختنی، بدهی‌های کوتاه مدت
        
        current_liabilities = {}
        total = Decimal('0')
        
        for code_prefix in current_liability_codes:
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=code_prefix,
                is_active=True
            )
            balance = self._calculate_accounts_balance(accounts)
            current_liabilities[code_prefix] = balance
            total += balance
        
        current_liabilities['total'] = total
        return current_liabilities
    
    def _calculate_non_current_liabilities(self) -> Dict:
        """محاسبه بدهی‌های بلندمدت"""
        non_current_liability_codes = ['23', '24']  # وام‌های بلندمدت
        
        non_current_liabilities = {}
        total = Decimal('0')
        
        for code_prefix in non_current_liability_codes:
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=code_prefix,
                is_active=True
            )
            balance = self._calculate_accounts_balance(accounts)
            non_current_liabilities[code_prefix] = balance
            total += balance
        
        non_current_liabilities['total'] = total
        return non_current_liabilities
    
    def _calculate_equity(self) -> Dict:
        """محاسبه حقوق صاحبان سهام"""
        # کدهای حساب‌های حقوق صاحبان سهام (معمولاً با ۳ شروع می‌شوند)
        equity_accounts = ChartOfAccounts.objects.filter(
            code__startswith='3',
            is_active=True
        )
        
        equity_balance = self._calculate_accounts_balance(equity_accounts)
        
        return {
            'capital': self._calculate_capital(),
            'retained_earnings': self._calculate_retained_earnings(),
            'total': equity_balance
        }
    
    def _calculate_capital(self) -> Decimal:
        """محاسبه سرمایه"""
        capital_accounts = ChartOfAccounts.objects.filter(
            code__startswith='31',  # حساب‌های سرمایه
            is_active=True
        )
        return self._calculate_accounts_balance(capital_accounts)
    
    def _calculate_retained_earnings(self) -> Decimal:
        """محاسبه سود انباشته"""
        retained_earnings_accounts = ChartOfAccounts.objects.filter(
            code__startswith='32',  # حساب‌های سود انباشته
            is_active=True
        )
        return self._calculate_accounts_balance(retained_earnings_accounts)
    
    def _calculate_accounts_balance(self, accounts) -> Decimal:
        """محاسبه مانده حساب‌ها"""
        total_debit = Decimal('0')
        total_credit = Decimal('0')
        
        for account in accounts:
            # محاسبه جمع بدهکار و بستانکار برای این حساب
            items = DocumentItem.objects.filter(
                account=account,
                document__company=self.company,
                document__period=self.period
            )
            
            account_debit = items.aggregate(total=Sum('debit'))['total'] or Decimal('0')
            account_credit = items.aggregate(total=Sum('credit'))['total'] or Decimal('0')
            
            total_debit += account_debit
            total_credit += account_credit
        
        # برای حساب‌های دارایی: مانده = بدهکار - بستانکار
        # برای حساب‌های بدهی و سرمایه: مانده = بستانکار - بدهکار
        if accounts and accounts.first().code.startswith('1'):  # دارایی
            balance = total_debit - total_credit
        else:  # بدهی و سرمایه
            balance = total_credit - total_debit
        
        return balance
    
    def _check_balance(self, total_assets: Dict, total_liabilities_equity: Dict) -> Dict:
        """کنترل توازن ترازنامه"""
        assets_total = total_assets['total']
        liabilities_equity_total = total_liabilities_equity['total']
        
        difference = abs(assets_total - liabilities_equity_total)
        tolerance = Decimal('0.01')  # تحمل ۱ ریال
        
        is_balanced = difference <= tolerance
        
        return {
            'is_balanced': is_balanced,
            'difference': difference,
            'assets_total': assets_total,
            'liabilities_equity_total': liabilities_equity_total,
            'tolerance': tolerance
        }
    
    def _detailed_analysis(self) -> Dict:
        """تحلیل جزئیات ترازنامه"""
        
        # تحلیل نسبت‌های کلیدی
        ratios = self._calculate_ratios()
        
        # شناسایی حساب‌های مشکوک
        suspicious_accounts = self._identify_suspicious_accounts()
        
        # تحلیل روند
        trend_analysis = self._analyze_trends()
        
        return {
            'ratios': ratios,
            'suspicious_accounts': suspicious_accounts,
            'trend_analysis': trend_analysis,
            'recommendations': self._generate_recommendations()
        }
    
    def _calculate_ratios(self) -> Dict:
        """محاسبه نسبت‌های کلیدی ترازنامه"""
        current_assets = self._calculate_current_assets()['total']
        current_liabilities = self._calculate_current_liabilities()['total']
        total_assets = self._calculate_total_assets()['total']
        total_liabilities = self._calculate_liabilities()['total']
        total_equity = self._calculate_equity()['total']
        
        ratios = {}
        
        # نسبت جاری
        if current_liabilities > 0:
            ratios['current_ratio'] = current_assets / current_liabilities
        else:
            ratios['current_ratio'] = Decimal('0')
        
        # نسبت بدهی
        if total_assets > 0:
            ratios['debt_ratio'] = total_liabilities / total_assets
        else:
            ratios['debt_ratio'] = Decimal('0')
        
        # نسبت حقوق صاحبان سهام
        if total_assets > 0:
            ratios['equity_ratio'] = total_equity / total_assets
        else:
            ratios['equity_ratio'] = Decimal('0')
        
        return ratios
    
    def _identify_suspicious_accounts(self) -> List[Dict]:
        """شناسایی حساب‌های مشکوک"""
        suspicious_accounts = []
        
        # حساب‌هایی با مانده منفی غیرعادی
        all_accounts = ChartOfAccounts.objects.filter(is_active=True)
        
        for account in all_accounts:
            balance = self._calculate_accounts_balance([account])
            
            # اگر حساب دارایی باشد و مانده منفی داشته باشد
            if account.code.startswith('1') and balance < Decimal('0'):
                suspicious_accounts.append({
                    'account': account.name,
                    'code': account.code,
                    'balance': balance,
                    'issue': 'مانده منفی در حساب دارایی'
                })
            
            # اگر حساب بدهی/سرمایه باشد و مانده منفی داشته باشد
            elif (account.code.startswith('2') or account.code.startswith('3')) and balance < Decimal('0'):
                suspicious_accounts.append({
                    'account': account.name,
                    'code': account.code,
                    'balance': balance,
                    'issue': 'مانده منفی در حساب بدهی/سرمایه'
                })
        
        return suspicious_accounts
    
    def _analyze_trends(self) -> Dict:
        """تحلیل روند ترازنامه"""
        # این بخش نیاز به داده‌های تاریخی دارد
        # فعلاً ساختار پایه ایجاد می‌شود
        return {
            'message': 'تحلیل روند نیاز به داده‌های دوره‌های قبلی دارد',
            'recommended_periods': 3
        }
    
    def _generate_recommendations(self) -> List[str]:
        """تولید توصیه‌های تحلیلی"""
        recommendations = []
        
        balance_status = self._check_balance(
            self._calculate_total_assets(),
            self._calculate_total_liabilities_equity()
        )
        
        if not balance_status['is_balanced']:
            recommendations.append(
                f"ترازنامه نامتوازن است. تفاوت: {balance_status['difference']:,.0f} ریال"
            )
        
        ratios = self._calculate_ratios()
        
        # تحلیل نسبت جاری
        if ratios['current_ratio'] < Decimal('1'):
            recommendations.append("نسبت جاری کمتر از ۱ است - ریسک نقدینگی بالا")
        elif ratios['current_ratio'] > Decimal('3'):
            recommendations.append("نسبت جاری بالاتر از ۳ است - سرمایه در گردش بیش از حد")
        
        # تحلیل نسبت بدهی
        if ratios['debt_ratio'] > Decimal('0.7'):
            recommendations.append("نسبت بدهی بالاتر از ۷۰٪ است - ریسک اهرمی بالا")
        
        return recommendations
    
    def generate_report(self) -> Dict:
        """تولید گزارش کامل ترازنامه"""
        analysis = self.analyze_balance_sheet()
        
        report = {
            'title': f'گزارش تحلیل ترازنامه - {self.company.name}',
            'period': self.period.name,
            'analysis_date': 'تاریخ تحلیل',
            'summary': {
                'total_assets': f"{analysis['total_assets']['total']:,.0f}",
                'total_liabilities_equity': f"{analysis['total_liabilities_equity']['total']:,.0f}",
                'is_balanced': analysis['is_balanced'],
                'difference': f"{analysis['difference']:,.0f}"
            },
            'detailed_analysis': analysis['detailed_analysis'],
            'balance_status': analysis['balance_status']
        }
        
        return report


# ابزار LangChain برای تحلیل ترازنامه
class BalanceSheetAnalysisTool:
    """ابزار تحلیل ترازنامه برای LangChain"""
    
    name = "balance_sheet_analyzer"
    description = "تحلیل و کنترل توازن ترازنامه شرکت"
    
    def __init__(self):
        self.analyzer_class = BalanceSheetAnalyzer
    
    def analyze(self, company_id: int, period_id: int) -> Dict:
        """تحلیل ترازنامه برای شرکت و دوره مشخص"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            analyzer = BalanceSheetAnalyzer(company, period)
            result = analyzer.analyze_balance_sheet()
            
            return {
                'success': True,
                'analysis': result,
                'report': analyzer.generate_report()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
