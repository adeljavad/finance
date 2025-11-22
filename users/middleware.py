from django.shortcuts import redirect
from django.contrib import messages
from .models import Company, UserCompanyRole

class CompanyAccessMiddleware:
    """میدلور برای بررسی دسترسی کاربر به شرکت جاری"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # اگر کاربر لاگین کرده و شرکت جاری تنظیم شده
        if request.user.is_authenticated and 'current_company_id' in request.session:
            company_id = request.session['current_company_id']
            
            # بررسی وجود شرکت و دسترسی کاربر
            try:
                company = Company.objects.get(id=company_id, is_active=True)
                has_access = UserCompanyRole.objects.filter(
                    user=request.user,
                    company=company,
                    is_active=True
                ).exists()
                
                if not has_access:
                    # کاربر دسترسی ندارد، حذف شرکت از سشن
                    del request.session['current_company_id']
                    if 'current_company_name' in request.session:
                        del request.session['current_company_name']
                    if 'user_role' in request.session:
                        del request.session['user_role']
                    
                    messages.warning(request, 'دسترسی شما به شرکت جاری لغو شده است.')
                    
            except Company.DoesNotExist:
                # شرکت وجود ندارد، حذف از سشن
                del request.session['current_company_id']
                if 'current_company_name' in request.session:
                    del request.session['current_company_name']
                if 'user_role' in request.session:
                    del request.session['user_role']
        
        response = self.get_response(request)
        return response