# financial_system/agents/financial_agent.py
import os
import logging
import json
from typing import Dict, List, Any
from ..tools.financial_analysis_tools import (
    analyze_financial_ratios_tool,
    detect_financial_anomalies_tool,
    generate_financial_report_tool,
    generate_four_column_balance_sheet_tool,
    analyze_seasonal_performance_tool,
    generate_comprehensive_financial_report_tool
)
from ..tools.financial_classifier import (
    classify_financial_question,
    get_financial_fallback_response
)
from ..tools.ai_classifier import (
    classify_financial_question_ai,
    get_tool_recommendations_ai
)
from ..help_system import help_system

logger = logging.getLogger(__name__)

class FinancialAgent:
    def __init__(self):
        self.tools = {
            "analyze_ratios": analyze_financial_ratios_tool,
            "detect_anomalies": detect_financial_anomalies_tool,
            "generate_report": generate_financial_report_tool,
            "four_column_balance": generate_four_column_balance_sheet_tool,
            "seasonal_analysis": analyze_seasonal_performance_tool,
            "comprehensive_report": generate_comprehensive_financial_report_tool
        }
        
        # بهبود mapping کلمات کلیدی
        self.keyword_mapping = {
            "نسبت": "analyze_ratios",
            "تحلیل": "analyze_ratios",
            "نقدینگی": "analyze_ratios",
            "نسبت جاری": "analyze_ratios",
            "نسبت آنی": "analyze_ratios",
            "بازده": "analyze_ratios",
            "انحراف": "detect_anomalies",
            "مشکوک": "detect_anomalies",
            "کنترل": "detect_anomalies",
            "مغایرت": "detect_anomalies",
            "ترازنامه": "generate_report",
            "صورت مالی": "generate_report",
            "گزارش مالی": "generate_report",
            "سود و زیان": "generate_report",
            "جریان نقد": "generate_report",
            "چهارستونی": "four_column_balance",
            "چهار ستون": "four_column_balance",
            "تراز کل": "four_column_balance",
            "تراز چهارستونی": "four_column_balance",
            "تراز چهار ستونی": "four_column_balance",
            "گردش حساب": "four_column_balance",
            "فصلی": "seasonal_analysis",
            "فصل": "seasonal_analysis",
            "بهار": "seasonal_analysis",
            "تابستان": "seasonal_analysis",
            "پاییز": "seasonal_analysis",
            "زمستان": "seasonal_analysis",
            "عملکرد فصلی": "seasonal_analysis",
            "جامع": "comprehensive_report",
            "کامل": "comprehensive_report",
            "گزارش کامل": "comprehensive_report",
            "گزارش جامع": "comprehensive_report",
            "تحلیل کلی": "comprehensive_report"
        }
        
        # دستورات راهنما
        self.help_commands = {
            "راهنما": "general",
            "help": "general",
            "ابزارها": "tools_list",
            "لیست ابزارها": "tools_list",
            "چه ابزارهایی داری": "tools_list",
            "چطور استفاده کنم": "tutorial",
            "نمونه سوال": "examples",
            "جستجوی": "search",
            "راهنمای": "tool_detail"
        }
    
    def _select_tool(self, question: str) -> str:
        """انتخاب ابزار مناسب بر اساس کلمات کلیدی در سوال"""
        question_lower = question.lower()
        
        for keyword, tool_name in self.keyword_mapping.items():
            if keyword in question_lower:
                return tool_name
        
        # اگر ابزار خاصی پیدا نشد، از تحلیل جامع استفاده کن
        return "comprehensive_report"
    
    def _extract_season(self, question: str) -> str:
        """استخراج فصل از سوال"""
        question_lower = question.lower()
        
        if "بهار" in question_lower:
            return "spring"
        elif "تابستان" in question_lower:
            return "summer"
        elif "پاییز" in question_lower:
            return "autumn"
        elif "زمستان" in question_lower:
            return "winter"
        else:
            return "spring"  # پیش‌فرض
    
    def _extract_report_type(self, question: str) -> str:
        """استخراج نوع گزارش از سوال"""
        question_lower = question.lower()
        
        if "سود و زیان" in question_lower or "سودوزیان" in question_lower:
            return "income_statement"
        elif "جریان نقد" in question_lower or "نقدی" in question_lower:
            return "cash_flow"
        else:
            return "balance_sheet"  # پیش‌فرض
    
    def _context_aware_router(self, question: str, classification: Dict[str, any], 
                            company_id: int, period_id: int) -> str:
        """مسیریابی هوشمند بر اساس context و طبقه‌بندی سوال"""
        try:
            # اگر سوال مالی نیست، از fallback استفاده کن
            if not classification['is_financial']:
                return get_financial_fallback_response(question)
            
            # اگر ابزار پیشنهادی وجود دارد، از آن استفاده کن
            suggested_tool = classification['suggested_tool']
            if suggested_tool and suggested_tool in self.tools:
                tool_function = self.tools[suggested_tool]
                
                # اجرای ابزار با پارامترهای مناسب
                if suggested_tool == "four_column_balance":
                    season = self._extract_season(question)
                    return tool_function(company_id, period_id, season)
                elif suggested_tool == "seasonal_analysis":
                    season = self._extract_season(question)
                    return tool_function(company_id, period_id, season)
                elif suggested_tool == "generate_report":
                    report_type = self._extract_report_type(question)
                    return tool_function(company_id, period_id, report_type)
                else:
                    return tool_function(company_id, period_id)
            
            # اگر ابزار پیشنهادی وجود ندارد، از روش قدیمی استفاده کن
            selected_tool = self._select_tool(question)
            tool_function = self.tools.get(selected_tool)
            
            if not tool_function:
                return "متأسفانه ابزار مناسب برای پاسخ به این سوال یافت نشد."
            
            # اجرای ابزار با پارامترهای مناسب
            if selected_tool == "four_column_balance":
                season = self._extract_season(question)
                return tool_function(company_id, period_id, season)
            elif selected_tool == "seasonal_analysis":
                season = self._extract_season(question)
                return tool_function(company_id, period_id, season)
            elif selected_tool == "generate_report":
                report_type = self._extract_report_type(question)
                return tool_function(company_id, period_id, report_type)
            else:
                return tool_function(company_id, period_id)
            
        except Exception as e:
            logger.error(f"خطا در مسیریابی هوشمند: {e}")
            return f"خطا در پردازش سوال مالی: {str(e)}"
    
    def _is_json_response(self, response: str) -> bool:
        """بررسی اینکه آیا پاسخ JSON است"""
        try:
            json.loads(response)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    def _format_json_response(self, response: str, question: str, company_id: int, period_id: int) -> Dict[str, Any]:
        """فرمت‌بندی پاسخ JSON"""
        try:
            response_data = json.loads(response)
            
            # اگر پاسخ از قبل فرمت استاندارد ما را دارد، همان را برگردان
            if isinstance(response_data, dict) and 'success' in response_data:
                return response_data
            
            # اگر پاسخ JSON است اما فرمت استاندارد ما را ندارد، آن را فرمت کن
            return {
                "success": True,
                "report_type": "financial_analysis",
                "company_id": company_id,
                "period_id": period_id,
                "data": {
                    "metadata": {
                        "report_title": "تحلیل مالی",
                        "company_name": f"شرکت {company_id}",
                        "period_name": f"دوره {period_id}",
                        "generation_date": "2025-10-31",
                        "currency": "ریال",
                        "language": "fa"
                    },
                    "content": response_data,
                    "question": question
                }
            }
            
        except Exception as e:
            logger.error(f"خطا در فرمت‌بندی پاسخ JSON: {e}")
            return {
                "success": False,
                "error": f"خطا در پردازش پاسخ: {str(e)}"
            }
    
    def _format_text_response(self, response: str, question: str, company_id: int, period_id: int) -> Dict[str, Any]:
        """فرمت‌بندی پاسخ متنی"""
        return {
            "success": True,
            "report_type": "text_response",
            "company_id": company_id,
            "period_id": period_id,
            "data": {
                "metadata": {
                    "report_title": "پاسخ متنی",
                    "company_name": f"شرکت {company_id}",
                    "period_name": f"دوره {period_id}",
                    "generation_date": "2025-10-31",
                    "currency": "ریال",
                    "language": "fa"
                },
                "content": response,
                "question": question
            }
        }
    
    def _enhanced_fallback_response(self, question: str, classification: Dict[str, Any]) -> str:
        """سیستم fallback پیشرفته برای سوالات مالی نامشخص"""
        try:
            # دریافت توصیه‌های ابزار از سیستم AI
            recommendations = get_tool_recommendations_ai(question, top_k=3)
            
            if recommendations:
                response = "سوال شما به طور کامل مشخص نیست، اما می‌توانم در زمینه‌های زیر کمک کنم:\n\n"
                
                for i, rec in enumerate(recommendations, 1):
                    response += f"{i}. {rec['display_name']} (امتیاز اطمینان: {rec['confidence']:.2f})\n"
                    response += f"   توضیحات: {rec['description']}\n"
                    if rec['examples']:
                        response += f"   مثال: {rec['examples'][0]}\n"
                    response += "\n"
                
                response += "لطفاً سوال خود را دقیق‌تر مطرح کنید یا یکی از گزینه‌های بالا را انتخاب نمایید."
                return response
            
            # اگر هیچ توصیه‌ای پیدا نشد، از fallback اصلی استفاده کن
            return get_financial_fallback_response(question)
            
        except Exception as e:
            logger.error(f"خطا در سیستم fallback پیشرفته: {e}")
            return "متأسفانه در تشخیص قصد شما مشکل دارم. لطفاً سوال مالی خود را دقیق‌تر مطرح کنید."
    
    def _ai_enhanced_router(self, question: str, company_id: int, period_id: int) -> str:
        """مسیریابی پیشرفته با استفاده از AI"""
        try:
            # طبقه‌بندی هوشمند با AI
            ai_classification = classify_financial_question_ai(question)
            
            logger.info(f"سوال: '{question}' - طبقه‌بندی AI: {ai_classification}")
            
            # اگر سوال مالی نیست، از fallback پیشرفته استفاده کن
            if not ai_classification['is_financial']:
                return self._enhanced_fallback_response(question, ai_classification)
            
            # اگر ابزار پیشنهادی با اطمینان بالا وجود دارد، از آن استفاده کن
            suggested_tool = ai_classification['suggested_tool']
            confidence = ai_classification['confidence']
            
            if suggested_tool and confidence >= 0.6 and suggested_tool in self.tools:
                tool_function = self.tools[suggested_tool]
                
                # اجرای ابزار با پارامترهای مناسب
                if suggested_tool == "four_column_balance":
                    season = self._extract_season(question)
                    return tool_function(company_id, period_id, season)
                elif suggested_tool == "seasonal_analysis":
                    season = self._extract_season(question)
                    return tool_function(company_id, period_id, season)
                elif suggested_tool == "generate_report":
                    report_type = self._extract_report_type(question)
                    return tool_function(company_id, period_id, report_type)
                else:
                    return tool_function(company_id, period_id)
            
            # اگر اطمینان پایین است، از سیستم قدیمی به عنوان fallback استفاده کن
            if confidence >= 0.3:
                # استفاده از سیستم قدیمی برای تصمیم‌گیری
                old_classification = classify_financial_question(question)
                return self._context_aware_router(question, old_classification, company_id, period_id)
            else:
                # اطمینان بسیار پایین - استفاده از fallback پیشرفته
                return self._enhanced_fallback_response(question, ai_classification)
                
        except Exception as e:
            logger.error(f"خطا در مسیریابی پیشرفته: {e}")
            # در صورت خطا، به سیستم قدیمی برگرد
            old_classification = classify_financial_question(question)
            return self._context_aware_router(question, old_classification, company_id, period_id)
    
    def _is_help_command(self, question: str) -> bool:
        """بررسی اینکه آیا سوال یک دستور راهنما است"""
        question_lower = question.lower().strip()
        
        # حذف علائم نگارشی برای تطابق بهتر
        import string
        translator = str.maketrans('', '', string.punctuation + '،؟')
        question_clean = question_lower.translate(translator)
        
        # بررسی دستورات مستقیم
        for command in self.help_commands.keys():
            if (question_clean == command or 
                question_clean.startswith(command + " ") or 
                " " + command in question_clean):
                return True
        
        # بررسی سوالات متداول راهنما
        help_patterns = [
            "چه ابزارهایی داری",
            "چه کارهایی میتونی انجام بدی",
            "چیکار میتونی بکنی",
            "چه امکاناتی داری",
            "راهنمایی کن",
            "کمک میخوام",
            "نمونه سوال",
            "مثال بزن",
            "چطور استفاده کنم",
            "نحوه استفاده",
            "دستورات",
            "command",
            "help",
            "tools",
            "لیست"
        ]
        
        for pattern in help_patterns:
            if pattern in question_clean:
                return True
        
        return False
    
    def _handle_help_command(self, question: str) -> str:
        """پردازش دستورات راهنما"""
        question_lower = question.lower().strip()
        
        # تشخیص نوع دستور راهنما
        for command, help_type in self.help_commands.items():
            if question_lower.startswith(command) or command in question_lower:
                if help_type == "general":
                    return help_system.generate_help_response("general")
                elif help_type == "tools_list":
                    return help_system.generate_help_response("tools_list")
                elif help_type == "tutorial":
                    return help_system.get_usage_tutorial()
                elif help_type == "examples":
                    return self._generate_examples_response()
                elif help_type == "search":
                    query = question_lower.replace("جستجوی", "").strip()
                    return help_system.generate_help_response("search", query)
                elif help_type == "tool_detail":
                    tool_name = question_lower.replace("راهنمای", "").strip()
                    return help_system.generate_help_response("tool_detail", tool_name)
        
        # اگر دستور مشخصی پیدا نشد، راهنمای عمومی برگردان
        return help_system.generate_help_response("general")
    
    def _generate_examples_response(self) -> str:
        """تولید پاسخ با مثال‌های کاربردی"""
        examples = """💡 **مثال‌های کاربردی سوالات مالی**

📊 **نسبت‌های مالی:**
• "نسبت جاری شرکت چقدر است؟"
• "نسبت آنی را محاسبه کن"
• "نسبت بدهی به حقوق صاحبان سهام چطور است؟"

💰 **جریان نقدی:**
• "جریان نقدی شرکت را شبیه‌سازی کن"
• "تحلیل جریان وجوه نقد برای دوره ۱"

🔍 **تشخیص تقلب:**
• "اسناد مشکوک با مبالغ بالا را پیدا کن"
• "اسناد تکراری را شناسایی کن"
• "اسناد با مبالغ رند را بررسی کن"

📈 **تحلیل‌های جامع:**
• "گزارش مالی کامل شرکت را بده"
• "ترازنامه چهارستونی فصل بهار"
• "عملکرد فصلی شرکت را تحلیل کن"

📋 **گزارش‌های مالی:**
• "ترازنامه شرکت را نمایش بده"
• "صورت سود و زیان را ارائه کن"
• "گزارش جریان نقدی را بده"

💬 **می‌توانید سوالات خود را به صورت طبیعی و فارسی مطرح کنید!**"""
        
        return examples
    
    def ask_financial_question(self, question: str, company_id: int = 1, period_id: int = 1) -> Dict[str, Any]:
        """پرسش سوال مالی با استفاده از سیستم طبقه‌بندی و مسیریابی هوشمند"""
        try:
            # بررسی اینکه آیا سوال یک دستور راهنما است (اولین و مهمترین چک)
            if self._is_help_command(question):
                help_response = self._handle_help_command(question)
                return self._format_text_response(help_response, question, company_id, period_id)
            
            # اگر سوال بسیار کوتاه است یا فقط کلمات کلیدی راهنما دارد، مستقیماً به کمک پاسخ دهد
            if self._is_obvious_help_request(question):
                help_response = self._handle_help_command(question)
                return self._format_text_response(help_response, question, company_id, period_id)
            
            # استفاده از مسیریابی پیشرفته با AI
            response = self._ai_enhanced_router(question, company_id, period_id)
            
            # بررسی نوع پاسخ و فرمت‌بندی مناسب
            if self._is_json_response(response):
                return self._format_json_response(response, question, company_id, period_id)
            else:
                return self._format_text_response(response, question, company_id, period_id)
            
        except Exception as e:
            logger.error(f"خطا در پردازش سوال مالی: {e}")
            return {
                "success": False,
                "error": f"خطا در پردازش سوال مالی: {str(e)}"
            }
    
    def _is_obvious_help_request(self, question: str) -> bool:
        """بررسی اینکه آیا سوال به وضوح یک درخواست راهنما است"""
        question_lower = question.lower().strip()
        
        # حذف علائم نگارشی
        import string
        translator = str.maketrans('', '', string.punctuation + '،؟')
        question_clean = question_lower.translate(translator)
        
        # سوالات بسیار کوتاه که احتمالاً راهنما هستند
        short_help_queries = [
            "نمونه سوال",
            "نمونه",
            "مثال",
            "چطور",
            "چگونه",
            "کمک",
            "help",
            "راهنما",
            "راهنمایی",
            "دستور",
            "command",
            "چکار کنم",
            "چیکار کنم",
            "نحوه استفاده",
            "طریقه استفاده"
        ]
        
        # اگر سوال دقیقاً یکی از این عبارات است
        if question_clean in short_help_queries:
            return True
        
        # اگر سوال فقط شامل یکی از این کلمات است
        words = question_clean.split()
        if len(words) <= 2 and any(word in short_help_queries for word in words):
            return True
            
        return False
