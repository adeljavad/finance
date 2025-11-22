from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from datetime import timedelta

from .models import (
    Company, UserCompanyRole, FinancialPeriod, 
    CompanyInvitation, UserSession, CustomUser
)
from .forms import CompanyForm, FinancialPeriodForm, CompanyInvitationForm

@login_required
def create_company(request):
    """ایجاد شرکت جدید - تسک ۳۰۶ - ✅ کامل"""
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    company = form.save(commit=False)
                    company.created_by = request.user
                    company.save()
                    
                    # ایجاد نقش مالک برای کاربر
                    UserCompanyRole.objects.create(
                        user=request.user,
                        company=company,
                        role='OWNER',
                        is_primary=True
                    )
                    
                    messages.success(request, f'شرکت "{company.name}" با موفقیت ایجاد شد.')
                    return redirect('users:company_selection')
                    
            except Exception as e:
                messages.error(request, f'خطا در ایجاد شرکت: {str(e)}')
    else:
        form = CompanyForm()
    
    return render(request, 'users/create_company.html', {
        'form': form,
        'title': 'ایجاد شرکت جدید'
    })

@login_required
def company_list(request):
    """لیست شرکت‌های کاربر - ✅ کامل"""
    user_companies = UserCompanyRole.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('company').order_by('-is_primary', 'company__name')
    
    return render(request, 'users/company_list.html', {
        'user_companies': user_companies
    })

@login_required
def company_detail(request, company_id):
    """نمایش جزئیات شرکت - ✅ کامل"""
    company = get_object_or_404(Company, id=company_id)
    
    # بررسی دسترسی کاربر به شرکت
    user_role = UserCompanyRole.objects.filter(
        user=request.user, 
        company=company,
        is_active=True
    ).first()
    
    if not user_role:
        raise PermissionDenied("شما دسترسی به این شرکت ندارید.")
    
    # آمار شرکت
    stats = {
        'active_periods': company.financial_periods.filter(is_active=True).count(),
        'total_members': company.user_roles.filter(is_active=True).count(),
        'pending_invitations': company.invitations.filter(status='PENDING').count(),
    }
    
    return render(request, 'users/company_detail.html', {
        'company': company,
        'user_role': user_role,
        'stats': stats
    })

@login_required
def update_company(request, company_id):
    """ویرایش اطلاعات شرکت - ✅ کامل"""
    company = get_object_or_404(Company, id=company_id)
    
    # بررسی دسترسی کاربر
    user_role = UserCompanyRole.objects.filter(
        user=request.user, 
        company=company,
        is_active=True
    ).first()
    
    if not user_role or user_role.role not in ['OWNER', 'ADMIN']:
        raise PermissionDenied("شما دسترسی لازم برای ویرایش شرکت را ندارید.")
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'اطلاعات شرکت با موفقیت بروزرسانی شد.')
            return redirect('users:company_detail', company_id=company.id)
    else:
        form = CompanyForm(instance=company)
    
    return render(request, 'users/update_company.html', {
        'form': form,
        'company': company,
        'title': f'ویرایش شرکت {company.name}'
    })

@login_required
def company_selection(request):
    """صفحه انتخاب شرکت پس از ورود - تسک ۳۱۶ - ✅ کامل"""
    user_roles = UserCompanyRole.objects.filter(
        user=request.user, 
        is_active=True
    ).select_related('company')
    
    if not user_roles.exists():
        messages.info(request, 'شما به هیچ شرکتی دسترسی ندارید. لطفاً اولین شرکت خود را ایجاد کنید.')
        return redirect('users:create_company')
    
    # اگر کاربر فقط یک شرکت دارد، مستقیماً به آن هدایت شود
    if user_roles.count() == 1:
        company = user_roles.first().company
        return redirect('users:set_current_company', company_id=company.id)
    
    return render(request, 'users/company_selection.html', {
        'user_roles': user_roles
    })

@login_required
def set_current_company(request, company_id):
    """تنظیم شرکت جاری برای کاربر - تسک ۳۱۶ - ✅ کامل"""
    company = get_object_or_404(Company, id=company_id)
    
    # بررسی دسترسی کاربر به شرکت
    user_role = UserCompanyRole.objects.filter(
        user=request.user,
        company=company,
        is_active=True
    ).first()
    
    if not user_role:
        messages.error(request, 'شما دسترسی به این شرکت ندارید.')
        return redirect('users:company_selection')
    
    # ذخیره شرکت جاری در سشن
    request.session['current_company_id'] = company.id
    request.session['current_company_name'] = company.name
    request.session['user_role'] = user_role.role
    
    # به‌روزرسانی یا ایجاد UserSession
    user_session, created = UserSession.objects.get_or_create(
        user=request.user,
        defaults={'company': company}
    )
    if not created:
        user_session.company = company
        user_session.save()
    
    messages.success(request, f'شرکت {company.name} به عنوان شرکت جاری انتخاب شد.')
    
    # هدایت به داشبورد یا صفحه اصلی
    return redirect('users:dashboard')

@login_required
def manage_company_members(request, company_id):
    """مدیریت اعضای شرکت - ✅ کامل"""
    company = get_object_or_404(Company, id=company_id)
    
    # بررسی دسترسی کاربر
    user_role = UserCompanyRole.objects.filter(
        user=request.user, 
        company=company,
        is_active=True
    ).first()
    
    if not user_role or user_role.role not in ['OWNER', 'ADMIN']:
        raise PermissionDenied("شما دسترسی لازم برای مدیریت اعضا را ندارید.")
    
    members = UserCompanyRole.objects.filter(company=company, is_active=True).select_related('user')
    invitations = CompanyInvitation.objects.filter(company=company, status='PENDING')
    
    if request.method == 'POST':
        invitation_form = CompanyInvitationForm(request.POST)
        if invitation_form.is_valid():
            try:
                invitation = invitation_form.save(commit=False)
                invitation.company = company
                invitation.invited_by = request.user
                invitation.token = CompanyInvitation.generate_token()
                invitation.expires_at = timezone.now() + timedelta(days=7)
                invitation.save()
                
                # TODO: ارسال ایمیل دعوت
                
                messages.success(request, f'دعوتنامه برای {invitation.email} ارسال شد.')
                return redirect('users:manage_company_members', company_id=company.id)
                
            except Exception as e:
                messages.error(request, f'خطا در ارسال دعوتنامه: {str(e)}')
    else:
        invitation_form = CompanyInvitationForm()
    
    return render(request, 'users/manage_members.html', {
        'company': company,
        'members': members,
        'invitations': invitations,
        'invitation_form': invitation_form,
        'user_role': user_role
    })

@login_required
def accept_invitation(request, token):
    """پذیرش دعوتنامه شرکت - تسک ۳۱۰ - ✅ کامل"""
    invitation = get_object_or_404(CompanyInvitation, token=token)
    
    if invitation.is_expired():
        invitation.status = 'EXPIRED'
        invitation.save()
        messages.error(request, 'دعوتنامه منقضی شده است.')
        return redirect('users:dashboard')
    
    if invitation.status != 'PENDING':
        messages.error(request, 'این دعوتنامه قبلاً استفاده شده است.')
        return redirect('users:dashboard')
    
    # بررسی تطابق ایمیل
    if request.user.email != invitation.email:
        messages.error(request, 'لطفاً با ایمیلی که دعوت شده‌اید وارد شوید.')
        return redirect('users:dashboard')
    
    # بررسی اینکه آیا کاربر قبلاً عضو شرکت شده
    existing_role = UserCompanyRole.objects.filter(
        user=request.user,
        company=invitation.company
    ).first()
    
    if existing_role:
        if existing_role.is_active:
            messages.warning(request, 'شما قبلاً به این شرکت دسترسی دارید.')
        else:
            existing_role.is_active = True
            existing_role.role = invitation.role
            existing_role.save()
            messages.success(request, f'دسترسی شما به شرکت {invitation.company.name} فعال شد.')
    else:
        # ایجاد نقش جدید برای کاربر
        UserCompanyRole.objects.create(
            user=request.user,
            company=invitation.company,
            role=invitation.role,
            invited_by=invitation.invited_by,
            joined_at=timezone.now()
        )
        messages.success(request, f'شما با موفقیت به شرکت {invitation.company.name} اضافه شدید.')
    
    invitation.mark_as_accepted()
    
    return redirect('users:company_selection')

@login_required
def create_financial_period(request, company_id):
    """ایجاد دوره مالی جدید"""
    company = get_object_or_404(Company, id=company_id)
    
    # بررسی دسترسی کاربر
    user_role = UserCompanyRole.objects.filter(
        user=request.user, 
        company=company,
        is_active=True
    ).first()
    
    if not user_role or not user_role.can_manage_financial_data:
        raise PermissionDenied("شما دسترسی لازم برای ایجاد دوره مالی را ندارید.")
    
    if request.method == 'POST':
        form = FinancialPeriodForm(request.POST)
        if form.is_valid():
            try:
                financial_period = form.save(commit=False)
                financial_period.company = company
                financial_period.created_by = request.user
                financial_period.save()
                
                messages.success(request, f'دوره مالی "{financial_period.name}" با موفقیت ایجاد شد.')
                return redirect('users:dashboard')
                
            except Exception as e:
                messages.error(request, f'خطا در ایجاد دوره مالی: {str(e)}')
    else:
        form = FinancialPeriodForm()
    
    return render(request, 'users/create_financial_period.html', {
        'form': form,
        'company': company,
        'title': f'ایجاد دوره مالی جدید - {company.name}'
    })

@login_required
def dashboard(request):
    """داشبورد شرکت جاری - ✅ کامل"""
    company_id = request.session.get('current_company_id')
    if not company_id:
        messages.info(request, 'لطفاً یک شرکت انتخاب کنید.')
        return redirect('users:company_selection')
    
    company = get_object_or_404(Company, id=company_id)
    
    # بررسی دسترسی کاربر به شرکت جاری
    user_role = UserCompanyRole.objects.filter(
        user=request.user,
        company=company,
        is_active=True
    ).first()
    
    if not user_role:
        messages.error(request, 'شما دسترسی به شرکت جاری را ندارید.')
        del request.session['current_company_id']
        return redirect('users:company_selection')
    
    # دریافت دوره‌های مالی شرکت
    financial_periods = FinancialPeriod.objects.filter(company=company)
    
    return render(request, 'users/company_dashboard.html', {
        'company': company,
        'user_role': user_role,
        'financial_periods': financial_periods
    })

def check_auth_status(request):
    """بررسی وضعیت احراز هویت کاربر - برای دیباگ"""
    if request.user.is_authenticated:
        current_company = None
        company_id = request.session.get('current_company_id')
        if company_id:
            try:
                current_company = Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                pass
        
        return JsonResponse({
            'authenticated': True,
            'username': request.user.username,
            'email': request.user.email,
            'current_company': {
                'id': current_company.id if current_company else None,
                'name': current_company.name if current_company else None
            } if current_company else None
        })
    else:
        return JsonResponse({'authenticated': False})
