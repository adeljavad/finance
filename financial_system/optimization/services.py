"""
سرویس‌های بهینه‌سازی عملکرد برای سیستم مالی هوشمند

این ماژول سرویس‌های زیر را ارائه می‌دهد:
- کش‌گذاری پیشرفته
- پردازش موازی
- مدیریت حافظه
- بهینه‌سازی کوئری‌ها
"""

import logging
import time
import functools
from typing import Any, Callable, Optional, List
from django.core.cache import cache
from django.db import connection, models
from django.db.models import QuerySet
from django.utils import timezone
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import gc

# Import psutil with fallback for optional dependency
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("psutil not available. Memory monitoring features will be limited.")

logger = logging.getLogger(__name__)


class CacheService:
    """سرویس کش‌گذاری پیشرفته"""
    
    # کلیدهای پیشوند برای کش
    CACHE_KEYS = {
        'dashboard_stats': 'dashboard_stats_{company_id}',
        'financial_reports': 'financial_reports_{report_type}_{period_id}',
        'user_session': 'user_session_{user_id}',
        'analysis_results': 'analysis_{analysis_type}_{data_hash}',
        'document_list': 'documents_{company_id}_{page}',
    }
    
    @classmethod
    def initialize(cls):
        """راه‌اندازی سرویس کش"""
        logger.info("سرویس کش‌گذاری پیشرفته راه‌اندازی شد")
    
    @classmethod
    def get_cached_data(cls, key: str, timeout: int = 3600) -> Any:
        """
        دریافت داده از کش
        
        Args:
            key: کلید کش
            timeout: زمان انقضا (ثانیه)
            
        Returns:
            داده کش شده یا None
        """
        try:
            data = cache.get(key)
            if data is not None:
                logger.debug(f"داده از کش بازیابی شد: {key}")
            return data
        except Exception as e:
            logger.error(f"خطا در بازیابی از کش {key}: {e}")
            return None
    
    @classmethod
    def set_cached_data(cls, key: str, data: Any, timeout: int = 3600) -> bool:
        """
        ذخیره داده در کش
        
        Args:
            key: کلید کش
            data: داده برای ذخیره
            timeout: زمان انقضا (ثانیه)
            
        Returns:
            موفقیت عملیات
        """
        try:
            cache.set(key, data, timeout)
            logger.debug(f"داده در کش ذخیره شد: {key} (انقضا: {timeout} ثانیه)")
            return True
        except Exception as e:
            logger.error(f"خطا در ذخیره در کش {key}: {e}")
            return False
    
    @classmethod
    def invalidate_pattern(cls, pattern: str):
        """
        حذف تمام کلیدهای منطبق با الگو
        
        Args:
            pattern: الگوی کلیدها
        """
        try:
            # در Redis می‌توان از دستور KEYS و DEL استفاده کرد
            # در اینجا از منطق ساده استفاده می‌کنیم
            keys_to_delete = []
            for key in cls.CACHE_KEYS.values():
                if pattern in key:
                    keys_to_delete.append(key.format(company_id='*', user_id='*', report_type='*'))
            
            for key_pattern in keys_to_delete:
                cache.delete_pattern(key_pattern)
                
            logger.info(f"کلیدهای منطبق با الگوی {pattern} حذف شدند")
            
        except Exception as e:
            logger.error(f"خطا در حذف الگوی کش {pattern}: {e}")
    
    @classmethod
    def cache_decorator(cls, timeout: int = 3600, key_func: Callable = None):
        """
        دکوراتور برای کش‌گذاری خودکار توابع
        
        Args:
            timeout: زمان انقضای کش
            key_func: تابع برای تولید کلید (اختیاری)
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # تولید کلید کش
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    # تولید کلید بر اساس نام تابع و آرگومان‌ها
                    func_name = func.__name__
                    args_str = str(args) + str(kwargs)
                    cache_key = f"{func_name}_{hash(args_str)}"
                
                # بررسی وجود در کش
                cached_result = cls.get_cached_data(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # اجرای تابع و ذخیره نتیجه
                result = func(*args, **kwargs)
                cls.set_cached_data(cache_key, result, timeout)
                
                return result
            return wrapper
        return decorator


class QueryOptimizationService:
    """سرویس بهینه‌سازی کوئری‌های دیتابیس"""
    
    @classmethod
    def optimize_queryset(cls, queryset: QuerySet, use_select_related: bool = True, 
                         use_prefetch_related: bool = True, max_depth: int = 2) -> QuerySet:
        """
        بهینه‌سازی QuerySet
        
        Args:
            queryset: QuerySet اصلی
            use_select_related: استفاده از select_related برای روابط ForeignKey
            use_prefetch_related: استفاده از prefetch_related برای روابط ManyToMany
            max_depth: حداکثر عمق بهینه‌سازی
            
        Returns:
            QuerySet بهینه‌سازی شده
        """
        optimized_queryset = queryset
        
        try:
            # بهینه‌سازی select_related
            if use_select_related:
                optimized_queryset = cls._apply_select_related(optimized_queryset, max_depth)
            
            # بهینه‌سازی prefetch_related
            if use_prefetch_related:
                optimized_queryset = cls._apply_prefetch_related(optimized_queryset, max_depth)
            
            # فقط گرفتن فیلدهای مورد نیاز
            optimized_queryset = cls._apply_only_fields(optimized_queryset)
            
        except Exception as e:
            logger.warning(f"خطا در بهینه‌سازی QuerySet: {e}")
        
        return optimized_queryset
    
    @classmethod
    def _apply_select_related(cls, queryset: QuerySet, max_depth: int) -> QuerySet:
        """اعمال select_related برای روابط ForeignKey"""
        model = queryset.model
        related_fields = []
        
        # پیدا کردن فیلدهای ForeignKey
        for field in model._meta.get_fields():
            if (isinstance(field, models.ForeignKey) and 
                field.related_model and 
                field.related_model != model):
                related_fields.append(field.name)
        
        if related_fields:
            return queryset.select_related(*related_fields[:max_depth])
        
        return queryset
    
    @classmethod
    def _apply_prefetch_related(cls, queryset: QuerySet, max_depth: int) -> QuerySet:
        """اعمال prefetch_related برای روابط ManyToMany و Reverse ForeignKey"""
        model = queryset.model
        prefetch_fields = []
        
        # پیدا کردن فیلدهای ManyToMany و Reverse ForeignKey
        for field in model._meta.get_fields():
            if (isinstance(field, models.ManyToManyField) or 
                (isinstance(field, models.ForeignKey) and field.auto_created)):
                prefetch_fields.append(field.name)
        
        if prefetch_fields:
            return queryset.prefetch_related(*prefetch_fields[:max_depth])
        
        return queryset
    
    @classmethod
    def _apply_only_fields(cls, queryset: QuerySet) -> QuerySet:
        """اعمال only برای گرفتن فقط فیلدهای مورد نیاز"""
        # این منطق می‌تواند بر اساس آنالیز استفاده از فیلدها پیچیده‌تر شود
        return queryset
    
    @classmethod
    def analyze_query_performance(cls, queryset: QuerySet) -> dict:
        """
        تحلیل عملکرد کوئری
        
        Args:
            queryset: QuerySet برای تحلیل
            
        Returns:
            دیکشنری با اطلاعات عملکرد
        """
        start_time = time.time()
        
        try:
            # اجرای کوئری و گرفتن نتایج
            results = list(queryset)
            execution_time = time.time() - start_time
            
            # تحلیل کوئری‌ها
            query_count = len(connection.queries)
            total_query_time = sum(float(q['time']) for q in connection.queries)
            
            performance_info = {
                'execution_time': execution_time,
                'query_count': query_count,
                'total_query_time': total_query_time,
                'result_count': len(results),
                'average_query_time': total_query_time / query_count if query_count > 0 else 0,
                'queries': connection.queries[-query_count:] if query_count > 0 else []
            }
            
            return performance_info
            
        except Exception as e:
            logger.error(f"خطا در تحلیل عملکرد کوئری: {e}")
            return {'error': str(e)}


class ParallelProcessingService:
    """سرویس پردازش موازی"""
    
    @classmethod
    def process_in_parallel(cls, tasks: List[Callable], max_workers: int = None, 
                          use_threads: bool = True) -> List[Any]:
        """
        پردازش لیست وظایف به صورت موازی
        
        Args:
            tasks: لیست توابع برای اجرا
            max_workers: حداکثر تعداد کارگران
            use_threads: استفاده از نخ‌ها (در غیر این صورت از پردازه‌ها)
            
        Returns:
            لیست نتایج
        """
        if not tasks:
            return []
        
        if max_workers is None:
            max_workers = min(len(tasks), 4)  # تعداد منطقی کارگران
        
        try:
            if use_threads:
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    results = list(executor.map(cls._safe_execute, tasks))
            else:
                with ProcessPoolExecutor(max_workers=max_workers) as executor:
                    results = list(executor.map(cls._safe_execute, tasks))
            
            return results
            
        except Exception as e:
            logger.error(f"خطا در پردازش موازی: {e}")
            # اجرای سریع در صورت خطا
            return [cls._safe_execute(task) for task in tasks]
    
    @classmethod
    def _safe_execute(cls, task: Callable) -> Any:
        """اجرای ایمن تابع با مدیریت خطا"""
        try:
            return task()
        except Exception as e:
            logger.error(f"خطا در اجرای وظیفه موازی: {e}")
            return None
    
    @classmethod
    def batch_process(cls, data: List[Any], process_func: Callable, 
                     batch_size: int = 100, max_workers: int = None) -> List[Any]:
        """
        پردازش دسته‌ای داده‌ها به صورت موازی
        
        Args:
            data: لیست داده‌ها
            process_func: تابع پردازش
            batch_size: اندازه هر دسته
            max_workers: حداکثر تعداد کارگران
            
        Returns:
            لیست نتایج
        """
        if not data:
            return []
        
        # تقسیم داده به دسته‌ها
        batches = [data[i:i + batch_size] for i in range(0, len(data), batch_size)]
        
        # ایجاد توابع برای پردازش هر دسته
        tasks = [functools.partial(cls._process_batch, batch, process_func) 
                for batch in batches]
        
        # اجرای موازی
        batch_results = cls.process_in_parallel(tasks, max_workers)
        
        # ترکیب نتایج
        results = []
        for batch_result in batch_results:
            if batch_result is not None:
                results.extend(batch_result)
        
        return results
    
    @classmethod
    def _process_batch(cls, batch: List[Any], process_func: Callable) -> List[Any]:
        """پردازش یک دسته داده"""
        return [process_func(item) for item in batch]


class MemoryManagementService:
    """سرویس مدیریت حافظه"""
    
    @classmethod
    def get_memory_usage(cls) -> dict:
        """دریافت اطلاعات استفاده از حافظه"""
        if not PSUTIL_AVAILABLE:
            return {
                'rss_mb': 0,
                'vms_mb': 0,
                'percent': 0,
                'available_mb': 0,
                'total_mb': 0,
                'psutil_available': False
            }
        
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
                'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
                'percent': process.memory_percent(),
                'available_mb': psutil.virtual_memory().available / 1024 / 1024,
                'total_mb': psutil.virtual_memory().total / 1024 / 1024,
                'psutil_available': True
            }
        except Exception as e:
            logger.error(f"خطا در دریافت اطلاعات حافظه: {e}")
            return {
                'rss_mb': 0,
                'vms_mb': 0,
                'percent': 0,
                'available_mb': 0,
                'total_mb': 0,
                'psutil_available': False,
                'error': str(e)
            }
    
    @classmethod
    def optimize_memory(cls):
        """بهینه‌سازی استفاده از حافظه"""
        try:
            # پاکسازی حافظه کش Django
            cache.clear()
            logger.info("حافظه کش پاکسازی شد")
            
            # اجرای جمع‌آوری زباله
            collected = gc.collect()
            logger.info(f"جمع‌آوری زباله انجام شد: {collected} شیء آزاد شد")
            
            # اطلاعات حافظه پس از بهینه‌سازی
            memory_info = cls.get_memory_usage()
            logger.info(f"وضعیت حافظه پس از بهینه‌سازی: {memory_info}")
            
            return memory_info
            
        except Exception as e:
            logger.error(f"خطا در بهینه‌سازی حافظه: {e}")
            return None
    
    @classmethod
    def monitor_memory_usage(cls, threshold_mb: float = 500):
        """
        مانیتورینگ استفاده از حافظه و هشدار در صورت превы آستانه
        
        Args:
            threshold_mb: آستانه حافظه (مگابایت)
        """
        memory_info = cls.get_memory_usage()
        
        # فقط اگر psutil در دسترس باشد و اطلاعات معتبر داشته باشیم
        if memory_info.get('psutil_available') and memory_info['rss_mb'] > threshold_mb:
            from financial_system.services import SystemAlertService
            SystemAlertService.alert_high_memory_usage(
                usage_percent=memory_info['percent'],
                threshold=80
            )
            
            # اجرای بهینه‌سازی خودکار
            cls.optimize_memory()
        elif not memory_info.get('psutil_available'):
            logger.debug("psutil در دسترس نیست - مانیتورینگ حافظه غیرفعال")


class PerformanceMonitoringService:
    """سرویس مانیتورینگ عملکرد"""
    
    @classmethod
    def monitor_view_performance(cls, view_func: Callable) -> Callable:
        """
        دکوراتور برای مانیتورینگ عملکرد ویوها
        
        Args:
            view_func: تابع ویو
            
        Returns:
            تابع پوشش داده شده
        """
        @functools.wraps(view_func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_queries = len(connection.queries)
            
            try:
                response = view_func(*args, **kwargs)
                execution_time = time.time() - start_time
                query_count = len(connection.queries) - start_queries
                
                # ثبت لاگ عملکرد
                cls._log_performance(view_func.__name__, execution_time, query_count)
                
                # هشدار در صورت عملکرد ضعیف
                if execution_time > 5.0:  # بیش از 5 ثانیه
                    from financial_system.services import SystemAlertService
                    SystemAlertService.alert_high_memory_usage(
                        usage_percent=0,  # اینجا باید منطق بهتری داشته باشیم
                        threshold=0
                    )
                
                return response
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"خطا در ویو {view_func.__name__}: {e} (زمان: {execution_time:.2f}ثانیه)")
                raise
        
        return wrapper
    
    @classmethod
    def _log_performance(cls, view_name: str, execution_time: float, query_count: int):
        """ثبت لاگ عملکرد"""
        performance_level = 'GOOD'
        if execution_time > 2.0:
            performance_level = 'SLOW'
        elif execution_time > 5.0:
            performance_level = 'CRITICAL'
        
        logger.info(
            f"عملکرد ویو {view_name}: "
            f"زمان={execution_time:.2f}ثانیه, "
            f"کوئری‌ها={query_count}, "
            f"سطح={performance_level}"
        )


# دکوراتورهای کاربردی برای استفاده آسان
cache_view = CacheService.cache_decorator
monitor_performance = PerformanceMonitoringService.monitor_view_performance
