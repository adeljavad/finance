import logging
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class FinancialAgent:

    def __init__(self, router=None, tools: Dict[str, Any] = None):
        self.router = router
        self.tools = tools or {}

        # LLMs
        import os
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        self.llm_general = ChatOpenAI(
            model="deepseek-chat",
            api_key=deepseek_key,
            base_url="https://api.deepseek.com",
            temperature=0.4
        )
        self.llm_accounting = ChatOpenAI(
            model="deepseek-chat",
            api_key=deepseek_key,
            base_url="https://api.deepseek.com",
            temperature=0.2
        )

    # ---------------- MEMORY ----------------
    def update_history(self, user_id, user, assistant):
        try:
            hist = RedisChatMessageHistory(
                url="redis://localhost:6379/0",
                session_id=f"agent:{user_id}",
            )
            hist.add_user_message(user)
            hist.add_ai_message(assistant)
        except Exception as e:
            logger.warning(f"Failed to update chat history in Redis: {e}")
            # Continue without history if Redis is not available

    # ---------------- MAIN PIPELINE ----------------
    async def ask(self, user_id: str, question: str):

        if self.router is None:
            # Fallback برای وقتی router وجود ندارد
            answer = await self.llm_general.ainvoke(
                f"به عنوان دستیار مالی پاسخ بده: {question}"
            )
            self.update_history(user_id, question, str(answer))
            return answer

        # 1️⃣ Router decides
        route = await self.router.route(question, user_id)

        if route["route"] == "greeting":
            answer = "سلام! در خدمت شما هستم. چطور میتونم کمک کنم؟"

        elif route["route"] == "general":
            answer = await self.llm_general.ainvoke(question)

        elif route["route"] == "accounting":
            answer = await self.llm_accounting.ainvoke(
                f"به‌عنوان کارشناس حسابداری پاسخ بده: {question}"
            )

        elif route["route"] == "tool":
            tool_name = route["tool_name"]
            args = route.get("arguments", {})
            tool = self.tools.get(tool_name)

            if not tool:
                answer = f"ابزار '{tool_name}' پیدا نشد."
            else:
                answer = tool.run(**args)

        else:
            answer = "متوجه نشدم، لطفا دوباره سوال کنید."

        # Save history
        self.update_history(user_id, question, str(answer))

        return answer

    def ask_financial_question(self, question: str, company_id: int, period_id: int):
        """متد همگام برای پرسش مالی"""
        # استفاده از LLM به صورت همگام
        if self.router is None:
            answer = self.llm_general.invoke(f"به عنوان دستیار مالی پاسخ بده: {question}")
            self.update_history("default_user", question, str(answer))
            return answer
        else:
            # برای سادگی، از حالت async صرف نظر می‌کنیم و از LLM عمومی استفاده می‌کنیم
            answer = self.llm_general.invoke(f"به عنوان دستیار مالی پاسخ بده: {question}")
            self.update_history("default_user", question, str(answer))
            return answer
