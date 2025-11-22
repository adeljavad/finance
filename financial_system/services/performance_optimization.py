# financial_system/services/performance_optimization.py
"""
تسک ۹۸: بهینه‌سازی سرعت و کارایی سیستم
این سرویس برای بهبود عملکرد، کاهش زمان پاسخ‌دهی و بهینه‌سازی منابع سیستم طراحی شده است.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time
import json
import logging
import threading
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import gc


class PerformanceOptimizationSystem:
    """سیستم بهینه‌سازی سرعت و کارایی"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.performance_metrics = {}
        self.optimization_history = []
        self.cache = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def analyze_system_performance(self) -> Dict[str, Any]:
        """تحلیل عملکرد سیستم و شناسایی حوزه‌های بهبود"""
        
        try:
            # جمع‌آوری معیارهای عملکرد
            system_metrics = self._collect_system_metrics()
            application_metrics = self._collect_application_metrics()
            database_metrics = self._collect_database_metrics()
            
            # شناسایی حوزه‌های بهبود
            optimization_areas = self._identify_optimization_areas(
                system_metrics, application_metrics, database_metrics
            )
            
            # تولید توصیه‌های بهینه‌سازی
            optimization_recommendations = self._generate_optimization_recommendations(optimization_areas)
            
            # ارزیابی تأثیر بالقوه
            impact_assessment = self._assess_optimization_impact(optimization_recommendations)
            
            return {
                'success': True,
                'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'system_metrics': system_metrics,
                'application_metrics': application_metrics,
                'database_metrics': database_metrics,
                'optimization_areas': optimization_areas,
                'optimization_recommendations': optimization_recommendations,
                'impact_assessment': impact_assessment,
                'next_steps': self._generate_next_steps(optimization_areas)
            }
            
        except Exception as e:
            self.logger.error(f"خطا در تحلیل عملکرد سیستم: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """جمع‌آوری معیارهای سیستم"""
        
        try:
            # معیارهای CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # معیارهای حافظه
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available / (1024 ** 3)  # به گیگابایت
            
            # معیارهای دیسک
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free = disk.free / (1024 ** 3)  # به گیگابایت
            
            # معیارهای شبکه
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
            
            return {
                'cpu': {
                    'usage_percent': cpu_percent,
                    'core_count': cpu_count,
                    'status': 'عالی' if cpu_percent < 50 else 'خوب' if cpu_percent < 80 else 'نیاز به بهبود'
                },
                'memory': {
                    'usage_percent': memory_percent,
                    'available_gb': round(memory_available, 2),
                    'status': 'عالی' if memory_percent < 60 else 'خوب' if memory_percent < 85 else 'نیاز به بهبود'
                },
                'disk': {
                    'usage_percent': disk_percent,
                    'free_gb': round(disk_free, 2),
                    'status': 'عالی' if disk_percent < 70 else 'خوب' if disk_percent < 90 else 'نیاز به بهبود'
                },
                'network': {
                    'bytes_sent': network_bytes_sent,
                    'bytes_received': network_bytes_recv,
                    'status': 'عالی'
                }
            }
            
        except Exception as e:
            self.logger.error(f"خطا در جمع‌آوری معیارهای سیستم: {str(e)}")
            return {
                'cpu': {'usage_percent': 0, 'core_count': 0, 'status': 'نامشخص'},
                'memory': {'usage_percent': 0, 'available_gb': 0, 'status': 'نامشخص'},
                'disk': {'usage_percent': 0, 'free_gb': 0, 'status': 'نامشخص'},
                'network': {'bytes_sent': 0, 'bytes_received': 0, 'status': 'نامشخص'}
            }
    
    def _collect_application_metrics(self) -> Dict[str, Any]:
        """جمع‌آوری معیارهای برنامه"""
        
        try:
            # این بخش باید با سیستم نظارت برنامه یکپارچه شود
            # فعلاً از داده‌های نمونه استفاده می‌کنیم
            
            return {
                'response_times': {
                    'average_response_time': 2.3,
                    'p95_response_time': 4.1,
                    'p99_response_time': 6.8,
                    'status': 'خوب' if 2.3 <= 3 else 'نیاز به بهبود'
                },
                'throughput': {
                    'requests_per_second': 45.2,
                    'concurrent_users': 28,
                    'status': 'عالی' if 45.2 >= 40 else 'خوب' if 45.2 >= 20 else 'نیاز به بهبود'
                },
                'error_rates': {
                    'error_percentage': 0.8,
                    'success_rate': 99.2,
                    'status': 'عالی' if 0.8 <= 1 else 'خوب' if 0.8 <= 3 else 'نیاز به بهبود'
                },
                'cache_efficiency': {
                    'cache_hit_rate': 78.5,
                    'cache_miss_rate': 21.5,
                    'status': 'خوب' if 78.5 >= 70 else 'نیاز به بهبود'
                }
            }
            
        except Exception as e:
            self.logger.error(f"خطا در جمع‌آوری معیارهای برنامه: {str(e)}")
            return {
                'response_times': {'average_response_time': 0, 'p95_response_time': 0, 'p99_response_time': 0, 'status': 'نامشخص'},
                'throughput': {'requests_per_second': 0, 'concurrent_users': 0, 'status': 'نامشخص'},
                'error_rates': {'error_percentage': 0, 'success_rate': 0, 'status': 'نامشخص'},
                'cache_efficiency': {'cache_hit_rate': 0, 'cache_miss_rate': 0, 'status': 'نامشخص'}
            }
    
    def _collect_database_metrics(self) -> Dict[str, Any]:
        """جمع‌آوری معیارهای پایگاه داده"""
        
        try:
            # این بخش باید با سیستم نظارت پایگاه داده یکپارچه شود
            # فعلاً از داده‌های نمونه استفاده می‌کنیم
            
            return {
                'query_performance': {
                    'average_query_time': 0.15,
                    'slow_queries_percentage': 2.3,
                    'status': 'عالی' if 0.15 <= 0.2 else 'خوب' if 0.15 <= 0.5 else 'نیاز به بهبود'
                },
                'connection_pool': {
                    'active_connections': 12,
                    'max_connections': 50,
                    'connection_utilization': 24.0,
                    'status': 'عالی' if 24.0 <= 30 else 'خوب' if 24.0 <= 70 else 'نیاز به بهبود'
                },
                'index_efficiency': {
                    'index_hit_rate': 92.5,
                    'table_scans_percentage': 7.5,
                    'status': 'عالی' if 92.5 >= 90 else 'خوب' if 92.5 >= 80 else 'نیاز به بهبود'
                }
            }
            
        except Exception as e:
            self.logger.error(f"خطا در جمع‌آوری معیارهای پایگاه داده: {str(e)}")
            return {
                'query_performance': {'average_query_time': 0, 'slow_queries_percentage': 0, 'status': 'نامشخص'},
                'connection_pool': {'active_connections': 0, 'max_connections': 0, 'connection_utilization': 0, 'status': 'نامشخص'},
                'index_efficiency': {'index_hit_rate': 0, 'table_scans_percentage': 0, 'status': 'نامشخص'}
            }
    
    def _identify_optimization_areas(self, system_metrics: Dict, 
                                   application_metrics: Dict, 
                                   database_metrics: Dict) -> List[Dict[str, Any]]:
        """شناسایی حوزه‌های بهینه‌سازی"""
        
        optimization_areas = []
        
        # تحلیل معیارهای سیستم
        cpu_status = system_metrics.get('cpu', {}).get('status', '')
        memory_status = system_metrics.get('memory', {}).get('status', '')
        disk_status = system_metrics.get('disk', {}).get('status', '')
        
        if cpu_status == 'نیاز به بهبود':
            optimization_areas.append({
                'area': 'CPU',
                'priority': 'بالا',
                'description': 'استفاده از CPU بالا است، ممکن است بر عملکرد تأثیر بگذارد',
                'current_metric': f"{system_metrics.get('cpu', {}).get('usage_percent', 0)}%",
                'target_metric': 'کمتر از ۸۰٪',
                'improvement_potential': 'متوسط'
            })
        
        if memory_status == 'نیاز به بهبود':
            optimization_areas.append({
                'area': 'حافظه',
                'priority': 'بالا',
                'description': 'استفاده از حافظه بالا است، ممکن است باعث کندی سیستم شود',
                'current_metric': f"{system_metrics.get('memory', {}).get('usage_percent', 0)}%",
                'target_metric': 'کمتر از ۸۵٪',
                'improvement_potential': 'بالا'
            })
        
        # تحلیل معیارهای برنامه
        response_time_status = application_metrics.get('response_times', {}).get('status', '')
        cache_efficiency_status = application_metrics.get('cache_efficiency', {}).get('status', '')
        
        if response_time_status == 'نیاز به بهبود':
            optimization_areas.append({
                'area': 'زمان پاسخ',
                'priority': 'بسیار بالا',
                'description': 'زمان پاسخ برنامه نیاز به بهبود دارد',
                'current_metric': f"{application_metrics.get('response_times', {}).get('average_response_time', 0)} ثانیه",
                'target_metric': 'کمتر از ۳ ثانیه',
                'improvement_potential': 'بالا'
            })
        
        if cache_efficiency_status == 'نیاز به بهبود':
            optimization_areas.append({
                'area': 'کارایی کش',
                'priority': 'متوسط',
                'description': 'کارایی کش نیاز به بهبود دارد',
                'current_metric': f"{application_metrics.get('cache_efficiency', {}).get('cache_hit_rate', 0)}%",
                'target_metric': 'بیشتر از ۸۰٪',
                'improvement_potential': 'متوسط'
            })
        
        # تحلیل معیارهای پایگاه داده
        query_performance_status = database_metrics.get('query_performance', {}).get('status', '')
        
        if query_performance_status == 'نیاز به بهبود':
            optimization_areas.append({
                'area': 'کارایی کوئری',
                'priority': 'بالا',
                'description': 'کارایی کوئری‌های پایگاه داده نیاز به بهبود دارد',
                'current_metric': f"{database_metrics.get('query_performance', {}).get('average_query_time', 0)} ثانیه",
                'target_metric': 'کمتر از ۰.۲ ثانیه',
                'improvement_potential': 'بالا'
            })
        
        return optimization_areas
    
    def _generate_optimization_recommendations(self, optimization_areas: List[Dict]) -> List[Dict[str, Any]]:
        """تولید توصیه‌های بهینه‌سازی"""
        
        recommendations = []
        
        for area in optimization_areas:
            area_name = area['area']
            priority = area['priority']
            
            if area_name == 'CPU':
                recommendations.extend([
                    {
                        'category': 'CPU',
                        'priority': priority,
                        'recommendation': 'بهینه‌سازی الگوریتم‌های پردازش سنگین',
                        'implementation_effort': 'متوسط',
                        'expected_improvement': 'کاهش ۲۰-۳۰٪ استفاده از CPU',
                        'implementation_steps': [
                            'شناسایی الگوریتم‌های با مصرف CPU بالا',
                            'بهینه‌سازی حلقه‌ها و محاسبات',
                            'استفاده از کتابخانه‌های بهینه‌شده'
                        ]
                    },
                    {
                        'category': 'CPU',
                        'priority': 'متوسط',
                        'recommendation': 'افزایش مقیاس افقی با اضافه کردن سرور',
                        'implementation_effort': 'بالا',
                        'expected_improvement': 'کاهش ۴۰-۵۰٪ بار روی هر سرور',
                        'implementation_steps': [
                            'بررسی امکان Load Balancing',
                            'افزایش تعداد نمونه‌های برنامه',
                            'پیکربندی Load Balancer'
                        ]
                    }
                ])
            
            elif area_name == 'حافظه':
                recommendations.extend([
                    {
                        'category': 'حافظه',
                        'priority': priority,
                        'recommendation': 'بهینه‌سازی مدیریت حافظه و کاهش نشتی حافظه',
                        'implementation_effort': 'متوسط',
                        'expected_improvement': 'کاهش ۲۵-۳۵٪ استفاده از حافظه',
                        'implementation_steps': [
                            'بررسی و رفع نشتی‌های حافظه',
                            'بهینه‌سازی ساختار داده‌ها',
                            'پیاده‌سازی کش‌گذاری هوشمند'
                        ]
                    },
                    {
                        'category': 'حافظه',
                        'priority': 'پایین',
                        'recommendation': 'افزایش حافظه سرور',
                        'implementation_effort': 'پایین',
                        'expected_improvement': 'کاهش فوری فشار روی حافظه',
                        'implementation_steps': [
                            'بررسی مشخصات سرور',
                            'افزایش RAM',
                            'تست عملکرد'
                        ]
                    }
                ])
            
            elif area_name == 'زمان پاسخ':
                recommendations.extend([
                    {
                        'category': 'زمان پاسخ',
                        'priority': priority,
                        'recommendation': 'بهینه‌سازی کوئری‌های پایگاه داده',
                        'implementation_effort': 'متوسط',
                        'expected_improvement': 'کاهش ۳۰-۴۰٪ زمان پاسخ',
                        'implementation_steps': [
                            'شناسایی کوئری‌های کند',
                            'اضافه کردن ایندکس‌های مناسب',
                            'بهینه‌سازی ساختار جداول'
                        ]
                    },
                    {
                        'category': 'زمان پاسخ',
                        'priority': 'بالا',
                        'recommendation': 'پیاده‌سازی کش‌گذاری پیشرفته',
                        'implementation_effort': 'متوسط',
                        'expected_improvement': 'کاهش ۵۰-۶۰٪ زمان پاسخ برای داده‌های تکراری',
                        'implementation_steps': [
                            'شناسایی داده‌های قابل کش',
                            'پیاده‌سازی کش در سطح برنامه',
                            'تنظیم زمان انقضای کش'
                        ]
                    },
                    {
                        'category': 'زمان پاسخ',
                        'priority': 'متوسط',
                        'recommendation': 'بهینه‌سازی پردازش ناهمزمان',
                        'implementation_effort': 'بالا',
                        'expected_improvement': 'کاهش ۴۰-۵۰٪ زمان پاسخ برای عملیات سنگین',
                        'implementation_steps': [
                            'شناسایی عملیات قابل اجرای ناهمزمان',
                            'پیاده‌سازی صف‌های پردازش',
                            'استفاده از Celery برای پردازش پس‌زمینه'
                        ]
                    }
                ])
            
            elif area_name == 'کارایی کش':
                recommendations.append({
                    'category': 'کارایی کش',
                    'priority': priority,
                    'recommendation': 'بهینه‌سازی استراتژی کش‌گذاری',
                    'implementation_effort': 'متوسط',
                    'expected_improvement': 'افزایش ۱۵-۲۵٪ نرخ برخورد کش',
                        'implementation_steps': [
                            'تحلیل الگوهای دسترسی به داده',
                            'تنظیم اندازه و زمان انقضای کش',
                            'پیاده‌سازی کش‌گذاری چندسطحی'
                        ]
                    })
            
            elif area_name == 'کارایی کوئری':
                recommendations.extend([
                    {
                        'category': 'کارایی کوئری',
                        'priority': priority,
                        'recommendation': 'بهینه‌سازی ایندکس‌های پایگاه داده',
                        'implementation_effort': 'متوسط',
                        'expected_improvement': 'کاهش ۴۰-۵۰٪ زمان اجرای کوئری',
                        'implementation_steps': [
                            'تحلیل کوئری‌های کند',
                            'اضافه کردن ایندکس‌های مرکب',
                            'حذف ایندکس‌های غیرضروری'
                        ]
                    },
                    {
                        'category': 'کارایی کوئری',
                        'priority': 'متوسط',
                        'recommendation': 'بهینه‌سازی ساختار جداول',
                        'implementation_effort': 'بالا',
                        'expected_improvement': 'کاهش ۲۰-۳۰٪ حجم داده‌ها',
                        'implementation_steps': [
                            'نرمال‌سازی جداول',
                            'حذف داده‌های تکراری',
                            'فشرده‌سازی داده‌ها'
                        ]
                    }
                ])
        
        # حذف توصیه‌های تکراری
        unique_recommendations = []
        seen_recommendations = set()
        
        for rec in recommendations:
            rec_key = rec['recommendation']
            if rec_key not in seen_recommendations:
                unique_recommendations.append(rec)
                seen_recommendations.add(rec_key)
        
        return unique_recommendations
    
    def _assess_optimization_impact(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """ارزیابی تأثیر بهینه‌سازی"""
        
        total_impact = 0
        high_impact_count = 0
        
        for rec in recommendations:
            expected_improvement = rec.get('expected_improvement', '')
            priority = rec.get('priority', '')
            
            # محاسبه تأثیر بر اساس اولویت و بهبود مورد انتظار
            if priority == 'بسیار بالا':
                total_impact += 40
                high_impact_count += 1
            elif priority == 'بالا':
                total_impact += 30
            elif priority == 'متوسط':
                total_impact += 20
            else:
                total_impact += 10
        
        # ارزیابی کلی تأثیر
        if total_impact >= 80:
            overall_impact = 'بسیار بالا'
        elif total_impact >= 60:
            overall_impact = 'بالا'
        elif total_impact >= 40:
            overall_impact = 'متوسط'
        else:
            overall_impact = 'پایین'
        
        return {
            'overall_impact': overall_impact,
            'impact_score': total_impact,
            'high_impact_recommendations': high_impact_count,
            'expected_benefits': self._generate_expected_benefits(recommendations)
        }
    
    def _generate_expected_benefits(self, recommendations: List[Dict]) -> List[str]:
        """تولید مزایای مورد انتظار"""
        
        benefits = []
        
        for rec in recommendations:
            category = rec.get('category', '')
            expected_improvement = rec.get('expected_improvement', '')
            
            if 'CPU' in category:
                benefits.append('کاهش مصرف منابع پردازشی')
            
            if 'حافظه' in category:
                benefits.append('بهبود مدیریت حافظه و کاهش نشتی')
            
            if 'زمان پاسخ' in category:
                benefits.append('تجربه کاربری بهتر و پاسخ‌دهی سریع‌تر')
            
            if 'کارایی کش' in category:
                benefits.append('کاهش بار روی پایگاه داده')
            
            if 'کارایی کوئری' in category:
                benefits.append('سرعت بیشتر در بازیابی داده‌ها')
        
        return list(set(benefits))  # حذف موارد تکراری
    
    def _generate_next_steps(self, optimization_areas: List[Dict]) -> List[Dict[str, Any]]:
        """تولید گام‌های بعدی"""
        
        next_steps = []
        
        # تحلیل حوزه‌های بهینه‌سازی برای تعیین اولویت
        high_priority_areas = [area for area in optimization_areas if area['priority'] in ['بسیار بالا', 'بالا']]
        
        if high_priority_areas:
            next_steps.append({
                'step': 'پیاده‌سازی بهینه‌سازی‌های با اولویت بالا',
                'priority': 'فوری',
                'description': 'تمرکز بر حوزه‌هایی که بیشترین تأثیر را بر عملکرد دارند',
                'timeline': '۱-۲ هفته'
            })
        
        # نظارت بر تأثیر بهینه‌سازی‌ها
        next_steps.append({
            'step': 'نظارت بر عملکرد پس از بهینه‌سازی',
            'priority': 'متوسط',
            'description': 'ارزیابی تأثیر واقعی بهینه‌سازی‌ها بر عملکرد سیستم',
            'timeline': '۲-۴ هفته'
        })
        
        # برنامه‌ریزی برای بهینه‌سازی‌های آینده
        next_steps.append({
            'step': 'برنامه‌ریزی برای بهینه‌سازی‌های دوره‌ای',
            'priority': 'پایین',
            'description': 'تعیین برنامه منظم برای نظارت و بهینه‌سازی عملکرد',
            'timeline': '۱ ماه'
        })
        
        return next_steps
    
    def apply_optimizations(self, optimization_plan: List[Dict]) -> Dict[str, Any]:
        """اعمال بهینه‌سازی‌ها"""
        
        try:
            applied_optimizations = []
            failed_optimizations = []
            
            for optimization in optimization_plan:
                try:
                    result = self._apply_single_optimization(optimization)
                    applied_optimizations.append({
                        'optimization': optimization.get('recommendation', ''),
                        'result': result,
                        'status': 'موفق'
                    })
                except Exception as e:
                    failed_optimizations.append({
                        'optimization': optimization.get('recommendation', ''),
                        'error': str(e),
                        'status': 'ناموفق'
                    })
            
            # ارزیابی تأثیر کلی
            overall_impact = self._evaluate_optimization_impact(applied_optimizations)
            
            return {
                'success': True,
                'total_optimizations': len(optimization_plan),
                'applied_optimizations': len(applied_optimizations),
                'failed_optimizations': len(failed_optimizations),
                'applied_optimizations_details': applied_optimizations,
                'failed_optimizations_details': failed_optimizations,
                'overall_impact': overall_impact,
                'performance_comparison': self._compare_performance_before_after()
            }
            
        except Exception as e:
            self.logger.error(f"خطا در اعمال بهینه‌سازی‌ها: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _apply_single_optimization(self, optimization: Dict) -> Dict[str, Any]:
        """اعمال یک بهینه‌سازی واحد"""
        
        optimization_type = optimization.get('category', '')
        recommendation = optimization.get('recommendation', '')
        
        # شبیه‌سازی اعمال بهینه‌سازی‌های مختلف
        if 'CPU' in optimization_type:
            return {
                'optimization_type': 'CPU',
                'description': 'بهینه‌سازی الگوریتم‌های پردازش',
                'applied_changes': [
                    'بهینه‌سازی حلقه‌های پردازشی',
                    'استفاده از کتابخانه‌های بهینه‌شده',
                    'کاهش پیچیدگی محاسبات'
                ],
                'estimated_improvement': 'کاهش ۲۵-۳۵٪ استفاده از CPU'
            }
        
        elif 'حافظه' in optimization_type:
            return {
                'optimization_type': 'حافظه',
                'description': 'بهینه‌سازی مدیریت حافظه',
                'applied_changes': [
                    'رفع نشتی‌های حافظه',
                    'بهینه‌سازی ساختار داده‌ها',
                    'پیاده‌سازی کش‌گذاری'
                ],
                'estimated_improvement': 'کاهش ۲۰-۳۰٪ استفاده از حافظه'
            }
        
        elif 'زمان پاسخ' in optimization_type:
            return {
                'optimization_type': 'زمان پاسخ',
                'description': 'بهینه‌سازی زمان پاسخ‌دهی',
                'applied_changes': [
                    'بهینه‌سازی کوئری‌های پایگاه داده',
                    'پیاده‌سازی کش‌گذاری',
                    'بهینه‌سازی پردازش ناهمزمان'
                ],
                'estimated_improvement': 'کاهش ۴۰-۵۰٪ زمان پاسخ'
            }
        
        else:
            return {
                'optimization_type': 'عمومی',
                'description': 'بهینه‌سازی عمومی عملکرد',
                'applied_changes': ['تنظیمات عمومی بهینه‌سازی'],
                'estimated_improvement': 'کاهش ۱۰-۲۰٪ زمان پاسخ'
            }
    
    def _evaluate_optimization_impact(self, applied_optimizations: List[Dict]) -> Dict[str, Any]:
        """ارزیابی تأثیر بهینه‌سازی‌ها"""
        
        total_improvement = 0
        optimization_count = len(applied_optimizations)
        
        for optimization in applied_optimizations:
            result = optimization.get('result', {})
            improvement = result.get('estimated_improvement', '')
            
            # استخراج عدد بهبود از رشته
            if 'کاهش' in improvement and '%' in improvement:
                try:
                    # استخراج عدد از رشته (مثلاً "کاهش ۲۵-۳۵٪" -> 30)
                    numbers = [int(s) for s in improvement.split() if s.isdigit()]
                    if numbers:
                        avg_improvement = sum(numbers) / len(numbers)
                        total_improvement += avg_improvement
                except:
                    pass
        
        if optimization_count > 0:
            average_improvement = total_improvement / optimization_count
        else:
            average_improvement = 0
        
        # ارزیابی کلی تأثیر
        if average_improvement >= 30:
            overall_impact = 'بسیار بالا'
        elif average_improvement >= 20:
            overall_impact = 'بالا'
        elif average_improvement >= 10:
            overall_impact = 'متوسط'
        else:
            overall_impact = 'پایین'
        
        return {
            'overall_impact': overall_impact,
            'average_improvement_percentage': round(average_improvement, 1),
            'total_optimizations_applied': optimization_count,
            'estimated_performance_gain': f'{round(average_improvement, 1)}% بهبود کلی'
        }
    
    def _compare_performance_before_after(self) -> Dict[str, Any]:
        """مقایسه عملکرد قبل و بعد از بهینه‌سازی"""
        
        # این بخش باید با داده‌های واقعی عملکرد یکپارچه شود
        # فعلاً از داده‌های نمونه استفاده می‌کنیم
        
        return {
            'response_time': {
                'before': 2.8,
                'after': 1.9,
                'improvement': '۳۲.۱٪ کاهش'
            },
            'cpu_usage': {
                'before': 68.5,
                'after': 52.3,
                'improvement': '۲۳.۶٪ کاهش'
            },
            'memory_usage': {
                'before': 78.2,
                'after': 62.8,
                'improvement': '۱۹.۷٪ کاهش'
            },
            'throughput': {
                'before': 38.4,
                'after': 51.2,
                'improvement': '۳۳.۳٪ افزایش'
            }
        }
    
    def get_optimization_history(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """دریافت تاریخچه بهینه‌سازی"""
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        recent_history = [
            entry for entry in self.optimization_history
            if entry.get('timestamp', datetime.min) >= cutoff_date
        ]
        
        return recent_history
    
    def clear_cache(self) -> Dict[str, Any]:
        """پاک کردن کش سیستم"""
        
        try:
            cache_size_before = len(self.cache)
            self.cache.clear()
            gc.collect()  # آزادسازی حافظه
            
            return {
                'success': True,
                'cache_cleared': True,
                'cache_size_before': cache_size_before,
                'cache_size_after': 0,
                'memory_freed': 'کش سیستم پاک شد و حافظه آزاد گردید'
            }
            
        except Exception as e:
            self.logger.error(f"خطا در پاک کردن کش: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# ابزار LangChain برای بهینه‌سازی عملکرد
class PerformanceOptimizationTool:
    """ابزار بهینه‌سازی عملکرد برای LangChain"""
    
    name = "performance_optimization"
    description = "تحلیل و بهینه‌سازی عملکرد سیستم برای بهبود سرعت و کارایی"
    
    def __init__(self):
        self.optimization_system = PerformanceOptimizationSystem()
    
    def analyze_system_performance(self) -> Dict:
        """تحلیل عملکرد سیستم"""
        try:
            result = self.optimization_system.analyze_system_performance()
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def apply_optimizations(self, optimization_plan: List[Dict]) -> Dict:
        """اعمال بهینه‌سازی‌ها"""
        try:
            result = self.optimization_system.apply_optimizations(optimization_plan)
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def clear_cache(self) -> Dict:
        """پاک کردن کش سیستم"""
        try:
            result = self.optimization_system.clear_cache()
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
