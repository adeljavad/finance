# financial_system/services/balance_control_service.py
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from typing import Dict, List, Optional, Tuple
import logging
from decimal import Decimal

from financial_system.models.document_models import DocumentHeader, DocumentItem
from financial_system.models.coding_models import ChartOfAccounts

logger = logging.getLogger(__name__)
User = get_user_model()


class BalanceControlService:
    """سرویس کنترل توازن اسناد مالی - قابل استفاده در کل سیستم"""
    
    def __init__(self):
        self.tolerance = Decimal('0.01')  # تحمل خطای کوچک
    
    def check_document_balance(self, document_header: DocumentHeader) -> Dict:
        """بررسی توازن یک سند مالی"""
        try:
            # محاسبه جمع بدهکار و بستانکار از آرتیکل‌ها
            items = document_header.items.all()
            total_debit = sum(item.debit for item in items)
            total_credit = sum(item.credit for item in items)
            
            # بررسی توازن
            difference = abs(total_debit - total_credit)
            is_balanced = difference <= self.tolerance
            
            # به‌روزرسانی مقادیر در سربرگ سند
            document_header.total_debit = total_debit
            document_header.total_credit = total_credit
            document_header.is_balanced = is_balanced
            document_header.save()
            
            return {
                'is_balanced': is_balanced,
                'total_debit': total_debit,
                'total_credit': total_credit,
                'difference': difference,
                'document_number': document_header.document_number,
                'items_count': len(items)
            }
            
        except Exception as e:
            logger.error(f"خطا در بررسی توازن سند {document_header.document_number}: {e}")
            raise
    
    def analyze_balance_issues(self, document_header: DocumentHeader) -> Dict:
        """تحلیل مشکلات توازن و ارائه راه‌حل"""
        balance_check = self.check_document_balance(document_header)
        
        if balance_check['is_balanced']:
            return {
                'has_issues': False,
                'message': 'سند متوازن است',
                'balance_check': balance_check
            }
        
        # تحلیل مشکلات توازن
        issues = self._analyze_balance_problems(document_header, balance_check)
        suggestions = self._generate_balance_suggestions(document_header, balance_check)
        
        return {
            'has_issues': True,
            'balance_check': balance_check,
            'issues': issues,
            'suggestions': suggestions,
            'correction_options': self._get_correction_options(balance_check['difference'])
        }
    
    def _analyze_balance_problems(self, document_header: DocumentHeader, balance_check: Dict) -> List[Dict]:
        """تحلیل مشکلات خاص توازن"""
        issues = []
        difference = balance_check['difference']
        
        # بررسی آرتیکل‌های مشکوک
        items = document_header.items.all()
        
        # آرتیکل‌های با مقادیر بزرگ
        large_items = items.filter(
            models.Q(debit__gt=difference) | models.Q(credit__gt=difference)
        )
        
        if large_items.exists():
            issues.append({
                'type': 'LARGE_VALUES',
                'description': 'آرتیکل‌هایی با مقادیر بزرگتر از تفاوت توازن',
                'items': [
                    {
                        'row_number': item.row_number,
                        'account': item.account.code,
                        'debit': item.debit,
                        'credit': item.credit
                    }
                    for item in large_items
                ]
            })
        
        # آرتیکل‌های با مقادیر صفر
        zero_items = items.filter(debit=0, credit=0)
        if zero_items.exists():
            issues.append({
                'type': 'ZERO_VALUES',
                'description': 'آرتیکل‌هایی با مقادیر صفر',
                'count': zero_items.count()
            })
        
        # آرتیکل‌های با مقادیر منفی
        negative_items = items.filter(
            models.Q(debit__lt=0) | models.Q(credit__lt=0)
        )
        if negative_items.exists():
            issues.append({
                'type': 'NEGATIVE_VALUES',
                'description': 'آرتیکل‌هایی با مقادیر منفی',
                'count': negative_items.count()
            })
        
        return issues
    
    def _generate_balance_suggestions(self, document_header: DocumentHeader, balance_check: Dict) -> List[Dict]:
        """تولید پیشنهادات برای اصلاح توازن"""
        suggestions = []
        difference = balance_check['difference']
        items = document_header.items.all()
        
        # پیشنهاد 1: اضافه کردن ردیف تنظیمی
        suggestions.append({
            'type': 'ADD_ADJUSTMENT_ITEM',
            'description': f'افزودن ردیف تنظیمی برای تفاوت {difference} ریال',
            'implementation': 'AUTO',
            'impact': 'LOW',
            'details': {
                'adjustment_amount': difference,
                'suggested_account': '999999'  # حساب تنظیمی
            }
        })
        
        # پیشنهاد 2: اصلاح بزرگترین مقادیر
        largest_debit_items = items.order_by('-debit')[:3]
        largest_credit_items = items.order_by('-credit')[:3]
        
        if largest_debit_items or largest_credit_items:
            suggestions.append({
                'type': 'ADJUST_LARGEST_VALUES',
                'description': 'اصلاح بزرگترین مقادیر بدهکار/بستانکار',
                'implementation': 'MANUAL',
                'impact': 'MEDIUM',
                'details': {
                    'debit_candidates': [
                        {
                            'row_number': item.row_number,
                            'account': item.account.code,
                            'current_value': item.debit,
                            'suggested_adjustment': -min(difference, item.debit)
                        }
                        for item in largest_debit_items
                    ],
                    'credit_candidates': [
                        {
                            'row_number': item.row_number,
                            'account': item.account.code,
                            'current_value': item.credit,
                            'suggested_adjustment': -min(difference, item.credit)
                        }
                        for item in largest_credit_items
                    ]
                }
            })
        
        # پیشنهاد 3: بررسی تکراری بودن آرتیکل‌ها
        duplicate_check = self._check_duplicate_items(items)
        if duplicate_check['has_duplicates']:
            suggestions.append({
                'type': 'REMOVE_DUPLICATES',
                'description': 'حذف آرتیکل‌های تکراری',
                'implementation': 'AUTO',
                'impact': 'HIGH',
                'details': duplicate_check
            })
        
        return suggestions
    
    def _get_correction_options(self, difference: Decimal) -> List[Dict]:
        """گزینه‌های اصلاح توازن"""
        return [
            {
                'id': 'auto_adjustment',
                'name': 'اصلاح خودکار',
                'description': 'سیستم به صورت خودکار ردیف تنظیمی اضافه می‌کند',
                'type': 'AUTO',
                'requires_confirmation': True
            },
            {
                'id': 'manual_correction',
                'name': 'اصلاح دستی',
                'description': 'کاربر مقادیر را به صورت دستی اصلاح می‌کند',
                'type': 'MANUAL',
                'requires_confirmation': False
            },
            {
                'id': 'suggested_fix',
                'name': 'پیشنهاد سیستم',
                'description': 'سیستم پیشنهادات اصلاح را ارائه می‌دهد',
                'type': 'SUGGESTED',
                'requires_confirmation': True
            }
        ]
    
    def _check_duplicate_items(self, items) -> Dict:
        """بررسی آرتیکل‌های تکراری"""
        seen = set()
        duplicates = []
        
        for item in items:
            item_key = (item.account_id, item.debit, item.credit, item.description)
            if item_key in seen:
                duplicates.append({
                    'row_number': item.row_number,
                    'account': item.account.code,
                    'debit': item.debit,
                    'credit': item.credit
                })
            else:
                seen.add(item_key)
        
        return {
            'has_duplicates': len(duplicates) > 0,
            'duplicates': duplicates,
            'count': len(duplicates)
        }
    
    def apply_auto_correction(self, document_header: DocumentHeader, correction_type: str) -> Dict:
        """اعمال اصلاح خودکار توازن"""
        try:
            balance_check = self.check_document_balance(document_header)
            
            if balance_check['is_balanced']:
                return {
                    'success': True,
                    'message': 'سند از قبل متوازن است',
                    'corrected': False
                }
            
            if correction_type == 'auto_adjustment':
                return self._add_adjustment_item(document_header, balance_check['difference'])
            else:
                return {
                    'success': False,
                    'message': 'نوع اصلاح پشتیبانی نمی‌شود',
                    'corrected': False
                }
                
        except Exception as e:
            logger.error(f"خطا در اعمال اصلاح خودکار برای سند {document_header.document_number}: {e}")
            return {
                'success': False,
                'message': f'خطا در اعمال اصلاح: {str(e)}',
                'corrected': False
            }
    
    def _add_adjustment_item(self, document_header: DocumentHeader, difference: Decimal) -> Dict:
        """افزودن ردیف تنظیمی برای اصلاح توازن"""
        try:
            # ایجاد حساب تنظیمی اگر وجود ندارد
            adjustment_account, created = ChartOfAccounts.objects.get_or_create(
                code='999999',
                defaults={
                    'name': 'حساب تنظیمی تفاوت',
                    'level': 'DETAIL',
                    'is_active': True
                }
            )
            
            # تعیین نوع تنظیم (بدهکار یا بستانکار)
            items = document_header.items.all()
            total_debit = sum(item.debit for item in items)
            total_credit = sum(item.credit for item in items)
            
            if total_debit > total_credit:
                # نیاز به بستانکار
                debit = Decimal('0')
                credit = difference
                description = 'تنظیم تفاوت - بستانکار'
            else:
                # نیاز به بدهکار
                debit = difference
                credit = Decimal('0')
                description = 'تنظیم تفاوت - بدهکار'
            
            # ایجاد آرتیکل تنظیمی
            max_row_number = items.aggregate(models.Max('row_number'))['row_number__max'] or 0
            
            DocumentItem.objects.create(
                document=document_header,
                row_number=max_row_number + 1,
                account=adjustment_account,
                debit=debit,
                credit=credit,
                description=description
            )
            
            # بررسی مجدد توازن
            final_check = self.check_document_balance(document_header)
            
            return {
                'success': True,
                'message': 'اصلاح خودکار با موفقیت اعمال شد',
                'corrected': True,
                'adjustment_added': True,
                'final_balance_check': final_check
            }
            
        except Exception as e:
            logger.error(f"خطا در افزودن ردیف تنظیمی: {e}")
            raise


class DocumentBalanceTool:
    """ابزار کنترل توازن اسناد برای استفاده در چت بات و گزارش‌ها"""
    
    def __init__(self):
        self.balance_service = BalanceControlService()
    
    def check_company_balance_status(self, company_id: int, period_id: int) -> Dict:
        """بررسی وضعیت توازن کلی شرکت در یک دوره"""
        try:
            documents = DocumentHeader.objects.filter(
                company_id=company_id,
                period_id=period_id
            )
            
            total_documents = documents.count()
            balanced_documents = documents.filter(is_balanced=True).count()
            unbalanced_documents = total_documents - balanced_documents
            
            # تحلیل اسناد نامتوازن
            unbalanced_analysis = []
            for doc in documents.filter(is_balanced=False):
                analysis = self.balance_service.analyze_balance_issues(doc)
                unbalanced_analysis.append({
                    'document_number': doc.document_number,
                    'analysis': analysis
                })
            
            return {
                'company_id': company_id,
                'period_id': period_id,
                'total_documents': total_documents,
                'balanced_documents': balanced_documents,
                'unbalanced_documents': unbalanced_documents,
                'balance_ratio': balanced_documents / total_documents if total_documents > 0 else 0,
                'unbalanced_analysis': unbalanced_analysis,
                'overall_status': 'GOOD' if unbalanced_documents == 0 else 'NEEDS_ATTENTION'
            }
            
        except Exception as e:
            logger.error(f"خطا در بررسی وضعیت توازن شرکت {company_id}: {e}")
            raise
    
    def get_balance_insights(self, company_id: int, days_back: int = 30) -> Dict:
        """دریافت بینش‌های توازن برای گزارش‌دهی"""
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            start_date = timezone.now() - timedelta(days=days_back)
            
            documents = DocumentHeader.objects.filter(
                company_id=company_id,
                document_date__gte=start_date
            )
            
            balance_stats = {
                'total_documents': documents.count(),
                'balanced_documents': documents.filter(is_balanced=True).count(),
                'unbalanced_documents': documents.filter(is_balanced=False).count(),
                'total_difference': Decimal('0')
            }
            
            # محاسبه مجموع تفاوت‌ها
            for doc in documents.filter(is_balanced=False):
                balance_check = self.balance_service.check_document_balance(doc)
                balance_stats['total_difference'] += balance_check['difference']
            
            # تحلیل روند
            trend_analysis = self._analyze_balance_trend(documents)
            
            return {
                'balance_statistics': balance_stats,
                'trend_analysis': trend_analysis,
                'recommendations': self._generate_balance_recommendations(balance_stats)
            }
            
        except Exception as e:
            logger.error(f"خطا در دریافت بینش‌های توازن: {e}")
            raise
    
    def _analyze_balance_trend(self, documents) -> Dict:
        """تحلیل روند توازن اسناد"""
        # این تابع می‌تواند پیچیده‌تر شود برای تحلیل روند زمانی
        return {
            'trend': 'STABLE',  # یا IMPROVING, DECLINING
            'confidence': 'HIGH',
            'notes': 'نیاز به داده‌های بیشتر برای تحلیل دقیق'
        }
    
    def _generate_balance_recommendations(self, balance_stats: Dict) -> List[str]:
        """تولید توصیه‌های بر اساس آمار توازن"""
        recommendations = []
        
        if balance_stats['unbalanced_documents'] > 0:
            recommendations.append(
                f"{balance_stats['unbalanced_documents']} سند نامتوازن نیاز به بررسی دارند"
            )
        
        if balance_stats['total_difference'] > Decimal('1000000'):  # 1 میلیون ریال
            recommendations.append(
                f"تفاوت کل توازن {balance_stats['total_difference']} ریال است - نیاز به توجه فوری"
            )
        
        if balance_stats['balanced_documents'] / balance_stats['total_documents'] < 0.9:
            recommendations.append(
                "نسبت اسناد متوازن کمتر از 90% است - نیاز به بهبود فرآیندها"
            )
        
        return recommendations


# نمونه استفاده از سرویس در سایر بخش‌های سیستم
balance_service = BalanceControlService()
balance_tool = DocumentBalanceTool()
