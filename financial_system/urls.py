# financial_system/urls.py
from django.urls import path
from . import views
from .views.advanced_financial_chat import advanced_chat_interface, AdvancedFinancialChatView
from .views.financial_chat import FinancialChatView

app_name = 'financial_system'

urlpatterns = [
    # چت بات اصلی
    path('', views.FinancialChatView.as_view(), name='dashboard'),
    
    # گزارش‌ها
    path('reports/', views.FinancialChatView.as_view(), name='reports'),
    
    # چت بات
    path('chat/', views.FinancialChatView.as_view(), name='financial_chatbot'),
    path('api/chat/', views.FinancialChatView.as_view(), name='financial_chat_api'),
    
    # گزارش تراز آزمایشی
    path('reports/trial_balance/', views.trial_balance_report, name='trial_balance'),
    path('api/trial_balance/', views.trial_balance_api, name='trial_balance_api'),
    path('reports/trial_balance/export/', views.export_trial_balance, name='export_trial_balance'),
    
    # چت بات پیشرفته - سیستم جدید
    path('advanced-chat/', advanced_chat_interface, name='advanced_chat'),
    path('api/advanced-chat/', AdvancedFinancialChatView.as_view(), name='advanced_chat_api'),
    path("api/financial-chat/", FinancialChatView.as_view()),

]
