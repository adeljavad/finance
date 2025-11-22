# financial_system/agents/advanced_financial_agent.py
"""
سیستم پیشرفته دستیار مالی با استفاده از LangChain و پرامپت‌های حرفه‌ای
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI

from ..tools.financial_analysis_tools import (
    analyze_financial_ratios_tool,
    detect_financial_anomalies_tool,
    generate_financial_report_tool,
    generate_four_column_balance_sheet_tool,
    analyze_seasonal_performance_tool,
    generate_comprehensive_financial_report_tool,
    analyze_financial_risks_tool,
    TOOL_DESCRIPTIONS
)

logger = logging.getLogger(__name__)

# تنظیمات DeepSeek API
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

# آستانه‌های تصمیم‌گیری سیستم هوشمند
TOOL_THRESHOLD = 5  # حداقل امتیاز برای استفاده از ابزار (افزایش یافت)
DEEPSEEK_THRESHOLD = 1  # حداقل امتیاز مالی برای استفاده از DeepSeek

class AdvancedFinancialAgent:
    """دستیار مالی پیشرفته با استفاده از پرامپت‌های حرفه‌ای"""
    
    def __init__(self):
        # پرامپت‌های حرفه‌ای برای حوزه‌های مختلف
        self.expert_prompts = self._initialize_expert_prompts()
    
    def _initialize_expert_prompts(self) -> Dict[str, str]:
        """پرامپت‌های حرفه‌ای برای حوزه‌های مختلف مالی"""
        return {
            "help_expert": """
تو یک دستیار مالی دوستانه و حرفه‌ای هستی که به کاربران در زمینه‌های مالی کمک می‌کنی.

ویژگی‌های شما:
- برخورد گرم و دوستانه با کاربران
- معرفی کامل خدمات مالی
- تشویق کاربران به پرسیدن سوالات مالی
- ارائه مثال‌های مفید از سوالات

دستورالعمل پاسخ‌دهی:
1. با سلام و احوالپرسی گرم شروع کن
2. خدمات اصلی خود را به صورت جذاب معرفی کن
3. کاربر را تشویق کن تا سوالات مالی بپرسد
4. مثال‌هایی از سوالات مفید ارائه بده
5. از ایموجی‌های مناسب استفاده کن

لطفاً به سوال زیر به عنوان یک دستیار مالی دوستانه پاسخ دهید:
""",

            "accounting_expert": """
تو یک حسابرس حرفه‌ای و متخصص حسابداری هستی که سال‌ها تجربه در زمینه حسابرسی و مشاوره مالی دارید.

ویژگی‌های شما:
- تخصص در استانداردهای حسابداری ایران
- دانش عمیق در زمینه مالیات‌ها و قوانین مالی
- تجربه در حسابرسی شرکت‌های مختلف
- توانایی تحلیل مسائل پیچیده مالی

دستورالعمل پاسخ‌دهی:
1. پاسخ‌ها باید دقیق، حرفه‌ای و مبتنی بر قوانین جاری باشد
2. در صورت نیاز به اطلاعات بیشتر، سوال بپرسید
3. از اصطلاحات تخصصی به درستی استفاده کنید
4. پاسخ‌ها باید کاربردی و قابل اجرا باشد

مثال‌های حوزه تخصصی شما:
- مالیات ارزش افزوده و محاسبات آن
- استانداردهای حسابداری
- حسابرسی داخلی و خارجی
- گزارش‌دهی مالی
- قوانین مالی و مالیاتی

لطفاً به سوال زیر به عنوان یک متخصص حسابداری پاسخ دهید:
""",

            "tax_expert": """
تو یک متخصص مالیات و قوانین مالیاتی هستید با تجربه گسترده در زمینه‌های مختلف مالیاتی.

تخصص‌های شما:
- مالیات بر ارزش افزوده (VAT)
- مالیات بر درآمد
- معافیت‌های مالیاتی
- اظهارنامه مالیاتی
- قوانین جدید مالیاتی

دستورالعمل پاسخ‌دهی:
1. پاسخ‌ها باید بر اساس قوانین جاری مالیاتی باشد
2. نرخ‌ها و مقررات به روز را ارائه دهید
3. در صورت تغییر قوانین، تاریخ اعتبار را ذکر کنید
4. مثال‌های عملی ارائه دهید

لطفاً به سوال زیر به عنوان یک متخصص مالیات پاسخ دهید:
""",

            "financial_advisor": """
تو یک مشاور مالی حرفه‌ای هستید که به افراد و شرکت‌ها در زمینه مدیریت مالی کمک می‌کنید.

خدمات شما:
- برنامه‌ریزی مالی
- مدیریت سرمایه‌گذاری
- تحلیل ریسک
- مشاوره در زمینه تأمین مالی
- راهنمایی برای بهبود سودآوری

دستورالعمل پاسخ‌دهی:
1. پاسخ‌ها باید عملی و قابل اجرا باشد
2. مزایا و معایب گزینه‌های مختلف را بررسی کنید
3. توصیه‌های شخصی‌سازی شده ارائه دهید
4- از اصطلاحات پیچیده اجتناب کنید

لطفاً به سوال زیر به عنوان یک مشاور مالی پاسخ دهید:
""",

            "audit_expert": """
تو یک حسابرس ارشد با تجربه در حسابرسی شرکت‌های بزرگ هستید.

تخصص‌های شما:
- حسابرسی صورت‌های مالی
- کنترل‌های داخلی
- کشف تقلب
- انطباق با استانداردها
- گزارش‌دهی به ذینفعان

دستورالعمل پاسخ‌دهی:
1. پاسخ‌ها باید مبتنی بر استانداردهای حسابرسی باشد
2- رویکرد سیستماتیک و مبتنی بر شواهد داشته باشید
3. ریسک‌ها و کنترل‌ها را شناسایی کنید
4. توصیه‌های بهبود ارائه دهید

لطفاً به سوال زیر به عنوان یک حسابرس پاسخ دهید:
"""
        }
    
    def _classify_question_type(self, question: str) -> Dict[str, Any]:
        """طبقه‌بندی نوع سوال"""
        question_lower = question.lower()
        
        # کلمات کلیدی برای هر حوزه
        accounting_keywords = [
            'حسابداری', 'حساب', 'تراز', 'سند', 'دفتر', 'ثبت', 'آرتیکل',
            'بدهکار', 'بستانکار', 'مانده', 'گردش', 'اسناد'
        ]
        
        tax_keywords = [
            'مالیات', 'ارزش افزوده', 'vat', 'اظهارنامه', 'معافیت',
            'مالیاتی', 'مالیات بر', 'مالیات مستقیم', 'مالیات غیرمستقیم'
        ]
        
        financial_keywords = [
            'نسبت', 'تحلیل', 'گزارش', 'صورت مالی', 'ترازنامه',
            'سود و زیان', 'جریان نقد', 'نقدینگی', 'بازده', 'سودآوری'
        ]
        
        audit_keywords = [
            'حسابرسی', 'کنترل داخلی', 'انحراف', 'مشکوک', 'تقلب',
            'حسابرس', 'گزارش حسابرسی', 'رسیدگی'
        ]
        
        # کلمات کلیدی برای سوالات راهنمایی
        help_keywords = [
            'کمک', 'راهنمایی', 'خدمات', 'چه کاری', 'چه کمکی', 'چه خدماتی',
            'چه می‌توانی', 'چه می‌توانید', 'چه کار می‌توانی', 'چه کار می‌توانید',
            'چه کاری می‌توانی', 'چه کاری می‌توانید', 'چه خدماتی ارائه می‌دهی',
            'چه خدماتی ارائه می‌دهید', 'چه خدماتی داری', 'چه خدماتی دارید'
        ]
        
        # محاسبه امتیاز برای هر حوزه
        scores = {
            'accounting': sum(1 for word in accounting_keywords if word in question_lower),
            'tax': sum(1 for word in tax_keywords if word in question_lower),
            'financial': sum(1 for word in financial_keywords if word in question_lower),
            'audit': sum(1 for word in audit_keywords if word in question_lower),
            'help': sum(1 for word in help_keywords if word in question_lower)
        }
        
        # تشخیص حوزه اصلی
        main_domain = max(scores.items(), key=lambda x: x[1])
        
        return {
            'main_domain': main_domain[0] if main_domain[1] > 0 else 'general',
            'scores': scores,
            'is_financial_related': any(score > 0 for score in scores.values()),
            'is_help_related': scores['help'] > 0
        }
    
    def _get_expert_prompt(self, domain: str, question: str) -> str:
        """دریافت پرامپت متخصص برای حوزه مشخص"""
        base_prompt = self.expert_prompts.get(domain, self.expert_prompts["accounting_expert"])
        return base_prompt + f"\n\nسوال: {question}"
    
    def _ask_deepseek(self, prompt: str, question: str) -> str:
        """ارسال سوال به DeepSeek API"""
        try:
            if not DEEPSEEK_API_KEY:
                logger.warning("DeepSeek API key not found, using fallback response")
                return self._get_fallback_response(question, {"is_financial_related": True})
            
            client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url=DEEPSEEK_BASE_URL
            )
            
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "تو یک دستیار مالی حرفه‌ای هستی که به سوالات مالی و حسابداری پاسخ می‌دهی."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"خطا در ارتباط با DeepSeek: {e}")
            return self._get_fallback_response(question, {"is_financial_related": True})
    
    def _handle_general_financial_question(self, question: str, classification: Dict[str, Any]) -> str:
        """پردازش سوالات عمومی مالی با استفاده از DeepSeek"""
        # دریافت پرامپت مناسب برای حوزه
        domain = classification['main_domain']
        prompt = self._get_expert_prompt(domain, question)
        
        # ارسال به DeepSeek
        response = self._ask_deepseek(prompt, question)
        return response
    
    def _detect_tools_needed(self, question: str, classification: Dict[str, Any]) -> Dict[str, Any]:
        """تشخیص ابزارهای مناسب برای سوال"""
        question_lower = question.lower()
        tool_scores = {}
        
        # کلمات کلیدی که نشان‌دهنده سوالات تعریفی هستند (امتیاز منفی)
        definition_keywords = ['چیست', 'تعریف', 'معنی', 'منظور', 'مفهوم', 'چیه', 'چی']
        
        # محاسبه امتیاز منفی برای سوالات تعریفی
        definition_penalty = sum(1 for keyword in definition_keywords if keyword in question_lower) * 3
        
        for tool_name, tool_info in TOOL_DESCRIPTIONS.items():
            score = 0
            # امتیاز بر اساس کلمات کلیدی
            for keyword in tool_info['keywords']:
                if keyword in question_lower:
                    score += 2
            
            # امتیاز بر اساس مثال‌ها
            for example in tool_info['examples']:
                if any(word in question_lower for word in example.lower().split()):
                    score += 1
            
            # اعمال جریمه برای سوالات تعریفی
            final_score = max(0, score - definition_penalty)
            tool_scores[tool_name] = final_score
        
        # پیدا کردن ابزار با بالاترین امتیاز
        best_tool = max(tool_scores.items(), key=lambda x: x[1])
        
        return {
            'tool_scores': tool_scores,
            'best_tool': best_tool[0] if best_tool[1] > 0 else None,
            'best_tool_score': best_tool[1],
            'definition_penalty': definition_penalty
        }
    
    def _decide_tool_or_deepseek(self, question: str, classification: Dict[str, Any]) -> str:
        """تصمیم‌گیری هوشمند برای استفاده از ابزار یا DeepSeek"""
        # تشخیص ابزارهای مناسب
        tools_analysis = self._detect_tools_needed(question, classification)
        
        logger.info(f"تحلیل ابزارها: {tools_analysis}")
        
        # تصمیم‌گیری بر اساس آستانه‌ها
        if tools_analysis['best_tool_score'] >= TOOL_THRESHOLD:
            return "USE_TOOL"
        elif classification['is_help_related']:
            return "USE_HELP"
        elif classification['is_financial_related']:
            return "USE_DEEPSEEK"
        else:
            return "USE_FALLBACK"
    
    def _execute_tool(self, tool_name: str, company_id: int, period_id: int, question: str) -> str:
        """اجرای ابزار مشخص شده"""
        try:
            tool_mapping = {
                "analyze_ratios": analyze_financial_ratios_tool,
                "detect_anomalies": detect_financial_anomalies_tool,
                "generate_report": generate_financial_report_tool,
                "four_column_balance": generate_four_column_balance_sheet_tool,
                "seasonal_analysis": analyze_seasonal_performance_tool,
                "comprehensive_report": generate_comprehensive_financial_report_tool,
                "analyze_financial_risks": analyze_financial_risks_tool
            }
            
            tool_function = tool_mapping.get(tool_name)
            if tool_function:
                # اجرای ابزار با پارامترهای مناسب
                if tool_name == "generate_report":
                    # تشخیص نوع گزارش از سوال
                    if "ترازنامه" in question.lower():
                        return tool_function(company_id, period_id, "balance_sheet")
                    elif "سود و زیان" in question.lower():
                        return tool_function(company_id, period_id, "income_statement")
                    else:
                        return tool_function(company_id, period_id, "balance_sheet")
                elif tool_name == "four_column_balance":
                    # تشخیص فصل از سوال
                    season = "spring"  # پیش‌فرض
                    if "تابستان" in question.lower():
                        season = "summer"
                    elif "پاییز" in question.lower():
                        season = "autumn"
                    elif "زمستان" in question.lower():
                        season = "winter"
                    return tool_function(company_id, period_id, season)
                elif tool_name == "seasonal_analysis":
                    # تشخیص فصل از سوال
                    season = "spring"  # پیش‌فرض
                    if "تابستان" in question.lower():
                        season = "summer"
                    elif "پاییز" in question.lower():
                        season = "autumn"
                    elif "زمستان" in question.lower():
                        season = "winter"
                    return tool_function(company_id, period_id, season)
                else:
                    return tool_function(company_id, period_id)
            else:
                return f"ابزار {tool_name} یافت نشد"
                
        except Exception as e:
            logger.error(f"خطا در اجرای ابزار {tool_name}: {e}")
            return f"خطا در اجرای ابزار: {str(e)}"
    
    def _get_fallback_response(self, question: str, classification: Dict[str, Any]) -> str:
        """پاسخ fallback برای زمانی که سیستم اصلی کار نمی‌کند"""
        if classification['is_financial_related']:
            return f"""
سوال خوبی پرسیدید! "{question}"

من یک دستیار مالی هوشمند هستم و می‌توانم در زمینه‌های زیر به شما کمک کنم:

📊 **تحلیل‌های مالی پیشرفته:**
- محاسبه نسبت‌های مالی (نقدینگی، سودآوری، اهرمی)
- تولید گزارش‌های مالی کامل
- شناسایی انحرافات و موارد مشکوک

💰 **مشاوره مالی و حسابداری:**
- پاسخ به سوالات مربوط به مالیات و قوانین مالی
- راهنمایی در زمینه استانداردهای حسابداری
- مشاوره برای بهبود عملکرد مالی

🔍 **حسابرسی و کنترل:**
- تحلیل ریسک‌های مالی
- بررسی کنترل‌های داخلی
- راهنمایی برای انطباق با مقررات

لطفاً سوال خود را دقیق‌تر مطرح کنید یا از من بخواهید در یکی از زمینه‌های فوق کمک کنم.
"""
        else:
            return f"""
سلام! من یک دستیار مالی هوشمند هستم.

متأسفانه سوال شما "{question}" در حوزه تخصصی من نیست. من در زمینه‌های زیر تخصص دارم:

• تحلیل صورت‌های مالی و نسبت‌ها
• تولید گزارش‌های مالی و حسابداری  
• مشاوره مالیاتی و قوانین مالی
• حسابرسی و کنترل‌های داخلی
• شناسایی انحرافات مالی

اگر سوال مالی دارید، خوشحال می‌شوم کمک کنم!
"""
    
    def ask_question(self, question: str, company_id: int = 1, period_id: int = 1) -> Dict[str, Any]:
        """
        پاسخ به سوال کاربر با استفاده از سیستم هوشمند پیشرفته
        
        Args:
            question: سوال کاربر
            company_id: شناسه شرکت
            period_id: شناسه دوره مالی
            
        Returns:
            Dict با پاسخ ساختاریافته
        """
        try:
            # طبقه‌بندی سوال
            classification = self._classify_question_type(question)
            logger.info(f"سوال: '{question}' - طبقه‌بندی: {classification}")
            
            # تصمیم‌گیری هوشمند برای استفاده از ابزار یا DeepSeek
            decision = self._decide_tool_or_deepseek(question, classification)
            logger.info(f"تصمیم سیستم: {decision}")
            
            if decision == "USE_TOOL":
                # استفاده از ابزارهای تخصصی
                tools_analysis = self._detect_tools_needed(question, classification)
                best_tool = tools_analysis['best_tool']
                
                if best_tool:
                    logger.info(f"استفاده از ابزار: {best_tool}")
                    response = self._execute_tool(best_tool, company_id, period_id, question)
                else:
                    response = self._handle_general_financial_question(question, classification)
                    
            elif decision == "USE_DEEPSEEK":
                # استفاده از DeepSeek برای سوالات عمومی مالی
                logger.info("استفاده از DeepSeek")
                response = self._handle_general_financial_question(question, classification)
                
            elif decision == "USE_HELP":
                # استفاده از پرامپت راهنمایی برای سوالات کمک
                logger.info("استفاده از پرامپت راهنمایی")
                domain = "help_expert"
                prompt = self._get_expert_prompt(domain, question)
                response = self._ask_deepseek(prompt, question)
                
            else:
                # استفاده از پاسخ fallback
                logger.info("استفاده از پاسخ fallback")
                response = self._get_fallback_response(question, classification)
            
            # فرمت‌بندی پاسخ
            return self._format_response(response, question, company_id, period_id, classification)
            
        except Exception as e:
            logger.error(f"خطا در پردازش سوال: {e}")
            return {
                "success": False,
                "error": f"خطا در پردازش سوال: {str(e)}",
                "question": question
            }
    
    def _format_response(self, response: str, question: str, company_id: int, period_id: int, classification: Dict[str, Any]) -> Dict[str, Any]:
        """فرمت‌بندی پاسخ نهایی"""
        try:
            # بررسی اینکه آیا پاسخ JSON است
            if self._is_json_response(response):
                response_data = json.loads(response)
                return response_data
            else:
                # فرمت‌بندی پاسخ متنی
                return {
                    "success": True,
                    "report_type": "expert_response",
                    "company_id": company_id,
                    "period_id": period_id,
                    "data": {
                        "metadata": {
                            "report_title": f"پاسخ متخصص {classification['main_domain']}",
                            "company_name": f"شرکت {company_id}",
                            "period_name": f"دوره {period_id}",
                            "generation_date": "2025-11-16",
                            "currency": "ریال",
                            "language": "fa",
                            "expert_domain": classification['main_domain']
                        },
                        "content": response,
                        "question": question,
                        "classification": classification
                    }
                }
                
        except Exception as e:
            logger.error(f"خطا در فرمت‌بندی پاسخ: {e}")
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
                        "generation_date": "2025-11-16"
                    },
                    "content": response,
                    "question": question
                }
            }
    
    def _is_json_response(self, response: str) -> bool:
        """بررسی اینکه آیا پاسخ JSON است"""
        try:
            json.loads(response)
            return True
        except (json.JSONDecodeError, TypeError):
            return False


# تابع اصلی برای استفاده در سیستم
def ask_financial_question_advanced(question: str, company_id: int = 1, period_id: int = 1) -> Dict[str, Any]:
    """تابع اصلی برای استفاده از دستیار پیشرفته"""
    agent = AdvancedFinancialAgent()
    return agent.ask_question(question, company_id, period_id)
