# financial_ai_core/urls.py
from django.urls import path
from .views import openai_compatible_chat

urlpatterns = [
    path('v1/chat/completions/', openai_compatible_chat, name='openai_chat'),
]