from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import uuid

from .services.agent_engine import AgentEngine
from .services.rag_engine import StableRAGEngine
from .services.data_manager import UserDataManager
from .services.data_importer_wrapper import DataImporterWrapper

logger = logging.getLogger(__name__)

# Initialize services with error handling
try:
    agent_engine = AgentEngine()
    logger.info("✅ AgentEngine initialized in views")
except Exception as e:
    logger.error(f"❌ Failed to initialize AgentEngine: {e}")
    agent_engine = None

try:
    rag_engine = StableRAGEngine()
    logger.info("✅ RAGEngine initialized in views")
except Exception as e:
    logger.error(f"❌ Failed to initialize RAGEngine: {e}")
    rag_engine = None

try:
    data_manager = UserDataManager()
    logger.info("✅ DataManager initialized in views")
except Exception as e:
    logger.error(f"❌ Failed to initialize DataManager: {e}")
    data_manager = None

try:
    data_importer_wrapper = DataImporterWrapper()
    logger.info("✅ DataImporterWrapper initialized in views")
except Exception as e:
    logger.error(f"❌ Failed to initialize DataImporterWrapper: {e}")
    data_importer_wrapper = None

def home(request):
    """صفحه اصلی چت با مدیریت خطا"""
    try:
        session_id = request.GET.get('session_id')
        
        if not session_id:
            # ایجاد session_id جدید
            session_id = request.session.session_key or str(uuid.uuid4())
            if not request.session.session_key:
                request.session.create()
                session_id = request.session.session_key
        
        logger.info(f"🏠 Home page - Session: {session_id}")
        
        context = {
            'session_id': session_id,
            'agent_available': agent_engine is not None,
            'data_manager_available': data_manager is not None
        }
        
        return render(request, 'assistant/chat.html', context)
        
    except Exception as e:
        logger.error(f"❌ Error in home view: {e}")
        # بازگردانی صفحه اصلی با مقادیر پیش‌فرض
        context = {
            'session_id': str(uuid.uuid4()),
            'agent_available': False,
            'data_manager_available': False,
            'error': 'خطا در بارگذاری سیستم'
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
        
        logger.info(f"💬 Chat request (Django Template) - User: {user_id}, Message: {user_message[:100]}...")
        
        if not agent_engine:
            return JsonResponse({
                'success': False,
                'error': 'سرویس هوش مصنوعی در حال حاضر در دسترس نیست'
            }, status=503)
        
        response = agent_engine.run(user_message, session_id, user_id)
        
        return JsonResponse({
            'success': True,
            'response': response,
            'user_message': user_message,
            'user_id': user_id,
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"❌ Error in chat_api_django: {e}")
        return JsonResponse({
            'success': False,
            'error': 'خطا در پردازش درخواست'
        })

@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    """API چت با مدیریت خطا و debugging بهبود یافته"""
    try:
        # پردازش JSON request
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error(f"❌ Invalid JSON in request body: {request.body}")
            return JsonResponse({
                'success': False,
                'error': 'فرمت JSON نامعتبر است',
                'details': 'متن پیام باید در قالب JSON ارسال شود'
            }, status=400)
        
        user_message = data.get('user_message', '').strip()
        session_id = data.get('session_id', '').strip()
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'پیام کاربر خالی است'
            }, status=400)
            
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'شناسه جلسه الزامی است'
            }, status=400)
        
        # تعیین user_id با منطق بهبود یافته
        if request.user.is_authenticated:
            user_id = str(request.user.id)
            user_type = 'authenticated'
        else:
            # برای کاربران ناشناس، از session_id به عنوان user_id استفاده می‌کنیم
            user_id = session_id
            user_type = 'anonymous'
        
        logger.info(f"💬 Chat request - Session: {session_id}, User ID: {user_id}, Type: {user_type}")
        logger.info(f"💬 User message: {user_message[:100]}...")
        
        # بررسی دسترسی به agent
        if not agent_engine:
            logger.error("❌ Agent engine not available")
            return JsonResponse({
                'success': False,
                'error': 'سرویس هوش مصنوعی در حال حاضر در دسترس نیست',
                'session_id': session_id,
                'user_id': user_id
            }, status=503)
        
        # اجرای agent
        try:
            result = agent_engine.run(user_message, session_id, user_id)
            
            # لاگ کردن نتیجه
            if result.get('success'):
                logger.info(f"✅ Chat processed successfully - Type: {result.get('query_type', 'unknown')}")
                logger.info(f"📊 Tools used: {result.get('tools_used', [])}")
                logger.info(f"📁 Has data: {result.get('has_data', False)}")
            else:
                logger.error(f"❌ Chat processing failed: {result.get('error', 'Unknown error')}")
            
            # اضافه کردن اطلاعات debugging
            result['debug_info'] = {
                'session_id': session_id,
                'user_id': user_id,
                'user_type': user_type,
                'agent_available': True,
                'request_timestamp': str(uuid.uuid4())[:8]  # برای tracing
            }
            
            return JsonResponse(result)
            
        except Exception as e:
            logger.error(f"❌ Error in agent execution: {e}")
            return JsonResponse({
                'success': False,
                'error': f'خطا در پردازش پیام: {str(e)}',
                'session_id': session_id,
                'user_id': user_id,
                'debug_info': {
                    'error_type': type(e).__name__,
                    'error_details': str(e)
                }
            }, status=500)
            
    except Exception as e:
        logger.error(f"❌ Unexpected error in chat_api: {e}")
        return JsonResponse({
            'success': False,
            'error': 'خطای غیرمنتظره در سیستم',
            'details': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def upload_document(request):
    """آپلود و پردازش فایل حسابداری با استفاده از data_importer"""
    try:
        logger.info(f"📁 Document upload request received")
        
        # بررسی وجود فایل
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'فایل ارسال نشده است',
                'details': 'لطفاً یک فایل اکسل یا CSV انتخاب کنید'
            }, status=400)
        
        uploaded_file = request.FILES['file']
        filename = uploaded_file.name
        file_size = uploaded_file.size
        
        logger.info(f"📄 File received: {filename} ({file_size} bytes)")
        
        # بررسی نوع فایل
        if not filename.lower().endswith(('.xlsx', '.xls', '.csv')):
            return JsonResponse({
                'success': False,
                'error': 'فرمت فایل پشتیبانی نمی‌شود',
                'details': 'فقط فایل‌های Excel (.xlsx, .xls) و CSV مجاز هستند'
            }, status=400)
        
        # بررسی اندازه فایل (حداکثر 50MB)
        if file_size > 50 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'فایل بسیار بزرگ است',
                'details': 'حداکثر اندازه فایل 50 مگابایت است'
            }, status=400)
        
        # دریافت user_id از POST data یا استفاده از session
        try:
            post_data = json.loads(request.body) if request.body else {}
        except:
            post_data = {}
        
        user_id = post_data.get('user_id', '').strip()
        session_id = post_data.get('session_id', '').strip()
        
        if not user_id and session_id:
            # از session_id به عنوان user_id استفاده می‌کنیم
            user_id = session_id
        elif not user_id:
            user_id = str(uuid.uuid4())
        
        logger.info(f"🔍 Upload processing - User: {user_id}, Session: {session_id}")
        
        # استفاده مستقیم از data_manager (به دلیل مشکلات data_importer)
        if not data_manager:
            return JsonResponse({
                'success': False,
                'error': 'سرویس پردازش فایل در دسترس نیست'
            }, status=503)
        
        logger.info("🔄 Using data_manager for file processing")
        return _upload_with_data_manager(request, uploaded_file, filename, file_size, user_id, session_id)
            
    except Exception as e:
        logger.error(f"❌ Unexpected error in upload: {e}")
        return JsonResponse({
            'success': False,
            'error': 'خطای غیرمنتظره در آپلود فایل',
            'details': str(e)
        }, status=500)

def _upload_with_data_manager(request, uploaded_file, filename, file_size, user_id, session_id):
    """آپلود با استفاده از data_manager قدیمی (fallback)"""
    try:
        # خواندن محتوای فایل
        if filename.lower().endswith('.csv'):
            file_content = uploaded_file.read().decode('utf-8')
        else:
            file_content = uploaded_file.read()
        
        # پردازش فایل
        dataframe = data_manager.process_accounting_file(user_id, file_content, filename)
        
        # دریافت خلاصه داده‌ها
        summary = data_manager.get_accounting_summary(user_id)
        mapping_history = data_manager.get_mapping_history(user_id)
        
        # آماده‌سازی پاسخ
        response_data = {
            'success': True,
            'message': f'فایل {filename} با موفقیت پردازش شد (با data_manager قدیمی)',
            'user_id': user_id,
            'session_id': session_id,
            'filename': filename,
            'file_size': file_size,
            'dataframe_info': {
                'rows': len(dataframe),
                'columns': list(dataframe.columns)
            },
            'mapping_info': {
                'confidence': 'high',
                'original_columns': list(dataframe.columns),
                'mapped_columns': list(dataframe.columns),
                'notes': 'Columns detected and mapped successfully'
            },
            'summary': summary,
            'has_data': summary.get('has_data', False)
        }
        
        # اضافه کردن mapping_history اگر موجود باشد
        if mapping_history:
            response_data['mapping_history'] = mapping_history[-1]
        
        logger.info(f"✅ File processed successfully with data_manager - Rows: {len(dataframe)}, Columns: {len(dataframe.columns)}")
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"❌ Error processing file with data_manager: {e}")
        return JsonResponse({
            'success': False,
            'error': f'خطا در پردازش فایل: {str(e)}',
            'details': 'لطفاً مطمئن شوید که فایل حاوی ستون‌های مورد نیاز است',
            'filename': filename
        }, status=500)

@require_http_methods(["GET"])
def get_system_info(request):
    """دریافت اطلاعات سیستم با مدیریت خطا"""
    try:
        logger.info("🔧 System info request received")
        
        # جمع‌آوری اطلاعات سیستم
        system_info = {
            'success': True,
            'timestamp': str(uuid.uuid4())[:8],
            'components': {}
        }
        
        # RAG Information
        if rag_engine:
            try:
                rag_info = rag_engine.get_collection_info()
                system_info['components']['rag'] = rag_info
            except Exception as e:
                system_info['components']['rag'] = {'error': str(e)}
        else:
            system_info['components']['rag'] = {'status': 'unavailable'}
        
        # Tools Information
        if agent_engine:
            try:
                tools_info = agent_engine.get_available_tools()
                system_info['components']['tools'] = tools_info
            except Exception as e:
                system_info['components']['tools'] = {'error': str(e)}
        else:
            system_info['components']['tools'] = {'status': 'unavailable'}
        
        # System Status
        if agent_engine:
            try:
                system_status = agent_engine.get_system_status()
                system_info['components']['status'] = system_status
            except Exception as e:
                system_info['components']['status'] = {'error': str(e)}
        else:
            system_info['components']['status'] = {'status': 'unavailable'}
        
        # Data Manager Status
        if data_manager:
            try:
                # Simple data manager status check
                system_info['components']['data_manager'] = {
                    'status': 'active',
                    'storage_type': 'redis_with_fallback'
                }
            except Exception as e:
                system_info['components']['data_manager'] = {'error': str(e)}
        else:
            system_info['components']['data_manager'] = {'status': 'unavailable'}
        
        logger.info("✅ System info retrieved successfully")
        return JsonResponse(system_info)
        
    except Exception as e:
        logger.error(f"❌ Error in get_system_info: {e}")
        return JsonResponse({
            'success': False,
            'error': 'خطا در دریافت اطلاعات سیستم',
            'details': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def clear_chat(request):
    """پاک کردن تاریخچه چت"""
    try:
        # پردازش JSON request
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id', '').strip()
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'فرمت JSON نامعتبر است'
            }, status=400)
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'شناسه جلسه الزامی است'
            }, status=400)
        
        # پاک کردن حافظه
        if agent_engine:
            success = agent_engine.clear_memory(session_id)
            if success:
                logger.info(f"🗑️ Chat cleared for session: {session_id}")
                return JsonResponse({
                    'success': True,
                    'message': 'تاریخچه چت پاک شد',
                    'session_id': session_id
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'خطا در پاک کردن تاریخچه'
                }, status=500)
        else:
            return JsonResponse({
                'success': False,
                'error': 'سرویس حافظه در دسترس نیست'
            }, status=503)
            
    except Exception as e:
        logger.error(f"❌ Error in clear_chat: {e}")
        return JsonResponse({
            'success': False,
            'error': 'خطا در پاک کردن چت',
            'details': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def create_new_session(request):
    """ایجاد جلسه جدید"""
    try:
        new_session_id = str(uuid.uuid4())
        
        logger.info(f"🆕 New session created: {new_session_id}")
        
        return JsonResponse({
            'success': True,
            'session_id': new_session_id,
            'message': 'جلسه جدید ایجاد شد'
        })
        
    except Exception as e:
        logger.error(f"❌ Error creating new session: {e}")
        return JsonResponse({
            'success': False,
            'error': 'خطا در ایجاد جلسه جدید',
            'details': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_session_info(request):
    """دریافت اطلاعات جلسه"""
    try:
        session_id = request.GET.get('session_id', '').strip()
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'شناسه جلسه الزامی است'
            }, status=400)
        
        # دریافت تاریخچه مکالمه
        history = []
        context_summary = ""
        
        if agent_engine and agent_engine.memory:
            try:
                history = agent_engine.memory.get_conversation_history(session_id, last_n=10)
                context_summary = agent_engine.memory.get_context_summary(session_id)
            except Exception as e:
                logger.warning(f"⚠️ Error getting memory data: {e}")
        
        # دریافت اطلاعات داده کاربر
        user_dataframes = {}
        user_files = []
        
        if data_manager and agent_engine:
            try:
                # از session_id به عنوان user_id استفاده می‌کنیم
                user_id = session_id
                user_dataframes = data_manager.get_user_dataframes_info(user_id)
                user_files = data_manager.get_uploaded_files_info(user_id)
            except Exception as e:
                logger.warning(f"⚠️ Error getting user data: {e}")
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'conversation_history': history,
            'context_summary': context_summary,
            'message_count': len(history),
            'has_data': len(user_dataframes) > 0,
            'dataframes': user_dataframes,
            'uploaded_files': user_files,
            'session_active': len(history) > 0
        })
        
    except Exception as e:
        logger.error(f"❌ Error in get_session_info: {e}")
        return JsonResponse({
            'success': False,
            'error': 'خطا در دریافت اطلاعات جلسه',
            'details': str(e)
        }, status=500)

@require_http_methods(["GET"])
def debug_system(request):
    """صفحه دیباگ سیستم با اطلاعات کامل"""
    try:
        user_id = request.GET.get('user_id', '').strip()
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'شناسه کاربر الزامی است'
            }, status=400)
        
        debug_data = {
            'success': True,
            'user_id': user_id,
            'system_status': {}
        }
        
        # Agent status
        if agent_engine:
            try:
                debug_data['system_status']['agent'] = agent_engine.get_system_status()
            except Exception as e:
                debug_data['system_status']['agent'] = {'error': str(e)}
        else:
            debug_data['system_status']['agent'] = {'status': 'unavailable'}
        
        # User data debug
        if data_manager:
            try:
                debug_data['user_data'] = data_manager.debug_user_data(user_id)
            except Exception as e:
                debug_data['user_data'] = {'error': str(e)}
        else:
            debug_data['user_data'] = {'status': 'unavailable'}
        
        # Dynamic tools (if available)
        if agent_engine and agent_engine.dynamic_manager:
            try:
                dynamic_tools = agent_engine.dynamic_manager.get_all_tools()
                debug_data['dynamic_tools'] = {
                    'count': len(dynamic_tools),
                    'tools': [{'id': str(tool.metadata.get('tool_id', 'unknown')), 'name': tool.name} for tool in dynamic_tools]
                }
            except Exception as e:
                debug_data['dynamic_tools'] = {'error': str(e)}
        else:
            debug_data['dynamic_tools'] = {'status': 'unavailable'}
        
        return JsonResponse(debug_data)
        
    except Exception as e:
        logger.error(f"❌ Error in debug_system: {e}")
        return JsonResponse({
            'success': False,
            'error': 'خطا در دیباگ سیستم',
            'details': str(e)
        }, status=500)

@require_http_methods(["GET"])
def get_tool_code(request):
    """دریافت کد ابزار داینامیک"""
    try:
        tool_id = request.GET.get('tool_id', '').strip()
        
        if not tool_id:
            return JsonResponse({
                'success': False,
                'error': 'شناسه ابزار الزامی است'
            }, status=400)
        
        if agent_engine and agent_engine.dynamic_manager:
            try:
                tool_code = agent_engine.dynamic_manager.get_tool_code(tool_id)
                if tool_code:
                    return JsonResponse({
                        'success': True,
                        'tool_id': tool_id,
                        'code': tool_code
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'ابزار پیدا نشد'
                    }, status=404)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'خطا در دریافت کد ابزار: {str(e)}'
                }, status=500)
        else:
            return JsonResponse({
                'success': False,
                'error': 'مدیریت ابزارهای داینامیک در دسترس نیست'
            }, status=503)
            
    except Exception as e:
        logger.error(f"❌ Error in get_tool_code: {e}")
        return JsonResponse({
            'success': False,
            'error': 'خطای غیرمنتظره در دریافت کد ابزار',
            'details': str(e)
        }, status=500)

def about(request):
    """صفحه درباره"""
    try:
        return render(request, 'assistant/about.html')
    except Exception as e:
        logger.error(f"❌ Error in about page: {e}")
        return JsonResponse({'error': 'خطا در بارگذاری صفحه درباره'})

def docs(request):
    """صفحه مستندات"""
    try:
        return render(request, 'assistant/docs.html')
    except Exception as e:
        logger.error(f"❌ Error in docs page: {e}")
        return JsonResponse({'error': 'خطا در بارگذاری صفحه مستندات'})

def chat_old(request):
    """صفحه چت قدیمی"""
    try:
        session_id = request.GET.get('session_id')
        
        if not session_id:
            # ایجاد session_id جدید
            session_id = request.session.session_key or str(uuid.uuid4())
            if not request.session.session_key:
                request.session.create()
                session_id = request.session.session_key
        
        logger.info(f"🏠 Chat Old page - Session: {session_id}")
        
        context = {
            'session_id': session_id,
            'agent_available': agent_engine is not None,
            'data_manager_available': data_manager is not None
        }
        
        return render(request, 'assistant/chat_old.html', context)
        
    except Exception as e:
        logger.error(f"❌ Error in chat_old view: {e}")
        context = {
            'session_id': str(uuid.uuid4()),
            'agent_available': False,
            'data_manager_available': False,
            'error': 'خطا در بارگذاری سیستم'
        }
        return render(request, 'assistant/chat_old.html', context)

def chat_mini(request):
    """صفحه چت مینی"""
    try:
        session_id = request.GET.get('session_id')
        
        if not session_id:
            # ایجاد session_id جدید
            session_id = request.session.session_key or str(uuid.uuid4())
            if not request.session.session_key:
                request.session.create()
                session_id = request.session.session_key
        
        logger.info(f"🏠 Chat Mini page - Session: {session_id}")
        
        context = {
            'session_id': session_id,
            'agent_available': agent_engine is not None,
            'data_manager_available': data_manager is not None
        }
        
        return render(request, 'assistant/chat_mini.html', context)
        
    except Exception as e:
        logger.error(f"❌ Error in chat_mini view: {e}")
        context = {
            'session_id': str(uuid.uuid4()),
            'agent_available': False,
            'data_manager_available': False,
            'error': 'خطا در بارگذاری سیستم'
        }
        return render(request, 'assistant/chat_mini.html', context)

# Error Handlers
def handler404(request, exception):
    """404 Error Handler"""
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'صفحه مورد نظر یافت نشد',
            'status': 404,
            'path': request.path
        }, status=404)
    
    return render(request, 'assistant/404.html', status=404)

def handler500(request):
    """500 Error Handler"""
    if request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'خطای داخلی سرور',
            'status': 500
        }, status=500)
    
    return render(request, 'assistant/500.html', status=500)
