import pandas as pd
import json
import logging
import re
import uuid
import sqlite3
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ToolParameter(BaseModel):
    """مدل پارامترهای ابزار"""
    name: str
    type: str
    description: str
    required: bool = True

class DynamicToolDefinition(BaseModel):
    """تعریف کامل یک ابزار داینامیک"""
    tool_id: str
    name: str
    description: str
    python_code: str
    parameters: List[ToolParameter]
    created_at: str
    usage_count: int = 0
    success_rate: float = 0.0

class DynamicToolManager:
    """
    مدیریت کامل ابزارهای داینامیک - با قابلیت استفاده مجدد و پارامترهای پویا
    """
    
    def __init__(self, data_manager, llm):
        self.data_manager = data_manager
        self.llm = llm
        self.tools_db = "dynamic_tools.db"
        self._init_database()
    
    def _init_database(self):
        """ایجاد دیتابیس ابزارها"""
        try:
            conn = sqlite3.connect(self.tools_db)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dynamic_tools (
                    tool_id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    python_code TEXT,
                    parameters TEXT,
                    created_at TEXT,
                    usage_count INTEGER,
                    success_count INTEGER
                )
            ''')
            conn.commit()
            conn.close()
            logger.info("دیتابیس ابزارهای داینامیک راه‌اندازی شد")
        except Exception as e:
            logger.error(f"خطا در راه‌اندازی دیتابیس: {e}")
    
    def find_or_create_tool(self, query: str, user_id: str) -> Optional[BaseTool]:
        """
        پیدا کردن ابزار موجود یا ایجاد ابزار جدید
        """
        try:
            # جستجو در ابزارهای موجود
            existing_tool = self._find_similar_tool(query)
            if existing_tool:
                logger.info(f"ابزار مشابه پیدا شد: {existing_tool.name}")
                return self._create_tool_instance(existing_tool, user_id)
            
            # ایجاد ابزار جدید
            logger.info("ایجاد ابزار داینامیک جدید")
            new_tool_def = self._create_new_tool_definition(query, user_id)
            if new_tool_def:
                self._save_tool_to_db(new_tool_def)
                return self._create_tool_instance(new_tool_def, user_id)
            
            return None
            
        except Exception as e:
            logger.error(f"خطا در پیدا کردن/ایجاد ابزار: {e}")
            return None
    
    def _find_similar_tool(self, query: str) -> Optional[DynamicToolDefinition]:
        """پیدا کردن ابزار مشابه در دیتابیس"""
        try:
            conn = sqlite3.connect(self.tools_db)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM dynamic_tools")
            tools_data = cursor.fetchall()
            conn.close()
            
            for tool_data in tools_data:
                tool_def = self._deserialize_tool(tool_data)
                if self._is_tool_similar(tool_def, query):
                    return tool_def
            
            return None
            
        except Exception as e:
            logger.error(f"خطا در جستجوی ابزار مشابه: {e}")
            return None
    
    def _is_tool_similar(self, tool_def: DynamicToolDefinition, query: str) -> bool:
        """بررسی مشابهت ابزار با سوال"""
        # اینجا می‌توان از LLM برای تشخیص مشابهت استفاده کرد
        query_lower = query.lower()
        tool_desc_lower = tool_def.description.lower()
        
        # کلمات کلیدی مشترک
        common_keywords = ['تاریخ', 'بدهکار', 'بستانکار', 'سند', 'اسناد', 'جمع', 'میانگین']
        
        tool_keywords = set(tool_desc_lower.split())
        query_keywords = set(query_lower.split())
        
        common_words = tool_keywords.intersection(query_keywords)
        common_financial = set(common_keywords).intersection(query_keywords)
        
        return len(common_words) >= 2 or len(common_financial) >= 2
    
    def _create_new_tool_definition(self, query: str, user_id: str) -> Optional[DynamicToolDefinition]:
        """ایجاد تعریف جدید برای ابزار"""
        try:
            # دریافت داده‌های کاربر برای تحلیل
            df = self.data_manager.get_dataframe(user_id, 'accounting_data')
            if df is None:
                return None
            
            # تولید کد و پارامترها با LLM
            tool_spec = self._generate_tool_specification(query, df)
            if not tool_spec:
                return None
            
            # ایجاد ابزار
            tool_def = DynamicToolDefinition(
                tool_id=f"tool_{uuid.uuid4().hex[:8]}",
                name=tool_spec["name"],
                description=tool_spec["description"],
                python_code=tool_spec["python_code"],
                parameters=tool_spec["parameters"],
                created_at=datetime.now().isoformat()
            )
            
            return tool_def
            
        except Exception as e:
            logger.error(f"خطا در ایجاد تعریف ابزار جدید: {e}")
            return None
    
    def _generate_tool_specification(self, query: str, df: pd.DataFrame) -> Optional[Dict]:
        """تولید مشخصات کامل ابزار با LLM"""
        df_info = self._prepare_dataframe_info(df)
        
        prompt = f"""
        شما یک طراح ابزارهای تحلیل داده هستید. لطفاً برای سوال کاربر یک ابزار پایتون با پارامترهای پویا طراحی کنید.

        سوال کاربر: {query}

        اطلاعات دیتافریم:
        {df_info}

        خروجی مورد انتظار:
        1. یک نام معنادار برای ابزار (به فارسی)
        2. توضیح کامل ابزار
        3. لیست پارامترهای مورد نیاز
        4. کد پایتون با قابلیت استفاده مجدد

        فرمت خروجی (JSON):
        {{
            "name": "نام ابزار",
            "description": "توضیح کامل ابزار",
            "parameters": [
                {{
                    "name": "نام پارامتر",
                    "type": "نوع داده",
                    "description": "توضیح پارامتر",
                    "required": true/false
                }}
            ],
            "python_code": "کد پایتون"
        }}

        نکات مهم در کد:
        - از پارامترهای تابع استفاده کنید، نه مقادیر ثابت
        - خطاها را مدیریت کنید
        - خروجی را به صورت dict یا str برگردانید
        - تابع باید analyze_query نام داشته باشد و پارامترهای تعریف شده را بگیرد
        """

        messages = [
            {
                "role": "system",
                "content": "شما یک متخصص طراحی ابزارهای تحلیل داده هستید. فقط JSON ساختاریافته برگردانید."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        try:
            response = self.llm.invoke(messages)
            tool_spec = self._extract_json_from_response(response)
            
            # اعتبارسنجی ساختار
            if self._validate_tool_spec(tool_spec):
                return tool_spec
            else:
                logger.error("ساختار ابزار تولید شده نامعتبر است")
                return None
                
        except Exception as e:
            logger.error(f"خطا در تولید مشخصات ابزار: {e}")
            return None
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict]:
        """استخراج JSON از پاسخ LLM"""
        try:
            # پیدا کردن JSON در پاسخ
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except Exception as e:
            logger.error(f"خطا در استخراج JSON: {e}")
        
        return None
    
    def _validate_tool_spec(self, tool_spec: Dict) -> bool:
        """اعتبارسنجی ساختار ابزار"""
        required_fields = ['name', 'description', 'parameters', 'python_code']
        return all(field in tool_spec for field in required_fields)
    
    def _create_tool_instance(self, tool_def: DynamicToolDefinition, user_id: str) -> BaseTool:
        """ایجاد نمونه ابزار از تعریف"""
        
        class ReusableDynamicTool(BaseTool):
            name: str = tool_def.name
            description: str = tool_def.description
            
            def _init__(self, tool_definition, data_manager, user_id):
                super()._init__()
                self.tool_def = tool_definition
                self.data_manager = data_manager
                self.user_id = user_id
            
            def _run(self, tool_input: str) -> str:
                try:
                    # پارس کردن ورودی
                    input_data = json.loads(tool_input) if isinstance(tool_input, str) else tool_input
                    
                    # دریافت داده‌ها
                    df = self.data_manager.get_dataframe(self.user_id, 'accounting_data')
                    if df is None:
                        return "⚠️ هیچ داده‌ای برای تحلیل موجود نیست."
                    
                    # اجرای کد با پارامترها
                    result = self._execute_with_parameters(df, self.tool_def.python_code, input_data)
                    
                    # آپدیت آمار استفاده
                    self._update_tool_stats(self.tool_def.tool_id, success=True)
                    
                    return result
                    
                except Exception as e:
                    # آپدیت آمار خطا
                    self._update_tool_stats(self.tool_def.tool_id, success=False)
                    return f"❌ خطا در اجرای ابزار: {str(e)}"
            
            def _execute_with_parameters(self, df: pd.DataFrame, code: str, parameters: Dict) -> str:
                """اجرای کد با پارامترهای پویا"""
                try:
                    # ایجاد محیط اجرا
                    local_vars = {
                        'df': df.copy(),
                        'pd': pd,
                        'json': json,
                        'parameters': parameters
                    }
                    
                    # اجرای کد
                    exec(code, {}, local_vars)
                    
                    # فراخوانی تابع با پارامترها
                    if 'analyze_query' in local_vars:
                        # استخراج پارامترهای مورد نیاز از کد
                        required_params = self._extract_required_parameters(code)
                        
                        # آماده‌سازی آرگومان‌ها
                        args = {}
                        for param in required_params:
                            if param in parameters:
                                args[param] = parameters[param]
                            else:
                                args[param] = None
                        
                        result = local_vars['analyze_query'](df, **args)
                    else:
                        result = "تابع analyze_query در کد یافت نشد"
                    
                    return self._format_result(result)
                    
                except Exception as e:
                    return f"خطا در اجرای کد: {str(e)}"
            
            def _extract_required_parameters(self, code: str) -> List[str]:
                """استخراج پارامترهای مورد نیاز از کد"""
                # این یک پیاده‌سازی ساده است - می‌توان بهبود یابد
                param_pattern = r'def analyze_query\(df, (.*?)\):'
                match = re.search(param_pattern, code)
                if match:
                    params_str = match.group(1)
                    return [p.strip() for p in params_str.split(',') if p.strip()]
                return []
            
            def _format_result(self, result) -> str:
                """فرمت‌دهی نتیجه"""
                if isinstance(result, dict):
                    return json.dumps(result, ensure_ascii=False, indent=2)
                elif isinstance(result, pd.DataFrame):
                    if len(result) > 10:
                        return f"نتایج ({len(result)} سطر):\n{result.head(10).to_string()}\n\n... و {len(result)-10} سطر دیگر"
                    else:
                        return result.to_string()
                else:
                    return str(result)
            
            def _update_tool_stats(self, tool_id: str, success: bool):
                """آپدیت آمار استفاده از ابزار"""
                try:
                    conn = sqlite3.connect(self.tools_db)
                    cursor = conn.cursor()
                    
                    if success:
                        cursor.execute(
                            "UPDATE dynamic_tools SET usage_count = usage_count + 1, success_count = success_count + 1 WHERE tool_id = ?",
                            (tool_id,)
                        )
                    else:
                        cursor.execute(
                            "UPDATE dynamic_tools SET usage_count = usage_count + 1 WHERE tool_id = ?",
                            (tool_id,)
                        )
                    
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logger.error(f"خطا در آپدیت آمار ابزار: {e}")
        
        return ReusableDynamicTool(tool_def, self.data_manager, user_id)
    
    def _save_tool_to_db(self, tool_def: DynamicToolDefinition):
        """ذخیره ابزار در دیتابیس"""
        try:
            conn = sqlite3.connect(self.tools_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO dynamic_tools (tool_id, name, description, python_code, parameters, created_at, usage_count, success_count)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0)
            ''', (
                tool_def.tool_id,
                tool_def.name,
                tool_def.description,
                tool_def.python_code,
                json.dumps([param.dict() for param in tool_def.parameters]),
                tool_def.created_at
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"ابزار جدید ذخیره شد: {tool_def.name}")
            
        except Exception as e:
            logger.error(f"خطا در ذخیره ابزار: {e}")
    
    def _deserialize_tool(self, db_data) -> DynamicToolDefinition:
        """تبدیل داده دیتابیس به ابزار"""
        return DynamicToolDefinition(
            tool_id=db_data[0],
            name=db_data[1],
            description=db_data[2],
            python_code=db_data[3],
            parameters=[ToolParameter(**p) for p in json.loads(db_data[4])],
            created_at=db_data[5],
            usage_count=db_data[6]
        )
    
    def get_tool_statistics(self) -> Dict:
        """دریافت آمار ابزارها"""
        try:
            conn = sqlite3.connect(self.tools_db)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*), SUM(usage_count) FROM dynamic_tools")
            total_tools, total_usage = cursor.fetchone()
            
            cursor.execute("SELECT name, usage_count FROM dynamic_tools ORDER BY usage_count DESC LIMIT 5")
            popular_tools = cursor.fetchall()
            
            conn.close()
            
            return {
                "total_tools": total_tools,
                "total_usage": total_usage,
                "popular_tools": popular_tools
            }
            
        except Exception as e:
            logger.error(f"خطا در دریافت آمار: {e}")
            return {}

    # در dynamic_tool_manager.py - به کلاس DynamicToolManager اضافه کن

    def get_all_tools(self) -> List[DynamicToolDefinition]:
        """دریافت تمام ابزارهای داینامیک"""
        try:
            conn = sqlite3.connect(self.tools_db)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM dynamic_tools")
            tools_data = cursor.fetchall()
            conn.close()
            
            return [self._deserialize_tool(data) for data in tools_data]
            
        except Exception as e:
            logger.error(f"خطا در دریافت ابزارها: {e}")
            return []

    def get_tool_code(self, tool_id: str) -> Optional[str]:
        """دریافت کد یک ابزار خاص"""
        try:
            conn = sqlite3.connect(self.tools_db)
            cursor = conn.cursor()
            
            cursor.execute("SELECT python_code FROM dynamic_tools WHERE tool_id = ?", (tool_id,))
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"خطا در دریافت کد ابزار: {e}")
            return None        