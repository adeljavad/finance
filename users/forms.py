# users/forms.py
from django import forms
import jdatetime
from .models import Company, FinancialPeriod, CompanyInvitation, UserCompanyRole

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

class FinancialPeriodForm(forms.ModelForm):
    """فرم ایجاد دوره مالی"""
    
    # تغییر فیلدهای تاریخ از DateField به CharField
    start_date = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'مثلاً: 1403/01/01',
            'pattern': r'\d{4}/\d{2}/\d{2}',
            'title': 'فرمت تاریخ باید به صورت 1403/01/01 باشد'
        }),
        label='تاریخ شروع'
    )
    
    end_date = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'مثلاً: 1403/12/29',
            'pattern': r'\d{4}/\d{2}/\d{2}',
            'title': 'فرمت تاریخ باید به صورت 1403/12/29 باشد'
        }),
        label='تاریخ پایان'
    )
    
    class Meta:
        model = FinancialPeriod
        fields = ['name', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثلاً: دوره ۱۴۰۳'
            }),
        }
    
    def clean_start_date(self):
        """اعتبارسنجی تاریخ شروع فارسی"""
        start_date = self.cleaned_data['start_date']
        
        try:
            # تبدیل تاریخ فارسی به میلادی
            year, month, day = map(int, start_date.split('/'))
            persian_date = jdatetime.date(year, month, day)
            gregorian_date = persian_date.togregorian()
            return gregorian_date
        except (ValueError, AttributeError):
            raise forms.ValidationError('فرمت تاریخ شروع صحیح نیست. فرمت باید به صورت 1403/01/01 باشد.')
    
    def clean_end_date(self):
        """اعتبارسنجی تاریخ پایان فارسی"""
        end_date = self.cleaned_data['end_date']
        
        try:
            # تبدیل تاریخ فارسی به میلادی
            year, month, day = map(int, end_date.split('/'))
            persian_date = jdatetime.date(year, month, day)
            gregorian_date = persian_date.togregorian()
            return gregorian_date
        except (ValueError, AttributeError):
            raise forms.ValidationError('فرمت تاریخ پایان صحیح نیست. فرمت باید به صورت 1403/12/29 باشد.')
    
    def clean(self):
        """اعتبارسنجی منطقی تاریخ‌ها"""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError('تاریخ پایان باید بعد از تاریخ شروع باشد.')
        
        return cleaned_data

class CompanyInvitationForm(forms.ModelForm):
    """فرم دعوت کاربر به شرکت"""
    
    class Meta:
        model = CompanyInvitation
        fields = ['email', 'role']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ایمیل کاربر مورد نظر'
            }),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # محدود کردن نقش‌های قابل انتخاب (بدون مالک)
        self.fields['role'].choices = [
            ('ADMIN', 'مدیر'),
            ('ACCOUNTANT', 'حسابدار'),
            ('AUDITOR', 'حسابرس'),
            ('DATA_ENTRY', 'تکمیل کننده داده'),
            ('VIEWER', 'مشاهده‌کننده'),
        ]
