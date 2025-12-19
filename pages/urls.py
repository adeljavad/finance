from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('upload-page/', views.upload_page, name='upload_page'),
    path('tools-page/', views.tools_page, name='tools_page'),
    path('status-page/', views.status_page, name='status_page'),
    path('history-page/', views.history_page, name='history_page'),
    path('api/chat-history/', views.get_chat_history_api, name='chat_history_api'),
]
