import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .agents.advanced.router_agent import route_user_query

import time
import uuid
from django.conf import settings
from .services.financial_ai_service import FinancialAIService

# ✅ خواندن تنظیمات از settings (قابل override در پروژه‌های مصرف‌کننده)
OPENAI_COMPATIBLE_MODEL_NAME = getattr(settings, 'FINANCIAL_AI_MODEL_NAME', 'financial-ai-core-v1')
DEBUG_MODE = getattr(settings, 'FINANCIAL_AI_DEBUG', False)

@csrf_exempt
@require_http_methods(["POST"])
def openai_compatible_chat(request):
    """
    API endpoint fully compatible with OpenAI format
    POST /v1/chat/completions
    
    Example request:
    {
      "model": "financial-ai-core-v1",
      "messages": [{"role": "user", "content": "سود خالص چقدر بود؟"}],
      "session_id": "sess_123"  # optional
    }
    
    Example response (OpenAI format):
    {
      "id": "chatcmpl-...",
      "object": "chat.completion",
      "created": 1717986912,
      "model": "financial-ai-core-v1",
      "choices": [...],
      "usage": {...}
    }
    """
    start_time = time.time()
    
    try:
        # === ۱. اعتبارسنجی درخواست ===
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return _error_response("Invalid JSON format", 400)
        
        messages = data.get('messages', [])
        session_id = data.get('session_id', str(uuid.uuid4()))
        model = data.get('model', OPENAI_COMPATIBLE_MODEL_NAME)
        
        if not messages or not isinstance(messages, list):
            return _error_response("'messages' field is required", 400)
        
        # آخرین پیام کاربر را استخراج می‌کنیم (مثل OpenAI)
        latest_message = next(
            (msg['content'] for msg in reversed(messages) if msg.get('role') == 'user'),
            None
        )
        if not latest_message:
            return _error_response("No user message found in 'messages'", 400)

        # === ۲. پردازش هوشمند با سرویس متمرکز ===
        service = FinancialAIService(
            session_id=session_id,
            model_name=model,
            debug=DEBUG_MODE
        )
        
        # اینجا تمام جادو انجام می‌شود:
        # - روتینگ به ابزار مناسب
        # - اجرای الگوریتم‌های مالی
        # - ترکیب نتایج
        # - مدیریت خطا
        result = service.process_query(latest_message)

        # === ۳. تبدیل به قالب OpenAI ===
        response_data = _format_as_openai_response(
            result=result,
            session_id=session_id,
            model=model,
            process_time=time.time() - start_time
        )
        
        return JsonResponse(response_data)
    
    except Exception as e:
        # خطای غیرمنتظره (مثلاً مشکل در سرویس)
        return _error_response(
            message=f"Internal server error: {str(e)}",
            status=500,
            debug_info={"exception": str(type(e))}
        )

# =============== توابع کمکی ===============
def _error_response(message, status, debug_info=None):
    """قالب‌بندی یکپارچه برای خطاها"""
    response = {
        "error": {
            "message": message,
            "type": "invalid_request_error" if status == 400 else "server_error",
            "param": None,
            "code": None
        }
    }
    if DEBUG_MODE and debug_info:
        response['debug'] = debug_info
    return JsonResponse(response, status=status)

def _format_as_openai_response(result, session_id, model, process_time):
    """تبدیل نتیجه داخلی به قالب OpenAI"""
    # ✅ محاسبه‌ی تقریبی توکن‌ها (می‌توانیم دقیق‌تر کنیم)
    prompt_tokens = len(result.get('query', '').split())
    completion_tokens = len(result.get('answer', '').split())
    
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": result.get('answer', 'متأسفانه نتوانستم پاسخ دهم.')
            },
            "finish_reason": "stop" if result.get('success') else "error"
        }],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        },
        # 🔒 اطلاعات debugging فقط در حالت توسعه
        **({"debug": {
            "session_id": session_id,
            "tools_used": result.get('tools_used', []),
            "processing_time_sec": round(process_time, 3),
            "confidence": result.get('confidence_score', 0)
        }} if DEBUG_MODE else {})
    }



@csrf_exempt
@require_http_methods(["POST"])
def advanced_chat_interface(request):
    try:
        data = json.loads(request.body)
        user_query = data.get("query", "").strip()
        user_id = data.get("user_id")

        if not user_query:
            return JsonResponse({"error": "Query is required"}, status=400)

        response = route_user_query(user_query, context={"user_id": user_id})

        return JsonResponse({
            "response": response.get("answer"),
            "tool_used": response.get("tool"),
            "confidence": response.get("confidence")
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
