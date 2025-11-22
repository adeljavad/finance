# 🎯 **تسک ۳۰۶: طراحی مدل Company برای مدیریت شرکت‌ها**

## 📋 **شرح تسک**
ایجاد مدل Company برای مدیریت شرکت‌های مختلف و ارتباط آن با کاربران از طریق سیستم نقش‌ها و دسترسی‌های چند شرکتی.

## 🗃️ **کد کامل مدل Company**

```python
# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    """مدل کاربر سفارشی"""
    phone = models.CharField(max_length=15, blank=True, verbose_name='تلفن')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='تصویر پروفایل')
    email_verified = models.BooleanField(default=False, verbose_name='ایمیل تأیید شده')
    
    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'
    
    def __str__(self):
        return f"{self.username} - {self.email}"

class Company(models.Model):
    """مدل شرکت - تسک ۳۰۶"""
    
    COMPANY_TYPES = [
        ('MANUFACTURING', 'تولیدی'),
        ('TRADING', 'بازرگانی'),
        ('SERVICE', 'خدماتی'),
        ('CONSTRUCTION', 'پیمانکاری'),
        ('HOLDING', 'هلدینگ'),
        ('OTHER', 'سایر'),
    ]
    
    # اطلاعات اصلی شرکت
    name = models.CharField(max_length=200, verbose_name='نام شرکت')
    economic_code = models.CharField(max_length=20, verbose_name='کد اقتصادی', unique=True)
    national_code = models.CharField(max_length=20, verbose_name='شناسه ملی', unique=True)
    company_type = models.CharField(
        max_length=20, 
        choices=COMPANY_TYPES, 
        verbose_name='نوع شرکت',
        default='SERVICE'
    )
    
    # اطلاعات تماس
    address = models.TextField(verbose_name='آدرس')
    phone = models.CharField(max_length=15, verbose_name='تلفن')
    website = models.URLField(blank=True, verbose_name='وبسایت')
    email = models.EmailField(blank=True, verbose_name='ایمیل')
    
    # اطلاعات مالی
    fiscal_year_start = models.DateField(
        default=timezone.now().replace(month=1, day=1),
        verbose_name='شروع سال مالی'
    )
    fiscal_year_end = models.DateField(
        default=timezone.now().replace(month=12, day=29),
        verbose_name='پایان سال مالی'
    )
    currency = models.CharField(
        max_length=10, 
        default='IRR',
        verbose_name='واحد پول',
        choices=[('IRR', 'ریال'), ('USD', 'دلار'), ('EUR', 'یورو')]
    )
    
    # ظاهر و نمایش
    logo = models.ImageField(
        upload_to='company_logos/', 
        null=True, 
        blank=True, 
        verbose_name='لوگو'
    )
    description = models.TextField(blank=True, verbose_name='توضیحات')
    
    # وضعیت و مدیریت
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_verified = models.BooleanField(default=False, verbose_name='تأیید شده')
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='created_companies',
        verbose_name='ایجاد شده توسط'
    )
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')
    
    class Meta:
        verbose_name = 'شرکت'
        verbose_name_plural = 'شرکت‌ها'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['economic_code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_active_periods(self):
        """دریافت دوره‌های مالی فعال شرکت"""
        return self.financial_periods.filter(is_active=True)
    
    def get_active_members_count(self):
        """تعداد اعضای فعال شرکت"""
        return self.user_roles.filter(is_active=True).count()
    
    def can_user_access(self, user):
        """بررسی دسترسی کاربر به شرکت"""
        return self.user_roles.filter(user=user, is_active=True).exists()
    
    @property
    def current_fiscal_year(self):
        """سال مالی جاری"""
        today = timezone.now().date()
        if self.fiscal_year_start <= today <= self.fiscal_year_end:
            return today.year
        return self.fiscal_year_start.year

class FinancialPeriod(models.Model):
    """مدل دوره مالی - مرتبط با تسک ۳۰۸"""
    
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='financial_periods',
        verbose_name='شرکت'
    )
    name = models.CharField(max_length=100, verbose_name='نام دوره')
    start_date = models.DateField(verbose_name='تاریخ شروع')
    end_date = models.DateField(verbose_name='تاریخ پایان')
    
    # وضعیت دوره
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_closed = models.BooleanField(default=False, verbose_name='بسته شده')
    is_locked = models.BooleanField(default=False, verbose_name='قفل شده')
    
    # اطلاعات ایجاد
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        verbose_name='ایجاد شده توسط'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    
    class Meta:
        verbose_name = 'دوره مالی'
        verbose_name_plural = 'دوره‌های مالی'
        unique_together = ['company', 'name']
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} - {self.company.name}"
    
    def is_current_period(self):
        """آیا این دوره دوره جاری است؟"""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

class UserCompanyRole(models.Model):
    """مدل نقش کاربر در شرکت - مرتبط با تسک ۳۰۷"""
    
    ROLE_CHOICES = [
        ('OWNER', 'مالک'),
        ('ADMIN', 'مدیر'),
        ('ACCOUNTANT', 'حسابدار'),
        ('AUDITOR', 'حسابرس'),
        ('VIEWER', 'مشاهده‌کننده'),
        ('DATA_ENTRY', 'تکمیل کننده داده'),
    ]
    
    PERMISSION_LEVELS = {
        'OWNER': 100,
        'ADMIN': 90,
        'ACCOUNTANT': 80,
        'AUDITOR': 70,
        'DATA_ENTRY': 60,
        'VIEWER': 50,
    }
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='company_roles',
        verbose_name='کاربر'
    )
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='user_roles',
        verbose_name='شرکت'
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        verbose_name='نقش'
    )
    
    # وضعیت
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_primary = models.BooleanField(default=False, verbose_name='شرکت اصلی')
    
    # اطلاعات دعوت
    invited_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='sent_invitations',
        verbose_name='دعوت شده توسط'
    )
    invited_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ دعوت')
    joined_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ پیوستن')
    
    # تنظیمات دسترسی
    can_manage_users = models.BooleanField(default=False, verbose_name='مدیریت کاربران')
    can_manage_financial_data = models.BooleanField(default=False, verbose_name='مدیریت داده مالی')
    can_view_reports = models.BooleanField(default=True, verbose_name='مشاهده گزارش‌ها')
    can_export_data = models.BooleanField(default=False, verbose_name='خروجی گرفتن')
    
    class Meta:
        verbose_name = 'نقش کاربر در شرکت'
        verbose_name_plural = 'نقش‌های کاربران در شرکت‌ها'
        unique_together = ['user', 'company']
        ordering = ['company', '-is_primary', 'role']
    
    def __str__(self):
        return f"{self.user.username} - {self.company.name} - {self.get_role_display()}"
    
    def save(self, *args, **kwargs):
        """اتوماتیک کردن دسترسی‌ها بر اساس نقش"""
        if self.role == 'OWNER':
            self.can_manage_users = True
            self.can_manage_financial_data = True
            self.can_view_reports = True
            self.can_export_data = True
        elif self.role == 'ADMIN':
            self.can_manage_users = True
            self.can_manage_financial_data = True
            self.can_view_reports = True
            self.can_export_data = True
        elif self.role == 'ACCOUNTANT':
            self.can_manage_users = False
            self.can_manage_financial_data = True
            self.can_view_reports = True
            self.can_export_data = True
        elif self.role == 'AUDITOR':
            self.can_manage_users = False
            self.can_manage_financial_data = False
            self.can_view_reports = True
            self.can_export_data = True
        elif self.role == 'DATA_ENTRY':
            self.can_manage_users = False
            self.can_manage_financial_data = True
            self.can_view_reports = False
            self.can_export_data = False
        elif self.role == 'VIEWER':
            self.can_manage_users = False
            self.can_manage_financial_data = False
            self.can_view_reports = True
            self.can_export_data = False
        
        super().save(*args, **kwargs)
    
    def get_permission_level(self):
        """دریافت سطح دسترسی عددی"""
        return self.PERMISSION_LEVELS.get(self.role, 0)
    
    def has_permission(self, required_level):
        """بررسی داشتن دسترسی مورد نیاز"""
        return self.get_permission_level() >= required_level
```

## 🎯 **ویوهای مرتبط با Company**

```python
# users/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import Company, UserCompanyRole, FinancialPeriod
from .forms import CompanyForm, FinancialPeriodForm

@login_required
def create_company(request):
    """ایجاد شرکت جدید - تسک ۳۰۶"""
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
                role='OWNER',
                is_primary=True
            )
            
            messages.success(request, f'شرکت "{company.name}" با موفقیت ایجاد شد.')
            return redirect('users:company_selection')
    else:
        form = CompanyForm()
    
    return render(request, 'users/create_company.html', {
        'form': form,
        'title': 'ایجاد شرکت جدید'
    })

@login_required
def company_detail(request, company_id):
    """نمایش جزئیات شرکت"""
    company = get_object_or_404(Company, id=company_id)
    user_role = get_object_or_404(
        UserCompanyRole, 
        user=request.user, 
        company=company,
        is_active=True
    )
    
    # آمار شرکت
    stats = {
        'active_periods': company.financial_periods.filter(is_active=True).count(),
        'total_members': company.user_roles.filter(is_active=True).count(),
        'active_members': company.user_roles.filter(is_active=True).count(),
    }
    
    return render(request, 'users/company_detail.html', {
        'company': company,
        'user_role': user_role,
        'stats': stats
    })

@login_required
def update_company(request, company_id):
    """ویرایش اطلاعات شرکت"""
    company = get_object_or_404(Company, id=company_id)
    user_role = get_object_or_404(
        UserCompanyRole, 
        user=request.user, 
        company=company,
        is_active=True
    )
    
    # فقط مالک و مدیر می‌توانند ویرایش کنند
    if user_role.role not in ['OWNER', 'ADMIN']:
        messages.error(request, 'شما دسترسی لازم برای ویرایش شرکت را ندارید.')
        return redirect('users:company_detail', company_id=company.id)
    
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
def company_list(request):
    """لیست شرکت‌های کاربر"""
    user_companies = UserCompanyRole.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('company').order_by('-is_primary', 'company__name')
    
    return render(request, 'users/company_list.html', {
        'user_companies': user_companies
    })
```

## 📝 **فرم‌های مرتبط**

```python
# users/forms.py
from django import forms
from .models import Company, FinancialPeriod

class CompanyForm(forms.ModelForm):
    """فرم ایجاد و ویرایش شرکت"""
    
    class Meta:
        model = Company
        fields = [
            'name', 'economic_code', 'national_code', 'company_type',
            'address', 'phone', 'website', 'email', 'logo',
            'fiscal_year_start', 'fiscal_year_end', 'currency', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام کامل شرکت'
            }),
            'economic_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'کد اقتصادی ۱۲ رقمی'
            }),
            'national_code': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'شناسه ملی'
            }),
            'company_type': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'آدرس کامل شرکت'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شماره تلفن'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@company.com'
            }),
            'fiscal_year_start': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fiscal_year_end': forms.DateInput(attrs={
                'class': 'form-control', 
                'type': 'date'
            }),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'توضیحات درباره شرکت'
            }),
        }
        labels = {
            'name': 'نام شرکت *',
            'economic_code': 'کد اقتصادی *',
            'national_code': 'شناسه ملی *',
            'company_type': 'نوع شرکت *',
        }
    
    def clean_economic_code(self):
        """اعتبارسنجی کد اقتصادی"""
        economic_code = self.cleaned_data['economic_code']
        if len(economic_code) != 12 or not economic_code.isdigit():
            raise forms.ValidationError('کد اقتصادی باید ۱۲ رقم باشد.')
        return economic_code
```

## 🔗 **URLهای مرتبط**

```python
# users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # شرکت‌ها - تسک ۳۰۶
    path('company/create/', views.create_company, name='create_company'),
    path('company/list/', views.company_list, name='company_list'),
    path('company/<int:company_id>/', views.company_detail, name='company_detail'),
    path('company/<int:company_id>/update/', views.update_company, name='update_company'),
    
    # سایر URLهای موجود...
]
```

## 🎯 **خلاصه تسک ۳۰۶**

### **آنچه ایجاد شد:**
- ✅ **مدل Company** با فیلدهای کامل اطلاعات شرکتی
- ✅ **مدل FinancialPeriod** برای مدیریت دوره‌های مالی
- ✅ **مدل UserCompanyRole** برای مدیریت نقش‌ها
- ✅ **ویوهای CRUD** برای مدیریت شرکت‌ها
- ✅ **فرم‌های اعتبارسنجی** برای ایجاد و ویرایش
- ✅ **سیستم دسترسی** بر اساس نقش‌ها

### **قابلیت‌های کلیدی:**
- مدیریت اطلاعات کامل شرکت‌ها
- سیستم نقش‌ها و دسترسی‌های چندسطحی
- دوره‌های مالی مستقل برای هر شرکت
- اعتبارسنجی داده‌های شرکتی
- رابط مدیریت برای مالکان و مدیران

**تسک ۳۰۶ کامل شد! آماده برای تسک ۳۰۷ (UserCompanyRole) هستید؟** 🚀