import json
import asyncio
import logging
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.chat_message_histories import RedisChatMessageHistory

logger = logging.getLogger(__name__)


class FinancialRouter:

    def __init__(self, tools: Dict[str, Any]):
        self.tools = tools
        self.tool_names = list(tools.keys())

        self.llm = ChatOpenAI(
            model="gpt-4.1",
            temperature=0,
        )

        self.router_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
تو یک Router هوشمند هستی که تصمیم می‌گیرد سؤال کاربر به کدام مسیر برود.

قوانین:
- اگر احوال‌پرسی → greeting
- اگر سوال مالی/حسابداری تخصصی → accounting
- اگر نیاز به محاسبه و داده → tool
- در سایر موارد → general

ابزارهای موجود:
{tools_list}

خروجی فقط JSON:
{
  "route": "greeting" | "accounting" | "general" | "tool",
  "tool_name": null,
  "arguments": {},
  "reasoning": "..."
}
"""
            ),
            ("user", "{question}"),
            ("assistant", "حافظه اخیر:\n{history}")
        ])

        self.parser = JsonOutputParser()

    # ---------------- MEMORY ----------------
    def load_history(self, user_id: str):
        try:
            hist = RedisChatMessageHistory(
                session_id=f"router:{user_id}",
                url="redis://localhost:6379/0"
            )

            last = hist.messages[-5:]
            if not last:
                return "بدون تاریخچه"

            return "\n".join(f"{m.type}: {m.content[:80]}" for m in last)
        except:
            return "بدون تاریخچه"

    def save(self, user_id, u, a):
        try:
            hist = RedisChatMessageHistory(
                session_id=f"router:{user_id}",
                url="redis://localhost:6379/0"
            )
            hist.add_user_message(u)
            hist.add_ai_message(a)
        except Exception as e:
            logger.error(f"Memory save failed: {e}")

    # ---------------- ROUTE ----------------
    async def route(self, question: str, user_id: str):
        history = self.load_history(user_id)

        try:
            result = await (self.router_prompt | self.llm | self.parser).ainvoke({
                "question": question,
                "history": history,
                "tools_list": "\n".join(f"- {name}" for name in self.tool_names)
            })
        except:
            result = {
                "route": "general",
                "tool_name": None,
                "arguments": {},
                "reasoning": "fallback"
            }

        self.save(user_id, question, str(result))
        return result
