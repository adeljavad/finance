# financial_system/views/financial_chat.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render
from ..agents.financial_agent import FinancialAgent
import json

@method_decorator(csrf_exempt, name='dispatch')
class FinancialChatView(View):
    def __init__(self):
        self.agent = FinancialAgent()
    
    def get(self, request):
        """نمایش رابط چت مالی"""
        # دریافت شرکت و دوره جاری از سشن
        company_id = request.session.get('current_company_id')
        period_id = request.session.get('current_period_id')
        
        company = None
        period = None
        
        # در صورت وجود، اطلاعات شرکت و دوره را دریافت کن
        if company_id:
            try:
                from users.models import Company, FinancialPeriod
                company = Company.objects.get(id=company_id)
                if period_id:
                    period = FinancialPeriod.objects.filter(id=period_id, company=company).first()
            except Exception:
                # در صورت خطا، از مقادیر پیش‌فرض استفاده کن
                pass
        
        return render(request, 'financial_system/chatbot.html', {
            'company': company,
            'period': period,
            'title': 'دستیار مالی هوشمند'
        })
    
    def post(self, request):
        """دریافت سوال مالی و ارسال به agent"""
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
            
            # ارسال سوال به agent
            response = self.agent.ask_financial_question(question, company_id, period_id)
            
            # برگرداندن پاسخ به صورت JSON
            return JsonResponse(response)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
