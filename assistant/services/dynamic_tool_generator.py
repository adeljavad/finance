import pandas as pd
import json
import logging
import re
import ast
import uuid
from typing import Dict, Any, Optional, List
from langchain_core.tools import BaseTool

logger = logging.getLogger(__name__)

class DynamicToolGenerator:
    """
    تولید کننده داینامیک ابزارهای پایتون بر اساس سوال کاربر
    """
    
    def __init__(self, data_manager, llm):
        self.data_manager = data_manager
        self.llm = llm
        self.tool_cache = {}  # کش ابزارهای تولید شده
        self.code_templates = self._load_code_templates()
    
    def _load_code_templates(self) -> Dict:
        """لود تمپلیت‌های کد برای انواع سوالات رایج"""
        return {
            "aggregation": """
def analyze_data(df):
    \"\"\"تحلیل تجمیعی داده‌ها\"\"\"
    try:
        result = {}
        {user_specific_code}
        return result
    except Exception as e:
        return {"error": str(e)}
""",
            "filtering": """
def filter_data(df):
    \"\"\"فیلتر کردن داده‌ها\"\"\"
    try:
        filtered_df = df.copy()
        {user_specific_code}
        return filtered_df
    except Exception as e:
        return {"error": str(e)}
""",
            "calculation": """
def calculate_metrics(df):
    \"\"\"محاسبه متریک‌ها\"\"\"
    try:
        metrics = {}
        {user_specific_code}
        return metrics
    except Exception as e:
        return {"error": str(e)}
"""
        }
    
    def generate_tool_for_query(self, query: str, user_id: str) -> Optional[BaseTool]:
        """
        تولید ابزار داینامیک برای سوال کاربر
        """
        try:
            # بررسی کش
            cache_key = f"{user_id}_{hash(query)}"
            if cache_key in self.tool_cache:
                logger.info("ابزار از کش بازیابی شد")
                return self.tool_cache[cache_key]
            
            # دریافت داده‌های کاربر
            df = self.data_manager.get_dataframe(user_id, 'accounting_data')
            if df is None or df.empty:
                return None
            
            # تولید کد پایتون با LLM
            python_code = self._generate_python_code(query, df)
            if not python_code:
                return None
            
            # ایجاد ابزار داینامیک
            dynamic_tool = self._create_dynamic_tool(python_code, query, user_id)
            
            # ذخیره در کش
            self.tool_cache[cache_key] = dynamic_tool
            
            logger.info(f"ابزار داینامیک برای سوال تولید شد: {query[:50]}...")
            return dynamic_tool
            
        except Exception as e:
            logger.error(f"خطا در تولید ابزار داینامیک: {e}")
            return None
    
    def _generate_python_code(self, query: str, df: pd.DataFrame) -> str:
        """
        تولید کد پایتون با استفاده از LLM
        """
        # آماده‌سازی اطلاعات دیتافریم برای LLM
        df_info = self._prepare_dataframe_info(df)
        
        prompt = f"""
        شما یک برنامه‌نویس حرفه‌ای پایتون هستید. لطفاً یک تکه کد پایتون برای پاسخ به سوال کاربر بنویسید.

        سوال کاربر: {query}

        اطلاعات دیتافریم:
        {df_info}

        نکات مهم:
        - تاریخ‌ها به صورت رشته‌ی ۱۰ کاراکتری فارسی هستند (مثال: "1403/01/01")
        - ستون‌های بدهکار و بستانکار شامل مبالغ عددی هستند
        - اگر پاسخ سوال در داده‌ها موجود نیست، پیام مناسبی برگردانید

        ساختار کد:
        1. یک تابع به نام `analyze_query` تعریف کنید که `df` (دیتافریم) را دریافت می‌کند
        2. در تابع، سوال کاربر را تحلیل و پردازش کنید
        3. نتیجه را به صورت دیکشنری یا رشته برگردانید
        4. خطاها را مدیریت کنید

        فقط کد پایتون خالص برگردانید، بدون توضیح اضافی.
        """

        messages = [
            {
                "role": "system",
                "content": "شما یک برنامه‌نویس متخصص پایتون هستید. فقط کد پایتون تولید کنید."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        try:
            response = self.llm.invoke(messages)
            # استخراج کد از پاسخ
            code = self._extract_python_code(response)
            return code
        except Exception as e:
            logger.error(f"خطا در تولید کد: {e}")
            return None
    
    def _prepare_dataframe_info(self, df: pd.DataFrame) -> str:
        """آماده‌سازی اطلاعات دیتافریم برای LLM"""
        info = f"""
        ستون‌های موجود: {list(df.columns)}
        تعداد سطرها: {len(df)}
        نمونه داده‌ها (۳ سطر اول):
        {df.head(3).to_string()}
        
        اطلاعات ستون‌های مهم:
        - تاریخ سند: رشته فارسی (مثال: 1403/01/01)
        - بدهکار: عدد (مجموع: {df['بدهکار'].sum():,.0f})
        - بستانکار: عدد (مجموع: {df['بستانکار'].sum():,.0f})
        """
        return info
    
    def _extract_python_code(self, response: str) -> str:
        """استخراج کد پایتون از پاسخ LLM"""
        # پیدا کردن بلوک کد
        code_blocks = re.findall(r'```python\n(.*?)\n```', response, re.DOTALL)
        if code_blocks:
            return code_blocks[0]
        
        # اگر بلوک کد نبود، کل پاسخ را برگردان
        return response
    
    def _create_dynamic_tool(self, python_code: str, original_query: str, user_id: str) -> BaseTool:
        """ایجاد ابزار داینامیک از کد تولید شده"""
        
        class DynamicAnalysisTool(BaseTool):
            name: str = f"dynamic_tool_{uuid.uuid4().hex[:8]}"
            description: str = f"ابزار داینامیک برای: {original_query}"
            
            def __init__(self, code, data_manager, user_id):
                super().__init__()
                self.python_code = code
                self.data_manager = data_manager
                self.user_id = user_id
            
            def _run(self, tool_input: str) -> str:
                try:
                    # دریافت داده‌های کاربر
                    df = self.data_manager.get_dataframe(self.user_id, 'accounting_data')
                    if df is None or df.empty:
                        return "⚠️ هیچ داده‌ای برای تحلیل موجود نیست."
                    
                    # اجرای کد داینامیک
                    result = self._execute_dynamic_code(df, self.python_code)
                    return result
                    
                except Exception as e:
                    return f"❌ خطا در اجرای تحلیل داینامیک: {str(e)}"
            
            def _execute_dynamic_code(self, df: pd.DataFrame, code: str) -> str:
                """اجرای امن کد پایتون"""
                try:
                    # ایجاد محیط امن برای اجرا
                    local_vars = {'df': df.copy(), 'pd': pd, 'json': json}
                    global_vars = {}
                    
                    # اجرای کد
                    exec(code, global_vars, local_vars)
                    
                    # فراخوانی تابع analyze_query
                    if 'analyze_query' in local_vars:
                        result = local_vars['analyze_query'](df)
                    else:
                        # اگر تابع خاصی نبود، کد را مستقیماً اجرا کن
                        result = local_vars.get('result', 'تحلیل انجام شد اما نتیجه خاصی برگردانده نشد.')
                    
                    return self._format_result(result)
                    
                except Exception as e:
                    return f"خطا در اجرای کد: {str(e)}"
            
            def _format_result(self, result) -> str:
                """فرمت‌دهی نتیجه"""
                if isinstance(result, dict):
                    return json.dumps(result, ensure_ascii=False, indent=2)
                elif isinstance(result, pd.DataFrame):
                    if len(result) > 10:
                        return f"نتایج ({len(result)} سطر):\n{result.head(10).to_string()}\n\n... و {len(result)-10} سطر دیگر"
                    else:
                        return result.to_string()
                elif isinstance(result, (str, int, float)):
                    return str(result)
                else:
                    return f"📊 نتایج تحلیل:\n{str(result)}"
        
        return DynamicAnalysisTool(python_code, self.data_manager, user_id)