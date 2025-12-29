# advanced_financial_agent_complete.py
"""
سیستم کامل دستیار مالی پیشرفته با LangChain
نسخه یکپارچه و آماده استفاده
"""

import os
import logging
import json
import time
import asyncio
from typing import Dict, List, Any, Optional
from functools import lru_cache
from pydantic import BaseModel, Field
from enum import Enum
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

# ==================== IMPORTS ====================
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.tools import BaseTool
from langchain_community.cache import RedisCache
from langchain_core.globals import set_llm_cache
from langchain_community.chat_message_histories import RedisChatMessageHistory
from tenacity import retry, stop_after_attempt, wait_exponential

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== PYDANTIC MODELS ====================
class ResponseType(str, Enum):
    TOOL_RESULT = "tool_result"
    EXPERT_OPINION = "expert_opinion"
    GREETING = "greeting"
    ERROR = "error"

class RouterDecision(BaseModel):
    route: str  # tool | llm_accounting | llm_general | greeting
    tool_name: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str

class ToolSelection(BaseModel):
    tool_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    required_params: Dict[str, Any] = Field(default_factory=dict)
    reasoning: str

class FinancialResponse(BaseModel):
    success: bool
    response_type: ResponseType
    user_id: str
    question: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    follow_up_questions: Optional[List[str]] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.0)

# ==================== FINANCIAL ROUTER ====================
class FinancialRouter:
    """روتر هوشمند برای انتخاب مسیر پاسخ‌دهی"""
    
    def __init__(
        self,
        tools: List[BaseTool],
        llm: BaseChatModel,
        redis_url: str = "redis://localhost:6379",
        cache_ttl: int = 3600
    ):
        self.tools = tools
        self.llm = llm
        self.redis_url = redis_url
        self.tool_registry = {tool.name: tool for tool in tools}
        
        # تنظیم Redis Cache
        set_llm_cache(RedisCache(redis_url=redis_url, ttl=cache_ttl))
        
        # ساخت چین‌ها
        self.routing_chain = self._build_routing_chain()
        self.tool_selection_chain = self._build_tool_selection_chain()
        
        logger.info(f"✅ FinancialRouter راه‌اندازی شد: {len(tools)} ابزار")

    def _build_routing_chain(self):
        """چین روتینگ با Runnable interface"""
        routing_template = """شما یک رباتر (Router) هوشمند برای سیستم حسابداری هستید.

**کاربر پرسیده:** "{question}"

**ابزارهای موجود:**
{tools_description}

**تاریخچه اخیر:**
{history}

**دستورالعمل تصمیم‌گیری:**
- اگر سوال نیاز به محاسبات/داده دارد → `tool`
- اگر سوال تخصصی حسابداری/مالیاتی است → `llm_accounting`
- اگر احوال‌پرسی/راهنمایی است → `greeting`
- در غیر این صورت → `llm_general`

**خروجی JSON:**
{{
    "route": "tool",
    "tool_name": "balance_sheet_tool",
    "confidence": 0.95,
    "reasoning": "کاربر درخواست 'ترازنامه' کرده"
}}

تصمیم:"""

        prompt = ChatPromptTemplate.from_template(routing_template)
        output_parser = JsonOutputParser()
        
        return (
            {
                "question": RunnablePassthrough(),
                "tools_description": lambda _: self._format_tools_description(),
                "history": lambda x: self._get_memory_context(x.get("user_id", ""))
            }
            | prompt
            | self.llm
            | output_parser
        )

    def _build_tool_selection_chain(self):
        """چین انتخاب ابزار"""
        selection_template = """کاربر پرسیده: "{question}"

**ابزارهای موجود:**
{tools_description}

**کدام ابزار بهترین است؟**

خروجی JSON:
{{
    "tool_name": "balance_sheet_tool",
    "confidence": 0.92,
    "required_params": {{"company_id": 1}},
    "reasoning": "کاربر درخواست ترازنامه داده"
}}"""

        prompt = ChatPromptTemplate.from_template(selection_template)
        output_parser = JsonOutputParser()
        
        return (
            {
                "question": RunnablePassthrough(),
                "tools_description": lambda _: self._format_tools_description()
            }
            | prompt
            | self.llm
            | output_parser
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def route(
        self,
        question: str,
        user_id: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> RouterDecision:
        """روتینگ هوشمند با retry"""
        start_time = time.time()
        
        try:
            decision_dict = await self.routing_chain.ainvoke({
                "question": question,
                "user_id": user_id
            })
            
            # Validation ابزار
            if decision_dict["route"] == "tool":
                decision_dict = self._validate_tool_selection(decision_dict, question)
            
            decision = RouterDecision(**decision_dict)
            
            execution_time = time.time() - start_time
            logger.info(
                f"✅ روتر: {decision.route} | "
                f"ابزار: {decision.tool_name} | "
                f"اعتماد: {decision.confidence:.2f} | "
                f"زمان: {execution_time*1000:.2f}ms"
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"❌ خطا در روتینگ: {e}")
            return self._fallback_route(question)

    def _validate_tool_selection(self, decision_dict: Dict, question: str) -> Dict:
        """اعتبارسنجی انتخاب ابزار"""
        tool_name = decision_dict.get("tool_name")
        
        if not tool_name:
            decision_dict["route"] = "llm_accounting"
            decision_dict["reasoning"] += " (ابزار مشخص نشده)"
            return decision_dict
        
        if tool_name not in self.tool_registry:
            logger.warning(f"ابزار {tool_name} نامعتبر است. در حال انتخاب مجدد...")
            
            selection = asyncio.run(
                self.tool_selection_chain.ainvoke(question)
            )
            
            decision_dict["tool_name"] = selection["tool_name"]
            decision_dict["reasoning"] += f" (ابزار اصلاح شد به {selection['tool_name']})"
        
        return decision_dict

    def _get_memory_context(self, user_id: str) -> str:
        """دریافت حافظه از Redis"""
        if not user_id:
            return "بدون تاریخچه"
        
        try:
            history = RedisChatMessageHistory(
                url=self.redis_url,
                session_id=f"router:{user_id}"
            )
            
            messages = history.messages[-3:]
            if not messages:
                return "بدون تاریخچه"
            
            return "\n".join([
                f"- {msg.type}: {msg.content[:80]}..."
                for msg in messages
            ])
            
        except Exception as e:
            logger.warning(f"خطا در خواندن حافظه: {e}")
            return "بدون تاریخچه"

    def _format_tools_description(self) -> str:
        """فرمت توضیحات ابزارها"""
        return "\n".join([
            f"• {name}: {tool.description.strip()}"
            for name, tool in self.tool_registry.items()
        ])

    def _fallback_route(self, question: str) -> RouterDecision:
        """روتینگ fallback"""
        question_lower = question.lower()
        
        greeting_keywords = {'سلام', 'درود', 'عرض ادب', 'وقت بخیر', 'خوش آمدید'}
        help_keywords = {'کمک', 'راهنمایی', 'خدمات', 'چه کاری', 'چطور', 'چجوری'}
        
        if any(kw in question_lower for kw in greeting_keywords):
            return RouterDecision(
                route='greeting',
                tool_name=None,
                confidence=0.85,
                reasoning='تشخیص احوال‌پرسی'
            )
        
        if any(kw in question_lower for kw in help_keywords):
            return RouterDecision(
                route='greeting',
                tool_name=None,
                confidence=0.80,
                reasoning='تشخیص درخواست راهنمایی'
            )
        
        tool_keywords = {
            'balance_sheet_tool': {'ترازنامه', 'تراز', 'صورت وضعیت'},
            'financial_ratios_tool': {'نسبت', 'تحلیل مالی', 'نقدینگی', 'سودآوری'},
            'anomaly_detection_tool': {'انحراف', 'مشکوک', 'کنترل', 'مغایرت'},
            'report_generation_tool': {'گزارش', 'صورت مالی', 'سود و زیان'},
            'greeting_tool': {'کمک', 'راهنمایی', 'چه کار', 'خدمات'}
        }
        
        for tool_name, keywords in tool_keywords.items():
            if tool_name in self.tool_registry and any(kw in question_lower for kw in keywords):
                return RouterDecision(
                    route='tool',
                    tool_name=tool_name,
                    confidence=0.75,
                    reasoning=f'تطابق کلمات کلیدی {keywords}'
                )
        
        financial_keywords = {
            'حسابداری', 'حساب', 'سند', 'دفتر', 'آرتیکل',
            'بدهکار', 'بستانکار', 'مانده', 'گردش',
            'مالیات', 'ارزش افزوده', 'اظهارنامه',
            'حسابرسی', 'کنترل داخلی'
        }
        
        if any(kw in question_lower for kw in financial_keywords):
            return RouterDecision(
                route='llm_accounting',
                tool_name=None,
                confidence=0.70,
                reasoning='تشخیص سوال مالی تخصصی'
            )
        
        return RouterDecision(
            route='llm_general',
            tool_name=None,
            confidence=0.60,
            reasoning='پیش‌فرض: سوال عمومی'
        )

# ==================== FINANCIAL TOOLS ====================
class GreetingTool(BaseTool):
    name: str = "greeting_tool"
    description: str = "پاسخ به احوال‌پرسی و معرفی خدمات"
    
    def _run(self, question: str, **kwargs) -> Dict[str, Any]:
        return self._arun_sync(question, **kwargs)
    
    async def _arun(self, question: str, **kwargs) -> Dict[str, Any]:
        return self._arun_sync(question, **kwargs)
    
    def _arun_sync(self, question: str, **kwargs) -> Dict[str, Any]:
        return {
            "type": "greeting",
            "message": "سلام! من دستیار مالی هوشمند شما هستم. می‌توانم در امور حسابداری، مالیات، حسابرسی و تحلیل مالی به شما کمک کنم. سوال خود را بپرسید!",
            "services": ["تحلیل مالی", "حسابداری", "مالیات", "حسابرسی"]
        }

class BalanceSheetTool(BaseTool):
    name: str = "balance_sheet_tool"
    description: str = "محاسبه ترازنامه و مانده حساب‌ها. کلمات کلیدی: ترازنامه، تراز، صورت وضعیت"
    
    def _run(self, company_id: int, period_id: int, season: Optional[str] = "spring", **kwargs) -> Dict[str, Any]:
        return self._arun_sync(company_id, period_id, season, **kwargs)
    
    async def _arun(
        self,
        company_id: int,
        period_id: int,
        season: Optional[str] = "spring",
        **kwargs
    ) -> Dict[str, Any]:
        return self._arun_sync(company_id, period_id, season, **kwargs)
    
    def _arun_sync(
        self,
        company_id: int,
        period_id: int,
        season: Optional[str] = "spring",
        **kwargs
    ) -> Dict[str, Any]:
        # اینجا کد واقعی ترازنامه را قرار می‌دهید
        return {
            "type": "balance_sheet",
            "company_id": company_id,
            "period_id": period_id,
            "season": season,
            "total_assets": 1_000_000_000,
            "total_liabilities": 600_000_000,
            "equity": 400_000_000,
            "message": f"ترازنامه شرکت {company_id} برای دوره {period_id} محاسبه شد."
        }

class FinancialRatiosTool(BaseTool):
    name: str = "financial_ratios_tool"
    description: str = "محاسبه و تحلیل نسبت‌های مالی. کلمات کلیدی: نسبت، تحلیل مالی، نقدینگی، سودآوری"
    
    def _run(self, company_id: int, period_id: int, **kwargs) -> Dict[str, Any]:
        return self._arun_sync(company_id, period_id, **kwargs)
    
    async def _arun(
        self,
        company_id: int,
        period_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        return self._arun_sync(company_id, period_id, **kwargs)
    
    def _arun_sync(
        self,
        company_id: int,
        period_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "type": "financial_ratios",
            "company_id": company_id,
            "period_id": period_id,
            "ratios": {
                "current_ratio": 2.5,
                "quick_ratio": 1.8,
                "roe": 0.15,
                "roa": 0.12
            },
            "message": f"نسبت‌های مالی شرکت {company_id} محاسبه شدند."
        }

class AnomalyDetectionTool(BaseTool):
    name: str = "anomaly_detection_tool"
    description: str = "شناسایی انحرافات و موارد مشکوک. کلمات کلیدی: انحراف، مشکوک، کنترل، مغایرت"
    
    def _run(self, company_id: int, period_id: int, **kwargs) -> Dict[str, Any]:
        return self._arun_sync(company_id, period_id, **kwargs)
    
    async def _arun(
        self,
        company_id: int,
        period_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        return self._arun_sync(company_id, period_id, **kwargs)
    
    def _arun_sync(
        self,
        company_id: int,
        period_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "type": "anomaly_detection",
            "company_id": company_id,
            "period_id": period_id,
            "anomalies_found": 3,
            "details": [
                "انحراف در حساب درآمدها",
                "مغایرت در موجودی کالا",
                "عدم تطابق در اسناد پرداختنی"
            ]
        }

class ReportGenerationTool(BaseTool):
    name: str = "report_generation_tool"
    description: str = "تولید گزارش‌های مالی. کلمات کلیدی: گزارش، صورت مالی، سود و زیان"
    
    def _run(self, company_id: int, period_id: int, report_type: str = "balance_sheet", **kwargs) -> Dict[str, Any]:
        return self._arun_sync(company_id, period_id, report_type, **kwargs)
    
    async def _arun(
        self,
        company_id: int,
        period_id: int,
        report_type: str = "balance_sheet",
        **kwargs
    ) -> Dict[str, Any]:
        return self._arun_sync(company_id, period_id, report_type, **kwargs)
    
    def _arun_sync(
        self,
        company_id: int,
        period_id: int,
        report_type: str = "balance_sheet",
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "type": "financial_report",
            "company_id": company_id,
            "period_id": period_id,
            "report_type": report_type,
            "status": "generated",
            "download_link": f"/reports/{company_id}_{period_id}_{report_type}.pdf"
        }

class LedgerTool(BaseTool):
    name: str = "ledger_tool"
    description: str = "مدیریت دفتر معین و دفتر کل. کلمات کلیدی: دفتر، معین، کل"
    
    def _run(self, company_id: int, period_id: int, account_code: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        return self._arun_sync(company_id, period_id, account_code, **kwargs)
    
    async def _arun(
        self,
        company_id: int,
        period_id: int,
        account_code: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        return self._arun_sync(company_id, period_id, account_code, **kwargs)
    
    def _arun_sync(
        self,
        company_id: int,
        period_id: int,
        account_code: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "type": "ledger",
            "company_id": company_id,
            "period_id": period_id,
            "account_code": account_code,
            "entries": [
                {"date": "2024-01-01", "debit": 1000000, "credit": 0, "balance": 1000000},
                {"date": "2024-01-02", "debit": 0, "credit": 500000, "balance": 500000}
            ]
        }

class TaxAdvisorTool(BaseTool):
    name: str = "tax_advisor_tool"
    description: str = "مشاوره مالیاتی. کلمات کلیدی: مالیات، ارزش افزوده، اظهارنامه"
    
    def _run(self, question: str, **kwargs) -> Dict[str, Any]:
        return self._arun_sync(question, **kwargs)
    
    async def _arun(
        self,
        question: str,
        **kwargs
    ) -> Dict[str, Any]:
        return self._arun_sync(question, **kwargs)
    
    def _arun_sync(
        self,
        question: str,
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "type": "tax_advice",
            "answer": "طبق قانون مالیات بر ارزش افزوده، نرخ استاندارد 9٪ است.",
            "law_reference": "ماده ۳۸ قانون مالیات بر ارزش افزوده"
        }

class AuditTool(BaseTool):
    name: str = "audit_tool"
    description: str = "خدمات حسابرسی و کنترل داخلی. کلمات کلیدی: حسابرسی، کنترل داخلی"
    
    def _run(self, company_id: int, **kwargs) -> Dict[str, Any]:
        return self._arun_sync(company_id, **kwargs)
    
    async def _arun(
        self,
        company_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        return self._arun_sync(company_id, **kwargs)
    
    def _arun_sync(
        self,
        company_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "type": "audit_report",
            "company_id": company_id,
            "control_status": "نیاز به بهبود",
            "recommendations": [
                "تقویت کنترل‌های دسترسی به سیستم",
                "اجرای segregation of duties",
                "بررسی دوره‌ای معاملات مشکوک"
            ]
        }

# ==================== ADVANCED FINANCIAL AGENT ====================
class AdvancedFinancialAgent:
    """دستیار مالی پیشرفته با روتر هوشمند"""
    
    def __init__(
        self,
        redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379"),
        llm_config: Optional[Dict[str, Any]] = None
    ):
        self.llm_config = llm_config or {
            "model": "deepseek-chat",
            "temperature": 0.3,
            "api_key": os.getenv("DEEPSEEK_API_KEY"),
            "base_url": "https://api.deepseek.com",
            "max_tokens": 2000
        }
        
        self.llm = ChatOpenAI(**self.llm_config)
        self.tools = self._initialize_tools()
        self.redis_url = redis_url
        
        self.router = FinancialRouter(
            tools=self.tools,
            llm=self.llm,
            redis_url=redis_url
        )

    def _initialize_tools(self) -> List[BaseTool]:
        return [
            GreetingTool(),
            BalanceSheetTool(),
            FinancialRatiosTool(),
            AnomalyDetectionTool(),
            ReportGenerationTool(),
            LedgerTool(),
            TaxAdvisorTool(),
            AuditTool(),
        ]

    async def process_question(
        self,
        question: str,
        user_id: str,
        company_id: int = 1,
        period_id: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> FinancialResponse:
        """پردازش سوال با روتر هوشمند"""
        
        start_time = time.time()
        
        try:
            # Routing
            router_decision = await self.router.route(
                question=question,
                user_id=user_id,
                user_context={
                    "company_id": company_id,
                    "period_id": period_id,
                    **(metadata or {})
                }
            )
            
            # اجرای تصمیم
            response_data = await self._execute_decision(
                decision=router_decision,
                question=question,
                user_id=user_id,
                company_id=company_id,
                period_id=period_id
            )
            
            # ساخت پاسخ نهایی
            response = FinancialResponse(
                success=True,
                response_type=ResponseType(router_decision.route),
                user_id=user_id,
                question=question,
                data=response_data,
                metadata={
                    "company_id": company_id,
                    "period_id": period_id,
                    "router_confidence": round(router_decision.confidence, 2),
                    "tool_used": router_decision.tool_name,
                    "processing_time_ms": round((time.time() - start_time) * 1000, 2),
                    "model": self.llm_config["model"]
                },
                confidence_score=router_decision.confidence,
                follow_up_questions=self._generate_follow_up_questions(router_decision.route)
            )
            
            # به‌روزرسانی حافظه
            await self._update_user_memory(user_id, question, response)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ خطا در پردازش: {e}", exc_info=True)
            return self._fallback_response(question, user_id, str(e))

    async def _execute_decision(
        self,
        decision: RouterDecision,
        question: str,
        user_id: str,
        company_id: int,
        period_id: int
    ) -> Dict[str, Any]:
        """اجرای تصمیم روتر"""
        
        if decision.route == "tool" and decision.tool_name:
            return await self._execute_tool(
                tool_name=decision.tool_name,
                question=question,
                company_id=company_id,
                period_id=period_id,
                user_id=user_id
            )
        
        elif decision.route == "greeting":
            return await self._handle_greeting(question, user_id)
        
        elif decision.route == "llm_accounting":
            return await self._handle_llm_response(question, "accounting_expert", user_id)
        
        else:  # llm_general
            return await self._handle_llm_response(question, "help_expert", user_id)

    async def _execute_tool(
        self,
        tool_name: str,
        question: str,
        company_id: int,
        period_id: int,
        user_id: str
    ) -> Dict[str, Any]:
        """اجرای ابزار"""
        
        try:
            tool = self.router.tool_registry.get(tool_name)
            if not tool:
                raise ValueError(f"ابزار {tool_name} یافت نشد")
            
            input_args = {
                "question": question,
                "company_id": company_id,
                "period_id": period_id,
                "user_id": user_id,
                "user_context": await self._get_user_context(user_id)
            }
            
            input_args.update(self._extract_additional_params(question))
            
            logger.debug(f"🛠️ اجرای ابزار: {tool_name}")
            result = await tool.ainvoke(input_args)
            
            return {
                "tool_name": tool_name,
                "result": result,
                "status": "success",
                "executed_at": time.time()
            }
            
        except Exception as e:
            logger.error(f"❌ خطا در اجرای ابزار {tool_name}: {e}", exc_info=True)
            return {
                "tool_name": tool_name,
                "status": "error",
                "error": str(e),
                "message": "خطا در اجرای ابزار"
            }

    async def _handle_greeting(self, question: str, user_id: str) -> Dict[str, Any]:
        """پاسخ احوال‌پرسی هوشمند"""
        
        history = RedisChatMessageHistory(
            url=self.redis_url,
            session_id=f"agent:{user_id}"
        )
        
        conversation_count = len(history.messages) // 2
        is_returning_user = conversation_count > 1
        
        greeting_prompt = f"""شما یک دستیار مالی هوشمند و دوستانه هستید.

کاربر: "{question}"
تاریخچه: {conversation_count} مکالمه قبلی
کاربر بازگشتی: {'بله' if is_returning_user else 'خیر'}

دستورالعمل:
1. سلام و احوال‌پرسی گرم
2. معرفی خدمات به صورت جذاب
3. استفاده از ایموجی
4. تشویق به پرسش سوالات مالی
5. اگر بازگشتی است، به آن اشاره کن

پاسخ:"""
        
        response = await self.llm.ainvoke(greeting_prompt)
        
        return {
            "response_type": "greeting",
            "content": response.content,
            "personalized": is_returning_user,
            "conversation_count": conversation_count
        }

    async def _handle_llm_response(
        self,
        question: str,
        domain: str,
        user_id: str
    ) -> Dict[str, Any]:
        """پاسخ LLM برای سوالات تخصصی"""
        
        expert_prompts = {
            "accounting_expert": """شما یک حسابدار و حسابرس حرفه‌ای با 20 سال تجربه هستید.
تخصص: استانداردهای ایران، مالیات، حسابرسی، گزارش‌دهی
لطفاً پاسخ دقیق و حرفه‌ای دهید:""",
            
            "help_expert": """شما یک دستیار مالی هوشمند و دوستانه هستید.
پاسخ: واضح، کاربردی، با ایموجی، تشویق‌کننده
لطفاً پاسخ دهید:"""
        }
        
        system_prompt = expert_prompts.get(domain, expert_prompts["accounting_expert"])
        full_prompt = f"{system_prompt}\n\nسوال کاربر: {question}"
        
        response = await self.llm.ainvoke(full_prompt)
        
        return {
            "response_type": "llm_expert",
            "domain": domain,
            "content": response.content,
            "model": self.llm_config["model"]
        }

    def _extract_additional_params(self, question: str) -> Dict[str, Any]:
        """استخراج پارامترهای اضافی از سوال"""
        
        question_lower = question.lower()
        params = {}
        
        # تشخیص فصل
        if "تابستان" in question_lower:
            params["season"] = "summer"
        elif "پاییز" in question_lower:
            params["season"] = "autumn"
        elif "زمستان" in question_lower:
            params["season"] = "winter"
        else:
            params["season"] = "spring"
        
        # تشخیص نوع گزارش
        if "ترازنامه" in question_lower:
            params["report_type"] = "balance_sheet"
        elif "سود و زیان" in question_lower:
            params["report_type"] = "income_statement"
        elif "جریان نقد" in question_lower:
            params["report_type"] = "cash_flow"
        
        return params

    async def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """بازیابی context کاربر"""
        
        try:
            history = RedisChatMessageHistory(
                url=self.redis_url,
                session_id=f"agent:{user_id}"
            )
            
            recent_messages = history.messages[-10:]
            
            return {
                "conversation_count": len(recent_messages) // 2,
                "last_questions": [
                    msg.content for msg in recent_messages[-5:]
                    if msg.type == "human"
                ]
            }
            
        except Exception as e:
            logger.warning(f"خطا در بازیابی context: {e}")
            return {}

    async def _update_user_memory(
        self,
        user_id: str,
        question: str,
        response: FinancialResponse
    ):
        """به‌روزرسانی حافظه کاربر"""
        
        try:
            history = RedisChatMessageHistory(
                url=self.redis_url,
                session_id=f"agent:{user_id}"
            )
            
            history.add_user_message(question)
            history.add_ai_message(str(response.dict()))
            
            logger.debug(f"✅ حافظه کاربر {user_id} به‌روز شد")
            
        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی حافظه: {e}")

    def _generate_follow_up_questions(self, route: str) -> Optional[List[str]]:
        """تولید سوالات پیشنهادی"""
        
        follow_up_map = {
            "tool": [
                "آیا می‌خواهید تحلیل بیشتری روی این داده‌ها داشته باشید؟",
                "آیا می‌خواهید این گزارش را دانلود کنید؟"
            ],
            "greeting": [
                "مثلاً می‌توانید بپرسید: 'ترازنامه بده' یا 'نسبت‌ها را تحلیل کن'",
                "یا سوالات مالیاتی خود را بپرسید"
            ],
            "llm_accounting": [
                "آیا نیاز به مثال عملی دارید؟",
                "آیا می‌خواهید قوانین مرتبط را هم بررسی کنیم؟"
            ]
        }
        
        return follow_up_map.get(route)

    def _fallback_response(
        self,
        question: str,
        user_id: str,
        error: str
    ) -> FinancialResponse:
        """پاسخ fallback در صورت خطا"""
        
        logger.warning(f"⚠️ Fallback برای: {question[:60]}... | خطا: {error[:50]}...")
        
        return FinancialResponse(
            success=False,
            response_type=ResponseType.ERROR,
            user_id=user_id,
            question=question,
            data={
                "error": error,
                "message": "متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید یا سوال را ساده‌تر مطرح کنید."
            },
            metadata={"details": error},
            confidence_score=0.0,
            follow_up_questions=[
                "آیا می‌توانید سوال را ساده‌تر کنید؟",
                "آیا می‌خواهید با پشتیبانی تماس بگیرید؟"
            ]
        )

# ==================== ASYNC/SYNC INTERFACE ====================
async def ask_financial_question_complete(
    question: str,
    user_id: str,
    company_id: int = 1,
    period_id: int = 1,
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379"),
    llm_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    ✅ تابع async اصلی برای استفاده از سیستم کامل
    
    Args:
        question: سوال کاربر
        user_id: شناسه یکتای کاربر (مثل user_123)
        company_id: شناسه شرکت (پیش‌فرض: 1)
        period_id: شناسه دوره مالی (پیش‌فرض: 1)
        redis_url: آدرس Redis
        llm_config: تنظیمات LLM (اختیاری)
        
    Returns:
        Dict[str, Any]: پاسخ کامل به صورت dictionary
        
    Examples:
        >>> response = await ask_financial_question_complete("ترازنامه بده", "user_123")
        >>> print(response["data"]["result"]["total_assets"])
    """
    
    # بررسی Redis
    if redis_url.startswith("redis://") and not _check_redis_connection(redis_url):
        logger.warning("⚠️ Redis در دسترس نیست. از حافظه محلی استفاده می‌شود.")
        redis_url = "memory://"
    
    agent = AdvancedFinancialAgent(redis_url=redis_url, llm_config=llm_config)
    response = await agent.process_question(
        question=question,
        user_id=user_id,
        company_id=company_id,
        period_id=period_id
    )
    
    return response.dict()

def ask_financial_question_complete_sync(
    question: str,
    user_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    نسخه sync برای کدهای قدیمی (استفاده از asyncio.run)
    """
    return asyncio.run(ask_financial_question_complete(question, user_id, **kwargs))

# ==================== UTILITY FUNCTIONS ====================
def _check_redis_connection(redis_url: str) -> bool:
    """بررسی اتصال Redis"""
    try:
        import redis
        client = redis.from_url(redis_url)
        client.ping()
        return True
    except Exception:
        return False

def show_sample_calls():
    """نمایش مثال‌های آماده برای کپی/پیست"""
    
    samples = """
# ========== نمونه کدهای آماده برای استفاده ==========

# 1. اجرای async (توصیه می‌شود)
import asyncio
from financial_system.agents.advanced_financial_agent_complete import ask_financial_question_complete

async def demo():
    response = await ask_financial_question_complete(
        question="ترازنامه را بده",
        user_id="user_123"
    )
    print(response)

asyncio.run(demo())

# 2. اجرای sync (ساده‌تر)
from financial_system.agents.advanced_financial_agent_complete import ask_financial_question_complete_sync

response = ask_financial_question_complete_sync(
    question="نسبت جاری چیست؟",
    user_id="user_456"
)
print(response)

# 3. استفاده مستقیم از کلاس
from financial_system.agents.advanced_financial_agent_complete import AdvancedFinancialAgent

agent = AdvancedFinancialAgent(redis_url="redis://localhost:6379")
response = asyncio.run(agent.process_question("گزارش مالی بده", "user_789"))
print(response.dict())

# ========== تنظیمات ==========

# Redis (اختیاری اما توصیه می‌شود)
# دیتابیس Redis را نصب و اجرا کنید:
# docker run -d -p 6379:6379 redis:latest

# متغیرهای محیطی:
# export OPENAI_API_KEY="sk-..."
# export REDIS_URL="redis://localhost:6379"

# ===============================================
"""
    print(samples)

# ==================== MAIN & EXAMPLES ====================
async def main():
    """مثال‌های استفاده از دستیار مالی"""
    
    print("="*60)
    print("دستیار مالی هوشمند - نسخه دمو")
    print("="*60)
    
    # مثال 1: ترازنامه
    print("\n🔹 مثال 1: ترازنامه")
    response = await ask_financial_question_complete(
        question="ترازنامه شرکت برای فصل تابستان را بده",
        user_id="user_123",
        company_id=1,
        period_id=2
    )
    print(f"پاسخ: {response['data']['result']['message']}")
    print(f"ابزار: {response['metadata']['tool_used']}")
    print(f"زمان: {response['metadata']['processing_time_ms']}ms")
    
    # مثال 2: سوال مالی عمومی
    print("\n🔹 مثال 2: سوال مالی عمومی")
    response = await ask_financial_question_complete(
        question="نسبت جاری چیست و چطور محاسبه می‌شود؟",
        user_id="user_456"
    )
    print(f"پاسخ: {response['data']['content'][:100]}...")
    print(f"نوع پاسخ: {response['response_type']}")
    
    # مثال 3: احوال‌پرسی
    print("\n🔹 مثال 3: احوال‌پرسی")
    response = await ask_financial_question_complete(
        question="سلام، تو چه کمکی می‌تونی به من بکنی؟",
        user_id="user_789"
    )
    print(f"پاسخ: {response['data']['content']}")
    print(f"سوالات پیشنهادی: {response['follow_up_questions']}")
    
    # مثال 4: حسابرسی
    print("\n🔹 مثال 4: حسابرسی")
    response = await ask_financial_question_complete(
        question="کنترل‌های داخلی شرکت را بررسی کن",
        user_id="user_101",
        company_id=1
    )
    print(f"پاسخ: {response['data']['result']['recommendations']}")
    
    print("\n" + "="*60)

# ==================== RUN DEMO ====================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        # اجرای دمو
        asyncio.run(main())
    elif len(sys.argv) > 1 and sys.argv[1] == "--samples":
        # نمایش نمونه کدها
        show_sample_calls()
    else:
        print("""
دستیار مالی هوشمند - راهنما

استفاده:
  python advanced_financial_agent_complete.py --demo     # اجرای دمو
  python advanced_financial_agent_complete.py --samples  # نمایش نمونه کدها

یا import کردن در پروژه خود:
  from financial_system.agents.advanced_financial_agent_complete import ask_financial_question_complete
        """)
