# financial_system/services/intelligent_recommendations.py
"""
تسک ۹۳: پیاده‌سازی ارائه توصیه‌های هوشمند
این سرویس برای تولید توصیه‌های شخصی‌سازی شده مالی طراحی شده است.
"""

from typing import Dict, List, Any
from decimal import Decimal
from financial_ai_core.services.balance_sheet_analyzer import BalanceSheetAnalyzer
from financial_ai_core.services.cash_bank_analyzer import CashBankAnalyzer
from financial_ai_core.services.revenue_analyzer import RevenueAnalyzer
from financial_ai_core.services.expense_analyzer import ExpenseAnalyzer
from financial_ai_core.services.report_generator import FinancialReportGenerator
from users.models import Company, FinancialPeriod


class IntelligentRecommendationEngine:
    """موتور توصیه‌های هوشمند مالی"""
    
    def __init__(self, company: Company, period: FinancialPeriod):
        self.company = company
        self.period = period
        self.analyzers = {
            'balance_sheet': BalanceSheetAnalyzer(company, period),
            'cash_bank': CashBankAnalyzer(company, period),
            'revenue': RevenueAnalyzer(company, period),
            'expense': ExpenseAnalyzer(company, period),
            'report': FinancialReportGenerator(company, period)
        }
    
    def generate_personalized_recommendations(self, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """تولید توصیه‌های شخصی‌سازی شده"""
        
        # جمع‌آوری داده‌های تحلیلی
        analysis_data = self._collect_analysis_data()
        
        # تولید توصیه‌ها بر اساس زمینه کاربر
        recommendations = {
            'immediate_actions': self._generate_immediate_actions(analysis_data),
            'strategic_improvements': self._generate_strategic_improvements(analysis_data),
            'risk_mitigation': self._generate_risk_mitigation_recommendations(analysis_data),
            'growth_opportunities': self._generate_growth_opportunities(analysis_data),
            'efficiency_enhancements': self._generate_efficiency_enhancements(analysis_data)
        }
        
        # اولویت‌بندی و فیلتر کردن بر اساس زمینه کاربر
        personalized_recommendations = self._personalize_recommendations(
            recommendations, user_context
        )
        
        return {
            'company': self.company.name,
            'period': self.period.name,
            'overall_assessment': self._generate_overall_assessment(analysis_data),
            'recommendations': personalized_recommendations,
            'implementation_roadmap': self._create_implementation_roadmap(personalized_recommendations)
        }
    
    def _collect_analysis_data(self) -> Dict[str, Any]:
        """جمع‌آوری داده‌های تحلیلی"""
        
        return {
            'balance_sheet': self.analyzers['balance_sheet'].analyze_balance_sheet(),
            'cash_bank': self.analyzers['cash_bank'].analyze_cash_bank(),
            'revenue': self.analyzers['revenue'].analyze_revenue(),
            'expense': self.analyzers['expense'].analyze_expenses(),
            'comprehensive_report': self.analyzers['report'].generate_comprehensive_report()
        }
    
    def _generate_immediate_actions(self, analysis_data: Dict) -> List[Dict[str, Any]]:
        """تولید اقدامات فوری"""
        
        actions = []
        
        # بررسی ترازنامه
        balance_sheet = analysis_data['balance_sheet']
        if not balance_sheet['is_balanced']:
            actions.append({
                'id': 'IA001',
                'title': 'اصلاح ترازنامه نامتوازن',
                'description': f'ترازنامه با تفاوت {balance_sheet["difference"]:,.0f} ریال نامتوازن است',
                'priority': 'فوری',
                'impact': 'بالا',
                'effort': 'متوسط',
                'timeline': '۱ هفته',
                'steps': [
                    'بررسی آرتیکل‌های مشکوک',
                    'اصلاح خطاهای محاسباتی',
                    'بررسی کدینگ حساب‌ها'
                ]
            })
        
        # بررسی نقدینگی
        cash_bank = analysis_data['cash_bank']
        cash_ratio = cash_bank['liquidity_analysis']['ratios'].get('cash_ratio', 0)
        if cash_ratio < 0.1:
            actions.append({
                'id': 'IA002',
                'title': 'بهبود وضعیت نقدینگی',
                'description': 'نسبت نقدی بسیار پایین است',
                'priority': 'فوری',
                'impact': 'بالا',
                'effort': 'بالا',
                'timeline': '۲ هفته',
                'steps': [
                    'افزایش موجودی نقدی',
                    'برنامه‌ریزی برای دریافت‌های معوق',
                    'مدیریت پرداخت‌های جاری'
                ]
            })
        
        # بررسی درآمد
        revenue = analysis_data['revenue']
        if revenue['total_revenue']['total'] == 0:
            actions.append({
                'id': 'IA003',
                'title': 'ایجاد جریان درآمدی',
                'description': 'هیچ درآمدی در این دوره ثبت نشده است',
                'priority': 'فوری',
                'impact': 'بالا',
                'effort': 'بالا',
                'timeline': '۱ ماه',
                'steps': [
                    'بررسی فرآیندهای فروش',
                    'تحلیل بازار و مشتریان',
                    'تعیین استراتژی درآمدزایی'
                ]
            })
        
        return actions
    
    def _generate_strategic_improvements(self, analysis_data: Dict) -> List[Dict[str, Any]]:
        """تولید بهبودهای استراتژیک"""
        
        improvements = []
        
        # تحلیل ساختار سرمایه
        balance_sheet = analysis_data['balance_sheet']
        debt_ratio = balance_sheet['detailed_analysis']['ratios'].get('debt_ratio', 0)
        
        if debt_ratio > 0.7:
            improvements.append({
                'id': 'SI001',
                'title': 'بهینه‌سازی ساختار سرمایه',
                'description': 'نسبت بدهی بسیار بالا است',
                'category': 'ساختار مالی',
                'benefit': 'کاهش ریسک مالی و هزینه‌های بهره',
                'implementation_complexity': 'بالا',
                'expected_roi': '۱۵-۲۵٪',
                'key_metrics': ['نسبت بدهی', 'هزینه بهره', 'نسبت پوشش بهره']
            })
        
        # تحلیل تمرکز درآمد
        revenue = analysis_data['revenue']
        concentration = revenue['revenue_composition']['concentration_analysis']
        hhi_index = concentration.get('hhi_index', 0)
        
        if hhi_index > 0.25:
            improvements.append({
                'id': 'SI002',
                'title': 'تنوع‌بخشی منابع درآمدی',
                'description': 'تمرکز درآمد بسیار بالا است',
                'category': 'استراتژی کسب‌وکار',
                'benefit': 'کاهش ریسک وابستگی و افزایش پایداری',
                'implementation_complexity': 'متوسط',
                'expected_roi': '۱۰-۲۰٪',
                'key_metrics': ['شاخص HHI', 'تعداد منابع درآمدی', 'سهم بازار']
            })
        
        # تحلیل کارایی هزینه
        expense = analysis_data['expense']
        expense_ratio = expense['cost_efficiency']['efficiency_ratios'].get('expense_to_revenue_ratio', 100)
        
        if expense_ratio > 80:
            improvements.append({
                'id': 'SI003',
                'title': 'بهبود کارایی عملیاتی',
                'description': 'نسبت هزینه به درآمد بسیار بالا است',
                'category': 'بهبود فرآیند',
                'benefit': 'افزایش سودآوری و رقابت‌پذیری',
                'implementation_complexity': 'متوسط',
                'expected_roi': '۲۰-۳۰٪',
                'key_metrics': ['نسبت هزینه به درآمد', 'حاشیه سود', 'بهره‌وری']
            })
        
        return improvements
    
    def _generate_risk_mitigation_recommendations(self, analysis_data: Dict) -> List[Dict[str, Any]]:
        """تولید توصیه‌های کاهش ریسک"""
        
        risk_recommendations = []
        
        report = analysis_data['comprehensive_report']
        risk_assessment = report.get('risk_assessment', {})
        
        # ریسک نقدینگی
        if risk_assessment.get('risk_levels', {}).get('liquidity_risk') == "بالا":
            risk_recommendations.append({
                'id': 'RM001',
                'risk_type': 'نقدینگی',
                'severity': 'بالا',
                'recommendation': 'ایجاد خط اعتباری اضطراری و مدیریت جریان نقدی',
                'mitigation_strategy': 'افزایش موجودی نقدی و برنامه‌ریزی جریان نقدی',
                'monitoring_indicators': ['نسبت جاری', 'نسبت نقدی', 'جریان نقدی عملیاتی'],
                'contingency_plan': 'فروش دارایی‌های غیرضروری و مذاکره با تامین‌کنندگان'
            })
        
        # ریسک توانایی پرداخت
        if risk_assessment.get('risk_levels', {}).get('solvency_risk') == "بالا":
            risk_recommendations.append({
                'id': 'RM002',
                'risk_type': 'توانایی پرداخت',
                'severity': 'بالا',
                'recommendation': 'بازسازی ساختار بدهی و افزایش سرمایه',
                'mitigation_strategy': 'تجدید ساختار بدهی و جذب سرمایه جدید',
                'monitoring_indicators': ['نسبت بدهی', 'نسبت پوشش بهره', 'جریان نقدی آزاد'],
                'contingency_plan': 'مذاکره با طلبکاران و فروش دارایی‌ها'
            })
        
        # ریسک سودآوری
        if risk_assessment.get('risk_levels', {}).get('profitability_risk') == "بالا":
            risk_recommendations.append({
                'id': 'RM003',
                'risk_type': 'سودآوری',
                'severity': 'متوسط',
                'recommendation': 'بازنگری مدل کسب‌وکار و کاهش هزینه‌ها',
                'mitigation_strategy': 'بهبود حاشیه سود و کاهش هزینه‌های ثابت',
                'monitoring_indicators': ['حاشیه سود خالص', 'نسبت هزینه به درآمد', 'رشد درآمد'],
                'contingency_plan': 'کاهش ظرفیت تولید و تمرکز بر محصولات سودآور'
            })
        
        return risk_recommendations
    
    def _generate_growth_opportunities(self, analysis_data: Dict) -> List[Dict[str, Any]]:
        """تولید فرصت‌های رشد"""
        
        opportunities = []
        
        revenue = analysis_data['revenue']
        growth_rate = revenue['monthly_trend'].get('growth_rate', 0)
        
        # فرصت‌های مبتنی بر رشد
        if growth_rate > 15:
            opportunities.append({
                'id': 'GO001',
                'opportunity_type': 'توسعه بازار',
                'potential_impact': 'بالا',
                'description': 'رشد قوی درآمدی نشان‌دهنده پتانسیل توسعه بازار است',
                'implementation_approach': 'توسعه جغرافیایی و ورود به بازارهای جدید',
                'required_investment': 'متوسط',
                'expected_roi': '۲۵-۴۰٪',
                'success_factors': ['تحلیل بازار', 'شبکه توزیع', 'برندینگ']
            })
        
        # فرصت‌های مبتنی بر ترکیب درآمد
        composition = revenue['revenue_composition']['composition']
        if 'خدمات' in composition and composition['خدمات']['percentage'] < 20:
            opportunities.append({
                'id': 'GO002',
                'opportunity_type': 'تنوع خدمات',
                'potential_impact': 'متوسط',
                'description': 'پتانسیل توسعه خدمات ارزش‌افزوده وجود دارد',
                'implementation_approach': 'توسعه خدمات پس از فروش و مشاوره',
                'required_investment': 'پایین',
                'expected_roi': '۱۵-۲۵٪',
                'success_factors': ['تخصص نیروی انسانی', 'رضایت مشتری', 'کیفیت خدمات']
            })
        
        # فرصت‌های مبتنی بر کارایی
        expense = analysis_data['expense']
        efficiency_score = analysis_data['comprehensive_report']['overall_assessment']['scores']['efficiency']
        
        if efficiency_score > 0.7:
            opportunities.append({
                'id': 'GO003',
                'opportunity_type': 'افزایش مقیاس',
                'potential_impact': 'بالا',
                'description': 'کارایی بالا نشان‌دهنده آمادگی برای افزایش مقیاس است',
                'implementation_approach': 'افزایش ظرفیت تولید و توسعه محصولات',
                'required_investment': 'بالا',
                'expected_roi': '۳۰-۵۰٪',
                'success_factors': ['مدیریت عملیاتی', 'زنجیره تامین', 'تکنولوژی']
            })
        
        return opportunities
    
    def _generate_efficiency_enhancements(self, analysis_data: Dict) -> List[Dict[str, Any]]:
        """تولید بهبودهای کارایی"""
        
        enhancements = []
        
        expense = analysis_data['expense']
        expense_breakdown = expense['expenses_by_type']
        
        # بهبود هزینه‌های عملیاتی
        if 'هزینه‌های عملیاتی' in expense_breakdown:
            op_expense = expense_breakdown['هزینه‌های عملیاتی']['total']
            if op_expense > Decimal('500000000'):  # 500 میلیون
                enhancements.append({
                    'id': 'EE001',
                    'title': 'بهینه‌سازی هزینه‌های عملیاتی',
                    'description': 'هزینه‌های عملیاتی قابل توجه است',
                    'area': 'عملیات',
                    'potential_savings': '۱۰-۲۰٪',
                    'implementation_approach': 'بررسی فرآیندها و حذف فعالیت‌های غیرضروری',
                    'key_metrics': ['هزینه عملیاتی', 'بهره‌وری نیروی کار', 'کارایی فرآیند']
                })
        
        # بهبود هزینه‌های اداری
        if 'هزینه‌های اداری' in expense_breakdown:
            admin_expense = expense_breakdown['هزینه‌های اداری']['total']
            if admin_expense > Decimal('100000000'):  # 100 میلیون
                enhancements.append({
                    'id': 'EE002',
                    'title': 'کاهش هزینه‌های اداری',
                    'description': 'هزینه‌های اداری قابل کاهش است',
                    'area': 'اداری',
                    'potential_savings': '۱۵-۲۵٪',
                    'implementation_approach': 'دیجیتالی‌سازی و حذف کاغذبازی',
                    'key_metrics': ['هزینه اداری', 'کارایی پرسنل', 'زمان پردازش']
                })
        
        return enhancements
    
    def _personalize_recommendations(self, recommendations: Dict, user_context: Dict = None) -> Dict[str, Any]:
        """شخصی‌سازی توصیه‌ها بر اساس زمینه کاربر"""
        
        if not user_context:
            return recommendations
        
        personalized = {}
        
        # فیلتر کردن بر اساس نقش کاربر
        user_role = user_context.get('role', 'مدیر مالی')
        if user_role == 'حسابدار':
            personalized['immediate_actions'] = recommendations['immediate_actions']
            personalized['efficiency_enhancements'] = recommendations['efficiency_enhancements']
        elif user_role == 'مدیرعامل':
            personalized['strategic_improvements'] = recommendations['strategic_improvements']
            personalized['growth_opportunities'] = recommendations['growth_opportunities']
        elif user_role == 'مدیر ریسک':
            personalized['risk_mitigation'] = recommendations['risk_mitigation']
        else:
            personalized = recommendations
        
        # فیلتر کردن بر اساس اولویت‌های کاربر
        user_priorities = user_context.get('priorities', [])
        if 'نقدینگی' in user_priorities:
            if 'immediate_actions' not in personalized:
                personalized['immediate_actions'] = []
            personalized['immediate_actions'].extend([
                rec for rec in recommendations.get('immediate_actions', [])
                if 'نقدینگی' in rec.get('title', '')
            ])
        
        return personalized
    
    def _generate_overall_assessment(self, analysis_data: Dict) -> Dict[str, Any]:
        """تولید ارزیابی کلی"""
        
        report = analysis_data['comprehensive_report']
        overall_assessment = report.get('overall_assessment', {})
        
        return {
            'financial_health': overall_assessment.get('health_level', 'متوسط'),
            'overall_score': overall_assessment.get('overall_score', 0.5),
            'trend': overall_assessment.get('trend', 'ثابت'),
            'key_strengths': self._identify_key_strengths(analysis_data),
            'main_concerns': self._identify_main_concerns(analysis_data),
            'improvement_areas': self._identify_improvement_areas(analysis_data)
        }
    
    def _identify_key_strengths(self, analysis_data: Dict) -> List[str]:
        """شناسایی نقاط قوت کلیدی"""
        
        strengths = []
        
        balance_sheet = analysis_data['balance_sheet']
        if balance_sheet['is_balanced']:
            strengths.append('ترازنامه متوازن')
        
        cash_bank = analysis_data['cash_bank']
        cash_ratio = cash_bank['liquidity_analysis']['ratios'].get('cash_ratio', 0)
        if cash_ratio > 0.3:
            strengths.append('نقدینگی مناسب')
        
        revenue = analysis_data['revenue']
        growth_rate = revenue['monthly_trend'].get('growth_rate', 0)
        if growth_rate > 10:
            strengths.append(f'رشد درآمدی قوی ({growth_rate:.1f}%)')
        
        return strengths
    
    def _identify_main_concerns(self, analysis_data: Dict) -> List[str]:
        """شناسایی نگرانی‌های اصلی"""
        
        concerns = []
        
        balance_sheet = analysis_data['balance_sheet']
        if not balance_sheet['is_balanced']:
            concerns.append('ترازنامه نامتوازن')
        
        cash_bank = analysis_data['cash_bank']
        cash_ratio = cash_bank['liquidity_analysis']['ratios'].get('cash_ratio', 0)
        if cash_ratio < 0.1:
            concerns.append('نقدینگی پایین')
        
        expense = analysis_data['expense']
        expense_ratio = expense['cost_efficiency']['efficiency_ratios'].get('expense_to_revenue_ratio', 100)
        if expense_ratio > 80:
            concerns.append('کارایی پایین هزینه‌ها')
        
        return concerns
    
    def _identify_improvement_areas(self, analysis_data: Dict) -> List[str]:
        """شناسایی حوزه‌های بهبود"""
        
        improvements = []
        
        revenue = analysis_data['revenue']
        concentration = revenue['revenue_composition']['concentration_analysis']
        hhi_index = concentration.get('hhi_index', 0)
        if hhi_index > 0.25:
            improvements.append('تنوع‌بخشی درآمدها')
        
        balance_sheet = analysis_data['balance_sheet']
        debt_ratio = balance_sheet['detailed_analysis']['ratios'].get('debt_ratio', 0)
        if debt_ratio > 0.6:
            improvements.append('بهینه‌سازی ساختار بدهی')
        
        return improvements
    
    def _create_implementation_roadmap(self, recommendations: Dict) -> Dict[str, Any]:
        """ایجاد نقشه راه اجرایی"""
        
        roadmap = {
            'short_term': {'timeline': '۱-۳ ماه', 'actions': []},
            'medium_term': {'timeline': '۳-۱۲ ماه', 'actions': []},
            'long_term': {'timeline': '۱-۳ سال', 'actions': []}
        }
        
        # دسته‌بندی اقدامات بر اساس جدول زمانی
        for category, rec_list in recommendations.items():
            for recommendation in rec_list:
                timeline = recommendation.get('timeline', '')
                if 'هفته' in timeline or 'ماه' in timeline and '۱' in timeline:
                    roadmap['short_term']['actions'].append(recommendation)
                elif 'ماه' in timeline:
                    roadmap['medium_term']['actions'].append(recommendation)
                elif 'سال' in timeline:
                    roadmap['long_term']['actions'].append(recommendation)
        
        return roadmap
    
    def get_recommendation_by_id(self, recommendation_id: str, user_context: Dict = None) -> Dict[str, Any]:
        """دریافت توصیه خاص بر اساس شناسه"""
        
        all_recommendations = self.generate_personalized_recommendations(user_context)
        
        # جستجو در تمام دسته‌بندی‌ها
        for category, recommendations in all_recommendations['recommendations'].items():
            for rec in recommendations:
                if rec.get('id') == recommendation_id:
                    return {
                        'recommendation': rec,
                        'category': category,
                        'implementation_details': self._get_implementation_details(rec)
                    }
        
        return {'error': 'توصیه یافت نشد'}
    
    def _get_implementation_details(self, recommendation: Dict) -> Dict[str, Any]:
        """دریافت جزئیات اجرایی برای یک توصیه"""
        
        implementation_map = {
            'IA001': {
                'resources_needed': ['حسابدار ارشد', 'نرم‌افزار حسابداری'],
                'estimated_cost': 'کم',
                'success_criteria': ['ترازنامه متوازن', 'تفاوت صفر'],
                'risks': ['خطای محاسباتی', 'داده‌های ناقص']
            },
            'IA002': {
                'resources_needed': ['مدیر مالی', 'بانک'],
                'estimated_cost': 'متوسط',
                'success_criteria': ['نسبت نقدی > 0.2', 'جریان نقدی مثبت'],
                'risks': ['عدم همکاری بانک', 'کاهش فروش']
            },
            'SI001': {
                'resources_needed': ['مشاور مالی', 'وکیل'],
                'estimated_cost': 'بالا',
                'success_criteria': ['نسبت بدهی < 0.6', 'کاهش هزینه بهره'],
                'risks': ['عدم پذیرش سرمایه‌گذاران', 'شرایط بازار']
            }
        }
        
        return implementation_map.get(recommendation.get('id'), {
            'resources_needed': ['تیم اجرایی'],
            'estimated_cost': 'متوسط',
            'success_criteria': ['بهبود شاخص‌های کلیدی'],
            'risks': ['عدم اجرای صحیح']
        })


# ابزار LangChain برای توصیه‌های هوشمند
class IntelligentRecommendationTool:
    """ابزار توصیه‌های هوشمند برای LangChain"""
    
    name = "intelligent_recommendations"
    description = "تولید توصیه‌های شخصی‌سازی شده مالی و استراتژیک"
    
    def __init__(self):
        self.engine_class = IntelligentRecommendationEngine
    
    def get_recommendations(self, company_id: int, period_id: int, user_context: Dict = None) -> Dict:
        """دریافت توصیه‌های هوشمند برای شرکت و دوره مشخص"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            engine = IntelligentRecommendationEngine(company, period)
            result = engine.generate_personalized_recommendations(user_context)
            
            return {
                'success': True,
                'recommendations': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
