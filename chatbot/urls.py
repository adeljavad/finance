# chatbot/urls.py (فایل اصلی پروژه)
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('users/', include('users.urls')),
    # صفحه اصلی
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('assistant/', include('assistant.urls')),
    # path('pages/', include('pages.urls')),
    # path('ai/', include('financial_ai_core.urls')),  # موقتاً غیرفعال به دلیل مشکل import
    
    # ✨ این خط را اضافه کنید - مسیر financial_system
    path('financial/', include('financial_system.urls', namespace='financial_system')),
    
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
