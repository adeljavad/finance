# chatbot/urls.py (فایل اصلی پروژه)
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('users/', include('users.urls')),
    path('financial/', include('financial_system.urls')),
    # صفحه اصلی
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('assistant/', include('assistant.urls')),

    # مسیرهای موجود شما
    # path('chatbot/', views.chatbot_view, name='chatbot'),
    # path('sql_editor/', views.sql_editor, name='sql_editor'),
    # path('home/', views.home, name='home'),
    # path('chat/<str:query>/', views.chat, name='chat'),
    # path('send_message/', views.send_message, name='send_message'),
    # path('view1/', views.view1, name='view1'),
    # path('view2/', views.view2, name='view2'),
    # path('view_tablecolumn/', views.view_tablecolumn, name='view_tablecolumn'),
    # path('view_table_description/', views.view_table_description, name='view_table_description'),
    # path('select_model/', views.select_model, name='select_model'),
    # path('tblApp/', include('tblApp.urls')),
    # path('login/', views.login_redirect, name='login_redirect'),
    # path('register/', views.register_redirect, name='register_redirect'),
    
    # ✨ این خط را اضافه کنید - مسیر financial_system
    # path('financial/', include('financial_system.urls', namespace='financial_system')),
    
    # ✨ اضافه کردن مسیر data_importer
    path('data-importer/', include('data_importer.urls', namespace='data_importer')),
    # path('api/risk-matrix/', views.risk_levels_matrix, name='risk-levelsmatrix'),
    # path('api/generate-action/', views.generate_action, name='generate-action'),
    # path('api/set-action-value/', views.set_action_value, name='set-action-value'),
    # path('api/remove-action/', views.remove_action, name='remove-action'),
    # path('api/get-risk-impactful-action-queue/', views.get_risk_impactful_action_queue, name='get-risk-impactful-action-queue'),
    # path('test/generate/', views.test_generate, name='test_generate'),
    # path('test/set-value/', views.test_set_value, name='test_set_value'),
    # path('test/remove/', views.test_remove, name='test_remove'),
    # path('test/get-risk/', views.test_get_risk, name='test_get_risk'),
 
]
