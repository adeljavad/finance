"""
Agent روتینگ هوشمند برای سیستم مالی
"""

import logging
import json
import time
from typing import List, Dict, Any, Optional
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferWindowMemory
from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool

from ..models.response_models import RouterDecision, ToolSelection


logger = logging.getLogger(__name__)


class SmartRouter:
    """Agent روتینگ هوشمند با استفاده از LangChain"""
    
    def __init__(self, tools: List[BaseTool], llm_config: Dict[str, Any]):
        """
        Initialize SmartRouter
        
        Args:
            tools: لیست ابزارهای موجود
            llm_config: تنظیمات LLM
        """
        self.tools = tools
        self.llm_config = llm_config
        
        # LLM برای روتینگ
        self.router_llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.1,
            **llm_config
        )
        
        # حافظه مکالمه
        self.memory = ConversationBufferWindowMemory(k=5)
        
        # Agent برای تصمیم‌گیری
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.router_llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            memory=self.memory,
            handle_parsing_errors=True
        )
        
        logger.info(f"SmartRouter با {len(tools)} ابزار راه‌اندازی شد")

    async def route(
        self, 
        question: str, 
        user_id: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> RouterDecision:
        """
        روتینگ هوشمند سوال با استفاده از LLM
        
        Args:
            question: سوال کاربر
            user_id: شناسه کاربر
            user_context: context کاربر (اختیاری)
            
        Returns:
            RouterDecision: تصمیم روتینگ
        """
        
        start_time = time.time()
        
        try:
            # ساخت پرامپت روتینگ
            routing_prompt = self._build_routing_prompt(question, user_context)
            
            logger.info(f"روتینگ سوال: '{question}' برای کاربر {user_id}")
            
            # استفاده از LLM برای تصمیم‌گیری
            result = await self.agent.arun(routing_prompt)
            
            # پارس کردن نتیجه
            decision = self._parse_llm_response(result, question)
            
            execution_time = time.time() - start_time
            logger.info(f"تصمیم روتینگ: {decision.route} (اعتماد: {decision.confidence:.2f}) - زمان: {execution_time:.2f}s")
            
            return decision
            
        except Exception as e:
            logger.error(f"خطا در روتینگ هوشمند: {e}")
            # Fallback به روش کلاسیک
            return self._fallback_route(question)

    def _build_routing_prompt(
        self, 
        question: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """ساخت پرامپت روتینگ"""
        
        tools_description = self._format_tools_description()
        conversation_history = self.memory.load_memory_variables({})
        
        prompt = f"""
شما یک رباتر (Router) هوشمند برای سیستم حسابداری و مالی هستید.

**کاربر پرسیده:** "{question}"

**ابزارهای موجود:**
{tools_description}

**تاریخچه مکالمه اخیر:**
{conversation_history.get('history', 'بدون تاریخچه')}

**Context کاربر:**
{json.dumps(user_context or {}, ensure_ascii=False, indent=2)}

---

**دستورالعمل تصمیم‌گیری:**

1. **ابزار (tool)**: اگر سوال مستقیماً با یکی از ابزارهای موجود قابل پاسخ است
2. **LLM حسابداری (llm_accounting)**: اگر سوال تخصصی حسابداری/مالیاتی است اما نیاز به تحلیل LLM دارد
3. **LLM عمومی (llm_general)**: اگر سوال عمومی/راهنمایی است
4. **احوال‌پرسی (greeting)**: اگر فقط احوال‌پرسی یا راهنمایی اولیه است

**نکات مهم:**
- برای سوالات "چه کمکی می‌توانی بکنی؟" از greeting استفاده کنید
- برای سوالات "ترازنامه" از ابزار balance_sheet استفاده کنید
- برای سوالات "نسبت مالی" از ابزار financial_ratios استفاده کنید
- برای سوالات تعریفی از llm_accounting استفاده کنید

**خروجی مورد انتظار (JSON):**
{{
    "route": "tool",
    "tool_name": "balance_sheet_tool",
    "confidence": 0.95,
    "reasoning": "کاربر درخواست 'ترازنامه' کرده که مستقیماً با ابزار balance_sheet_tool قابل اجراست"
}}

لطفاً تصمیم خود را به صورت JSON برگردانید:
"""
        return prompt

    def _format_tools_description(self) -> str:
        """فرمت توضیحات ابزارها برای پرامپت"""
        
        descriptions = []
        for tool in self.tools:
            descriptions.append(f"• {tool.name}: {tool.description}")
        
        return "\n".join(descriptions)

    def _parse_llm_response(self, response: str, question: str) -> RouterDecision:
        """پارس کردن پاسخ LLM"""
        
        try:
            # تلاش برای پارس کردن JSON
            if response.strip().startswith('{') and response.strip().endswith('}'):
                decision_data = json.loads(response.strip())
            else:
                # اگر JSON نیست، از متن استخراج کنیم
                decision_data = self._extract_json_from_text(response)
            
            # اعتبارسنجی داده‌ها
            route = decision_data.get('route', '').lower()
            tool_name = decision_data.get('tool_name')
            confidence = float(decision_data.get('confidence', 0.5))
            reasoning = decision_data.get('reasoning', 'بدون دلیل')
            
            # اعتبارسنجی مسیر
            valid_routes = ['tool', 'llm_accounting', 'llm_general', 'greeting']
            if route not in valid_routes:
                route = self._determine_route_from_question(question)
                confidence = 0.7
                reasoning = f"مسیر نامعتبر تشخیص داده شد. بر اساس سوال تصمیم گرفته شد: {route}"
            
            # اگر مسیر tool است، ابزار باید مشخص باشد
            if route == 'tool' and not tool_name:
                available_tools = [tool.name for tool in self.tools]
                tool_name = self._select_tool_from_question(question, available_tools)
                reasoning = f"ابزار مشخص نشده بود. بر اساس سوال انتخاب شد: {tool_name}"
            
            return RouterDecision(
                route=route,
                tool_name=tool_name,
                confidence=confidence,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"خطا در پارس کردن پاسخ LLM: {e}")
            return self._fallback_route(question)

    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """استخراج JSON از متن"""
        
        try:
            # جستجوی بلوک JSON
            start_idx = text.find('{')
            end_idx = text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return {}
                
        except Exception:
            return {}

    def _fallback_route(self, question: str) -> RouterDecision:
        """روتینگ fallback برای زمانی که LLM کار نمی‌کند"""
        
        question_lower = question.lower()
        
        # کلمات کلیدی برای تشخیص
        greeting_keywords = ['سلام', 'درود', 'عرض ادب', 'وقت بخیر', 'خوش آمدید']
        help_keywords = ['کمک', 'راهنمایی', 'خدمات', 'چه کاری', 'چه کمکی']
        tool_keywords = {
            'balance_sheet_tool': ['ترازنامه', 'تراز', 'صورت وضعیت'],
            'financial_ratios_tool': ['نسبت', 'تحلیل مالی', 'نقدینگی', 'سودآوری'],
            'anomaly_detection_tool': ['انحراف', 'مشکوک', 'کنترل', 'مغایرت'],
            'report_generation_tool': ['گزارش', 'صورت مالی', 'سود و زیان']
        }
        
        # تشخیص نوع سوال
        if any(keyword in question_lower for keyword in greeting_keywords + help_keywords):
            return RouterDecision(
                route='greeting',
                tool_name=None,
                confidence=0.8,
                reasoning='سوال احوال‌پرسی یا راهنمایی تشخیص داده شد'
            )
        
        # تشخیص ابزار
        for tool_name, keywords in tool_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                return RouterDecision(
                    route='tool',
                    tool_name=tool_name,
                    confidence=0.7,
                    reasoning=f'سوال با کلمات کلیدی {keywords} تشخیص داده شد'
                )
        
        # پیش‌فرض: LLM حسابداری
        return RouterDecision(
            route='llm_accounting',
            tool_name=None,
            confidence=0.6,
            reasoning='سوال عمومی حسابداری تشخیص داده شد'
        )

    def _determine_route_from_question(self, question: str) -> str:
        """تعیین مسیر بر اساس سوال (بدون LLM)"""
        
        question_lower = question.lower()
        
        # کلمات کلیدی مالی
        financial_keywords = [
            'حسابداری', 'مالی', 'تراز', 'سند', 'دفتر', 'ثبت', 'آرتیکل',
            'بدهکار', 'بستانکار', 'مانده', 'گردش', 'اسناد', 'مالیات',
            'ارزش افزوده', 'اظهارنامه', 'حسابرسی', 'کنترل داخلی'
        ]
        
        if any(keyword in question_lower for keyword in financial_keywords):
            return 'llm_accounting'
        else:
            return 'llm_general'

    def _select_tool_from_question(self, question: str, available_tools: List[str]) -> Optional[str]:
        """انتخاب ابزار بر اساس سوال (بدون LLM)"""
        
        question_lower = question.lower()
        tool_keywords = {
            'balance_sheet_tool': ['ترازنامه', 'تراز', 'صورت وضعیت'],
            'financial_ratios_tool': ['نسبت', 'تحلیل مالی', 'نقدینگی', 'سودآوری'],
            'anomaly_detection_tool': ['انحراف', 'مشکوک', 'کنترل', 'مغایرت'],
            'report_generation_tool': ['گزارش', 'صورت مالی', 'سود و زیان'],
            'greeting_tool': ['سلام', 'کمک', 'راهنمایی', 'چه کاری']
        }
        
        for tool_name, keywords in tool_keywords.items():
            if tool_name in available_tools and any(keyword in question_lower for keyword in keywords):
                return tool_name
        
        return None

    async def select_best_tool(self, question: str) -> ToolSelection:
        """انتخاب بهترین ابزار با استفاده از LLM"""
        
        try:
            selection_prompt = f"""
کاربر پرسیده: "{question}"

ابزارهای موجود:
{self._format_tools_description()}

کدام ابزار را برای پاسخ به این سوال انتخاب می‌کنی؟

خروجی JSON:
{{
    "tool_name": "balance_sheet_tool",
    "confidence": 0.92,
    "required_params": {{"company_id": 1, "period_id": 2}},
    "reasoning": "کاربر درخواست ترازنامه داده که مستقیماً با این ابزار قابل اجراست"
}}
"""
            
            result = await self.router_llm.ainvoke(selection_prompt)
            selection_data = json.loads(result.content.strip())
            
            return ToolSelection(**selection_data)
            
        except Exception as e:
            logger.error(f"خطا در انتخاب ابزار: {e}")
            # Fallback
            available_tools = [tool.name for tool in self.tools]
            selected_tool = self._select_tool_from_question(question, available_tools)
            
            return ToolSelection(
                tool_name=selected_tool or available_tools[0],
                confidence=0.5,
                required_params={},
                reasoning="انتخاب fallback به دلیل خطا"
            )

    def update_memory(self, user_input: str, assistant_response: str):
        """به‌روزرسانی حافظه مکالمه"""
        
        self.memory.save_context(
            {"input": user_input},
            {"output": assistant_response}
        )

    def get_conversation_history(self) -> Dict[str, Any]:
        """دریافت تاریخچه مکالمه"""
        
        return self.memory.load_memory_variables({})
