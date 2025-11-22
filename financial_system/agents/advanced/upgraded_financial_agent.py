"""
سیستم پیشرفته دستیار مالی با استفاده از معماری ارتقاء یافته
"""

import os
import logging
import json
import time
from typing import Dict, List, Any, Optional
from openai import OpenAI

from .router_agent import SmartRouter
from ..tools.greetings.greeting_tool import GreetingTool
from ..tools.accounting.balance_tool import BalanceTool
from ...models.response_models import (
    FinancialResponse, 
    ResponseFactory, 
    ToolExecutionResult,
    UserContext
)

logger = logging.getLogger(__name__)

# تنظیمات DeepSeek API
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"


class UpgradedFinancialAgent:
    """دستیار مالی پیشرفته با استفاده از معماری ارتقاء یافته"""
    
    def __init__(self):
        # ابزارهای موجود
        self.tools = self._initialize_tools()
        
        # تنظیمات LLM
        self.llm_config = {
            "openai_api_key": DEEPSEEK_API_KEY,
            "temperature": 0.1
        }
        
        # SmartRouter برای روتینگ هوشمند
        self.router = SmartRouter(tools=self.tools, llm_config=self.llm_config)
        
        # پرامپت‌های حرفه‌ای
        self.expert_prompts = self._initialize_expert_prompts()
        
        logger.info("UpgradedFinancialAgent با معماری جدید راه‌اندازی شد")

    def _initialize_tools(self) -> List:
        """راه‌اندازی ابزارهای موجود"""
        return [
            GreetingTool(),
            BalanceTool()
        ]

    def _initialize_expert_prompts(self) -> Dict[str, str]:
        """پرامپت‌های حرفه‌ای برای حوزه‌های مختلف مالی"""
        return {
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
4. از اصطلاحات پیچیده اجتناب کنید

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
2. رویکرد سیستماتیک و مبتنی بر شواهد داشته باشید
3. ریسک‌ها و کنترل‌ها را شناسایی کنید
4. توصیه‌های بهبود ارائه دهید

لطفاً به سوال زیر به عنوان یک حسابرس پاسخ دهید:
"""
        }

    async def ask_question(
        self, 
        question: str, 
        user_id: str = "default_user",
        company_id: int = 1, 
        period_id: int = 1,
        user_context: Optional[UserContext] = None
    ) -> FinancialResponse:
        """
        پاسخ به سوال کاربر با استفاده از معماری ارتقاء یافته
        
        Args:
            question: سوال کاربر
            user_id: شناسه کاربر
            company_id: شناسه شرکت
            period_id: شناسه دوره مالی
            user_context: context کاربر
            
        Returns:
            FinancialResponse: پاسخ استاندارد
        """
        
        start_time = time.time()
        
        try:
            logger.info(f"پردازش سوال: '{question}' برای کاربر {user_id}")
            
            # روتینگ هوشمند
            routing_decision = await self.router.route(question, user_id, user_context)
            
            # پردازش بر اساس تصمیم روتینگ
            if routing_decision.route == "greeting":
                response = await self._handle_greeting(question, user_id, user_context)
            elif routing_decision.route == "tool":
                response = await self._handle_tool_execution(
                    routing_decision.tool_name, question, user_id, company_id, period_id
                )
            elif routing_decision.route == "llm_accounting":
                response = await self._handle_accounting_question(question, user_id)
            else:
                response = await self._handle_general_question(question, user_id)
            
            execution_time = time.time() - start_time
            response.execution_time = execution_time
            
            logger.info(f"پاسخ تولید شد - نوع: {response.response_type} - زمان: {execution_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"خطا در پردازش سوال: {e}")
            execution_time = time.time() - start_time
            
            return ResponseFactory.create_error_response(
                user_id=user_id,
                question=question,
                error_message=f"خطا در پردازش سوال: {str(e)}",
                error_type="processing_error"
            )

    async def _handle_greeting(
        self, 
        question: str, 
        user_id: str,
        user_context: Optional[UserContext] = None
    ) -> FinancialResponse:
        """پردازش سوالات احوال‌پرسی"""
        
        try:
            # استفاده از ابزار احوال‌پرسی
            greeting_tool = self.tools[0]  # اولین ابزار GreetingTool است
            user_name = user_context.user_name if user_context else None
            
            result = await greeting_tool._arun(question, user_name)
            
            if result["success"]:
                return ResponseFactory.create_greeting_response(
                    user_id=user_id,
                    question=question,
                    greeting_data=result,
                    user_name=user_name
                )
            else:
                return ResponseFactory.create_error_response(
                    user_id=user_id,
                    question=question,
                    error_message=result["error"]
                )
                
        except Exception as e:
            logger.error(f"خطا در ابزار احوال‌پرسی: {e}")
            return self._get_fallback_greeting_response(user_id, question)

    async def _handle_tool_execution(
        self,
        tool_name: str,
        question: str,
        user_id: str,
        company_id: int,
        period_id: int
    ) -> FinancialResponse:
        """اجرای ابزار تخصصی"""
        
        try:
            # تشخیص فصل از سوال
            season = "spring"  # پیش‌فرض
            if "تابستان" in question.lower():
                season = "summer"
            elif "پاییز" in question.lower():
                season = "autumn"
            elif "زمستان" in question.lower():
                season = "winter"
            
            # اجرای ابزار مناسب
            if tool_name == "greeting_tool":
                return await self._handle_greeting(question, user_id)
            elif tool_name == "balance_tool":
                # استفاده از ابزار تراز چهارستونی
                balance_tool = self.tools[1]  # ابزار دوم BalanceTool است
                result = await balance_tool._arun(company_id, period_id, season)
                
                if result["success"]:
                    return ResponseFactory.create_tool_response(
                        user_id=user_id,
                        question=question,
                        tool_result=result,
                        tool_name="balance_tool"
                    )
                else:
                    return ResponseFactory.create_error_response(
                        user_id=user_id,
                        question=question,
                        error_message=result["error"]
                    )
            else:
                return ResponseFactory.create_error_response(
                    user_id=user_id,
                    question=question,
                    error_message=f"ابزار {tool_name} در حال حاضر در دسترس نیست"
                )
                
        except Exception as e:
            logger.error(f"خطا در اجرای ابزار {tool_name}: {e}")
            return ResponseFactory.create_error_response(
                user_id=user_id,
                question=question,
                error_message=f"خطا در اجرای ابزار: {str(e)}"
            )

    async def _handle_accounting_question(self, question: str, user_id: str) -> FinancialResponse:
        """پردازش سوالات حسابداری با DeepSeek"""
        
        try:
            # تشخیص حوزه تخصصی
            domain = self._classify_accounting_domain(question)
            prompt = self._get_expert_prompt(domain, question)
            
            # ارسال به DeepSeek
            response_text = await self._ask_deepseek(prompt, question)
            
            return ResponseFactory.create_expert_response(
                user_id=user_id,
                question=question,
                expert_opinion=response_text,
                domain=domain,
                confidence=0.85
            )
            
        except Exception as e:
            logger.error(f"خطا در پردازش سوال حسابداری: {e}")
            return ResponseFactory.create_error_response(
                user_id=user_id,
                question=question,
                error_message=f"خطا در پردازش سوال حسابداری: {str(e)}"
            )

    async def _handle_general_question(self, question: str, user_id: str) -> FinancialResponse:
        """پردازش سوالات عمومی"""
        
        try:
            # استفاده از پرامپت عمومی
            prompt = f"""
تو یک دستیار مالی هوشمند هستی که به سوالات مختلف کاربران پاسخ می‌دهی.

سوال کاربر: "{question}"

لطفاً به این سوال به عنوان یک دستیار مالی پاسخ بده:
"""
            
            response_text = await self._ask_deepseek(prompt, question)
            
            return ResponseFactory.create_expert_response(
                user_id=user_id,
                question=question,
                expert_opinion=response_text,
                domain="general",
                confidence=0.7
            )
            
        except Exception as e:
            logger.error(f"خطا در پردازش سوال عمومی: {e}")
            return ResponseFactory.create_error_response(
                user_id=user_id,
                question=question,
                error_message=f"خطا در پردازش سوال عمومی: {str(e)}"
            )

    def _classify_accounting_domain(self, question: str) -> str:
        """طبقه‌بندی حوزه حسابداری سوال"""
        
        question_lower = question.lower()
        
        # کلمات کلیدی برای هر حوزه
        tax_keywords = [
            'مالیات', 'ارزش افزوده', 'vat', 'اظهارنامه', 'معافیت',
            'مالیاتی', 'مالیات بر', 'مالیات مستقیم', 'مالیات غیرمستقیم'
        ]
        
        audit_keywords = [
            'حسابرسی', 'کنترل داخلی', 'انحراف', 'مشکوک', 'تقلب',
            'حسابرس', 'گزارش حسابرسی', 'رسیدگی'
        ]
        
        financial_keywords = [
            'نسبت', 'تحلیل', 'گزارش', 'صورت مالی', 'ترازنامه',
            'سود و زیان', 'جریان نقد', 'نقدینگی', 'بازده', 'سودآوری'
        ]
        
        # تشخیص حوزه
        if any(keyword in question_lower for keyword in tax_keywords):
            return "tax_expert"
        elif any(keyword in question_lower for keyword in audit_keywords):
            return "audit_expert"
        elif any(keyword in question_lower for keyword in financial_keywords):
            return "financial_advisor"
        else:
            return "accounting_expert"

    def _get_expert_prompt(self, domain: str, question: str) -> str:
        """دریافت پرامپت متخصص برای حوزه مشخص"""
        base_prompt = self.expert_prompts.get(domain, self.expert_prompts["accounting_expert"])
        return base_prompt + f"\n\nسوال: {question}"

    async def _ask_deepseek(self, prompt: str, question: str) -> str:
        """ارسال سوال به DeepSeek API"""
        
        try:
            if not DEEPSEEK_API_KEY:
                logger.warning("DeepSeek API key not found, using fallback response")
                return self._get_fallback_response(question)
            
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
            return self._get_fallback_response(question)

    def _get_fallback_response(self, question: str) -> str:
        """پاسخ fallback برای زمانی که DeepSeek کار نمی‌کند"""
        
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

    def _get_fallback_greeting_response(self, user_id: str, question: str) -> FinancialResponse:
        """پاسخ fallback برای احوال‌پرسی"""
        
        greeting_data = {
            "message": f"""
سلام! 👋

به سیستم هوشمند مالی خوش آمدید! من یک دستیار مالی حرفه‌ای هستم که می‌توانم در زمینه‌های مختلف مالی و حسابداری به شما کمک کنم.

اگر سوال مالی دارید یا نیاز به تحلیل خاصی دارید، خوشحال می‌شوم کمک کنم.

برای شروع می‌توانید بپرسید:
• "چه کمکی می‌توانی بکنی؟"
• "ترازنامه شرکت را نشان بده"
• "نسبت‌های مالی را تحلیل کن"

منتظر سوال شما هستم! ✨
"""
        }
        
        return ResponseFactory.create_greeting_response(
            user_id=user_id,
            question=question,
            greeting_data=greeting_data,
            user_name=None
        )


# تابع اصلی برای استفاده در سیستم
async def ask_financial_question_upgraded(
    question: str, 
    user_id: str = "default_user",
    company_id: int = 1, 
    period_id: int = 1
) -> FinancialResponse:
    """تابع اصلی برای استفاده از دستیار ارتقاء یافته"""
    agent = UpgradedFinancialAgent()
    return await agent.ask_question(question, user_id, company_id, period_id)
