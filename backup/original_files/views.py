from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required # برای امنیت بیشتر
import json
import logging
import uuid
import time  # FIX: اضافه شده
from datetime import datetime # FIX: اضافه شده برای خوانایی بیشتر

from .services.agent_engine import AgentEngine
from .services.rag_engine import StableRAGEngine
from .services.data_manager import UserDataManager
import jwt
from django.conf import settings


logger = logging.getLogger(__name__)

# ایجاد نمونه‌های سراسری
agent_engine = AgentEngine()
rag_engine = StableRAGEngine()
data_manager = UserDataManager() # FIX: به بالای فایل منتقل شد

def home(request):
    """صفحه اصلی چت"""
    # ایجاد session ID جدید یا استفاده از session موجود
    session_id = request.GET.get('session_id')
    if not session_id:
        # اگر session_key وجود ندارد، یک session ID تصادفی ایجاد کن
        if not request.session.session_key:
            request.session.create()
        session_id = f"session_{request.session.session_key or uuid.uuid4().hex[:10]}"
    
    context = {
        'session_id': session_id
    }
    return render(request, 'assistant/chat.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def chat_api_django(request):
    """API چت برای تمپلیت‌های جنگو"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        
        user_id = data.get('user_id')
        if not user_id:
            if request.user.is_authenticated:
                user_id = str(request.user.id)
            else:
                user_id = f"anon_{session_id}"
        
        logger.info(f"دریافت پیام (Django Template) - User: {user_id}, Message: {user_message[:100]}...")
        
        response = agent_engine.run(user_message, session_id, user_id)
        
        return JsonResponse({
            'success': True,
            'response': response,
            'user_message': user_message,
            'user_id': user_id,
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"خطا در پردازش پیام (Django Template): {e}")
        return JsonResponse({
            'success': False,
            'error': 'خطا در پردازش درخواست'
        })



@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    """API چت که با فرمت OpenAI و احراز هویت Supabase سازگار است"""
    try:
        # 1. استخراج و اعتبارسنجی توکن JWT از هدر
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({'error': 'Authorization token required'}, status=401)

        token = auth_header.split(' ')[1]
        try:
            # اعتبارسنجی توکن با استفاده از JWT Secret
            decoded_token = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"])
            user_id = decoded_token.get('sub') # 'sub' معمولاً شناسه کاربر است
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token has expired'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        # 2. دریافت و پارس کردن درخواست در فرمت OpenAI
        data = json.loads(request.body)
        openai_messages = data.get('messages', [])
        
        user_message = ""
        if openai_messages and openai_messages[-1].get('role') == 'user':
            user_message = openai_messages[-1].get('content', '').strip()

        if not user_message:
            return JsonResponse({'error': 'No user message found'}, status=400)

        # 3. استفاده از user_id استخراج شده از توکن
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        logger.info(f"دریافت پیام (Secure) - User: {user_id}, Message: {user_message[:100]}...")
        
        # 4. فراخوانی منطق اصلی چت‌بات شما
        response_text = agent_engine.run(user_message, session_id, user_id)
        
        # 5. ساخت پاسخ در فرمت استاندارد OpenAI
        openai_format_response = {
            "id": f"chatcmpl-{uuid.uuid4()}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "custom-agent-model",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }
            ]
        }
        
        return JsonResponse(openai_format_response)
        
    except Exception as e:
        logger.error(f"خطا در پردازش پیام امن: {e}")
        return JsonResponse({'error': 'خطا در پردازش درخواست'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def upload_document(request):
    """آپلود سند با پشتیبانی از multi-user - نسخه هوشمند"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'success': False, 'error': 'فایلی انتخاب نشده است'})
        
        uploaded_file = request.FILES['file']
        user_id = request.POST.get('user_id', 'default')
        
        file_name = uploaded_file.name.lower()
        if not (file_name.endswith('.xlsx') or file_name.endswith('.xls')):
            return JsonResponse({
                'success': False, 
                'error': 'فقط فایل‌های Excel (xlsx, xls) پشتیبانی می‌شوند'
            })
        
        logger.info(f"آپلود هوشمند فایل Excel: {uploaded_file.name}")
        
        dataframe = data_manager.process_accounting_file(user_id, uploaded_file, uploaded_file.name)
        
        summary = data_manager.get_accounting_summary(user_id)
        mapping_history = data_manager.get_mapping_history(user_id)
        latest_mapping = mapping_history[-1] if mapping_history else {}
        
        mapping_result = latest_mapping.get('mapping_result', {})
        original_columns = list(mapping_result.get('mapping', {}).keys())
        
        response_data = {
            'success': True,
            'message': f'فایل با موفقیت پردازش شد. سیستم به صورت هوشمند ستون‌ها را تشخیص داد.',
            'user_id': user_id,
            'mapping_info': {
                'confidence': mapping_result.get('confidence', 'unknown'),
                'original_columns': original_columns,
                'mapped_columns': list(dataframe.columns),
                'notes': mapping_result.get('notes', '')
            },
            'dataframe_info': {
                'rows': len(dataframe),
                'columns': list(dataframe.columns),
                'total_debit': summary.get('financial_totals', {}).get('total_debit', 0),
                'total_credit': summary.get('financial_totals', {}).get('total_credit', 0),
            },
            'summary': summary
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"خطا در آپلود هوشمند سند: {e}")
        return JsonResponse({
            'success': False,
            'error': f'خطا در پردازش فایل: {str(e)}'
        })

@require_http_methods(["GET"])
def get_system_info(request):
    """دریافت اطلاعات سیستم"""
    try:
        logger.info("دریافت درخواست اطلاعات سیستم")
        
        rag_info = rag_engine.get_collection_info()
        tools_info = agent_engine.get_available_tools()
        system_status = agent_engine.get_system_status()
        
        response_data = {
            'success': True,
            'rag_info': rag_info,
            'available_tools': tools_info,
            'system_status': system_status,
            'timestamp': str(datetime.now()) # FIX: ساده‌سازی
        }
        
        logger.info(f"اطلاعات سیستم آماده - RAG Docs: {rag_info.get('total_documents', 0)}")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"خطا در دریافت اطلاعات سیستم: {e}")
        return JsonResponse({
            'success': False,
            'error': 'خطا در دریافت اطلاعات سیستم'
        })

@csrf_exempt
@require_http_methods(["POST"])
def clear_chat(request):
    """پاک کردن تاریخچه چت"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', 'default')
        
        logger.info(f"درخواست پاک کردن تاریخچه - Session: {session_id}")
        
        success = agent_engine.clear_memory(session_id)
        
        if success:
            logger.info(f"تاریخچه چت برای session {session_id} پاک شد")
            return JsonResponse({
                'success': True,
                'message': 'تاریخچه چت پاک شد'
            })
        else:
            logger.error(f"خطا در پاک کردن تاریخچه برای session {session_id}")
            return JsonResponse({
                'success': False,
                'error': 'خطا در پاک کردن تاریخچه'
            })
        
    except json.JSONDecodeError as e:
        logger.error(f"خطای JSON در پاک کردن چت: {e}")
        return JsonResponse({
            'success': False,
            'error': 'فرمت داده ارسالی نامعتبر است'
        })
    except Exception as e:
        logger.error(f"خطا در پاک کردن چت: {e}")
        return JsonResponse({
            'success': False,
            'error': 'خطا در پاک کردن تاریخچه'
        })

@csrf_exempt
@require_http_methods(["POST"])
def create_new_session(request):
    """ایجاد session جدید"""
    try:
        new_session_id = f"session_{uuid.uuid4().hex[:10]}"
        
        logger.info(f"ایجاد session جدید: {new_session_id}")
        
        return JsonResponse({
            'success': True,
            'session_id': new_session_id,
            'message': 'Session جدید ایجاد شد'
        })
        
    except Exception as e:
        logger.error(f"خطا در ایجاد session جدید: {e}")
        return JsonResponse({
            'success': False,
            'error': 'خطا در ایجاد session جدید'
        })

@require_http_methods(["GET"])
def get_session_info(request):
    """دریافت اطلاعات session"""
    try:
        session_id = request.GET.get('session_id', 'default')
        
        history = agent_engine.memory.get_conversation_history(session_id)
        context_summary = agent_engine.memory.get_context_summary(session_id)
        
        response_data = {
            'success': True,
            'session_id': session_id,
            'message_count': len(history),
            'context_summary': context_summary,
            'has_session': session_id in agent_engine.memory.active_sessions
        }
        
        logger.info(f"اطلاعات session {session_id} - Messages: {len(history)}")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"خطا در دریافت اطلاعات session: {e}")
        return JsonResponse({
            'success': False,
            'error': 'خطا در دریافت اطلاعات session'
        })

def handler404(request, exception):
    return JsonResponse({
        'success': False,
        'error': 'صفحه مورد نظر یافت نشد'
    }, status=404)

def handler500(request):
    return JsonResponse({
        'success': False,
        'error': 'خطای داخلی سرور'
    }, status=500)

# REMOVED: Duplicate and incorrectly indented functions
# REMOVED: validate_accounting_csv, debug_system, get_tool_code

# تعریف صحیح توابع در انتهای فایل
@require_http_methods(["GET"])
def debug_system(request):
    """صفحه دیباگ سیستم"""
    try:
        user_id = request.GET.get('user_id', 'default')
        
        data_status = agent_engine.debug_user_data(user_id)
        
        dynamic_tools = []
        if hasattr(agent_engine, 'dynamic_manager') and agent_engine.dynamic_manager:
            try:
                dynamic_tools = agent_engine.dynamic_manager.get_all_tools()
            except Exception as e:
                logger.error(f"خطا در دریافت ابزارهای داینامیک: {e}")
        
        response_data = {
            'success': True,
            'data_status': data_status,
            'dynamic_tools_count': len(dynamic_tools),
            'dynamic_tools': [
                {
                    'tool_id': tool.tool_id,
                    'name': tool.name,
                    'description': tool.description,
                    'usage_count': tool.usage_count,
                    'parameters': [param.dict() for param in tool.parameters]
                }
                for tool in dynamic_tools
            ],
            'static_tools': agent_engine.get_available_tools()
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"خطا در دیباگ سیستم: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_http_methods(["GET"]) 
def get_tool_code(request):
    """دریافت کد یک ابزار داینامیک"""
    try:
        tool_id = request.GET.get('tool_id')
        
        if not tool_id or not hasattr(agent_engine, 'dynamic_manager') or not agent_engine.dynamic_manager:
            return JsonResponse({'success': False, 'error': 'ابزار پیدا نشد'})
        
        code = agent_engine.dynamic_manager.get_tool_code(tool_id)
        
        if code:
            return JsonResponse({
                'success': True,
                'tool_id': tool_id,
                'code': code
            })
        else:
            return JsonResponse({'success': False, 'error': 'کد ابزار پیدا نشد'})
            
    except Exception as e:
        logger.error(f"خطا در دریافت کد ابزار: {e}")
        return JsonResponse({'success': False, 'error': str(e)})            

def about(request):
    return render(request, 'assistant/about.html')    

def docs(request):
    return render(request, 'assistant/docs.html')        