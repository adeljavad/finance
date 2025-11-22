# financial_system/services/advanced_reporting.py
"""
تسک ۱۰۰: گزارش‌دهی پیشرفته
این سرویس برای تولید گزارش‌های مالی پیشرفته و سفارشی‌سازی شده طراحی شده است.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
import pandas as pd
from users.models import User, Company, FinancialPeriod
from financial_system.models import FinancialData, RatioAnalysis, ReportTemplate


class AdvancedReportingSystem:
    """سیستم گزارش‌دهی پیشرفته"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.report_templates = {}
        self.report_history = []
    
    def generate_comprehensive_report(self, company_id: int, period_id: int, 
                                   report_type: str = 'comprehensive') -> Dict[str, Any]:
        """تولید گزارش جامع مالی"""
        
        try:
            # دریافت داده‌های شرکت
            company_data = self._get_company_data(company_id, period_id)
            
            if not company_data:
                return {
                    'success': False,
                    'error': 'داده‌های شرکت یافت نشد'
                }
            
            # تولید بخش‌های مختلف گزارش
            executive_summary = self._generate_executive_summary(company_data)
            financial_analysis = self._generate_financial_analysis(company_data)
            ratio_analysis = self._generate_ratio_analysis(company_data)
            trend_analysis = self._generate_trend_analysis(company_id, period_id)
            industry_comparison = self._generate_industry_comparison(company_data)
            recommendations = self._generate_recommendations(company_data)
            
            # جمع‌بندی گزارش
            report = {
                'success': True,
                'report_id': self._generate_report_id(),
                'company_id': company_id,
                'company_name': company_data.get('company_name'),
                'period_id': period_id,
                'period_name': company_data.get('period_name'),
                'report_type': report_type,
                'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'executive_summary': executive_summary,
                'financial_analysis': financial_analysis,
                'ratio_analysis': ratio_analysis,
                'trend_analysis': trend_analysis,
                'industry_comparison': industry_comparison,
                'recommendations': recommendations,
                'key_metrics': self._extract_key_metrics(
                    executive_summary, financial_analysis, ratio_analysis
                )
            }
            
            # ذخیره گزارش در تاریخچه
            self._save_report_to_history(report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"خطا در تولید گزارش جامع: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_company_data(self, company_id: int, period_id: int) -> Optional[Dict[str, Any]]:
        """دریافت داده‌های شرکت"""
        
        try:
            company = Company.objects.filter(id=company_id).first()
            financial_data = FinancialData.objects.filter(
                company_id=company_id,
                period_id=period_id
            ).first()
            period = FinancialPeriod.objects.filter(id=period_id).first()
            
            if not company or not financial_data or not period:
                return None
            
            # محاسبه نسبت‌های مالی
            ratios = self._calculate_ratios(financial_data)
            
            return {
                'company_id': company_id,
                'company_name': company.name,
                'industry_code': company.industry_code,
                'period_id': period_id,
                'period_name': period.name,
                'financial_data': {
                    'revenue': financial_data.revenue,
                    'net_income': financial_data.net_income,
                    'total_assets': financial_data.total_assets,
                    'total_liabilities': financial_data.total_liabilities,
                    'equity': financial_data.equity,
                    'current_assets': financial_data.current_assets,
                    'current_liabilities': financial_data.current_liabilities,
                    'operating_cash_flow': financial_data.operating_cash_flow,
                    'investing_cash_flow': financial_data.investing_cash_flow,
                    'financing_cash_flow': financial_data.financing_cash_flow
                },
                'ratios': ratios
            }
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده‌های شرکت: {str(e)}")
            return None
    
    def _calculate_ratios(self, financial_data) -> Dict[str, Decimal]:
        """محاسبه نسبت‌های مالی"""
        
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
            
            # نسبت‌های جریان نقدی
            if financial_data.revenue and financial_data.revenue > 0:
                ratios['operating_cash_flow_margin'] = financial_data.operating_cash_flow / financial_data.revenue if financial_data.operating_cash_flow else 0
            
            return ratios
            
        except Exception as e:
            self.logger.error(f"خطا در محاسبه نسبت‌ها: {str(e)}")
            return {}
    
    def _generate_executive_summary(self, company_data: Dict) -> Dict[str, Any]:
        """تولید خلاصه مدیریتی"""
        
        try:
            financial_data = company_data.get('financial_data', {})
            ratios = company_data.get('ratios', {})
            
            # تحلیل کلی عملکرد
            revenue = financial_data.get('revenue', 0)
            net_income = financial_data.get('net_income', 0)
            total_assets = financial_data.get('total_assets', 0)
            
            # ارزیابی کلی عملکرد
            if net_income > 0:
                profitability_status = 'سودآور'
                profitability_color = 'success'
            else:
                profitability_status = 'زیان‌ده'
                profitability_color = 'danger'
            
            # تحلیل نقدینگی
            current_ratio = ratios.get('current_ratio', 0)
            if current_ratio >= 2.0:
                liquidity_status = 'عالی'
                liquidity_color = 'success'
            elif current_ratio >= 1.5:
                liquidity_status = 'خوب'
                liquidity_color = 'warning'
            elif current_ratio >= 1.0:
                liquidity_status = 'متوسط'
                liquidity_color = 'warning'
            else:
                liquidity_status = 'ضعیف'
                liquidity_color = 'danger'
            
            # تحلیل اهرم مالی
            debt_to_assets = ratios.get('debt_to_assets', 0)
            if debt_to_assets <= 0.3:
                leverage_status = 'کم'
                leverage_color = 'success'
            elif debt_to_assets <= 0.6:
                leverage_status = 'متوسط'
                leverage_color = 'warning'
            else:
                leverage_status = 'بالا'
                leverage_color = 'danger'
            
            return {
                'overview': {
                    'revenue': revenue,
                    'net_income': net_income,
                    'total_assets': total_assets,
                    'profitability_status': profitability_status,
                    'profitability_color': profitability_color,
                    'liquidity_status': liquidity_status,
                    'liquidity_color': liquidity_color,
                    'leverage_status': leverage_status,
                    'leverage_color': leverage_color
                },
                'key_achievements': self._identify_key_achievements(company_data),
                'major_challenges': self._identify_major_challenges(company_data),
                'strategic_highlights': self._generate_strategic_highlights(company_data)
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تولید خلاصه مدیریتی: {str(e)}")
            return {}
    
    def _identify_key_achievements(self, company_data: Dict) -> List[str]:
        """شناسایی دستاوردهای کلیدی"""
        
        achievements = []
        financial_data = company_data.get('financial_data', {})
        ratios = company_data.get('ratios', {})
        
        # تحلیل سودآوری
        net_income = financial_data.get('net_income', 0)
        if net_income > 0:
            achievements.append(f'سود خالص مثبت به مبلغ {net_income:,.0f}')
        
        # تحلیل نقدینگی
        current_ratio = ratios.get('current_ratio', 0)
        if current_ratio >= 2.0:
            achievements.append(f'نقدینگی قوی (نسبت جاری: {current_ratio:.1f})')
        
        # تحلیل کارایی
        asset_turnover = ratios.get('asset_turnover', 0)
        if asset_turnover >= 1.0:
            achievements.append(f'کارایی مناسب دارایی‌ها (گردش دارایی: {asset_turnover:.1f})')
        
        return achievements
    
    def _identify_major_challenges(self, company_data: Dict) -> List[str]:
        """شناسایی چالش‌های اصلی"""
        
        challenges = []
        financial_data = company_data.get('financial_data', {})
        ratios = company_data.get('ratios', {})
        
        # تحلیل سودآوری
        net_income = financial_data.get('net_income', 0)
        if net_income <= 0:
            challenges.append('سودآوری منفی و نیاز به بهبود عملکرد')
        
        # تحلیل اهرم مالی
        debt_to_assets = ratios.get('debt_to_assets', 0)
        if debt_to_assets > 0.6:
            challenges.append(f'اهرم مالی بالا (نسبت بدهی: {debt_to_assets:.1%})')
        
        # تحلیل نقدینگی
        current_ratio = ratios.get('current_ratio', 0)
        if current_ratio < 1.0:
            challenges.append(f'نقدینگی ضعیف (نسبت جاری: {current_ratio:.1f})')
        
        return challenges
    
    def _generate_strategic_highlights(self, company_data: Dict) -> List[Dict[str, Any]]:
        """تولید نکات برجسته استراتژیک"""
        
        highlights = []
        financial_data = company_data.get('financial_data', {})
        ratios = company_data.get('ratios', {})
        
        # تحلیل جریان نقدی عملیاتی
        operating_cash_flow = financial_data.get('operating_cash_flow', 0)
        if operating_cash_flow > 0:
            highlights.append({
                'title': 'جریان نقدی عملیاتی مثبت',
                'description': 'شرکت توانایی تولید جریان نقدی از عملیات اصلی را دارد',
                'impact': 'بالا',
                'metric': f'{operating_cash_flow:,.0f}'
            })
        
        # تحلیل بازده دارایی‌ها
        return_on_assets = ratios.get('return_on_assets', 0)
        if return_on_assets > 0.05:
            highlights.append({
                'title': 'بازده مناسب دارایی‌ها',
                'description': 'شرکت از دارایی‌های خود به طور مؤثر استفاده می‌کند',
                'impact': 'متوسط',
                'metric': f'{return_on_assets:.1%}'
            })
        
        # تحلیل حاشیه سود
        net_margin = ratios.get('net_margin', 0)
        if net_margin > 0.1:
            highlights.append({
                'title': 'حاشیه سود بالا',
                'description': 'شرکت در کنترل هزینه‌ها و مدیریت سودآوری موفق عمل کرده است',
                'impact': 'بالا',
                'metric': f'{net_margin:.1%}'
            })
        
        return highlights
    
    def _generate_financial_analysis(self, company_data: Dict) -> Dict[str, Any]:
        """تولید تحلیل مالی"""
        
        try:
            financial_data = company_data.get('financial_data', {})
            
            # تحلیل صورت سود و زیان
            income_statement_analysis = self._analyze_income_statement(financial_data)
            
            # تحلیل ترازنامه
            balance_sheet_analysis = self._analyze_balance_sheet(financial_data)
            
            # تحلیل صورت جریان نقدی
            cash_flow_analysis = self._analyze_cash_flow(financial_data)
            
            return {
                'income_statement': income_statement_analysis,
                'balance_sheet': balance_sheet_analysis,
                'cash_flow': cash_flow_analysis,
                'financial_health': self._assess_financial_health(financial_data)
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تولید تحلیل مالی: {str(e)}")
            return {}
    
    def _analyze_income_statement(self, financial_data: Dict) -> Dict[str, Any]:
        """تحلیل صورت سود و زیان"""
        
        try:
            revenue = financial_data.get('revenue', 0)
            net_income = financial_data.get('net_income', 0)
            
            # محاسبه حاشیه سود
            if revenue > 0:
                net_margin = net_income / revenue
            else:
                net_margin = 0
            
            # ارزیابی سودآوری
            if net_margin > 0.15:
                profitability_assessment = 'عالی'
            elif net_margin > 0.08:
                profitability_assessment = 'خوب'
            elif net_margin > 0:
                profitability_assessment = 'متوسط'
            else:
                profitability_assessment = 'ضعیف'
            
            return {
                'revenue': revenue,
                'net_income': net_income,
                'net_margin': net_margin,
                'profitability_assessment': profitability_assessment,
                'revenue_growth_trend': 'مثبت' if revenue > 0 else 'منفی',
                'profit_growth_trend': 'مثبت' if net_income > 0 else 'منفی'
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل صورت سود و زیان: {str(e)}")
            return {}
    
    def _analyze_balance_sheet(self, financial_data: Dict) -> Dict[str, Any]:
        """تحلیل ترازنامه"""
        
        try:
            total_assets = financial_data.get('total_assets', 0)
            total_liabilities = financial_data.get('total_liabilities', 0)
            equity = financial_data.get('equity', 0)
            current_assets = financial_data.get('current_assets', 0)
            current_liabilities = financial_data.get('current_liabilities', 0)
            
            # محاسبه نسبت‌ها
            if total_assets > 0:
                debt_ratio = total_liabilities / total_assets
            else:
                debt_ratio = 0
            
            if current_liabilities > 0:
                current_ratio = current_assets / current_liabilities
            else:
                current_ratio = 0
            
            # ارزیابی ساختار مالی
            if debt_ratio < 0.4:
                financial_structure = 'محافظه‌کارانه'
            elif debt_ratio < 0.6:
                financial_structure = 'متوازن'
            else:
                financial_structure = 'تهاجمی'
            
            # ارزیابی نقدینگی
            if current_ratio >= 2.0:
                liquidity_assessment = 'عالی'
            elif current_ratio >= 1.5:
                liquidity_assessment = 'خوب'
            elif current_ratio >= 1.0:
                liquidity_assessment = 'متوسط'
            else:
                liquidity_assessment = 'ضعیف'
            
            return {
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'equity': equity,
                'debt_ratio': debt_ratio,
                'current_ratio': current_ratio,
                'financial_structure': financial_structure,
                'liquidity_assessment': liquidity_assessment
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل ترازنامه: {str(e)}")
            return {}
    
    def _analyze_cash_flow(self, financial_data: Dict) -> Dict[str, Any]:
        """تحلیل صورت جریان نقدی"""
        
        try:
            operating_cash_flow = financial_data.get('operating_cash_flow', 0)
            investing_cash_flow = financial_data.get('investing_cash_flow', 0)
            financing_cash_flow = financial_data.get('financing_cash_flow', 0)
            
            # محاسبه جریان نقدی خالص
            net_cash_flow = operating_cash_flow + investing_cash_flow + financing_cash_flow
            
            # ارزیابی کیفیت جریان نقدی
            if operating_cash_flow > 0:
                cash_flow_quality = 'عالی'
            elif operating_cash_flow >= 0:
                cash_flow_quality = 'خوب'
            else:
                cash_flow_quality = 'ضعیف'
            
            # تحلیل الگوی جریان نقدی
            if operating_cash_flow > 0 and investing_cash_flow < 0 and financing_cash_flow < 0:
                cash_flow_pattern = 'رشد'
                pattern_description = 'شرکت در حال رشد و توسعه است'
            elif operating_cash_flow > 0 and investing_cash_flow < 0 and financing_cash_flow > 0:
                cash_flow_pattern = 'توسعه'
                pattern_description = 'شرکت در حال توسعه با تأمین مالی خارجی است'
            elif operating_cash_flow > 0 and investing_cash_flow > 0 and financing_cash_flow < 0:
                cash_flow_pattern = 'بلوغ'
                pattern_description = 'شرکت بالغ و سودآور است'
            else:
                cash_flow_pattern = 'نامشخص'
                pattern_description = 'الگوی جریان نقدی نیاز به بررسی دارد'
            
            return {
                'operating_cash_flow': operating_cash_flow,
                'investing_cash_flow': investing_cash_flow,
                'financing_cash_flow': financing_cash_flow,
                'net_cash_flow': net_cash_flow,
                'cash_flow_quality': cash_flow_quality,
                'cash_flow_pattern': cash_flow_pattern,
                'pattern_description': pattern_description
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل صورت جریان نقدی: {str(e)}")
            return {}
    
    def _assess_financial_health(self, financial_data: Dict) -> Dict[str, Any]:
        """ارزیابی سلامت مالی"""
        
        try:
            # جمع‌آوری معیارها
            current_ratio = financial_data.get('current_assets', 0) / financial_data.get('current_liabilities', 1)
            debt_ratio = financial_data.get('total_liabilities', 0) / financial_data.get('total_assets', 1)
            operating_cash_flow = financial_data.get('operating_cash_flow', 0)
            
            # محاسبه امتیاز سلامت مالی
            health_score = 0
            
            # معیار نقدینگی (۳۰٪)
            if current_ratio >= 2.0:
                health_score += 30
            elif current_ratio >= 1.5:
                health_score += 20
            elif current_ratio >= 1.0:
                health_score += 10
            
            # معیار اهرم مالی (۳۰٪)
            if debt_ratio <= 0.3:
                health_score += 30
            elif debt_ratio <= 0.5:
                health_score += 20
            elif debt_ratio <= 0.7:
                health_score += 10
            
            # معیار جریان نقدی (۴۰٪)
            if operating_cash_flow > 0:
                health_score += 40
            elif operating_cash_flow >= 0:
                health_score += 20
            
            # تعیین وضعیت سلامت مالی
            if health_score >= 80:
                health_status = 'عالی'
                health_color = 'success'
            elif health_score >= 60:
                health_status = 'خوب'
                health_color = 'warning'
            elif health_score >= 40:
                health_status = 'متوسط'
                health_color = 'warning'
            else:
                health_status = 'ضعیف'
                health_color = 'danger'
            
            return {
                'health_score': health_score,
                'health_status': health_status,
                'health_color': health_color,
                'components': {
                    'liquidity_score': min(30, int(current_ratio * 15)),
                    'leverage_score': min(30, int((1 - debt_ratio) * 30)),
                    'cash_flow_score': 40 if operating_cash_flow > 0 else 20 if operating_cash_flow >= 0 else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"خطا در ارزیابی سلامت مالی: {str(e)}")
            return {'health_score': 0, 'health_status': 'نامشخص', 'health_color': 'secondary'}
    
    def _generate_ratio_analysis(self, company_data: Dict) -> Dict[str, Any]:
        """تولید تحلیل نسبت‌ها"""
        
        try:
            ratios = company_data.get('ratios', {})
            
            # تحلیل نسبت‌های نقدینگی
            liquidity_analysis = self._analyze_liquidity_ratios(ratios)
            
            # تحلیل نسبت‌های اهرمی
            leverage_analysis = self._analyze_leverage_ratios(ratios)
            
            # تحلیل نسبت‌های سودآوری
            profitability_analysis = self._analyze_profitability_ratios(ratios)
            
            # تحلیل نسبت‌های فعالیت
            activity_analysis = self._analyze_activity_ratios(ratios)
            
            return {
                'liquidity': liquidity_analysis,
                'leverage': leverage_analysis,
                'profitability': profitability_analysis,
                'activity': activity_analysis,
                'overall_assessment': self._assess_overall_ratio_performance(ratios)
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تولید تحلیل نسبت‌ها: {str(e)}")
            return {}
    
    def _analyze_liquidity_ratios(self, ratios: Dict) -> Dict[str, Any]:
        """تحلیل نسبت‌های نقدینگی"""
        
        try:
            current_ratio = ratios.get('current_ratio', 0)
            
            # ارزیابی نقدینگی
            if current_ratio >= 2.0:
                assessment = 'عالی'
                description = 'شرکت از نقدینگی بسیار خوبی برخوردار است'
            elif current_ratio >= 1.5:
                assessment = 'خوب'
                description = 'شرکت نقدینگی مناسبی دارد'
            elif current_ratio >= 1.0:
                assessment = 'متوسط'
                description = 'نقدینگی شرکت در سطح قابل قبولی است'
            else:
                assessment = 'ضعیف'
                description = 'شرکت با چالش نقدینگی مواجه است'
            
            return {
                'current_ratio': current_ratio,
                'assessment': assessment,
                'description': description,
                'recommendation': 'افزایش دارایی‌های جاری یا کاهش بدهی‌های جاری' if current_ratio < 1.5 else 'حفظ وضعیت موجود'
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل نسبت‌های نقدینگی: {str(e)}")
            return {}
    
    def _analyze_leverage_ratios(self, ratios: Dict) -> Dict[str, Any]:
        """تحلیل نسبت‌های اهرمی"""
        
        try:
            debt_to_assets = ratios.get('debt_to_assets', 0)
            debt_to_equity = ratios.get('debt_to_equity', 0)
            
            # ارزیابی اهرم مالی
            if debt_to_assets <= 0.3:
                assessment = 'کم'
                description = 'شرکت از اهرم مالی محافظه‌کارانه‌ای استفاده می‌کند'
            elif debt_to_assets <= 0.6:
                assessment = 'متوازن'
                description = 'ساختار مالی شرکت متوازن است'
            else:
                assessment = 'بالا'
                description = 'شرکت از اهرم مالی بالایی برخوردار است'
            
            return {
                'debt_to_assets': debt_to_assets,
                'debt_to_equity': debt_to_equity,
                'assessment': assessment,
                'description': description,
                'recommendation': 'کاهش بدهی‌ها' if debt_to_assets > 0.6 else 'حفظ ساختار مالی'
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل نسبت‌های اهرمی: {str(e)}")
            return {}
    
    def _analyze_profitability_ratios(self, ratios: Dict) -> Dict[str, Any]:
        """تحلیل نسبت‌های سودآوری"""
        
        try:
            net_margin = ratios.get('net_margin', 0)
            return_on_assets = ratios.get('return_on_assets', 0)
            return_on_equity = ratios.get('return_on_equity', 0)
            
            # ارزیابی سودآوری
            if net_margin > 0.15:
                assessment = 'عالی'
                description = 'شرکت از سودآوری بسیار بالایی برخوردار است'
            elif net_margin > 0.08:
                assessment = 'خوب'
                description = 'سودآوری شرکت در سطح مطلوبی قرار دارد'
            elif net_margin > 0:
                assessment = 'متوسط'
                description = 'سودآوری شرکت نیاز به بهبود دارد'
            else:
                assessment = 'ضعیف'
                description = 'شرکت با چالش سودآوری مواجه است'
            
            return {
                'net_margin': net_margin,
                'return_on_assets': return_on_assets,
                'return_on_equity': return_on_equity,
                'assessment': assessment,
                'description': description,
                'recommendation': 'بهبود حاشیه سود از طریق کنترل هزینه‌ها' if net_margin < 0.08 else 'حفظ سطح سودآوری'
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل نسبت‌های سودآوری: {str(e)}")
            return {}
    
    def _analyze_activity_ratios(self, ratios: Dict) -> Dict[str, Any]:
        """تحلیل نسبت‌های فعالیت"""
        
        try:
            asset_turnover = ratios.get('asset_turnover', 0)
            
            # ارزیابی کارایی
            if asset_turnover >= 1.5:
                assessment = 'عالی'
                description = 'شرکت از دارایی‌های خود به طور بسیار مؤثر استفاده می‌کند'
            elif asset_turnover >= 1.0:
                assessment = 'خوب'
                description = 'کارایی استفاده از دارایی‌ها در سطح مطلوبی است'
            elif asset_turnover >= 0.5:
                assessment = 'متوسط'
                description = 'کارایی استفاده از دارایی‌ها نیاز به بهبود دارد'
            else:
                assessment = 'ضعیف'
                description = 'شرکت در استفاده از دارایی‌ها کارایی پایینی دارد'
            
            return {
                'asset_turnover': asset_turnover,
                'assessment': assessment,
                'description': description,
                'recommendation': 'بهبود مدیریت دارایی‌ها' if asset_turnover < 1.0 else 'حفظ سطح کارایی'
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل نسبت‌های فعالیت: {str(e)}")
            return {}
    
    def _assess_overall_ratio_performance(self, ratios: Dict) -> Dict[str, Any]:
        """ارزیابی کلی عملکرد نسبت‌ها"""
        
        try:
            # جمع‌آوری ارزیابی‌ها
            current_ratio = ratios.get('current_ratio', 0)
            debt_to_assets = ratios.get('debt_to_assets', 0)
            net_margin = ratios.get('net_margin', 0)
            asset_turnover = ratios.get('asset_turnover', 0)
            
            # محاسبه امتیاز کلی
            overall_score = 0
            
            # معیار نقدینگی (۲۵٪)
            if current_ratio >= 2.0:
                overall_score += 25
            elif current_ratio >= 1.5:
                overall_score += 20
            elif current_ratio >= 1.0:
                overall_score += 15
            else:
                overall_score += 5
            
            # معیار اهرم مالی (۲۵٪)
            if debt_to_assets <= 0.3:
                overall_score += 25
            elif debt_to_assets <= 0.5:
                overall_score += 20
            elif debt_to_assets <= 0.7:
                overall_score += 15
            else:
                overall_score += 5
            
            # معیار سودآوری (۲۵٪)
            if net_margin > 0.15:
                overall_score += 25
            elif net_margin > 0.08:
                overall_score += 20
            elif net_margin > 0:
                overall_score += 15
            else:
                overall_score += 5
            
            # معیار کارایی (۲۵٪)
            if asset_turnover >= 1.5:
                overall_score += 25
            elif asset_turnover >= 1.0:
                overall_score += 20
            elif asset_turnover >= 0.5:
                overall_score += 15
            else:
                overall_score += 5
            
            # تعیین وضعیت کلی
            if overall_score >= 80:
                overall_assessment = 'عالی'
                overall_color = 'success'
            elif overall_score >= 60:
                overall_assessment = 'خوب'
                overall_color = 'warning'
            elif overall_score >= 40:
                overall_assessment = 'متوسط'
                overall_color = 'warning'
            else:
                overall_assessment = 'ضعیف'
                overall_color = 'danger'
            
            return {
                'overall_score': overall_score,
                'overall_assessment': overall_assessment,
                'overall_color': overall_color,
                'component_scores': {
                    'liquidity': min(25, int(current_ratio * 12.5)),
                    'leverage': min(25, int((1 - debt_to_assets) * 25)),
                    'profitability': min(25, int(net_margin * 166.67)),
                    'efficiency': min(25, int(asset_turnover * 16.67))
                }
            }
            
        except Exception as e:
            self.logger.error(f"خطا در ارزیابی کلی عملکرد نسبت‌ها: {str(e)}")
            return {'overall_score': 0, 'overall_assessment': 'نامشخص', 'overall_color': 'secondary'}
    
    def _generate_trend_analysis(self, company_id: int, period_id: int) -> Dict[str, Any]:
        """تولید تحلیل روند"""
        
        try:
            # دریافت داده‌های تاریخی
            historical_data = FinancialData.objects.filter(
                company_id=company_id
            ).order_by('-period_id')[:4]  # ۴ دوره اخیر
            
            if len(historical_data) < 2:
                return {
                    'available_periods': len(historical_data),
                    'trend_analysis': 'داده‌های کافی برای تحلیل روند موجود نیست'
                }
            
            # تحلیل روند درآمد
            revenue_trend = self._analyze_revenue_trend(historical_data)
            
            # تحلیل روند سود
            profit_trend = self._analyze_profit_trend(historical_data)
            
            # تحلیل روند دارایی‌ها
            assets_trend = self._analyze_assets_trend(historical_data)
            
            return {
                'available_periods': len(historical_data),
                'revenue_trend': revenue_trend,
                'profit_trend': profit_trend,
                'assets_trend': assets_trend,
                'overall_trend': self._assess_overall_trend(revenue_trend, profit_trend, assets_trend)
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تولید تحلیل روند: {str(e)}")
            return {'available_periods': 0, 'trend_analysis': 'خطا در تحلیل روند'}
    
    def _analyze_revenue_trend(self, historical_data: List) -> Dict[str, Any]:
        """تحلیل روند درآمد"""
        
        try:
            if len(historical_data) < 2:
                return {'trend': 'نامشخص', 'growth_rate': 0, 'description': 'داده‌های کافی نیست'}
            
            current_revenue = historical_data[0].revenue
            previous_revenue = historical_data[1].revenue
            
            if previous_revenue > 0:
                growth_rate = (current_revenue - previous_revenue) / previous_revenue
            else:
                growth_rate = 0
            
            if growth_rate > 0.1:
                trend = 'رشد قوی'
                description = 'درآمد شرکت در حال رشد قوی است'
            elif growth_rate > 0.05:
                trend = 'رشد متوسط'
                description = 'درآمد شرکت در حال رشد است'
            elif growth_rate > 0:
                trend = 'رشد کند'
                description = 'درآمد شرکت رشد کندی دارد'
            elif growth_rate == 0:
                trend = 'ثابت'
                description = 'درآمد شرکت ثابت مانده است'
            else:
                trend = 'کاهش'
                description = 'درآمد شرکت در حال کاهش است'
            
            return {
                'trend': trend,
                'growth_rate': round(growth_rate * 100, 1),
                'description': description,
                'current_revenue': current_revenue,
                'previous_revenue': previous_revenue
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل روند درآمد: {str(e)}")
            return {'trend': 'نامشخص', 'growth_rate': 0, 'description': 'خطا در تحلیل'}
    
    def _analyze_profit_trend(self, historical_data: List) -> Dict[str, Any]:
        """تحلیل روند سود"""
        
        try:
            if len(historical_data) < 2:
                return {'trend': 'نامشخص', 'growth_rate': 0, 'description': 'داده‌های کافی نیست'}
            
            current_profit = historical_data[0].net_income
            previous_profit = historical_data[1].net_income
            
            if previous_profit and previous_profit > 0:
                growth_rate = (current_profit - previous_profit) / previous_profit
            else:
                growth_rate = 0
            
            if growth_rate > 0.15:
                trend = 'رشد قوی'
                description = 'سود شرکت در حال رشد قوی است'
            elif growth_rate > 0.08:
                trend = 'رشد متوسط'
                description = 'سود شرکت در حال رشد است'
            elif growth_rate > 0:
                trend = 'رشد کند'
                description = 'سود شرکت رشد کندی دارد'
            elif growth_rate == 0:
                trend = 'ثابت'
                description = 'سود شرکت ثابت مانده است'
            else:
                trend = 'کاهش'
                description = 'سود شرکت در حال کاهش است'
            
            return {
                'trend': trend,
                'growth_rate': round(growth_rate * 100, 1),
                'description': description,
                'current_profit': current_profit,
                'previous_profit': previous_profit
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل روند سود: {str(e)}")
            return {'trend': 'نامشخص', 'growth_rate': 0, 'description': 'خطا در تحلیل'}
    
    def _analyze_assets_trend(self, historical_data: List) -> Dict[str, Any]:
        """تحلیل روند دارایی‌ها"""
        
        try:
            if len(historical_data) < 2:
                return {'trend': 'نامشخص', 'growth_rate': 0, 'description': 'داده‌های کافی نیست'}
            
            current_assets = historical_data[0].total_assets
            previous_assets = historical_data[1].total_assets
            
            if previous_assets > 0:
                growth_rate = (current_assets - previous_assets) / previous_assets
            else:
                growth_rate = 0
            
            if growth_rate > 0.1:
                trend = 'رشد قوی'
                description = 'دارایی‌های شرکت در حال رشد قوی است'
            elif growth_rate > 0.05:
                trend = 'رشد متوسط'
                description = 'دارایی‌های شرکت در حال رشد است'
            elif growth_rate > 0:
                trend = 'رشد کند'
                description = 'دارایی‌های شرکت رشد کندی دارد'
            elif growth_rate == 0:
                trend = 'ثابت'
                description = 'دارایی‌های شرکت ثابت مانده است'
            else:
                trend = 'کاهش'
                description = 'دارایی‌های شرکت در حال کاهش است'
            
            return {
                'trend': trend,
                'growth_rate': round(growth_rate * 100, 1),
                'description': description,
                'current_assets': current_assets,
                'previous_assets': previous_assets
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل روند دارایی‌ها: {str(e)}")
            return {'trend': 'نامشخص', 'growth_rate': 0, 'description': 'خطا در تحلیل'}
    
    def _assess_overall_trend(self, revenue_trend: Dict, profit_trend: Dict, assets_trend: Dict) -> Dict[str, Any]:
        """ارزیابی کلی روند"""
        
        try:
            # جمع‌آوری امتیازها
            revenue_score = self._calculate_trend_score(revenue_trend.get('trend', ''))
            profit_score = self._calculate_trend_score(profit_trend.get('trend', ''))
            assets_score = self._calculate_trend_score(assets_trend.get('trend', ''))
            
            # محاسبه امتیاز کلی
            overall_score = (revenue_score + profit_score + assets_score) / 3
            
            # تعیین وضعیت کلی
            if overall_score >= 80:
                overall_trend = 'بسیار مثبت'
                overall_color = 'success'
                description = 'شرکت در تمامی حوزه‌ها در حال رشد است'
            elif overall_score >= 60:
                overall_trend = 'مثبت'
                overall_color = 'warning'
                description = 'شرکت در اکثر حوزه‌ها عملکرد مثبت دارد'
            elif overall_score >= 40:
                overall_trend = 'متوازن'
                overall_color = 'warning'
                description = 'شرکت در برخی حوزه‌ها رشد و در برخی کاهش دارد'
            else:
                overall_trend = 'منفی'
                overall_color = 'danger'
                description = 'شرکت در اکثر حوزه‌ها با چالش مواجه است'
            
            return {
                'overall_score': round(overall_score, 1),
                'overall_trend': overall_trend,
                'overall_color': overall_color,
                'description': description,
                'component_scores': {
                    'revenue': revenue_score,
                    'profit': profit_score,
                    'assets': assets_score
                }
            }
            
        except Exception as e:
            self.logger.error(f"خطا در ارزیابی کلی روند: {str(e)}")
            return {'overall_score': 0, 'overall_trend': 'نامشخص', 'overall_color': 'secondary'}
    
    def _calculate_trend_score(self, trend: str) -> int:
        """محاسبه امتیاز روند"""
        
        trend_scores = {
            'رشد قوی': 100,
            'رشد متوسط': 80,
            'رشد کند': 60,
            'ثابت': 40,
            'کاهش': 20,
            'نامشخص': 0
        }
        
        return trend_scores.get(trend, 0)
    
    def _generate_industry_comparison(self, company_data: Dict) -> Dict[str, Any]:
        """تولید مقایسه صنعت"""
        
        try:
            # این بخش باید با سیستم تحلیل صنعت یکپارچه شود
            # فعلاً از داده‌های نمونه استفاده می‌کنیم
            
            return {
                'industry_position': 'متوسط',
                'competitive_advantage': 'متوسط',
                'market_share_trend': 'ثابت',
                'recommendations': [
                    'تمرکز بر بهبود حاشیه سود نسبت به رقبا',
                    'بهبود کارایی عملیاتی برای افزایش رقابت‌پذیری',
                    'تحلیل دقیق‌تر عملکرد رقبا در صنعت'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تولید مقایسه صنعت: {str(e)}")
            return {}
    
    def _generate_recommendations(self, company_data: Dict) -> List[Dict[str, Any]]:
        """تولید توصیه‌ها"""
        
        recommendations = []
        financial_data = company_data.get('financial_data', {})
        ratios = company_data.get('ratios', {})
        
        # تحلیل سودآوری
        net_margin = ratios.get('net_margin', 0)
        if net_margin < 0.05:
            recommendations.append({
                'category': 'سودآوری',
                'priority': 'بالا',
                'recommendation': 'بهبود حاشیه سود از طریق کنترل هزینه‌ها',
                'rationale': f'حاشیه سود خالص ({net_margin:.1%}) پایین‌تر از سطح مطلوب است',
                'expected_impact': 'افزایش ۱۰-۱۵٪ سودآوری',
                'implementation_steps': [
                    'بررسی ساختار هزینه‌ها',
                    'بهینه‌سازی فرآیندهای عملیاتی',
                    'مذاکره با تأمین‌کنندگان برای کاهش هزینه‌ها'
                ]
            })
        
        # تحلیل نقدینگی
        current_ratio = ratios.get('current_ratio', 0)
        if current_ratio < 1.5:
            recommendations.append({
                'category': 'نقدینگی',
                'priority': 'بسیار بالا',
                'recommendation': 'بهبود مدیریت نقدینگی',
                'rationale': f'نسبت جاری ({current_ratio:.1f}) پایین‌تر از سطح مطلوب است',
                'expected_impact': 'کاهش ریسک نقدینگی و افزایش انعطاف‌پذیری مالی',
                'implementation_steps': [
                    'بهبود مدیریت موجودی‌ها',
                    'بهینه‌سازی حساب‌های دریافتنی',
                    'بررسی خطوط اعتباری کوتاه‌مدت'
                ]
            })
        
        # تحلیل اهرم مالی
        debt_to_assets = ratios.get('debt_to_assets', 0)
        if debt_to_assets > 0.6:
            recommendations.append({
                'category': 'اهرم مالی',
                'priority': 'بالا',
                'recommendation': 'کاهش سطح بدهی‌ها',
                'rationale': f'نسبت بدهی به دارایی ({debt_to_assets:.1%}) بالاتر از سطح مطلوب است',
                'expected_impact': 'کاهش ریسک مالی و بهبود نرخ بهره',
                'implementation_steps': [
                    'برنامه‌ریزی برای بازپرداخت بدهی‌های پرریسک',
                    'جذب سرمایه از طریق افزایش سرمایه',
                    'بهبود جریان نقدی عملیاتی'
                ]
            })
        
        # تحلیل کارایی
        asset_turnover = ratios.get('asset_turnover', 0)
        if asset_turnover < 1.0:
            recommendations.append({
                'category': 'کارایی',
                'priority': 'متوسط',
                'recommendation': 'بهبود کارایی استفاده از دارایی‌ها',
                'rationale': f'گردش دارایی ({asset_turnover:.1f}) پایین‌تر از سطح مطلوب است',
                'expected_impact': 'افزایش بازده دارایی‌ها و بهبود سودآوری',
                'implementation_steps': [
                    'بررسی بهره‌وری دارایی‌های ثابت',
                    'بهبود مدیریت موجودی‌ها',
                    'بهینه‌سازی فرآیندهای تولید و توزیع'
                ]
            })
        
        return recommendations
    
    def _extract_key_metrics(self, executive_summary: Dict, financial_analysis: Dict, ratio_analysis: Dict) -> Dict[str, Any]:
        """استخراج معیارهای کلیدی"""
        
        try:
            overview = executive_summary.get('overview', {})
            health = financial_analysis.get('financial_health', {})
            overall_ratios = ratio_analysis.get('overall_assessment', {})
            
            return {
                'revenue': overview.get('revenue', 0),
                'net_income': overview.get('net_income', 0),
                'total_assets': overview.get('total_assets', 0),
                'current_ratio': ratio_analysis.get('liquidity', {}).get('current_ratio', 0),
                'debt_to_assets': ratio_analysis.get('leverage', {}).get('debt_to_assets', 0),
                'net_margin': ratio_analysis.get('profitability', {}).get('net_margin', 0),
                'asset_turnover': ratio_analysis.get('activity', {}).get('asset_turnover', 0),
                'financial_health_score': health.get('health_score', 0),
                'ratio_performance_score': overall_ratios.get('overall_score', 0),
                'profitability_status': overview.get('profitability_status', 'نامشخص'),
                'liquidity_status': overview.get('liquidity_status', 'نامشخص'),
                'leverage_status': overview.get('leverage_status', 'نامشخص')
            }
            
        except Exception as e:
            self.logger.error(f"خطا در استخراج معیارهای کلیدی: {str(e)}")
            return {}
    
    def _generate_report_id(self) -> str:
        """تولید شناسه گزارش"""
        
        return f"REP_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(datetime.now()))}"
    
    def _save_report_to_history(self, report: Dict[str, Any]) -> None:
        """ذخیره گزارش در تاریخچه"""
        
        try:
            self.report_history.append({
                'report_id': report.get('report_id'),
                'company_id': report.get('company_id'),
                'company_name': report.get('company_name'),
                'period_id': report.get('period_id'),
                'report_type': report.get('report_type'),
                'generation_date': report.get('generation_date'),
                'timestamp': datetime.now()
            })
            
            # محدود کردن تاریخچه به ۱۰۰ گزارش اخیر
            if len(self.report_history) > 100:
                self.report_history = self.report_history[-100:]
                
        except Exception as e:
            self.logger.error(f"خطا در ذخیره گزارش در تاریخچه: {str(e)}")
    
    def get_report_history(self, company_id: Optional[int] = None, days_back: int = 90) -> List[Dict[str, Any]]:
        """دریافت تاریخچه گزارش‌ها"""
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        filtered_history = [
            entry for entry in self.report_history
            if entry.get('timestamp', datetime.min) >= cutoff_date
        ]
        
        if company_id:
            filtered_history = [
                entry for entry in filtered_history
                if entry.get('company_id') == company_id
            ]
        
        return filtered_history


# ابزار LangChain برای گزارش‌دهی پیشرفته
class AdvancedReportingTool:
    """ابزار گزارش‌دهی پیشرفته برای LangChain"""
    
    name = "advanced_reporting"
    description = "تولید گزارش‌های مالی پیشرفته و جامع برای تحلیل عملکرد شرکت"
    
    def __init__(self):
        self.reporting_system = AdvancedReportingSystem()
    
    def generate_comprehensive_report(self, company_id: int, period_id: int, report_type: str = 'comprehensive') -> Dict:
        """تولید گزارش جامع مالی"""
        try:
            result = self.reporting_system.generate_comprehensive_report(company_id, period_id, report_type)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_report_history(self, company_id: Optional[int] = None, days_back: int = 90) -> Dict:
        """دریافت تاریخچه گزارش‌ها"""
        try:
            result = self.reporting_system.get_report_history(company_id, days_back)
            return {
                'success': True,
                'history': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
