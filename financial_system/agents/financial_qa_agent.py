# financial_system/agents/financial_qa_agent.py
"""
تسک ۹۱: سیستم پرسش و پاسخ مالی
این عامل هوشمند برای پاسخگویی به سوالات مالی و یکپارچه‌سازی با ابزارهای تحلیل طراحی شده است.
"""

import re
from typing import Dict, List, Any, Optional
from langchain.agents import Tool, AgentExecutor
from langchain.schema import BaseOutputParser
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationBufferWindowMemory

from financial_system.services.balance_sheet_analyzer import BalanceSheetAnalyzer
from financial_system.services.cash_bank_analyzer import CashBankAnalyzer
from financial_system.services.revenue_analyzer import RevenueAnalyzer
from financial_system.services.expense_analyzer import ExpenseAnalyzer
from financial_system.services.report_generator import FinancialReportGenerator
from financial_system.services.intelligent_recommendations import IntelligentRecommendationEngine
from financial_system.services.liquidity_ratios import LiquidityRatioAnalyzer, LiquidityRatioTool
from financial_system.services.leverage_ratios import LeverageRatioAnalyzer, LeverageRatioTool
from financial_system.services.profitability_ratios import ProfitabilityRatioAnalyzer, ProfitabilityRatioTool

from users.models import Company, FinancialPeriod, FinancialFile, Document


class FinancialQAAgent:
    """عامل هوشمند پرسش و پاسخ مالی"""
    
    def __init__(self, llm):
        self.llm = llm
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.tools = self._setup_tools()
        self.agent_executor = self._setup_agent()
    
    def _setup_tools(self) -> List[Tool]:
        """تنظیم ابزارهای تحلیل مالی"""
        
        tools = [
            Tool(
                name="balance_sheet_analysis",
                func=self._analyze_balance_sheet,
                description="تحلیل ترازنامه و کنترل توازن"
            ),
            Tool(
                name="cash_bank_analysis",
                func=self._analyze_cash_bank,
                description="تحلیل حساب‌های نقدی و بانکی"
            ),
            Tool(
                name="revenue_analysis",
                func=self._analyze_revenue,
                description="تحلیل درآمدها و روند فروش"
            ),
            Tool(
                name="expense_analysis",
                func=self._analyze_expense,
                description="تحلیل هزینه‌ها و کارایی"
            ),
            Tool(
                name="financial_report",
                func=self._generate_financial_report,
                description="تولید گزارش جامع مالی"
            ),
            Tool(
                name="intelligent_recommendations",
                func=self._get_intelligent_recommendations,
                description="دریافت توصیه‌های هوشمند مالی"
            ),
            Tool(
                name="liquidity_ratios",
                func=self._analyze_liquidity_ratios,
                description="محاسبه و تحلیل نسبت‌های نقدینگی"
            ),
            Tool(
                name="leverage_ratios",
                func=self._analyze_leverage_ratios,
                description="محاسبه و تحلیل نسبت‌های اهرمی"
            ),
            Tool(
                name="profitability_ratios",
                func=self._analyze_profitability_ratios,
                description="محاسبه و تحلیل نسبت‌های سودآوری"
            )
        ]
        
        return tools
    
    def _setup_agent(self) -> AgentExecutor:
        """تنظیم عامل اجرایی"""
        
        # قالب پرسش برای عامل
        prompt_template = PromptTemplate(
            input_variables=["input", "chat_history", "agent_scratchpad"],
            template="""
شما یک دستیار هوشمند مالی هستید. با استفاده از ابزارهای موجود به سوالات مالی کاربران پاسخ دهید.

دستورالعمل‌ها:
1. ابتدا نوع سوال را تشخیص دهید
2. از ابزار مناسب استفاده کنید
3. نتایج را به زبان ساده و قابل فهم ارائه دهید
4. در صورت نیاز، تحلیل و توصیه ارائه دهید
5. از داده‌های تاریخی و روندها استفاده کنید

ابزارهای موجود:
{tools}

تاریخچه گفتگو:
{chat_history}

ورودی کاربر: {input}

شروع کنید:
{agent_scratchpad}
"""
        )
        
        # ایجاد زنجیره عامل
        agent_chain = LLMChain(
            llm=self.llm,
            prompt=prompt_template,
            memory=self.memory
        )
        
        return AgentExecutor.from_agent_and_tools(
            agent=agent_chain,
            tools=self.tools,
            verbose=True,
            memory=self.memory
        )
    
    def _extract_entities(self, question: str) -> Dict[str, Any]:
        """استخراج موجودیت‌ها از سوال"""
        
        entities = {
            'company': None,
            'period': None,
            'account_type': None,
            'ratio_type': None,
            'analysis_type': None
        }
        
        # شناسایی شرکت
        company_patterns = [
            r'شرکت\s+(\w+)',
            r'(\w+)\s+شرکت',
            r'برای\s+(\w+)'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                entities['company'] = match.group(1)
                break
        
        # شناسایی دوره
        period_patterns = [
            r'فصل\s+(\w+)',
            r'ماه\s+(\w+)',
            r'سال\s+(\d+)',
            r'دوره\s+(\w+)'
        ]
        
        for pattern in period_patterns:
            match = re.search(pattern, question, re.IGNORECASE)
            if match:
                entities['period'] = match.group(1)
                break
        
        # شناسایی نوع حساب
        account_keywords = {
            'balance_sheet': ['ترازنامه', 'دارایی', 'بدهی', 'سرمایه'],
            'cash_bank': ['صندوق', 'بانک', 'نقد', 'وجه نقد'],
            'revenue': ['درآمد', 'فروش', 'دریافتی'],
            'expense': ['هزینه', 'خرج', 'پرداختی']
        }
        
        for account_type, keywords in account_keywords.items():
            if any(keyword in question for keyword in keywords):
                entities['account_type'] = account_type
                break
        
        # شناسایی نوع نسبت
        ratio_keywords = {
            'liquidity': ['نقدینگی', 'جاری', 'سریع', 'نقدی'],
            'leverage': ['اهرم', 'بدهی', 'سرمایه', 'بهره'],
            'profitability': ['سودآوری', 'سود', 'بازده', 'حاشیه']
        }
        
        for ratio_type, keywords in ratio_keywords.items():
            if any(keyword in question for keyword in keywords):
                entities['ratio_type'] = ratio_type
                break
        
        # شناسایی نوع تحلیل
        analysis_keywords = {
            'report': ['گزارش', 'تحلیل', 'بررسی'],
            'recommendation': ['توصیه', 'پیشنهاد', 'راهنمایی'],
            'trend': ['روند', 'تغییر', 'مقایسه']
        }
        
        for analysis_type, keywords in analysis_keywords.items():
            if any(keyword in question for keyword in keywords):
                entities['analysis_type'] = analysis_type
                break
        
        return entities
    
    def _classify_question(self, question: str) -> str:
        """طبقه‌بندی سوال مالی"""
        
        question_lower = question.lower()
        
        # سوالات مربوط به ترازنامه
        if any(word in question_lower for word in ['ترازنامه', 'دارایی', 'بدهی', 'سرمایه']):
            return 'balance_sheet'
        
        # سوالات مربوط به نقدینگی
        elif any(word in question_lower for word in ['صندوق', 'بانک', 'نقد', 'وجه نقد']):
            return 'cash_bank'
        
        # سوالات مربوط به درآمد
        elif any(word in question_lower for word in ['درآمد', 'فروش', 'دریافتی']):
            return 'revenue'
        
        # سوالات مربوط به هزینه
        elif any(word in question_lower for word in ['هزینه', 'خرج', 'پرداختی']):
            return 'expense'
        
        # سوالات مربوط به نسبت‌های نقدینگی
        elif any(word in question_lower for word in ['نقدینگی', 'جاری', 'سریع', 'نقدی']):
            return 'liquidity_ratios'
        
        # سوالات مربوط به نسبت‌های اهرمی
        elif any(word in question_lower for word in ['اهرم', 'بدهی', 'سرمایه', 'بهره']):
            return 'leverage_ratios'
        
        # سوالات مربوط به نسبت‌های سودآوری
        elif any(word in question_lower for word in ['سودآوری', 'سود', 'بازده', 'حاشیه']):
            return 'profitability_ratios'
        
        # سوالات مربوط به گزارش
        elif any(word in question_lower for word in ['گزارش', 'تحلیل', 'بررسی']):
            return 'financial_report'
        
        # سوالات مربوط به توصیه
        elif any(word in question_lower for word in ['توصیه', 'پیشنهاد', 'راهنمایی']):
            return 'intelligent_recommendations'
        
        else:
            return 'general_financial'
    
    def _analyze_balance_sheet(self, company_id: int, period_id: int) -> Dict[str, Any]:
        """تحلیل ترازنامه"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            analyzer = BalanceSheetAnalyzer(company, period)
            result = analyzer.analyze_balance_sheet()
            
            return {
                'success': True,
                'analysis': result,
                'display_format': self._format_balance_sheet_for_display(result)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_balance_sheet_for_display(self, analysis: Dict) -> str:
        """قالب‌بندی نتایج ترازنامه برای نمایش"""
        
        if not analysis.get('success', False):
            return "❌ خطا در تحلیل ترازنامه"
        
        data = analysis['analysis']
        
        display_text = f"""
📊 **تحلیل ترازنامه - {data['company']} - {data['period']}**

💰 **خلاصه مالی:**
- کل دارایی‌ها: {data['summary']['total_assets']:,.0f} ریال
- کل بدهی‌ها: {data['summary']['total_liabilities']:,.0f} ریال  
- حقوق صاحبان سهام: {data['summary']['total_equity']:,.0f} ریال

✅ **وضعیت توازن:**
{data['balance_status']['message']}

📈 **نسبت‌های کلیدی:**
- نسبت بدهی: {data['ratios']['debt_ratio']:.2%}
- نسبت سرمایه: {data['ratios']['equity_ratio']:.2%}

⚠️ **هشدارها:**
"""
        
        for warning in data['warnings']:
            display_text += f"- {warning}\n"
        
        return display_text
    
    def _analyze_cash_bank(self, company_id: int, period_id: int) -> Dict[str, Any]:
        """تحلیل حساب‌های نقدی"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            analyzer = CashBankAnalyzer(company, period)
            result = analyzer.analyze_cash_bank()
            
            return {
                'success': True,
                'analysis': result,
                'display_format': self._format_cash_bank_for_display(result)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_cash_bank_for_display(self, analysis: Dict) -> str:
        """قالب‌بندی نتایج حساب‌های نقدی برای نمایش"""
        
        if not analysis.get('success', False):
            return "❌ خطا در تحلیل حساب‌های نقدی"
        
        data = analysis['analysis']
        
        display_text = f"""
💵 **تحلیل حساب‌های نقدی - {data['company']} - {data['period']}**

💰 **موجودی‌ها:**
- صندوق: {data['cash_analysis']['cash_balance']:,.0f} ریال
- بانک: {data['cash_analysis']['bank_balance']:,.0f} ریال
- کل نقدینگی: {data['cash_analysis']['total_cash']:,.0f} ریال

📊 **نسبت‌های نقدینگی:**
- نسبت نقدی: {data['liquidity_ratios']['cash_ratio']:.2%}
- سرمایه در گردش: {data['liquidity_ratios']['working_capital']:,.0f} ریال

⚠️ **تراکنش‌های مشکوک:**
"""
        
        for transaction in data['suspicious_transactions']:
            display_text += f"- {transaction}\n"
        
        return display_text
    
    def _analyze_revenue(self, company_id: int, period_id: int) -> Dict[str, Any]:
        """تحلیل درآمدها"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            analyzer = RevenueAnalyzer(company, period)
            result = analyzer.analyze_revenue()
            
            return {
                'success': True,
                'analysis': result,
                'display_format': self._format_revenue_for_display(result)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_revenue_for_display(self, analysis: Dict) -> str:
        """قالب‌بندی نتایج درآمد برای نمایش"""
        
        if not analysis.get('success', False):
            return "❌ خطا در تحلیل درآمدها"
        
        data = analysis['analysis']
        
        display_text = f"""
💰 **تحلیل درآمدها - {data['company']} - {data['period']}**

📈 **خلاصه درآمد:**
- کل درآمد: {data['revenue_summary']['total_revenue']:,.0f} ریال
- رشد نسبت به دوره قبل: {data['revenue_summary']['growth_rate']:.2%}

🏷️ **توزیع درآمد:**
"""
        
        for category, amount in data['revenue_by_category'].items():
            percentage = (amount / data['revenue_summary']['total_revenue']) * 100
            display_text += f"- {category}: {amount:,.0f} ریال ({percentage:.1f}%)\n"
        
        display_text += f"\n📊 **تمرکز درآمد (HHI):** {data['concentration_analysis']['hhi_index']:.0f}"
        
        return display_text
    
    def _analyze_expense(self, company_id: int, period_id: int) -> Dict[str, Any]:
        """تحلیل هزینه‌ها"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            analyzer = ExpenseAnalyzer(company, period)
            result = analyzer.analyze_expense()
            
            return {
                'success': True,
                'analysis': result,
                'display_format': self._format_expense_for_display(result)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_expense_for_display(self, analysis: Dict) -> str:
        """قالب‌بندی نتایج هزینه برای نمایش"""
        
        if not analysis.get('success', False):
            return "❌ خطا در تحلیل هزینه‌ها"
        
        data = analysis['analysis']
        
        display_text = f"""
💸 **تحلیل هزینه‌ها - {data['company']} - {data['period']}**

📉 **خلاصه هزینه:**
- کل هزینه: {data['expense_summary']['total_expense']:,.0f} ریال
- نسبت هزینه به درآمد: {data['expense_summary']['expense_to_revenue_ratio']:.2%}

🏷️ **توزیع هزینه:**
"""
        
        for category, amount in data['expense_by_category'].items():
            percentage = (amount / data['expense_summary']['total_expense']) * 100
            display_text += f"- {category}: {amount:,.0f} ریال ({percentage:.1f}%)\n"
        
        display_text += f"\n📊 **کارایی هزینه:** {data['efficiency_analysis']['efficiency_score']}/5"
        
        return display_text
    
    def _generate_financial_report(self, company_id: int, period_id: int) -> Dict[str, Any]:
        """تولید گزارش مالی"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            generator = FinancialReportGenerator(company, period)
            result = generator.generate_comprehensive_report()
            
            return {
                'success': True,
                'analysis': result,
                'display_format': self._format_financial_report_for_display(result)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_financial_report_for_display(self, analysis: Dict) -> str:
        """قالب‌بندی نتایج گزارش مالی برای نمایش"""
        
        if not analysis.get('success', False):
            return "❌ خطا در تولید گزارش مالی"
        
        data = analysis['analysis']
        
        display_text = f"""
📋 **گزارش جامع مالی - {data['company']} - {data['period']}**

🏆 **امتیاز سلامت مالی:** {data['overall_assessment']['score']}/5 ({data['overall_assessment']['level']})
📝 **خلاصه مدیریتی:** {data['executive_summary']}

📊 **شاخص‌های کلیدی:**
"""
        
        for kpi in data['key_metrics']:
            display_text += f"- {kpi['name']}: {kpi['value']} ({kpi['trend']})\n"
        
        display_text += f"\n⚠️ **سطح ریسک:** {data['risk_assessment']['overall_risk_level']}"
        
        return display_text
    
    def _get_intelligent_recommendations(self, company_id: int, period_id: int, user_role: str = "accountant") -> Dict[str, Any]:
        """دریافت توصیه‌های هوشمند"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            engine = IntelligentRecommendationEngine(company, period)
            result = engine.generate_recommendations(user_role)
            
            return {
                'success': True,
                'analysis': result,
                'display_format': self._format_recommendations_for_display(result)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_recommendations_for_display(self, analysis: Dict) -> str:
        """قالب‌بندی نتایج توصیه‌ها برای نمایش"""
        
        if not analysis.get('success', False):
            return "❌ خطا در دریافت توصیه‌ها"
        
        data = analysis['analysis']
        
        display_text = f"""
💡 **توصیه‌های هوشمند مالی - {data['company']} - {data['period']}**

🎯 **نقش کاربر:** {data['user_role']}
📅 **نقشه راه اجرایی:** {data['implementation_roadmap']['timeline']}

🚀 **توصیه‌های با اولویت بالا:**
"""
        
        for recommendation in data['recommendations'][:3]:  # نمایش ۳ توصیه اول
            display_text += f"""
📌 **{recommendation['priority']} - {recommendation['category']}**
{recommendation['recommendation']}
📋 اقدام: {recommendation['action']}
🎯 تاثیر مورد انتظار: {recommendation['expected_impact']}
"""
        
        return display_text
    
    def _analyze_liquidity_ratios(self, company_id: int, period_id: int) -> Dict[str, Any]:
        """تحلیل نسبت‌های نقدینگی"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            analyzer = LiquidityRatioAnalyzer(company, period)
            result = analyzer.calculate_all_liquidity_ratios()
            
            return {
                'success': True,
                'analysis': result,
                'display_format': self._format_liquidity_ratios_for_display(result)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_liquidity_ratios_for_display(self, analysis: Dict) -> str:
        """قالب‌بندی نتایج نسبت‌های نقدینگی برای نمایش"""
        
        if not analysis.get('success', False):
            return "❌ خطا در تحلیل نسبت‌های نقدینگی"
        
        data = analysis['analysis']
        
        display_text = f"""
💧 **تحلیل نسبت‌های نقدینگی - {data['company']} - {data['period']}**

📊 **نسبت‌های کلیدی:**
"""
        
        for ratio_name, ratio_data in data['liquidity_ratios'].items():
            display_text += f"- {ratio_data['formula']}: {ratio_data['ratio']:.2f} ({ratio_data['assessment']})\n"
        
        display_text += f"\n📈 **تحلیل کلی:** {data['analysis']['overall_assessment']['interpretation']}"
        display_text += f"\n⚠️ **سطح ریسک نقدینگی:** {data['analysis']['risk_level']}"
        
        return display_text
    
    def _analyze_leverage_ratios(self, company_id: int, period_id: int) -> Dict[str, Any]:
        """تحلیل نسبت‌های اهرمی"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            analyzer = LeverageRatioAnalyzer(company, period)
            result = analyzer.calculate_all_leverage_ratios()
            
            return {
                'success': True,
                'analysis': result,
                'display_format': self._format_leverage_ratios_for_display(result)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_leverage_ratios_for_display(self, analysis: Dict) -> str:
        """قالب‌بندی نتایج نسبت‌های اهرمی برای نمایش"""
        
        if not analysis.get('success', False):
            return "❌ خطا در تحلیل نسبت‌های اهرمی"
        
        data = analysis['analysis']
        
        display_text = f"""
⚖️ **تحلیل نسبت‌های اهرمی - {data['company']} - {data['period']}**

📊 **نسبت‌های کلیدی:**
"""
        
        for ratio_name, ratio_data in data['leverage_ratios'].items():
            display_text += f"- {ratio_data['formula']}: {ratio_data['ratio']:.2f} ({ratio_data['assessment']})\n"
        
        display_text += f"\n📈 **تحلیل کلی:** {data['analysis']['overall_assessment']['interpretation']}"
        display_text += f"\n⚠️ **سطح ریسک اهرمی:** {data['analysis']['risk_level']}"
        
        return display_text
    
    def _analyze_profitability_ratios(self, company_id: int, period_id: int) -> Dict[str, Any]:
        """تحلیل نسبت‌های سودآوری"""
        try:
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            analyzer = ProfitabilityRatioAnalyzer(company, period)
            result = analyzer.calculate_all_profitability_ratios()
            
            return {
                'success': True,
                'analysis': result,
                'display_format': self._format_profitability_ratios_for_display(result)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_profitability_ratios_for_display(self, analysis: Dict) -> str:
        """قالب‌بندی نتایج نسبت‌های سودآوری برای نمایش"""
        
        if not analysis.get('success', False):
            return "❌ خطا در تحلیل نسبت‌های سودآوری"
        
        data = analysis['analysis']
        
        display_text = f"""
💰 **تحلیل نسبت‌های سودآوری - {data['company']} - {data['period']}**

📊 **نسبت‌های کلیدی:**
"""
        
        for ratio_name, ratio_data in data['profitability_ratios'].items():
            if 'percentage' in ratio_data:
                display_text += f"- {ratio_data['formula']}: {ratio_data['percentage']:.1f}% ({ratio_data['assessment']})\n"
            else:
                display_text += f"- {ratio_data['formula']}: {ratio_data['ratio']:.2f} ({ratio_data['assessment']})\n"
        
        display_text += f"\n📈 **تحلیل کلی:** {data['analysis']['overall_assessment']['interpretation']}"
        display_text += f"\n⚠️ **سطح ریسک سودآوری:** {data['analysis']['risk_level']}"
        
        return display_text
    
    def answer_question(self, question: str, company_id: int = 1, period_id: int = 1, user_role: str = "accountant") -> Dict[str, Any]:
        """پاسخ به سوال مالی"""
        
        try:
            # استخراج موجودیت‌ها از سوال
            entities = self._extract_entities(question)
            
            # طبقه‌بندی سوال
            question_type = self._classify_question(question)
            
            # انتخاب ابزار مناسب
            tool_result = None
            
            if question_type == 'balance_sheet':
                tool_result = self._analyze_balance_sheet(company_id, period_id)
            elif question_type == 'cash_bank':
                tool_result = self._analyze_cash_bank(company_id, period_id)
            elif question_type == 'revenue':
                tool_result = self._analyze_revenue(company_id, period_id)
            elif question_type == 'expense':
                tool_result = self._analyze_expense(company_id, period_id)
            elif question_type == 'liquidity_ratios':
                tool_result = self._analyze_liquidity_ratios(company_id, period_id)
            elif question_type == 'leverage_ratios':
                tool_result = self._analyze_leverage_ratios(company_id, period_id)
            elif question_type == 'profitability_ratios':
                tool_result = self._analyze_profitability_ratios(company_id, period_id)
            elif question_type == 'financial_report':
                tool_result = self._generate_financial_report(company_id, period_id)
            elif question_type == 'intelligent_recommendations':
                tool_result = self._get_intelligent_recommendations(company_id, period_id, user_role)
            else:
                # استفاده از عامل هوشمند برای سوالات عمومی
                response = self.agent_executor.run(question)
                return {
                    'success': True,
                    'question_type': 'general_financial',
                    'response': response,
                    'display_format': response
                }
            
            if tool_result and tool_result.get('success', False):
                return {
                    'success': True,
                    'question_type': question_type,
                    'entities': entities,
                    'analysis': tool_result['analysis'],
                    'display_format': tool_result['display_format']
                }
            else:
                return {
                    'success': False,
                    'error': tool_result.get('error', 'خطا در تحلیل مالی'),
                    'display_format': tool_result.get('display_format', '❌ خطا در پردازش سوال')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'display_format': f"❌ خطا در پردازش سوال: {str(e)}"
            }


# ابزار LangChain برای یکپارچه‌سازی با چت بات
class FinancialQATool:
    """ابزار پرسش و پاسخ مالی برای LangChain"""
    
    name = "financial_qa"
    description = "پاسخ به سوالات مالی و تحلیل‌های تخصصی"
    
    def __init__(self, llm):
        self.agent = FinancialQAAgent(llm)
    
    def answer_financial_question(self, question: str, company_id: int = 1, period_id: int = 1, user_role: str = "accountant") -> Dict:
        """پاسخ به سوال مالی"""
        return self.agent.answer_question(question, company_id, period_id, user_role)
