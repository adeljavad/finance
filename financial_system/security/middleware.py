"""
میدلورهای امنیتی برای سیستم مالی هوشمند

این ماژول میدلورهای امنیتی زیر را ارائه می‌دهد:
- میدلور ممیزی امنیتی
- میدلور تشخیص فعالیت‌های مشکوک
- میدلور کنترل دسترسی
- میدلور امنیت هدرها
"""

import logging
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

from .services import SecurityService, SuspiciousActivityDetector
from .models import SecurityEventType, SecurityLevel

logger = logging.getLogger(__name__)


class SecurityAuditMiddleware(MiddlewareMixin):
    """
    میدلور ممیزی امنیتی
    
    این میدلور تمام درخواست‌ها و پاسخ‌ها را برای ممیزی امنیتی ثبت می‌کند.
    """
    
    def process_request(self, request):
        """پردازش درخواست ورودی"""
        # ثبت اطلاعات درخواست برای استفاده در process_response
        request._security_audit_start_time = timezone.now()
        return None
    
    def process_response(self, request, response):
        """پردازش پاسخ خروجی"""
        try:
            # ثبت رویداد امنیتی برای درخواست‌های مهم
            if self._should_audit_request(request):
                self._audit_request(request, response)
            
            return response
            
        except Exception as e:
            logger.error(f"خطا در میدلور ممیزی امنیتی: {e}")
            return response
    
    def _should_audit_request(self, request):
        """بررسی نیاز به ممیزی درخواست"""
        # ممیزی برای مسیرهای خاص
        audit_paths = [
            '/admin/', '/api/', '/financial/', '/users/', 
            '/data/', '/reports/', '/chat/'
        ]
        
        # ممیزی برای متدهای خاص
        audit_methods = ['POST', 'PUT', 'DELETE', 'PATCH']
        
        path = request.path
        method = request.method
        
        # بررسی مسیر
        should_audit_path = any(audit_path in path for audit_path in audit_paths)
        
        # بررسی متد
        should_audit_method = method in audit_methods
        
        return should_audit_path or should_audit_method
    
    def _audit_request(self, request, response):
        """ثبت ممیزی برای درخواست"""
        try:
            user = getattr(request, 'user', None)
            if user and user.is_authenticated:
                event_type = self._get_event_type(request, response)
                description = self._get_event_description(request, response)
                security_level = self._get_security_level(request, response)
                
                # ثبت رویداد امنیتی
                SecurityService.log_security_event(
                    event_type=event_type,
                    description=description,
                    security_level=security_level,
                    user=user,
                    request=request,
                    success=(response.status_code < 400)
                )
                
                # تحلیل رفتار کاربر برای فعالیت‌های مشکوک
                SuspiciousActivityDetector.analyze_user_behavior(user, request)
                
        except Exception as e:
            logger.error(f"خطا در ثبت ممیزی درخواست: {e}")
    
    def _get_event_type(self, request, response):
        """تعیین نوع رویداد بر اساس درخواست و پاسخ"""
        method = request.method
        
        if method == 'GET':
            return SecurityEventType.DATA_ACCESS
        elif method in ['POST', 'PUT', 'PATCH']:
            return SecurityEventType.DATA_MODIFICATION
        elif method == 'DELETE':
            return SecurityEventType.DATA_MODIFICATION
        else:
            return SecurityEventType.DATA_ACCESS
    
    def _get_event_description(self, request, response):
        """ایجاد شرح رویداد"""
        method = request.method
        path = request.path
        status_code = response.status_code
        
        return f"{method} {path} - کد وضعیت: {status_code}"
    
    def _get_security_level(self, request, response):
        """تعیین سطح امنیتی رویداد"""
        method = request.method
        path = request.path
        
        # مسیرهای حساس
        sensitive_paths = [
            '/admin/', '/api/auth/', '/users/password/', 
            '/financial/reports/', '/data/export/'
        ]
        
        # متدهای حساس
        sensitive_methods = ['POST', 'PUT', 'DELETE']
        
        if any(sensitive_path in path for sensitive_path in sensitive_paths):
            return SecurityLevel.HIGH
        elif method in sensitive_methods:
            return SecurityLevel.MEDIUM
        else:
            return SecurityLevel.LOW


class SuspiciousActivityMiddleware(MiddlewareMixin):
    """
    میدلور تشخیص فعالیت‌های مشکوک
    
    این میدلور درخواست‌ها را برای شناسایی الگوهای مشکوک تحلیل می‌کند.
    """
    
    def process_request(self, request):
        """پردازش درخواست برای شناسایی فعالیت مشکوک"""
        try:
            user = getattr(request, 'user', None)
            
            if user and user.is_authenticated:
                # تحلیل سریع برای فعالیت‌های مشکوک
                self._quick_suspicious_activity_check(user, request)
            
            return None
            
        except Exception as e:
            logger.error(f"خطا در میدلور تشخیص فعالیت‌های مشکوک: {e}")
            return None
    
    def _quick_suspicious_activity_check(self, user, request):
        """بررسی سریع برای فعالیت‌های مشکوک"""
        try:
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            path = request.path
            
            # بررسی IP مشکوک
            if self._is_suspicious_ip(ip_address):
                self._log_suspicious_activity(
                    user=user,
                    request=request,
                    activity_type='IP مشکوک',
                    description=f'دسترسی از IP مشکوک: {ip_address}',
                    severity=SecurityLevel.MEDIUM,
                    confidence_score=0.7
                )
            
            # بررسی User Agent مشکوک
            if self._is_suspicious_user_agent(user_agent):
                self._log_suspicious_activity(
                    user=user,
                    request=request,
                    activity_type='User Agent مشکوک',
                    description=f'User Agent مشکوک: {user_agent[:100]}',
                    severity=SecurityLevel.LOW,
                    confidence_score=0.5
                )
            
            # بررسی مسیرهای حساس
            if self._is_sensitive_path(path) and not user.is_staff:
                self._log_suspicious_activity(
                    user=user,
                    request=request,
                    activity_type='دسترسی به مسیر حساس',
                    description=f'دسترسی کاربر عادی به مسیر حساس: {path}',
                    severity=SecurityLevel.HIGH,
                    confidence_score=0.8
                )
                
        except Exception as e:
            logger.error(f"خطا در بررسی سریع فعالیت مشکوک: {e}")
    
    def _get_client_ip(self, request):
        """دریافت IP کاربر"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _is_suspicious_ip(self, ip_address):
        """بررسی IP مشکوک"""
        if not ip_address:
            return False
        
        # لیست IPهای مشکوک (می‌تواند از دیتابیس یا فایل تنظیمات بارگذاری شود)
        suspicious_ips = [
            # نمونه IPهای مشکوک
        ]
        
        # بررسی IPهای خصوصی که نباید از خارج بیایند
        if ip_address.startswith('192.168.') or ip_address.startswith('10.') or ip_address.startswith('172.'):
            # اگر از IP خصوصی در محیط تولید استفاده شود، مشکوک است
            if not settings.DEBUG:
                return True
        
        return ip_address in suspicious_ips
    
    def _is_suspicious_user_agent(self, user_agent):
        """بررسی User Agent مشکوک"""
        if not user_agent:
            return True  # User Agent خالی مشکوک است
        
        # User Agentهای مشکوک
        suspicious_agents = [
            'curl', 'wget', 'python', 'scanner', 'bot', 'spider',
            'nmap', 'sqlmap', 'metasploit'
        ]
        
        user_agent_lower = user_agent.lower()
        return any(suspicious in user_agent_lower for suspicious in suspicious_agents)
    
    def _is_sensitive_path(self, path):
        """بررسی مسیرهای حساس"""
        sensitive_paths = [
            '/admin/', '/api/auth/', '/users/password/reset/',
            '/financial/encryption/', '/security/'
        ]
        
        return any(sensitive_path in path for sensitive_path in sensitive_paths)
    
    def _log_suspicious_activity(self, user, request, activity_type, description, severity, confidence_score):
        """ثبت فعالیت مشکوک"""
        try:
            from .models import SuspiciousActivity
            
            request_info = SecurityService._extract_request_info(request)
            
            SuspiciousActivity.objects.create(
                activity_type=activity_type,
                activity_description=description,
                severity=severity,
                user=user,
                ip_address=request_info.get('ip_address'),
                detection_method='میدلور تشخیص سریع',
                confidence_score=confidence_score,
                additional_data={
                    'path': request.path,
                    'method': request.method,
                    'user_agent': request_info.get('user_agent')
                }
            )
            
            logger.warning(f"فعالیت مشکوک شناسایی شد: {activity_type} - {description}")
            
        except Exception as e:
            logger.error(f"خطا در ثبت فعالیت مشکوک: {e}")


class AccessControlMiddleware(MiddlewareMixin):
    """
    میدلور کنترل دسترسی
    
    این میدلور دسترسی به مسیرهای خاص را کنترل می‌کند.
    """
    
    def process_request(self, request):
        """پردازش درخواست برای کنترل دسترسی"""
        try:
            path = request.path
            
            # مسیرهایی که نیاز به کنترل دسترسی خاص دارند
            controlled_paths = {
                '/admin/': self._check_admin_access,
                '/financial/reports/export/': self._check_export_access,
                '/security/': self._check_security_access,
                '/api/encryption/': self._check_encryption_access,
            }
            
            for controlled_path, check_function in controlled_paths.items():
                if controlled_path in path:
                    result = check_function(request)
                    if result is not None:
                        return result  # برگرداندن پاسخ در صورت رد دسترسی
            
            return None
            
        except Exception as e:
            logger.error(f"خطا در میدلور کنترل دسترسی: {e}")
            return None
    
    def _check_admin_access(self, request):
        """بررسی دسترسی به پنل ادمین"""
        user = getattr(request, 'user', None)
        
        if not user or not user.is_authenticated or not user.is_staff:
            SecurityService.log_security_event(
                event_type=SecurityEventType.ACCESS_DENIED,
                description="دسترسی غیرمجاز به پنل ادمین",
                security_level=SecurityLevel.HIGH,
                user=user,
                request=request,
                success=False
            )
            
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("دسترسی به پنل ادمین مجاز نیست")
        
        return None
    
    def _check_export_access(self, request):
        """بررسی دسترسی به خروجی گزارش‌ها"""
        user = getattr(request, 'user', None)
        
        if not user or not user.is_authenticated:
            SecurityService.log_security_event(
                event_type=SecurityEventType.ACCESS_DENIED,
                description="دسترسی غیرمجاز به خروجی گزارش‌ها",
                security_level=SecurityLevel.MEDIUM,
                user=user,
                request=request,
                success=False
            )
            
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("دسترسی به خروجی گزارش‌ها مجاز نیست")
        
        return None
    
    def _check_security_access(self, request):
        """بررسی دسترسی به ماژول امنیتی"""
        user = getattr(request, 'user', None)
        
        if not user or not user.is_authenticated or not user.is_staff:
            SecurityService.log_security_event(
                event_type=SecurityEventType.ACCESS_DENIED,
                description="دسترسی غیرمجاز به ماژول امنیتی",
                security_level=SecurityLevel.HIGH,
                user=user,
                request=request,
                success=False
            )
            
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("دسترسی به ماژول امنیتی مجاز نیست")
        
        return None
    
    def _check_encryption_access(self, request):
        """بررسی دسترسی به API رمزنگاری"""
        user = getattr(request, 'user', None)
        
        if not user or not user.is_authenticated or not user.is_staff:
            SecurityService.log_security_event(
                event_type=SecurityEventType.ACCESS_DENIED,
                description="دسترسی غیرمجاز به API رمزنگاری",
                security_level=SecurityLevel.CRITICAL,
                user=user,
                request=request,
                success=False
            )
            
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("دسترسی به API رمزنگاری مجاز نیست")
        
        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    میدلور امنیت هدرها
    
    این میدلور هدرهای امنیتی را به پاسخ‌ها اضافه می‌کند.
    """
    
    def process_response(self, request, response):
        """اضافه کردن هدرهای امنیتی به پاسخ"""
        try:
            # اضافه کردن هدرهای امنیتی
            security_headers = self._get_security_headers(request)
            
            for header, value in security_headers.items():
                if header not in response:
                    response[header] = value
            
            return response
            
        except Exception as e:
            logger.error(f"خطا در میدلور امنیت هدرها: {e}")
            return response
    
    def _get_security_headers(self, request):
        """دریافت هدرهای امنیتی"""
        headers = {}
        
        # Content Security Policy
        headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "object-src 'none'; "
            "media-src 'self'; "
            "frame-src 'none'; "
            "base-uri 'self';"
        )
        
        # X-Content-Type-Options
        headers['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options
        headers['X-Frame-Options'] = 'DENY'
        
        # X-XSS-Protection
        headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer-Policy
        headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions-Policy
        headers['Permissions-Policy'] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )
        
        # Strict-Transport-Security (فقط در HTTPS)
        if not settings.DEBUG and request.is_secure():
            headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return headers
