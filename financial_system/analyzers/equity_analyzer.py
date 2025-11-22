# financial_system/analyzers/equity_analyzer.py
from django.db.models import Sum, Q
from financial_system.models import DocumentItem, ChartOfAccounts
from decimal import Decimal
from typing import Dict, List, Any
from datetime import datetime

class EquityAnalyzer:
    def __init__(self, company_id: int, period_id: int):
        self.company_id = company_id
        self.period_id = period_id
        self.equity_codes = ['51', '52', '53', '54']  # کدهای حقوق صاحبان سهام
    
    def analyze_equity(self) -> Dict[str, Any]:
        """تحلیل جامع حقوق صاحبان سهام"""
        analysis = {
            'structure_analysis': self._analyze_structure(),
            'changes_analysis': self._analyze_changes(),
            'profitability_analysis': self._analyze_profitability(),
            'valuation_analysis': self._analyze_valuation(),
            'risk_assessment': self._assess_risks(),
            'recommendations': []
        }
        
        analysis['recommendations'] = self._generate_recommendations(analysis)
        return analysis
    
    def _analyze_structure(self) -> Dict[str, Any]:
        """تحلیل ساختار حقوق صاحبان سهام"""
        structure = {}
        total_equity = Decimal('0')
        
        for equity_code in self.equity_codes:
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=equity_code,
                is_active=True
            )
            
            for account in accounts:
                balance = self._get_account_balance(account.code)
                structure[account.name] = {
                    'code': account.code,
                    'balance': balance,
                    'percentage': Decimal('0'),
                    'type': self._classify_equity_type(account.code)
                }
                total_equity += balance
        
        # محاسبه درصد هر جزء
        for equity_name, data in structure.items():
            if total_equity > 0:
                data['percentage'] = (data['balance'] / total_equity) * 100
        
        return {
            'components': structure,
            'total_equity': total_equity,
            'capital_structure': self._analyze_capital_structure(total_equity)
        }
    
    def _analyze_changes(self) -> Dict[str, Any]:
        """تحلیل تغییرات حقوق صاحبان سهام"""
        # این تحلیل نیاز به داده‌های دوره‌های قبلی دارد
        changes = {
            'beginning_equity': Decimal('800000000'),
            'ending_equity': Decimal('900000000'),
            'net_change': Decimal('100000000'),
            'change_components': {
                'net_income': Decimal('120000000'),
                'dividends_paid': Decimal('-20000000'),
                'capital_increase': Decimal('0'),
                'other_changes': Decimal('0')
            },
            'change_percentage': Decimal('12.5')  # 100M / 800M
        }
        
        return changes
    
    def _analyze_profitability(self) -> Dict[str, Any]:
        """تحلیل سودآوری مرتبط با حقوق صاحبان سهام"""
        net_income = Decimal('120000000')
        total_equity = self._get_total_equity()
        average_equity = (Decimal('800000000') + total_equity) / Decimal('2')  # میانگین دوره
        
        return {
            'return_on_equity': (net_income / average_equity) * 100 if average_equity > 0 else Decimal('0'),
            'return_on_equity_trend': self._calculate_roe_trend(),
            'dividend_payout_ratio': Decimal('16.67'),  # 20M / 120M
            'retention_ratio': Decimal('83.33'),  # 100 - payout ratio
            'industry_comparison': {
                'industry_roe': Decimal('18.5'),
                'position': 'ABOVE_AVERAGE' if (net_income / average_equity) * 100 > Decimal('18.5') else 'BELOW_AVERAGE'
            }
        }
    
    def _analyze_valuation(self) -> Dict[str, Any]:
        """تحلیل ارزش‌گذاری مرتبط با حقوق صاحبان سهام"""
        total_equity = self._get_total_equity()
        net_income = Decimal('120000000')
        
        return {
            'book_value_per_share': total_equity / Decimal('1000000'),  # فرض ۱ میلیون سهم
            'earnings_per_share': net_income / Decimal('1000000'),
            'price_to_book_ratio': Decimal('1.2'),  # نسبت P/B فرضی
            'valuation_assessment': self._assess_valuation()
        }
    
    def _assess_risks(self) -> List[Dict[str, Any]]:
        """ارزیابی ریسک‌های مرتبط با حقوق صاحبان سهام"""
        risks = []
        
        profitability = self._analyze_profitability()
        if profitability['return_on_equity'] < Decimal('10.0'):
            risks.append({
                'type': 'LOW_PROFITABILITY',
                'severity': 'MEDIUM',
                'description': 'بازده حقوق صاحبان سهام پایین',
                'roe': profitability['return_on_equity'],
                'recommendation': 'بهبود سودآوری و بهره‌وری سرمایه'
            })
        
        structure = self._analyze_structure()
        capital_structure = structure['capital_structure']
        if capital_structure['equity_ratio'] < Decimal('0.3'):
            risks.append({
                'type': 'HIGH_LEVERAGE',
                'severity': 'HIGH',
                'description': 'نسبت حقوق صاحبان سهام به کل دارایی‌ها پایین',
                'equity_ratio': capital_structure['equity_ratio'],
                'recommendation': 'افزایش سرمایه یا کاهش بدهی‌ها'
            })
        
        changes = self._analyze_changes()
        if changes['change_percentage'] < Decimal('5.0'):
            risks.append({
                'type': 'SLOW_GROWTH',
                'severity': 'LOW',
                'description': 'رشد کند حقوق صاحبان سهام',
                'growth_rate': changes['change_percentage'],
                'recommendation': 'بررسی راه‌های افزایش سودآوری و رشد'
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
        
        # برای حساب‌های حقوق صاحبان سهام: مانده = بستانکار - بدهکار
        return credit - debit
    
    def _classify_equity_type(self, account_code: str) -> str:
        """طبقه‌بندی نوع حساب حقوق صاحبان سهام"""
        type_mapping = {
            '511': 'سرمایه',
            '512': 'اندوخته قانونی',
            '513': 'سایر اندوخته‌ها',
            '521': 'سود انباشته',
            '531': 'سود سال جاری'
        }
        
        for code_prefix, equity_type in type_mapping.items():
            if account_code.startswith(code_prefix):
                return equity_type
        
        return 'سایر موارد'
    
    def _analyze_capital_structure(self, total_equity: Decimal) -> Dict[str, Any]:
        """تحلیل ساختار سرمایه"""
        total_assets = self._get_total_assets()
        total_liabilities = total_assets - total_equity
        
        return {
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'debt_to_equity': total_liabilities / total_equity if total_equity > 0 else Decimal('0'),
            'equity_ratio': total_equity / total_assets if total_assets > 0 else Decimal('0'),
            'leverage_ratio': total_assets / total_equity if total_equity > 0 else Decimal('0')
        }
    
    def _calculate_roe_trend(self) -> str:
        """محاسبه روند بازده حقوق صاحبان سهام"""
        # این تحلیل نیاز به داده‌های تاریخی دارد
        roe_history = [Decimal('15.2'), Decimal('16.8'), Decimal('18.1')]  # نمونه
        
        if len(roe_history) < 2:
            return 'STABLE'
        
        if roe_history[-1] > roe_history[-2]:
            return 'IMPROVING'
        elif roe_history[-1] < roe_history[-2]:
            return 'DECLINING'
        else:
            return 'STABLE'
    
    def _assess_valuation(self) -> str:
        """ارزیابی ارزش‌گذاری"""
        pb_ratio = Decimal('1.2')
        roe = Decimal('18.1')
        
        # قاعده سرانگشتی: P/B باید حدوداً با ROE مرتبط باشد
        if pb_ratio < Decimal('1.0') and roe > Decimal('15.0'):
            return 'UNDERVALUED'
        elif pb_ratio > Decimal('2.0') and roe < Decimal('10.0'):
            return 'OVERVALUED'
        else:
            return 'FAIRLY_VALUED'
    
    def _get_total_equity(self) -> Decimal:
        """دریافت مجموع حقوق صاحبان سهام"""
        total = Decimal('0')
        for equity_code in self.equity_codes:
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=equity_code,
                is_active=True
            )
            for account in accounts:
                total += self._get_account_balance(account.code)
        
        return total
    
    def _get_total_assets(self) -> Decimal:
        """دریافت مجموع دارایی‌ها"""
        asset_codes = ['1', '2']  # دارایی‌های جاری و ثابت
        total_assets = Decimal('0')
        
        for code in asset_codes:
            # این خط اصلاح شده - کاما و پرانتز اضافی حذف شد
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=code,
                is_active=True
            )
            for account in accounts:
                balance = self._get_account_balance(account.code)
                if balance > 0:  # فقط مانده‌های مثبت (دارایی)
                    total_assets += balance
        
        return total_assets
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """تولید توصیه‌های مدیریتی"""
        recommendations = []
        
        # توصیه‌های مبتنی بر ریسک
        for risk in analysis['risk_assessment']:
            recommendations.append(risk['recommendation'])
        
        # توصیه‌های مبتنی بر سودآوری
        profitability = analysis['profitability_analysis']
        if profitability['return_on_equity'] < Decimal('15.0'):
            recommendations.append("بهبود بازده حقوق صاحبان سهام از طریق بهینه‌سازی سودآوری")
        
        # توصیه‌های مبتنی بر ساختار سرمایه
        structure = analysis['structure_analysis']
        capital_structure = structure['capital_structure']
        if capital_structure['debt_to_equity'] > Decimal('2.0'):
            recommendations.append("کاهش اهرم مالی برای بهبود ساختار سرمایه")
        
        # توصیه‌های مبتنی بر سود سهام
        profitability = analysis['profitability_analysis']
        if profitability['dividend_payout_ratio'] > Decimal('50.0'):
            recommendations.append("بازنگری در سیاست سود سهام برای حفظ منابع رشد")
        
        if not recommendations:
            recommendations.append("ساختار حقوق صاحبان سهام مطلوب است. ادامه روند فعلی توصیه می‌شود.")
        
        return recommendations
    
    def generate_equity_report(self) -> Dict[str, Any]:
        """تولید گزارش کامل حقوق صاحبان سهام"""
        analysis = self.analyze_equity()
        
        return {
            'executive_summary': {
                'total_equity': analysis['structure_analysis']['total_equity'],
                'return_on_equity': analysis['profitability_analysis']['return_on_equity'],
                'debt_to_equity': analysis['structure_analysis']['capital_structure']['debt_to_equity'],
                'risk_count': len(analysis['risk_assessment'])
            },
            'detailed_analysis': analysis,
            'report_date': datetime.now().isoformat()
        }