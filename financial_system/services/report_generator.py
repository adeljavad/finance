# financial_system/services/report_generator.py
"""
تسک ۹۲: ایجاد تولید گزارش تحلیلی خودکار
این سرویس برای تولید گزارش‌های مالی حرفه‌ای طراحی شده است.
"""

import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any
from financial_system.services.balance_sheet_analyzer import BalanceSheetAnalyzer
from financial_system.services.cash_bank_analyzer import CashBankAnalyzer
from financial_system.services.revenue_analyzer import RevenueAnalyzer
from financial_system.services.expense_analyzer import ExpenseAnalyzer
from users.models import Company, FinancialPeriod


class FinancialReportGenerator:
    """تولیدکننده گزارش‌های مالی"""
    
    def __init__(self, company: Company, period: FinancialPeriod):
        self.company = company
        self.period = period
        self.analyzers = {
            'balance_sheet': BalanceSheetAnalyzer(company, period),
            'cash_bank': CashBankAnalyzer(company, period),
            'revenue': RevenueAnalyzer(company, period),
            'expense': ExpenseAnalyzer(company, period)
        }
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """تولید گزارش جامع مالی"""
        
        # جمع‌آوری داده‌ها از تمام تحلیل‌گرها
        balance_sheet_analysis = self.analyzers['balance_sheet'].analyze_balance_sheet()
        cash_bank_analysis = self.analyzers['cash_bank'].analyze_cash_bank()
        revenue_analysis = self.analyzers['revenue'].analyze_revenue()
        expense_analysis = self.analyzers['expense'].analyze_expenses()
        
        # تحلیل کلی وضعیت مالی
        overall_assessment = self._assess_overall_financial_health(
            balance_sheet_analysis,
            cash_bank_analysis,
            revenue_analysis,
            expense_analysis
        )
        
        # تولید گزارش
        report = {
            'metadata': {
                'title': f'گزارش جامع مالی - {self.company.name}',
                'period': self.period.name,
                'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'report_id': f"FR-{self.company.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            },
            'executive_summary': self._generate_executive_summary(
                balance_sheet_analysis,
                cash_bank_analysis,
                revenue_analysis,
                expense_analysis,
                overall_assessment
            ),
            'detailed_analysis': {
                'balance_sheet': balance_sheet_analysis,
                'cash_bank': cash_bank_analysis,
                'revenue': revenue_analysis,
                'expense': expense_analysis
            },
            'key_indicators': self._extract_key_indicators(
                balance_sheet_analysis,
                cash_bank_analysis,
                revenue_analysis,
                expense_analysis
            ),
            'risk_assessment': self._assess_risks(
                balance_sheet_analysis,
                cash_bank_analysis,
                revenue_analysis,
                expense_analysis
            ),
            'strategic_recommendations': self._generate_strategic_recommendations(
                balance_sheet_analysis,
                cash_bank_analysis,
                revenue_analysis,
                expense_analysis,
                overall_assessment
            )
        }
        
        return report
    
    def _assess_overall_financial_health(self, balance_sheet: Dict, cash_bank: Dict, 
                                       revenue: Dict, expense: Dict) -> Dict[str, Any]:
        """ارزیابی کلی سلامت مالی"""
        
        scores = {
            'liquidity': self._calculate_liquidity_score(cash_bank, balance_sheet),
            'profitability': self._calculate_profitability_score(revenue, expense),
            'solvency': self._calculate_solvency_score(balance_sheet),
            'efficiency': self._calculate_efficiency_score(revenue, expense),
            'growth': self._calculate_growth_score(revenue)
        }
        
        overall_score = sum(scores.values()) / len(scores)
        
        return {
            'scores': scores,
            'overall_score': overall_score,
            'health_level': self._determine_health_level(overall_score),
            'trend': self._assess_trend(scores)
        }
    
    def _calculate_liquidity_score(self, cash_bank: Dict, balance_sheet: Dict) -> float:
        """محاسبه امتیاز نقدینگی"""
        try:
            current_ratio = balance_sheet['detailed_analysis']['ratios'].get('current_ratio', 0)
            cash_ratio = cash_bank['liquidity_analysis']['ratios'].get('cash_ratio', 0)
            
            # نمره‌دهی بر اساس استانداردها
            score = 0.0
            
            # امتیاز نسبت جاری
            if current_ratio >= 2.0:
                score += 0.4
            elif current_ratio >= 1.5:
                score += 0.3
            elif current_ratio >= 1.0:
                score += 0.2
            else:
                score += 0.1
            
            # امتیاز نسبت نقدی
            if cash_ratio >= 0.5:
                score += 0.3
            elif cash_ratio >= 0.3:
                score += 0.2
            elif cash_ratio >= 0.1:
                score += 0.1
            
            # امتیاز مانده نقدی
            total_cash = cash_bank['liquidity_analysis']['total_cash_bank']
            current_liabilities = cash_bank['liquidity_analysis'].get('current_liabilities', 1)
            cash_coverage = total_cash / current_liabilities if current_liabilities > 0 else 0
            
            if cash_coverage >= 0.3:
                score += 0.3
            elif cash_coverage >= 0.2:
                score += 0.2
            elif cash_coverage >= 0.1:
                score += 0.1
            
            return min(1.0, score)
        except:
            return 0.5  # امتیاز متوسط در صورت خطا
    
    def _calculate_profitability_score(self, revenue: Dict, expense: Dict) -> float:
        """محاسبه امتیاز سودآوری"""
        try:
            total_revenue = revenue['total_revenue']['total']
            total_expenses = expense['total_expenses']['total']
            
            if total_revenue == 0:
                return 0.2  # امتیاز پایین برای شرکت بدون درآمد
            
            profit_margin = (total_revenue - total_expenses) / total_revenue
            
            if profit_margin > 0.2:
                return 0.9
            elif profit_margin > 0.1:
                return 0.7
            elif profit_margin > 0.05:
                return 0.5
            elif profit_margin > 0:
                return 0.3
            else:
                return 0.1
        except:
            return 0.5
    
    def _calculate_solvency_score(self, balance_sheet: Dict) -> float:
        """محاسبه امتیاز توانایی پرداخت بدهی"""
        try:
            debt_ratio = balance_sheet['detailed_analysis']['ratios'].get('debt_ratio', 0)
            equity_ratio = balance_sheet['detailed_analysis']['ratios'].get('equity_ratio', 0)
            
            score = 0.0
            
            # امتیاز نسبت بدهی
            if debt_ratio < 0.4:
                score += 0.5
            elif debt_ratio < 0.6:
                score += 0.3
            elif debt_ratio < 0.8:
                score += 0.1
            
            # امتیاز نسبت حقوق صاحبان سهام
            if equity_ratio > 0.4:
                score += 0.5
            elif equity_ratio > 0.3:
                score += 0.3
            elif equity_ratio > 0.2:
                score += 0.1
            
            return min(1.0, score)
        except:
            return 0.5
    
    def _calculate_efficiency_score(self, revenue: Dict, expense: Dict) -> float:
        """محاسبه امتیاز کارایی"""
        try:
            expense_ratio = expense['cost_efficiency']['efficiency_ratios'].get('expense_to_revenue_ratio', 100)
            
            if expense_ratio < 60:
                return 0.9
            elif expense_ratio < 70:
                return 0.7
            elif expense_ratio < 80:
                return 0.5
            elif expense_ratio < 90:
                return 0.3
            else:
                return 0.1
        except:
            return 0.5
    
    def _calculate_growth_score(self, revenue: Dict) -> float:
        """محاسبه امتیاز رشد"""
        try:
            growth_rate = revenue['monthly_trend'].get('growth_rate', 0)
            
            if growth_rate > 20:
                return 0.9
            elif growth_rate > 10:
                return 0.7
            elif growth_rate > 5:
                return 0.5
            elif growth_rate > 0:
                return 0.3
            else:
                return 0.1
        except:
            return 0.5
    
    def _determine_health_level(self, overall_score: float) -> str:
        """تعیین سطح سلامت مالی"""
        if overall_score >= 0.8:
            return "عالی"
        elif overall_score >= 0.6:
            return "خوب"
        elif overall_score >= 0.4:
            return "متوسط"
        elif overall_score >= 0.2:
            return "ضعیف"
        else:
            return "بحرانی"
    
    def _assess_trend(self, scores: Dict[str, float]) -> str:
        """ارزیابی روند کلی"""
        # این تحلیل نیاز به داده‌های تاریخی دارد
        # فعلاً بر اساس توزیع امتیازها ارزیابی می‌شود
        good_scores = sum(1 for score in scores.values() if score >= 0.6)
        poor_scores = sum(1 for score in scores.values() if score < 0.4)
        
        if good_scores >= 3:
            return "صعودی"
        elif poor_scores >= 3:
            return "نزولی"
        else:
            return "ثابت"
    
    def _generate_executive_summary(self, balance_sheet: Dict, cash_bank: Dict, 
                                  revenue: Dict, expense: Dict, 
                                  overall_assessment: Dict) -> Dict[str, Any]:
        """تولید خلاصه مدیریتی"""
        
        return {
            'company_overview': {
                'name': self.company.name,
                'period': self.period.name,
                'financial_health': overall_assessment['health_level'],
                'overall_score': f"{overall_assessment['overall_score']:.1%}",
                'trend': overall_assessment['trend']
            },
            'key_highlights': self._extract_key_highlights(
                balance_sheet, cash_bank, revenue, expense
            ),
            'critical_issues': self._identify_critical_issues(
                balance_sheet, cash_bank, revenue, expense
            ),
            'immediate_actions': self._suggest_immediate_actions(
                balance_sheet, cash_bank, revenue, expense
            )
        }
    
    def _extract_key_highlights(self, balance_sheet: Dict, cash_bank: Dict, 
                              revenue: Dict, expense: Dict) -> List[str]:
        """استخراج نکات کلیدی"""
        highlights = []
        
        # نکات مثبت
        if balance_sheet['is_balanced']:
            highlights.append("ترازنامه کاملاً متوازن است")
        
        cash_ratio = cash_bank['liquidity_analysis']['ratios'].get('cash_ratio', 0)
        if cash_ratio > 0.3:
            highlights.append("نقدینگی در سطح مناسب قرار دارد")
        
        revenue_growth = revenue['monthly_trend'].get('growth_rate', 0)
        if revenue_growth > 10:
            highlights.append(f"رشد درآمدی قوی ({revenue_growth:.1f}%)")
        
        expense_ratio = expense['cost_efficiency']['efficiency_ratios'].get('expense_to_revenue_ratio', 100)
        if expense_ratio < 70:
            highlights.append("کارایی هزینه‌ها در سطح مطلوب")
        
        return highlights
    
    def _identify_critical_issues(self, balance_sheet: Dict, cash_bank: Dict, 
                                revenue: Dict, expense: Dict) -> List[str]:
        """شناسایی مسائل بحرانی"""
        issues = []
        
        # مسائل مربوط به ترازنامه
        if not balance_sheet['is_balanced']:
            issues.append(f"ترازنامه نامتوازن (تفاوت: {balance_sheet['difference']:,.0f} ریال)")
        
        # مسائل مربوط به نقدینگی
        cash_ratio = cash_bank['liquidity_analysis']['ratios'].get('cash_ratio', 0)
        if cash_ratio < 0.1:
            issues.append("نقدینگی بسیار پایین - ریسک پرداخت‌های جاری")
        
        # مسائل مربوط به درآمد
        if revenue['total_revenue']['total'] == 0:
            issues.append("هیچ درآمدی ثبت نشده است")
        
        # مسائل مربوط به هزینه
        expense_ratio = expense['cost_efficiency']['efficiency_ratios'].get('expense_to_revenue_ratio', 100)
        if expense_ratio > 90:
            issues.append("نسبت هزینه به درآمد بسیار بالا")
        
        return issues
    
    def _suggest_immediate_actions(self, balance_sheet: Dict, cash_bank: Dict, 
                                 revenue: Dict, expense: Dict) -> List[str]:
        """پیشنهاد اقدامات فوری"""
        actions = []
        
        # اقدامات مربوط به ترازنامه
        if not balance_sheet['is_balanced']:
            actions.append("بررسی و اصلاح ترازنامه نامتوازن")
        
        # اقدامات مربوط به نقدینگی
        cash_ratio = cash_bank['liquidity_analysis']['ratios'].get('cash_ratio', 0)
        if cash_ratio < 0.2:
            actions.append("افزایش موجودی نقدی یا کاهش بدهی‌های جاری")
        
        # اقدامات مربوط به درآمد
        if revenue['total_revenue']['total'] == 0:
            actions.append("بررسی فرآیندهای فروش و درآمدزایی")
        
        # اقدامات مربوط به هزینه
        expense_ratio = expense['cost_efficiency']['efficiency_ratios'].get('expense_to_revenue_ratio', 100)
        if expense_ratio > 80:
            actions.append("برنامه‌ریزی برای کاهش هزینه‌ها")
        
        return actions
    
    def _extract_key_indicators(self, balance_sheet: Dict, cash_bank: Dict, 
                              revenue: Dict, expense: Dict) -> Dict[str, Any]:
        """استخراج شاخص‌های کلیدی"""
        
        return {
            'profitability': {
                'revenue': revenue['total_revenue']['total'],
                'expenses': expense['total_expenses']['total'],
                'net_income': revenue['total_revenue']['total'] - expense['total_expenses']['total'],
                'profit_margin': self._calculate_profit_margin(revenue, expense)
            },
            'liquidity': {
                'current_ratio': balance_sheet['detailed_analysis']['ratios'].get('current_ratio', 0),
                'cash_ratio': cash_bank['liquidity_analysis']['ratios'].get('cash_ratio', 0),
                'quick_ratio': self._calculate_quick_ratio(balance_sheet, cash_bank)
            },
            'solvency': {
                'debt_ratio': balance_sheet['detailed_analysis']['ratios'].get('debt_ratio', 0),
                'equity_ratio': balance_sheet['detailed_analysis']['ratios'].get('equity_ratio', 0),
                'debt_to_equity': self._calculate_debt_to_equity(balance_sheet)
            },
            'efficiency': {
                'expense_to_revenue_ratio': expense['cost_efficiency']['efficiency_ratios'].get('expense_to_revenue_ratio', 0),
                'asset_turnover': self._calculate_asset_turnover(balance_sheet, revenue)
            },
            'growth': {
                'revenue_growth': revenue['monthly_trend'].get('growth_rate', 0),
                'expense_growth': expense['monthly_trend'].get('growth_rate', 0)
            }
        }
    
    def _calculate_profit_margin(self, revenue: Dict, expense: Dict) -> float:
        """محاسبه حاشیه سود"""
        try:
            net_income = revenue['total_revenue']['total'] - expense['total_expenses']['total']
            return (net_income / revenue['total_revenue']['total']) * 100 if revenue['total_revenue']['total'] > 0 else 0
        except:
            return 0
    
    def _calculate_quick_ratio(self, balance_sheet: Dict, cash_bank: Dict) -> float:
        """محاسبه نسبت سریع"""
        try:
            current_assets = balance_sheet['total_assets']['current_assets']['total']
            inventory = Decimal('0')  # نیاز به داده‌های دقیق‌تر برای موجودی
            current_liabilities = cash_bank['liquidity_analysis'].get('current_liabilities', 1)
            
            quick_assets = current_assets - inventory
            return quick_assets / current_liabilities if current_liabilities > 0 else 0
        except:
            return 0
    
    def _calculate_debt_to_equity(self, balance_sheet: Dict) -> float:
        """محاسبه نسبت بدهی به سرمایه"""
        try:
            total_liabilities = balance_sheet['total_liabilities_equity']['liabilities']['total']
            total_equity = balance_sheet['total_liabilities_equity']['equity']['total']
            
            return total_liabilities / total_equity if total_equity > 0 else 0
        except:
            return 0
    
    def _calculate_asset_turnover(self, balance_sheet: Dict, revenue: Dict) -> float:
        """محاسبه گردش دارایی"""
        try:
            total_assets = balance_sheet['total_assets']['total']
            total_revenue = revenue['total_revenue']['total']
            
            return total_revenue / total_assets if total_assets > 0 else 0
        except:
            return 0
    
    def _assess_risks(self, balance_sheet: Dict, cash_bank: Dict, 
                     revenue: Dict, expense: Dict) -> Dict[str, Any]:
        """ارزیابی ریسک‌های مالی"""
        
        risks = {
            'liquidity_risk': self._assess_liquidity_risk(cash_bank, balance_sheet),
            'solvency_risk': self._assess_solvency_risk(balance_sheet),
            'profitability_risk': self._assess_profitability_risk(revenue, expense),
            'operational_risk': self._assess_operational_risk(revenue, expense),
            'market_risk': self._assess_market_risk(revenue)
        }
        
        return {
            'risk_levels': risks,
            'overall_risk': self._determine_overall_risk(risks),
            'critical_risks': self._identify_critical_risks(risks)
        }
    
    def _assess_liquidity_risk(self, cash_bank: Dict, balance_sheet: Dict) -> str:
        """ارزیابی ریسک نقدینگی"""
        try:
            current_ratio = balance_sheet['detailed_analysis']['ratios'].get('current_ratio', 0)
            cash_ratio = cash_bank['liquidity_analysis']['ratios'].get('cash_ratio', 0)
            
            if current_ratio < 1.0 or cash_ratio < 0.1:
                return "بالا"
            elif current_ratio < 1.5 or cash_ratio < 0.2:
                return "متوسط"
            else:
                return "پایین"
        except:
            return "متوسط"
    
    def _assess_solvency_risk(self, balance_sheet: Dict) -> str:
        """ارزیابی ریسک توانایی پرداخت"""
        try:
            debt_ratio = balance_sheet['detailed_analysis']['ratios'].get('debt_ratio', 0)
            
            if debt_ratio > 0.7:
                return "بالا"
            elif debt_ratio > 0.5:
                return "متوسط"
            else:
                return "پایین"
        except:
            return "متوسط"
    
    def _assess_profitability_risk(self, revenue: Dict, expense: Dict) -> str:
        """ارزیابی ریسک سودآوری"""
        try:
            net_income = revenue['total_revenue']['total'] - expense['total_expenses']['total']
            
            if net_income < 0:
                return "بالا"
            elif net_income / revenue['total_revenue']['total'] < 0.05:
                return "متوسط"
            else:
                return "پایین"
        except:
            return "متوسط"
    
    def _assess_operational_risk(self, revenue: Dict, expense: Dict) -> str:
        """ارزیابی ریسک عملیاتی"""
        try:
            expense_ratio = expense['cost_efficiency']['efficiency_ratios'].get('expense_to_revenue_ratio', 100)
            
            if expense_ratio > 90:
                return "بالا"
            elif expense_ratio > 80:
                return "متوسط"
            else:
                return "پایین"
        except:
            return "متوسط"
    
    def _assess_market_risk(self, revenue: Dict) -> str:
        """ارزیابی ریسک بازار"""
        try:
            concentration = revenue['revenue_composition']['concentration_analysis']
            hhi_index = concentration.get('hhi_index', 0)
            
            if hhi_index > 0.25:
                return "بالا"  # تمرکز بالا
            elif hhi_index > 0.15:
                return "متوسط"
            else:
                return "پایین"
        except:
            return "متوسط"
    
    def _determine_overall_risk(self, risks: Dict[str, str]) -> str:
        """تعیین ریسک کلی"""
        high_risks = sum(1 for risk in risks.values() if risk == "بالا")
        medium_risks = sum(1 for risk in risks.values() if risk == "متوسط")
        
        if high_risks >= 2:
            return "بالا"
        elif high_risks >= 1 or medium_risks >= 2:
            return "متوسط"
        else:
            return "پایین"
    
    def _identify_critical_risks(self, risks: Dict[str, str]) -> List[str]:
        """شناسایی ریسک‌های بحرانی"""
        critical = []
        
        for risk_type, level in risks.items():
            if level == "بالا":
                risk_names = {
                    'liquidity_risk': 'ریسک نقدینگی',
                    'solvency_risk': 'ریسک توانایی پرداخت',
                    'profitability_risk': 'ریسک سودآوری',
                    'operational_risk': 'ریسک عملیاتی',
                    'market_risk': 'ریسک بازار'
                }
                critical.append(risk_names.get(risk_type, risk_type))
        
        return critical
    
    def _generate_strategic_recommendations(self, balance_sheet: Dict, cash_bank: Dict,
                                          revenue: Dict, expense: Dict,
                                          overall_assessment: Dict) -> List[Dict[str, Any]]:
        """تولید توصیه‌های استراتژیک"""
        
        recommendations = []
        
        # توصیه‌های مبتنی بر سلامت مالی
        health_level = overall_assessment['health_level']
        if health_level in ["ضعیف", "بحرانی"]:
            recommendations.append({
                'priority': 'بالا',
                'category': 'بازسازی مالی',
                'recommendation': 'برنامه‌ریزی فوری برای بهبود وضعیت مالی',
                'timeline': 'فوری',
                'impact': 'بالا'
            })
        
        # توصیه‌های مبتنی بر نقدینگی
        liquidity_risk = self._assess_liquidity_risk(cash_bank, balance_sheet)
        if liquidity_risk == "بالا":
            recommendations.append({
                'priority': 'بالا',
                'category': 'مدیریت نقدینگی',
                'recommendation': 'افزایش موجودی نقدی و مدیریت بدهی‌های جاری',
                'timeline': 'کوتاه‌مدت',
                'impact': 'بالا'
            })
        
        # توصیه‌های مبتنی بر سودآوری
        profitability_risk = self._assess_profitability_risk(revenue, expense)
        if profitability_risk == "بالا":
            recommendations.append({
                'priority': 'بالا',
                'category': 'بهبود سودآوری',
                'recommendation': 'بررسی راهکارهای افزایش درآمد و کاهش هزینه‌ها',
                'timeline': 'میان‌مدت',
                'impact': 'بالا'
            })
        
        # توصیه‌های مبتنی بر رشد
        growth_score = overall_assessment['scores']['growth']
        if growth_score < 0.4:
            recommendations.append({
                'priority': 'متوسط',
                'category': 'توسعه کسب‌وکار',
                'recommendation': 'بررسی استراتژی‌های رشد و توسعه بازار',
                'timeline': 'بلندمدت',
                'impact': 'متوسط'
            })
        
        # توصیه‌های مبتنی بر کارایی
        efficiency_score = overall_assessment['scores']['efficiency']
        if efficiency_score < 0.4:
            recommendations.append({
                'priority': 'متوسط',
                'category': 'بهبود کارایی',
                'recommendation': 'بهینه‌سازی فرآیندها و کاهش هزینه‌های غیرضروری',
                'timeline': 'میان‌مدت',
                'impact': 'متوسط'
            })
        
        return recommendations
