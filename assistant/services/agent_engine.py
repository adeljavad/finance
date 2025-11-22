from langchain_core.tools import BaseTool
from typing import Dict, Any, List, Optional
import json
import logging
import re
import pandas as pd

from .deepseek_api import DeepSeekLLM
from .rag_engine import StableRAGEngine
from .memory_manager import MemoryManager
from .data_manager import UserDataManager

logger = logging.getLogger(__name__)

class AgentEngine:
    """
    موتور ایجنت هوشمند با قابلیت تحلیل داده‌های واقعی کاربر و ابزارهای داینامیک
    """

    def __init__(self):
        self.llm = DeepSeekLLM()
        self.rag = StableRAGEngine()
        self.memory = MemoryManager()
        self.data_manager = UserDataManager()
        
        # مدیر ابزارهای داینامیک
        try:
            from .dynamic_tool_manager import DynamicToolManager
            self.dynamic_manager = DynamicToolManager(self.data_manager, self.llm)
        except ImportError as e:
            logger.warning(f"DynamicToolManager import نشد: {e}")
            self.dynamic_manager = None
        
        # ابزارهای ثابت
        self.static_tools = self._load_static_tools()
        self.static_tool_map = {tool.name: tool for tool in self.static_tools}
        
        logger.info(f"✅ AgentEngine با {len(self.static_tools)} ابزار ثابت راه‌اندازی شد")

    def _load_static_tools(self) -> List[BaseTool]:
        """لود ابزارهای ثابت"""
        tools = []
        try:
            # ابزارهای جستجو
            from .tools.search_tools import DocumentSearchTool, AdvancedFilterTool
            tools.extend([
                DocumentSearchTool(self.data_manager),
                AdvancedFilterTool(self.data_manager),
            ])
        except ImportError as e:
            logger.warning(f"ابزارهای جستجو import نشدند: {e}")
        
        try:
            # ابزارهای محاسباتی
            from .tools.calculation_tools import DataCalculatorTool
            tools.append(DataCalculatorTool(self.data_manager))
        except ImportError as e:
            logger.warning(f"ابزارهای محاسباتی import نشدند: {e}")
        
        try:
            # ابزارهای تحلیلی
            from .tools.analytical_tools import PatternAnalysisTool
            tools.append(PatternAnalysisTool(self.data_manager))
        except ImportError as e:
            logger.warning(f"ابزارهای تحلیلی import نشدند: {e}")
        
        return tools

    def _classify_query(self, query: str, context: str = "") -> str:
        """طبقه‌بندی سوال - نسخه پیشرفته"""
        query_lower = query.lower().strip()
        
        # 1. بررسی وجود داده‌های کاربر
        has_data = self._check_user_data_exists()
        
        if not has_data:
            # اگر داده‌ای نیست، فقط سوالات عمومی پاسخ داده شود
            if any(word in query_lower for word in ['داده', 'سند', 'آپلود', 'فایل']):
                return 'no_data'
            return 'general'
        
        # 2. سوالات ادامه‌دار
        if self._is_follow_up(query, context):
            return 'follow_up'
        
        # 3. سوالات مبتنی بر داده
        if self._is_data_related_query(query):
            return 'data_analysis'
        
        # 4. سوالات عمومی مالی
        if self._is_financial_query(query):
            return 'general_finance'
        
        return 'general'
    
    def _check_user_data_exists(self, user_id: str = "default") -> bool:
        """بررسی وجود داده‌های کاربر"""
        try:
            df = self.data_manager.get_dataframe(user_id, 'accounting_data')
            return df is not None and not df.empty
        except:
            return False
    
    def _is_follow_up(self, query: str, context: str) -> bool:
        """تشخیص سوالات ادامه‌دار"""
        follow_up_patterns = [
            r'^(آره|بله|بلی|حتما|مایلم|می‌خواهم|بفرمایید|ادامه|بیشتر|توضیح|شرح)',
            r'^(yes|yeah|sure|ok|okay|please|more|explain)',
        ]
        
        return context and any(re.search(pattern, query.lower()) for pattern in follow_up_patterns)
    
    def _is_data_related_query(self, query: str) -> bool:
        """تشخیص سوالات مرتبط با داده"""
        data_keywords = [
            'سند', 'اسناد', 'داده', 'دیتا', 'فایل', 'آپلود', 'تاریخ', 'بدهکار', 
            'بستانکار', 'معین', 'تفصیلی', 'تراز', 'مانده', 'جمع', 'میانگین',
            'بیشترین', 'کمترین', 'تعداد', 'شرح', 'توضیحات'
        ]
        return any(keyword in query.lower() for keyword in data_keywords)
    
    def _is_financial_query(self, query: str) -> bool:
        """تشخیص سوالات مالی"""
        financial_keywords = [
            'مالیات', 'حسابداری', 'حسابدار', 'مالی', 'بودجه', 'هزینه', 'درآمد',
            'سود', 'زیان', 'دارایی', 'بدهی', 'سرمایه', 'ترازنامه', 'صورت مالی',
            'نقدینگی', 'نسبت مالی', 'حاشیه سود', 'بازده', 'سرمایه‌گذاری'
        ]
        return any(keyword in query.lower() for keyword in financial_keywords)

    def run(self, query: str, session_id: str = "default", user_id: str = None) -> str:
        """اجرای اصلی با پشتیبانی از ابزارهای داینامیک"""
        if not query or not query.strip():
            return "لطفاً یک سوال معتبر وارد کنید."
        
        if not user_id:
            user_id = session_id
        
        logger.info(f"پردازش سوال: {query}")
        
        try:
            # مدیریت session
            if session_id not in self.memory.active_sessions:
                self.memory.create_session(session_id)
            
            self.memory.add_message(session_id, "user", query)
            context = self.memory.get_context_summary(session_id)
            
            # طبقه‌بندی سوال
            query_type = self._classify_query(query, context)
            logger.info(f"سوال طبقه‌بندی شد به: {query_type}")
            
            # پردازش بر اساس نوع
            if query_type == 'no_data':
                response = self._handle_no_data_query(query)
            
            elif query_type == 'data_analysis':
                response = self._handle_data_analysis_query(query, user_id)
            
            elif query_type == 'follow_up':
                response = self._handle_follow_up(session_id, query)
            
            elif query_type == 'general_finance':
                response = self._ask_llm_directly(query)
            
            else:
                response = self._ask_llm_directly(query)
            
            self.memory.add_message(session_id, "assistant", response)
            return response
            
        except Exception as e:
            logger.error(f"خطا در پردازش سوال: {e}")
            error_msg = f"متأسفانه در پردازش سوال خطایی رخ داد: {str(e)}"
            self.memory.add_message(session_id, "assistant", error_msg)
            return error_msg
    
    def _handle_no_data_query(self, query: str) -> str:
        """پردازش سوالات وقتی داده‌ای موجود نیست"""
        if any(word in query.lower() for word in ['داده', 'سند', 'آپلود', 'فایل']):
            return "📝 در حال حاضر هیچ سند حسابداری آپلود نشده است. لطفاً ابتدا فایل Excel اسناد خود را آپلود کنید تا بتوانم تحلیل‌های دقیق ارائه دهم."
        
        return self._ask_llm_directly(query)
    
    def _handle_data_analysis_query(self, query: str, user_id: str) -> str:
        """پردازش سوالات تحلیلی روی داده‌ها"""
        # 1. ابتدا ابزارهای ثابت را بررسی کن
        static_tool = self._find_static_tool(query)
        if static_tool:
            logger.info(f"استفاده از ابزار ثابت: {static_tool.name}")
            tool_input = json.dumps({"user_id": user_id, "query": query}, ensure_ascii=False)
            result = static_tool.run(tool_input)
            return self._enhance_with_llm(query, result)
        
        # 2. اگر ابزار ثابت نبود و مدیر داینامیک موجود است، ابزار داینامیک تولید کن
        if self.dynamic_manager:
            logger.info("جستجو در ابزارهای داینامیک")
            dynamic_tool = self.dynamic_manager.find_or_create_tool(query, user_id)
            
            if dynamic_tool:
                # استخراج پارامترها از سوال
                parameters = self._extract_parameters_from_query(query, dynamic_tool.name)
                tool_input = json.dumps({
                    "user_id": user_id,
                    **parameters
                }, ensure_ascii=False)
                
                result = dynamic_tool.run(tool_input)
                return self._enhance_with_llm(query, result)
        
        # 3. اگر هیچکدام کار نکرد، از LLM مستقیم استفاده کن
        return self._ask_llm_directly(query)
    
    def _find_static_tool(self, query: str) -> Optional[BaseTool]:
        """پیدا کردن ابزار ثابت مناسب"""
        query_lower = query.lower()
        
        tool_mappings = {
            'document_search': ['جستجو', 'پیدا کن', 'سند', 'تاریخ'],
            'advanced_filter': ['فیلتر', 'شرط'],
            'data_calculator': ['محاسبه', 'نسبت', 'آمار'],
            'pattern_analysis': ['الگو', 'روند', 'تحلیل']
        }
        
        for tool_name, keywords in tool_mappings.items():
            if any(keyword in query_lower for keyword in keywords):
                return self.static_tool_map.get(tool_name)
        
        return None
    
    def _extract_parameters_from_query(self, query: str, tool_name: str) -> Dict:
        """استخراج پارامترها از سوال کاربر"""
        parameters = {}
        
        # استخراج تاریخ
        date_pattern = r'(\d{4}/\d{2}/\d{2})'
        dates = re.findall(date_pattern, query)
        if dates:
            parameters['target_date'] = dates[0]
        
        # استخراج اعداد
        number_pattern = r'(\d[\d,]*\.?\d*)'
        numbers = re.findall(number_pattern, query)
        numbers = [float(n.replace(',', '')) for n in numbers if n.replace(',', '').replace('.', '').isdigit()]
        
        if numbers:
            if 'حداقل' in query or 'از' in query:
                parameters['min_amount'] = min(numbers)
            if 'حداکثر' in query or 'تا' in query:
                parameters['max_amount'] = max(numbers)
            elif len(numbers) == 1:
                parameters['amount'] = numbers[0]
        
        return parameters
    
    def _enhance_with_llm(self, query: str, analysis_result: str) -> str:
        """ارتقای نتیجه با LLM"""
        prompt = f"""
        شما یک تحلیل‌گر مالی حرفه‌ای هستید. بر اساس نتایج تحلیل زیر و سوال کاربر، یک پاسخ کامل و حرفه‌ای ارائه دهید.

        سوال کاربر: {query}

        نتایج تحلیل:
        {analysis_result}

        لطفاً:
        1. نتایج را به زبان ساده تفسیر کنید
        2. نکات کلیدی را برجسته کنید
        3. در صورت نیاز پیشنهاداتی ارائه دهید
        4. پاسخ باید کاملاً حرفه‌ای و کاربردی باشد
        """
        
        messages = [
            {"role": "system", "content": "شما یک مشاور مالی متخصص هستید."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            return self.llm.invoke(messages)
        except Exception as e:
            logger.warning(f"خطا در ارتقای نتیجه، برگشت به نتیجه خام: {e}")
            return f"📊 نتایج تحلیل:\n\n{analysis_result}"
    
    def _handle_follow_up(self, session_id: str, query: str) -> str:
        """پردازش سوالات ادامه‌دار"""
        history = self.memory.get_conversation_history(session_id)
        last_assistant_message = None
        
        for msg in reversed(history):
            if msg["role"] == "assistant":
                last_assistant_message = msg["content"]
                break
        
        if last_assistant_message:
            prompt = f"""
            کاربر در پاسخ به پیام قبلی من گفته: "{query}"
            
            پیام قبلی من به کاربر:
            {last_assistant_message}
            
            لطفاً بر اساس این context، پاسخ مناسب و ادامه‌دار بدهید.
            """
            
            messages = [
                {"role": "system", "content": "شما یک دستیار مالی هستید که مکالمات را به خاطر می‌سپارد و به صورت context-aware پاسخ می‌دهد."},
                {"role": "user", "content": prompt}
            ]
            
            try:
                return self.llm.invoke(messages)
            except Exception as e:
                logger.error(f"خطا در پردازش follow-up: {e}")
        
        return self._ask_llm_directly(query)

    def _ask_llm_directly(self, query: str) -> str:
        """استفاده مستقیم از LLM"""
        messages = [
            {"role": "system", "content": """
            شما یک دستیار مالی متخصص و خوش‌برخورد هستید. 
            به سوالات مالی و حسابداری پاسخ تخصصی دهید.
            برای سوالات غیرمرتبط، مودبانه توضیح دهید که تخصص شما امور مالی است.
            """},
            {"role": "user", "content": query}
        ]
        
        try:
            return self.llm.invoke(messages)
        except Exception as e:
            logger.error(f"خطا در ارتباط با LLM: {e}")
            return "متأسفانه در حال حاضر امکان پاسخگویی وجود ندارد."

    def get_available_tools(self) -> List[str]:
        """دریافت لیست ابزارها"""
        tool_names = [tool.name for tool in self.static_tools]
        
        if self.dynamic_manager:
            stats = self.dynamic_manager.get_tool_statistics()
            tool_names.append(f"{stats.get('total_tools', 0)} ابزار داینامیک")
        
        return tool_names

    def get_system_status(self) -> Dict[str, Any]:
        """وضعیت سیستم"""
        try:
            rag_info = self.rag.get_collection_info()
            
            status = {
                "status": "active",
                "tools_count": len(self.static_tools),
                "available_tools": self.get_available_tools(),
                "rag_documents": rag_info.get("total_documents", 0),
                "rag_engine": rag_info.get("engine", "unknown"),
                "llm_status": "connected",
                "memory_sessions": len(self.memory.active_sessions),
                "data_manager": "active"
            }
            
            if self.dynamic_manager:
                dynamic_stats = self.dynamic_manager.get_tool_statistics()
                status["dynamic_tools"] = dynamic_stats
            
            return status
            
        except Exception as e:
            logger.error(f"خطا در دریافت وضعیت سیستم: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def clear_memory(self, session_id: str = "default"):
        """پاک کردن memory"""
        try:
            self.memory.clear_session(session_id)
            logger.info(f"Memory cleared for session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            return False


    def debug_user_data(self, user_id: str = "default") -> Dict:
        """ابزار دیباگ برای بررسی داده‌های کاربر"""
        try:
            df = self.data_manager.get_dataframe(user_id, 'accounting_data')
            
            if df is None:
                return {"status": "no_data", "message": "هیچ DataFrameی پیدا نشد"}
            
            if df.empty:
                return {"status": "empty_data", "message": "DataFrame خالی است"}
            
            return {
                "status": "has_data", 
                "row_count": len(df),
                "columns": list(df.columns),
                "sample_data": df.head(3).to_dict('records')
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}            