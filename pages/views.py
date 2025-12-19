from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import uuid
from datetime import datetime

from assistant.services.agent_engine import AgentEngine
from assistant.services.rag_engine import StableRAGEngine
from assistant.services.data_manager import UserDataManager

logger = logging.getLogger(__name__)

# ایجاد نمونه‌های سراسری
agent_engine = AgentEngine()
rag_engine = StableRAGEngine()
data_manager = UserDataManager()

def upload_page(request):
    """صفحه مستقل آپلود اسناد مالی"""
    session_id = request.GET.get('session_id')
    if not session_id:
        if not request.session.session_key:
            request.session.create()
        session_id = f"session_{request.session.session_key or uuid.uuid4().hex[:10]}"
    
    context = {
        'session_id': session_id,
        'page_title': 'آپلود اسناد مالی',
        'active_page': 'upload'
    }
    return render(request, 'pages/upload_page.html', context)

def tools_page(request):
    """صفحه مستقل ابزارهای تحلیل سریع"""
    session_id = request.GET.get('session_id')
    if not session_id:
        if not request.session.session_key:
            request.session.create()
        session_id = f"session_{request.session.session_key or uuid.uuid4().hex[:10]}"
    
    # دریافت اطلاعات ابزارهای موجود
    try:
        tools_info = agent_engine.get_available_tools()
        # بررسی نوع داده برگشتی
        if isinstance(tools_info, list):
            tools_list = tools_info
        elif isinstance(tools_info, dict):
            tools_list = tools_info.get('tools', [])
        else:
            tools_list = []
    except Exception as e:
        logger.error(f"خطا در دریافت ابزارها: {e}")
        tools_list = []
    
    context = {
        'session_id': session_id,
        'page_title': 'ابزارهای تحلیل مالی',
        'active_page': 'tools',
        'tools': tools_list
    }
    return render(request, 'pages/tools_page.html', context)

def status_page(request):
    """صفحه مستقل وضعیت سیستم"""
    session_id = request.GET.get('session_id')
    if not session_id:
        if not request.session.session_key:
            request.session.create()
        session_id = f"session_{request.session.session_key or uuid.uuid4().hex[:10]}"
    
    # دریافت اطلاعات سیستم
    rag_info = rag_engine.get_collection_info()
    tools_info = agent_engine.get_available_tools()
    system_status = agent_engine.get_system_status()
    
    context = {
        'session_id': session_id,
        'page_title': 'وضعیت سیستم',
        'active_page': 'status',
        'rag_info': rag_info,
        'available_tools': tools_info,
        'system_status': system_status,
        'timestamp': str(datetime.now())
    }
    return render(request, 'pages/status_page.html', context)

def history_page(request):
    """صفحه مستقل تاریخچه چت"""
    session_id = request.GET.get('session_id')
    if not session_id:
        if not request.session.session_key:
            request.session.create()
        session_id = f"session_{request.session.session_key or uuid.uuid4().hex[:10]}"
    
    # بارگذاری تاریخچه از localStorage (در frontend انجام می‌شود)
    context = {
        'session_id': session_id,
        'page_title': 'تاریخچه مکالمات',
        'active_page': 'history'
    }
    return render(request, 'pages/history_page.html', context)

@require_http_methods(["GET"])
def get_chat_history_api(request):
    """API برای دریافت تاریخچه چت"""
    try:
        session_id = request.GET.get('session_id', 'default')
        
        # در اینجا می‌توانید از سیستم memory استفاده کنید
        # فعلاً یک نمونه خالی برمی‌گردانیم
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'history': [],
            'message': 'تاریخچه بارگذاری شد'
        })
        
    except Exception as e:
        logger.error(f"خطا در دریافت تاریخچه: {e}")
        return JsonResponse({
            'success': False,
            'error': 'خطا در دریافت تاریخچه'
        })
