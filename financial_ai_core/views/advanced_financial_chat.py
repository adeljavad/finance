# financial_system/views/advanced_financial_chat.py
"""
ویوی پیشرفته چت مالی با استفاده از سیستم جدید
"""

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json

from ..agents.advanced_financial_agent_complete import ask_financial_question_complete_sync

def advanced_chat_interface(request):
    """نمایش رابط کاربری چت پیشرفته"""
    return render(request, 'financial_system/advanced_chat_interface.html')

@method_decorator(csrf_exempt, name='dispatch')
class AdvancedFinancialChatView(View):
    """ویوی پیشرفته چت مالی با قابلیت پاسخ به سوالات عمومی مالی"""
    
    def post(self, request):
        """دریافت سوال و ارسال به سیستم پیشرفته"""
        try:
            data = json.loads(request.body)
            question = data.get('question', '')
            company_id = data.get('company_id', 1)
            period_id = data.get('period_id', 1)
            
            if not question:
                return JsonResponse({
                    'success': False,
                    'error': 'سوال الزامی است'
                }, status=400)
            
            # ارسال سوال به سیستم پیشرفته
            user_id = f"user_{request.user.id}" if request.user.is_authenticated else "anonymous_user"
            response = ask_financial_question_complete_sync(
                question=question,
                user_id=user_id,
                company_id=company_id,
                period_id=period_id
            )
            
            return JsonResponse(response)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'خطا در پردازش سوال: {str(e)}'
            }, status=500)
    
    def get(self, request):
        """نمایش اطلاعات سیستم"""
        return JsonResponse({
            'success': True,
            'system_info': {
                'name': 'دستیار مالی پیشرفته',
                'version': '2.0.0',
                'capabilities': [
                    'پاسخ به سوالات عمومی مالی و حسابداری',
                    'تحلیل نسبت‌های مالی پیشرفته',
                    'تولید گزارش‌های مالی',
                    'شناسایی انحرافات مالی',
                    'مشاوره مالیاتی و قوانین مالی',
                    'تحلیل ریسک‌های مالی'
                ],
                'supported_domains': [
                    'حسابداری و استانداردها',
                    'مالیات و قوانین مالی',
                    'تحلیل‌های مالی',
                    'حسابرسی و کنترل',
                    'مشاوره مالی'
                ]
            }
        })
