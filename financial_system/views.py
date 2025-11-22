# financial_system/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import TemplateView, ListView, DetailView
from django.db.models import Sum, Count
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ---------------------------
# Imports با مدیریت خطا
# ---------------------------
try:
    from users.models import Company, FinancialPeriod
    from .models import DocumentHeader, DocumentItem
except ImportError as e:
    logger.warning(f"مدل‌ها در دسترس نیستند: {e}")
    # استفاده از مدل‌های پایه از users
    from users.models import Company, FinancialPeriod

try:
    from .analyzers import (
        CurrentAssetsAnalyzer,
        CurrentLiabilitiesAnalyzer,
        EquityAnalyzer,
        BalanceSheetAnalyzer,
        CashBankAnalyzer,
    )
    ANALYZERS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"تحلیل‌گرها در دسترس نیستند: {e}")
    ANALYZERS_AVAILABLE = False

try:
    from .agents.advanced_financial_agent_complete import ask_financial_question_complete_sync
    LANGCHAIN_AVAILABLE = True
    logger.info("✅ سیستم تحلیل مالی پیشرفته با موفقیت راه‌اندازی شد")
except ImportError as e:
    logger.warning(f"خطا در راه‌اندازی سیستم تحلیل مالی پیشرفته: {e}")
    LANGCHAIN_AVAILABLE = False

# ---------------------------
# توابع کمکی
# ---------------------------
def get_current_company_and_period(request):
    """بازگرداندن شرکت و دوره جاری از session"""
    company_id = request.session.get('current_company_id')
    period_id = request.session.get('current_period_id')
    company = get_object_or_404(Company, id=company_id) if company_id else None
    period = get_object_or_404(FinancialPeriod, id=period_id) if period_id else None
    return company, period

def is_financial_question(message: str) -> bool:
    """تشخیص سوالات مالی با استفاده از سیستم طبقه‌بندی پیشرفته"""
    try:
        from .tools.financial_classifier import classify_financial_question
        classification = classify_financial_question(message)
        return classification['is_financial']
    except ImportError as e:
        logger.warning(f"سیستم طبقه‌بندی پیشرفته در دسترس نیست: {e}")
        # استفاده از روش قدیمی به عنوان fallback
        keywords = [
            'دارایی', 'بدهی', 'سود', 'زیان', 'ترازنامه', 'صورت مالی',
            'حساب', 'صندوق', 'بانک', 'نقدینگی', 'سرمایه', 'درآمد',
            'هزینه', 'سود خالص', 'گردش', 'مانده', 'نسبت', 'ریسک',
            'مالی', 'حسابداری', 'حسابرسی', 'بودجه', 'جریان نقد',
            'تراز کل', 'چهارستونی', 'چهار ستون', 'فصلی', 'فصل',
            'بهار', 'تابستان', 'پاییز', 'زمستان', 'انحراف', 'مشکوک',
            'کنترل', 'گزارش', 'تحلیل', 'نقدینگی', 'جامع', 'کامل',
            'balance', 'asset', 'liability', 'equity', 'revenue', 'expense',
            'profit', 'loss', 'cash flow', 'financial', 'audit'
        ]
        message_lower = message.lower()
        return any(kw in message_lower for kw in keywords)

def log_chat_interaction(user, company_id, period_id, question, answer, is_financial, has_error=False):
    """ثبت لاگ تعاملات چت"""
    try:
        # اگر مدل ChatLog دارید، از آن استفاده کنید
        from .models import ChatLog
        ChatLog.objects.create(
            user=user,
            company_id=company_id,
            financial_period_id=period_id,
            question=question,
            answer=answer,
            is_financial=is_financial,
            has_error=has_error,
            created_at=timezone.now()
        )
    except ImportError:
        # اگر مدل ChatLog ندارید، در فایل لاگ ثبت کنید
        logger.info(f"Chat - User: {user.username}, Company: {company_id}, Q: {question}, A: {answer}")

# ---------------------------
# ویوهای اصلی
# ---------------------------

class FinancialDashboardView(TemplateView):
    """داشبورد اصلی سیستم مالی هوشمند"""
    template_name = 'financial_system/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company, period = get_current_company_and_period(self.request)

        context.update({
            'analyzers_available': ANALYZERS_AVAILABLE,
            'langchain_available': LANGCHAIN_AVAILABLE,
            'company': company,
            'period': period,
            'ai_agent_ready': LANGCHAIN_AVAILABLE,
        })

        if company and period:
            context.update({
                'quick_stats': self.get_quick_stats(company.id, period.id),
                'recent_documents': self.get_recent_documents(company.id, period.id),
                'analysis_tools': self.get_available_tools(),
            })

        return context

    def get_quick_stats(self, company_id, period_id):
        """محاسبه آمار سریع مالی"""
        try:
            # بررسی وجود مدل‌های مالی
            if 'DocumentHeader' in globals():
                total_documents = DocumentHeader.objects.filter(
                    company_id=company_id, 
                    period_id=period_id
                ).count()

                total_transactions = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id
                ).count()

                aggregates = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )

                total_debit = aggregates['total_debit'] or 0
                total_credit = aggregates['total_credit'] or 0

                return {
                    'total_documents': total_documents,
                    'total_transactions': total_transactions,
                    'total_debit': total_debit,
                    'total_credit': total_credit,
                    'net_balance': total_debit - total_credit,
                }
        except Exception as e:
            logger.error(f"خطا در محاسبه آمار سریع: {e}")
        
        return {
            'total_documents': 0,
            'total_transactions': 0,
            'total_debit': 0,
            'total_credit': 0,
            'net_balance': 0,
        }

    def get_recent_documents(self, company_id, period_id, limit=5):
        """دریافت اسناد مالی اخیر"""
        try:
            if 'DocumentHeader' in globals():
                return DocumentHeader.objects.filter(
                    company_id=company_id, 
                    period_id=period_id
                ).select_related('company', 'period').order_by('-document_date')[:limit]
        except Exception as e:
            logger.error(f"خطا در دریافت اسناد اخیر: {e}")
        
        return []

    def get_available_tools(self):
        """لیست ابزارهای تحلیل موجود"""
        if not ANALYZERS_AVAILABLE:
            return []
        
        return [
            {'name': 'تحلیل دارایی‌های جاری', 'tool': 'current_assets', 'icon': '💰', 'color': 'primary'},
            {'name': 'تحلیل بدهی‌های جاری', 'tool': 'current_liabilities', 'icon': '📊', 'color': 'warning'},
            {'name': 'تحلیل حقوق صاحبان سهام', 'tool': 'equity', 'icon': '🏛️', 'color': 'info'},
            {'name': 'کنترل ترازنامه', 'tool': 'balance_sheet', 'icon': '⚖️', 'color': 'success'},
            {'name': 'تحلیل صندوق و بانک', 'tool': 'cash_bank', 'icon': '🏦', 'color': 'danger'},
        ]


@login_required
def financial_chatbot_view(request):
    """صفحه چت بات هوشمند مالی"""
    company, period = get_current_company_and_period(request)
    
    # اگر شرکت انتخاب شده اما دوره مالی انتخاب نشده، سعی کن یک دوره فعال پیدا کن
    if company and not period:
        try:
            active_period = FinancialPeriod.objects.filter(
                company=company,
                is_active=True
            ).first()
            
            if active_period:
                period = active_period
                request.session['current_period_id'] = active_period.id
        except Exception as e:
            logger.warning(f"خطا در پیدا کردن دوره مالی فعال: {e}")
    
    context = {
        'company': company,
        'period': period,
        'ai_agent_ready': LANGCHAIN_AVAILABLE,
        'langchain_available': LANGCHAIN_AVAILABLE,
    }
    
    return render(request, 'financial_system/chatbot.html', context)


@csrf_exempt
def financial_chat_api(request):
    """API چت بات هوشمند مالی"""
    if request.method != 'POST':
        return JsonResponse({'error': 'متد غیرمجاز'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_message = data.get('question', '').strip()  # تغییر از 'message' به 'question'
        company_id = request.session.get('current_company_id')
        period_id = request.session.get('current_period_id')
        
        # اعتبارسنجی ورودی
        if not user_message:
            return JsonResponse({'error': 'پیام نمی‌تواند خالی باشد'}, status=400)
        
        if not company_id:
            return JsonResponse({
                'error': 'لطفاً ابتدا شرکت را انتخاب کنید',
                'type': 'configuration_error'
            }, status=400)
        
        # اگر دوره مالی انتخاب نشده، از دوره فعال شرکت استفاده کن
        if not period_id:
            try:
                # پیدا کردن دوره مالی فعال شرکت
                active_period = FinancialPeriod.objects.filter(
                    company_id=company_id, 
                    is_active=True
                ).first()
                
                if active_period:
                    period_id = active_period.id
                    request.session['current_period_id'] = period_id
                else:
                    return JsonResponse({
                        'error': 'هیچ دوره مالی فعالی برای این شرکت یافت نشد. لطفاً دوره مالی ایجاد کنید.',
                        'type': 'configuration_error'
                    }, status=400)
            except Exception as e:
                logger.error(f"خطا در پیدا کردن دوره مالی فعال: {e}")
                return JsonResponse({
                    'error': 'خطا در پیدا کردن دوره مالی. لطفاً با مدیر سیستم تماس بگیرید.',
                    'type': 'configuration_error'
                }, status=400)

        # تشخیص نوع سوال و پردازش
        if is_financial_question(user_message):
            return handle_financial_question(request, user_message, company_id, period_id)
        else:
            return handle_general_question(request, user_message, company_id, period_id)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'داده‌های نامعتبر'}, status=400)
    except Exception as e:
        logger.error(f"خطای سرور در چت API: {e}")
        return JsonResponse({'error': 'خطای سرور'}, status=500)


def handle_financial_question(request, user_message, company_id, period_id):
    """پردازش سوالات مالی با استفاده از AdvancedFinancialAgent پیشرفته"""
    if not LANGCHAIN_AVAILABLE:
        return JsonResponse({
            'success': False,
            'error': 'سیستم تحلیل مالی پیشرفته در حال حاضر در دسترس نیست.'
        })
    
    try:
        # استفاده از AdvancedFinancialAgent پیشرفته
        user_id = f"user_{request.user.id}" if request.user.is_authenticated else "anonymous_user"
        
        response = ask_financial_question_complete_sync(
            question=user_message,
            user_id=user_id,
            company_id=company_id,
            period_id=period_id
        )
        
        # ثبت لاگ
        log_chat_interaction(
            user=request.user,
            company_id=company_id,
            period_id=period_id,
            question=user_message,
            answer=str(response),
            is_financial=True
        )
        
        # بررسی نوع پاسخ و فرمت‌بندی مناسب
        if isinstance(response, dict):
            # اگر پاسخ دیکشنری است، مستقیماً برگردان
            return JsonResponse(response, safe=False)
        else:
            # اگر پاسخ رشته است، آن را فرمت‌بندی کن
            company = Company.objects.get(id=company_id)
            period = FinancialPeriod.objects.get(id=period_id)
            
            formatted_response = {
                "success": True,
                "report_type": "financial_analysis",
                "company_id": company_id,
                "period_id": period_id,
                "data": {
                    "metadata": {
                        "report_title": "تحلیل مالی هوشمند",
                        "company_name": company.name,
                        "period_name": period.name,
                        "generation_date": timezone.now().strftime("%Y-%m-%d"),
                        "currency": "ریال",
                        "language": "fa"
                    },
                    "content": response,
                    "question": user_message
                }
            }
            return JsonResponse(formatted_response, safe=False)
        
    except Exception as e:
        error_msg = f"خطا در پردازش سوال مالی: {str(e)}"
        logger.error(error_msg)
        
        log_chat_interaction(
            user=request.user,
            company_id=company_id,
            period_id=period_id,
            question=user_message,
            answer=error_msg,
            is_financial=True,
            has_error=True
        )
        
        return JsonResponse({
            'success': False,
            'error': 'متأسفانه در پردازش سوال مالی مشکلی پیش آمده. لطفاً دوباره تلاش کنید.',
            'type': 'error',
            'is_financial': True
        }, safe=False)


def handle_general_question(request, user_message, company_id, period_id):
    """پردازش سوالات عمومی با استفاده از سیستم fallback پیشرفته"""
    try:
        # استفاده از سیستم fallback پیشرفته
        from .tools.financial_classifier import get_financial_fallback_response
        response_text = get_financial_fallback_response(user_message)
        
        log_chat_interaction(
            user=request.user,
            company_id=company_id,
            period_id=period_id,
            question=user_message,
            answer=response_text,
            is_financial=False
        )
        
        # فرمت‌بندی پاسخ به فرمت استاندارد
        response = {
            "success": True,
            "report_type": "text_response",
            "company_id": company_id,
            "period_id": period_id,
            "data": {
                "metadata": {
                    "report_title": "پاسخ متنی",
                    "company_name": f"شرکت {company_id}",
                    "period_name": f"دوره {period_id}",
                    "generation_date": "2025-10-31",
                    "currency": "ریال",
                    "language": "fa"
                },
                "content": response_text,
                "question": user_message
            }
        }
        
        return JsonResponse(response)
        
    except ImportError as e:
        logger.warning(f"سیستم fallback پیشرفته در دسترس نیست: {e}")
        # استفاده از پاسخ fallback ساده
        response_text = "سیستم چت عمومی در دسترس نیست. لطفاً از سوالات مالی استفاده کنید."
        
        response = {
            "success": True,
            "report_type": "text_response",
            "company_id": company_id,
            "period_id": period_id,
            "data": {
                "metadata": {
                    "report_title": "پاسخ متنی",
                    "company_name": f"شرکت {company_id}",
                    "period_name": f"دوره {period_id}",
                    "generation_date": "2025-10-31",
                    "currency": "ریال",
                    "language": "fa"
                },
                "content": response_text,
                "question": user_message
            }
        }
        
        return JsonResponse(response)
    except Exception as e:
        logger.error(f"خطا در پردازش سوال عمومی: {e}")
        response = {
            "success": False,
            "error": "خطا در پردازش سوال. لطفاً دوباره تلاش کنید."
        }
        return JsonResponse(response)


@login_required
def financial_analysis_view(request, analysis_type):
    """صفحه تحلیل‌های مالی تخصصی"""
    if not ANALYZERS_AVAILABLE:
        messages.error(request, 'سیستم تحلیل مالی در حال حاضر در دسترس نیست.')
        return redirect('financial_system:dashboard')
    
    company, period = get_current_company_and_period(request)
    
    if not company or not period:
        messages.error(request, 'لطفاً ابتدا شرکت و دوره مالی را انتخاب کنید.')
        return redirect('financial_system:dashboard')
    
    # مپینگ نوع تحلیل به آنالایزر
    analyzer_map = {
        'current_assets': ('تحلیل دارایی‌های جاری', CurrentAssetsAnalyzer),
        'current_liabilities': ('تحلیل بدهی‌های جاری', CurrentLiabilitiesAnalyzer),
        'equity': ('تحلیل حقوق صاحبان سهام', EquityAnalyzer),
        'balance_sheet': ('کنترل ترازنامه', BalanceSheetAnalyzer),
        'cash_bank': ('تحلیل صندوق و بانک', CashBankAnalyzer),
    }
    
    if analysis_type not in analyzer_map:
        messages.error(request, 'نوع تحلیل نامعتبر است.')
        return redirect('financial_system:dashboard')
    
        title, analyzer_class = analyzer_map[analysis_type]
    
        try:
            analyzer = analyzer_class(company.id, period.id)
            
            # اجرای تحلیل بر اساس نوع
            if analysis_type == 'balance_sheet':
                result = analyzer.analyze_balance_sheet(company.id, period.id)
            elif analysis_type == 'cash_bank':
                result = analyzer.analyze_cash_positions()
            elif analysis_type == 'current_assets':
                result = analyzer.analyze_current_assets()
            elif analysis_type == 'current_liabilities':
                result = analyzer.analyze_current_liabilities()
            else:  # equity
                result = analyzer.analyze_equity()
            
            context = {
                'company': company,
                'period': period,
                'analysis_type': analysis_type,
                'analysis_title': title,
                'result': result,
                'executed_at': timezone.now(),
            }
            
            return render(request, 'financial_system/analysis_result.html', context)
            
        except Exception as e:
            logger.error(f"خطا در اجرای تحلیل {analysis_type}: {e}")
            messages.error(request, f'خطا در اجرای تحلیل: {str(e)}')
            return redirect('financial_system:dashboard')


@login_required
def quick_analysis_api(request):
    """API برای تحلیل سریع"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            analysis_type = data.get('analysis_type')
            company_id = request.session.get('current_company_id')
            period_id = request.session.get('current_period_id')
            
            if not company_id or not period_id:
                return JsonResponse({'error': 'شرکت و دوره مالی انتخاب نشده'}, status=400)
            
            if not ANALYZERS_AVAILABLE:
                return JsonResponse({'error': 'سیستم تحلیل در دسترس نیست'}, status=503)
            
            # اجرای تحلیل سریع
            if analysis_type == 'balance_sheet':
                analyzer = BalanceSheetAnalyzer(company_id, period_id)
                result = analyzer.analyze_balance_sheet()
            elif analysis_type == 'current_assets':
                analyzer = CurrentAssetsAnalyzer(company_id, period_id)
                result = analyzer.analyze_current_assets()
            else:
                return JsonResponse({'error': 'نوع تحلیل پشتیبانی نمی‌شود'}, status=400)
            
            return JsonResponse({'result': result})
            
        except Exception as e:
            logger.error(f"خطا در تحلیل سریع: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'متد غیرمجاز'}, status=405)


# ---------------------------
# ویوهای مدیریت اسناد و گزارشات
# ---------------------------

class DocumentListView(ListView):
    """لیست اسناد مالی"""
    model = DocumentHeader
    template_name = 'financial_system/document_list.html'
    paginate_by = 20
    context_object_name = 'documents'
    
    def get_queryset(self):
        company_id = self.request.session.get('current_company_id')
        period_id = self.request.session.get('current_period_id')
        
        if company_id and period_id:
            return DocumentHeader.objects.filter(
                company_id=company_id,
                period_id=period_id
            ).select_related('company', 'period').order_by('-document_date')
        return DocumentHeader.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company, period = get_current_company_and_period(self.request)
        
        # محاسبه جمع‌بندی کل اسناد
        total_summary = self.get_total_summary()
        
        context.update({
            'company': company,
            'period': period,
            'total_summary': total_summary,
        })
        return context
    
    def get_total_summary(self):
        """محاسبه جمع‌بندی کل اسناد"""
        company_id = self.request.session.get('current_company_id')
        period_id = self.request.session.get('current_period_id')
        
        if not company_id or not period_id:
            return {
                'total_documents': 0,
                'total_debit': 0,
                'total_credit': 0,
                'net_balance': 0
            }
        
        try:
            # محاسبه تعداد کل اسناد
            total_documents = DocumentHeader.objects.filter(
                company_id=company_id,
                period_id=period_id
            ).count()
            
            # محاسبه جمع کل بدهکار و بستانکار
            aggregates = DocumentHeader.objects.filter(
                company_id=company_id,
                period_id=period_id
            ).aggregate(
                total_debit=Sum('total_debit'),
                total_credit=Sum('total_credit')
            )
            
            total_debit = aggregates['total_debit'] or 0
            total_credit = aggregates['total_credit'] or 0
            net_balance = total_debit - total_credit
            
            return {
                'total_documents': total_documents,
                'total_debit': total_debit,
                'total_credit': total_credit,
                'net_balance': net_balance
            }
            
        except Exception as e:
            logger.error(f"خطا در محاسبه جمع‌بندی: {e}")
            return {
                'total_documents': 0,
                'total_debit': 0,
                'total_credit': 0,
                'net_balance': 0
            }


class DocumentDetailView(DetailView):
    """جزئیات سند مالی"""
    model = DocumentHeader
    template_name = 'financial_system/document_detail.html'
    context_object_name = 'document'
    
    def get_queryset(self):
        company_id = self.request.session.get('current_company_id')
        if company_id:
            return DocumentHeader.objects.filter(company_id=company_id)
        return DocumentHeader.objects.none()


@login_required
def financial_reports_view(request):
    """صفحه گزارش‌های مالی"""
    company, period = get_current_company_and_period(request)
    
    if not company or not period:
        messages.error(request, 'لطفاً ابتدا شرکت و دوره مالی را انتخاب کنید.')
        return redirect('financial_system:dashboard')
    
    # گزارش‌های موجود
    reports = [
        {'name': 'تراز آزمایشی', 'slug': 'trial_balance', 'icon': '📋', 'description': 'گزارش کلی حساب‌ها'},
        {'name': 'ترازنامه', 'slug': 'balance_sheet', 'icon': '🏛️', 'description': 'وضعیت دارایی و بدهی‌ها'},
        {'name': 'گردش حساب‌ها', 'slug': 'account_turnover', 'icon': '🔄', 'description': 'گردش مالی حساب‌ها'},
        {'name': 'گزارش تحلیل‌های هوشمند', 'slug': 'ai_analysis', 'icon': '🤖', 'description': 'تحلیل‌های پیشرفته AI'},
    ]
    
    context = {
        'company': company,
        'period': period,
        'reports': reports,
    }
    
    return render(request, 'financial_system/reports.html', context)


@login_required
def risk_analysis_view(request):
    """تحلیل ریسک‌های مالی - ویژه حسابرسی"""
    company, period = get_current_company_and_period(request)
    
    if not company or not period:
        messages.error(request, 'لطفاً ابتدا شرکت و دوره مالی را انتخاب کنید.')
        return redirect('financial_system:dashboard')
    
    # تحلیل‌های ریسک (می‌تواند از آنالایزرها استفاده کند)
    risk_analysis = {
        'financial_risks': analyze_financial_risks(company.id, period.id),
        'compliance_risks': analyze_compliance_risks(company.id, period.id),
        'operational_risks': analyze_operational_risks(company.id, period.id),
    }
    
    context = {
        'company': company,
        'period': period,
        'risk_analysis': risk_analysis,
        'analysis_date': timezone.now(),
    }
    
    return render(request, 'financial_system/risk_analysis.html', context)


# ---------------------------
# توابع کمکی تحلیل ریسک (برای توسعه آینده)
# ---------------------------

def analyze_financial_risks(company_id, period_id):
    """تحلیل ریسک‌های مالی"""
    return {
        'liquidity_risk': 'متوسط',
        'solvency_risk': 'پایین',
        'profitability_risk': 'پایین',
        'cash_flow_risk': 'متوسط',
    }

def analyze_compliance_risks(company_id, period_id):
    """تحلیل ریسک‌های انطباقی"""
    return {
        'tax_compliance': 'مطابق',
        'accounting_standards': 'مطابق', 
        'reporting_requirements': 'نیاز به بررسی',
    }

def analyze_operational_risks(company_id, period_id):
    """تحلیل ریسک‌های عملیاتی"""
    return {
        'internal_controls': 'قوی',
        'fraud_risk': 'پایین',
        'error_rate': 'کم',
    }

# financial_system/views.py
# [کدهای قبلی تا انتهای فایل]

# ---------------------------
# ویوهای مفقوده - اضافه کردن این بخش
# ---------------------------

@login_required
def generate_report_view(request, report_slug):
    """تولید گزارش مالی"""
    company, period = get_current_company_and_period(request)
    
    if not company or not period:
        messages.error(request, 'لطفاً ابتدا شرکت و دوره مالی را انتخاب کنید.')
        return redirect('financial_system:reports')
    
    # مپینگ گزارش‌ها
    report_map = {
        'trial_balance': ('تراز آزمایشی', _generate_trial_balance),
        'balance_sheet': ('ترازنامه', _generate_balance_sheet),
        'account_turnover': ('گردش حساب‌ها', _generate_account_turnover),
        'ai_analysis': ('تحلیل هوشمند', _generate_ai_analysis),
    }
    
    if report_slug not in report_map:
        messages.error(request, 'گزارش مورد نظر یافت نشد.')
        return redirect('financial_system:reports')
    
    report_name, report_generator = report_map[report_slug]
    
    try:
        report_data = report_generator(company.id, period.id)
        
        context = {
            'company': company,
            'period': period,
            'report_name': report_name,
            'report_slug': report_slug,
            'report_data': report_data,
            'generated_at': timezone.now(),
        }
        
        return render(request, 'financial_system/report_result.html', context)
        
    except Exception as e:
        logger.error(f"خطا در تولید گزارش {report_slug}: {e}")
        messages.error(request, f'خطا در تولید گزارش: {str(e)}')
        return redirect('financial_system:reports')

def _generate_trial_balance(company_id, period_id):
    """تولید تراز آزمایشی"""
    try:
        from django.db.models import Sum, Count
        from financial_system.models.document_models import DocumentItem
        from financial_system.models.coding_models import ChartOfAccounts
        from .tools.json_formatter import FinancialJSONFormatter
        
        # جمع‌بندی گردش حساب‌ها
        account_turnover = DocumentItem.objects.filter(
            document__company_id=company_id,
            document__period_id=period_id
        ).values(
            'account__code',
            'account__name'
        ).annotate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit'),
            transaction_count=Count('id')
        ).order_by('account__code')
        
        # محاسبه مانده هر حساب
        accounts_data = []
        total_debit = 0
        total_credit = 0
        
        for account in account_turnover:
            debit = account['total_debit'] or 0
            credit = account['total_credit'] or 0
            balance = debit - credit
            
            accounts_data.append({
                'account_code': account['account__code'],
                'account_name': account['account__name'] or 'بدون نام',
                'debit': debit,
                'credit': credit,
                'balance': balance,
                'transaction_count': account['transaction_count'],
                'formatted_debit': f"{debit:,.0f} ریال",
                'formatted_credit': f"{credit:,.0f} ریال",
                'formatted_balance': f"{balance:,.0f} ریال"
            })
            
            total_debit += debit
            total_credit += credit
        
        # محاسبه مانده کل
        total_balance = total_debit - total_credit
        
        # استفاده از فرمت‌تر JSON
        formatter = FinancialJSONFormatter(company_id, period_id)
        trial_balance_data = {
            'accounts': accounts_data,
            'summary': {
                'total_accounts': len(accounts_data),
                'total_debit': total_debit,
                'total_credit': total_credit,
                'total_balance': total_balance,
                'is_balanced': total_balance == 0,
                'formatted_total_debit': f"{total_debit:,.0f} ریال",
                'formatted_total_credit': f"{total_credit:,.0f} ریال",
                'formatted_total_balance': f"{total_balance:,.0f} ریال"
            }
        }
        
        return formatter.format_trial_balance(trial_balance_data)
        
    except Exception as e:
        logger.error(f"خطا در تولید تراز آزمایشی: {e}")
        return {
            'type': 'trial_balance',
            'title': 'تراز آزمایشی',
            'data': {'error': f'خطا در تولید گزارش: {str(e)}'}
        }

def _generate_balance_sheet(company_id, period_id):
    """تولید ترازنامه"""
    return {
        'type': 'balance_sheet',
        'title': 'ترازنامه',
        'data': {'message': 'گزارش ترازنامه - در حال توسعه'}
    }

def _generate_account_turnover(company_id, period_id):
    """تولید گردش حساب‌ها"""
    try:
        from django.db.models import Sum, Count
        from financial_system.models.document_models import DocumentItem
        from .tools.json_formatter import FinancialJSONFormatter
        
        # جمع‌بندی گردش حساب‌ها
        account_turnover = DocumentItem.objects.filter(
            document__company_id=company_id,
            document__period_id=period_id
        ).values(
            'account__code',
            'account__name'
        ).annotate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit'),
            transaction_count=Count('id')
        ).order_by('account__code')
        
        # محاسبه مانده هر حساب
        accounts_data = []
        total_debit = 0
        total_credit = 0
        
        for account in account_turnover:
            debit = account['total_debit'] or 0
            credit = account['total_credit'] or 0
            balance = debit - credit
            
            accounts_data.append({
                'account_code': account['account__code'],
                'account_name': account['account__name'] or 'بدون نام',
                'debit': debit,
                'credit': credit,
                'balance': balance,
                'transaction_count': account['transaction_count'],
                'formatted_debit': f"{debit:,.0f} ریال",
                'formatted_credit': f"{credit:,.0f} ریال",
                'formatted_balance': f"{balance:,.0f} ریال"
            })
            
            total_debit += debit
            total_credit += credit
        
        # محاسبه مانده کل
        total_balance = total_debit - total_credit
        
        # استفاده از فرمت‌تر JSON
        formatter = FinancialJSONFormatter(company_id, period_id)
        account_turnover_data = {
            'accounts': accounts_data,
            'summary': {
                'total_accounts': len(accounts_data),
                'total_debit': total_debit,
                'total_credit': total_credit,
                'total_balance': total_balance,
                'is_balanced': total_balance == 0,
                'formatted_total_debit': f"{total_debit:,.0f} ریال",
                'formatted_total_credit': f"{total_credit:,.0f} ریال",
                'formatted_total_balance': f"{total_balance:,.0f} ریال"
            }
        }
        
        return formatter.format_account_turnover(account_turnover_data)
        
    except Exception as e:
        logger.error(f"خطا در تولید گزارش گردش حساب‌ها: {e}")
        return {
            'type': 'account_turnover',
            'title': 'گردش حساب‌ها',
            'data': {'error': f'خطا در تولید گزارش: {str(e)}'}
        }

def _generate_ai_analysis(company_id, period_id):
    """تولید تحلیل هوشمند"""
    return {
        'type': 'ai_analysis',
        'title': 'تحلیل هوشمند',
        'data': {'message': 'گزارش تحلیل هوشمند - در حال توسعه'}
    }

@login_required
def langchain_tools_view(request):
    """صفحه ابزارهای LangChain"""
    if not LANGCHAIN_AVAILABLE:
        messages.error(request, 'سیستم هوش مصنوعی در حال حاضر در دسترس نیست.')
        return redirect('financial_system:dashboard')
    
    try:
        from .core.langchain_tools import get_all_financial_tools
        tools_list = get_all_financial_tools()
        
        context = {
            'tools': tools_list,
            'tools_count': len(tools_list),
            'company': get_current_company_and_period(request)[0],
            'period': get_current_company_and_period(request)[1],
        }
        
        return render(request, 'financial_system/langchain_tools.html', context)
        
    except Exception as e:
        logger.error(f"خطا در بارگذاری ابزارهای LangChain: {e}")
        messages.error(request, 'خطا در بارگذاری ابزارهای هوش مصنوعی')
        return redirect('financial_system:dashboard')

@login_required
def execute_tool_view(request, tool_name):
    """اجرای یک ابزار LangChain"""
    if not LANGCHAIN_AVAILABLE:
        messages.error(request, 'سیستم هوش مصنوعی در حال حاضر در دسترس نیست.')
        return redirect('financial_system:langchain_tools')
    
    company_id = request.session.get('current_company_id')
    period_id = request.session.get('current_period_id')
    
    if not company_id or not period_id:
        messages.error(request, 'لطفاً ابتدا شرکت و دوره مالی را انتخاب کنید.')
        return redirect('financial_system:langchain_tools')
    
    try:
        from .core.langchain_tools import execute_tool
        
        result = execute_tool(tool_name, company_id=company_id, period_id=period_id)
        
        context = {
            'tool_name': tool_name,
            'tool_description': 'ابزار تحلیل مالی هوشمند',
            'result': result,
            'executed_at': timezone.now(),
            'company': get_current_company_and_period(request)[0],
            'period': get_current_company_and_period(request)[1],
        }
        
        # Check if the result contains financial ratios data and use the appropriate template
        try:
            if result and isinstance(result, str):
                # Try to parse the result as JSON
                parsed_result = json.loads(result)
                if (isinstance(parsed_result, dict) and 
                    parsed_result.get('report_type') == 'financial_ratios'):
                    return render(request, 'financial_system/financial_ratios_display.html', context)
            elif (isinstance(result, dict) and 
                  result.get('report_type') == 'financial_ratios'):
                return render(request, 'financial_system/financial_ratios_display.html', context)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Default to the regular tool result template
        return render(request, 'financial_system/tool_result.html', context)
        
    except Exception as e:
        logger.error(f"خطا در اجرای ابزار {tool_name}: {e}")
        messages.error(request, f'خطا در اجرای ابزار: {str(e)}')
        return redirect('financial_system:langchain_tools')

# ---------------------------
# ویو تحلیل ریسک - اضافه کردن
# ---------------------------

@login_required
def risk_analysis_view(request):
    """تحلیل ریسک‌های مالی"""
    company, period = get_current_company_and_period(request)
    
    if not company or not period:
        messages.error(request, 'لطفاً ابتدا شرکت و دوره مالی را انتخاب کنید.')
        return redirect('financial_system:dashboard')
    
    try:
        # تحلیل‌های ریسک
        risk_analysis = {
            'financial_risks': analyze_financial_risks(company.id, period.id),
            'compliance_risks': analyze_compliance_risks(company.id, period.id),
            'operational_risks': analyze_operational_risks(company.id, period.id),
        }
        
        context = {
            'company': company,
            'period': period,
            'risk_analysis': risk_analysis,
            'analysis_date': timezone.now(),
        }
        
        return render(request, 'financial_system/risk_analysis.html', context)
        
    except Exception as e:
        logger.error(f"خطا در تحلیل ریسک: {e}")
        messages.error(request, 'خطا در اجرای تحلیل ریسک')
        return redirect('financial_system:dashboard')

# ---------------------------
# ویوهای تراز آزمایشی - اضافه کردن
# ---------------------------

@login_required
def trial_balance_report(request):
    """گزارش تراز آزمایشی با قابلیت انتخاب سطح و فیلتر تاریخ"""
    company_id = request.session.get('current_company_id')
    period_id = request.session.get('current_period_id')
    
    if not company_id or not period_id:
        messages.error(request, 'لطفاً ابتدا شرکت و دوره مالی را انتخاب کنید.')
        return redirect('financial_system:dashboard')
    
    company = get_object_or_404(Company, id=company_id)
    period = get_object_or_404(FinancialPeriod, id=period_id)
    
    # دریافت پارامترهای فیلتر
    level_filter = request.GET.get('level', 'ALL')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # اعتبارسنجی تاریخ‌ها
    try:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date = None
        end_date = None
        messages.warning(request, 'فرمت تاریخ نامعتبر است. از فرمت YYYY-MM-DD استفاده کنید.')
    
    # تولید گزارش
    try:
        report_data = _generate_trial_balance_with_filters(
            company_id, period_id, level_filter, start_date, end_date
        )
        
        context = {
            'company': company,
            'period': period,
            'report_name': 'تراز آزمایشی',
            'report_slug': 'trial_balance',
            'report_data': report_data,
            'level_filter': level_filter,
            'start_date': start_date.strftime('%Y-%m-%d') if start_date else '',
            'end_date': end_date.strftime('%Y-%m-%d') if end_date else '',
            'account_levels': [
                {'value': 'ALL', 'label': 'همه سطوح'},
                {'value': 'CLASS', 'label': 'گروه (کل)'},
                {'value': 'SUBCLASS', 'label': 'معین'},
                {'value': 'DETAIL', 'label': 'تفصیلی'},
                {'value': 'PROJECT', 'label': 'پروژه'},
                {'value': 'COST_CENTER', 'label': 'مرکز هزینه'},
            ],
            'generated_at': timezone.now(),
        }
        
        return render(request, 'financial_system/trial_balance_report.html', context)
        
    except Exception as e:
        logger.error(f"خطا در تولید تراز آزمایشی: {e}")
        messages.error(request, f'خطا در تولید گزارش: {str(e)}')
        return redirect('financial_system:reports')

def _generate_trial_balance_with_filters(company_id, period_id, level_filter='ALL', start_date=None, end_date=None):
    """تولید تراز آزمایشی با فیلترهای سطح و تاریخ"""
    try:
        # ساخت کوئری پایه
        base_query = DocumentItem.objects.filter(
            document__company_id=company_id,
            document__period_id=period_id
        )
        
        # اعمال فیلتر تاریخ
        if start_date:
            base_query = base_query.filter(document__document_date__gte=start_date)
        if end_date:
            base_query = base_query.filter(document__document_date__lte=end_date)
        
        # اگر سطح خاصی انتخاب شده، فیلتر سطح حساب
        if level_filter != 'ALL':
            base_query = base_query.filter(account__level=level_filter)
        
        # جمع‌بندی گردش حساب‌ها
        account_turnover = base_query.values(
            'account__code',
            'account__name',
            'account__level'
        ).annotate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit'),
            transaction_count=Count('id')
        ).order_by('account__code')
        
        # محاسبه مانده هر حساب
        accounts_data = []
        total_debit = 0
        total_credit = 0
        
        for account in account_turnover:
            debit = account['total_debit'] or 0
            credit = account['total_credit'] or 0
            balance = debit - credit
            
            # تعیین نوع مانده
            balance_type = 'بدهکار' if balance > 0 else 'بستانکار' if balance < 0 else 'صفر'
            
            accounts_data.append({
                'account_code': account['account__code'],
                'account_name': account['account__name'] or 'بدون نام',
                'account_level': account['account__level'],
                'account_level_display': _get_level_display(account['account__level']),
                'debit': debit,
                'credit': credit,
                'balance': abs(balance),
                'balance_type': balance_type,
                'transaction_count': account['transaction_count'],
                'formatted_debit': f"{debit:,.0f} ریال",
                'formatted_credit': f"{credit:,.0f} ریال",
                'formatted_balance': f"{abs(balance):,.0f} ریال",
                'balance_display': f"{abs(balance):,.0f} ریال ({balance_type})"
            })
            
            total_debit += debit
            total_credit += credit
        
        # محاسبه مانده کل
        total_balance = total_debit - total_credit
        total_balance_type = 'بدهکار' if total_balance > 0 else 'بستانکار' if total_balance < 0 else 'صفر'
        
        # آمار سطح‌های حساب
        level_stats = _calculate_level_statistics(accounts_data)
        
        trial_balance_data = {
            'accounts': accounts_data,
            'summary': {
                'total_accounts': len(accounts_data),
                'total_debit': total_debit,
                'total_credit': total_credit,
                'total_balance': abs(total_balance),
                'total_balance_type': total_balance_type,
                'is_balanced': total_balance == 0,
                'formatted_total_debit': f"{total_debit:,.0f} ریال",
                'formatted_total_credit': f"{total_credit:,.0f} ریال",
                'formatted_total_balance': f"{abs(total_balance):,.0f} ریال ({total_balance_type})",
                'balance_status': 'متوازن' if total_balance == 0 else 'نامتوازن'
            },
            'filters': {
                'level_filter': level_filter,
                'start_date': start_date,
                'end_date': end_date,
                'level_filter_display': _get_level_display(level_filter) if level_filter != 'ALL' else 'همه سطوح'
            },
            'level_statistics': level_stats
        }
        
        return {
            'type': 'trial_balance',
            'title': 'تراز آزمایشی',
            'data': trial_balance_data
        }
        
    except Exception as e:
        logger.error(f"خطا در تولید تراز آزمایشی با فیلتر: {e}")
        return {
            'type': 'trial_balance',
            'title': 'تراز آزمایشی',
            'data': {'error': f'خطا در تولید گزارش: {str(e)}'}
        }

def _get_level_display(level_code):
    """نمایش فارسی سطح حساب"""
    level_map = {
        'CLASS': 'گروه (کل)',
        'SUBCLASS': 'معین',
        'DETAIL': 'تفصیلی',
        'PROJECT': 'پروژه',
        'COST_CENTER': 'مرکز هزینه',
        'ALL': 'همه سطوح'
    }
    return level_map.get(level_code, level_code)

def _calculate_level_statistics(accounts_data):
    """محاسبه آمار سطح‌های حساب"""
    level_stats = {}
    
    for account in accounts_data:
        level = account['account_level']
        if level not in level_stats:
            level_stats[level] = {
                'count': 0,
                'total_debit': 0,
                'total_credit': 0,
                'display_name': account['account_level_display']
            }
        
        level_stats[level]['count'] += 1
        level_stats[level]['total_debit'] += account['debit']
        level_stats[level]['total_credit'] += account['credit']
    
    # محاسبه مانده برای هر سطح
    for level in level_stats:
        stats = level_stats[level]
        balance = stats['total_debit'] - stats['total_credit']
        stats['total_balance'] = abs(balance)
        stats['balance_type'] = 'بدهکار' if balance > 0 else 'بستانکار' if balance < 0 else 'صفر'
        stats['formatted_balance'] = f"{abs(balance):,.0f} ریال ({stats['balance_type']})"
        stats['formatted_debit'] = f"{stats['total_debit']:,.0f} ریال"
        stats['formatted_credit'] = f"{stats['total_credit']:,.0f} ریال"
    
    return level_stats

@login_required
def trial_balance_api(request):
    """API برای دریافت تراز آزمایشی"""
    if request.method == 'GET':
        try:
            company_id = request.session.get('current_company_id')
            period_id = request.session.get('current_period_id')
            
            if not company_id or not period_id:
                return JsonResponse({'error': 'شرکت و دوره مالی انتخاب نشده'}, status=400)
            
            # دریافت پارامترهای فیلتر
            level_filter = request.GET.get('level', 'ALL')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            
            # اعتبارسنجی تاریخ‌ها
            try:
                if start_date:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                if end_date:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = None
                end_date = None
            
            # تولید گزارش
            report_data = _generate_trial_balance_with_filters(
                company_id, period_id, level_filter, start_date, end_date
            )
            
            return JsonResponse(report_data)
            
        except Exception as e:
            logger.error(f"خطا در API تراز آزمایشی: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'متد غیرمجاز'}, status=405)

@login_required
def export_trial_balance(request):
    """خروجی تراز آزمایشی"""
    company_id = request.session.get('current_company_id')
    period_id = request.session.get('current_period_id')
    
    if not company_id or not period_id:
        messages.error(request, 'لطفاً ابتدا شرکت و دوره مالی را انتخاب کنید.')
        return redirect('financial_system:trial_balance')
    
    # دریافت پارامترهای فیلتر
    level_filter = request.GET.get('level', 'ALL')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    try:
        # تولید گزارش
        report_data = _generate_trial_balance_with_filters(
            company_id, period_id, level_filter, start_date, end_date
        )
        
        # در اینجا می‌توانید خروجی Excel یا PDF تولید کنید
        # فعلاً فقط JSON برمی‌گردانیم
        response = JsonResponse(report_data)
        response['Content-Disposition'] = f'attachment; filename="trial_balance_{timezone.now().strftime("%Y%m%d_%H%M")}.json"'
        return response
        
    except Exception as e:
        logger.error(f"خطا در خروجی تراز آزمایشی: {e}")
        messages.error(request, f'خطا در تولید خروجی: {str(e)}')
        return redirect('financial_system:trial_balance')
