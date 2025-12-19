from django.urls import path
from . import views

app_name = 'assistant'

urlpatterns = [
    path('', views.home, name='home'),
    
    
    path('api/chat_django/', views.chat_api_django, name='chat_api_django'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/upload/', views.upload_document, name='upload_document'),
    path('api/system-info/', views.get_system_info, name='system_info'),
    path('api/clear-chat/', views.clear_chat, name='clear_chat'),
    path('api/new-session/', views.create_new_session, name='new_session'),
    path('api/session-info/', views.get_session_info, name='session_info'),
    path('debug/', views.debug_system, name='debug_system'),
    path('tool-code/', views.get_tool_code, name='tool_code'),
    path('about/', views.about, name='about'),  # این خط را اضافه کنید
    path('docs/', views.docs, name='docs'),
    # path('contact/', views.contact, name='contact'),
]