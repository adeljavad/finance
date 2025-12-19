"""
سیستم طبقه‌بندی سوالات مالی - نسخه ساده‌تر
برای تشخیص اولیه نوع سوال و انتخاب مسیر مناسب
"""

import re
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FinancialQuestionClassifier:
    """سیستم طبقه‌بندی سوالات مالی"""
    
    def __init__(self):
        # کلمات کلیدی برای تشخیص نوع سوال
        self.general_finance_keywords = [
            'مالیات', 'حسابداری', 'حسابدار', 'مالی', 'بودجه', 'هزینه', 'درآمد',
            'سود', 'زیان', 'دارایی', 'بدهی', 'سرمایه', 'ترازنامه', 'صورت مالی',
            'نقدینگی', 'نسبت مالی', 'حاشیه سود', 'بازده', 'سرمایه‌گذاری',
            'استاندارد', 'قانون', 'مقررات', 'حسابرسی', 'کنترل داخلی',
            'چطور', 'چگونه', 'روش', 'نحوه', 'طریقه', 'راهنمایی'
        ]
        
        self.data_related_keywords = [
            'سند', 'اسناد', 'داده', 'دیتا', 'فایل', 'آپلود', 'تاریخ', 'بدهکار', 
            'بستانکار', 'معین', 'تفصیلی', 'تراز', 'مانده', 'جمع', 'میانگین',
            'بیشترین', 'کمترین', 'تعداد', 'شرح', 'توضیحات', 'مبلغ', 'ریال',
            'جستجو', 'پیدا کن', 'بیاب', 'نمایش', 'فیلتر', 'شرط', 'محدودیت',
            'محاسبه', 'جمع', 'میانگین', 'مجموع', 'تعداد', 'تحلیل', 'بررسی'
        ]
        
        self.greeting_keywords = [
            'سلام', 'درود', 'عرض ادب', 'وقت بخیر', 'خوش آمدید', 'صبخ بخیر',
            'عصر بخیر', 'شب بخیر', 'حالتون چطوره', 'خوبی', 'خوبید'
        ]
        
        self.help_keywords = [
            'کمک', 'راهنما', 'راهنمایی', 'چه کار', 'چکار', 'چیکار',
            'چه کاری', 'چه کارهایی', 'امکانات', 'خدمات', 'توانایی',
            'می‌تونی', 'می‌توانی', 'می‌شه', 'می‌شود'
        ]
    
    def classify(self, question: str) -> Dict[str, Any]:
        """
        طبقه‌بندی سوال مالی
        
        Returns:
            Dict با اطلاعات طبقه‌بندی
        """
        question_lower = question.lower().strip()
        
        # 1. بررسی احوال‌پرسی
        if self._is_greeting(question_lower):
            return {
                'category': 'greeting',
                'is_financial': False,
                'confidence': 0.9,
                'reasoning': 'تشخیص احوال‌پرسی'
            }
        
        # 2. بررسی درخواست راهنما
        if self._is_help_request(question_lower):
            return {
                'category': 'help',
                'is_financial': False,
                'confidence': 0.8,
                'reasoning': 'تشخیص درخواست راهنما'
            }
        
        # 3. بررسی سوالات مرتبط با داده
        data_related_score = self._calculate_data_related_score(question_lower)
        general_finance_score = self._calculate_general_finance_score(question_lower)
        
        if data_related_score > general_finance_score:
            return {
                'category': 'data_related',
                'is_financial': True,
                'confidence': data_related_score,
                'reasoning': 'سوال مرتبط با داده‌های مالی کاربر',
                'needs_tool': True
            }
        elif general_finance_score > 0:
            return {
                'category': 'general_finance',
                'is_financial': True,
                'confidence': general_finance_score,
                'reasoning': 'سوال عمومی مالی',
                'needs_tool': False
            }
        else:
            return {
                'category': 'general',
                'is_financial': False,
                'confidence': 0.5,
                'reasoning': 'سوال عمومی غیرمالی',
                'needs_tool': False
            }
    
    def _is_greeting(self, question_lower: str) -> bool:
        """تشخیص احوال‌پرسی"""
        for keyword in self.greeting_keywords:
            if keyword in question_lower:
                return True
        return False
    
    def _is_help_request(self, question_lower: str) -> bool:
        """تشخیص درخواست راهنما"""
        for keyword in self.help_keywords:
            if keyword in question_lower:
                return True
        
        # بررسی سوالات کوتاه راهنما
        short_help_patterns = [
            r'^چه$', r'^چی$', r'^کمک$', r'^راهنما$',
            r'^help$', r'^what$', r'^how$'
        ]
        
        for pattern in short_help_patterns:
            if re.match(pattern, question_lower):
                return True
        
        return False
    
    def _calculate_data_related_score(self, question_lower: str) -> float:
        """محاسبه امتیاز مرتبط بودن با داده"""
        score = 0.0
        
        for keyword in self.data_related_keywords:
            if keyword in question_lower:
                score += 0.1
        
        # محدود کردن امتیاز به 1.0
        return min(score, 1.0)
    
    def _calculate_general_finance_score(self, question_lower: str) -> float:
        """محاسبه امتیاز عمومی مالی"""
        score = 0.0
        
        for keyword in self.general_finance_keywords:
            if keyword in question_lower:
                score += 0.1
        
        # محدود کردن امتیاز به 1.0
        return min(score, 1.0)
    
    def is_data_related(self, question: str) -> bool:
        """تشخیص سریع اینکه آیا سوال مرتبط با داده است"""
        classification = self.classify(question)
        return classification['category'] == 'data_related'
    
    def is_general_finance(self, question: str) -> bool:
        """تشخیص سریع اینکه آیا سوال عمومی مالی است"""
        classification = self.classify(question)
        return classification['category'] == 'general_finance'
    
    def get_financial_fallback_response(self, question: str) -> str:
        """پاسخ fallback برای سوالات مالی نامشخص"""
        classification = self.classify(question)
        
        if classification['category'] == 'greeting':
            return "سلام! من دستیار مالی شما هستم. چطور می‌توانم کمک کنم؟"
        
        elif classification['category'] == 'help':
            return """من یک دستیار مالی هوشمند هستم و می‌توانم در زمینه‌های زیر کمک کنم:

📊 **تحلیل داده‌های مالی شما:**
• جستجو در اسناد حسابداری
• محاسبات مالی و آماری
• تحلیل الگوها و روندها
• فیلتر کردن داده‌ها بر اساس شرایط مختلف

💡 **پاسخ به سوالات مالی عمومی:**
• حسابداری و استانداردها
• مالیات و قوانین
• حسابرسی و کنترل داخلی
• نسبت‌های مالی و تحلیل‌ها

📁 **برای استفاده از تحلیل داده‌ها، ابتدا فایل Excel اسناد خود را آپلود کنید.**
سوال مالی خود را بپرسید!"""
        
        elif classification['category'] == 'data_related':
            return "برای پاسخ به این سوال نیاز به تحلیل داده‌های مالی شما دارم. لطفاً ابتدا فایل Excel اسناد خود را آپلود کنید."
        
        elif classification['category'] == 'general_finance':
            return "سوال مالی خوبی پرسیدید! لطفاً صبر کنید تا پاسخ تخصصی شما را آماده کنم."
        
        else:
            return "سلام! من یک دستیار مالی هوشمند هستم. می‌توانم در امور مالی و حسابداری به شما کمک کنم. سوال مالی خود را بپرسید!"


# توابع اصلی برای استفاده در سیستم
def classify_financial_question(question: str) -> Dict[str, Any]:
    """تابع اصلی برای طبقه‌بندی سوالات مالی"""
    classifier = FinancialQuestionClassifier()
    return classifier.classify(question)


def get_financial_fallback_response(question: str) -> str:
    """دریافت پاسخ fallback برای سوالات مالی"""
    classifier = FinancialQuestionClassifier()
    return classifier.get_financial_fallback_response(question)


def is_data_related_question(question: str) -> bool:
    """تشخیص اینکه آیا سوال مرتبط با داده است"""
    classifier = FinancialQuestionClassifier()
    return classifier.is_data_related(question)


def is_general_finance_question(question: str) -> bool:
    """تشخیص اینکه آیا سوال عمومی مالی است"""
    classifier = FinancialQuestionClassifier()
    return classifier.is_general_finance(question)
