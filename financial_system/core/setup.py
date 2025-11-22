# financial_system/core/setup.py
import logging
import os

logger = logging.getLogger(__name__)

def setup_advanced_financial_agent():
    """راه‌اندازی عامل مالی پیشرفته با استفاده از FinancialQAAgent و DeepSeek API"""
    try:
        # بررسی وجود LangChain
        try:
            from langchain.llms import OpenAI
            from langchain.chat_models import ChatOpenAI
            
            # تنظیم DeepSeek API Key
            deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
            if not deepseek_api_key:
                logger.warning("⚠️ DEEPSEEK_API_KEY تنظیم نشده است")
                # استفاده از عامل ساده به عنوان fallback
                return setup_simple_financial_agent()
            
            # استفاده از DeepSeek API
            # تنظیم base_url برای DeepSeek
            llm = ChatOpenAI(
                model_name="deepseek-chat",
                temperature=0.1,
                max_tokens=2000,
                openai_api_key=deepseek_api_key,
                openai_api_base="https://api.deepseek.com/v1"
            )
            
            # ایجاد عامل پیشرفته
            from ..agents.financial_qa_agent import FinancialQAAgent
            agent = FinancialQAAgent(llm)
            
            logger.info("✅ FinancialQAAgent پیشرفته با DeepSeek API با موفقیت ایجاد شد")
            return agent
            
        except ImportError as e:
            logger.warning(f"⚠️ LangChain در دسترس نیست: {e}")
            # استفاده از عامل ساده به عنوان fallback
            return setup_simple_financial_agent()
            
    except Exception as e:
        logger.error(f"⚠️ خطا در ایجاد FinancialQAAgent پیشرفته با DeepSeek: {e}")
        # استفاده از عامل ساده به عنوان fallback
        return setup_simple_financial_agent()

def setup_simple_financial_agent():
    """راه‌اندازی عامل مالی ساده"""
    try:
        agent = SimpleFinancialAgent()
        logger.info("✅ SimpleFinancialAgent با موفقیت ایجاد شد")
        return agent
    except Exception as e:
        logger.error(f"⚠️ خطا در ایجاد SimpleFinancialAgent: {e}")
        return SimpleFinancialAgent()

# کلاس ساده FinancialAgent که به LangChain وابسته نیست (برای fallback)
class SimpleFinancialAgent:
    def __init__(self):
        self.tools = {}
        self._setup_tools()
    
    def _setup_tools(self):
        """راه‌اندازی ابزارهای مالی ساده"""
        try:
            # import مستقیم توابع بدون استفاده از دکوراتورها
            from ..tools.financial_analysis_tools import (
                analyze_financial_ratios_tool,
                detect_financial_anomalies_tool,
                generate_financial_report_tool,
                generate_four_column_balance_sheet_tool,
                analyze_seasonal_performance_tool,
                generate_comprehensive_financial_report_tool
            )
            
            # import ابزارهای مقایسه‌ای جدید
            from ..tools.comparison_tools import (
                compare_financial_ratios_tool,
                analyze_trend_tool
            )
            
            self.tools = {
                "analyze_ratios": analyze_financial_ratios_tool,
                "detect_anomalies": detect_financial_anomalies_tool,
                "generate_report": generate_financial_report_tool,
                "four_column_balance": generate_four_column_balance_sheet_tool,
                "seasonal_analysis": analyze_seasonal_performance_tool,
                "comprehensive_report": generate_comprehensive_financial_report_tool,
                "compare_ratios": compare_financial_ratios_tool,
                "analyze_trend": analyze_trend_tool
            }
            
            logger.info(f"✅ {len(self.tools)} ابزار مالی بارگذاری شد")
            
        except ImportError as e:
            logger.warning(f"⚠️ خطا در بارگذاری ابزارهای مالی: {e}")
            self.tools = {}
    
    def _select_tool(self, question: str) -> str:
        """انتخاب ابزار مناسب بر اساس کلمات کلیدی در سوال"""
        question_lower = question.lower()
        
        # اولویت ۱: تشخیص سوالات مقایسه‌ای (بالاترین اولویت)
        comparison_keywords = ["مقایسه", "مقایسه کن", "مقایسه کنید", "مقایسه شود"]
        if any(kw in question_lower for kw in comparison_keywords):
            return "compare_ratios"
        
        # اولویت ۲: تشخیص سوالات تحلیل روند
        trend_keywords = ["روند", "تحلیل روند", "تغییرات", "نوسان", "رشد", "کاهش", "افزایش"]
        if any(kw in question_lower for kw in trend_keywords):
            return "analyze_trend"
        
        # اولویت ۳: تشخیص ماه‌ها برای مقایسه
        month_keywords = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        if any(kw in question_lower for kw in month_keywords):
            return "compare_ratios"
        
        # اولویت ۴: مپینگ کلمات کلیدی عادی
        keyword_mapping = {
            # تحلیل نسبت‌ها
            "نسبت جاری": "analyze_ratios",
            "نسبت آنی": "analyze_ratios",
            "نسبت نقدینگی": "analyze_ratios",
            "نسبت سودآوری": "analyze_ratios",
            "نسبت اهرمی": "analyze_ratios",
            "نسبت": "analyze_ratios",
            "تحلیل نسبت": "analyze_ratios",
            
            # شناسایی انحرافات
            "انحراف": "detect_anomalies",
            "مشکوک": "detect_anomalies",
            "مغایرت": "detect_anomalies",
            "کنترل": "detect_anomalies",
            "ریسک": "detect_anomalies",
            
            # گزارش‌های مالی
            "ترازنامه": "generate_report",
            "صورت سود و زیان": "generate_report",
            "صورت جریان نقدی": "generate_report",
            "صورت مالی": "generate_report",
            "گزارش مالی": "generate_report",
            
            # تراز چهارستونی
            "چهارستونی": "four_column_balance",
            "چهار ستون": "four_column_balance",
            "تراز کل": "four_column_balance",
            
            # تحلیل فصلی
            "فصلی": "seasonal_analysis",
            "فصل": "seasonal_analysis",
            "بهار": "seasonal_analysis",
            "تابستان": "seasonal_analysis",
            "پاییز": "seasonal_analysis",
            "زمستان": "seasonal_analysis",
            "عملکرد فصلی": "seasonal_analysis",
            
            # گزارش جامع
            "گزارش جامع": "comprehensive_report",
            "تحلیل کامل": "comprehensive_report",
            "گزارش کامل": "comprehensive_report",
            "تحلیل جامع": "comprehensive_report",
            
            # سوالات خاص
            "صندوق": "generate_report",
            "بانک": "generate_report",
            "حساب": "generate_report",
            "مانده": "generate_report",
            "گردش مالی": "generate_report",
            "درآمد": "generate_report",
            "سود": "generate_report",
            "زیان": "generate_report",
            "دارایی": "generate_report",
            "بدهی": "generate_report",
        }
        
        # اولویت‌بندی: ابتدا عبارات طولانی‌تر را بررسی کن
        sorted_keywords = sorted(keyword_mapping.keys(), key=len, reverse=True)
        
        for keyword in sorted_keywords:
            if keyword in question_lower:
                return keyword_mapping[keyword]
        
        # اگر ابزار خاصی پیدا نشد، از تحلیل جامع استفاده کن
        return "comprehensive_report"
    
    def ask_financial_question(self, question: str, company_id: int = 1, period_id: int = 1) -> str:
        """پرسش سوال مالی و انتخاب ابزار مناسب"""
        try:
            # انتخاب ابزار مناسب
            selected_tool = self._select_tool(question)
            tool_function = self.tools.get(selected_tool)
            
            if not tool_function:
                return "متأسفانه ابزار مناسب برای پاسخ به این سوال یافت نشد."
            
            # اجرای ابزار با پارامترهای مناسب
            if selected_tool == "four_column_balance":
                season = "spring"  # پیش‌فرض
                if "تابستان" in question.lower():
                    season = "summer"
                elif "پاییز" in question.lower():
                    season = "autumn"
                elif "زمستان" in question.lower():
                    season = "winter"
                response = tool_function(company_id, period_id, season)
            elif selected_tool == "seasonal_analysis":
                season = "spring"  # پیش‌فرض
                if "تابستان" in question.lower():
                    season = "summer"
                elif "پاییز" in question.lower():
                    season = "autumn"
                elif "زمستان" in question.lower():
                    season = "winter"
                response = tool_function(company_id, period_id, season)
            elif selected_tool == "generate_report":
                report_type = "balance_sheet"  # پیش‌فرض
                if "سود و زیان" in question.lower() or "سودوزیان" in question.lower():
                    report_type = "income_statement"
                elif "جریان نقد" in question.lower() or "نقدی" in question.lower():
                    report_type = "cash_flow"
                response = tool_function(company_id, period_id, report_type)
            elif selected_tool == "compare_ratios":
                # استخراج نوع نسبت از سوال
                ratio_type = "نسبت آنی"  # پیش‌فرض
                if "نسبت جاری" in question.lower():
                    ratio_type = "نسبت جاری"
                elif "نسبت آنی" in question.lower():
                    ratio_type = "نسبت آنی"
                elif "بازده دارایی" in question.lower():
                    ratio_type = "بازده دارایی"
                elif "حاشیه سود" in question.lower():
                    ratio_type = "حاشیه سود"
                
                # استفاده از دوره‌های پیش‌فرض برای مقایسه
                response = tool_function(company_id, 1, 2, ratio_type)
            elif selected_tool == "analyze_trend":
                # استخراج متریک از سوال
                metric = "نسبت آنی"  # پیش‌فرض
                if "نسبت جاری" in question.lower():
                    metric = "نسبت جاری"
                elif "درآمد" in question.lower():
                    metric = "درآمد"
                elif "سود خالص" in question.lower():
                    metric = "سود خالص"
                
                # استفاده از دوره‌های پیش‌فرض برای تحلیل روند
                response = tool_function(company_id, metric, [1, 2, 3, 4])
            else:
                response = tool_function(company_id, period_id)
            
            return response
            
        except Exception as e:
            logger.error(f"خطا در پردازش سوال مالی: {e}")
            return f"خطا در پردازش سوال مالی: {str(e)}"

    def answer_question(self, question: str, company_id: int = 1, period_id: int = 1) -> str:
        """متد سازگار با FinancialQAAgent - استفاده از ask_financial_question"""
        return self.ask_financial_question(question, company_id, period_id)

def setup_financial_agent():
    """راه‌اندازی کامل agent مالی (استفاده از نسخه پیشرفته)"""
    try:
        # استفاده از عامل پیشرفته
        return setup_advanced_financial_agent()
    except Exception as e:
        logger.error(f"⚠️ خطا در ایجاد FinancialAgent پیشرفته: {e}")
        # استفاده از عامل ساده به عنوان fallback
        return setup_simple_financial_agent()
