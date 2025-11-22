"""
سیستم راهنمای چت بات مالی
این سیستم به صورت خودکار تمام ابزارهای موجود را کشف کرده و راهنمای جامعی ارائه می‌دهد
"""

import os
import importlib
import inspect
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from langchain.tools import BaseTool
from pydantic import BaseModel


@dataclass
class ToolInfo:
    """اطلاعات کامل یک ابزار مالی"""
    name: str
    description: str
    category: str
    input_schema: Optional[BaseModel] = None
    usage_examples: List[str] = None
    parameters: List[Dict[str, str]] = None
    file_path: str = None
    
    def __post_init__(self):
        if self.usage_examples is None:
            self.usage_examples = []
        if self.parameters is None:
            self.parameters = []


class FinancialHelpSystem:
    """سیستم راهنمای جامع برای ابزارهای مالی"""
    
    def __init__(self):
        self.tools_registry: Dict[str, ToolInfo] = {}
        self.categories = {
            "نسبت‌های مالی": "تحلیل و محاسبه نسبت‌های مالی مختلف",
            "جریان نقدی": "شبیه‌سازی و تحلیل جریان وجوه نقد",
            "تشخیص تقلب": "شناسایی الگوها و موارد مشکوک مالی",
            "انطباق و یکپارچگی": "بررسی انطباق با استانداردها و یکپارچگی داده‌ها",
            "تحلیل مالی": "تحلیل‌های جامع و گزارش‌های مالی",
            "اورکستراسیون حسابرسی": "هماهنگی و مدیریت فرآیندهای حسابرسی"
        }
        self._discover_tools()
    
    def _discover_tools(self) -> None:
        """کشف خودکار تمام ابزارهای موجود در پوشه tools"""
        tools_dir = os.path.join(os.path.dirname(__file__), "tools")
        
        # لیست تمام فایل‌های پایتون در پوشه tools
        for file_name in os.listdir(tools_dir):
            if file_name.endswith('.py') and not file_name.startswith('__'):
                module_name = file_name[:-3]  # حذف .py
                self._scan_tools_module(module_name, os.path.join(tools_dir, file_name))
    
    def _scan_tools_module(self, module_name: str, file_path: str) -> None:
        """اسکن یک ماژول برای یافتن ابزارهای LangChain"""
        try:
            module = importlib.import_module(f"financial_system.tools.{module_name}")
            
            # یافتن تمام کلاس‌هایی که از BaseTool ارث‌بری می‌کنند
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, BaseTool) and 
                    obj != BaseTool and 
                    hasattr(obj, 'name') and 
                    hasattr(obj, 'description')):
                    
                    # استخراج اطلاعات ابزار
                    tool_info = self._extract_tool_info(obj, module_name, file_path)
                    if tool_info:
                        self.tools_registry[tool_info.name] = tool_info
                        
        except Exception as e:
            # اگر خطا مربوط به Django settings است، به جای چاپ خطا، از fallback استفاده کن
            if "DJANGO_SETTINGS_MODULE" in str(e) or "settings are not configured" in str(e):
                # استفاده از fallback برای ابزارهای شناخته شده
                self._add_fallback_tools(module_name)
            else:
                print(f"خطا در اسکن ماژول {module_name}: {e}")
    
    def _add_fallback_tools(self, module_name: str) -> None:
        """اضافه کردن ابزارهای fallback زمانی که import با خطا مواجه می‌شود"""
        fallback_tools = {
            'financial_ratio_tools': [
                ('current_ratio_calculation', 'محاسبه نسبت جاری (Current Ratio)', 'نسبت‌های مالی'),
                ('quick_ratio_calculation', 'محاسبه نسبت آنی (Quick Ratio) - بدون موجودی کالا', 'نسبت‌های مالی'),
                ('debt_to_equity_calculation', 'محاسبه نسبت بدهی به حقوق صاحبان سهام (Debt-to-Equity)', 'نسبت‌های مالی'),
                ('return_on_assets_calculation', 'محاسبه نرخ بازده دارایی (Return on Assets - ROA)', 'نسبت‌های مالی'),
                ('return_on_equity_calculation', 'محاسبه نرخ بازده حقوق صاحبان سهام (Return on Equity - ROE)', 'نسبت‌های مالی'),
                ('inventory_turnover_calculation', 'محاسبه گردش موجودی کالا (Inventory Turnover)', 'نسبت‌های مالی')
            ],
            'cash_flow_tools': [
                ('cash_flow_simulation', 'شبیه‌سازی جریان وجوه نقد (روش غیرمستقیم) برای یک دوره مالی خاص', 'جریان نقدی')
            ],
            'fraud_detection_tools': [
                ('threshold_hit_detection', 'شناسایی اسناد با مبالغ برابر یا بیشتر از سقف مجاز انتقال وجه', 'تشخیص تقلب'),
                ('round_number_bias_detection', 'شناسایی اسناد با مبالغی که رقم آخرشان صفر است (Round-Number Bias)', 'تشخیص تقلب'),
                ('end_of_period_rush_detection', 'شناسایی اسنادی که در روزهای پایانی دوره ثبت شده‌اند (End-of-Period Rush)', 'تشخیص تقلب'),
                ('duplicate_document_detection', 'شناسایی اسناد تکراری در یک دوره مالی', 'تشخیص تقلب'),
                ('description_similarity_detection', 'شناسایی اسناد با توصیف‌های مشابه (تشابه بیش از 90%)', 'تشخیص تقلب')
            ],
            'integrity_compliance_tools': [
                ('integrity_check', 'بررسی یکپارچگی داده‌های مالی و انطباق با استانداردها', 'انطباق و یکپارچگی'),
                ('compliance_audit', 'بررسی انطباق با قوانین و مقررات مالی', 'انطباق و یکپارچگی')
            ],
            'financial_analysis_tools': [
                ('analyze_financial_ratios', 'تحلیل جامع نسبت‌های مالی', 'تحلیل مالی'),
                ('detect_financial_anomalies', 'شناسایی انحرافات و ناهنجاری‌های مالی', 'تحلیل مالی'),
                ('generate_financial_report', 'تولید گزارش مالی بر اساس نوع درخواست', 'تحلیل مالی'),
                ('generate_four_column_balance_sheet', 'تولید ترازنامه چهارستونی برای یک فصل خاص', 'تحلیل مالی'),
                ('analyze_seasonal_performance', 'تحلیل عملکرد فصلی شرکت', 'تحلیل مالی'),
                ('generate_comprehensive_financial_report', 'تولید گزارش مالی جامع', 'تحلیل مالی')
            ]
        }
        
        if module_name in fallback_tools:
            for tool_name, description, category in fallback_tools[module_name]:
                if tool_name not in self.tools_registry:
                    tool_info = ToolInfo(
                        name=tool_name,
                        description=description,
                        category=category,
                        usage_examples=self._generate_usage_examples(tool_name, category),
                        parameters=[],
                        file_path=f"financial_system/tools/{module_name}.py"
                    )
                    self.tools_registry[tool_name] = tool_info
    
    def _extract_tool_info(self, tool_class, module_name: str, file_path: str) -> Optional[ToolInfo]:
        """استخراج اطلاعات کامل از یک کلاس ابزار"""
        try:
            # تعیین دسته‌بندی بر اساس نام ماژول
            category = self._determine_category(module_name)
            
            # استخراج پارامترهای ورودی
            parameters = []
            if hasattr(tool_class, 'args_schema'):
                schema_class = tool_class.args_schema
                if hasattr(schema_class, 'schema'):
                    schema = schema_class.schema()
                    if 'properties' in schema:
                        for param_name, param_info in schema['properties'].items():
                            parameters.append({
                                'name': param_name,
                                'type': param_info.get('type', 'string'),
                                'description': param_info.get('description', 'بدون توضیح'),
                                'required': param_name in schema.get('required', [])
                            })
            
            # تولید مثال‌های استفاده
            usage_examples = self._generate_usage_examples(tool_class.name, category)
            
            return ToolInfo(
                name=tool_class.name,
                description=tool_class.description,
                category=category,
                input_schema=tool_class.args_schema if hasattr(tool_class, 'args_schema') else None,
                usage_examples=usage_examples,
                parameters=parameters,
                file_path=file_path
            )
            
        except Exception as e:
            print(f"خطا در استخراج اطلاعات ابزار {tool_class.name}: {e}")
            return None
    
    def _determine_category(self, module_name: str) -> str:
        """تعیین دسته‌بندی ابزار بر اساس نام ماژول"""
        category_map = {
            'financial_ratio_tools': 'نسبت‌های مالی',
            'cash_flow_tools': 'جریان نقدی',
            'fraud_detection_tools': 'تشخیص تقلب',
            'integrity_compliance_tools': 'انطباق و یکپارچگی',
            'financial_analysis_tools': 'تحلیل مالی',
            'audit_orchestration_tools': 'اورکستراسیون حسابرسی',
            'comparison_tools': 'تحلیل مالی',
            'import_assistance_tools': 'تحلیل مالی'
        }
        
        return category_map.get(module_name, 'تحلیل مالی')
    
    def _generate_usage_examples(self, tool_name: str, category: str) -> List[str]:
        """تولید مثال‌های استفاده برای ابزار"""
        examples_map = {
            'current_ratio_calculation': [
                "نسبت جاری شرکت برای دوره مالی ۱ چقدر است؟",
                "محاسبه نسبت جاری برای شرکت ما",
                "نسبت جاری دوره ۱ را تحلیل کن"
            ],
            'quick_ratio_calculation': [
                "نسبت آنی شرکت را محاسبه کن",
                "نسبت سریع برای دوره مالی ۱ چقدر است؟"
            ],
            'debt_to_equity_calculation': [
                "نسبت بدهی به حقوق صاحبان سهام شرکت چقدر است؟",
                "تحلیل اهرم مالی شرکت"
            ],
            'cash_flow_simulation': [
                "جریان نقدی شرکت را شبیه‌سازی کن",
                "تحلیل جریان وجوه نقد برای دوره ۱"
            ],
            'threshold_hit_detection': [
                "اسناد مشکوک با مبالغ بالا را پیدا کن",
                "کنترل سقف انتقال وجه در دوره مالی"
            ],
            'round_number_bias_detection': [
                "اسناد با مبالغ رند را شناسایی کن",
                "بررسی bias مبالغ رند در اسناد"
            ],
            'duplicate_document_detection': [
                "اسناد تکراری را پیدا کن",
                "کنترل تکراری بودن شماره اسناد"
            ]
        }
        
        return examples_map.get(tool_name, [
            f"از ابزار {tool_name} برای تحلیل مالی استفاده کن",
            f"تحلیل {category} با ابزار {tool_name}"
        ])
    
    def get_tools_by_category(self) -> Dict[str, List[ToolInfo]]:
        """دریافت ابزارها گروه‌بندی شده بر اساس دسته"""
        categorized_tools = {}
        for category in self.categories:
            categorized_tools[category] = []
        
        for tool in self.tools_registry.values():
            if tool.category in categorized_tools:
                categorized_tools[tool.category].append(tool)
            else:
                categorized_tools['تحلیل مالی'].append(tool)
        
        return categorized_tools
    
    def get_tool_info(self, tool_name: str) -> Optional[ToolInfo]:
        """دریافت اطلاعات کامل یک ابزار خاص"""
        return self.tools_registry.get(tool_name)
    
    def search_tools(self, query: str) -> List[ToolInfo]:
        """جستجوی ابزارها بر اساس کلمات کلیدی"""
        query = query.lower()
        results = []
        
        for tool in self.tools_registry.values():
            # جستجو در نام، توضیحات و دسته‌بندی
            search_text = f"{tool.name} {tool.description} {tool.category}".lower()
            if query in search_text:
                results.append(tool)
        
        return results
    
    def generate_help_response(self, help_type: str = "general", query: str = "") -> str:
        """تولید پاسخ راهنما بر اساس نوع درخواست"""
        if help_type == "general":
            return self._generate_general_help()
        elif help_type == "tools_list":
            return self._generate_tools_list()
        elif help_type == "tool_detail":
            return self._generate_tool_detail(query)
        elif help_type == "search":
            return self._generate_search_results(query)
        else:
            return self._generate_general_help()
    
    def _generate_general_help(self) -> str:
        """تولید راهنمای عمومی"""
        help_text = """🤖 **راهنمای چت بات مالی**

من یک دستیار هوشمند مالی هستم که می‌توانم در زمینه‌های زیر به شما کمک کنم:

"""
        
        categorized_tools = self.get_tools_by_category()
        
        for category, description in self.categories.items():
            tools_count = len(categorized_tools.get(category, []))
            if tools_count > 0:
                help_text += f"📊 **{category}** ({tools_count} ابزار)\n"
                help_text += f"   {description}\n\n"
        
        help_text += """📝 **دستورات راهنما:**
- «ابزارها» یا «لیست ابزارها» - مشاهده تمام ابزارهای موجود
- «راهنمای [نام ابزار]» - اطلاعات کامل یک ابزار خاص  
- «چطور استفاده کنم؟» - آموزش استفاده از چت بات
- «نمونه سوال» - مثال‌های کاربردی
- «جستجوی [کلمه کلیدی]» - جستجو در ابزارها

💡 **نکته:** برای تحلیل مالی، کافیست سوال خود را به فارسی و به صورت طبیعی مطرح کنید."""

        return help_text
    
    def _generate_tools_list(self) -> str:
        """تولید لیست کامل ابزارها"""
        categorized_tools = self.get_tools_by_category()
        
        help_text = "🔧 **لیست کامل ابزارهای مالی**\n\n"
        
        for category, tools in categorized_tools.items():
            if tools:
                help_text += f"**{category}**\n"
                for tool in tools:
                    help_text += f"• {tool.name}: {tool.description}\n"
                help_text += "\n"
        
        help_text += "💡 برای دریافت اطلاعات کامل هر ابزار، از دستور «راهنمای [نام ابزار]» استفاده کنید."
        
        return help_text
    
    def _generate_tool_detail(self, tool_name: str) -> str:
        """تولید اطلاعات کامل یک ابزار خاص"""
        tool_info = self.get_tool_info(tool_name)
        
        if not tool_info:
            return f"❌ ابزار '{tool_name}' یافت نشد. برای مشاهده لیست ابزارها از دستور «ابزارها» استفاده کنید."
        
        help_text = f"🔍 **راهنمای ابزار: {tool_info.name}**\n\n"
        help_text += f"**توضیحات:** {tool_info.description}\n"
        help_text += f"**دسته‌بندی:** {tool_info.category}\n\n"
        
        if tool_info.parameters:
            help_text += "**پارامترهای ورودی:**\n"
            for param in tool_info.parameters:
                required = " (الزامی)" if param['required'] else " (اختیاری)"
                help_text += f"• {param['name']}{required}: {param['description']}\n"
            help_text += "\n"
        
        if tool_info.usage_examples:
            help_text += "**مثال‌های استفاده:**\n"
            for example in tool_info.usage_examples:
                help_text += f"• \"{example}\"\n"
        
        return help_text
    
    def _generate_search_results(self, query: str) -> str:
        """تولید نتایج جستجو"""
        results = self.search_tools(query)
        
        if not results:
            return f"❌ هیچ ابزاری با کلمه کلیدی '{query}' یافت نشد."
        
        help_text = f"🔎 **نتایج جستجو برای '{query}'**\n\n"
        
        for tool in results:
            help_text += f"**{tool.name}** ({tool.category})\n"
            help_text += f"{tool.description}\n\n"
        
        help_text += "💡 برای دریافت اطلاعات کامل هر ابزار، از دستور «راهنمای [نام ابزار]» استفاده کنید."
        
        return help_text
    
    def get_usage_tutorial(self) -> str:
        """دریافت آموزش استفاده از چت بات"""
        tutorial = """🎓 **آموزش استفاده از چت بات مالی**

📝 **چطور سوال بپرسم؟**
سوالات خود را به صورت طبیعی و به فارسی مطرح کنید، مثلاً:
- «نسبت جاری شرکت چقدر است؟»
- «جریان نقدی را تحلیل کن»
- «اسناد مشکوک را پیدا کن»

🔧 **ابزارهای موجود**
من می‌توانم کارهای زیر را انجام دهم:
- محاسبه نسبت‌های مالی (جاری، آنی، بدهی و ...)
- شبیه‌سازی جریان وجوه نقد  
- تشخیص تقلب و انحرافات مالی
- تولید گزارش‌های مالی جامع
- تحلیل عملکرد فصلی

💬 **دستورات ویژه**
- «ابزارها» - مشاهده تمام قابلیت‌ها
- «راهنما» - نمایش این راهنما
- «نمونه سوال» - مثال‌های کاربردی

🤖 **نکته:** نیازی به یادگیری دستورات خاص نیست، کافیست سوال مالی خود را به فارسی بپرسید!"""

        return tutorial


# نمونه سراسری برای استفاده در سراسر سیستم
help_system = FinancialHelpSystem()
