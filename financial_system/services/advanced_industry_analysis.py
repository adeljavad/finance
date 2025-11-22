# financial_system/services/advanced_industry_analysis.py
"""
تسک ۹۹: تحلیل پیشرفته صنعت
این سرویس برای مقایسه عملکرد شرکت با رقبای صنعت و تحلیل روندهای صنعت طراحی شده است.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
from users.models import User, Company, FinancialPeriod
from financial_system.models import FinancialData, RatioAnalysis, IndustryData


class AdvancedIndustryAnalysis:
    """سیستم تحلیل پیشرفته صنعت"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.industry_data = {}
        self.comparison_history = []
    
    def analyze_industry_performance(self, company_id: int, period_id: int) -> Dict[str, Any]:
        """تحلیل عملکرد شرکت در مقایسه با صنعت"""
        
        try:
            # دریافت داده‌های شرکت
            company_data = self._get_company_financial_data(company_id, period_id)
            
            if not company_data:
                return {
                    'success': False,
                    'error': 'داده‌های مالی شرکت یافت نشد'
                }
            
            # دریافت داده‌های صنعت
            industry_data = self._get_industry_data(company_data.get('industry_code'))
            
            # تحلیل‌های مختلف
            ratio_comparison = self._compare_financial_ratios(company_data, industry_data)
            trend_analysis = self._analyze_industry_trends(company_data, industry_data)
            competitive_position = self._assess_competitive_position(company_data, industry_data)
            strategic_insights = self._generate_strategic_insights(company_data, industry_data)
            
            return {
                'success': True,
                'company_id': company_id,
                'period_id': period_id,
                'industry_code': company_data.get('industry_code'),
                'company_name': company_data.get('company_name'),
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'ratio_comparison': ratio_comparison,
                'trend_analysis': trend_analysis,
                'competitive_position': competitive_position,
                'strategic_insights': strategic_insights,
                'recommendations': self._generate_industry_recommendations(
                    ratio_comparison, competitive_position, strategic_insights
                )
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل صنعت: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_company_financial_data(self, company_id: int, period_id: int) -> Optional[Dict[str, Any]]:
        """دریافت داده‌های مالی شرکت"""
        
        try:
            # دریافت داده‌های شرکت از مدل
            company = Company.objects.filter(id=company_id).first()
            financial_data = FinancialData.objects.filter(
                company_id=company_id,
                period_id=period_id
            ).first()
            
            if not company or not financial_data:
                return None
            
            # محاسبه نسبت‌های مالی
            ratios = self._calculate_company_ratios(financial_data)
            
            return {
                'company_id': company_id,
                'company_name': company.name,
                'industry_code': company.industry_code,
                'period_id': period_id,
                'financial_data': {
                    'revenue': financial_data.revenue,
                    'net_income': financial_data.net_income,
                    'total_assets': financial_data.total_assets,
                    'equity': financial_data.equity,
                    'current_assets': financial_data.current_assets,
                    'current_liabilities': financial_data.current_liabilities
                },
                'ratios': ratios
            }
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده‌های شرکت: {str(e)}")
            return None
    
    def _calculate_company_ratios(self, financial_data) -> Dict[str, Decimal]:
        """محاسبه نسبت‌های مالی شرکت"""
        
        try:
            ratios = {}
            
            # نسبت‌های نقدینگی
            if financial_data.current_liabilities and financial_data.current_liabilities > 0:
                ratios['current_ratio'] = financial_data.current_assets / financial_data.current_liabilities
            
            # نسبت‌های اهرمی
            if financial_data.total_assets and financial_data.total_assets > 0:
                ratios['debt_to_assets'] = financial_data.total_liabilities / financial_data.total_assets
                ratios['debt_to_equity'] = financial_data.total_liabilities / financial_data.equity if financial_data.equity else 0
            
            # نسبت‌های سودآوری
            if financial_data.revenue and financial_data.revenue > 0:
                ratios['net_margin'] = financial_data.net_income / financial_data.revenue if financial_data.net_income else 0
                ratios['return_on_assets'] = financial_data.net_income / financial_data.total_assets if financial_data.net_income else 0
                ratios['return_on_equity'] = financial_data.net_income / financial_data.equity if financial_data.net_income and financial_data.equity else 0
            
            # نسبت‌های فعالیت
            if financial_data.total_assets and financial_data.total_assets > 0:
                ratios['asset_turnover'] = financial_data.revenue / financial_data.total_assets
            
            return ratios
            
        except Exception as e:
            self.logger.error(f"خطا در محاسبه نسبت‌های شرکت: {str(e)}")
            return {}
    
    def _get_industry_data(self, industry_code: str) -> Dict[str, Any]:
        """دریافت داده‌های صنعت"""
        
        try:
            # این بخش باید با پایگاه داده صنعت یکپارچه شود
            # فعلاً از داده‌های نمونه استفاده می‌کنیم
            
            industry_benchmarks = {
                'MANUFACTURING': {
                    'name': 'صنعت تولید',
                    'ratios': {
                        'current_ratio': {'average': 1.8, 'top_quartile': 2.5, 'bottom_quartile': 1.2},
                        'debt_to_assets': {'average': 0.45, 'top_quartile': 0.35, 'bottom_quartile': 0.60},
                        'net_margin': {'average': 0.08, 'top_quartile': 0.15, 'bottom_quartile': 0.02},
                        'return_on_assets': {'average': 0.06, 'top_quartile': 0.12, 'bottom_quartile': 0.01},
                        'return_on_equity': {'average': 0.12, 'top_quartile': 0.20, 'bottom_quartile': 0.04},
                        'asset_turnover': {'average': 1.2, 'top_quartile': 1.8, 'bottom_quartile': 0.8}
                    },
                    'growth_rates': {
                        'revenue_growth': {'average': 0.08, 'top_quartile': 0.15, 'bottom_quartile': 0.02},
                        'profit_growth': {'average': 0.06, 'top_quartile': 0.12, 'bottom_quartile': -0.05}
                    },
                    'market_share': {
                        'top_5_companies': 0.35,
                        'concentration_ratio': 0.42
                    }
                },
                'TECHNOLOGY': {
                    'name': 'صنعت فناوری',
                    'ratios': {
                        'current_ratio': {'average': 2.2, 'top_quartile': 3.0, 'bottom_quartile': 1.5},
                        'debt_to_assets': {'average': 0.25, 'top_quartile': 0.15, 'bottom_quartile': 0.40},
                        'net_margin': {'average': 0.12, 'top_quartile': 0.25, 'bottom_quartile': 0.03},
                        'return_on_assets': {'average': 0.10, 'top_quartile': 0.18, 'bottom_quartile': 0.04},
                        'return_on_equity': {'average': 0.18, 'top_quartile': 0.30, 'bottom_quartile': 0.08},
                        'asset_turnover': {'average': 0.9, 'top_quartile': 1.3, 'bottom_quartile': 0.6}
                    },
                    'growth_rates': {
                        'revenue_growth': {'average': 0.15, 'top_quartile': 0.25, 'bottom_quartile': 0.05},
                        'profit_growth': {'average': 0.12, 'top_quartile': 0.20, 'bottom_quartile': 0.02}
                    },
                    'market_share': {
                        'top_5_companies': 0.45,
                        'concentration_ratio': 0.55
                    }
                },
                'RETAIL': {
                    'name': 'صنعت خرده‌فروشی',
                    'ratios': {
                        'current_ratio': {'average': 1.5, 'top_quartile': 2.0, 'bottom_quartile': 1.0},
                        'debt_to_assets': {'average': 0.50, 'top_quartile': 0.40, 'bottom_quartile': 0.65},
                        'net_margin': {'average': 0.04, 'top_quartile': 0.08, 'bottom_quartile': 0.01},
                        'return_on_assets': {'average': 0.05, 'top_quartile': 0.09, 'bottom_quartile': 0.01},
                        'return_on_equity': {'average': 0.10, 'top_quartile': 0.16, 'bottom_quartile': 0.04},
                        'asset_turnover': {'average': 1.8, 'top_quartile': 2.5, 'bottom_quartile': 1.2}
                    },
                    'growth_rates': {
                        'revenue_growth': {'average': 0.06, 'top_quartile': 0.10, 'bottom_quartile': 0.01},
                        'profit_growth': {'average': 0.04, 'top_quartile': 0.08, 'bottom_quartile': -0.02}
                    },
                    'market_share': {
                        'top_5_companies': 0.28,
                        'concentration_ratio': 0.35
                    }
                }
            }
            
            return industry_benchmarks.get(industry_code, industry_benchmarks['MANUFACTURING'])
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده‌های صنعت: {str(e)}")
            return {}
    
    def _compare_financial_ratios(self, company_data: Dict, industry_data: Dict) -> Dict[str, Any]:
        """مقایسه نسبت‌های مالی با صنعت"""
        
        comparison_results = {}
        company_ratios = company_data.get('ratios', {})
        industry_ratios = industry_data.get('ratios', {})
        
        for ratio_name, company_value in company_ratios.items():
            if ratio_name in industry_ratios:
                industry_benchmark = industry_ratios[ratio_name]
                industry_average = industry_benchmark.get('average', 0)
                top_quartile = industry_benchmark.get('top_quartile', 0)
                bottom_quartile = industry_benchmark.get('bottom_quartile', 0)
                
                # محاسبه انحراف از میانگین صنعت
                if industry_average != 0:
                    deviation = (float(company_value) - industry_average) / industry_average
                else:
                    deviation = 0
                
                # تعیین موقعیت در صنعت
                if float(company_value) >= top_quartile:
                    position = 'ربع بالایی'
                    performance = 'عالی'
                elif float(company_value) >= industry_average:
                    position = 'بالاتر از میانگین'
                    performance = 'خوب'
                elif float(company_value) >= bottom_quartile:
                    position = 'پایین‌تر از میانگین'
                    performance = 'نیاز به بهبود'
                else:
                    position = 'ربع پایینی'
                    performance = 'ضعیف'
                
                comparison_results[ratio_name] = {
                    'company_value': float(company_value),
                    'industry_average': industry_average,
                    'deviation_percentage': round(deviation * 100, 1),
                    'position_in_industry': position,
                    'performance': performance,
                    'top_quartile': top_quartile,
                    'bottom_quartile': bottom_quartile
                }
        
        return comparison_results
    
    def _analyze_industry_trends(self, company_data: Dict, industry_data: Dict) -> Dict[str, Any]:
        """تحلیل روندهای صنعت"""
        
        try:
            trends = {}
            company_id = company_data.get('company_id')
            industry_code = company_data.get('industry_code')
            
            # دریافت داده‌های تاریخی شرکت
            historical_data = FinancialData.objects.filter(
                company_id=company_id
            ).order_by('-period_id')[:3]  # ۳ دوره اخیر
            
            if len(historical_data) >= 2:
                # تحلیل روند رشد درآمد
                current_revenue = historical_data[0].revenue
                previous_revenue = historical_data[1].revenue
                
                if previous_revenue > 0:
                    company_revenue_growth = (current_revenue - previous_revenue) / previous_revenue
                else:
                    company_revenue_growth = 0
                
                industry_growth = industry_data.get('growth_rates', {}).get('revenue_growth', {}).get('average', 0)
                
                trends['revenue_growth'] = {
                    'company_growth': round(company_revenue_growth * 100, 1),
                    'industry_average_growth': round(industry_growth * 100, 1),
                    'comparison': 'بالاتر از صنعت' if company_revenue_growth > industry_growth else 'پایین‌تر از صنعت',
                    'growth_gap': round((company_revenue_growth - industry_growth) * 100, 1)
                }
            
            # تحلیل روند سودآوری
            if len(historical_data) >= 2:
                current_profit = historical_data[0].net_income
                previous_profit = historical_data[1].net_income
                
                if previous_profit and previous_profit > 0:
                    company_profit_growth = (current_profit - previous_profit) / previous_profit
                else:
                    company_profit_growth = 0
                
                industry_profit_growth = industry_data.get('growth_rates', {}).get('profit_growth', {}).get('average', 0)
                
                trends['profit_growth'] = {
                    'company_growth': round(company_profit_growth * 100, 1),
                    'industry_average_growth': round(industry_profit_growth * 100, 1),
                    'comparison': 'بالاتر از صنعت' if company_profit_growth > industry_profit_growth else 'پایین‌تر از صنعت',
                    'growth_gap': round((company_profit_growth - industry_profit_growth) * 100, 1)
                }
            
            # تحلیل روندهای کلان صنعت
            trends['industry_macro_trends'] = self._get_industry_macro_trends(industry_code)
            
            return trends
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل روندهای صنعت: {str(e)}")
            return {}
    
    def _get_industry_macro_trends(self, industry_code: str) -> List[Dict[str, Any]]:
        """دریافت روندهای کلان صنعت"""
        
        macro_trends = {
            'MANUFACTURING': [
                {
                    'trend': 'دیجیتالی‌سازی',
                    'impact': 'بالا',
                    'description': 'اتوماسیون و استفاده از فناوری‌های دیجیتال در فرآیندهای تولید',
                    'opportunity': 'کاهش هزینه‌ها و افزایش کارایی',
                    'threat': 'نیاز به سرمایه‌گذاری در فناوری'
                },
                {
                    'trend': 'پایداری محیط زیست',
                    'impact': 'متوسط',
                    'description': 'افزایش تقاضا برای محصولات سازگار با محیط زیست',
                    'opportunity': 'دسترسی به بازارهای جدید',
                    'threat': 'افزایش هزینه‌های تولید'
                }
            ],
            'TECHNOLOGY': [
                {
                    'trend': 'هوش مصنوعی',
                    'impact': 'بسیار بالا',
                    'description': 'ادغام هوش مصنوعی در محصولات و خدمات',
                    'opportunity': 'ایجاد مزیت رقابتی و نوآوری',
                    'threat': 'رقابت شدید و نیاز به تخصص'
                },
                {
                    'trend': 'رایانش ابری',
                    'impact': 'بالا',
                    'description': 'مهاجرت به سرویس‌های ابری',
                    'opportunity': 'کاهش هزینه‌های زیرساخت',
                    'threat': 'وابستگی به ارائه‌دهندگان ابری'
                }
            ],
            'RETAIL': [
                {
                    'trend': 'تجارت الکترونیک',
                    'impact': 'بسیار بالا',
                    'description': 'رشد سریع خرید آنلاین و تغییر الگوهای مصرف',
                    'opportunity': 'دسترسی به بازارهای گسترده‌تر',
                    'threat': 'رقابت با غول‌های تجارت الکترونیک'
                },
                {
                    'trend': 'تجربه مشتری',
                    'impact': 'بالا',
                    'description': 'تمرکز بر تجربه مشتری و خدمات شخصی‌سازی شده',
                    'opportunity': 'افزایش وفاداری مشتریان',
                    'threat': 'افزایش انتظارات مشتریان'
                }
            ]
        }
        
        return macro_trends.get(industry_code, [])
    
    def _assess_competitive_position(self, company_data: Dict, industry_data: Dict) -> Dict[str, Any]:
        """ارزیابی موقعیت رقابتی شرکت"""
        
        try:
            competitive_position = {}
            company_ratios = company_data.get('ratios', {})
            industry_ratios = industry_data.get('ratios', {})
            
            # ارزیابی قدرت مالی
            financial_strength = self._assess_financial_strength(company_ratios, industry_ratios)
            competitive_position['financial_strength'] = financial_strength
            
            # ارزیابی سودآوری
            profitability_strength = self._assess_profitability_strength(company_ratios, industry_ratios)
            competitive_position['profitability_strength'] = profitability_strength
            
            # ارزیابی کارایی عملیاتی
            operational_efficiency = self._assess_operational_efficiency(company_ratios, industry_ratios)
            competitive_position['operational_efficiency'] = operational_efficiency
            
            # ارزیابی کلی موقعیت رقابتی
            overall_position = self._calculate_overall_competitive_position(
                financial_strength, profitability_strength, operational_efficiency
            )
            competitive_position['overall_position'] = overall_position
            
            return competitive_position
            
        except Exception as e:
            self.logger.error(f"خطا در ارزیابی موقعیت رقابتی: {str(e)}")
            return {}
    
    def _assess_financial_strength(self, company_ratios: Dict, industry_ratios: Dict) -> Dict[str, Any]:
        """ارزیابی قدرت مالی"""
        
        try:
            # تحلیل نسبت جاری
            current_ratio = company_ratios.get('current_ratio', 0)
            industry_current_ratio = industry_ratios.get('current_ratio', {}).get('average', 1.5)
            
            if current_ratio >= industry_current_ratio * 1.2:
                liquidity_score = 90
                liquidity_assessment = 'عالی'
            elif current_ratio >= industry_current_ratio:
                liquidity_score = 75
                liquidity_assessment = 'خوب'
            elif current_ratio >= industry_current_ratio * 0.8:
                liquidity_score = 60
                liquidity_assessment = 'متوسط'
            else:
                liquidity_score = 40
                liquidity_assessment = 'ضعیف'
            
            # تحلیل نسبت بدهی
            debt_to_assets = company_ratios.get('debt_to_assets', 0)
            industry_debt_to_assets = industry_ratios.get('debt_to_assets', {}).get('average', 0.5)
            
            if debt_to_assets <= industry_debt_to_assets * 0.8:
                debt_score = 90
                debt_assessment = 'عالی'
            elif debt_to_assets <= industry_debt_to_assets:
                debt_score = 75
                debt_assessment = 'خوب'
            elif debt_to_assets <= industry_debt_to_assets * 1.2:
                debt_score = 60
                debt_assessment = 'متوسط'
            else:
                debt_score = 40
                debt_assessment = 'ضعیف'
            
            # امتیاز کلی قدرت مالی
            overall_financial_score = (liquidity_score + debt_score) / 2
            
            return {
                'overall_score': round(overall_financial_score, 1),
                'liquidity': {
                    'score': liquidity_score,
                    'assessment': liquidity_assessment,
                    'company_ratio': current_ratio,
                    'industry_average': industry_current_ratio
                },
                'debt_management': {
                    'score': debt_score,
                    'assessment': debt_assessment,
                    'company_ratio': debt_to_assets,
                    'industry_average': industry_debt_to_assets
                },
                'strength_level': 'قوی' if overall_financial_score >= 80 else 'متوسط' if overall_financial_score >= 60 else 'ضعیف'
            }
            
        except Exception as e:
            self.logger.error(f"خطا در ارزیابی قدرت مالی: {str(e)}")
            return {'overall_score': 0, 'strength_level': 'نامشخص'}
    
    def _assess_profitability_strength(self, company_ratios: Dict, industry_ratios: Dict) -> Dict[str, Any]:
        """ارزیابی قدرت سودآوری"""
        
        try:
            # تحلیل حاشیه سود خالص
            net_margin = company_ratios.get('net_margin', 0)
            industry_net_margin = industry_ratios.get('net_margin', {}).get('average', 0.05)
            
            if net_margin >= industry_net_margin * 1.5:
                margin_score = 90
                margin_assessment = 'عالی'
            elif net_margin >= industry_net_margin:
                margin_score = 75
                margin_assessment = 'خوب'
            elif net_margin >= industry_net_margin * 0.7:
                margin_score = 60
                margin_assessment = 'متوسط'
            else:
                margin_score = 40
                margin_assessment = 'ضعیف'
            
            # تحلیل بازده دارایی‌ها
            return_on_assets = company_ratios.get('return_on_assets', 0)
            industry_roa = industry_ratios.get('return_on_assets', {}).get('average', 0.05)
            
            if return_on_assets >= industry_roa * 1.5:
                roa_score = 90
                roa_assessment = 'عالی'
            elif return_on_assets >= industry_roa:
                roa_score = 75
                roa_assessment = 'خوب'
            elif return_on_assets >= industry_roa * 0.7:
                roa_score = 60
                roa_assessment = 'متوسط'
            else:
                roa_score = 40
                roa_assessment = 'ضعیف'
            
            # امتیاز کلی سودآوری
            overall_profitability_score = (margin_score + roa_score) / 2
            
            return {
                'overall_score': round(overall_profitability_score, 1),
                'profit_margin': {
                    'score': margin_score,
                    'assessment': margin_assessment,
                    'company_ratio': net_margin,
                    'industry_average': industry_net_margin
                },
                'return_on_assets': {
                    'score': roa_score,
                    'assessment': roa_assessment,
                    'company_ratio': return_on_assets,
                    'industry_average': industry_roa
                },
                'strength_level': 'قوی' if overall_profitability_score >= 80 else 'متوسط' if overall_profitability_score >= 60 else 'ضعیف'
            }
            
        except Exception as e:
            self.logger.error(f"خطا در ارزیابی قدرت سودآوری: {str(e)}")
            return {'overall_score': 0, 'strength_level': 'نامشخص'}
    
    def _assess_operational_efficiency(self, company_ratios: Dict, industry_ratios: Dict) -> Dict[str, Any]:
        """ارزیابی کارایی عملیاتی"""
        
        try:
            # تحلیل گردش دارایی‌ها
            asset_turnover = company_ratios.get('asset_turnover', 0)
            industry_asset_turnover = industry_ratios.get('asset_turnover', {}).get('average', 1.0)
            
            if asset_turnover >= industry_asset_turnover * 1.3:
                turnover_score = 90
                turnover_assessment = 'عالی'
            elif asset_turnover >= industry_asset_turnover:
                turnover_score = 75
                turnover_assessment = 'خوب'
            elif asset_turnover >= industry_asset_turnover * 0.8:
                turnover_score = 60
                turnover_assessment = 'متوسط'
            else:
                turnover_score = 40
                turnover_assessment = 'ضعیف'
            
            # امتیاز کلی کارایی عملیاتی
            overall_efficiency_score = turnover_score
            
            return {
                'overall_score': round(overall_efficiency_score, 1),
                'asset_turnover': {
                    'score': turnover_score,
                    'assessment': turnover_assessment,
                    'company_ratio': asset_turnover,
                    'industry_average': industry_asset_turnover
                },
                'strength_level': 'قوی' if overall_efficiency_score >= 80 else 'متوسط' if overall_efficiency_score >= 60 else 'ضعیف'
            }
            
        except Exception as e:
            self.logger.error(f"خطا در ارزیابی کارایی عملیاتی: {str(e)}")
            return {'overall_score': 0, 'strength_level': 'نامشخص'}
    
    def _calculate_overall_competitive_position(self, financial_strength: Dict, 
                                              profitability_strength: Dict, 
                                              operational_efficiency: Dict) -> Dict[str, Any]:
        """محاسبه موقعیت رقابتی کلی"""
        
        try:
            financial_score = financial_strength.get('overall_score', 0)
            profitability_score = profitability_strength.get('overall_score', 0)
            efficiency_score = operational_efficiency.get('overall_score', 0)
            
            # وزن‌دهی به معیارها
            overall_score = (
                financial_score * 0.4 +      # قدرت مالی ۴۰٪
                profitability_score * 0.4 +  # سودآوری ۴۰٪
                efficiency_score * 0.2       # کارایی ۲۰٪
            )
            
            # تعیین موقعیت رقابتی
            if overall_score >= 85:
                position = 'رهبر بازار'
                description = 'شرکت در موقعیت رهبری بازار قرار دارد'
            elif overall_score >= 70:
                position = 'رقابت‌پذیر قوی'
                description = 'شرکت دارای مزیت رقابتی قوی است'
            elif overall_score >= 55:
                position = 'رقابت‌پذیر متوسط'
                description = 'شرکت در سطح متوسط صنعت قرار دارد'
            elif overall_score >= 40:
                position = 'ضعیف'
                description = 'شرکت در موقعیت رقابتی ضعیفی قرار دارد'
            else:
                position = 'بسیار ضعیف'
                description = 'شرکت با چالش‌های جدی رقابتی مواجه است'
            
            return {
                'overall_score': round(overall_score, 1),
                'competitive_position': position,
                'description': description,
                'component_scores': {
                    'financial_strength': financial_score,
                    'profitability_strength': profitability_score,
                    'operational_efficiency': efficiency_score
                }
            }
            
        except Exception as e:
            self.logger.error(f"خطا در محاسبه موقعیت رقابتی: {str(e)}")
            return {'overall_score': 0, 'competitive_position': 'نامشخص', 'description': 'خطا در محاسبه'}
    
    def _generate_strategic_insights(self, company_data: Dict, industry_data: Dict) -> List[Dict[str, Any]]:
        """تولید بینش‌های استراتژیک"""
        
        insights = []
        company_ratios = company_data.get('ratios', {})
        industry_ratios = industry_data.get('ratios', {})
        
        # تحلیل نقاط قوت
        strengths = self._identify_strengths(company_ratios, industry_ratios)
        if strengths:
            insights.append({
                'type': 'نقاط قوت',
                'title': 'مزیت‌های رقابتی شرکت',
                'description': 'شرکت در حوزه‌های زیر دارای عملکرد برتر نسبت به صنعت است',
                'items': strengths,
                'impact': 'بالا'
            })
        
        # تحلیل نقاط ضعف
        weaknesses = self._identify_weaknesses(company_ratios, industry_ratios)
        if weaknesses:
            insights.append({
                'type': 'نقاط ضعف',
                'title': 'حوزه‌های نیازمند بهبود',
                'description': 'شرکت در حوزه‌های زیر عملکرد ضعیف‌تری نسبت به صنعت دارد',
                'items': weaknesses,
                'impact': 'متوسط'
            })
        
        # تحلیل فرصت‌ها
        opportunities = self._identify_opportunities(company_data, industry_data)
        if opportunities:
            insights.append({
                'type': 'فرصت‌ها',
                'title': 'فرصت‌های رشد و توسعه',
                'description': 'فرصت‌های موجود برای بهبود موقعیت رقابتی',
                'items': opportunities,
                'impact': 'بالا'
            })
        
        # تحلیل تهدیدها
        threats = self._identify_threats(company_data, industry_data)
        if threats:
            insights.append({
                'type': 'تهدیدها',
                'title': 'ریسک‌ها و چالش‌های پیش رو',
                'description': 'تهدیدهای بالقوه برای موقعیت رقابتی شرکت',
                'items': threats,
                'impact': 'متوسط'
            })
        
        return insights
    
    def _identify_strengths(self, company_ratios: Dict, industry_ratios: Dict) -> List[str]:
        """شناسایی نقاط قوت"""
        
        strengths = []
        
        # تحلیل نسبت‌های مالی برتر
        for ratio_name, company_value in company_ratios.items():
            if ratio_name in industry_ratios:
                industry_average = industry_ratios[ratio_name].get('average', 0)
                top_quartile = industry_ratios[ratio_name].get('top_quartile', 0)
                
                if float(company_value) >= top_quartile:
                    if ratio_name == 'net_margin':
                        strengths.append(f'حاشیه سود خالص ({company_value:.1%}) در ربع بالایی صنعت')
                    elif ratio_name == 'return_on_assets':
                        strengths.append(f'بازده دارایی‌ها ({company_value:.1%}) در ربع بالایی صنعت')
                    elif ratio_name == 'current_ratio':
                        strengths.append(f'نقدینگی قوی (نسبت جاری: {company_value:.1f})')
        
        return strengths
    
    def _identify_weaknesses(self, company_ratios: Dict, industry_ratios: Dict) -> List[str]:
        """شناسایی نقاط ضعف"""
        
        weaknesses = []
        
        # تحلیل نسبت‌های مالی ضعیف
        for ratio_name, company_value in company_ratios.items():
            if ratio_name in industry_ratios:
                industry_average = industry_ratios[ratio_name].get('average', 0)
                bottom_quartile = industry_ratios[ratio_name].get('bottom_quartile', 0)
                
                if float(company_value) <= bottom_quartile:
                    if ratio_name == 'net_margin':
                        weaknesses.append(f'حاشیه سود خالص ({company_value:.1%}) در ربع پایینی صنعت')
                    elif ratio_name == 'debt_to_assets':
                        weaknesses.append(f'اهرم مالی بالا (نسبت بدهی: {company_value:.1%})')
                    elif ratio_name == 'asset_turnover':
                        weaknesses.append(f'کارایی پایین دارایی‌ها (گردش دارایی: {company_value:.1f})')
        
        return weaknesses
    
    def _identify_opportunities(self, company_data: Dict, industry_data: Dict) -> List[str]:
        """شناسایی فرصت‌ها"""
        
        opportunities = []
        industry_code = company_data.get('industry_code')
        
        # فرصت‌های مبتنی بر روندهای صنعت
        macro_trends = self._get_industry_macro_trends(industry_code)
        
        for trend in macro_trends:
            if trend.get('impact') in ['بسیار بالا', 'بالا']:
                opportunities.append(trend.get('opportunity', ''))
        
        # فرصت‌های مبتنی بر موقعیت رقابتی
        competitive_position = self._assess_competitive_position(company_data, industry_data)
        overall_score = competitive_position.get('overall_position', {}).get('overall_score', 0)
        
        if overall_score >= 70:
            opportunities.append('افزایش سهم بازار با استفاده از مزیت رقابتی موجود')
        elif overall_score >= 55:
            opportunities.append('بهبود موقعیت رقابتی از طریق تمرکز بر حوزه‌های کلیدی')
        
        return [opp for opp in opportunities if opp]  # حذف موارد خالی
    
    def _identify_threats(self, company_data: Dict, industry_data: Dict) -> List[str]:
        """شناسایی تهدیدها"""
        
        threats = []
        industry_code = company_data.get('industry_code')
        
        # تهدیدهای مبتنی بر روندهای صنعت
        macro_trends = self._get_industry_macro_trends(industry_code)
        
        for trend in macro_trends:
            if trend.get('impact') in ['بسیار بالا', 'بالا']:
                threats.append(trend.get('threat', ''))
        
        # تهدیدهای مبتنی بر موقعیت رقابتی
        competitive_position = self._assess_competitive_position(company_data, industry_data)
        overall_score = competitive_position.get('overall_position', {}).get('overall_score', 0)
        
        if overall_score < 55:
            threats.append('فشار رقابتی شدید از سوی شرکت‌های بزرگتر')
        
        # تهدیدهای مبتنی بر ساختار صنعت
        market_concentration = industry_data.get('market_share', {}).get('concentration_ratio', 0)
        if market_concentration > 0.4:
            threats.append('تمرکز بالای بازار و قدرت شرکت‌های بزرگ')
        
        return [threat for threat in threats if threat]  # حذف موارد خالی
    
    def _generate_industry_recommendations(self, ratio_comparison: Dict, 
                                         competitive_position: Dict, 
                                         strategic_insights: List[Dict]) -> List[Dict[str, Any]]:
        """تولید توصیه‌های صنعت"""
        
        recommendations = []
        
        # تحلیل نسبت‌های مالی برای تولید توصیه‌ها
        for ratio_name, comparison in ratio_comparison.items():
            performance = comparison.get('performance', '')
            deviation = comparison.get('deviation_percentage', 0)
            
            if performance == 'ضعیف':
                if ratio_name == 'net_margin':
                    recommendations.append({
                        'category': 'سودآوری',
                        'priority': 'بالا',
                        'recommendation': 'بهبود حاشیه سود از طریق کنترل هزینه‌ها',
                        'rationale': f'حاشیه سود {deviation}% پایین‌تر از میانگین صنعت است',
                        'expected_impact': 'افزایش ۱۰-۱۵٪ سودآوری'
                    })
                elif ratio_name == 'current_ratio':
                    recommendations.append({
                        'category': 'نقدینگی',
                        'priority': 'بسیار بالا',
                        'recommendation': 'بهبود مدیریت نقدینگی',
                        'rationale': f'نسبت جاری {deviation}% پایین‌تر از میانگین صنعت است',
                        'expected_impact': 'کاهش ریسک نقدینگی'
                    })
        
        # تحلیل موقعیت رقابتی برای تولید توصیه‌ها
        overall_position = competitive_position.get('overall_position', {})
        competitive_score = overall_position.get('overall_score', 0)
        
        if competitive_score < 60:
            recommendations.append({
                'category': 'استراتژی رقابتی',
                'priority': 'بالا',
                'recommendation': 'تمرکز بر ایجاد مزیت رقابتی پایدار',
                'rationale': f'موقعیت رقابتی شرکت (امتیاز: {competitive_score}) نیاز به بهبود دارد',
                'expected_impact': 'افزایش سهم بازار و حاشیه سود'
            })
        
        # تحلیل بینش‌های استراتژیک برای تولید توصیه‌ها
        for insight in strategic_insights:
            if insight['type'] == 'نقاط ضعف' and insight['impact'] == 'متوسط':
                recommendations.append({
                    'category': 'بهبود عملکرد',
                    'priority': 'متوسط',
                    'recommendation': 'تمرکز بر حوزه‌های نیازمند بهبود',
                    'rationale': 'شناسایی نقاط ضعف در عملکرد نسبت به صنعت',
                    'expected_impact': 'بهبود موقعیت رقابتی'
                })
        
        return recommendations
    
    def get_industry_comparison_history(self, company_id: Optional[int] = None, days_back: int = 90) -> List[Dict[str, Any]]:
        """دریافت تاریخچه مقایسه صنعت"""
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        filtered_history = [
            entry for entry in self.comparison_history
            if entry.get('timestamp', datetime.min) >= cutoff_date
        ]
        
        if company_id:
            filtered_history = [
                entry for entry in filtered_history
                if entry.get('company_id') == company_id
            ]
        
        return filtered_history


# ابزار LangChain برای تحلیل پیشرفته صنعت
class AdvancedIndustryAnalysisTool:
    """ابزار تحلیل پیشرفته صنعت برای LangChain"""
    
    name = "advanced_industry_analysis"
    description = "تحلیل عملکرد شرکت در مقایسه با صنعت و ارزیابی موقعیت رقابتی"
    
    def __init__(self):
        self.industry_analysis = AdvancedIndustryAnalysis()
    
    def analyze_industry_performance(self, company_id: int, period_id: int) -> Dict:
        """تحلیل عملکرد شرکت در مقایسه با صنعت"""
        try:
            result = self.industry_analysis.analyze_industry_performance(company_id, period_id)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_industry_comparison_history(self, company_id: Optional[int] = None, days_back: int = 90) -> Dict:
        """دریافت تاریخچه مقایسه صنعت"""
        try:
            result = self.industry_analysis.get_industry_comparison_history(company_id, days_back)
            return {
                'success': True,
                'history': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
