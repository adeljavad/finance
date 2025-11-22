# financial_system/services/cash_bank_analyzer.py
"""
تسک ۵۱: پیاده‌سازی تحلیل صندوق و بانک
این سرویس برای تحلیل حساب‌های نقدی و بانکی طراحی شده است.
"""

from django.db.models import Sum, Q, Count
from decimal import Decimal
from typing import Dict, List
from datetime import datetime, timedelta
from financial_system.models.document_models import DocumentHeader, DocumentItem
from financial_system.models.coding_models import ChartOfAccounts
from users.models import Company, FinancialPeriod


class CashBankAnalyzer:
    """تحلیل‌گر حساب‌های صندوق و بانک"""
    
    def __init__(self, company: Company, period: FinancialPeriod):
        self.company = company
        self.period = period
        self.cash_account_codes = ['101']  # حساب‌های صندوق
        self.bank_account_codes = ['102']  # حساب‌های بانک
    
    def analyze_cash_bank(self) -> Dict:
        """تحلیل کامل حساب‌های صندوق و بانک"""
        
        cash_analysis = self._analyze_cash_accounts()
        bank_analysis = self._analyze_bank_accounts()
        liquidity_analysis = self._analyze_liquidity()
        suspicious_transactions = self._identify_suspicious_transactions()
        
        return {
            'company': self.company.name,
            'period': self.period.name,
            'cash_analysis': cash_analysis,
            'bank_analysis': bank_analysis,
            'liquidity_analysis': liquidity_analysis,
            'suspicious_transactions': suspicious_transactions,
            'recommendations': self._generate_recommendations(cash_analysis, bank_analysis)
        }
    
    def _analyze_cash_accounts(self) -> Dict:
        """تحلیل حساب‌های صندوق"""
        cash_accounts = ChartOfAccounts.objects.filter(
            code__startswith='101',
            is_active=True
        )
        
        analysis = {
            'accounts': [],
            'total_balance': Decimal('0'),
            'total_receipts': Decimal('0'),
            'total_payments': Decimal('0'),
            'transaction_count': 0
        }
        
        for account in cash_accounts:
            account_analysis = self._analyze_single_account(account)
            analysis['accounts'].append(account_analysis)
            analysis['total_balance'] += account_analysis['balance']
            analysis['total_receipts'] += account_analysis['total_receipts']
            analysis['total_payments'] += account_analysis['total_payments']
            analysis['transaction_count'] += account_analysis['transaction_count']
        
        return analysis
    
    def _analyze_bank_accounts(self) -> Dict:
        """تحلیل حساب‌های بانک"""
        bank_accounts = ChartOfAccounts.objects.filter(
            code__startswith='102',
            is_active=True
        )
        
        analysis = {
            'accounts': [],
            'total_balance': Decimal('0'),
            'total_receipts': Decimal('0'),
            'total_payments': Decimal('0'),
            'transaction_count': 0
        }
        
        for account in bank_accounts:
            account_analysis = self._analyze_single_account(account)
            analysis['accounts'].append(account_analysis)
            analysis['total_balance'] += account_analysis['balance']
            analysis['total_receipts'] += account_analysis['total_receipts']
            analysis['total_payments'] += account_analysis['total_payments']
            analysis['transaction_count'] += account_analysis['transaction_count']
        
        return analysis
    
    def _analyze_single_account(self, account: ChartOfAccounts) -> Dict:
        """تحلیل یک حساب خاص"""
        # دریافت تمام آرتیکل‌های مربوط به این حساب
        items = DocumentItem.objects.filter(
            account=account,
            document__company=self.company,
            document__period=self.period
        ).select_related('document')
        
        # محاسبه مانده
        total_debit = items.aggregate(total=Sum('debit'))['total'] or Decimal('0')
        total_credit = items.aggregate(total=Sum('credit'))['total'] or Decimal('0')
        balance = total_debit - total_credit
        
        # تحلیل گردش
        monthly_analysis = self._analyze_monthly_activity(items)
        
        # شناسایی تراکنش‌های بزرگ
        large_transactions = self._identify_large_transactions(items)
        
        return {
            'account_name': account.name,
            'account_code': account.code,
            'balance': balance,
            'total_receipts': total_debit,
            'total_payments': total_credit,
            'transaction_count': items.count(),
            'monthly_analysis': monthly_analysis,
            'large_transactions': large_transactions,
            'average_transaction_size': self._calculate_average_transaction_size(total_debit, total_credit, items.count())
        }
    
    def _analyze_monthly_activity(self, items) -> Dict:
        """تحلیل فعالیت ماهانه حساب"""
        monthly_data = {}
        
        for item in items:
            month_key = item.document.document_date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    'receipts': Decimal('0'),
                    'payments': Decimal('0'),
                    'transactions': 0
                }
            
            monthly_data[month_key]['receipts'] += item.debit
            monthly_data[month_key]['payments'] += item.credit
            monthly_data[month_key]['transactions'] += 1
        
        return monthly_data
    
    def _identify_large_transactions(self, items, threshold: Decimal = Decimal('10000000')) -> List[Dict]:
        """شناسایی تراکنش‌های بزرگ"""
        large_transactions = []
        
        for item in items:
            amount = max(item.debit, item.credit)
            if amount >= threshold:
                large_transactions.append({
                    'document_number': item.document.document_number,
                    'date': item.document.document_date,
                    'amount': amount,
                    'description': item.description,
                    'type': 'دریافت' if item.debit > 0 else 'پرداخت'
                })
        
        return large_transactions
    
    def _calculate_average_transaction_size(self, total_receipts: Decimal, total_payments: Decimal, transaction_count: int) -> Decimal:
        """محاسبه میانگین اندازه تراکنش"""
        if transaction_count > 0:
            total_amount = total_receipts + total_payments
            return total_amount / transaction_count
        return Decimal('0')
    
    def _analyze_liquidity(self) -> Dict:
        """تحلیل نقدینگی"""
        cash_balance = self._analyze_cash_accounts()['total_balance']
        bank_balance = self._analyze_bank_accounts()['total_balance']
        
        total_cash_bank = cash_balance + bank_balance
        
        # محاسبه نسبت‌های نقدینگی
        current_liabilities = self._get_current_liabilities()
        
        ratios = {}
        
        # نسبت نقدی
        if current_liabilities > 0:
            ratios['cash_ratio'] = total_cash_bank / current_liabilities
        else:
            ratios['cash_ratio'] = Decimal('0')
        
        # نسبت گردش نقدی
        total_operating_cash_flow = self._calculate_operating_cash_flow()
        if total_operating_cash_flow > 0:
            ratios['cash_turnover_ratio'] = total_cash_bank / total_operating_cash_flow
        else:
            ratios['cash_turnover_ratio'] = Decimal('0')
        
        return {
            'cash_balance': cash_balance,
            'bank_balance': bank_balance,
            'total_cash_bank': total_cash_bank,
            'ratios': ratios,
            'liquidity_assessment': self._assess_liquidity(ratios)
        }
    
    def _get_current_liabilities(self) -> Decimal:
        """دریافت جمع بدهی‌های جاری"""
        current_liability_accounts = ChartOfAccounts.objects.filter(
            code__startswith='2',  # بدهی‌های جاری
            is_active=True
        )
        
        total_liabilities = Decimal('0')
        for account in current_liability_accounts:
            items = DocumentItem.objects.filter(
                account=account,
                document__company=self.company,
                document__period=self.period
            )
            
            account_debit = items.aggregate(total=Sum('debit'))['total'] or Decimal('0')
            account_credit = items.aggregate(total=Sum('credit'))['total'] or Decimal('0')
            
            # برای حساب‌های بدهی: مانده = بستانکار - بدهکار
            balance = account_credit - account_debit
            total_liabilities += balance
        
        return total_liabilities
    
    def _calculate_operating_cash_flow(self) -> Decimal:
        """محاسبه جریان نقدی عملیاتی"""
        # این یک محاسبه ساده است - در نسخه کامل باید دقیق‌تر باشد
        cash_receipts = self._analyze_cash_accounts()['total_receipts']
        cash_payments = self._analyze_cash_accounts()['total_payments']
        
        return cash_receipts - cash_payments
    
    def _assess_liquidity(self, ratios: Dict) -> str:
        """ارزیابی وضعیت نقدینگی"""
        cash_ratio = ratios.get('cash_ratio', Decimal('0'))
        
        if cash_ratio < Decimal('0.2'):
            return "نقدینگی پایین - ریسک بالا"
        elif cash_ratio < Decimal('0.5'):
            return "نقدینگی متوسط"
        else:
            return "نقدینگی مناسب"
    
    def _identify_suspicious_transactions(self) -> List[Dict]:
        """شناسایی تراکنش‌های مشکوک"""
        suspicious_transactions = []
        
        # بررسی حساب‌های صندوق و بانک
        cash_bank_accounts = ChartOfAccounts.objects.filter(
            Q(code__startswith='101') | Q(code__startswith='102'),
            is_active=True
        )
        
        for account in cash_bank_accounts:
            items = DocumentItem.objects.filter(
                account=account,
                document__company=self.company,
                document__period=self.period
            ).select_related('document')
            
            for item in items:
                # تراکنش‌های با مبلغ گرد
                if self._is_round_amount(item.debit) or self._is_round_amount(item.credit):
                    suspicious_transactions.append({
                        'account': account.name,
                        'document_number': item.document.document_number,
                        'date': item.document.document_date,
                        'amount': max(item.debit, item.credit),
                        'issue': 'مبلغ گرد',
                        'description': item.description
                    })
                
                # تراکنش‌های در ساعات غیرعادی (اگر تاریخ‌شمار داشته باشیم)
                if self._is_unusual_time(item.document.document_date):
                    suspicious_transactions.append({
                        'account': account.name,
                        'document_number': item.document.document_number,
                        'date': item.document.document_date,
                        'amount': max(item.debit, item.credit),
                        'issue': 'زمان غیرعادی',
                        'description': item.description
                    })
        
        return suspicious_transactions
    
    def _is_round_amount(self, amount: Decimal) -> bool:
        """بررسی گرد بودن مبلغ"""
        if amount == Decimal('0'):
            return False
        
        # مبالغی که مضرب ۱,۰۰۰,۰۰۰ هستند
        return amount % Decimal('1000000') == Decimal('0')
    
    def _is_unusual_time(self, date) -> bool:
        """بررسی زمان غیرعادی (مثلاً آخر هفته)"""
        # این یک نمونه ساده است - در نسخه کامل باید دقیق‌تر باشد
        return date.weekday() >= 5  # شنبه و یکشنبه
    
    def _generate_recommendations(self, cash_analysis: Dict, bank_analysis: Dict) -> List[str]:
        """تولید توصیه‌های تحلیلی"""
        recommendations = []
        
        # تحلیل صندوق
        if cash_analysis['total_balance'] < Decimal('0'):
            recommendations.append("مانده صندوق منفی است - نیاز به بررسی فوری")
        
        if cash_analysis['total_balance'] > Decimal('100000000'):  # 100 میلیون
            recommendations.append("موجودی صندوق بیش از حد است - ریسک سرقت")
        
        # تحلیل بانک
        if bank_analysis['total_balance'] < Decimal('0'):
            recommendations.append("مانده بانک منفی است - احتمال اعتبار اضافه برداشت")
        
        # تحلیل نقدینگی
        liquidity = self._analyze_liquidity()
        if liquidity['liquidity_assessment'] == "نقدینگی پایین - ریسک بالا":
            recommendations.append("نقدینگی پایین است - نیاز به مدیریت جریان نقدی")
        
        # تحلیل تراکنش‌های مشکوک
        suspicious = self._identify_suspicious_transactions()
        if suspicious:
            recommendations.append(f"{len(suspicious)} تراکنش مشکوک شناسایی شد")
        
        return recommendations
    
    def generate_cash_flow_statement(self) -> Dict:
        """تولید صورت جریان نقدی ساده"""
        cash_analysis = self._analyze_cash_accounts()
        bank_analysis = self._analyze_bank_accounts()
        
        return {
            'title': f'گزارش جریان نقدی - {self.company.name}',
            'period': self.period.name,
            'opening_balance': self._get_opening_balance(),
            'cash_receipts': cash_analysis['total_receipts'] + bank_analysis['total_receipts'],
            'cash_payments': cash_analysis['total_payments'] + bank_analysis['total_payments'],
            'net_cash_flow': (cash_analysis['total_receipts'] + bank_analysis['total_receipts']) - 
                            (cash_analysis['total_payments'] + bank_analysis['total_payments']),
            'closing_balance': cash_analysis['total_balance'] + bank_analysis['total_balance']
        }
    
    def _get_opening_balance(self) -> Decimal:
        """دریافت مانده اول دوره"""
        # این یک نمونه ساده است - در نسخه کامل باید دقیق‌تر باشد
        return Decimal('0')


# ابزار LangChain برای تحلیل صندوق و بانک
class CashBankAnalysisTool:
    """ابزار تحلیل صندوق و بانک برای LangChain"""
    
    name = "cash_bank_analyzer"
    description = "تحلیل حساب‌های صندوق و بانک و وضعیت نقدینگی"
    
    def __init__(self):
        self.analyzer_class = CashBankAnalyzer
    
    def analyze(self, company_id: int, period_id: int) -> Dict:
        """تحلیل صندوق و بانک برای شرکت و دوره مشخص"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            analyzer = CashBankAnalyzer(company, period)
            result = analyzer.analyze_cash_bank()
            
            return {
                'success': True,
                'analysis': result,
                'cash_flow_statement': analyzer.generate_cash_flow_statement()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
