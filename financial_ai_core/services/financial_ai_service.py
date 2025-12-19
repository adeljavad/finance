# financial_ai_core/services/financial_ai_service.py
from .agents.advanced.router_agent import route_user_query
from .tools import get_all_financial_tools
from .models import AIInteractionLog

class FinancialAIService:
    def __init__(self, session_id, model_name="financial-ai-core-v1", debug=False):
        self.session_id = session_id
        self.model_name = model_name
        self.debug = debug
        self.tools = get_all_financial_tools()  # لیست تمام ابزارهای مالی
    
    def process_query(self, user_query):
        """
        پردازش هوشمند پرسش کاربر:
        1. روتینگ به ابزار مناسب
        2. اجرای الگوریتم
        3. ذخیره لاگ (اختیاری)
        4. بازگرداندن نتیجه یکپارچه
        """
        try:
            # === ۱. روتینگ هوشمند (همان منطق قدیمی، ولی تمیزشده) ===
            routing_result = route_user_query(
                query=user_query,
                context={
                    "session_id": self.session_id,
                    "available_tools": list(self.tools.keys())
                }
            )
            
            # === ۲. اجرای ابزار انتخاب‌شده ===
            tool_name = routing_result.get('tool')
            if tool_name and tool_name in self.tools:
                tool = self.tools[tool_name]
                execution_result = tool.execute(
                    query=user_query,
                    context=routing_result.get('context', {})
                )
            else:
                execution_result = {
                    "answer": "متأسفانه نتوانستم ابزار مناسبی پیدا کنم.",
                    "success": False
                }
            
            # === ۳. ترکیب نتایج ===
            final_result = {
                "success": execution_result.get('success', False),
                "answer": execution_result.get('answer', ''),
                "tool_used": tool_name,
                "confidence_score": routing_result.get('confidence', 0.5),
                "tools_used": [tool_name] if tool_name else [],
                "raw_data": execution_result.get('data', None)  # داده خام برای debugging
            }
            
            # === ۴. ذخیره لاگ تعامل (با تنظیمات قابل کنترل) ===
            if getattr(settings, 'FINANCIAL_AI_LOG_INTERACTIONS', True):
                AIInteractionLog.objects.create(
                    session_id=self.session_id,
                    user_query=user_query,
                    tool_used=tool_name,
                    confidence_score=final_result['confidence_score'],
                    raw_response=final_result
                )
            
            return final_result
            
        except Exception as e:
            # مدیریت خطا در سطح سرویس
            return {
                "success": False,
                "answer": f"خطا در پردازش: {str(e)}",
                "error": str(e),
                "tool_used": None,
                "confidence_score": 0
            }