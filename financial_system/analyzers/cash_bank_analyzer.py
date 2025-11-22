# financial_system/analyzers/cash_bank_analyzer.py
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
import pandas as pd

class CashBankAnalyzer:
    def __init__(self, company_id, financial_period_id):
        self.company_id = company_id
        self.financial_period_id = financial_period_id
    
    def analyze_cash_positions(self):
        """تحلیل جامع وضعیت نقدی شرکت"""
        
        # 1. محاسبه مانده‌های نقدی
        cash_balances = self._calculate_cash_balances()
        
        # 2. تحلیل گردش نقدی
        cash_flow_analysis = self._analyze_cash_flow()
        
        # 3. شناسایی الگوهای مشکوک
        suspicious_patterns = self._detect_suspicious_patterns()
        
        # 4. محاسبه نسبت‌های نقدینگی
        liquidity_ratios = self._calculate_liquidity_ratios()
        
        return {
            'cash_balances': cash_balances,
            'cash_flow_analysis': cash_flow_analysis,
            'suspicious_patterns': suspicious_patterns,
            'liquidity_ratios': liquidity_ratios,
            'recommendations': self._generate_recommendations()
        }
    
    def _calculate_cash_balances(self):
        """محاسبه مانده‌های صندوق، بانک و تنخواه"""
        from .models import DocumentItem, ChartOfAccounts
        
        # شناسایی حساب‌های نقدی (کدهای شروع با 1)
        cash_accounts = ChartOfAccounts.objects.filter(
            company_id=self.company_id,
            code__startswith='1',  # گروه دارایی‌های جاری
            level__in=['SUBCLASS', 'DETAIL']
        )
        
        balances = {}
        for account in cash_accounts:
            # محاسبه مانده آخر دوره
            debit_total = DocumentItem.objects.filter(
                document__company_id=self.company_id,
                document__financial_period_id=self.financial_period_id,
                account_code=account.code,
                debit__gt=0
            ).aggregate(total=Sum('debit'))['total'] or 0
            
            credit_total = DocumentItem.objects.filter(
                document__company_id=self.company_id,
                document__financial_period_id=self.financial_period_id,
                account_code=account.code,
                credit__gt=0
            ).aggregate(total=Sum('credit'))['total'] or 0
            
            balance = debit_total - credit_total
            balances[account.name] = {
                'code': account.code,
                'balance': balance,
                'nature': 'بدهکار' if balance >= 0 else 'بستانکار'
            }
        
        return balances
    
    def _analyze_cash_flow(self):
        """تحلیل گردش نقدی در دوره مالی"""
        from .models import DocumentItem
        
        # گردش‌های نقدی ورودی و خروجی
        cash_flow_data = DocumentItem.objects.filter(
            document__company_id=self.company_id,
            document__financial_period_id=self.financial_period_id,
            account_code__startswith='1'  # حساب‌های نقدی
        ).values('document__document_date').annotate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        ).order_by('document__document_date')
        
        # تبدیل به DataFrame برای تحلیل پیشرفته
        df = pd.DataFrame(list(cash_flow_data))
        
        analysis = {
            'total_cash_in': df['total_debit'].sum(),
            'total_cash_out': df['total_credit'].sum(),
            'net_cash_flow': df['total_debit'].sum() - df['total_credit'].sum(),
            'daily_patterns': self._analyze_daily_patterns(df),
            'peak_days': self._find_peak_days(df)
        }
        
        return analysis
    
    def _detect_suspicious_patterns(self):
        """شناسایی الگوهای مشکوک در گردش نقدی"""
        suspicious_patterns = []
        
        # 1. کنترل مانده‌های منفی
        negative_balances = self._find_negative_balances()
        if negative_balances:
            suspicious_patterns.append({
                'type': 'مانده منفی',
                'accounts': negative_balances,
                'risk_level': 'HIGH',
                'message': 'حساب‌های نقدی دارای مانده منفی شناسایی شد'
            })
        
        # 2. کنترل گردش‌های بزرگ غیرعادی
        large_transactions = self._find_large_transactions()
        if large_transactions:
            suspicious_patterns.append({
                'type': 'گردش بزرگ غیرعادی',
                'transactions': large_transactions,
                'risk_level': 'MEDIUM',
                'message': 'گردش‌های مالی بزرگ غیرمتعارف شناسایی شد'
            })
        
        # 3. کنترل توالی تاریخی
        sequence_issues = self._check_date_sequence()
        if sequence_issues:
            suspicious_patterns.append({
                'type': 'مشکل توالی تاریخی',
                'issues': sequence_issues,
                'risk_level': 'LOW',
                'message': 'عدم توالی در تاریخ اسناد شناسایی شد'
            })
        
        return suspicious_patterns
    
    def _calculate_liquidity_ratios(self):
        """محاسبه نسبت‌های نقدینگی"""
        from .models import DocumentItem
        
        # جمع دارایی‌های جاری
        current_assets = DocumentItem.objects.filter(
            document__company_id=self.company_id,
            document__financial_period_id=self.financial_period_id,
            account_code__startswith='1'  # دارایی‌های جاری
        ).aggregate(total=Sum('debit') - Sum('credit'))['total'] or 0
        
        # جمع بدهی‌های جاری
        current_liabilities = DocumentItem.objects.filter(
            document__company_id=self.company_id,
            document__financial_period_id=self.financial_period_id,
            account_code__startswith='2'  # بدهی‌های جاری
        ).aggregate(total=Sum('credit') - Sum('debit'))['total'] or 0
        
        # نسبت جاری
        current_ratio = current_assets / current_liabilities if current_liabilities > 0 else 0
        
        # نسبت آنی (نقدی‌ترین دارایی‌ها / بدهی‌های جاری)
        quick_assets = self._calculate_quick_assets()
        quick_ratio = quick_assets / current_liabilities if current_liabilities > 0 else 0
        
        return {
            'current_ratio': round(current_ratio, 2),
            'quick_ratio': round(quick_ratio, 2),
            'current_assets': current_assets,
            'current_liabilities': current_liabilities,
            'quick_assets': quick_assets
        }
    
    def _calculate_quick_assets(self):
        """محاسبه دارایی‌های سریع‌الوصول"""
        from .models import DocumentItem
        
        # صندوق، بانک، سرمایه‌گذاری‌های کوتاه مدت
        quick_assets_codes = ['111', '112', '113']  # کدهای نمونه
        
        quick_assets = 0
        for code in quick_assets_codes:
            balance = DocumentItem.objects.filter(
                document__company_id=self.company_id,
                document__financial_period_id=self.financial_period_id,
                account_code__startswith=code
            ).aggregate(
                net=Sum('debit') - Sum('credit')
            )['net'] or 0
            
            quick_assets += balance
        
        return quick_assets
    
    def _find_negative_balances(self):
        """پیدا کردن حساب‌های نقدی با مانده منفی"""
        balances = self._calculate_cash_balances()
        negative_accounts = []
        
        for account_name, data in balances.items():
            if data['balance'] < 0:
                negative_accounts.append({
                    'account': account_name,
                    'balance': data['balance'],
                    'code': data['code']
                })
        
        return negative_accounts
    
    def _find_large_transactions(self):
        """پیدا کردن گردش‌های بزرگ غیرعادی"""
        from .models import DocumentItem
        
        # آستانه برای گردش بزرگ (مثلاً ۱۰٪ از کل گردش)
        threshold = self._get_large_transaction_threshold()
        
        large_transactions = DocumentItem.objects.filter(
            document__company_id=self.company_id,
            document__financial_period_id=self.financial_period_id,
            account_code__startswith='1',
            debit__gt=threshold
        ).values(
            'document__document_id',
            'document__document_date',
            'account_code',
            'debit'
        ).order_by('-debit')[:10]  # 10 گردش بزرگ
        
        return list(large_transactions)
    
    def _get_large_transaction_threshold(self):
        """محاسبه آستانه برای گردش‌های بزرگ"""
        from .models import DocumentItem
        
        total_cash_flow = DocumentItem.objects.filter(
            document__company_id=self.company_id,
            document__financial_period_id=self.financial_period_id,
            account_code__startswith='1'
        ).aggregate(
            total_debit=Sum('debit')
        )['total_debit'] or 0
        
        return total_cash_flow * 0.1  # 10% از کل گردش
    
    def _check_date_sequence(self):
        """کنترل توالی تاریخی اسناد"""
        from .models import DocumentHeader
        
        documents = DocumentHeader.objects.filter(
            company_id=self.company_id,
            financial_period_id=self.financial_period_id
        ).order_by('document_date')
        
        issues = []
        prev_date = None
        
        for doc in documents:
            if prev_date and doc.document_date < prev_date:
                issues.append({
                    'document_id': doc.document_id,
                    'document_date': doc.document_date,
                    'issue': 'تاریخ سند قبل از سند قبلی'
                })
            prev_date = doc.document_date
        
        return issues
    
    def _analyze_daily_patterns(self, df):
        """تحلیل الگوهای روزانه گردش نقدی"""
        if df.empty:
            return {}
        
        df['document__document_date'] = pd.to_datetime(df['document__document_date'])
        df['day_of_week'] = df['document__document_date'].dt.day_name()
        
        daily_patterns = df.groupby('day_of_week').agg({
            'total_debit': 'mean',
            'total_credit': 'mean'
        }).to_dict()
        
        return daily_patterns
    
    def _find_peak_days(self, df):
        """پیدا کردن روزهای با بیشترین گردش"""
        if df.empty:
            return []
        
        df['net_flow'] = df['total_debit'] - df['total_credit']
        peak_days = df.nlargest(5, 'net_flow')[['document__document_date', 'net_flow']]
        
        return peak_days.to_dict('records')
    
    def _generate_recommendations(self):
        """تولید توصیه‌های مدیریتی"""
        analysis = self.analyze_cash_positions()
        recommendations = []
        
        # تحلیل نسبت‌های نقدینگی
        if analysis['liquidity_ratios']['current_ratio'] < 1:
            recommendations.append({
                'type': 'ریسک نقدینگی',
                'priority': 'HIGH',
                'message': 'نسبت جاری کمتر از 1 است - شرکت در تامین نقدینگی مشکل دارد',
                'suggestion': 'افزایش سرمایه در گردش یا کاهش بدهی‌های کوتاه مدت'
            })
        
        # تحلیل مانده‌های منفی
        if analysis['suspicious_patterns']:
            for pattern in analysis['suspicious_patterns']:
                if pattern['type'] == 'مانده منفی':
                    recommendations.append({
                        'type': 'کنترل داخلی',
                        'priority': 'HIGH',
                        'message': 'حساب‌های نقدی با مانده منفی شناسایی شد',
                        'suggestion': 'بررسی فوری حساب‌های: ' + 
                                     ', '.join([acc['account'] for acc in pattern['accounts']])
                    })
        
        # تحلیل گردش‌های بزرگ
        large_trans_found = any(
            pattern['type'] == 'گردش بزرگ غیرعادی' 
            for pattern in analysis['suspicious_patterns']
        )
        if large_trans_found:
            recommendations.append({
                'type': 'کنترل گردش‌ها',
                'priority': 'MEDIUM',
                'message': 'گردش‌های بزرگ غیرعادی شناسایی شد',
                'suggestion': 'بررسی مجوزها و تاییدیه‌های گردش‌های بزرگ'
            })
        
        return recommendations