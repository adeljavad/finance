"""
سیستم طبقه‌بندی هوشمند با استفاده از مدل‌های هوش مصنوعی
برای تشخیص دقیق‌تر قصد کاربر و انتخاب ابزار مناسب
نسخه سازگار با assistant (MVP)
"""

import re
import json
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)

# توضیحات ابزارهای موجود در assistant
ASSISTANT_TOOL_DESCRIPTIONS = {
    "document_search": {
        "name": "جستجوی اسناد",
        "description": "جستجو در اسناد حسابداری بر اساس تاریخ، مبلغ، شرح و غیره",
        "examples": ["اسناد تاریخ 1403/01/01 را پیدا کن", "سند با مبلغ 1000000 را جستجو کن"]
    },
    "advanced_filter": {
        "name": "فیلتر پیشرفته",
        "description": "فیلتر کردن داده‌ها بر اساس شرایط مختلف",
        "examples": ["اسناد با مبلغ بیشتر از 5000000 را فیلتر کن", "اسناد بدهکار را نشان بده"]
    },
    "data_calculator": {
        "name": "ماشین حساب داده",
        "description": "محاسبات آماری و مالی روی داده‌ها",
        "examples": ["جمع بدهکارها را محاسبه کن", "میانگین مبالغ را بگو"]
    },
    "pattern_analysis": {
        "name": "تحلیل الگو",
        "description": "تحلیل الگوها و روندها در داده‌های مالی",
        "examples": ["روند ماهانه درآمدها را تحلیل کن", "الگوی هزینه‌ها را بررسی کن"]
    },
    "dynamic_tool": {
        "name": "ابزار داینامیک",
        "description": "ابزارهای تولید شده به صورت پویا برای تحلیل‌های خاص",
        "examples": ["تحلیل سفارشی بر اساس نیاز کاربر"]
    }
}

class AIToolClassifier:
    """سیستم طبقه‌بندی هوشمند با استفاده از مدل‌های AI"""
    
    def __init__(self):
        self.tool_descriptions = ASSISTANT_TOOL_DESCRIPTIONS
        
        # الگوهای پیشرفته برای تشخیص قصد کاربر
        self.intent_patterns = {
            "document_search": [
                r'.*(جستجو|پیدا کن|بیاب|نمایش).*(سند|اسناد|داده|دیتا).*',
                r'.*(کدام|چه).*(سند|اسناد).*(تاریخ|مبلغ).*',
                r'.*(سند|اسناد).*(تاریخ|ماه|سال).*',
                r'.*(نمایش|نشان دادن).*(همه|تمام).*(سند|اسناد).*'
            ],
            "advanced_filter": [
                r'.*(فیلتر|شرط|محدودیت).*(اعمال|اعمال کن|بگذار).*',
                r'.*(اسناد|داده).*(بیشتر|کمتر|بزرگتر|کوچکتر).*(از|از مقدار).*',
                r'.*(فقط|تنها).*(اسناد|داده).*(بدهکار|بستانکار).*',
                r'.*(شرایط|محدودیت).*(خاص|ویژه).*(اعمال).*'
            ],
            "data_calculator": [
                r'.*(محاسبه|جمع|میانگین|مجموع|تعداد).*(بدهکار|بستانکار|مبلغ).*',
                r'.*(چند|چقدر|چه مقدار).*(سند|اسناد).*(وجود|هست).*',
                r'.*(آمار|آماره).*(داده|اسناد).*(محاسبه).*',
                r'.*(جمع کل|مجموع کل|میانگین کل).*(را).*(بگو|محاسبه کن).*'
            ],
            "pattern_analysis": [
                r'.*(تحلیل|بررسی|مطالعه).*(الگو|روند|رفتار).*',
                r'.*(چگونه|چطور).*(تغییر|تغییرات).*(داده|اسناد).*',
                r'.*(مقایسه|سنجش).*(ماه|فصل|دوره).*(با|با هم).*',
                r'.*(روند|ترند).*(زمانی|تاریخی).*(نمایش|نشان بده).*'
            ],
            "dynamic_tool": [
                r'.*(تحلیل|آنالیز|بررسی).*(خاص|ویژه|سفارشی).*',
                r'.*(نیاز|درخواست).*(منحصربه‌فرد|خاص).*(دارم).*',
                r'.*(هیچ|هیچکدام).*(ابزار|ابزارهای).*(موجود).*(مناسب).*',
                r'.*(سوال|پرسش).*(پیچیده|پیشرفته).*(دارم).*'
            ]
        }
        
        # کلمات کلیدی با وزن‌های مختلف
        self.weighted_keywords = {
            "document_search": {
                "جستجو": 3.0, "پیدا کن": 3.0, "بیاب": 2.5, "نمایش": 2.0,
                "سند": 2.5, "اسناد": 2.5, "داده": 2.0, "دیتا": 2.0,
                "تاریخ": 1.5, "مبلغ": 1.5, "شرح": 1.5
            },
            "advanced_filter": {
                "فیلتر": 3.0, "شرط": 2.5, "محدودیت": 2.5, "اعمال کن": 2.0,
                "بیشتر": 1.5, "کمتر": 1.5, "بزرگتر": 1.5, "کوچکتر": 1.5,
                "فقط": 1.5, "تنها": 1.5, "بدهکار": 1.5, "بستانکار": 1.5
            },
            "data_calculator": {
                "محاسبه": 3.0, "جمع": 2.5, "میانگین": 2.5, "مجموع": 2.5,
                "تعداد": 2.0, "چند": 2.0, "چقدر": 2.0, "چه مقدار": 2.0,
                "آمار": 2.0, "آماره": 2.0, "جمع کل": 2.5, "مجموع کل": 2.5
            },
            "pattern_analysis": {
                "تحلیل": 3.0, "بررسی": 2.5, "مطالعه": 2.0, "الگو": 2.5,
                "روند": 2.5, "رفتار": 2.0, "چگونه": 1.5, "چطور": 1.5,
                "تغییر": 1.5, "تغییرات": 1.5, "مقایسه": 2.0, "سنجش": 2.0
            },
            "dynamic_tool": {
                "خاص": 3.0, "ویژه": 3.0, "سفارشی": 3.0, "منحصربه‌فرد": 2.5,
                "پیچیده": 2.0, "پیشرفته": 2.0, "هیچکدام": 2.5, "مناسب": 2.0
            }
        }
    
    def _calculate_semantic_similarity(self, question: str, tool_keywords: List[str]) -> float:
        """
        محاسبه شباهت معنایی بین سوال و کلمات کلیدی ابزار
        """
        question_lower = question.lower()
        score = 0.0
        
        for keyword in tool_keywords:
            if keyword in question_lower:
                # امتیاز بر اساس طول کلمه کلیدی (کلمات طولانی‌تر وزن بیشتری دارند)
                weight = len(keyword) * 0.1
                score += weight
        
        return min(score, 1.0)
    
    def _match_intent_patterns(self, question: str) -> Dict[str, float]:
        """مطابقت الگوهای قصد کاربر"""
        question_lower = question.lower()
        pattern_scores = {}
        
        for tool_name, patterns in self.intent_patterns.items():
            tool_score = 0.0
            for pattern in patterns:
                if re.match(pattern, question_lower):
                    tool_score += 0.3  # امتیاز برای هر الگوی مطابقت‌یافته
            
            pattern_scores[tool_name] = min(tool_score, 1.0)
        
        return pattern_scores
    
    def _calculate_keyword_scores(self, question: str) -> Dict[str, float]:
        """محاسبه امتیاز کلمات کلیدی با وزن"""
        question_lower = question.lower()
        keyword_scores = {}
        
        for tool_name, keywords in self.weighted_keywords.items():
            tool_score = 0.0
            for keyword, weight in keywords.items():
                if keyword in question_lower:
                    tool_score += weight
            
            # نرمال‌سازی امتیاز
            max_possible_score = sum(keywords.values())
            if max_possible_score > 0:
                keyword_scores[tool_name] = min(tool_score / max_possible_score, 1.0)
            else:
                keyword_scores[tool_name] = 0.0
        
        return keyword_scores
    
    def _analyze_question_structure(self, question: str) -> Dict[str, float]:
        """تحلیل ساختار سوال برای تشخیص قصد"""
        question_lower = question.lower()
        structure_scores = {}
        
        # تشخیص سوالات جستجو
        if any(word in question_lower for word in ['جستجو', 'پیدا کن', 'بیاب', 'نمایش']):
            structure_scores["document_search"] = 0.4
        
        # تشخیص سوالات فیلتر
        if any(word in question_lower for word in ['فیلتر', 'شرط', 'محدودیت']):
            structure_scores["advanced_filter"] = 0.5
        
        # تشخیص سوالات محاسباتی
        if any(word in question_lower for word in ['محاسبه', 'جمع', 'میانگین', 'تعداد']):
            structure_scores["data_calculator"] = 0.6
        
        # تشخیص سوالات تحلیلی
        if any(word in question_lower for word in ['تحلیل', 'بررسی', 'مطالعه', 'روند']):
            structure_scores["pattern_analysis"] = 0.5
        
        # تشخیص سوالات خاص/سفارشی
        if any(word in question_lower for word in ['خاص', 'ویژه', 'سفارشی', 'منحصربه‌فرد']):
            structure_scores["dynamic_tool"] = 0.7
        
        return structure_scores
    
    def classify_with_ai(self, question: str) -> Dict[str, Any]:
        """
        طبقه‌بندی سوال با استفاده از الگوریتم‌های هوشمند
        
        Returns:
            Dict با اطلاعات طبقه‌بندی پیشرفته
        """
        # محاسبه امتیازهای مختلف
        pattern_scores = self._match_intent_patterns(question)
        keyword_scores = self._calculate_keyword_scores(question)
        structure_scores = self._analyze_question_structure(question)
        
        # محاسبه امتیاز نهایی برای هر ابزار
        final_scores = {}
        for tool_name in self.tool_descriptions.keys():
            pattern_score = pattern_scores.get(tool_name, 0.0)
            keyword_score = keyword_scores.get(tool_name, 0.0)
            structure_score = structure_scores.get(tool_name, 0.0)
            
            # ترکیب امتیازها با وزن‌های مختلف
            final_score = (
                pattern_score * 0.4 +      # الگوها مهم‌ترین هستند
                keyword_score * 0.3 +      # کلمات کلیدی
                structure_score * 0.3      # ساختار سوال
            )
            
            final_scores[tool_name] = final_score
        
        # انتخاب ابزار با بالاترین امتیاز
        best_tool = max(final_scores.items(), key=lambda x: x[1])
        best_tool_name, best_tool_score = best_tool
        
        # تشخیص اینکه آیا سوال نیاز به ابزار دارد
        needs_tool = best_tool_score >= 0.3
        
        # تولید توضیحات برای تصمیم
        decision_explanation = self._generate_decision_explanation(
            question, best_tool_name, best_tool_score, final_scores
        )
        
        # تعیین category بر اساس نیاز به ابزار
        if needs_tool:
            category = 'data_related'
        else:
            # بررسی اینکه آیا سوال عمومی مالی است
            general_finance_keywords = [
                'مالیات', 'حسابداری', 'حسابدار', 'مالی', 'بودجه', 'هزینه', 'درآمد',
                'سود', 'زیان', 'دارایی', 'بدهی', 'سرمایه', 'ترازنامه', 'صورت مالی',
                'نقدینگی', 'نسبت مالی', 'حاشیه سود', 'بازده', 'سرمایه‌گذاری'
            ]
            question_lower = question.lower()
            has_finance_keywords = any(keyword in question_lower for keyword in general_finance_keywords)
            
            if has_finance_keywords:
                category = 'general_finance'
            else:
                category = 'general'
        
        return {
            'category': category,
            'needs_tool': needs_tool,
            'suggested_tool': best_tool_name if needs_tool else None,
            'confidence': best_tool_score,
            'all_scores': final_scores,
            'decision_explanation': decision_explanation,
            'tool_description': self.tool_descriptions.get(best_tool_name, {}) if needs_tool else None
        }
    
    def _generate_decision_explanation(self, question: str, best_tool: str, 
                                     best_score: float, all_scores: Dict[str, float]) -> str:
        """تولید توضیحات برای تصمیم طبقه‌بندی"""
        if best_score < 0.3:
            return "سوال به اندازه کافی مشخص نیست یا نیاز به ابزار خاصی ندارد."
        
        tool_desc = self.tool_descriptions.get(best_tool, {})
        tool_name = tool_desc.get('name', best_tool)
        
        explanation = f"سوال شما مربوط به '{tool_name}' تشخیص داده شد. "
        explanation += f"امتیاز اطمینان: {best_score:.2f}\n\n"
        
        # اضافه کردن کلمات کلیدی پیدا شده
        question_lower = question.lower()
        found_keywords = []
        for keyword in self.weighted_keywords.get(best_tool, {}).keys():
            if keyword in question_lower:
                found_keywords.append(keyword)
        
        if found_keywords:
            explanation += f"کلمات کلیدی پیدا شده: {', '.join(found_keywords)}\n"
        
        # اضافه کردن رقیب‌های نزدیک
        competitors = [(tool, score) for tool, score in all_scores.items() 
                      if tool != best_tool and score > 0.2]
        if competitors:
            competitors.sort(key=lambda x: x[1], reverse=True)
            explanation += f"ابزارهای جایگزین: {', '.join([f'{tool}({score:.2f})' for tool, score in competitors[:2]])}"
        
        return explanation
    
    def get_tool_recommendations(self, question: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """دریافت لیست توصیه‌های ابزار"""
        classification = self.classify_with_ai(question)
        
        if not classification['needs_tool']:
            return []
        
        all_scores = classification['all_scores']
        recommendations = []
        
        for tool_name, score in sorted(all_scores.items(), key=lambda x: x[1], reverse=True):
            if score > 0.1:  # فقط ابزارهایی با امتیاز قابل توجه
                tool_desc = self.tool_descriptions.get(tool_name, {})
                recommendations.append({
                    'tool_name': tool_name,
                    'display_name': tool_desc.get('name', tool_name),
                    'confidence': score,
                    'description': tool_desc.get('description', ''),
                    'examples': tool_desc.get('examples', [])
                })
        
        return recommendations[:top_k]
    
    def is_data_related_query(self, question: str) -> bool:
        """
        تشخیص اینکه آیا سوال مربوط به داده‌های مالی است یا سوال عمومی مالی
        
        Returns:
            True: سوال روی دیتای مالی (نیاز به ابزار دارد)
            False: سوال عمومی مالی (نیاز به LLM مستقیم دارد)
        """
        classification = self.classify_with_ai(question)
        
        # اگر نیاز به ابزار دارد، سوال روی دیتای مالی است
        if classification['needs_tool']:
            return True
        
        # کلمات کلیدی عمومی مالی
        general_finance_keywords = [
            'مالیات', 'حسابداری', 'حسابدار', 'مالی', 'بودجه', 'هزینه', 'درآمد',
            'سود', 'زیان', 'دارایی', 'بدهی', 'سرمایه', 'ترازنامه', 'صورت مالی',
            'نقدینگی', 'نسبت مالی', 'حاشیه سود', 'بازده', 'سرمایه‌گذاری',
            'استاندارد', 'قانون', 'مقررات', 'حسابرسی', 'کنترل داخلی'
        ]
        
        question_lower = question.lower()
        has_finance_keywords = any(keyword in question_lower for keyword in general_finance_keywords)
        
        # اگر کلمات کلیدی مالی دارد اما نیاز به ابزار ندارد، سوال عمومی مالی است
        if has_finance_keywords:
            return False
        
        # در غیر این صورت، سوال عمومی غیرمالی است
        return False


# تابع اصلی برای استفاده در سیستم
def classify_financial_question_ai(question: str) -> Dict[str, Any]:
    """تابع اصلی برای طبقه‌بندی هوشمند سوالات مالی"""
    classifier = AIToolClassifier()
    return classifier.classify_with_ai(question)


def get_tool_recommendations_ai(question: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """دریافت لیست توصیه‌های ابزار با استفاده از AI"""
    classifier = AIToolClassifier()
    return classifier.get_tool_recommendations(question, top_k)


def is_data_related_query_ai(question: str) -> bool:
    """تشخیص اینکه آیا سوال مربوط به داده‌های مالی است یا سوال عمومی مالی"""
    classifier = AIToolClassifier()
    return classifier.is_data_related_query(question)
