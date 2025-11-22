# financial_system/analyzers/balance_sheet_analyzer.py
from ..core.langchain_tools import register_financial_tool
from django.db.models import Sum, Q
from financial_system.models import DocumentItem, ChartOfAccounts
from decimal import Decimal
from typing import Dict, Any

class BalanceSheetAnalyzer:
    def __init__(self, company_id: int, period_id: int):
        self.company_id = company_id
        self.period_id = period_id
    
    @register_financial_tool(
        name="analyze_balance_sheet",
        description="""
        تحلیل کامل ترازنامه و کنترل توازن. این ابزار معادله اصلی حسابداری را بررسی می‌کند:
        دارایی‌ها = بدهی‌ها + حقوق صاحبان سهام
        
        ورودی:
        - company_id: شناسه شرکت
        - period_id: شناسه دوره مالی
        
        خروجی:
        - گزارش توازن ترازنامه و تحلیل ساختار مالی
        """
    )
    def analyze_balance_sheet(self, company_id: int, period_id: int) -> str:
        """ابزار تحلیل ترازنامه برای LangChain"""
        self.company_id = company_id
        self.period_id = period_id
        
        try:
            # محاسبه کل دارایی‌ها
            total_assets = self._calculate_total_assets()
            
            # محاسبه کل بدهی‌ها
            total_liabilities = self._calculate_total_liabilities()
            
            # محاسبه کل حقوق صاحبان سهام
            total_equity = self._calculate_total_equity()
            
            # کنترل توازن
            balance_check = self._check_balance_sheet_equality(total_assets, total_liabilities, total_equity)
            
            # تحلیل ساختار
            structure_analysis = self._analyze_structure(total_assets, total_liabilities, total_equity)
            
            return self._format_balance_sheet_report(
                total_assets, total_liabilities, total_equity, 
                balance_check, structure_analysis
            )
            
        except Exception as e:
            return f"خطا در تحلیل ترازنامه: {str(e)}"
    
    def _calculate_total_assets(self) -> Decimal:
        """محاسبه کل دارایی‌ها"""
        asset_codes = ['1', '2']  # دارایی‌های جاری و ثابت
        total = Decimal('0')
        
        for code in asset_codes:
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=code,
                is_active=True
            )
            for account in accounts:
                balance = self._get_account_balance(account.code)
                if balance > 0:  # فقط مانده‌های مثبت دارایی
                    total += balance
        
        return total
    
    def _calculate_total_liabilities(self) -> Decimal:
        """محاسبه کل بدهی‌ها"""
        liability_codes = ['3']  # بدهی‌های جاری و بلندمدت
        total = Decimal('0')
        
        for code in liability_codes:
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=code,
                is_active=True
            )
            for account in accounts:
                balance = abs(self._get_account_balance(account.code))
                total += balance
        
        return total
    
    def _calculate_total_equity(self) -> Decimal:
        """محاسبه کل حقوق صاحبان سهام"""
        equity_codes = ['5']  # حقوق صاحبان سهام
        total = Decimal('0')
        
        for code in equity_codes:
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=code,
                is_active=True
            )
            for account in accounts:
                balance = self._get_account_balance(account.code)
                total += balance
        
        return total
    
    def _check_balance_sheet_equality(self, total_assets: Decimal, total_liabilities: Decimal, total_equity: Decimal) -> Dict[str, Any]:
        """کنترل معادله ترازنامه"""
        calculated_liabilities_equity = total_liabilities + total_equity
        difference = total_assets - calculated_liabilities_equity
        tolerance = Decimal('0.01')  # تلورانس برای خطای محاسباتی
        
        is_balanced = abs(difference) <= tolerance
        
        return {
            'is_balanced': is_balanced,
            'difference': difference,
            'tolerance': tolerance,
            'equation': f"{total_assets} = {total_liabilities} + {total_equity}",
            'message': 'ترازنامه متوازن است' if is_balanced else 'ترازنامه متوازن نیست'
        }
    
    def _analyze_structure(self, total_assets: Decimal, total_liabilities: Decimal, total_equity: Decimal) -> Dict[str, Any]:
        """تحلیل ساختار ترازنامه"""
        return {
            'asset_composition': {
                'current_assets_ratio': self._calculate_current_assets_ratio(),
                'fixed_assets_ratio': self._calculate_fixed_assets_ratio(),
            },
            'capital_structure': {
                'debt_ratio': total_liabilities / total_assets if total_assets > 0 else Decimal('0'),
                'equity_ratio': total_equity / total_assets if total_assets > 0 else Decimal('0'),
                'debt_to_equity': total_liabilities / total_equity if total_equity > 0 else Decimal('0'),
            },
            'liquidity_position': {
                'current_ratio': self._calculate_current_ratio(),
                'quick_ratio': self._calculate_quick_ratio(),
            }
        }
    
    def _get_account_balance(self, account_code: str) -> Decimal:
        """دریافت مانده حساب"""
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
        
        # تشخیص ماهیت حساب بر اساس کد
        if account_code.startswith(('1', '2')):  # دارایی
            return debit - credit
        else:  # بدهی و حقوق صاحبان سهام
            return credit - debit
    
    def _calculate_current_assets_ratio(self) -> Decimal:
        """محاسبه نسبت دارایی‌های جاری"""
        current_assets = self._calculate_category_total(['11', '12', '13'])
        total_assets = self._calculate_total_assets()
        
        return current_assets / total_assets if total_assets > 0 else Decimal('0')
    
    def _calculate_fixed_assets_ratio(self) -> Decimal:
        """محاسبه نسبت دارایی‌های ثابت"""
        fixed_assets = self._calculate_category_total(['21', '22', '23'])
        total_assets = self._calculate_total_assets()
        
        return fixed_assets / total_assets if total_assets > 0 else Decimal('0')
    
    def _calculate_current_ratio(self) -> Decimal:
        """محاسبه نسبت جاری"""
        current_assets = self._calculate_category_total(['11', '12', '13'])
        current_liabilities = self._calculate_category_total(['31', '32'])
        
        return current_assets / current_liabilities if current_liabilities > 0 else Decimal('0')
    
    def _calculate_quick_ratio(self) -> Decimal:
        """محاسبه نسبت آنی"""
        quick_assets = self._calculate_category_total(['111', '112', '121'])  # نقد، بانک، اسناد دریافتنی
        current_liabilities = self._calculate_category_total(['31', '32'])
        
        return quick_assets / current_liabilities if current_liabilities > 0 else Decimal('0')
    
    def _calculate_category_total(self, codes: list) -> Decimal:
        """محاسبه جمع یک دسته از حساب‌ها"""
        total = Decimal('0')
        for code in codes:
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=code,            is_active=True     )
            for account in accounts:
                balance = abs(self._get_account_balance(account.code))
                total += balance
        return total
    
    def _format_balance_sheet_report(self, total_assets, total_liabilities, total_equity, balance_check, structure_analysis) -> str:
        """قالب‌بندی گزارش ترازنامه"""
        return f"""
                # 🏦 تحلیل ترازنامه

                ## کنترل توازن
                {'✅' if balance_check['is_balanced'] else '❌'} **{balance_check['message']}**
                - دارایی‌ها: {total_assets:,.0f} ریال
                - بدهی‌ها: {total_liabilities:,.0f} ریال  
                - حقوق صاحبان سهام: {total_equity:,.0f} ریال
                - اختلاف: {balance_check['difference']:,.0f} ریال

                ## ساختار دارایی‌ها
                - دارایی‌های جاری: {structure_analysis['asset_composition']['current_assets_ratio']:.1%}
                - دارایی‌های ثابت: {structure_analysis['asset_composition']['fixed_assets_ratio']:.1%}

                ## ساختار سرمایه
                - نسبت بدهی: {structure_analysis['capital_structure']['debt_ratio']:.1%}
                - نسبت حقوق صاحبان سهام: {structure_analysis['capital_structure']['equity_ratio']:.1%}
                - اهرم مالی: {structure_analysis['capital_structure']['debt_to_equity']:.2f}

                ## وضعیت نقدینگی
                - نسبت جاری: {structure_analysis['liquidity_position']['current_ratio']:.2f}
                - نسبت آنی: {structure_analysis['liquidity_position']['quick_ratio']:.2f}
                """