# 🎯 تسک‌های جدید برای مدیریت احراز هویت پیشرفته و دسترسی چند شرکتی

## 📋 **تسک‌های جدید پیشنهادی** (تسک‌های ۳۰۱-۳۲۰)

### **فاز ۱-الف: یکپارچه‌سازی احراز هویت جیمیل** (تسک‌های ۳۰۱-۳۰۵)

```
301. **نصب و پیکربندی django-allauth برای احراز هویت اجتماعی**
302. **پیکربندی Google OAuth2 در کنسول توسعه‌دهندگان گوگل**
303. **پیاده‌سازی ثبت‌نام و ورود با جیمیل**
304. **ایجاد سیستم مدیریت حساب‌های متصل (Google + محلی)**
305. **پیاده‌سازی merge accounts برای کاربران با چندین روش ورود**
```

### **فاز ۱-ب: مدل‌سازی روابط کاربر-شرکت** (تسک‌های ۳۰۶-۳۱۰)

```
306. **طراحی مدل Company برای مدیریت شرکت‌ها**
307. **ایجاد مدل UserCompanyRole برای مدیریت دسترسی‌های چند شرکتی**
308. **پیاده‌سازی مدل FinancialPeriod برای دوره‌های مالی**
309. **ایجاد مدل UserPermission برای سطوح دسترسی پیشرفته**
310. **طراحی سیستم invite و عضویت در شرکت‌ها**
```

### **فاز ۱-ج: مدیریت دسترسی و پرمیژن‌ها** (تسک‌های ۳۱۱-۳۱۵)

```
311. **پیاده‌سازی سیستم RBAC (Role-Based Access Control)**
312. **ایجاد پرمیژن‌های سطح شرکت و سطح دوره مالی**
313. **پیاده‌سازی میدلور برای کنترل دسترسی به شرکت‌ها**
314. **ایجاد ویوهای مدیریت اعضای شرکت**
315. **پیاده‌سازی سیستم invite لینک برای شرکت‌ها**
```

### **فاز ۱-د: رابط کاربری و تجربه کاربری** (تسک‌های ۳۱۶-۳۲۰)

```
316. **ایجاد صفحه انتخاب شرکت پس از ورود**
317. **پیاده‌سازی سوئیچ بین شرکت‌های مختلف**
318. **ایجاد داشبورد مدیریت شرکت برای ادمین‌ها**
319. **پیاده‌سازی تنظیمات پروفایل کاربر در سطح شرکت**
320. **ایجاد سیستم نوتیفیکیشن برای دعوت‌نامه‌های شرکت**
```

## 🗃️ **کدهای پیاده‌سازی:**

### **۱. مدل‌های جدید برای مدیریت شرکت‌ها و دسترسی‌ها**

```python
# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.username} - {self.email}"

class Company(models.Model):
    COMPANY_TYPES = [
        ('MANUFACTURING', 'تولیدی'),
        ('TRADING', 'بازرگانی'),
        ('SERVICE', 'خدماتی'),
        ('CONSTRUCTION', 'پیمانکاری'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='نام شرکت')
    economic_code = models.CharField(max_length=20, verbose_name='کد اقتصادی', unique=True)
    national_code = models.CharField(max_length=20, verbose_name='شناسه ملی', unique=True)
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPES, verbose_name='نوع شرکت')
    address = models.TextField(verbose_name='آدرس')
    phone = models.CharField(max_length=15, verbose_name='تلفن')
    website = models.URLField(blank=True, verbose_name='وبسایت')
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True, verbose_name='لوگو')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_companies')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'شرکت'
        verbose_name_plural = 'شرکت‌ها'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class FinancialPeriod(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='financial_periods')
    name = models.CharField(max_length=100, verbose_name='نام دوره')
    start_date = models.DateField(verbose_name='تاریخ شروع')
    end_date = models.DateField(verbose_name='تاریخ پایان')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_closed = models.BooleanField(default=False, verbose_name='بسته شده')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'دوره مالی'
        verbose_name_plural = 'دوره‌های مالی'
        unique_together = ['company', 'name']
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"

class UserCompanyRole(models.Model):
    ROLE_CHOICES = [
        ('OWNER', 'مالک'),
        ('ADMIN', 'مدیر'),
        ('ACCOUNTANT', 'حسابدار'),
        ('AUDITOR', 'حسابرس'),
        ('VIEWER', 'مشاهده‌کننده'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='company_roles')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='user_roles')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name='نقش')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    invited_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='sent_invitations')
    invited_at = models.DateTimeField(auto_now_add=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'نقش کاربر در شرکت'
        verbose_name_plural = 'نقش‌های کاربران در شرکت‌ها'
        unique_together = ['user', 'company']
    
    def __str__(self):
        return f"{self.user.username} - {self.company.name} - {self.get_role_display()}"

class CompanyInvitation(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'در انتظار'),
        ('ACCEPTED', 'پذیرفته شده'),
        ('REJECTED', 'رد شده'),
        ('EXPIRED', 'منقضی شده'),
    ]
    
    email = models.EmailField(verbose_name='ایمیل دعوت شده')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invitations')
    role = models.CharField(max_length=20, choices=UserCompanyRole.ROLE_CHOICES, verbose_name='نقش')
    invited_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='company_invitations')
    token = models.CharField(max_length=100, unique=True, verbose_name='توکن دعوت')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name='وضعیت')
    expires_at = models.DateTimeField(verbose_name='تاریخ انقضا')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'دعوتنامه شرکت'
        verbose_name_plural = 'دعوتنامه‌های شرکت'
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"{self.email} - {self.company.name} - {self.get_role_display()}"

class UserSession(models.Model):
    """مدل برای مدیریت session کاربر بین شرکت‌های مختلف"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sessions')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    financial_period = models.ForeignKey(FinancialPeriod, on_delete=models.SET_NULL, null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'سشن کاربر'
        verbose_name_plural = 'سشن‌های کاربران'
    
    def __str__(self):
        return f"{self.user.username} - {self.company.name if self.company else 'No Company'}"
```

### **۲. پیکربندی django-allauth برای احراز هویت جیمیل**

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'django.contrib.sites',
    
    # allauth apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    
    'users',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

AUTH_USER_MODEL = 'users.CustomUser'

# Allauth Settings
SITE_ID = 1
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_UNIQUE_EMAIL = True
LOGIN_REDIRECT_URL = '/company/select/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

# Social Auth Settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
            'secret': os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'),
            'key': ''
        }
    }
}

# Email Settings (برای تأیید ایمیل)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
```

### **۳. ویوهای مدیریت شرکت و دسترسی‌ها**

```python
# users/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Company, UserCompanyRole, FinancialPeriod, CompanyInvitation, UserSession
from .forms import CompanyForm, FinancialPeriodForm, CompanyInvitationForm
import secrets
from django.utils import timezone
from datetime import timedelta

@login_required
def company_selection(request):
    """صفحه انتخاب شرکت پس از ورود"""
    user_roles = UserCompanyRole.objects.filter(
        user=request.user, 
        is_active=True
    ).select_related('company')
    
    # اگر کاربر فقط یک شرکت دارد، مستقیماً به آن هدایت شود
    if user_roles.count() == 1:
        company = user_roles.first().company
        return redirect('set_current_company', company_id=company.id)
    
    return render(request, 'users/company_selection.html', {
        'user_roles': user_roles
    })

@login_required
def set_current_company(request, company_id):
    """تنظیم شرکت جاری برای کاربر"""
    company = get_object_or_404(Company, id=company_id)
    
    # بررسی دسترسی کاربر به شرکت
    user_role = UserCompanyRole.objects.filter(
        user=request.user,
        company=company,
        is_active=True
    ).first()
    
    if not user_role:
        messages.error(request, 'شما دسترسی به این شرکت ندارید.')
        return redirect('company_selection')
    
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
    return redirect('dashboard')  # یا هر صفحه‌ای که پس از انتخاب شرکت باید نمایش داده شود

@login_required
def create_company(request):
    """ایجاد شرکت جدید توسط کاربر"""
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(commit=False)
            company.created_by = request.user
            company.save()
            
            # ایجاد نقش مالک برای کاربر
            UserCompanyRole.objects.create(
                user=request.user,
                company=company,
                role='OWNER'
            )
            
            messages.success(request, 'شرکت با موفقیت ایجاد شد.')
            return redirect('company_selection')
    else:
        form = CompanyForm()
    
    return render(request, 'users/create_company.html', {'form': form})

@login_required
def manage_company_members(request, company_id):
    """مدیریت اعضای شرکت"""
    company = get_object_or_404(Company, id=company_id)
    
    # بررسی دسترسی کاربر (فقط مالک و مدیر می‌توانند اعضا را مدیریت کنند)
    user_role = get_object_or_404(UserCompanyRole, user=request.user, company=company)
    if user_role.role not in ['OWNER', 'ADMIN']:
        messages.error(request, 'شما دسترسی لازم برای مدیریت اعضا را ندارید.')
        return redirect('dashboard')
    
    members = UserCompanyRole.objects.filter(company=company, is_active=True)
    invitations = CompanyInvitation.objects.filter(company=company, status='PENDING')
    
    if request.method == 'POST':
        invitation_form = CompanyInvitationForm(request.POST)
        if invitation_form.is_valid():
            invitation = invitation_form.save(commit=False)
            invitation.company = company
            invitation.invited_by = request.user
            invitation.token = secrets.token_urlsafe(32)
            invitation.expires_at = timezone.now() + timedelta(days=7)
            invitation.save()
            
            # ارسال ایمیل دعوت (اینجا باید پیاده‌سازی شود)
            # send_invitation_email(invitation)
            
            messages.success(request, 'دعوتنامه با موفقیت ارسال شد.')
            return redirect('manage_company_members', company_id=company.id)
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
    """پذیرش دعوتنامه شرکت"""
    invitation = get_object_or_404(CompanyInvitation, token=token)
    
    if invitation.is_expired():
        invitation.status = 'EXPIRED'
        invitation.save()
        messages.error(request, 'دعوتنامه منقضی شده است.')
        return redirect('dashboard')
    
    if invitation.status != 'PENDING':
        messages.error(request, 'این دعوتنامه قبلاً استفاده شده است.')
        return redirect('dashboard')
    
    # بررسی اینکه آیا کاربر با ایمیل دعوت شده موجود است
    try:
        user = CustomUser.objects.get(email=invitation.email)
    except CustomUser.DoesNotExist:
        messages.error(request, 'لطفاً با ایمیلی که دعوت شده‌اید ثبت‌نام کنید.')
        return redirect('register')
    
    # ایجاد نقش کاربر در شرکت
    UserCompanyRole.objects.create(
        user=user,
        company=invitation.company,
        role=invitation.role,
        invited_by=invitation.invited_by,
        joined_at=timezone.now()
    )
    
    invitation.status = 'ACCEPTED'
    invitation.save()
    
    messages.success(request, f'شما با موفقیت به شرکت {invitation.company.name} اضافه شدید.')
    return redirect('company_selection')

@login_required
def company_dashboard(request):
    """داشبورد شرکت جاری"""
    company_id = request.session.get('current_company_id')
    if not company_id:
        return redirect('company_selection')
    
    company = get_object_or_404(Company, id=company_id)
    user_role = request.session.get('user_role')
    
    # دریافت دوره‌های مالی شرکت
    financial_periods = FinancialPeriod.objects.filter(company=company)
    
    return render(request, 'users/company_dashboard.html', {
        'company': company,
        'user_role': user_role,
        'financial_periods': financial_periods
    })
```

### **۴. میدلور برای کنترل دسترسی**

```python
# users/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from .models import UserCompanyRole

class CompanyAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # لیست URLهایی که نیاز به شرکت جاری ندارند
        exempt_urls = [
            '/accounts/',
            '/company/select/',
            '/company/create/',
            '/invitation/',
            '/admin/',
        ]
        
        current_path = request.path
        
        # اگر کاربر لاگین کرده و مسیر معاف نیست
        if (request.user.is_authenticated and 
            not any(current_path.startswith(url) for url in exempt_urls) and
            current_path != '/'):
            
            # اگر شرکت جاری تنظیم نشده است
            if not request.session.get('current_company_id'):
                return redirect('company_selection')
            
            # بررسی دسترسی کاربر به شرکت جاری
            company_id = request.session.get('current_company_id')
            has_access = UserCompanyRole.objects.filter(
                user=request.user,
                company_id=company_id,
                is_active=True
            ).exists()
            
            if not has_access:
                # حذف شرکت جاری از سشن
                del request.session['current_company_id']
                del request.session['current_company_name']
                del request.session['user_role']
                messages.error(request, 'دسترسی شما به شرکت جاری لغو شده است.')
                return redirect('company_selection')
        
        response = self.get_response(request)
        return response
```

### **۵. فرم‌های جدید**

```python
# users/forms.py
from django import forms
from .models import Company, FinancialPeriod, CompanyInvitation

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'economic_code', 'national_code', 'company_type', 
                 'address', 'phone', 'website', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'economic_code': forms.TextInput(attrs={'class': 'form-control'}),
            'national_code': forms.TextInput(attrs={'class': 'form-control'}),
            'company_type': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }

class FinancialPeriodForm(forms.ModelForm):
    class Meta:
        model = FinancialPeriod
        fields = ['name', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class CompanyInvitationForm(forms.ModelForm):
    class Meta:
        model = CompanyInvitation
        fields = ['email', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
```

## 🚀 **اولویت اجرا:**

### **هفته ۱: یکپارچه‌سازی OAuth**
```python
301. **نصب و پیکربندی django-allauth**
302. **پیکربندی Google OAuth2**
303. **پیاده‌سازی ثبت‌نام و ورود با جیمیل**
```

### **هفته ۲: مدل‌سازی و دسترسی‌ها**
```python
306. **طراحی مدل Company**
307. **ایجاد مدل UserCompanyRole**
308. **پیاده‌سازی مدل FinancialPeriod**
```

### **هفته ۳: رابط کاربری و مدیریت**
```python
316. **ایجاد صفحه انتخاب شرکت**
311. **پیاده‌سازی سیستم RBAC**
314. **ایجاد ویوهای مدیریت اعضای شرکت**
```

**آیا مایلید با تسک ۳۰۱ (نصب و پیکربندی django-allauth) شروع کنیم؟**