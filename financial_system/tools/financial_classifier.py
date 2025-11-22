# financial_system/tools/financial_classifier.py
import re
from typing import Dict, List, Tuple

class FinancialQuestionClassifier:
    """سیستم تشخیص سوالات مالی از سوالات عمومی"""
    
    def __init__(self):
        # دیکشنری جامع اصطلاحات مالی فارسی
        self.financial_keywords = {
            # اصطلاحات حسابداری و مالی
            'حساب', 'تراز', 'ترازنامه', 'سود', 'زیان', 'درآمد', 'هزینه', 'دارایی', 'بدهی',
            'حقوق صاحبان سهام', 'نقدینگی', 'نسبت', 'تحلیل', 'گزارش', 'صورت مالی',
            'جریان نقدی', 'سود و زیان', 'سودوزیان', 'انحراف', 'مشکوک', 'کنترل',
            
            # انواع حساب‌ها
            'صندوق', 'بانک', 'موجودی', 'کالا', 'دریافتنی', 'پرداختنی', 'وام', 'سرمایه',
            'فروش', 'خرید', 'هزینه عملیاتی', 'درآمد عملیاتی',
            
            # دوره‌های مالی
            'دوره', 'فصل', 'بهار', 'تابستان', 'پاییز', 'زمستان', 'ماه', 'سال',
            
            # انواع گزارش‌ها
            'گزارش مالی', 'گزارش حسابرسی', 'گزارش مدیریت', 'گزارش عملکرد',
            'تراز کل', 'چهارستونی', 'چهار ستون', 'فصلی', 'ماهانه', 'سالانه',
            
            # نسبت‌های مالی
            'نسبت جاری', 'نسبت آنی', 'نسبت نقدینگی', 'بازده دارایی', 'بازده حقوق',
            'حاشیه سود', 'اهرم', 'بدهی', 'سودآوری', 'نقدشوندگی',
            
            # عملیات مالی
            'معامله', 'گردش', 'مانده', 'اول دوره', 'انتهای دوره', 'بدهکار', 'بستانکار',
            'اسناد', 'آرتیکل', 'سند', 'ثبت', 'دفتر', 'کل', 'معین', 'تفصیلی'
        }
        
        # الگوهای سوالات مالی
        self.financial_patterns = [
            r'.*(تراز|گزارش|صورت).*(مالی|حساب|سود|زیان).*',
            r'.*(نسبت|تحلیل).*(مالی|حساب|سود|زیان).*',
            r'.*(مانده|گردش).*(حساب|صندوق|بانک).*',
            r'.*(انحراف|مشکوک).*(مالی|حساب).*',
            r'.*(عملکرد|گزارش).*(فصلی|ماهانه|سالانه).*',
            r'.*(چهارستونی|چهار ستون).*',
            r'.*(تراز کل|ترازنامه).*',
            r'.*(سود و زیان|سودوزیان).*',
            r'.*(جریان نقد|نقدی).*'
        ]
        
        # کلمات عمومی که نشان‌دهنده سوال غیرمالی هستند
        self.general_keywords = {
            'سلام', 'خداحافظ', 'تشکر', 'ممنون', 'لطفا', 'ببخشید', 'عذر', 'کمک',
            'راهنما', 'دستور', 'چگونه', 'چطور', 'کجا', 'کی', 'چه', 'چرا', 'چی',
            'کدام', 'آیا', 'میشه', 'می‌شود', 'می‌توان', 'می‌شه'
        }
    
    def is_financial_question(self, question: str) -> Tuple[bool, float, List[str]]:
        """
        تشخیص اینکه آیا سوال مالی است یا عمومی
        
        Returns:
            Tuple[bool, float, List[str]]: 
            - آیا سوال مالی است
            - امتیاز اطمینان (0-1)
            - کلمات کلیدی پیدا شده
        """
        question_lower = question.lower().strip()
        
        # شمارش کلمات کلیدی مالی
        financial_matches = []
        for keyword in self.financial_keywords:
            if keyword in question_lower:
                financial_matches.append(keyword)
        
        # بررسی الگوهای مالی
        pattern_matches = 0
        for pattern in self.financial_patterns:
            if re.match(pattern, question_lower):
                pattern_matches += 1
        
        # شمارش کلمات عمومی
        general_matches = []
        for keyword in self.general_keywords:
            if keyword in question_lower:
                general_matches.append(keyword)
        
        # محاسبه امتیاز
        keyword_score = len(financial_matches) * 0.3
        pattern_score = pattern_matches * 0.4
        general_penalty = len(general_matches) * 0.2
        
        total_score = max(0, min(1, keyword_score + pattern_score - general_penalty))
        
        # تصمیم نهایی
        is_financial = total_score >= 0.3
        
        return is_financial, total_score, financial_matches
    
    def classify_question_intent(self, question: str) -> Dict[str, any]:
        """
        طبقه‌بندی قصد کاربر از سوال
        
        Returns:
            Dict با اطلاعات طبقه‌بندی
        """
        is_financial, confidence, keywords = self.is_financial_question(question)
        
        result = {
            'is_financial': is_financial,
            'confidence': confidence,
            'keywords_found': keywords,
            'intent_type': 'general',
            'suggested_tool': None
        }
        
        if is_financial:
            # تشخیص نوع قصد مالی
            question_lower = question.lower()
            
            if any(word in question_lower for word in ['نسبت', 'تحلیل', 'نقدینگی']):
                result['intent_type'] = 'financial_analysis'
                result['suggested_tool'] = 'analyze_ratios'
            
            elif any(word in question_lower for word in ['انحراف', 'مشکوک', 'کنترل']):
                result['intent_type'] = 'anomaly_detection'
                result['suggested_tool'] = 'detect_anomalies'
            
            elif any(word in question_lower for word in ['ترازنامه', 'صورت مالی', 'گزارش مالی']):
                result['intent_type'] = 'financial_report'
                result['suggested_tool'] = 'generate_report'
            
            elif any(word in question_lower for word in ['چهارستونی', 'چهار ستون', 'تراز کل', 'تراز چهارستونی', 'تراز چهار ستونی']):
                result['intent_type'] = 'four_column_balance'
                result['suggested_tool'] = 'four_column_balance'
            
            elif any(word in question_lower for word in ['فصلی', 'فصل', 'بهار', 'تابستان', 'پاییز', 'زمستان', 'عملکرد فصلی']):
                result['intent_type'] = 'seasonal_analysis'
                result['suggested_tool'] = 'seasonal_analysis'
            
            elif any(word in question_lower for word in ['جامع', 'کامل', 'گزارش کامل', 'گزارش جامع', 'تحلیل کلی']):
                result['intent_type'] = 'comprehensive_report'
                result['suggested_tool'] = 'comprehensive_report'
            
            else:
                result['intent_type'] = 'general_financial'
                result['suggested_tool'] = 'comprehensive_report'
        
        return result
    
    def get_fallback_response(self, question: str) -> str:
        """
        تولید پاسخ مناسب برای سوالات غیرمالی
        """
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['سلام', 'درود', 'سلامتی']):
            return "سلام! من دستیار مالی شما هستم. چگونه می‌توانم در زمینه مسائل مالی به شما کمک کنم؟"
        
        elif any(word in question_lower for word in ['تشکر', 'ممنون', 'مرسی']):
            return "خوشحالم که می‌توانم کمک کنم! اگر سوال مالی دیگری دارید، در خدمت شما هستم."
        
        elif any(word in question_lower for word in ['کمک', 'راهنما', 'دستور']):
            return """من یک دستیار مالی هوشمند هستم. می‌توانم در زمینه‌های زیر به شما کمک کنم:

📊 تحلیل نسبت‌های مالی
🔍 شناسایی انحرافات مالی  
📈 تولید گزارش‌های مالی
📋 ترازنامه چهارستونی
📅 تحلیل عملکرد فصلی

لطفاً سوال مالی خود را مطرح کنید."""

        else:
            return "متأسفانه من فقط می‌توانم به سوالات مالی پاسخ دهم. لطفاً سوال مالی خود را مطرح کنید."


# تابع اصلی برای استفاده در سیستم
def classify_financial_question(question: str) -> Dict[str, any]:
    """تابع اصلی برای طبقه‌بندی سوالات مالی"""
    classifier = FinancialQuestionClassifier()
    return classifier.classify_question_intent(question)


def get_financial_fallback_response(question: str) -> str:
    """تابع اصلی برای دریافت پاسخ fallback"""
    classifier = FinancialQuestionClassifier()
    return classifier.get_fallback_response(question)
