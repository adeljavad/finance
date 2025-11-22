# users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('company/select/', views.company_selection, name='company_selection'),
    path('company/set/<int:company_id>/', views.set_current_company, name='set_current_company'),
    path('company/<int:company_id>/members/', views.manage_company_members, name='manage_company_members'),
    path('invitation/accept/<str:token>/', views.accept_invitation, name='accept_invitation'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('auth-status/', views.check_auth_status, name='auth_status'),  # برای دیباگ
    
    # شرکت‌ها - تسک ۳۰۶
    path('company/create/', views.create_company, name='create_company'),
    path('company/list/', views.company_list, name='company_list'),
    path('company/<int:company_id>/', views.company_detail, name='company_detail'),
    path('company/<int:company_id>/update/', views.update_company, name='update_company'),
    path('company/<int:company_id>/financial-period/create/', views.create_financial_period, name='create_financial_period'),

]
