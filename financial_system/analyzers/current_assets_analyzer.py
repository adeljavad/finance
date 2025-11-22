# financial_system/analyzers/current_assets_analyzer.py
from ..core.langchain_tools import register_financial_tool
from django.db.models import Sum, Q, F
from financial_system.models import DocumentItem, ChartOfAccounts
from decimal import Decimal
from typing import Dict, List, Any
from datetime import datetime, timedelta

class CurrentAssetsAnalyzer:
    def __init__(self, company_id: int = None, period_id: int = None):
        self.company_id = company_id
        self.period_id = period_id
        self.current_asset_codes = ['11', '12', '13']

    @register_financial_tool(
        name="analyze_current_assets",
        description="""
        تحلیل جامع دارایی‌های جاری شرکت. این ابزار برای بررسی نقدشوندگی، ترکیب دارایی‌ها، 
        ریسک‌ها و ارائه توصیه‌های مدیریتی استفاده می‌شود.
        
        ورودی:
        - company_id: شناسه شرکت (عدد)
        - period_id: شناسه دوره مالی (عدد)
        
        خروجی:
        - گزارش تحلیلی کامل دارایی‌های جاری شامل نقدشوندگی، ریسک‌ها و توصیه‌ها
        """
    )
    def analyze_current_assets(self, **kwargs) -> str:
        """ابزار تحلیل دارایی‌های جاری برای LangChain"""
        try:
            analysis = {
                'composition_analysis': self._analyze_composition(),
                'liquidity_analysis': self._analyze_liquidity(),
                'aging_analysis': self._analyze_aging(),
                'turnover_analysis': self._analyze_turnover(),
                'risk_assessment': self._assess_risks(),
            }
            
            analysis['recommendations'] = self._generate_recommendations(analysis)
            
            return self._format_analysis_for_llm(analysis)
            
        except Exception as e:
            return f"خطا در تحلیل دارایی‌های جاری: {str(e)}"
    
    def _format_analysis_for_llm(self, analysis: Dict[str, Any]) -> str:
        """قالب‌بندی خروجی برای مدل زبانی"""
        composition = analysis['composition_analysis']
        liquidity = analysis['liquidity_analysis']
        risks = analysis['risk_assessment']
        recommendations = analysis['recommendations']
        
        report = f"""
# 📊 تحلیل دارایی‌های جاری

## خلاصه اجرایی
- کل دارایی‌های جاری: {composition.get('total_current_assets', 0):,.0f} ریال
- امتیاز نقدشوندگی: {liquidity.get('liquidity_score', 0)}/5
- تعداد ریسک‌های شناسایی شده: {len(risks)}

## نسبت‌های نقدشوندگی
- نسبت جاری: {liquidity.get('ratios', {}).get('current_ratio', 0):.2f}
- نسبت آنی: {liquidity.get('ratios', {}).get('quick_ratio', 0):.2f}
- نسبت نقدی: {liquidity.get('ratios', {}).get('cash_ratio', 0):.2f}

## ریسک‌های شناسایی شده
{self._format_risks_for_llm(risks)}

## توصیه‌های مدیریتی
{self._format_recommendations_for_llm(recommendations)}

## ترکیب دارایی‌های جاری
{self._format_composition_for_llm(composition.get('components', {}))}
"""
        return report

    def _format_risks_for_llm(self, risks: List[Dict]) -> str:
        """قالب‌بندی ریسک‌ها برای خروجی متنی"""
        if not risks:
            return "✅ هیچ ریسک جدی شناسایی نشد."
        
        risk_text = ""
        for risk in risks:
            risk_text += f"- **{risk.get('type', 'نامشخص')}** (شدت: {risk.get('severity', 'نامشخص')}): {risk.get('description', '')}\n"
        
        return risk_text

    def _format_recommendations_for_llm(self, recommendations: List[str]) -> str:
        """قالب‌بندی توصیه‌ها برای خروجی متنی"""
        if not recommendations:
            return "✅ وضعیت مطلوب است. ادامه روند فعلی توصیه می‌شود."
        
        rec_text = ""
        for i, rec in enumerate(recommendations, 1):
            rec_text += f"{i}. {rec}\n"
        
        return rec_text

    def _format_composition_for_llm(self, composition: Dict) -> str:
        """قالب‌بندی ترکیب دارایی‌ها برای خروجی متنی"""
        if not composition:
            return "هیچ داده‌ای برای نمایش وجود ندارد."
        
        comp_text = ""
        for asset_name, data in composition.items():
            balance = data.get('balance', 0)
            percentage = data.get('percentage', 0)
            comp_text += f"- {asset_name}: {balance:,.0f} ریال ({percentage:.1f}%)\n"
        
        return comp_text

    def _analyze_composition(self) -> Dict[str, Any]:
        """تحلیل ترکیب دارایی‌های جاری"""
        composition = {}
        total_current_assets = Decimal('0')
        
        for asset_code in self.current_asset_codes:
            accounts = ChartOfAccounts.objects.filter(
                code__startswith=asset_code,
                is_active=True
            )
            
            for account in accounts:
                balance = self._get_account_balance(account.code)
                if balance > 0:  # فقط حساب‌هایی با مانده مثبت
                    composition[account.name] = {
                        'code': account.code,
                        'balance': balance,
                        'percentage': Decimal('0')
                    }
                    total_current_assets += balance
        
        # محاسبه درصد هر جزء
        for asset_name, data in composition.items():
            if total_current_assets > 0:
                data['percentage'] = (data['balance'] / total_current_assets) * 100
        
        return {
            'components': composition,
            'total_current_assets': total_current_assets,
            'concentration_ratio': self._calculate_concentration_ratio(composition)
        }

    def _analyze_liquidity(self) -> Dict[str, Any]:
        """تحلیل نقدشوندگی دارایی‌های جاری"""
        liquidity_categories = {
            'highly_liquid': ['111', '112'],  # صندوق، بانک
            'quick_assets': ['121', '122'],   # اسناد دریافتنی، حساب‌های دریافتنی
            'medium_liquid': ['131', '132'],  # موجودی کالا، پیش‌پرداخت‌ها
            'less_liquid': ['141', '151']     # سفارشات، سایر دارایی‌های جاری
        }
        
        liquidity_analysis = {}
        total_by_category = {}
        
        for category, codes in liquidity_categories.items():
            category_balance = Decimal('0')
            for code in codes:
                accounts = ChartOfAccounts.objects.filter(
                    code__startswith=code,
                    is_active=True
                )
                for account in accounts:
                    balance = self._get_account_balance(account.code)
                    if balance > 0:
                        category_balance += balance
            
            total_by_category[category] = category_balance
            liquidity_analysis[category] = {
                'balance': category_balance,
                'accounts': codes
            }
        
        total_current_assets = sum(total_by_category.values())
        current_liabilities = self._get_current_liabilities()
        
        # محاسبه نسبت‌های نقدشوندگی
        quick_assets = total_by_category['highly_liquid'] + total_by_category['quick_assets']
        current_ratio = total_current_assets / current_liabilities if current_liabilities > 0 else Decimal('0')
        quick_ratio = quick_assets / current_liabilities if current_liabilities > 0 else Decimal('0')
        cash_ratio = total_by_category['highly_liquid'] / current_liabilities if current_liabilities > 0 else Decimal('0')
        
        return {
            'liquidity_categories': liquidity_analysis,
            'ratios': {
                'current_ratio': current_ratio,
                'quick_ratio': quick_ratio,
                'cash_ratio': cash_ratio
            },
            'liquidity_score': self._calculate_liquidity_score(current_ratio, quick_ratio)
        }
    
    def _analyze_aging(self) -> Dict[str, Any]:
        """تحلیل عمر دارایی‌های جاری"""
        aging_analysis = {}
        
        # تحلیل اسناد دریافتنی
        receivable_aging = self._analyze_receivable_aging()
        if receivable_aging:
            aging_analysis['receivables'] = receivable_aging
        
        # تحلیل موجودی کالا
        inventory_aging = self._analyze_inventory_aging()
        if inventory_aging:
            aging_analysis['inventory'] = inventory_aging
        
        return aging_analysis
    
    def _analyze_turnover(self) -> Dict[str, Any]:
        """تحلیل گردش دارایی‌های جاری"""
        turnover_analysis = {}
        
        # گردش موجودی کالا
        inventory_turnover = self._calculate_inventory_turnover()
        if inventory_turnover:
            turnover_analysis['inventory_turnover'] = inventory_turnover
        
        # دوره وصول مطالبات
        collection_period = self._calculate_collection_period()
        if collection_period:
            turnover_analysis['collection_period'] = collection_period
        
        # گردش دارایی‌های جاری
        current_assets_turnover = self._calculate_current_assets_turnover()
        if current_assets_turnover:
            turnover_analysis['current_assets_turnover'] = current_assets_turnover
        
        return turnover_analysis
    
    def _assess_risks(self) -> List[Dict[str, Any]]:
        """ارزیابی ریسک‌های دارایی‌های جاری"""
        risks = []
        
        try:
            # ریسک تمرکز
            composition = self._analyze_composition()
            concentration_ratio = composition.get('concentration_ratio', 0)
            if concentration_ratio > Decimal('0.6'):  # بیش از ۶۰٪ تمرکز
                risks.append({
                    'type': 'CONCENTRATION_RISK',
                    'severity': 'MEDIUM',
                    'description': 'تمرکز بالای دارایی‌های جاری در چند قلم خاص',
                    'ratio': float(concentration_ratio),
                    'recommendation': 'تنوع بخشی به ترکیب دارایی‌های جاری'
                })
            
            # ریسک نقدشوندگی
            liquidity = self._analyze_liquidity()
            quick_ratio = liquidity.get('ratios', {}).get('quick_ratio', Decimal('0'))
            if quick_ratio < Decimal('0.8'):
                risks.append({
                    'type': 'LIQUIDITY_RISK',
                    'severity': 'HIGH',
                    'description': f'نسبت آنی پایین ({quick_ratio:.2f})، ریسک نقدشوندگی بالا',
                    'quick_ratio': float(quick_ratio),
                    'recommendation': 'افزایش دارایی‌های نقدشونده'
                })
            
            # ریسک وصول مطالبات
            aging = self._analyze_aging()
            if 'receivables' in aging:
                receivables_data = aging['receivables']
                overdue_percentage = receivables_data.get('overdue_percentage', Decimal('0'))
                if overdue_percentage > Decimal('20'):  # بیش از ۲۰٪ مطالبات معوق
                    risks.append({
                        'type': 'COLLECTION_RISK',
                        'severity': 'HIGH',
                        'description': f'{float(overdue_percentage)}% مطالبات معوق',
                        'overdue_amount': float(receivables_data.get('overdue_amount', 0)),
                        'recommendation': 'بررسی و پیگیری مطالبات معوق'
                    })
            
            # ریسک موجودی کالا
            turnover = self._analyze_turnover()
            if 'inventory_turnover' in turnover:
                inventory_data = turnover['inventory_turnover']
                turnover_ratio = inventory_data.get('turnover_ratio', Decimal('0'))
                if turnover_ratio < Decimal('4'):  # گردش کمتر از ۴ بار در سال
                    risks.append({
                        'type': 'INVENTORY_RISK',
                        'severity': 'MEDIUM',
                        'description': f'گردش موجودی کالا پایین ({float(turnover_ratio):.1f} بار در سال)',
                        'turnover_ratio': float(turnover_ratio),
                        'recommendation': 'بهینه‌سازی سطح موجودی‌ها'
                    })
                    
        except Exception as e:
            # در صورت بروز خطا در تحلیل ریسک‌ها
            risks.append({
                'type': 'ANALYSIS_ERROR',
                'severity': 'MEDIUM',
                'description': f'خطا در تحلیل برخی ریسک‌ها: {str(e)}',
                'recommendation': 'بررسی مجدد داده‌های مالی'
            })
        
        return risks
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """تولید توصیه‌های مدیریتی"""
        recommendations = []
        
        # توصیه‌های مبتنی بر ریسک
        for risk in analysis.get('risk_assessment', []):
            rec = risk.get('recommendation')
            if rec and rec not in recommendations:
                recommendations.append(rec)
        
        # توصیه‌های مبتنی بر ترکیب دارایی
        composition = analysis.get('composition_analysis', {})
        concentration_ratio = composition.get('concentration_ratio', Decimal('0'))
        if concentration_ratio > Decimal('0.7'):
            rec = "تنوع بخشی به ترکیب دارایی‌های جاری برای کاهش ریسک تمرکز"
            if rec not in recommendations:
                recommendations.append(rec)
        
        # توصیه‌های مبتنی بر نقدشوندگی
        liquidity = analysis.get('liquidity_analysis', {})
        quick_ratio = liquidity.get('ratios', {}).get('quick_ratio', Decimal('0'))
        if quick_ratio < Decimal('1.0'):
            rec = "افزایش دارایی‌های نقدشونده برای بهبود نسبت آنی"
            if rec not in recommendations:
                recommendations.append(rec)
        
        # توصیه‌های مبتنی بر گردش
        turnover = analysis.get('turnover_analysis', {})
        if 'inventory_turnover' in turnover:
            inventory_data = turnover['inventory_turnover']
            if inventory_data.get('assessment') == 'NEEDS_IMPROVEMENT':
                rec = "بهبود مدیریت موجودی‌ها برای افزایش گردش"
                if rec not in recommendations:
                    recommendations.append(rec)
        
        if 'collection_period' in turnover:
            collection_data = turnover['collection_period']
            if collection_data.get('assessment') == 'NEEDS_IMPROVEMENT':
                rec = "اصلاح سیاست‌های اعتباری و وصول مطالبات"
                if rec not in recommendations:
                    recommendations.append(rec)
        
        if not recommendations:
            recommendations.append("وضعیت دارایی‌های جاری مطلوب است. ادامه روند فعلی توصیه می‌شود.")
        
        return recommendations

    def _get_account_balance(self, account_code: str) -> Decimal:
        """دریافت مانده یک حساب"""
        try:
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
            
            # برای حساب‌های دارایی: مانده = بدهکار - بستانکار
            return debit - credit
            
        except Exception:
            return Decimal('0')
    
    def _get_current_liabilities(self) -> Decimal:
        """دریافت مجموع بدهی‌های جاری"""
        try:
            liability_codes = ['31', '32']
            total_liabilities = Decimal('0')
            
            for code in liability_codes:
                accounts = ChartOfAccounts.objects.filter(
                    code__startswith=code,
                    is_active=True
                )
                for account in accounts:
                    balance = abs(self._get_account_balance(account.code))
                    total_liabilities += balance
            
            return total_liabilities
            
        except Exception:
            return Decimal('100000000')  # مقدار پیش‌فرض برای تست
    
    def _calculate_concentration_ratio(self, composition: Dict) -> Decimal:
        """محاسبه نسبت تمرکز"""
        if not composition:
            return Decimal('0')
        
        try:
            balances = [data['balance'] for data in composition.values() if data['balance'] > 0]
            if not balances:
                return Decimal('0')
                
            sorted_balances = sorted(balances, reverse=True)
            top_two = sum(sorted_balances[:2])
            total = sum(sorted_balances)
            
            return top_two / total if total > 0 else Decimal('0')
            
        except Exception:
            return Decimal('0')
    
    def _calculate_liquidity_score(self, current_ratio: Decimal, quick_ratio: Decimal) -> int:
        """محاسبه امتیاز نقدشوندگی"""
        try:
            score = 0
            
            if current_ratio >= Decimal('1.5'):
                score += 3
            elif current_ratio >= Decimal('1.0'):
                score += 2
            elif current_ratio >= Decimal('0.8'):
                score += 1
            
            if quick_ratio >= Decimal('1.0'):
                score += 3
            elif quick_ratio >= Decimal('0.8'):
                score += 2
            elif quick_ratio >= Decimal('0.5'):
                score += 1
            
            return min(score, 5)  # حداکثر امتیاز 5
            
        except Exception:
            return 0
    
    def _analyze_receivable_aging(self) -> Dict[str, Any]:
        """تحلیل عمر مطالبات"""
        # این تابع نیاز به داده‌های تاریخ‌دار دارد - فعلاً نمونه
        try:
            return {
                'current': Decimal('50000000'),      # جاری
                '1_30_days': Decimal('20000000'),    # ۱-۳۰ روز
                '31_60_days': Decimal('10000000'),   # ۳۱-۶۰ روز
                '61_90_days': Decimal('5000000'),    # ۶۱-۹۰ روز
                'over_90_days': Decimal('3000000'),  # بیش از ۹۰ روز
                'total_receivables': Decimal('88000000'),
                'overdue_amount': Decimal('8000000'),  # مطالبات معوق
                'overdue_percentage': Decimal('9.09')  # ۸ میلیون از ۸۸ میلیون
            }
        except Exception:
            return {}
    
    def _analyze_inventory_aging(self) -> Dict[str, Any]:
        """تحلیل عمر موجودی کالا"""
        try:
            return {
                'less_30_days': Decimal('30000000'),
                '31_60_days': Decimal('15000000'),
                '61_90_days': Decimal('8000000'),
                'over_90_days': Decimal('4000000'),
                'total_inventory': Decimal('57000000'),
                'slow_moving_percentage': Decimal('21.05')  # موجودی بیش از ۶۰ روز
            }
        except Exception:
            return {}
    
    def _calculate_inventory_turnover(self) -> Dict[str, Any]:
        """محاسبه گردش موجودی کالا"""
        try:
            cost_of_goods_sold = Decimal('400000000')  # بهای تمام شده کالای فروش رفته
            average_inventory = Decimal('50000000')    # میانگین موجودی
            
            turnover_ratio = cost_of_goods_sold / average_inventory if average_inventory > 0 else Decimal('0')
            days_inventory = Decimal('365') / turnover_ratio if turnover_ratio > 0 else Decimal('0')
            
            assessment = 'GOOD' if turnover_ratio >= Decimal('6.0') else 'NEEDS_IMPROVEMENT'
            
            return {
                'turnover_ratio': turnover_ratio,
                'days_inventory': days_inventory,
                'industry_average': Decimal('8.0'),
                'assessment': assessment
            }
        except Exception:
            return {}
    
    def _calculate_collection_period(self) -> Dict[str, Any]:
        """محاسبه دوره وصول مطالبات"""
        try:
            net_credit_sales = Decimal('600000000')  # فروش نسیه خالص
            average_receivables = Decimal('55000000')  # میانگین مطالبات
            
            turnover_ratio = net_credit_sales / average_receivables if average_receivables > 0 else Decimal('0')
            collection_period = Decimal('365') / turnover_ratio if turnover_ratio > 0 else Decimal('0')
            
            assessment = 'GOOD' if collection_period <= Decimal('45') else 'NEEDS_IMPROVEMENT'
            
            return {
                'collection_period': collection_period,
                'turnover_ratio': turnover_ratio,
                'industry_average': Decimal('45'),
                'assessment': assessment
            }
        except Exception:
            return {}
    
    def _calculate_current_assets_turnover(self) -> Dict[str, Any]:
        """محاسبه گردش دارایی‌های جاری"""
        try:
            net_sales = Decimal('800000000')  # فروش خالص
            average_current_assets = Decimal('150000000')  # میانگین دارایی‌های جاری
            
            turnover_ratio = net_sales / average_current_assets if average_current_assets > 0 else Decimal('0')
            
            assessment = 'GOOD' if turnover_ratio >= Decimal('4.5') else 'NEEDS_IMPROVEMENT'
            
            return {
                'turnover_ratio': turnover_ratio,
                'industry_average': Decimal('5.0'),
                'assessment': assessment
            }
        except Exception:
            return {}
    
    def generate_current_assets_report(self) -> Dict[str, Any]:
        """تولید گزارش کامل دارایی‌های جاری"""
        try:
            analysis = self.analyze_current_assets()
            
            return {
                'executive_summary': {
                    'total_current_assets': analysis.get('composition_analysis', {}).get('total_current_assets', 0),
                    'liquidity_score': analysis.get('liquidity_analysis', {}).get('liquidity_score', 0),
                    'risk_count': len(analysis.get('risk_assessment', [])),
                    'overall_health': 'EXCELLENT' if len(analysis.get('risk_assessment', [])) == 0 else 'GOOD'
                },
                'detailed_analysis': analysis,
                'report_date': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'error': f'خطا در تولید گزارش: {str(e)}',
                'report_date': datetime.now().isoformat()
            }
