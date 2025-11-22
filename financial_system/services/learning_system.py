# financial_system/services/learning_system.py
"""
تسک ۹۴: ایجاد سیستم یادگیری از تاریخچه
این سرویس برای یادگیری از تاریخچه تعاملات کاربران و بهبود عملکرد چت بات طراحی شده است.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
from users.models import User, Company, FinancialPeriod


class LearningSystem:
    """سیستم یادگیری از تاریخچه"""
    
    def __init__(self):
        self.learning_data = {}
    
    def analyze_interaction_history(self, user_id: int, days_back: int = 30) -> Dict[str, Any]:
        """تحلیل تاریخچه تعاملات کاربر"""
        
        try:
            # دریافت تاریخچه چت کاربر
            start_date = datetime.now() - timedelta(days=days_back)
            chat_history = ChatHistory.objects.filter(
                user_id=user_id,
                created_at__gte=start_date
            ).order_by('created_at')
            
            # تحلیل الگوهای تعامل
            interaction_patterns = self._analyze_interaction_patterns(chat_history)
            
            # تحلیل ترجیحات کاربر
            user_preferences = self._analyze_user_preferences(chat_history)
            
            # تحلیل عملکرد سیستم
            system_performance = self._analyze_system_performance(chat_history)
            
            # شناسایی حوزه‌های بهبود
            improvement_areas = self._identify_improvement_areas(interaction_patterns, system_performance)
            
            return {
                'success': True,
                'user_id': user_id,
                'analysis_period': f'{days_back} روز گذشته',
                'total_interactions': len(chat_history),
                'interaction_patterns': interaction_patterns,
                'user_preferences': user_preferences,
                'system_performance': system_performance,
                'improvement_areas': improvement_areas,
                'recommendations': self._generate_learning_recommendations(
                    interaction_patterns, user_preferences, improvement_areas
                )
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_interaction_patterns(self, chat_history: List[ChatHistory]) -> Dict[str, Any]:
        """تحلیل الگوهای تعامل کاربر"""
        
        if not chat_history:
            return {
                'frequency': 'بدون تعامل',
                'preferred_times': [],
                'session_lengths': [],
                'top_categories': []
            }
        
        # تحلیل فرکانس تعامل
        frequency_analysis = self._analyze_interaction_frequency(chat_history)
        
        # تحلیل زمان‌های ترجیحی
        preferred_times = self._analyze_preferred_times(chat_history)
        
        # تحلیل طول جلسات
        session_lengths = self._analyze_session_lengths(chat_history)
        
        # تحلیل دسته‌بندی‌های محبوب
        top_categories = self._analyze_top_categories(chat_history)
        
        return {
            'frequency': frequency_analysis,
            'preferred_times': preferred_times,
            'session_lengths': session_lengths,
            'top_categories': top_categories,
            'engagement_level': self._assess_engagement_level(frequency_analysis, session_lengths)
        }
    
    def _analyze_interaction_frequency(self, chat_history: List[ChatHistory]) -> Dict[str, Any]:
        """تحلیل فرکانس تعامل"""
        
        if not chat_history:
            return {'level': 'بدون تعامل', 'average_per_day': 0}
        
        # محاسبه میانگین تعاملات روزانه
        first_date = chat_history[0].created_at.date()
        last_date = chat_history[-1].created_at.date()
        days_diff = (last_date - first_date).days + 1
        
        if days_diff == 0:
            avg_per_day = len(chat_history)
        else:
            avg_per_day = len(chat_history) / days_diff
        
        # تعیین سطح فرکانس
        if avg_per_day >= 5:
            level = 'بسیار فعال'
        elif avg_per_day >= 2:
            level = 'فعال'
        elif avg_per_day >= 0.5:
            level = 'متوسط'
        elif avg_per_day > 0:
            level = 'کم'
        else:
            level = 'بدون تعامل'
        
        return {
            'level': level,
            'average_per_day': round(avg_per_day, 2),
            'total_days': days_diff
        }
    
    def _analyze_preferred_times(self, chat_history: List[ChatHistory]) -> List[Dict[str, Any]]:
        """تحلیل زمان‌های ترجیحی تعامل"""
        
        if not chat_history:
            return []
        
        # گروه‌بندی بر اساس ساعت روز
        hour_counts = {}
        for chat in chat_history:
            hour = chat.created_at.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        # مرتب‌سازی و قالب‌بندی
        preferred_times = []
        for hour, count in sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            time_period = self._get_time_period(hour)
            preferred_times.append({
                'hour': hour,
                'time_period': time_period,
                'interaction_count': count,
                'percentage': round((count / len(chat_history)) * 100, 1)
            })
        
        return preferred_times
    
    def _get_time_period(self, hour: int) -> str:
        """تعیین بازه زمانی"""
        if 6 <= hour < 12:
            return 'صبح'
        elif 12 <= hour < 14:
            return 'ظهر'
        elif 14 <= hour < 18:
            return 'بعدازظهر'
        elif 18 <= hour < 22:
            return 'عصر'
        else:
            return 'شب'
    
    def _analyze_session_lengths(self, chat_history: List[ChatHistory]) -> Dict[str, Any]:
        """تحلیل طول جلسات تعامل"""
        
        if len(chat_history) < 2:
            return {
                'average_length_minutes': 0,
                'longest_session_minutes': 0,
                'session_count': 0
            }
        
        # شناسایی جلسات (تعاملات با فاصله کمتر از ۳۰ دقیقه)
        sessions = []
        current_session = [chat_history[0]]
        
        for i in range(1, len(chat_history)):
            time_diff = (chat_history[i].created_at - chat_history[i-1].created_at).total_seconds() / 60
            
            if time_diff <= 30:  # کمتر از ۳۰ دقیقه فاصله
                current_session.append(chat_history[i])
            else:
                sessions.append(current_session)
                current_session = [chat_history[i]]
        
        sessions.append(current_session)
        
        # محاسبه آمار جلسات
        session_lengths = []
        for session in sessions:
            if len(session) > 1:
                session_duration = (session[-1].created_at - session[0].created_at).total_seconds() / 60
                session_lengths.append(session_duration)
        
        if session_lengths:
            avg_length = sum(session_lengths) / len(session_lengths)
            longest_session = max(session_lengths)
        else:
            avg_length = 0
            longest_session = 0
        
        return {
            'average_length_minutes': round(avg_length, 2),
            'longest_session_minutes': round(longest_session, 2),
            'session_count': len(sessions),
            'average_messages_per_session': round(len(chat_history) / len(sessions), 2)
        }
    
    def _analyze_top_categories(self, chat_history: List[ChatHistory]) -> List[Dict[str, Any]]:
        """تحلیل دسته‌بندی‌های محبوب"""
        
        if not chat_history:
            return []
        
        # تحلیل دسته‌بندی‌های سوالات
        category_counts = {}
        for chat in chat_history:
            # استخراج دسته‌بندی از پیام (در صورت وجود)
            # این بخش باید با سیستم طبقه‌بندی یکپارچه شود
            category = self._extract_category_from_message(chat.message)
            if category:
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # مرتب‌سازی و قالب‌بندی
        top_categories = []
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            top_categories.append({
                'category': category,
                'interaction_count': count,
                'percentage': round((count / len(chat_history)) * 100, 1)
            })
        
        return top_categories
    
    def _extract_category_from_message(self, message: str) -> Optional[str]:
        """استخراج دسته‌بندی از پیام"""
        
        # این یک پیاده‌سازی ساده است
        # در عمل باید با سیستم طبقه‌بندی یکپارچه شود
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['تراز', 'دارایی', 'بدهی', 'سرمایه']):
            return 'ترازنامه'
        elif any(word in message_lower for word in ['سود', 'زیان', 'درآمد', 'هزینه']):
            return 'صورت سود و زیان'
        elif any(word in message_lower for word in ['نقد', 'جریان', 'صندوق', 'بانک']):
            return 'جریان نقدی'
        elif any(word in message_lower for word in ['نسبت', 'نقدینگی', 'سودآوری', 'اهرمی']):
            return 'نسبت‌های مالی'
        elif any(word in message_lower for word in ['گزارش', 'تحلیل', 'خلاصه']):
            return 'گزارش‌گیری'
        elif any(word in message_lower for word in ['پیشنهاد', 'توصیه', 'بهبود']):
            return 'توصیه‌ها'
        else:
            return 'سایر'
    
    def _assess_engagement_level(self, frequency_analysis: Dict, session_lengths: Dict) -> str:
        """ارزیابی سطح تعامل کاربر"""
        
        frequency_level = frequency_analysis['level']
        avg_session_length = session_lengths.get('average_length_minutes', 0)
        
        if frequency_level == 'بسیار فعال' and avg_session_length > 10:
            return 'تعامل بسیار بالا'
        elif frequency_level in ['بسیار فعال', 'فعال'] and avg_session_length > 5:
            return 'تعامل بالا'
        elif frequency_level == 'متوسط' and avg_session_length > 3:
            return 'تعامل متوسط'
        elif frequency_level in ['کم', 'بدون تعامل']:
            return 'تعامل کم'
        else:
            return 'تعامل محدود'
    
    def _analyze_user_preferences(self, chat_history: List[ChatHistory]) -> Dict[str, Any]:
        """تحلیل ترجیحات کاربر"""
        
        if not chat_history:
            return {
                'preferred_detail_level': 'متوسط',
                'response_format': 'متن ساده',
                'interaction_style': 'مستقیم'
            }
        
        # تحلیل سطح جزئیات مورد علاقه
        detail_level = self._analyze_preferred_detail_level(chat_history)
        
        # تحلیل فرمت پاسخ مورد علاقه
        response_format = self._analyze_preferred_response_format(chat_history)
        
        # تحلیل سبک تعامل
        interaction_style = self._analyze_interaction_style(chat_history)
        
        return {
            'preferred_detail_level': detail_level,
            'response_format': response_format,
            'interaction_style': interaction_style,
            'learning_preferences': self._analyze_learning_preferences(chat_history)
        }
    
    def _analyze_preferred_detail_level(self, chat_history: List[ChatHistory]) -> str:
        """تحلیل سطح جزئیات مورد علاقه کاربر"""
        
        # تحلیل بر اساس طول پاسخ‌ها و پیگیری‌ها
        detailed_responses = 0
        total_responses = 0
        
        for chat in chat_history:
            if chat.is_bot_response and chat.message:
                total_responses += 1
                # فرض: پاسخ‌های طولانی‌تر نشان‌دهنده علاقه به جزئیات بیشتر است
                if len(chat.message.split()) > 100:
                    detailed_responses += 1
        
        if total_responses == 0:
            return 'متوسط'
        
        detailed_ratio = detailed_responses / total_responses
        
        if detailed_ratio > 0.7:
            return 'بسیار جزئی'
        elif detailed_ratio > 0.4:
            return 'جزئی'
        elif detailed_ratio > 0.2:
            return 'متوسط'
        else:
            return 'خلاصه'
    
    def _analyze_preferred_response_format(self, chat_history: List[ChatHistory]) -> str:
        """تحلیل فرمت پاسخ مورد علاقه کاربر"""
        
        # تحلیل بر اساس ساختار پاسخ‌ها
        structured_responses = 0
        total_responses = 0
        
        for chat in chat_history:
            if chat.is_bot_response and chat.message:
                total_responses += 1
                # شناسایی پاسخ‌های ساختاریافته (جدول، لیست، نمودار)
                if any(marker in chat.message for marker in ['|', '-', '•', '۱.', 'جدول', 'نمودار']):
                    structured_responses += 1
        
        if total_responses == 0:
            return 'متن ساده'
        
        structured_ratio = structured_responses / total_responses
        
        if structured_ratio > 0.6:
            return 'ساختاریافته'
        elif structured_ratio > 0.3:
            return 'ترکیبی'
        else:
            return 'متن ساده'
    
    def _analyze_interaction_style(self, chat_history: List[ChatHistory]) -> str:
        """تحلیل سبک تعامل کاربر"""
        
        if len(chat_history) < 5:
            return 'مستقیم'
        
        # تحلیل بر اساس الگوی پیگیری‌ها
        follow_up_count = 0
        for i in range(1, len(chat_history)):
            if not chat_history[i].is_bot_response and not chat_history[i-1].is_bot_response:
                time_diff = (chat_history[i].created_at - chat_history[i-1].created_at).total_seconds() / 60
                if time_diff < 5:  # پیگیری سریع
                    follow_up_count += 1
        
        follow_up_ratio = follow_up_count / (len(chat_history) - 1)
        
        if follow_up_ratio > 0.3:
            return 'گفتگویی'
        elif follow_up_ratio > 0.1:
            return 'تعاملی'
        else:
            return 'مستقیم'
    
    def _analyze_learning_preferences(self, chat_history: List[ChatHistory]) -> Dict[str, Any]:
        """تحلیل ترجیحات یادگیری کاربر"""
        
        # این بخش می‌تواند با تحلیل محتوای سوالات توسعه یابد
        return {
            'financial_concepts': 'متوسط',
            'technical_details': 'متوسط',
            'practical_examples': 'بالا',
            'visual_aids': 'متوسط'
        }
    
    def _analyze_system_performance(self, chat_history: List[ChatHistory]) -> Dict[str, Any]:
        """تحلیل عملکرد سیستم"""
        
        if not chat_history:
            return {
                'response_accuracy': 'نامشخص',
                'user_satisfaction': 'نامشخص',
                'response_times': [],
                'success_rate': 0
            }
        
        # تحلیل دقت پاسخ‌ها (بر اساس فیدبک کاربران)
        accuracy_analysis = self._analyze_response_accuracy(chat_history)
        
        # تحلیل رضایت کاربر
        satisfaction_analysis = self._analyze_user_satisfaction(chat_history)
        
        # تحلیل زمان پاسخ‌دهی
        response_times = self._analyze_response_times(chat_history)
        
        # تحلیل نرخ موفقیت
        success_rate = self._calculate_success_rate(chat_history)
        
        return {
            'response_accuracy': accuracy_analysis,
            'user_satisfaction': satisfaction_analysis,
            'response_times': response_times,
            'success_rate': success_rate,
            'performance_improvements': self._identify_performance_improvements(
                accuracy_analysis, satisfaction_analysis, response_times
            )
        }
    
    def _analyze_response_accuracy(self, chat_history: List[ChatHistory]) -> Dict[str, Any]:
        """تحلیل دقت پاسخ‌ها"""
        
        # این بخش باید با سیستم فیدبک یکپارچه شود
        # فعلاً از داده‌های نمونه استفاده می‌کنیم
        
        total_responses = sum(1 for chat in chat_history if chat.is_bot_response)
        if total_responses == 0:
            return {'level': 'نامشخص', 'accuracy_percentage': 0}
        
        # فرض: ۸۵٪ دقت برای نمونه
        accuracy_percentage = 85
        
        if accuracy_percentage >= 90:
            level = 'عالی'
        elif accuracy_percentage >= 80:
            level = 'خوب'
        elif accuracy_percentage >= 70:
            level = 'متوسط'
        else:
            level = 'نیاز به بهبود'
        
        return {
            'level': level,
            'accuracy_percentage': accuracy_percentage,
            'improvement_suggestions': self._generate_accuracy_improvements(accuracy_percentage)
        }
    
    def _generate_accuracy_improvements(self, accuracy_percentage: float) -> List[str]:
        """تولید پیشنهادات بهبود دقت"""
        
        improvements = []
        
        if accuracy_percentage < 80:
            improvements.append('بهبود طبقه‌بندی سوالات مالی')
            improvements.append('افزایش دقت استخراج موجودیت‌ها')
        
        if accuracy_percentage < 70:
            improvements.append('بهبود یکپارچه‌سازی با ابزارهای تحلیل')
            improvements.append('افزایش پوشش سوالات مالی')
        
        return improvements
    
    def _analyze_user_satisfaction(self, chat_history: List[ChatHistory]) -> Dict[str, Any]:
        """تحلیل رضایت کاربر"""
        
        # این بخش باید با سیستم فیدبک یکپارچه شود
        # فعلاً از داده‌های نمونه استفاده می‌کنیم
        
        total_interactions = len([chat for chat in chat_history if not chat.is_bot_response])
        if total_interactions == 0:
            return {'level': 'نامشخص', 'satisfaction_score': 0}
        
        # فرض: امتیاز رضایت ۴.۲ از ۵
        satisfaction_score = 4.2
        
        if satisfaction_score >= 4.5:
            level = 'بسیار راضی'
        elif satisfaction_score >= 4.0:
            level = 'راضی'
        elif satisfaction_score >= 3.5:
            level = 'متوسط'
        else:
            level = 'ناراضی'
        
        return {
            'level': level,
            'satisfaction_score': satisfaction_score,
            'feedback_count': total_interactions
        }
    
    def _analyze_response_times(self, chat_history: List[ChatHistory]) -> Dict[str, Any]:
        """تحلیل زمان پاسخ‌دهی"""
        
        response_times = []
        
        for i in range(1, len(chat_history)):
            if not chat_history[i-1].is_bot_response and chat_history[i].is_bot_response:
                time_diff = (chat_history[i].created_at - chat_history[i-1].created_at).total_seconds()
                response_times.append(time_diff)
        
        if not response_times:
            return {
                'average_response_time_seconds': 0,
                'performance_level': 'نامشخص'
            }
        
        avg_response_time = sum(response_times) / len(response_times)
        
        if avg_response_time <= 2:
            performance_level = 'عالی'
        elif avg_response_time <= 5:
            performance_level = 'خوب'
        elif avg_response_time <= 10:
            performance_level = 'متوسط'
        else:
            performance_level = 'نیاز به بهبود'
        
        return {
            'average_response_time_seconds': round(avg_response_time, 2),
            'performance_level': performance_level,
            'total_responses_analyzed': len(response_times)
        }
    
    def _calculate_success_rate(self, chat_history: List[ChatHistory]) -> float:
        """محاسبه نرخ موفقیت"""
        
        # این بخش باید با معیارهای موفقیت یکپارچه شود
        # فعلاً از داده‌های نمونه استفاده می‌کنیم
        
        total_questions = len([chat for chat in chat_history if not chat.is_bot_response])
        if total_questions == 0:
            return 0.0
        
        # فرض: نرخ موفقیت ۸۸٪
        success_rate = 88.0
        
        return success_rate
    
    def _identify_performance_improvements(self, accuracy_analysis: Dict, 
                                         satisfaction_analysis: Dict, 
                                         response_times: Dict) -> List[str]:
        """شناسایی حوزه‌های بهبود عملکرد"""
        
        improvements = []
        
        # بهبود دقت
        if accuracy_analysis.get('accuracy_percentage', 0) < 80:
            improvements.append('بهبود دقت پاسخ‌ها با آموزش بیشتر مدل')
        
        # بهبود رضایت
        if satisfaction_analysis.get('satisfaction_score', 0) < 4.0:
            improvements.append('افزایش کیفیت پاسخ‌ها و قالب‌بندی بهتر')
        
        # بهبود زمان پاسخ
        if response_times.get('average_response_time_seconds', 0) > 5:
            improvements.append('بهینه‌سازی سرعت پردازش و پاسخ‌دهی')
        
        return improvements
    
    def _identify_improvement_areas(self, interaction_patterns: Dict, 
                                  system_performance: Dict) -> List[Dict[str, Any]]:
        """شناسایی حوزه‌های بهبود"""
        
        improvement_areas = []
        
        # بهبود تعامل
        engagement_level = interaction_patterns.get('engagement_level', '')
        if engagement_level in ['تعامل کم', 'تعامل محدود']:
            improvement_areas.append({
                'area': 'افزایش تعامل',
                'priority': 'متوسط',
                'description': 'افزایش فرکانس و کیفیت تعاملات کاربر',
                'suggested_actions': [
                    'ارائه محتوای شخصی‌سازی شده',
                    'ایجاد یادآوری‌های هوشمند',
                    'افزایش قابلیت‌های تعاملی'
                ]
            })
        
        # بهبود عملکرد
        accuracy_level = system_performance.get('response_accuracy', {}).get('level', '')
        if accuracy_level == 'نیاز به بهبود':
            improvement_areas.append({
                'area': 'بهبود دقت',
                'priority': 'بالا',
                'description': 'افزایش دقت پاسخ‌ها و کاهش خطاها',
                'suggested_actions': [
                    'بهبود طبقه‌بندی سوالات',
                    'افزایش دقت استخراج موجودیت‌ها',
                    'بهبود یکپارچه‌سازی با ابزارها'
                ]
            })
        
        # بهبود تجربه کاربری
        satisfaction_level = system_performance.get('user_satisfaction', {}).get('level', '')
        if satisfaction_level in ['متوسط', 'ناراضی']:
            improvement_areas.append({
                'area': 'بهبود تجربه کاربری',
                'priority': 'بالا',
                'description': 'افزایش رضایت کاربر و کیفیت تعامل',
                'suggested_actions': [
                    'بهبود رابط کاربری',
                    'افزایش سرعت پاسخ‌دهی',
                    'ارائه پاسخ‌های شخصی‌سازی شده'
                ]
            })
        
        return improvement_areas
    
    def _generate_learning_recommendations(self, interaction_patterns: Dict,
                                         user_preferences: Dict,
                                         improvement_areas: List[Dict]) -> List[Dict[str, Any]]:
        """تولید توصیه‌های یادگیری"""
        
        recommendations = []
        
        # توصیه‌های مبتنی بر الگوهای تعامل
        engagement_level = interaction_patterns.get('engagement_level', '')
        if engagement_level in ['تعامل کم', 'تعامل محدود']:
            recommendations.append({
                'type': 'تعامل',
                'priority': 'متوسط',
                'recommendation': 'افزایش فرکانس تعامل با کاربر',
                'action': 'ایجاد یادآوری‌های هوشمند و محتوای شخصی',
                'expected_impact': 'افزایش ۲۰-۳۰٪ تعامل'
            })
        
        # توصیه‌های مبتنی بر ترجیحات کاربر
        detail_level = user_preferences.get('preferred_detail_level', '')
        if detail_level == 'خلاصه':
            recommendations.append({
                'type': 'شخصی‌سازی',
                'priority': 'پایین',
                'recommendation': 'ارائه پاسخ‌های خلاصه و مستقیم',
                'action': 'بهینه‌سازی طول و ساختار پاسخ‌ها',
                'expected_impact': 'افزایش رضایت کاربر'
            })
        
        # توصیه‌های مبتنی بر حوزه‌های بهبود
        for area in improvement_areas:
            if area['priority'] == 'بالا':
                recommendations.append({
                    'type': 'بهبود عملکرد',
                    'priority': 'بالا',
                    'recommendation': f'تمرکز بر {area["area"]}',
                    'action': 'اجرای اقدامات پیشنهادی',
                    'expected_impact': 'بهبود قابل توجه عملکرد'
                })
        
        return recommendations
    
    def update_learning_model(self, user_feedback: List[UserFeedback]) -> Dict[str, Any]:
        """به‌روزرسانی مدل یادگیری بر اساس فیدبک کاربران"""
        
        try:
            # تحلیل فیدبک‌ها
            feedback_analysis = self._analyze_user_feedback(user_feedback)
            
            # به‌روزرسانی داده‌های یادگیری
            self._update_learning_data(feedback_analysis)
            
            # تولید گزارش بهبود
            improvement_report = self._generate_improvement_report(feedback_analysis)
            
            return {
                'success': True,
                'feedback_analyzed': len(user_feedback),
                'feedback_analysis': feedback_analysis,
                'improvement_report': improvement_report,
                'model_updated': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_user_feedback(self, user_feedback: List[UserFeedback]) -> Dict[str, Any]:
        """تحلیل فیدبک کاربران"""
        
        if not user_feedback:
            return {
                'total_feedback': 0,
                'average_rating': 0,
                'sentiment_analysis': 'بدون داده'
            }
        
        # تحلیل امتیازات
        ratings = [fb.rating for fb in user_feedback if fb.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # تحلیل احساسات
        positive_feedback = len([fb for fb in user_feedback if fb.rating and fb.rating >= 4])
        negative_feedback = len([fb for fb in user_feedback if fb.rating and fb.rating <= 2])
        
        if positive_feedback > negative_feedback * 2:
            sentiment = 'مثبت'
        elif negative_feedback > positive_feedback * 2:
            sentiment = 'منفی'
        else:
            sentiment = 'خنثی'
        
        return {
            'total_feedback': len(user_feedback),
            'average_rating': round(avg_rating, 2),
            'sentiment_analysis': sentiment,
            'positive_feedback_count': positive_feedback,
            'negative_feedback_count': negative_feedback,
            'improvement_suggestions': self._extract_improvement_suggestions(user_feedback)
        }
    
    def _extract_improvement_suggestions(self, user_feedback: List[UserFeedback]) -> List[str]:
        """استخراج پیشنهادات بهبود از فیدبک کاربران"""
        
        suggestions = []
        
        for feedback in user_feedback:
            if feedback.comments:
                # تحلیل ساده نظرات برای استخراج پیشنهادات
                comment_lower = feedback.comments.lower()
                if any(word in comment_lower for word in ['سریع', 'آهسته', 'زمان']):
                    suggestions.append('بهبود سرعت پاسخ‌دهی')
                if any(word in comment_lower for word in ['مشکل', 'خطا', 'غلط']):
                    suggestions.append('افزایش دقت پاسخ‌ها')
                if any(word in comment_lower for word in ['پیچیده', 'سخت', 'مبهم']):
                    suggestions.append('ساده‌سازی پاسخ‌ها')
        
        return list(set(suggestions))  # حذف موارد تکراری
    
    def _update_learning_data(self, feedback_analysis: Dict) -> None:
        """به‌روزرسانی داده‌های یادگیری"""
        
        # ذخیره تحلیل فیدبک برای استفاده آینده
        self.learning_data['last_feedback_analysis'] = feedback_analysis
        self.learning_data['last_update'] = datetime.now()
    
    def _generate_improvement_report(self, feedback_analysis: Dict) -> Dict[str, Any]:
        """تولید گزارش بهبود"""
        
        return {
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'key_findings': {
                'user_satisfaction': feedback_analysis.get('average_rating', 0),
                'sentiment_trend': feedback_analysis.get('sentiment_analysis', ''),
                'improvement_areas': feedback_analysis.get('improvement_suggestions', [])
            },
            'recommended_actions': self._generate_feedback_based_actions(feedback_analysis),
            'expected_impact': 'بهبود ۱۰-۱۵٪ در رضایت کاربر'
        }
    
    def _generate_feedback_based_actions(self, feedback_analysis: Dict) -> List[str]:
        """تولید اقدامات مبتنی بر فیدبک"""
        
        actions = []
        
        avg_rating = feedback_analysis.get('average_rating', 0)
        if avg_rating < 4.0:
            actions.append('بهبود کیفیت پاسخ‌ها و کاهش خطاها')
        
        sentiment = feedback_analysis.get('sentiment_analysis', '')
        if sentiment == 'منفی':
            actions.append('بررسی و رفع مشکلات گزارش شده')
        
        suggestions = feedback_analysis.get('improvement_suggestions', [])
        if 'بهبود سرعت پاسخ‌دهی' in suggestions:
            actions.append('بهینه‌سازی الگوریتم‌های پردازش')
        
        return actions


# ابزار LangChain برای سیستم یادگیری
class LearningSystemTool:
    """ابزار سیستم یادگیری برای LangChain"""
    
    name = "learning_system"
    description = "تحلیل تاریخچه تعاملات و بهبود عملکرد چت بات"
    
    def __init__(self):
        self.learning_system = LearningSystem()
    
    def analyze_user_interactions(self, user_id: int, days_back: int = 30) -> Dict:
        """تحلیل تعاملات کاربر"""
        try:
            result = self.learning_system.analyze_interaction_history(user_id, days_back)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_from_feedback(self, feedback_data: List[Dict]) -> Dict:
        """به‌روزرسانی بر اساس فیدبک"""
        try:
            # تبدیل داده‌های فیدبک به مدل UserFeedback
            user_feedback = []
            for fb in feedback_data:
                # این بخش باید با مدل واقعی یکپارچه شود
                user_feedback.append(UserFeedback(
                    user_id=fb.get('user_id'),
                    rating=fb.get('rating'),
                    comments=fb.get('comments', '')
                ))
            
            result = self.learning_system.update_learning_model(user_feedback)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
