# financial_system/tools/ai_classifier.py
"""
سیستم طبقه‌بندی هوشمند با استفاده از مدل‌های هوش مصنوعی
برای تشخیص دقیق‌تر قصد کاربر و انتخاب ابزار مناسب
"""

import re
import json
from typing import Dict, List, Tuple, Any
from .financial_analysis_tools import TOOL_DESCRIPTIONS

class AIToolClassifier:
    """سیستم طبقه‌بندی هوشمند با استفاده از مدل‌های AI"""
    
    def __init__(self):
        self.tool_descriptions = TOOL_DESCRIPTIONS
        
        # الگوهای پیشرفته برای تشخیص قصد کاربر
        self.intent_patterns = {
            "analyze_ratios": [
                r'.*(نسبت|تحلیل|محاسبه).*(مالی|نقدینگی|سودآوری|اهرم|کارایی).*',
                r'.*(وضعیت|چگونه).*(نقدینگی|سودآوری|بازده).*',
                r'.*(نسبت جاری|نسبت آنی|بازده دارایی|بازده حقوق).*',
                r'.*(تحلیل مالی|نسبت‌های مالی|شاخص‌های مالی).*'
            ],
            "detect_anomalies": [
                r'.*(انحراف|مشکوک|مغایرت|نامتعادل).*(مالی|حساب|سند).*',
                r'.*(کنترل|بررسی).*(داخلی|مالی|اسناد).*',
                r'.*(گردش|معامله).*(غیرعادی|بزرگ|مشکوک).*',
                r'.*(شناسایی|پیدا کردن).*(مشکل|خطا|انحراف).*'
            ],
            "generate_report": [
                r'.*(گزارش|ترازنامه|صورت).*(مالی|سود و زیان|جریان نقد).*',
                r'.*(تولید|نمایش|نشان دادن).*(گزارش|ترازنامه|صورت مالی).*',
                r'.*(گزارش مالی|صورت مالی|ترازنامه).*',
                r'.*(سود و زیان|جریان نقدی).*'
            ],
            "four_column_balance": [
                r'.*(چهارستونی|چهار ستون|تراز کل|تراز چهارستونی|تراز چهار ستونی).*',
                r'.*(گردش|مانده).*(حساب|سرفصل).*',
                r'.*(تراز).*(کل|چهارستونی).*',
                r'.*(بدهکار|بستانکار|گردش حساب).*'
            ],
            "seasonal_analysis": [
                r'.*(فصلی|فصل|بهار|تابستان|پاییز|زمستان|عملکرد فصلی).*(عملکرد|تحلیل).*',
                r'.*(عملکرد|مقایسه).*(فصلی|فصل).*',
                r'.*(فصل).*(عملکرد|درآمد|سود).*',
                r'.*(مقایسه).*(فصل|فصلی).*(سال قبل).*'
            ],
            "comprehensive_report": [
                r'.*(جامع|کامل|کلی|گزارش جامع).*(گزارش|تحلیل|وضعیت).*',
                r'.*(گزارش|تحلیل).*(کامل|جامع|کلی).*',
                r'.*(وضعیت|تحلیل).*(مالی|کلی).*',
                r'.*(گزارش کامل|تحلیل جامع).*'
            ]
        }
        
        # کلمات کلیدی با وزن‌های مختلف
        self.weighted_keywords = {
            "analyze_ratios": {
                "نسبت": 3.0, "تحلیل": 2.5, "نقدینگی": 2.0, "سودآوری": 2.0,
                "بازده": 2.0, "اهرم": 1.5, "کارایی": 1.5, "نسبت جاری": 3.0,
                "نسبت آنی": 3.0, "بازده دارایی": 3.0, "بازده حقوق": 3.0
            },
            "detect_anomalies": {
                "انحراف": 3.0, "مشکوک": 3.0, "کنترل": 2.5, "مغایرت": 2.5,
                "نامتعادل": 2.0, "گردش غیرعادی": 3.0, "اسناد مشکوک": 3.0
            },
            "generate_report": {
                "گزارش": 2.5, "ترازنامه": 3.0, "صورت مالی": 3.0, "سود و زیان": 3.0,
                "جریان نقد": 3.0, "تولید گزارش": 3.0
            },
            "four_column_balance": {
                "چهارستونی": 3.0, "چهار ستون": 3.0, "تراز کل": 3.0, "تراز چهارستونی": 3.0, "تراز چهار ستونی": 3.0,
                "گردش حساب": 2.5, "مانده": 2.0, "بدهکار": 2.0, "بستانکار": 2.0
            },
            "seasonal_analysis": {
                "فصلی": 3.0, "فصل": 2.5, "بهار": 2.0, "تابستان": 2.0,
                "پاییز": 2.0, "زمستان": 2.0, "عملکرد فصلی": 3.0
            },
            "comprehensive_report": {
                "جامع": 3.0, "کامل": 3.0, "گزارش کامل": 3.0, "گزارش جامع": 3.0, "تحلیل کلی": 2.5,
                "وضعیت مالی": 2.5
            }
        }
    
    def _calculate_semantic_similarity(self, question: str, tool_keywords: List[str]) -> float:
        """
        محاسبه شباهت معنایی بین سوال و کلمات کلیدی ابزار
        (در حالت واقعی از مدل‌های embedding استفاده می‌شود)
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
        
        # تشخیص سوالات تحلیلی
        if any(word in question_lower for word in ['چگونه', 'چطور', 'وضعیت', 'تحلیل']):
            structure_scores["analyze_ratios"] = 0.4
            structure_scores["comprehensive_report"] = 0.3
        
        # تشخیص سوالات گزارشی
        if any(word in question_lower for word in ['گزارش', 'نمایش', 'نشان', 'تولید']):
            structure_scores["generate_report"] = 0.5
            structure_scores["comprehensive_report"] = 0.4
        
        # تشخیص سوالات کنترلی
        if any(word in question_lower for word in ['کنترل', 'بررسی', 'شناسایی', 'پیدا']):
            structure_scores["detect_anomalies"] = 0.6
        
        # تشخیص سوالات فصلی
        if any(word in question_lower for word in ['فصل', 'فصلی', 'بهار', 'تابستان', 'پاییز', 'زمستان']):
            structure_scores["seasonal_analysis"] = 0.7
            structure_scores["four_column_balance"] = 0.3
        
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
        
        # تشخیص اینکه آیا سوال مالی است
        is_financial = best_tool_score >= 0.3
        
        # تولید توضیحات برای تصمیم
        decision_explanation = self._generate_decision_explanation(
            question, best_tool_name, best_tool_score, final_scores
        )
        
        return {
            'is_financial': is_financial,
            'suggested_tool': best_tool_name if is_financial else None,
            'confidence': best_tool_score,
            'all_scores': final_scores,
            'decision_explanation': decision_explanation,
            'tool_description': self.tool_descriptions.get(best_tool_name, {}) if is_financial else None
        }
    
    def _generate_decision_explanation(self, question: str, best_tool: str, 
                                     best_score: float, all_scores: Dict[str, float]) -> str:
        """تولید توضیحات برای تصمیم طبقه‌بندی"""
        if best_score < 0.3:
            return "سوال به اندازه کافی مشخص نیست یا مربوط به امور مالی نمی‌باشد."
        
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
        
        if not classification['is_financial']:
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


# تابع اصلی برای استفاده در سیستم
def classify_financial_question_ai(question: str) -> Dict[str, Any]:
    """تابع اصلی برای طبقه‌بندی هوشمند سوالات مالی"""
    classifier = AIToolClassifier()
    return classifier.classify_with_ai(question)


def get_tool_recommendations_ai(question: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """دریافت لیست توصیه‌های ابزار با استفاده از AI"""
    classifier = AIToolClassifier()
    return classifier.get_tool_recommendations(question, top_k)
