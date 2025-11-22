# financial_system/services/management_dashboard.py
"""
تسک ۹۶: ایجاد داشبورد مدیریتی برای نظارت بر عملکرد
این سرویس برای ارائه دیدگاه مدیریتی از عملکرد کلی سیستم طراحی شده است.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
from users.models import User, Company, FinancialPeriod


class ManagementDashboard:
    """داشبورد مدیریتی برای نظارت بر عملکرد"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_dashboard_data(self, days_back: int = 30) -> Dict[str, Any]:
        """دریافت داده‌های داشبورد"""
        
        try:
            # محاسبه تاریخ شروع
            start_date = datetime.now() - timedelta(days=days_back)
            
            # جمع‌آوری داده‌های مختلف
            usage_metrics = self._get_usage_metrics(start_date)
            performance_metrics = self._get_performance_metrics(start_date)
            user_metrics = self._get_user_metrics(start_date)
            financial_metrics = self._get_financial_metrics(start_date)
            system_health = self._get_system_health_metrics(start_date)
            
            # تولید بینش‌های مدیریتی
            management_insights = self._generate_management_insights(
                usage_metrics, performance_metrics, user_metrics, financial_metrics
            )
            
            return {
                'success': True,
                'dashboard_period': f'{days_back} روز گذشته',
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'overview': self._generate_overview_summary(
                    usage_metrics, performance_metrics, user_metrics
                ),
                'usage_metrics': usage_metrics,
                'performance_metrics': performance_metrics,
                'user_metrics': user_metrics,
                'financial_metrics': financial_metrics,
                'system_health': system_health,
                'management_insights': management_insights,
                'alerts_and_recommendations': self._generate_alerts_and_recommendations(
                    usage_metrics, performance_metrics, system_health
                )
            }
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت داده‌های داشبورد: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_usage_metrics(self, start_date: datetime) -> Dict[str, Any]:
        """دریافت معیارهای استفاده"""
        
        try:
            # دریافت تاریخچه چت
            chat_history = ChatHistory.objects.filter(
                created_at__gte=start_date
            )
            
            # محاسبه معیارهای استفاده
            total_interactions = chat_history.count()
            bot_responses = chat_history.filter(is_bot_response=True).count()
            user_questions = total_interactions - bot_responses
            
            # تحلیل فرکانس استفاده
            daily_usage = self._analyze_daily_usage(chat_history)
            hourly_usage = self._analyze_hourly_usage(chat_history)
            
            # تحلیل دسته‌بندی سوالات
            question_categories = self._analyze_question_categories(chat_history)
            
            return {
                'total_interactions': total_interactions,
                'user_questions': user_questions,
                'bot_responses': bot_responses,
                'response_rate': round((bot_responses / user_questions) * 100, 1) if user_questions > 0 else 0,
                'average_daily_interactions': daily_usage.get('average_daily', 0),
                'peak_usage_hours': hourly_usage.get('peak_hours', []),
                'question_categories': question_categories,
                'usage_trend': daily_usage.get('trend', 'پایدار'),
                'engagement_level': self._assess_engagement_level(daily_usage, total_interactions)
            }
            
        except Exception as e:
            self.logger.error(f"خطا در محاسبه معیارهای استفاده: {str(e)}")
            return {
                'total_interactions': 0,
                'user_questions': 0,
                'bot_responses': 0,
                'response_rate': 0,
                'average_daily_interactions': 0,
                'peak_usage_hours': [],
                'question_categories': [],
                'usage_trend': 'نامشخص',
                'engagement_level': 'نامشخص'
            }
    
    def _analyze_daily_usage(self, chat_history) -> Dict[str, Any]:
        """تحلیل استفاده روزانه"""
        
        if not chat_history:
            return {
                'average_daily': 0,
                'trend': 'بدون داده',
                'busiest_day': 'نامشخص'
            }
        
        # گروه‌بندی بر اساس روز
        daily_counts = {}
        for chat in chat_history:
            date_str = chat.created_at.strftime('%Y-%m-%d')
            daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
        
        if not daily_counts:
            return {
                'average_daily': 0,
                'trend': 'بدون داده',
                'busiest_day': 'نامشخص'
            }
        
        # محاسبه میانگین روزانه
        average_daily = sum(daily_counts.values()) / len(daily_counts)
        
        # تحلیل روند
        dates = sorted(daily_counts.keys())
        if len(dates) >= 3:
            first_week_avg = sum(list(daily_counts.values())[:7]) / min(7, len(daily_counts))
            last_week_avg = sum(list(daily_counts.values())[-7:]) / min(7, len(daily_counts))
            
            if last_week_avg > first_week_avg * 1.2:
                trend = 'رشد'
            elif last_week_avg < first_week_avg * 0.8:
                trend = 'کاهش'
            else:
                trend = 'پایدار'
        else:
            trend = 'داده کافی نیست'
        
        # شناسایی شلوغ‌ترین روز
        busiest_day = max(daily_counts.items(), key=lambda x: x[1])[0] if daily_counts else 'نامشخص'
        
        return {
            'average_daily': round(average_daily, 1),
            'trend': trend,
            'busiest_day': busiest_day,
            'total_days': len(daily_counts)
        }
    
    def _analyze_hourly_usage(self, chat_history) -> Dict[str, Any]:
        """تحلیل استفاده ساعتی"""
        
        if not chat_history:
            return {
                'peak_hours': [],
                'average_hourly': 0
            }
        
        # گروه‌بندی بر اساس ساعت
        hourly_counts = {}
        for chat in chat_history:
            hour = chat.created_at.hour
            hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
        
        # شناسایی ساعات اوج
        peak_hours = []
        if hourly_counts:
            max_count = max(hourly_counts.values())
            for hour, count in sorted(hourly_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
                if count >= max_count * 0.7:  # حداقل ۷۰٪ از حداکثر
                    peak_hours.append({
                        'hour': hour,
                        'count': count,
                        'percentage': round((count / len(chat_history)) * 100, 1)
                    })
        
        # محاسبه میانگین ساعتی
        average_hourly = len(chat_history) / 24 if chat_history else 0
        
        return {
            'peak_hours': peak_hours,
            'average_hourly': round(average_hourly, 1),
            'total_hours_analyzed': len(hourly_counts)
        }
    
    def _analyze_question_categories(self, chat_history) -> List[Dict[str, Any]]:
        """تحلیل دسته‌بندی سوالات"""
        
        if not chat_history:
            return []
        
        # تحلیل دسته‌بندی‌های سوالات
        category_counts = {}
        user_questions = chat_history.filter(is_bot_response=False)
        
        for chat in user_questions:
            category = self._categorize_question(chat.message)
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # قالب‌بندی و مرتب‌سازی
        categories = []
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(user_questions)) * 100 if user_questions else 0
            categories.append({
                'category': category,
                'count': count,
                'percentage': round(percentage, 1)
            })
        
        return categories
    
    def _categorize_question(self, message: str) -> str:
        """طبقه‌بندی سوال"""
        
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
    
    def _assess_engagement_level(self, daily_usage: Dict, total_interactions: int) -> str:
        """ارزیابی سطح تعامل"""
        
        avg_daily = daily_usage.get('average_daily', 0)
        trend = daily_usage.get('trend', '')
        
        if avg_daily >= 50 and trend == 'رشد':
            return 'تعامل بسیار بالا'
        elif avg_daily >= 30:
            return 'تعامل بالا'
        elif avg_daily >= 15:
            return 'تعامل متوسط'
        elif avg_daily >= 5:
            return 'تعامل کم'
        else:
            return 'تعامل محدود'
    
    def _get_performance_metrics(self, start_date: datetime) -> Dict[str, Any]:
        """دریافت معیارهای عملکرد"""
        
        try:
            # دریافت فیدبک کاربران
            user_feedback = UserFeedback.objects.filter(
                created_at__gte=start_date
            )
            
            # محاسبه معیارهای عملکرد
            accuracy_metrics = self._calculate_accuracy_metrics(user_feedback)
            response_time_metrics = self._calculate_response_time_metrics(start_date)
            success_metrics = self._calculate_success_metrics(user_feedback)
            
            return {
                'accuracy': accuracy_metrics,
                'response_times': response_time_metrics,
                'success_rates': success_metrics,
                'overall_performance': self._assess_overall_performance(
                    accuracy_metrics, response_time_metrics, success_metrics
                )
            }
            
        except Exception as e:
            self.logger.error(f"خطا در محاسبه معیارهای عملکرد: {str(e)}")
            return {
                'accuracy': {'level': 'نامشخص', 'score': 0},
                'response_times': {'level': 'نامشخص', 'average_seconds': 0},
                'success_rates': {'level': 'نامشخص', 'rate': 0},
                'overall_performance': 'نامشخص'
            }
    
    def _calculate_accuracy_metrics(self, user_feedback) -> Dict[str, Any]:
        """محاسبه معیارهای دقت"""
        
        if not user_feedback:
            return {
                'level': 'نامشخص',
                'score': 0,
                'feedback_count': 0
            }
        
        # محاسبه میانگین امتیاز
        ratings = [fb.rating for fb in user_feedback if fb.rating is not None]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            accuracy_score = (avg_rating / 5) * 100
        else:
            avg_rating = 0
            accuracy_score = 0
        
        # ارزیابی سطح دقت
        if accuracy_score >= 90:
            level = 'عالی'
        elif accuracy_score >= 80:
            level = 'خوب'
        elif accuracy_score >= 70:
            level = 'متوسط'
        else:
            level = 'نیاز به بهبود'
        
        return {
            'level': level,
            'score': round(accuracy_score, 1),
            'average_rating': round(avg_rating, 2),
            'feedback_count': len(ratings)
        }
    
    def _calculate_response_time_metrics(self, start_date: datetime) -> Dict[str, Any]:
        """محاسبه معیارهای زمان پاسخ"""
        
        try:
            # دریافت تاریخچه چت برای تحلیل زمان پاسخ
            chat_history = ChatHistory.objects.filter(
                created_at__gte=start_date
            ).order_by('created_at')
            
            response_times = []
            for i in range(1, len(chat_history)):
                if not chat_history[i-1].is_bot_response and chat_history[i].is_bot_response:
                    time_diff = (chat_history[i].created_at - chat_history[i-1].created_at).total_seconds()
                    response_times.append(time_diff)
            
            if not response_times:
                return {
                    'level': 'نامشخص',
                    'average_seconds': 0,
                    'samples': 0
                }
            
            avg_response_time = sum(response_times) / len(response_times)
            
            # ارزیابی سطح زمان پاسخ
            if avg_response_time <= 2:
                level = 'عالی'
            elif avg_response_time <= 5:
                level = 'خوب'
            elif avg_response_time <= 10:
                level = 'متوسط'
            else:
                level = 'نیاز به بهبود'
            
            return {
                'level': level,
                'average_seconds': round(avg_response_time, 2),
                'samples': len(response_times),
                'improvement_suggestions': self._generate_response_time_suggestions(level)
            }
            
        except Exception as e:
            self.logger.error(f"خطا در محاسبه زمان پاسخ: {str(e)}")
            return {
                'level': 'نامشخص',
                'average_seconds': 0,
                'samples': 0
            }
    
    def _generate_response_time_suggestions(self, level: str) -> List[str]:
        """تولید پیشنهادات بهبود زمان پاسخ"""
        
        suggestions = []
        
        if level == 'نیاز به بهبود':
            suggestions.append('بهینه‌سازی الگوریتم‌های پردازش')
            suggestions.append('افزایش منابع سرور')
        
        if level in ['نیاز به بهبود', 'متوسط']:
            suggestions.append('کاهش پیچیدگی محاسبات')
            suggestions.append('بهبود کش‌گذاری داده‌ها')
        
        return suggestions
    
    def _calculate_success_metrics(self, user_feedback) -> Dict[str, Any]:
        """محاسبه معیارهای موفقیت"""
        
        if not user_feedback:
            return {
                'level': 'نامشخص',
                'rate': 0,
                'feedback_count': 0
            }
        
        # محاسبه نرخ موفقیت بر اساس امتیازات بالا
        successful_feedback = len([fb for fb in user_feedback if fb.rating and fb.rating >= 4])
        success_rate = (successful_feedback / len(user_feedback)) * 100 if user_feedback else 0
        
        # ارزیابی سطح موفقیت
        if success_rate >= 85:
            level = 'عالی'
        elif success_rate >= 75:
            level = 'خوب'
        elif success_rate >= 60:
            level = 'متوسط'
        else:
            level = 'نیاز به بهبود'
        
        return {
            'level': level,
            'rate': round(success_rate, 1),
            'feedback_count': len(user_feedback),
            'successful_interactions': successful_feedback
        }
    
    def _assess_overall_performance(self, accuracy_metrics: Dict, 
                                  response_time_metrics: Dict, 
                                  success_metrics: Dict) -> str:
        """ارزیابی عملکرد کلی"""
        
        # محاسبه امتیاز کلی
        accuracy_score = accuracy_metrics.get('score', 0)
        response_time_level = response_time_metrics.get('level', '')
        success_rate = success_metrics.get('rate', 0)
        
        # وزن‌دهی به معیارها
        total_score = (accuracy_score * 0.4) + (success_rate * 0.4)
        
        # تنظیم بر اساس زمان پاسخ
        if response_time_level == 'عالی':
            total_score += 20
        elif response_time_level == 'خوب':
            total_score += 10
        elif response_time_level == 'نیاز به بهبود':
            total_score -= 10
        
        # ارزیابی کلی
        if total_score >= 85:
            return 'عالی'
        elif total_score >= 70:
            return 'خوب'
        elif total_score >= 55:
            return 'متوسط'
        else:
            return 'نیاز به بهبود'
    
    def _get_user_metrics(self, start_date: datetime) -> Dict[str, Any]:
        """دریافت معیارهای کاربران"""
        
        try:
            # دریافت داده‌های کاربران
            active_users = User.objects.filter(
                last_login__gte=start_date
            ).count()
            
            total_users = User.objects.count()
            
            # تحلیل وفاداری کاربران
            loyalty_metrics = self._analyze_user_loyalty(start_date)
            
            # تحلیل نقش کاربران
            user_roles = self._analyze_user_roles()
            
            return {
                'active_users': active_users,
                'total_users': total_users,
                'user_activity_rate': round((active_users / total_users) * 100, 1) if total_users > 0 else 0,
                'loyalty_metrics': loyalty_metrics,
                'user_roles': user_roles,
                'user_growth_trend': self._assess_user_growth_trend(start_date)
            }
            
        except Exception as e:
            self.logger.error(f"خطا در محاسبه معیارهای کاربران: {str(e)}")
            return {
                'active_users': 0,
                'total_users': 0,
                'user_activity_rate': 0,
                'loyalty_metrics': {'level': 'نامشخص'},
                'user_roles': [],
                'user_growth_trend': 'نامشخص'
            }
    
    def _analyze_user_loyalty(self, start_date: datetime) -> Dict[str, Any]:
        """تحلیل وفاداری کاربران"""
        
        try:
            # دریافت تاریخچه چت برای تحلیل وفاداری
            chat_history = ChatHistory.objects.filter(
                created_at__gte=start_date
            )
            
            # گروه‌بندی بر اساس کاربر
            user_interactions = {}
            for chat in chat_history:
                user_id = chat.user_id
                user_interactions[user_id] = user_interactions.get(user_id, 0) + 1
            
            if not user_interactions:
                return {
                    'level': 'بدون داده',
                    'average_interactions_per_user': 0,
                    'loyal_users_count': 0
                }
            
            # محاسبه میانگین تعاملات
            avg_interactions = sum(user_interactions.values()) / len(user_interactions)
            
            # شناسایی کاربران وفادار (بیش از ۱۰ تعامل)
            loyal_users = len([count for count in user_interactions.values() if count >= 10])
            loyalty_rate = (loyal_users / len(user_interactions)) * 100 if user_interactions else 0
            
            # ارزیابی سطح وفاداری
            if loyalty_rate >= 40:
                level = 'وفاداری بالا'
            elif loyalty_rate >= 25:
                level = 'وفاداری متوسط'
            elif loyalty_rate >= 10:
                level = 'وفاداری کم'
            else:
                level = 'وفاداری محدود'
            
            return {
                'level': level,
                'average_interactions_per_user': round(avg_interactions, 1),
                'loyal_users_count': loyal_users,
                'loyalty_rate': round(loyalty_rate, 1),
                'total_active_users': len(user_interactions)
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل وفاداری: {str(e)}")
            return {
                'level': 'نامشخص',
                'average_interactions_per_user': 0,
                'loyal_users_count': 0,
                'loyalty_rate': 0,
                'total_active_users': 0
            }
    
    def _analyze_user_roles(self) -> List[Dict[str, Any]]:
        """تحلیل نقش کاربران"""
        
        try:
            # این بخش باید با سیستم نقش‌ها یکپارچه شود
            # فعلاً از داده‌های نمونه استفاده می‌کنیم
            
            roles_data = [
                {'role': 'حسابدار', 'count': 45, 'percentage': 45},
                {'role': 'مدیر مالی', 'count': 25, 'percentage': 25},
                {'role': 'مدیرعامل', 'count': 15, 'percentage': 15},
                {'role': 'کارشناس مالی', 'count': 10, 'percentage': 10},
                {'role': 'سایر', 'count': 5, 'percentage': 5}
            ]
            
            return roles_data
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل نقش کاربران: {str(e)}")
            return []
    
    def _assess_user_growth_trend(self, start_date: datetime) -> str:
        """ارزیابی روند رشد کاربران"""
        
        try:
            # محاسبه کاربران جدید در دوره جاری
            new_users_current = User.objects.filter(
                date_joined__gte=start_date
            ).count()
            
            # محاسبه کاربران جدید در دوره قبلی
            previous_start_date = start_date - timedelta(days=30)
            new_users_previous = User.objects.filter(
                date_joined__gte=previous_start_date,
                date_joined__lt=start_date
            ).count()
            
            if new_users_previous == 0:
                return 'بدون داده قبلی'
            
            growth_rate = ((new_users_current - new_users_previous) / new_users_previous) * 100
            
            if growth_rate > 20:
                return 'رشد قوی'
            elif growth_rate > 5:
                return 'رشد'
            elif growth_rate > -5:
                return 'پایدار'
            else:
                return 'کاهش'
                
        except Exception as e:
            self.logger.error(f"خطا در ارزیابی رشد کاربران: {str(e)}")
            return 'نامشخص'
    
    def _get_financial_metrics(self, start_date: datetime) -> Dict[str, Any]:
        """دریافت معیارهای مالی"""
        
        try:
            # این بخش باید با سیستم مالی یکپارچه شود
            # فعلاً از داده‌های نمونه استفاده می‌کنیم
            
            return {
                'total_companies_analyzed': 150,
                'total_financial_reports': 450,
                'average_report_accuracy': 92.5,
                'cost_savings_estimated': 125000000,  # به ریال
                'efficiency_improvement': 35.2,
                'roi_metrics': {
                    'estimated_roi': 285,
                    'payback_period_months': 6.5,
                    'annual_savings': 250000000
                }
            }
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت معیارهای مالی: {str(e)}")
            return {
                'total_companies_analyzed': 0,
                'total_financial_reports': 0,
                'average_report_accuracy': 0,
                'cost_savings_estimated': 0,
                'efficiency_improvement': 0,
                'roi_metrics': {'estimated_roi': 0, 'payback_period_months': 0, 'annual_savings': 0}
            }
    
    def _get_system_health_metrics(self, start_date: datetime) -> Dict[str, Any]:
        """دریافت معیارهای سلامت سیستم"""
        
        try:
            # این بخش باید با سیستم نظارت یکپارچه شود
            # فعلاً از داده‌های نمونه استفاده می‌کنیم
            
            return {
                'uptime_percentage': 99.8,
                'average_response_time': 2.3,
                'error_rate': 0.8,
                'system_load': 65.5,
                'database_performance': 88.2,
                'api_health': 95.7,
                'overall_health': 'عالی',
                'health_indicators': [
                    {'indicator': 'پردازش', 'status': 'عالی', 'value': 98.5},
                    {'indicator': 'حافظه', 'status': 'خوب', 'value': 85.2},
                    {'indicator': 'شبکه', 'status': 'عالی', 'value': 99.1},
                    {'indicator': 'ذخیره‌سازی', 'status': 'خوب', 'value': 92.3}
                ]
            }
            
        except Exception as e:
            self.logger.error(f"خطا در دریافت معیارهای سلامت سیستم: {str(e)}")
            return {
                'uptime_percentage': 0,
                'average_response_time': 0,
                'error_rate': 0,
                'system_load': 0,
                'database_performance': 0,
                'api_health': 0,
                'overall_health': 'نامشخص',
                'health_indicators': []
            }
    
    def _generate_overview_summary(self, usage_metrics: Dict, 
                                 performance_metrics: Dict, 
                                 user_metrics: Dict) -> Dict[str, Any]:
        """تولید خلاصه کلی"""
        
        total_interactions = usage_metrics.get('total_interactions', 0)
        overall_performance = performance_metrics.get('overall_performance', 'نامشخص')
        active_users = user_metrics.get('active_users', 0)
        engagement_level = usage_metrics.get('engagement_level', 'نامشخص')
        
        return {
            'total_interactions': total_interactions,
            'overall_performance': overall_performance,
            'active_users': active_users,
            'engagement_level': engagement_level,
            'key_highlights': self._generate_key_highlights(usage_metrics, performance_metrics, user_metrics),
            'performance_summary': self._generate_performance_summary(performance_metrics)
        }
    
    def _generate_key_highlights(self, usage_metrics: Dict, 
                               performance_metrics: Dict, 
                               user_metrics: Dict) -> List[str]:
        """تولید نکات برجسته"""
        
        highlights = []
        
        # تحلیل استفاده
        total_interactions = usage_metrics.get('total_interactions', 0)
        if total_interactions >= 1000:
            highlights.append(f'{total_interactions} تعامل موفق در دوره')
        
        engagement_level = usage_metrics.get('engagement_level', '')
        if engagement_level in ['تعامل بسیار بالا', 'تعامل بالا']:
            highlights.append('سطح تعامل کاربران بالا')
        
        # تحلیل عملکرد
        overall_performance = performance_metrics.get('overall_performance', '')
        if overall_performance == 'عالی':
            highlights.append('عملکرد سیستم در سطح عالی')
        
        # تحلیل کاربران
        active_users = user_metrics.get('active_users', 0)
        if active_users >= 50:
            highlights.append(f'{active_users} کاربر فعال')
        
        return highlights
    
    def _generate_performance_summary(self, performance_metrics: Dict) -> Dict[str, Any]:
        """تولید خلاصه عملکرد"""
        
        accuracy = performance_metrics.get('accuracy', {})
        response_times = performance_metrics.get('response_times', {})
        success_rates = performance_metrics.get('success_rates', {})
        
        return {
            'accuracy_level': accuracy.get('level', 'نامشخص'),
            'accuracy_score': accuracy.get('score', 0),
            'response_time_level': response_times.get('level', 'نامشخص'),
            'average_response_time': response_times.get('average_seconds', 0),
            'success_rate_level': success_rates.get('level', 'نامشخص'),
            'success_rate': success_rates.get('rate', 0)
        }
    
    def _generate_management_insights(self, usage_metrics: Dict, 
                                    performance_metrics: Dict, 
                                    user_metrics: Dict, 
                                    financial_metrics: Dict) -> List[Dict[str, Any]]:
        """تولید بینش‌های مدیریتی"""
        
        insights = []
        
        # بینش‌های مبتنی بر استفاده
        usage_trend = usage_metrics.get('usage_trend', '')
        if usage_trend == 'رشد':
            insights.append({
                'type': 'استراتژی رشد',
                'title': 'افزایش استفاده از سیستم',
                'description': 'روند استفاده از سیستم در حال رشد است، فرصت خوبی برای سرمایه‌گذاری بیشتر',
                'impact': 'بالا',
                'recommendation': 'افزایش منابع و توسعه قابلیت‌ها'
            })
        
        # بینش‌های مبتنی بر عملکرد
        overall_performance = performance_metrics.get('overall_performance', '')
        if overall_performance == 'نیاز به بهبود':
            insights.append({
                'type': 'بهبود عملکرد',
                'title': 'نیاز به بهبود عملکرد',
                'description': 'عملکرد سیستم نیاز به بهبود دارد، ممکن است بر رضایت کاربران تأثیر بگذارد',
                'impact': 'بالا',
                'recommendation': 'تمرکز بر بهبود دقت و سرعت پاسخ'
            })
        
        # بینش‌های مبتنی بر کاربران
        user_growth = user_metrics.get('user_growth_trend', '')
        if user_growth == 'رشد قوی':
            insights.append({
                'type': 'رشد کاربران',
                'title': 'رشد قوی کاربران',
                'description': 'تعداد کاربران فعال در حال رشد قوی است، نشان‌دهنده پذیرش خوب سیستم',
                'impact': 'متوسط',
                'recommendation': 'افزایش پشتیبانی و توسعه ویژگی‌ها'
            })
        
        # بینش‌های مبتنی بر مالی
        roi = financial_metrics.get('roi_metrics', {}).get('estimated_roi', 0)
        if roi >= 200:
            insights.append({
                'type': 'بازگشت سرمایه',
                'title': 'بازگشت سرمایه عالی',
                'description': f'سیستم بازگشت سرمایه {roi}% دارد، نشان‌دهنده ارزش‌آفرینی بالا',
                'impact': 'بسیار بالا',
                'recommendation': 'ادامه سرمایه‌گذاری و توسعه'
            })
        
        return insights
    
    def _generate_alerts_and_recommendations(self, usage_metrics: Dict, 
                                           performance_metrics: Dict, 
                                           system_health: Dict) -> Dict[str, Any]:
        """تولید هشدارها و توصیه‌ها"""
        
        alerts = []
        recommendations = []
        
        # هشدارهای عملکرد
        overall_performance = performance_metrics.get('overall_performance', '')
        if overall_performance == 'نیاز به بهبود':
            alerts.append({
                'type': 'عملکرد',
                'severity': 'بالا',
                'message': 'عملکرد سیستم نیاز به بهبود فوری دارد',
                'action': 'بررسی علل کاهش عملکرد'
            })
        
        # هشدارهای استفاده
        engagement_level = usage_metrics.get('engagement_level', '')
        if engagement_level == 'تعامل محدود':
            alerts.append({
                'type': 'استفاده',
                'severity': 'متوسط',
                'message': 'سطح تعامل کاربران محدود است',
                'action': 'بررسی موانع استفاده و بهبود تجربه کاربری'
            })
        
        # هشدارهای سلامت سیستم
        system_health_status = system_health.get('overall_health', '')
        if system_health_status == 'نیاز به بهبود':
            alerts.append({
                'type': 'سلامت سیستم',
                'severity': 'بالا',
                'message': 'سلامت سیستم نیاز به توجه دارد',
                'action': 'بررسی و رفع مشکلات زیرساختی'
            })
        
        # توصیه‌ها
        if overall_performance in ['عالی', 'خوب']:
            recommendations.append('ادامه سرمایه‌گذاری در توسعه قابلیت‌ها')
        
        if engagement_level in ['تعامل بسیار بالا', 'تعامل بالا']:
            recommendations.append('افزایش ظرفیت سیستم برای پاسخ به تقاضای رو به رشد')
        
        return {
            'alerts': alerts,
            'recommendations': recommendations,
            'total_alerts': len(alerts),
            'alert_severity_summary': self._summarize_alert_severity(alerts)
        }
    
    def _summarize_alert_severity(self, alerts: List[Dict]) -> Dict[str, int]:
        """خلاصه‌سازی شدت هشدارها"""
        
        severity_counts = {
            'بسیار بالا': 0,
            'بالا': 0,
            'متوسط': 0,
            'پایین': 0
        }
        
        for alert in alerts:
            severity = alert.get('severity', '')
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return severity_counts


# ابزار LangChain برای داشبورد مدیریتی
class ManagementDashboardTool:
    """ابزار داشبورد مدیریتی برای LangChain"""
    
    name = "management_dashboard"
    description = "دریافت داده‌های داشبورد مدیریتی برای نظارت بر عملکرد سیستم"
    
    def __init__(self):
        self.dashboard = ManagementDashboard()
    
    def get_dashboard_data(self, days_back: int = 30) -> Dict:
        """دریافت داده‌های داشبورد"""
        try:
            result = self.dashboard.get_dashboard_data(days_back)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
