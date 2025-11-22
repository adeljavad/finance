"""
سرویس‌های امنیتی پیشرفته برای سیستم مالی هوشمند

این ماژول سرویس‌های اصلی برای مدیریت امنیت را ارائه می‌دهد:
- رمزنگاری و رمزگشایی داده‌ها
- کنترل دسترسی دقیق
- ممیزی امنیتی
- مدیریت کلیدهای رمزنگاری
- تشخیص فعالیت‌های مشکوک
"""

import logging
import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import (
    SecurityPolicy, EncryptionKey, SecurityAuditLog, DataAccessLog,
    SuspiciousActivity, SecurityAlertRule, SecurityLevel, SecurityEventType,
    EncryptionAlgorithm
)

User = get_user_model()
logger = logging.getLogger(__name__)


class EncryptionService:
    """سرویس رمزنگاری و رمزگشایی داده‌ها"""
    
    @classmethod
    def encrypt_data(cls, data: str, key_name: str = None) -> Tuple[bool, str, str]:
        """
        رمزنگاری داده
        
        Args:
            data: داده برای رمزنگاری
            key_name: نام کلید (اگر None باشد از کلید پیش‌فرض استفاده می‌شود)
            
        Returns:
            (موفقیت, داده رمز شده, پیام خطا)
        """
        try:
            # پیدا کردن کلید مناسب
            encryption_key = cls._get_encryption_key(key_name)
            if not encryption_key:
                return False, "", "کلید رمزنگاری یافت نشد"
            
            # پیاده‌سازی رمزنگاری (نمونه ساده - در تولید باید از کتابخانه‌های امن استفاده شود)
            # توجه: این یک نمونه ساده است و برای محیط تولید باید از الگوریتم‌های استاندارد استفاده شود
            encoded_data = base64.b64encode(data.encode('utf-8')).decode('utf-8')
            
            # ثبت لاگ رمزنگاری
            SecurityService.log_security_event(
                event_type=SecurityEventType.ENCRYPTION,
                description=f"رمزنگاری داده با کلید {encryption_key.key_name}",
                security_level=SecurityLevel.HIGH,
                additional_data={
                    'key_name': encryption_key.key_name,
                    'key_version': encryption_key.key_version,
                    'data_length': len(data)
                }
            )
            
            return True, encoded_data, ""
            
        except Exception as e:
            error_msg = f"خطا در رمزنگاری داده: {e}"
            logger.error(error_msg)
            return False, "", error_msg
    
    @classmethod
    def decrypt_data(cls, encrypted_data: str, key_name: str = None) -> Tuple[bool, str, str]:
        """
        رمزگشایی داده
        
        Args:
            encrypted_data: داده رمز شده
            key_name: نام کلید (اگر None باشد از کلید پیش‌فرض استفاده می‌شود)
            
        Returns:
            (موفقیت, داده رمزگشایی شده, پیام خطا)
        """
        try:
            # پیدا کردن کلید مناسب
            encryption_key = cls._get_encryption_key(key_name)
            if not encryption_key:
                return False, "", "کلید رمزنگاری یافت نشد"
            
            # پیاده‌سازی رمزگشایی (نمونه ساده)
            decoded_data = base64.b64decode(encrypted_data.encode('utf-8')).decode('utf-8')
            
            # ثبت لاگ رمزگشایی
            SecurityService.log_security_event(
                event_type=SecurityEventType.DECRYPTION,
                description=f"رمزگشایی داده با کلید {encryption_key.key_name}",
                security_level=SecurityLevel.HIGH,
                additional_data={
                    'key_name': encryption_key.key_name,
                    'key_version': encryption_key.key_version,
                    'data_length': len(decoded_data)
                }
            )
            
            return True, decoded_data, ""
            
        except Exception as e:
            error_msg = f"خطا در رمزگشایی داده: {e}"
            logger.error(error_msg)
            return False, "", error_msg
    
    @classmethod
    def _get_encryption_key(cls, key_name: str = None) -> Optional[EncryptionKey]:
        """پیدا کردن کلید رمزنگاری مناسب"""
        try:
            if key_name:
                # پیدا کردن کلید مشخص
                return EncryptionKey.objects.filter(
                    key_name=key_name,
                    is_active=True
                ).first()
            else:
                # پیدا کردن کلید اصلی
                return EncryptionKey.objects.filter(
                    is_primary=True,
                    is_active=True,
                    expires_at__gt=timezone.now()
                ).first()
                
        except Exception as e:
            logger.error(f"خطا در پیدا کردن کلید رمزنگاری: {e}")
            return None
    
    @classmethod
    def rotate_keys(cls) -> Tuple[bool, str]:
        """
        گردش کلیدهای رمزنگاری
        
        Returns:
            (موفقیت, پیام نتیجه)
        """
        try:
            # پیدا کردن کلیدهای منقضی شده
            expired_keys = EncryptionKey.objects.filter(
                expires_at__lte=timezone.now(),
                is_active=True
            )
            
            for key in expired_keys:
                key.is_active = False
                key.save()
                logger.info(f"کلید {key.key_name} v{key.key_version} غیرفعال شد")
            
            # پیدا کردن کلیدهایی که نیاز به گردش دارند
            policy = SecurityPolicy.objects.filter(is_active=True).first()
            if not policy:
                return False, "سیاست امنیتی فعال یافت نشد"
            
            rotation_threshold = timezone.now() - timedelta(days=policy.key_rotation_days)
            keys_to_rotate = EncryptionKey.objects.filter(
                is_primary=True,
                activated_at__lte=rotation_threshold,
                is_active=True
            )
            
            rotated_count = 0
            for key in keys_to_rotate:
                # ایجاد کلید جدید
                new_key = EncryptionKey.objects.create(
                    key_name=key.key_name,
                    key_description=f"گردش شده از {key.key_name} v{key.key_version}",
                    algorithm=key.algorithm,
                    key_version=key.key_version + 1,
                    key_data=key.key_data,  # در واقعیت باید کلید جدید تولید شود
                    key_checksum=cls._generate_key_checksum(key.key_data),
                    is_active=True,
                    is_primary=True,
                    expires_at=timezone.now() + timedelta(days=policy.key_rotation_days),
                    created_by=key.created_by
                )
                
                # غیرفعال کردن کلید قدیمی
                key.mark_rotated()
                
                rotated_count += 1
                logger.info(f"کلید {key.key_name} از v{key.key_version} به v{new_key.key_version} گردش شد")
            
            return True, f"{rotated_count} کلید گردش شد"
            
        except Exception as e:
            error_msg = f"خطا در گردش کلیدها: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    @classmethod
    def _generate_key_checksum(cls, key_data: bytes) -> str:
        """تولید چکسام برای کلید"""
        return hashlib.sha256(key_data).hexdigest()


class AccessControlService:
    """سرویس کنترل دسترسی دقیق"""
    
    @classmethod
    def check_data_access(cls, user: User, data_type: str, access_type: str, 
                         company_id: int = None, period_id: int = None) -> Tuple[bool, str]:
        """
        بررسی دسترسی کاربر به داده
        
        Args:
            user: کاربر
            data_type: نوع داده
            access_type: نوع دسترسی (READ, WRITE, UPDATE, DELETE, EXPORT)
            company_id: شناسه شرکت
            period_id: شناسه دوره مالی
            
        Returns:
            (مجاز بودن, پیام خطا)
        """
        try:
            # لاگ دسترسی
            cls._log_data_access(user, data_type, access_type, company_id, period_id)
            
            # بررسی دسترسی پایه
            if not user.is_authenticated:
                return False, "کاربر احراز هویت نشده"
            
            # بررسی دسترسی شرکت
            if company_id and not cls._has_company_access(user, company_id):
                return False, "دسترسی به شرکت مورد نظر مجاز نیست"
            
            # بررسی دسترسی دوره مالی
            if period_id and not cls._has_period_access(user, period_id, company_id):
                return False, "دسترسی به دوره مالی مورد نظر مجاز نیست"
            
            # بررسی دسترسی بر اساس نوع داده
            if not cls._has_data_type_access(user, data_type, access_type):
                return False, f"دسترسی {access_type} به داده‌های {data_type} مجاز نیست"
            
            return True, ""
            
        except Exception as e:
            error_msg = f"خطا در بررسی دسترسی: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    @classmethod
    def _log_data_access(cls, user: User, data_type: str, access_type: str,
                        company_id: int = None, period_id: int = None):
        """ثبت لاگ دسترسی به داده"""
        try:
            DataAccessLog.objects.create(
                user=user,
                access_type=access_type,
                data_type=data_type,
                company_id=company_id,
                period_id=period_id,
                request_path="",  # می‌تواند از request پر شود
                ip_address="",    # می‌تواند از request پر شود
                additional_data={
                    'checked_at': timezone.now().isoformat(),
                    'access_granted': True
                }
            )
        except Exception as e:
            logger.error(f"خطا در ثبت لاگ دسترسی: {e}")
    
    @classmethod
    def _has_company_access(cls, user: User, company_id: int) -> bool:
        """بررسی دسترسی کاربر به شرکت"""
        # این تابع باید با سیستم مدیریت شرکت‌ها یکپارچه شود
        # فعلاً فرض می‌کنیم کاربر به شرکت خودش دسترسی دارد
        try:
            from users.models import CompanyAccess
            return CompanyAccess.objects.filter(
                user=user,
                company_id=company_id,
                is_active=True
            ).exists()
        except ImportError:
            # اگر مدل CompanyAccess وجود ندارد، از منطق ساده استفاده کن
            return True
    
    @classmethod
    def _has_period_access(cls, user: User, period_id: int, company_id: int = None) -> bool:
        """بررسی دسترسی کاربر به دوره مالی"""
        # این تابع باید با سیستم مدیریت دوره‌های مالی یکپارچه شود
        try:
            from users.models import FinancialPeriod
            period = FinancialPeriod.objects.filter(id=period_id).first()
            if not period:
                return False
            
            # اگر شرکت مشخص شده، بررسی کن که دوره متعلق به همان شرکت باشد
            if company_id and period.company_id != company_id:
                return False
            
            return True
        except ImportError:
            return True
    
    @classmethod
    def _has_data_type_access(cls, user: User, data_type: str, access_type: str) -> bool:
        """بررسی دسترسی کاربر به نوع داده"""
        # این تابع باید با سیستم نقش‌ها و مجوزها یکپارچه شود
        # فعلاً منطق ساده
        
        # داده‌های حساس فقط برای کاربران خاص
        sensitive_data_types = ['financial_reports', 'audit_logs', 'user_data']
        if data_type in sensitive_data_types and not user.is_staff:
            return False
        
        # عملیات حساس فقط برای مدیران
        sensitive_operations = ['DELETE', 'EXPORT']
        if access_type in sensitive_operations and not user.is_staff:
            return False
        
        return True


class SecurityService:
    """سرویس اصلی امنیتی"""
    
    @classmethod
    def initialize(cls):
        """راه‌اندازی سرویس امنیتی"""
        logger.info("سرویس امنیتی راه‌اندازی شد")
        
        # ایجاد سیاست امنیتی پیش‌فرض اگر وجود ندارد
        cls._create_default_security_policy()
    
    @classmethod
    def _create_default_security_policy(cls):
        """ایجاد سیاست امنیتی پیش‌فرض"""
        try:
            if not SecurityPolicy.objects.filter(is_active=True).exists():
                SecurityPolicy.objects.create(
                    policy_name="سیاست امنیتی پیش‌فرض",
                    policy_description="سیاست امنیتی پیش‌فرض سیستم مالی هوشمند",
                    default_encryption_algorithm=EncryptionAlgorithm.AES_256,
                    key_rotation_days=90,
                    max_login_attempts=5,
                    session_timeout_minutes=30,
                    password_min_length=8,
                    password_complexity=True,
                    enable_security_audit=True,
                    audit_retention_days=365,
                    is_active=True
                )
                logger.info("سیاست امنیتی پیش‌فرض ایجاد شد")
        except Exception as e:
            logger.error(f"خطا در ایجاد سیاست امنیتی پیش‌فرض: {e}")
    
    @classmethod
    def log_security_event(cls, event_type: str, description: str, 
                          security_level: str = SecurityLevel.MEDIUM,
                          user: User = None, request=None,
                          success: bool = True, error_message: str = None,
                          additional_data: Dict[str, Any] = None):
        """
        ثبت رویداد امنیتی
        
        Args:
            event_type: نوع رویداد
            description: شرح رویداد
            security_level: سطح امنیتی
            user: کاربر مرتبط
            request: درخواست مرتبط
            success: موفقیت رویداد
            error_message: پیام خطا
            additional_data: داده‌های اضافی
        """
        try:
            request_info = cls._extract_request_info(request) if request else {}
            
            SecurityAuditLog.objects.create(
                event_type=event_type,
                event_description=description,
                security_level=security_level,
                user=user,
                session_id=request_info.get('session_id'),
                request_path=request_info.get('path'),
                request_method=request_info.get('method'),
                user_agent=request_info.get('user_agent'),
                ip_address=request_info.get('ip_address'),
                success=success,
                error_message=error_message,
                additional_data=additional_data or {}
            )
            
            # بررسی قوانین هشدار
            cls._check_security_alert_rules(event_type, security_level, user)
            
        except Exception as e:
            logger.error(f"خطا در ثبت رویداد امنیتی: {e}")
    
    @classmethod
    def _extract_request_info(cls, request) -> Dict[str, Any]:
        """استخراج اطلاعات از درخواست"""
        if not request:
            return {}
        
        return {
            'path': request.path,
            'method': request.method,
            'user_agent': request.META.get('HTTP_USER_AGENT'),
            'ip_address': cls._get_client_ip(request),
            'session_id': request.session.session_key if hasattr(request, 'session') else None
        }
    
    @classmethod
    def _get_client_ip(cls, request):
        """دریافت IP کاربر"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @classmethod
    def _check_security_alert_rules(cls, event_type: str, security_level: str, user: User = None):
        """بررسی قوانین هشدار امنیتی"""
        try:
            rules = SecurityAlertRule.objects.filter(is_active=True)
            
            for rule in rules:
                if cls._matches_security_alert_rule(event_type, security_level, rule):
                    cls._trigger_security_alert(rule, event_type, security_level, user)
                    rule.increment_trigger()
                    
        except Exception as e:
            logger.error(f"خطا در بررسی قوانین هشدار امنیتی: {e}")
    
    @classmethod
    def _matches_security_alert_rule(cls, event_type: str, security_level: str, rule: SecurityAlertRule) -> bool:
        """بررسی تطابق رویداد با قانون هشدار امنیتی"""
        # بررسی نوع رویداد
        if rule.event_type_filter and rule.event_type_filter != event_type:
            return False
        
        # بررسی سطح امنیتی
        security_order = [SecurityLevel.LOW, SecurityLevel.MEDIUM, SecurityLevel.HIGH, SecurityLevel.CRITICAL]
        event_severity_index = security_order.index(security_level)
        rule_severity_index = security_order.index(rule.security_level_threshold)
        
        if event_severity_index < rule_severity_index:
            return False
        
        # بررسی تعداد رویدادها در بازه زمانی
        time_threshold = timezone.now() - timedelta(minutes=rule.time_window_minutes)
        event_count = SecurityAuditLog.objects.filter(
            event_type=event_type,
            security_level=security_level,
            created_at__gte=time_threshold
        ).count()
        
        return event_count >= rule.event_count_threshold
    
    @classmethod
    def _trigger_security_alert(cls, rule: SecurityAlertRule, event_type: str, 
                               security_level: str, user: User = None):
        """فعال‌سازی هشدار امنیتی"""
        try:
            if rule.alert_channel == 'EMAIL':
                cls._send_security_email_alert(rule, event_type, security_level, user)
            elif rule.alert_channel == 'DASHBOARD':
                cls._log_security_dashboard_alert(rule, event_type, security_level, user)
            
            logger.info(f"هشدار امنیتی فعال شد: {rule.rule_name} برای رویداد {event_type}")
            
        except Exception as e:
            logger.error(f"خطا در فعال‌سازی هشدار امنیتی: {e}")
    
    @classmethod
    def _send_security_email_alert(cls, rule: SecurityAlertRule, event_type: str,
                                  security_level: str, user: User = None):
        """ارسال هشدار امنیتی از طریق ایمیل"""
        if not rule.recipients:
            return
        
        subject = f"هشدار امنیتی - {rule.rule_name}"
        message = f"""
        هشدار امنیتی در سیستم مالی شناسایی شد:
        
        قانون هشدار: {rule.rule_name}
        نوع رویداد: {event_type}
        سطح امنیتی: {security_level}
        کاربر: {user.username if user else 'ناشناس'}
        
        تاریخ وقوع: {timezone.now()}
        
        لطفاً در اسرع وقت اقدام نمایید.
        """
        
        recipients = [email.strip() for email in rule.recipients.split(',')]
        
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"خطا در ارسال ایمیل هشدار امنیتی: {e}")
    
    @classmethod
    def _log_security_dashboard_alert(cls, rule: SecurityAlertRule, event_type: str,
                                     security_level: str, user: User = None):
        """ثبت هشدار امنیتی در لاگ برای نمایش در داشبورد"""
        alert_message = (
            f"هشدار امنیتی: {rule.rule_name} - "
            f"رویداد {event_type} با سطح {security_level}"
        )
        logger.warning(alert_message)


class SuspiciousActivityDetector:
    """تشخیص‌دهنده فعالیت‌های مشکوک"""
    
    @classmethod
    def analyze_user_behavior(cls, user: User, request=None) -> List[Dict[str, Any]]:
        """
        تحلیل رفتار کاربر برای شناسایی فعالیت مشکوک
        
        Args:
            user: کاربر
            request: درخواست مرتبط
            
        Returns:
            لیست فعالیت‌های مشکوک شناسایی شده
        """
        suspicious_activities = []
        
        try:
            # تحلیل تعداد لاگین‌های ناموفق
            failed_logins = cls._analyze_failed_logins(user)
            if failed_logins:
                suspicious_activities.append(failed_logins)
            
            # تحلیل دسترسی به داده‌های حساس
            sensitive_access = cls._analyze_sensitive_data_access(user)
            if sensitive_access:
                suspicious_activities.append(sensitive_access)
            
            # تحلیل الگوهای دسترسی غیرعادی
            abnormal_patterns = cls._analyze_abnormal_access_patterns(user, request)
            if abnormal_patterns:
                suspicious_activities.append(abnormal_patterns)
            
            # ثبت فعالیت‌های مشکوک
            for activity in suspicious_activities:
                cls._record_suspicious_activity(activity, user, request)
            
            return suspicious_activities
            
        except Exception as e:
            logger.error(f"خطا در تحلیل رفتار کاربر: {e}")
            return []
    
    @classmethod
    def _analyze_failed_logins(cls, user: User) -> Optional[Dict[str, Any]]:
        """تحلیل لاگین‌های ناموفق"""
        try:
            policy = SecurityPolicy.objects.filter(is_active=True).first()
            if not policy:
                return None
            
            time_threshold = timezone.now() - timedelta(hours=24)
            failed_count = SecurityAuditLog.objects.filter(
                user=user,
                event_type=SecurityEventType.LOGIN_FAILED,
                created_at__gte=time_threshold
            ).count()
            
            if failed_count >= policy.max_login_attempts:
                return {
                    'activity_type': 'تعداد زیاد لاگین ناموفق',
                    'description': f'کاربر {failed_count} بار در 24 ساعت گذشته لاگین ناموفق داشته است',
                    'severity': SecurityLevel.HIGH,
                    'detection_method': 'تحلیل لاگین‌های ناموفق',
                    'confidence_score': 0.8
                }
            
            return None
            
        except Exception as e:
            logger.error(f"خطا در تحلیل لاگین‌های ناموفق: {e}")
            return None
    
    @classmethod
    def _analyze_sensitive_data_access(cls, user: User) -> Optional[Dict[str, Any]]:
        """تحلیل دسترسی به داده‌های حساس"""
        try:
            time_threshold = timezone.now() - timedelta(hours=1)
            
            # داده‌های حساس
            sensitive_data_types = ['financial_reports', 'audit_logs', 'user_data', 'encryption_keys']
            
            sensitive_access_count = DataAccessLog.objects.filter(
                user=user,
                data_type__in=sensitive_data_types,
                created_at__gte=time_threshold
            ).count()
            
            if sensitive_access_count > 10:  # آستانه دلخواه
                return {
                    'activity_type': 'دسترسی زیاد به داده‌های حساس',
                    'description': f'کاربر به {sensitive_access_count} داده حساس در 1 ساعت گذشته دسترسی داشته است',
                    'severity': SecurityLevel.MEDIUM,
                    'detection_method': 'تحلیل دسترسی به داده‌های حساس',
                    'confidence_score': 0.6
                }
            
            return None
            
        except Exception as e:
            logger.error(f"خطا در تحلیل دسترسی به داده‌های حساس: {e}")
            return None
    
    @classmethod
    def _analyze_abnormal_access_patterns(cls, user: User, request=None) -> Optional[Dict[str, Any]]:
        """تحلیل الگوهای دسترسی غیرعادی"""
        # این تابع می‌تواند پیچیده‌تر شود و از یادگیری ماشین استفاده کند
        # فعلاً یک نمونه ساده
        
        try:
            # تحلیل زمان دسترسی (مثلاً دسترسی در ساعات غیرعادی)
            current_hour = timezone.now().hour
            if current_hour < 6 or current_hour > 22:  # بین 10 شب تا 6 صبح
                return {
                    'activity_type': 'دسترسی در ساعات غیرعادی',
                    'description': f'کاربر در ساعت {current_h00} که ساعات غیرعادی است به سیستم دسترسی داشته',
                    'severity': SecurityLevel.LOW,
                    'detection_method': 'تحلیل زمان دسترسی',
                    'confidence_score': 0.4
                }
            
            return None
            
        except Exception as e:
            logger.error(f"خطا در تحلیل الگوهای دسترسی: {e}")
            return None
    
    @classmethod
    def _record_suspicious_activity(cls, activity_data: Dict[str, Any], user: User, request=None):
        """ثبت فعالیت مشکوک"""
        try:
            request_info = SecurityService._extract_request_info(request) if request else {}
            
            SuspiciousActivity.objects.create(
                activity_type=activity_data['activity_type'],
                activity_description=activity_data['description'],
                severity=activity_data['severity'],
                user=user,
                ip_address=request_info.get('ip_address'),
                detection_method=activity_data['detection_method'],
                confidence_score=activity_data['confidence_score'],
                additional_data=activity_data
            )
            
        except Exception as e:
            logger.error(f"خطا در ثبت فعالیت مشکوک: {e}")


# دکوراتور برای کنترل دسترسی
def require_access(data_type: str, access_type: str = 'READ'):
    """
    دکوراتور برای کنترل دسترسی به داده‌ها
    
    Args:
        data_type: نوع داده
        access_type: نوع دسترسی
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # پیدا کردن کاربر و درخواست از آرگومان‌ها
            user = None
            request = None
            company_id = None
            period_id = None
            
            for arg in args:
                if hasattr(arg, 'user') and hasattr(arg, 'method'):
                    request = arg
                    user = getattr(arg, 'user', None)
                    break
            
            for key, value in kwargs.items():
                if key == 'request' and hasattr(value, 'user') and hasattr(value, 'method'):
                    request = value
                    user = getattr(value, 'user', None)
                elif key == 'company_id':
                    company_id = value
                elif key == 'period_id':
                    period_id = value
            
            # بررسی دسترسی
            if user:
                has_access, error_message = AccessControlService.check_data_access(
                    user=user,
                    data_type=data_type,
                    access_type=access_type,
                    company_id=company_id,
                    period_id=period_id
                )
                
                if not has_access:
                    # ثبت رویداد امنیتی
                    SecurityService.log_security_event(
                        event_type=SecurityEventType.ACCESS_DENIED,
                        description=f"دسترسی {access_type} به {data_type} رد شد",
                        security_level=SecurityLevel.HIGH,
                        user=user,
                        request=request,
                        success=False,
                        error_message=error_message
                    )
                    
                    from django.http import JsonResponse
                    return JsonResponse({
                        'error': 'دسترسی رد شد',
                        'message': error_message
                    }, status=403)
            
            return func(*args, **kwargs)
            
        return wrapper
    return decorator
