# data_importer/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import FinancialFileViewSet, ImportJobViewSet, DataImporterAPIView
from .api_views.flexible_upload import FlexibleFileUploadView, AnalyzeOnlyView

app_name = 'data_importer'

# Create router for API views
router = DefaultRouter()
router.register(r'api/files', FinancialFileViewSet, basename='financialfile')
router.register(r'api/jobs', ImportJobViewSet, basename='importjob')

urlpatterns = [
    # داشبورد و صفحه اصلی
    path('', views.data_import_dashboard, name='dashboard'),
    
    # آپلود فایل
    path('upload/', views.upload_excel_file, name='upload'),
    
    # پیش‌نمایش و تأیید
    path('preview/<int:file_id>/', views.import_preview, name='preview'),
    path('start-import/<int:file_id>/', views.start_import, name='start_import'),
    
    # مدیریت وضعیت
    path('status/<str:job_id>/', views.import_status, name='status'),
    path('progress/<str:job_id>/', views.get_import_progress, name='get_progress'),
    path('cancel/<str:job_id>/', views.cancel_import, name='cancel'),
    
    # مدیریت فایل‌ها
    path('files/', views.file_list, name='file_list'),
    path('delete/<int:file_id>/', views.delete_file, name='delete_file'),
    
    # پاک کردن کامل داده‌ها
    path('cleanup-all-data/', views.cleanup_all_data, name='cleanup_all_data'),
    
    # استخراج کدینگ
    path('extract-chart-of-accounts/', views.extract_chart_of_accounts, name='extract_chart_of_accounts'),
    
    # API Routes
    path('api/', include(router.urls)),
    path('api/dashboard/', DataImporterAPIView.as_view(), name='api_dashboard'),
    
    # APIهای جدید برای سیستم پیشرفته
    path('api/flexible-upload/', FlexibleFileUploadView.as_view(), name='flexible_upload'),
    path('api/analyze-only/', AnalyzeOnlyView.as_view(), name='analyze_only'),
    
    # گزارش‌ها (فعلاً غیرفعال)
    # path('audit-report/', views.audit_report, name='audit_report'),
]
