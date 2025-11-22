# data_importer/urls.py
from django.urls import path
from . import views

app_name = 'data_importer'

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
    
    # گزارش‌ها (فعلاً غیرفعال)
    # path('audit-report/', views.audit_report, name='audit_report'),
]
