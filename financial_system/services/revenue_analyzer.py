# financial_system/services/revenue_analyzer.py
"""
تسک ۵۶: ایجاد تحلیل درآمدها
این سرویس برای تحلیل حساب‌های درآمدی طراحی شده است.
"""

from django.db.models import Sum, Q
from decimal import Decimal
from typing import Dict, List
from financial_system.models.document_models import DocumentHeader, DocumentItem
from financial_system.models.coding_models import ChartOfAccounts
from users.models import Company, FinancialPeriod


class RevenueAnalyzer:
    """تحلیل‌گر حساب‌های درآمدی"""
    
    def __init__(self, company: Company, period: FinancialPeriod):
        self.company = company
        self.period = period
        self.revenue_account_codes = ['4']  # حساب‌های درآمدی (معمولاً با ۴ شروع می‌شوند)
    
    def analyze_revenue(self) -> Dict:
        """تحلیل کامل حساب‌های درآمدی"""
        
        total_revenue = self._calculate_total_revenue()
        revenue_by_type = self._analyze_revenue_by_type()
        monthly_trend = self._analyze_monthly_trend()
        revenue_composition = self._analyze_revenue_composition()
        growth_analysis = self._analyze_growth()
        
        return {
            'company': self.company.name,
            'period': self.period.name,
            'total_revenue': total_revenue,
            'revenue_by_type': revenue_by_type,
            'monthly_trend': monthly_trend,
            'revenue_composition': revenue_composition,
            'growth_analysis': growth_analysis,
            'recommendations': self._generate_recommendations(total_revenue, revenue_by_type)
        }
    
    def _calculate_total_revenue(self) -> Dict:
        """محاسبه کل درآمدها"""
        revenue_accounts = ChartOfAccounts.objects.filter(
            code__startswith='4',
            is_active=True
        )
        
        total_revenue = Decimal('0')
        revenue_details = {}
        
        for account in revenue_accounts:
            items = DocumentItem.objects.filter(
                account=account,
                document__company=self.company,
                document__period=self.period
            )
            
            # برای حساب‌های درآمدی: درآمد = بستانکار - بدهکار
            account_debit = items.aggregate(total=Sum('debit'))['total'] or Decimal('0')
            account_credit = items.aggregate(total=Sum('credit'))['total'] or Decimal('0')
            account_revenue = account_credit - account_debit
            
            revenue_details[account.code] = {
                'account_name': account.name,
                'revenue': account_revenue,
                'transaction_count': items.count()
            }
            
            total_revenue += account_revenue
        
        return {
            'total': total_revenue,
            'details': revenue_details
        }
    
    def _analyze_revenue_by_type(self) -> Dict:
        """تحلیل درآمد بر اساس نوع"""
        revenue_types = {
            'فروش کالا': ['41'],  # فروش
            'خدمات': ['42'],      # درآمد خدمات
            'سایر درآمدها': ['43', '44', '45']  # سایر درآمدهای عملیاتی و غیرعملیاتی
        }
        
        analysis = {}
        total = Decimal('0')
        
        for revenue_type, codes in revenue_types.items():
            type_revenue = Decimal('0')
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
                    account_revenue = account_credit - account_debit
                    
                    type_details[account.code] = {
                        'account_name': account.name,
                        'revenue': account_revenue
                    }
                    
                    type_revenue += account_revenue
            
            analysis[revenue_type] = {
                'total': type_revenue,
                'percentage': (type_revenue / total * 100) if total > 0 else Decimal('0'),
                'details': type_details
            }
            
            total += type_revenue
        
        # محاسبه درصدها
        for revenue_type in analysis:
            if total > 0:
                analysis[revenue_type]['percentage'] = (analysis[revenue_type]['total'] / total * 100)
        
        analysis['total'] = total
        return analysis
    
    def _analyze_monthly_trend(self) -> Dict:
        """تحلیل روند ماهانه درآمد"""
        revenue_accounts = ChartOfAccounts.objects.filter(
            code__startswith='4',
            is_active=True
        )
        
        monthly_data = {}
        
        for account in revenue_accounts:
            items = DocumentItem.objects.filter(
                account=account,
                document__company=self.company,
                document__period=self.period
            ).select_related('document')
            
            for item in items:
                month_key = item.document.document_date.strftime('%Y-%m')
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        'revenue': Decimal('0'),
                        'transactions': 0
                    }
                
                # برای درآمد: بستانکار منهای بدهکار
                monthly_data[month_key]['revenue'] += (item.credit - item.debit)
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
        """محاسبه نرخ رشد درآمد"""
        if len(monthly_data) < 2:
            return Decimal('0')
        
        sorted_months = sorted(monthly_data.keys())
        first_month_revenue = monthly_data[sorted_months[0]]['revenue']
        last_month_revenue = monthly_data[sorted_months[-1]]['revenue']
        
        if first_month_revenue > 0:
            growth_rate = ((last_month_revenue - first_month_revenue) / first_month_revenue) * 100
            return growth_rate
        
        return Decimal('0')
    
    def _analyze_seasonality(self, monthly_data: Dict) -> Dict:
        """تحلیل فصلی بودن درآمد"""
        if len(monthly_data) < 3:
            return {'message': 'داده کافی برای تحلیل فصلی وجود ندارد'}
        
        # محاسبه میانگین ماهانه
        monthly_totals = [data['revenue'] for data in monthly_data.values()]
        average_monthly = sum(monthly_totals) / len(monthly_totals)
        
        # شناسایی ماه‌های پیک و افت
        peak_month = max(monthly_data, key=lambda x: monthly_data[x]['revenue'])
        low_month = min(monthly_data, key=lambda x: monthly_data[x]['revenue'])
        
        peak_value = monthly_data[peak_month]['revenue']
        low_value = monthly_data[low_month]['revenue']
        
        return {
            'average_monthly': average_monthly,
            'peak_month': peak_month,
            'peak_value': peak_value,
            'low_month': low_month,
            'low_value': low_value,
            'seasonality_index': (peak_value - low_value) / average_monthly if average_monthly > 0 else Decimal('0')
        }
    
    def _analyze_revenue_composition(self) -> Dict:
        """تحلیل ترکیب درآمد"""
        revenue_by_type = self._analyze_revenue_by_type()
        total_revenue = revenue_by_type['total']
        
        composition = {}
        for revenue_type, data in revenue_by_type.items():
            if revenue_type != 'total':
                composition[revenue_type] = {
                    'amount': data['total'],
                    'percentage': (data['total'] / total_revenue * 100) if total_revenue > 0 else Decimal('0'),
                    'concentration': self._assess_concentration(data['total'], total_revenue)
                }
        
        # تحلیل تمرکز درآمد
        concentration_analysis = self._analyze_revenue_concentration(composition)
        
        return {
            'composition': composition,
            'concentration_analysis': concentration_analysis
        }
    
    def _assess_concentration(self, type_revenue: Decimal, total_revenue: Decimal) -> str:
        """ارزیابی تمرکز درآمد"""
        if total_revenue == 0:
            return "بدون درآمد"
        
        percentage = (type_revenue / total_revenue) * 100
        
        if percentage > 70:
            return "تمرکز بسیار بالا"
        elif percentage > 50:
            return "تمرکز بالا"
        elif percentage > 30:
            return "تمرکز متوسط"
        else:
            return "تمرکز پایین"
    
    def _analyze_revenue_concentration(self, composition: Dict) -> Dict:
        """تحلیل تمرکز درآمد"""
        if not composition:
            return {'message': 'داده‌ای برای تحلیل وجود ندارد'}
        
        # محاسبه شاخص هرفیندال-هیرشمن (HHI)
        hhi_index = Decimal('0')
        for revenue_type, data in composition.items():
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
        
        # شناسایی بزرگترین منبع درآمد
        largest_source = max(composition.items(), key=lambda x: x[1]['amount'])
        
        return {
            'hhi_index': hhi_index,
            'concentration_level': concentration_level,
            'largest_source': {
                'type': largest_source[0],
                'percentage': largest_source[1]['percentage'],
                'amount': largest_source[1]['amount']
            },
            'diversification_score': (1 - hhi_index) * 100  # امتیاز تنوع
        }
    
    def _analyze_growth(self) -> Dict:
        """تحلیل رشد درآمد"""
        # این تحلیل نیاز به داده‌های تاریخی دارد
        # فعلاً ساختار پایه ایجاد می‌شود
        current_revenue = self._calculate_total_revenue()['total']
        
        return {
            'current_revenue': current_revenue,
            'growth_metrics': {
                'month_over_month': self._calculate_mom_growth(),
                'year_over_year': self._calculate_yoy_growth(),
                'quarterly_growth': self._calculate_quarterly_growth()
            },
            'growth_targets': self._assess_growth_targets(current_revenue)
        }
    
    def _calculate_mom_growth(self) -> Dict:
        """محاسبه رشد ماه به ماه"""
        # نیاز به داده‌های ماه قبل دارد
        return {
            'growth_rate': Decimal('0'),
            'message': 'نیاز به داده‌های ماه قبل'
        }
    
    def _calculate_yoy_growth(self) -> Dict:
        """محاسبه رشد سال به سال"""
        # نیاز به داده‌های سال قبل دارد
        return {
            'growth_rate': Decimal('0'),
            'message': 'نیاز به داده‌های سال قبل'
        }
    
    def _calculate_quarterly_growth(self) -> Dict:
        """محاسبه رشد فصلی"""
        # نیاز به داده‌های فصول قبل دارد
        return {
            'growth_rate': Decimal('0'),
            'message': 'نیاز به داده‌های فصول قبل'
        }
    
    def _assess_growth_targets(self, current_revenue: Decimal) -> Dict:
        """ارزیابی اهداف رشد"""
        # این یک تحلیل نمونه است
        if current_revenue == 0:
            return {'status': 'بدون درآمد', 'recommendation': 'تمرکز بر ایجاد جریان درآمدی'}
        
        monthly_trend = self._analyze_monthly_trend()
        growth_rate = monthly_trend['growth_rate']
        
        if growth_rate > 20:
            status = 'رشد بسیار بالا'
            recommendation = 'حفظ روند رشد و توسعه بازار'
        elif growth_rate > 10:
            status = 'رشد مناسب'
            recommendation = 'بهبود مستمر و توسعه محصولات'
        elif growth_rate > 0:
            status = 'رشد کند'
            recommendation = 'بررسی موانع رشد و توسعه استراتژی‌های جدید'
        else:
            status = 'رشد منفی'
            recommendation = 'بررسی علل کاهش درآمد و اصلاح استراتژی'
        
        return {
            'status': status,
            'growth_rate': growth_rate,
            'recommendation': recommendation
        }
    
    def _generate_recommendations(self, total_revenue: Dict, revenue_by_type: Dict) -> List[str]:
        """تولید توصیه‌های تحلیلی"""
        recommendations = []
        
        # تحلیل کل درآمد
        if total_revenue['total'] == Decimal('0'):
            recommendations.append("هیچ درآمدی ثبت نشده است - نیاز به بررسی فرآیندهای فروش")
        
        # تحلیل ترکیب درآمد
        composition = self._analyze_revenue_composition()
        concentration = composition['concentration_analysis']
        
        if concentration['concentration_level'] == "تمرکز بسیار بالا":
            recommendations.append("تمرکز درآمد بسیار بالا است - ریسک وابستگی به یک منبع")
        
        # تحلیل رشد
        growth = self._analyze_growth()
        if growth['growth_targets']['status'] == 'رشد منفی':
            recommendations.append("رشد درآمد منفی است - نیاز به بررسی علل و اصلاح استراتژی")
        
        # تحلیل فصلی
        seasonality = self._analyze_monthly_trend()['seasonality']
        if 'seasonality_index' in seasonality and seasonality['seasonality_index'] > Decimal('1'):
            recommendations.append("نوسانات فصلی بالا - نیاز به برنامه‌ریزی برای فصول کم‌رونق")
        
        # تحلیل انواع درآمد
        if 'سایر درآمدها' in revenue_by_type:
            other_revenue_percentage = revenue_by_type['سایر درآمدها']['percentage']
            if other_revenue_percentage > 30:
                recommendations.append("سهم سایر درآمدها بالا است - بررسی شفافیت منابع درآمدی")
        
        return recommendations
    
    def generate_revenue_report(self) -> Dict:
        """تولید گزارش کامل درآمد"""
        analysis = self.analyze_revenue()
        
        report = {
            'title': f'گزارش تحلیل درآمد - {self.company.name}',
            'period': self.period.name,
            'executive_summary': {
                'total_revenue': f"{analysis['total_revenue']['total']:,.0f} ریال",
                'revenue_sources': len(analysis['revenue_by_type']) - 1,  # منهای total
                'growth_status': analysis['growth_analysis']['growth_targets']['status'],
                'concentration_level': analysis['revenue_composition']['concentration_analysis']['concentration_level']
            },
            'detailed_analysis': {
                'revenue_breakdown': analysis['revenue_by_type'],
                'monthly_trend': analysis['monthly_trend'],
                'composition': analysis['revenue_composition']
            },
            'recommendations': analysis['recommendations']
        }
        
        return report


# ابزار LangChain برای تحلیل درآمد
class RevenueAnalysisTool:
    """ابزار تحلیل درآمد برای LangChain"""
    
    name = "revenue_analyzer"
    description = "تحلیل حساب‌های درآمدی و روند فروش"
    
    def __init__(self):
        self.analyzer_class = RevenueAnalyzer
    
    def analyze(self, company_id: int, period_id: int) -> Dict:
        """تحلیل درآمد برای شرکت و دوره مشخص"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            analyzer = RevenueAnalyzer(company, period)
            result = analyzer.analyze_revenue()
            
            return {
                'success': True,
                'analysis': result,
                'report': analyzer.generate_revenue_report()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
