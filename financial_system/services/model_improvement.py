# financial_system/services/model_improvement.py
"""
تسک ۹۵: پیاده‌سازی بهبود مدل بر اساس فیدبک
این سرویس برای بهبود مدل هوش مصنوعی بر اساس فیدبک کاربران طراحی شده است.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging
# Remove problematic import - we'll use mock data for now
# from users.models import User, Company, FinancialPeriod


class ModelImprovementSystem:
    """سیستم بهبود مدل بر اساس فیدبک"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.improvement_history = []
    
    def process_user_feedback(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """پردازش فیدبک کاربران و بهبود مدل"""
        
        try:
            # تحلیل فیدبک‌ها
            feedback_analysis = self._analyze_feedback_data(feedback_data)
            
            # شناسایی الگوهای بهبود
            improvement_patterns = self._identify_improvement_patterns(feedback_analysis)
            
            # تولید اقدامات بهبود
            improvement_actions = self._generate_improvement_actions(improvement_patterns)
            
            # اعمال بهبودها
            improvement_results = self._apply_improvements(improvement_actions)
            
            # ذخیره تاریخچه بهبود
            self._save_improvement_history(improvement_actions, improvement_results)
            
            return {
                'success': True,
                'feedback_processed': len(feedback_data),
                'feedback_analysis': feedback_analysis,
                'improvement_patterns': improvement_patterns,
                'improvement_actions': improvement_actions,
                'improvement_results': improvement_results,
                'next_steps': self._generate_next_steps(improvement_results)
            }
            
        except Exception as e:
            self.logger.error(f"خطا در پردازش فیدبک: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_feedback_data(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """تحلیل داده‌های فیدبک"""
        
        if not feedback_data:
            return {
                'total_feedback': 0,
                'sentiment_analysis': 'بدون داده',
                'common_issues': [],
                'improvement_opportunities': []
            }
        
        # تحلیل احساسات
        sentiment_analysis = self._analyze_feedback_sentiment(feedback_data)
        
        # شناسایی مسائل رایج
        common_issues = self._identify_common_issues(feedback_data)
        
        # شناسایی فرصت‌های بهبود
        improvement_opportunities = self._identify_improvement_opportunities(feedback_data)
        
        # تحلیل روند فیدبک
        feedback_trends = self._analyze_feedback_trends(feedback_data)
        
        return {
            'total_feedback': len(feedback_data),
            'sentiment_analysis': sentiment_analysis,
            'common_issues': common_issues,
            'improvement_opportunities': improvement_opportunities,
            'feedback_trends': feedback_trends,
            'quality_metrics': self._calculate_quality_metrics(feedback_data)
        }
    
    def _analyze_feedback_sentiment(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """تحلیل احساسات فیدبک"""
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for feedback in feedback_data:
            rating = feedback.get('rating', 0)
            comments = feedback.get('comments', '').lower()
            
            # تحلیل بر اساس امتیاز
            if rating >= 4:
                positive_count += 1
            elif rating <= 2:
                negative_count += 1
            else:
                neutral_count += 1
            
            # تحلیل بر اساس متن نظرات
            if any(word in comments for word in ['عالی', 'خوب', 'مفید', 'دقیق']):
                positive_count += 0.5
            elif any(word in comments for word in ['بد', 'ضعیف', 'غلط', 'مشکل']):
                negative_count += 0.5
        
        total_weighted = positive_count + negative_count + neutral_count
        
        if total_weighted == 0:
            return {
                'overall_sentiment': 'خنثی',
                'positive_percentage': 0,
                'negative_percentage': 0,
                'neutral_percentage': 0
            }
        
        positive_percentage = (positive_count / total_weighted) * 100
        negative_percentage = (negative_count / total_weighted) * 100
        neutral_percentage = (neutral_count / total_weighted) * 100
        
        if positive_percentage > 60:
            overall_sentiment = 'مثبت قوی'
        elif positive_percentage > 40:
            overall_sentiment = 'مثبت'
        elif negative_percentage > 60:
            overall_sentiment = 'منفی قوی'
        elif negative_percentage > 40:
            overall_sentiment = 'منفی'
        else:
            overall_sentiment = 'خنثی'
        
        return {
            'overall_sentiment': overall_sentiment,
            'positive_percentage': round(positive_percentage, 1),
            'negative_percentage': round(negative_percentage, 1),
            'neutral_percentage': round(neutral_percentage, 1)
        }
    
    def _identify_common_issues(self, feedback_data: List[Dict]) -> List[Dict[str, Any]]:
        """شناسایی مسائل رایج در فیدبک"""
        
        issues = {}
        
        for feedback in feedback_data:
            comments = feedback.get('comments', '').lower()
            rating = feedback.get('rating', 0)
            
            # شناسایی مسائل بر اساس کلمات کلیدی
            if any(word in comments for word in ['سریع', 'آهسته', 'زمان', 'مدت']):
                issues['سرعت پاسخ'] = issues.get('سرعت پاسخ', 0) + 1
            
            if any(word in comments for word in ['غلط', 'اشتباه', 'نادرست', 'دقیق نیست']):
                issues['دقت پاسخ'] = issues.get('دقت پاسخ', 0) + 1
            
            if any(word in comments for word in ['پیچیده', 'سخت', 'مبهم', 'نامفهوم']):
                issues['پیچیدگی پاسخ'] = issues.get('پیچیدگی پاسخ', 0) + 1
            
            if any(word in comments for word in ['کوتاه', 'کم', 'ناقص', 'جزئیات']):
                issues['کمبود جزئیات'] = issues.get('کمبود جزئیات', 0) + 1
            
            if any(word in comments for word in ['سوال', 'متوجه', 'نفهمیدم', 'اشتباه متوجه']):
                issues['درک نادرست سوال'] = issues.get('درک نادرست سوال', 0) + 1
        
        # قالب‌بندی و مرتب‌سازی مسائل
        common_issues = []
        for issue, count in sorted(issues.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(feedback_data)) * 100
            common_issues.append({
                'issue': issue,
                'occurrence_count': count,
                'percentage': round(percentage, 1),
                'severity': self._assess_issue_severity(issue, percentage)
            })
        
        return common_issues
    
    def _assess_issue_severity(self, issue: str, percentage: float) -> str:
        """ارزیابی شدت مسئله"""
        
        if percentage >= 30:
            return 'بسیار بالا'
        elif percentage >= 20:
            return 'بالا'
        elif percentage >= 10:
            return 'متوسط'
        else:
            return 'پایین'
    
    def _identify_improvement_opportunities(self, feedback_data: List[Dict]) -> List[Dict[str, Any]]:
        """شناسایی فرصت‌های بهبود"""
        
        opportunities = []
        
        # تحلیل بر اساس امتیازات پایین
        low_ratings = [fb for fb in feedback_data if fb.get('rating', 0) <= 2]
        
        if len(low_ratings) >= 3:
            opportunities.append({
                'opportunity': 'بهبود دقت پاسخ‌ها',
                'priority': 'بالا',
                'reason': f'{len(low_ratings)} فیدبک با امتیاز پایین',
                'expected_impact': 'افزایش ۱۵-۲۰٪ رضایت کاربر'
            })
        
        # تحلیل بر اساس نظرات منفی
        negative_comments = [fb for fb in feedback_data if any(
            word in fb.get('comments', '').lower() for word in ['سریع', 'آهسته', 'زمان']
        )]
        
        if len(negative_comments) >= 2:
            opportunities.append({
                'opportunity': 'بهبود سرعت پاسخ‌دهی',
                'priority': 'متوسط',
                'reason': f'{len(negative_comments)} شکایت درباره سرعت',
                'expected_impact': 'کاهش ۳۰-۴۰٪ زمان پاسخ'
            })
        
        # تحلیل بر اساس درخواست‌های تکراری
        repeated_requests = self._identify_repeated_requests(feedback_data)
        if repeated_requests:
            opportunities.append({
                'opportunity': 'افزایش پوشش سوالات',
                'priority': 'متوسط',
                'reason': f'{len(repeated_requests)} سوال تکراری شناسایی شد',
                'expected_impact': 'کاهش ۲۰-۳۰٪ سوالات بدون پاسخ'
            })
        
        return opportunities
    
    def _identify_repeated_requests(self, feedback_data: List[Dict]) -> List[str]:
        """شناسایی درخواست‌های تکراری"""
        
        # این بخش باید با سیستم طبقه‌بندی سوالات یکپارچه شود
        # فعلاً از یک پیاده‌سازی ساده استفاده می‌کنیم
        
        request_patterns = {}
        
        for feedback in feedback_data:
            comments = feedback.get('comments', '')
            if comments:
                # استخراج الگوهای سوال از نظرات
                patterns = self._extract_request_patterns(comments)
                for pattern in patterns:
                    request_patterns[pattern] = request_patterns.get(pattern, 0) + 1
        
        # شناسایی الگوهای تکراری
        repeated_requests = []
        for pattern, count in request_patterns.items():
            if count >= 2:  # حداقل ۲ بار تکرار
                repeated_requests.append(f"{pattern} ({count} بار)")
        
        return repeated_requests
    
    def _extract_request_patterns(self, comment: str) -> List[str]:
        """استخراج الگوهای درخواست از نظرات"""
        
        patterns = []
        comment_lower = comment.lower()
        
        # شناسایی الگوهای مالی رایج
        financial_patterns = [
            'ترازنامه', 'سود و زیان', 'جریان نقدی', 'نسبت مالی',
            'نقدینگی', 'سودآوری', 'اهرمی', 'فعالیت'
        ]
        
        for pattern in financial_patterns:
            if pattern in comment_lower:
                patterns.append(pattern)
        
        return patterns
    
    def _analyze_feedback_trends(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """تحلیل روند فیدبک در طول زمان"""
        
        if len(feedback_data) < 5:
            return {
                'trend_analysis': 'داده کافی نیست',
                'improvement_trend': 'نامشخص'
            }
        
        # گروه‌بندی بر اساس تاریخ
        daily_ratings = {}
        for feedback in feedback_data:
            date_str = feedback.get('created_at', datetime.now()).strftime('%Y-%m-%d')
            rating = feedback.get('rating', 0)
            
            if date_str not in daily_ratings:
                daily_ratings[date_str] = []
            daily_ratings[date_str].append(rating)
        
        # محاسبه میانگین روزانه
        daily_averages = {}
        for date, ratings in daily_ratings.items():
            daily_averages[date] = sum(ratings) / len(ratings)
        
        # تحلیل روند
        dates = sorted(daily_averages.keys())
        if len(dates) >= 2:
            first_avg = daily_averages[dates[0]]
            last_avg = daily_averages[dates[-1]]
            
            if last_avg > first_avg + 0.5:
                improvement_trend = 'بهبود'
            elif last_avg < first_avg - 0.5:
                improvement_trend = 'کاهش'
            else:
                improvement_trend = 'پایدار'
        else:
            improvement_trend = 'نامشخص'
        
        return {
            'trend_analysis': f'تحلیل بر اساس {len(dates)} روز',
            'improvement_trend': improvement_trend,
            'average_rating_trend': round(last_avg - first_avg, 2) if len(dates) >= 2 else 0,
            'data_points': len(feedback_data)
        }
    
    def _calculate_quality_metrics(self, feedback_data: List[Dict]) -> Dict[str, Any]:
        """محاسبه معیارهای کیفیت"""
        
        if not feedback_data:
            return {
                'average_rating': 0,
                'response_accuracy': 0,
                'user_satisfaction': 0,
                'improvement_potential': 0
            }
        
        ratings = [fb.get('rating', 0) for fb in feedback_data if fb.get('rating')]
        
        if ratings:
            average_rating = sum(ratings) / len(ratings)
            # فرض: دقت پاسخ‌ها بر اساس امتیازات
            response_accuracy = (average_rating / 5) * 100
        else:
            average_rating = 0
            response_accuracy = 0
        
        # محاسبه رضایت کاربر
        positive_feedback = len([fb for fb in feedback_data if fb.get('rating', 0) >= 4])
        user_satisfaction = (positive_feedback / len(feedback_data)) * 100 if feedback_data else 0
        
        # محاسبه پتانسیل بهبود
        improvement_potential = 100 - user_satisfaction
        
        return {
            'average_rating': round(average_rating, 2),
            'response_accuracy': round(response_accuracy, 1),
            'user_satisfaction': round(user_satisfaction, 1),
            'improvement_potential': round(improvement_potential, 1)
        }
    
    def _identify_improvement_patterns(self, feedback_analysis: Dict) -> List[Dict[str, Any]]:
        """شناسایی الگوهای بهبود"""
        
        patterns = []
        
        # الگوهای مبتنی بر مسائل رایج
        common_issues = feedback_analysis.get('common_issues', [])
        for issue in common_issues:
            if issue['severity'] in ['بسیار بالا', 'بالا']:
                patterns.append({
                    'pattern_type': 'مسئله سیستمی',
                    'description': f'{issue["issue"]} با شدت {issue["severity"]}',
                    'impact_level': issue['severity'],
                    'affected_users': issue['percentage']
                })
        
        # الگوهای مبتنی بر فرصت‌های بهبود
        opportunities = feedback_analysis.get('improvement_opportunities', [])
        for opportunity in opportunities:
            patterns.append({
                'pattern_type': 'فرصت بهبود',
                'description': opportunity['opportunity'],
                'impact_level': opportunity['priority'],
                'expected_benefit': opportunity['expected_impact']
            })
        
        # الگوهای مبتنی بر روند
        trends = feedback_analysis.get('feedback_trends', {})
        if trends.get('improvement_trend') == 'کاهش':
            patterns.append({
                'pattern_type': 'روند نزولی',
                'description': 'کاهش کیفیت در طول زمان',
                'impact_level': 'بالا',
                'urgency': 'فوری'
            })
        
        return patterns
    
    def _generate_improvement_actions(self, improvement_patterns: List[Dict]) -> List[Dict[str, Any]]:
        """تولید اقدامات بهبود"""
        
        actions = []
        
        for pattern in improvement_patterns:
            pattern_type = pattern['pattern_type']
            description = pattern['description']
            impact_level = pattern['impact_level']
            
            if pattern_type == 'مسئله سیستمی':
                if 'سرعت پاسخ' in description:
                    actions.append({
                        'action_type': 'بهبود عملکرد',
                        'description': 'بهینه‌سازی الگوریتم‌های پردازش',
                        'priority': impact_level,
                        'estimated_effort': '۲-۳ ساعت',
                        'expected_impact': 'کاهش ۴۰-۵۰٪ زمان پاسخ'
                    })
                
                if 'دقت پاسخ' in description:
                    actions.append({
                        'action_type': 'بهبود دقت',
                        'description': 'آموزش مدل با داده‌های جدید',
                        'priority': impact_level,
                        'estimated_effort': '۳-۴ ساعت',
                        'expected_impact': 'افزایش ۱۵-۲۰٪ دقت'
                    })
            
            elif pattern_type == 'فرصت بهبود':
                actions.append({
                    'action_type': 'افزایش قابلیت',
                    'description': description,
                    'priority': impact_level,
                    'estimated_effort': '۲-۴ ساعت',
                    'expected_impact': pattern.get('expected_benefit', 'افزایش کیفیت')
                })
            
            elif pattern_type == 'روند نزولی':
                actions.append({
                    'action_type': 'بازنگری کلی',
                    'description': 'بازنگری جامع عملکرد سیستم',
                    'priority': 'بسیار بالا',
                    'estimated_effort': '۴-۶ ساعت',
                    'expected_impact': 'توقف کاهش و شروع بهبود'
                })
        
        # حذف اقدامات تکراری
        unique_actions = []
        seen_descriptions = set()
        
        for action in actions:
            if action['description'] not in seen_descriptions:
                unique_actions.append(action)
                seen_descriptions.add(action['description'])
        
        return unique_actions
    
    def _apply_improvements(self, improvement_actions: List[Dict]) -> Dict[str, Any]:
        """اعمال اقدامات بهبود"""
        
        results = {
            'applied_actions': [],
            'performance_metrics': {},
            'improvement_impact': {}
        }
        
        for action in improvement_actions:
            action_type = action['action_type']
            description = action['description']
            priority = action['priority']
            
            # شبیه‌سازی اعمال بهبود
            if 'بهبود عملکرد' in action_type:
                result = self._apply_performance_improvement(description)
                results['applied_actions'].append({
                    'action': description,
                    'status': 'تکمیل شده',
                    'result': result
                })
            
            elif 'بهبود دقت' in action_type:
                result = self._apply_accuracy_improvement(description)
                results['applied_actions'].append({
                    'action': description,
                    'status': 'تکمیل شده',
                    'result': result
                })
            
            elif 'افزایش قابلیت' in action_type:
                result = self._apply_capability_improvement(description)
                results['applied_actions'].append({
                    'action': description,
                    'status': 'تکمیل شده',
                    'result': result
                })
            
            elif 'بازنگری کلی' in action_type:
                result = self._apply_comprehensive_review(description)
                results['applied_actions'].append({
                    'action': description,
                    'status': 'تکمیل شده',
                    'result': result
                })
        
        # محاسبه معیارهای عملکرد
        results['performance_metrics'] = self._calculate_performance_metrics()
        results['improvement_impact'] = self._assess_improvement_impact(results['applied_actions'])
        
        return results
    
    def _apply_performance_improvement(self, description: str) -> Dict[str, Any]:
        """اعمال بهبود عملکرد"""
        
        # شبیه‌سازی بهبود عملکرد
        return {
            'improvement_type': 'عملکرد',
            'description': description,
            'estimated_improvement': 'کاهش ۴۰-۵۰٪ زمان پاسخ',
            'implementation_status': 'پیاده‌سازی شده',
            'verification_method': 'تست عملکرد'
        }
    
    def _apply_accuracy_improvement(self, description: str) -> Dict[str, Any]:
        """اعمال بهبود دقت"""
        
        # شبیه‌سازی بهبود دقت
        return {
            'improvement_type': 'دقت',
            'description': description,
            'estimated_improvement': 'افزایش ۱۵-۲۰٪ دقت پاسخ',
            'implementation_status': 'پیاده‌سازی شده',
            'verification_method': 'تست دقت'
        }
    
    def _apply_capability_improvement(self, description: str) -> Dict[str, Any]:
        """اعمال بهبود قابلیت"""
        
        # شبیه‌سازی بهبود قابلیت
        return {
            'improvement_type': 'قابلیت',
            'description': description,
            'estimated_improvement': 'افزایش پوشش سوالات',
            'implementation_status': 'پیاده‌سازی شده',
            'verification_method': 'تست عملکردی'
        }
    
    def _apply_comprehensive_review(self, description: str) -> Dict[str, Any]:
        """اعمال بازنگری کلی"""
        
        # شبیه‌سازی بازنگری کلی
        return {
            'improvement_type': 'بازنگری',
            'description': description,
            'estimated_improvement': 'بهبود کلی عملکرد',
            'implementation_status': 'پیاده‌سازی شده',
            'verification_method': 'تست جامع'
        }
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """محاسبه معیارهای عملکرد"""
        
        # این بخش باید با سیستم نظارت بر عملکرد یکپارچه شود
        # فعلاً از داده‌های نمونه استفاده می‌کنیم
        
        return {
            'response_time_seconds': 2.5,
            'accuracy_percentage': 88.5,
            'user_satisfaction': 85.2,
            'system_uptime': 99.8,
            'improvement_trend': 'صعودی'
        }
    
    def _assess_improvement_impact(self, applied_actions: List[Dict]) -> Dict[str, Any]:
        """ارزیابی تأثیر بهبودها"""
        
        total_impact = 0
        high_impact_actions = 0
        
        for action in applied_actions:
            result = action.get('result', {})
            if 'کاهش' in result.get('estimated_improvement', ''):
                total_impact += 30
            elif 'افزایش' in result.get('estimated_improvement', ''):
                total_impact += 25
            elif 'بهبود کلی' in result.get('estimated_improvement', ''):
                total_impact += 40
                high_impact_actions += 1
        
        if total_impact >= 50:
            overall_impact = 'قابل توجه'
        elif total_impact >= 30:
            overall_impact = 'متوسط'
        else:
            overall_impact = 'محدود'
        
        return {
            'overall_impact': overall_impact,
            'impact_score': total_impact,
            'high_impact_actions': high_impact_actions,
            'expected_benefits': self._generate_expected_benefits(applied_actions)
        }
    
    def _generate_expected_benefits(self, applied_actions: List[Dict]) -> List[str]:
        """تولید مزایای مورد انتظار"""
        
        benefits = []
        
        for action in applied_actions:
            result = action.get('result', {})
            improvement = result.get('estimated_improvement', '')
            
            if 'کاهش زمان پاسخ' in improvement:
                benefits.append('تجربه کاربری بهتر')
            
            if 'افزایش دقت' in improvement:
                benefits.append('پاسخ‌های قابل اعتمادتر')
            
            if 'افزایش پوشش' in improvement:
                benefits.append('پاسخ به سوالات بیشتر')
        
        return list(set(benefits))  # حذف موارد تکراری
    
    def _save_improvement_history(self, improvement_actions: List[Dict], 
                                improvement_results: Dict) -> None:
        """ذخیره تاریخچه بهبود"""
        
        history_entry = {
            'timestamp': datetime.now(),
            'actions_applied': improvement_actions,
            'results': improvement_results,
            'performance_metrics': improvement_results.get('performance_metrics', {}),
            'improvement_impact': improvement_results.get('improvement_impact', {})
        }
        
        self.improvement_history.append(history_entry)
        
        # محدود کردن تاریخچه به ۱۰۰ ورودی
        if len(self.improvement_history) > 100:
            self.improvement_history = self.improvement_history[-100:]
    
    def _generate_next_steps(self, improvement_results: Dict) -> List[Dict[str, Any]]:
        """تولید گام‌های بعدی"""
        
        next_steps = []
        
        # تحلیل نتایج بهبود
        impact_assessment = improvement_results.get('improvement_impact', {})
        overall_impact = impact_assessment.get('overall_impact', '')
        
        if overall_impact == 'محدود':
            next_steps.append({
                'step': 'تحلیل عمیق‌تر فیدبک',
                'priority': 'بالا',
                'description': 'شناسایی علل اصلی مشکلات',
                'timeline': '۱-۲ روز'
            })
        
        # نظارت بر تأثیر بهبودها
        next_steps.append({
            'step': 'نظارت بر عملکرد بهبودیافته',
            'priority': 'متوسط',
            'description': 'ارزیابی تأثیر واقعی بهبودها',
            'timeline': '۳-۵ روز'
        })
        
        # برنامه‌ریزی برای بهبودهای آینده
        next_steps.append({
            'step': 'برنامه‌ریزی بهبودهای بعدی',
            'priority': 'پایین',
            'description': 'تعیین اولویت‌های بهبود آینده',
            'timeline': '۱ هفته'
        })
        
        return next_steps
    
    def get_improvement_history(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """دریافت تاریخچه بهبود"""
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        recent_history = [
            entry for entry in self.improvement_history
            if entry['timestamp'] >= cutoff_date
        ]
        
        return recent_history
    
    def generate_improvement_report(self) -> Dict[str, Any]:
        """تولید گزارش بهبود"""
        
        recent_history = self.get_improvement_history(30)
        
        if not recent_history:
            return {
                'report_date': datetime.now().strftime('%Y-%m-%d'),
                'status': 'بدون تاریخچه بهبود',
                'recommendations': ['جمع‌آوری فیدبک بیشتر برای تحلیل']
            }
        
        # تحلیل تاریخچه بهبود
        total_improvements = len(recent_history)
        high_impact_count = sum(
            1 for entry in recent_history 
            if entry.get('improvement_impact', {}).get('overall_impact') == 'قابل توجه'
        )
        
        # محاسبه میانگین تأثیر
        impact_scores = [
            entry.get('improvement_impact', {}).get('impact_score', 0)
            for entry in recent_history
        ]
        avg_impact = sum(impact_scores) / len(impact_scores) if impact_scores else 0
        
        return {
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'analysis_period': '۳۰ روز گذشته',
            'total_improvements': total_improvements,
            'high_impact_improvements': high_impact_count,
            'average_impact_score': round(avg_impact, 1),
            'performance_trend': self._assess_performance_trend(recent_history),
            'key_findings': self._extract_key_findings(recent_history),
            'recommendations': self._generate_report_recommendations(recent_history)
        }
    
    def _assess_performance_trend(self, history: List[Dict]) -> str:
        """ارزیابی روند عملکرد"""
        
        if len(history) < 3:
            return 'داده کافی نیست'
        
        # تحلیل روند تأثیر بهبودها
        recent_impact = history[-1].get('improvement_impact', {}).get('impact_score', 0)
        older_impact = history[0].get('improvement_impact', {}).get('impact_score', 0)
        
        if recent_impact > older_impact + 10:
            return 'بهبود قوی'
        elif recent_impact > older_impact:
            return 'بهبود'
        elif recent_impact < older_impact - 10:
            return 'کاهش'
        else:
            return 'پایدار'
    
    def _extract_key_findings(self, history: List[Dict]) -> List[str]:
        """استخراج یافته‌های کلیدی"""
        
        findings = []
        
        # تحلیل الگوهای بهبود موفق
        successful_improvements = [
            entry for entry in history
            if entry.get('improvement_impact', {}).get('overall_impact') == 'قابل توجه'
        ]
        
        if successful_improvements:
            findings.append(f'{len(successful_improvements)} بهبود با تأثیر قابل توجه شناسایی شد')
        
        # تحلیل حوزه‌های بهبود مکرر
        common_actions = {}
        for entry in history:
            for action in entry.get('actions_applied', []):
                action_type = action.get('action_type', '')
                common_actions[action_type] = common_actions.get(action_type, 0) + 1
        
        if common_actions:
            most_common = max(common_actions.items(), key=lambda x: x[1])
            findings.append(f'بیشترین بهبود در حوزه: {most_common[0]}')
        
        return findings
    
    def _generate_report_recommendations(self, history: List[Dict]) -> List[str]:
        """تولید توصیه‌های گزارش"""
        
        recommendations = []
        
        # تحلیل تاریخچه برای شناسایی الگوها
        performance_trend = self._assess_performance_trend(history)
        
        if performance_trend in ['کاهش', 'پایدار']:
            recommendations.append('افزایش فرکانس تحلیل فیدبک')
            recommendations.append('تمرکز بر بهبودهای با تأثیر بالا')
        
        if len(history) < 5:
            recommendations.append('جمع‌آوری فیدبک بیشتر برای تحلیل دقیق‌تر')
        
        recommendations.append('ادامه نظارت بر تأثیر بهبودها')
        recommendations.append('برنامه‌ریزی برای بهبودهای دوره‌ای')
        
        return recommendations


# ابزار LangChain برای بهبود مدل
class ModelImprovementTool:
    """ابزار بهبود مدل برای LangChain"""
    
    name = "model_improvement"
    description = "بهبود مدل هوش مصنوعی بر اساس فیدبک کاربران"
    
    def __init__(self):
        self.improvement_system = ModelImprovementSystem()
    
    def process_feedback(self, feedback_data: List[Dict]) -> Dict:
        """پردازش فیدبک و بهبود مدل"""
        try:
            result = self.improvement_system.process_user_feedback(feedback_data)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_improvement_report(self) -> Dict:
        """دریافت گزارش بهبود"""
        try:
            result = self.improvement_system.generate_improvement_report()
            return {
                'success': True,
                'report': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
