# assistant/services/agent_engine.py
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

# در agent_engine.py
class AgentEngine:
    def __init__(self):
        self.llm = DeepSeekLLM()
        self.rag = StableRAGEngine()
        self.memory = MemoryManager()
        self.data_manager = UserDataManager()
        
        # مدیر ابزارهای داینامیک
        from .dynamic_tool_manager import DynamicToolManager
        self.dynamic_manager = DynamicToolManager(self.data_manager, self.llm)
        
        # ابزارهای ثابت
        self.static_tools = self._load_static_tools()
        self.static_tool_map = {tool.name: tool for tool in self.static_tools}
    
    def _handle_data_analysis_query(self, query: str, user_id: str) -> str:
        """پردازش سوالات تحلیلی با سیستم داینامیک پیشرفته"""
        # 1. ابزارهای ثابت
        static_tool = self._find_static_tool(query)
        if static_tool:
            logger.info(f"استفاده از ابزار ثابت: {static_tool.name}")
            tool_input = json.dumps({"user_id": user_id, "query": query}, ensure_ascii=False)
            result = static_tool.run(tool_input)
            return self._enhance_with_llm(query, result)
        
        # 2. ابزارهای داینامیک
        logger.info("جستجو در ابزارهای داینامیک")
        dynamic_tool = self.dynamic_manager.find_or_create_tool(query, user_id)
        
        if dynamic_tool:
            # استخراج پارامترها از سوال با LLM
            parameters = self._extract_parameters_from_query(query, dynamic_tool.name)
            tool_input = json.dumps({
                "user_id": user_id,
                **parameters
            }, ensure_ascii=False)
            
            result = dynamic_tool.run(tool_input)
            return self._enhance_with_llm(query, result)
        
        # 3. fallback به LLM مستقیم
        return self._ask_llm_directly(query)
    
    def _extract_parameters_from_query(self, query: str, tool_name: str) -> Dict:
        """استخراج پارامترها از سوال کاربر با LLM"""
        prompt = f"""
        سوال کاربر: {query}
        نام ابزار: {tool_name}
        
        لطفاً پارامترهای مورد نیاز برای این ابزار را از سوال کاربر استخراج کنید.
        خروجی باید یک JSON باشد.
        """
        
        # پیاده‌سازی ساده - می‌توان با LLM کامل‌تر شود
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
        
        return parameters