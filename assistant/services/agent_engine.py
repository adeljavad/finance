import json
import logging
import re
from typing import Dict, Any, List, Optional
from langchain_core.tools import BaseTool

from .deepseek_api import DeepSeekLLM
from .rag_engine import StableRAGEngine
from .memory_manager import MemoryManager
from .data_manager import UserDataManager

logger = logging.getLogger(__name__)

# تلاش برای import کردن optional tools
try:
    from .tools.search_tools import DocumentSearchTool, AdvancedFilterTool
    SEARCH_TOOLS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Search tools not available: {e}")
    SEARCH_TOOLS_AVAILABLE = False

try:
    from .tools.calculation_tools import DataCalculatorTool
    CALCULATION_TOOLS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Calculation tools not available: {e}")
    CALCULATION_TOOLS_AVAILABLE = False

try:
    from .tools.analytical_tools import PatternAnalysisTool
    ANALYTICAL_TOOLS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Analytical tools not available: {e}")
    ANALYTICAL_TOOLS_AVAILABLE = False

# تلاش برای import کردن optional dynamic tool manager
try:
    from .dynamic_tool_manager import DynamicToolManager
    DYNAMIC_TOOLS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Dynamic tools manager not available: {e}")
    DYNAMIC_TOOLS_AVAILABLE = False

class AgentEngine:
    """
    موتور هوشمند برای تحلیل مالی - نسخه بهبود یافته با مدیریت خطا
    """
    
    def __init__(self):
        """مقداردهی اولیه موتور با مدیریت خطا"""
        try:
            # LLM
            self.llm = DeepSeekLLM()
            logger.info("✅ DeepSeekLLM initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM: {e}")
            self.llm = None

        try:
            # RAG Engine
            self.rag = StableRAGEngine()
            logger.info("✅ RAG Engine initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG Engine: {e}")
            self.rag = None

        try:
            # Memory Manager
            self.memory = MemoryManager()
            logger.info("✅ Memory Manager initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Memory Manager: {e}")
            self.memory = None

        try:
            # Data Manager
            self.data_manager = UserDataManager()
            logger.info("✅ UserDataManager initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Data Manager: {e}")
            self.data_manager = None

        # Dynamic Tools Manager (optional)
        self.dynamic_manager = None
        if DYNAMIC_TOOLS_AVAILABLE and self.data_manager and self.llm:
            try:
                self.dynamic_manager = DynamicToolManager(self.data_manager, self.llm)
                logger.info("✅ Dynamic Tool Manager initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Dynamic Tool Manager: {e}")

        # Load static tools
        self.static_tools = self._load_static_tools()
        
        # Create combined tools list
        self.all_tools = []
        if self.static_tools:
            self.all_tools.extend(self.static_tools)
        if self.dynamic_manager:
            try:
                dynamic_tools = self.dynamic_manager.get_all_tools()
                if dynamic_tools:
                    self.all_tools.extend(dynamic_tools)
                    logger.info(f"✅ Added {len(dynamic_tools)} dynamic tools")
            except Exception as e:
                logger.error(f"❌ Failed to load dynamic tools: {e}")

        logger.info(f"🚀 AgentEngine initialized with {len(self.static_tools)} static tools")

    def _load_static_tools(self) -> List[BaseTool]:
        """بارگذاری ابزارهای استاتیک با مدیریت خطا"""
        tools = []
        
        if SEARCH_TOOLS_AVAILABLE and self.data_manager:
            try:
                tools.append(DocumentSearchTool(self.data_manager))
                tools.append(AdvancedFilterTool(self.data_manager))
                logger.info("✅ Search tools loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load search tools: {e}")
        
        if CALCULATION_TOOLS_AVAILABLE and self.data_manager:
            try:
                tools.append(DataCalculatorTool(self.data_manager))
                logger.info("✅ Calculation tools loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load calculation tools: {e}")
        
        if ANALYTICAL_TOOLS_AVAILABLE and self.data_manager:
            try:
                tools.append(PatternAnalysisTool(self.data_manager))
                logger.info("✅ Analytical tools loaded")
            except Exception as e:
                logger.error(f"❌ Failed to load analytical tools: {e}")

        logger.info(f"📦 Loaded {len(tools)} static tools")
        return tools

    def _normalize_user_id(self, session_id: str, user_id: str = None) -> str:
        """تولید user_id استاندارد با مدیریت session"""
        if user_id and user_id != "default":
            return str(user_id)
        elif session_id:
            # از session_id به عنوان user_id استفاده می‌کنیم
            return session_id
        else:
            return "anonymous"

    def _check_user_data_exists(self, session_id: str, user_id: str = None) -> bool:
        """بررسی وجود داده کاربر با مدیریت خطا"""
        try:
            if not self.data_manager:
                logger.warning("⚠️ Data manager not available")
                return False
                
            normalized_user_id = self._normalize_user_id(session_id, user_id)
            logger.debug(f"🔍 Checking data for user: {normalized_user_id}")
            
            # استفاده از debug_user_data برای اطلاعات کامل
            debug_info = self.data_manager.debug_user_data(normalized_user_id)
            
            has_data = debug_info.get('has_data', False)
            session_exists = debug_info.get('session_exists', False)
            
            logger.info(f"📊 Data check result for {normalized_user_id}: has_data={has_data}, session_exists={session_exists}")
            
            if has_data:
                logger.info(f"✅ User data exists for {normalized_user_id}")
                logger.info(f"DataFrames: {list(debug_info.get('dataframes', {}).keys())}")
                return True
            else:
                logger.info(f"⚠️ No user data found for {normalized_user_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error checking user data: {e}")
            return False

    def _classify_query(self, query: str, session_id: str, user_id: str = None) -> str:
        """طبقه‌بندی سوالات با منطق بهبود یافته"""
        try:
            normalized_user_id = self._normalize_user_id(session_id, user_id)
            query_lower = query.lower().strip()
            
            # 1. بررسی وجود داده کاربر
            has_user_data = self._check_user_data_exists(session_id, user_id)
            
            if has_user_data:
                # اگر داده وجود دارد، سوالات مربوط به داده
                if self._is_data_related_query(query_lower):
                    logger.info(f"📊 Classified as 'data_analysis' - User has data: {normalized_user_id}")
                    return 'data_analysis'
                elif self._is_follow_up(query, session_id):
                    logger.info(f"🔄 Classified as 'follow_up' - Context exists: {normalized_user_id}")
                    return 'follow_up'
                else:
                    logger.info(f"💼 Classified as 'general_finance' - User has data: {normalized_user_id}")
                    return 'general_finance'
            else:
                # اگر داده وجود ندارد
                if self._is_data_related_query(query_lower):
                    logger.info(f"📂 Classified as 'no_data' - Requesting data upload")
                    return 'no_data'
                elif self._is_follow_up(query, session_id):
                    logger.info(f"🔄 Classified as 'follow_up' - Context exists but no data: {normalized_user_id}")
                    return 'follow_up'
                elif self._is_financial_query(query_lower):
                    logger.info(f"💼 Classified as 'general_finance' - No data but financial query")
                    return 'general_finance'
                else:
                    logger.info(f"💬 Classified as 'general' - Non-financial query")
                    return 'general'
                    
        except Exception as e:
            logger.error(f"❌ Error in query classification: {e}")
            return 'general'

    def _is_data_related_query(self, query: str) -> bool:
        """تشخیص سوالات مربوط به داده"""
        data_keywords = [
            'سند', 'سند حسابداری', 'عملیات حسابداری', 'روزانه', 'کل', 'معین',
            'تراز', 'تراز آزمایشی', 'دفتر روزانه', 'دفتر کل', 'دفتر معین',
            'جمع', 'مجموع', 'مانده', 'بدهکار', 'بستانکار', 'تعداد',
            'آمار', 'تحلیل', 'گزارش', 'نمودار', 'روند', 'میانگین',
            'حداکثر', 'حداقل', 'انحراف', 'ضریب', 'نسبت',
            'document', 'record', 'transaction', 'ledger', 'trial balance'
        ]
        
        return any(keyword in query for keyword in data_keywords)

    def _is_financial_query(self, query: str) -> bool:
        """تشخیص سوالات عمومی مالی"""
        financial_keywords = [
            'مالیات', 'بودجه', 'سود', 'زیان', 'سرمایه', 'دارایی', 'بدهی',
            'استاندارد', 'حسابداری', 'حسابرسی', 'کنترل', 'ریسک', 'ریسک مالی',
            'انطباق', 'گزارش', 'بازرسی', 'قوانین', 'مقررات',
            'tax', 'budget', 'profit', 'loss', 'capital', 'assets', 'liability'
        ]
        
        return any(keyword in query for keyword in financial_keywords)

    def _is_follow_up(self, query: str, session_id: str) -> bool:
        """تشخیص follow-up questions با مدیریت خطا"""
        follow_up_keywords = [
            'همچنین', 'علاوه بر این', 'در ادامه', 'حالا', 'حالا که', 'بیشتر',
            'جزئیات', 'شرح', 'توضیح', 'چه طور', 'چگونه', 'میتونی', 'می‌تونی',
            'also', 'furthermore', 'more', 'details', 'how', 'what', 'why'
        ]
        
        # بررسی وجود تاریخچه مکالمه
        try:
            if self.memory:
                history = self.memory.get_conversation_history(session_id, last_n=5)
                has_context = len(history) > 0
            else:
                has_context = False
                
            query_has_follow_keywords = any(keyword in query.lower() for keyword in follow_up_keywords)
            
            if has_context and query_has_follow_keywords:
                logger.info(f"🔄 Follow-up detected - has_context: {has_context}, query: '{query}'")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"❌ Error checking follow-up: {e}")
            return False

    def run(self, user_message: str, session_id: str, user_id: str = None) -> Dict[str, Any]:
        """اجرای اصلی موتور با مدیریت خطا"""
        try:
            logger.info(f"🚀 Starting query processing - Session: {session_id}, User: {user_id}")
            logger.info(f"💬 User message: {user_message[:100]}...")
            
            # Normalize user_id
            normalized_user_id = self._normalize_user_id(session_id, user_id)
            logger.info(f"🆔 Normalized user ID: {normalized_user_id}")
            
            # Add user message to memory
            if self.memory:
                try:
                    self.memory.add_message(session_id, 'user', user_message)
                    logger.info(f"💾 User message added to memory")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to add message to memory: {e}")

            # Classify query
            query_type = self._classify_query(user_message, session_id, user_id)
            logger.info(f"🏷️ Query classified as: {query_type}")

            # Process based on classification
            if query_type == 'data_analysis':
                response = self._handle_data_analysis_query(user_message, session_id, user_id)
            elif query_type == 'no_data':
                response = self._handle_no_data_query(user_message, session_id, user_id)
            elif query_type == 'follow_up':
                response = self._handle_follow_up(user_message, session_id, user_id)
            elif query_type == 'general_finance':
                response = self._handle_general_finance_query(user_message, session_id, user_id)
            else:
                response = self._handle_general_query(user_message, session_id, user_id)

            # Add assistant response to memory
            if self.memory and response:
                try:
                    self.memory.add_message(session_id, 'assistant', response)
                    logger.info(f"💾 Assistant response added to memory")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to add assistant response to memory: {e}")

            # Add context summary
            try:
                if self.memory:
                    context_summary = self.memory.get_context_summary(session_id)
                    logger.info(f"📝 Context summary: {context_summary[:100]}...")
            except Exception as e:
                logger.warning(f"⚠️ Failed to get context summary: {e}")

            result = {
                'success': True,
                'response': response,
                'query_type': query_type,
                'session_id': session_id,
                'user_id': normalized_user_id,
                'tools_used': response.get('tools_used', []) if isinstance(response, dict) else [],
                'has_data': self._check_user_data_exists(session_id, user_id) if response else False
            }
            
            logger.info(f"✅ Query processing completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in agent run: {e}")
            return {
                'success': False,
                'response': f'متأسفانه خطایی در پردازش درخواست شما رخ داد: {str(e)}',
                'query_type': 'error',
                'session_id': session_id,
                'user_id': self._normalize_user_id(session_id, user_id),
                'error': str(e)
            }

    def _handle_data_analysis_query(self, query: str, session_id: str, user_id: str = None) -> str:
        """پردازش سوالات تحلیل داده"""
        try:
            normalized_user_id = self._normalize_user_id(session_id, user_id)
            logger.info(f"🔍 Handling data analysis query for user: {normalized_user_id}")
            
            # بررسی وجود داده
            if not self._check_user_data_exists(session_id, user_id):
                logger.warning(f"⚠️ No user data found for data analysis")
                return "⚠️ متأسفانه هیچ داده‌ای برای تحلیل پیدا نشد. لطفاً ابتدا فایل اکسل اسناد حسابداری خود را آپلود کنید."
            
            # پیدا کردن ابزار مناسب
            tool = self._find_static_tool(query)
            tools_used = []
            
            if tool:
                try:
                    # آماده‌سازی پارامترها
                    params = self._extract_parameters_from_query(query, normalized_user_id)
                    logger.info(f"🔧 Found tool: {tool.name}, params: {params}")
                    
                    # اجرای ابزار
                    tool_result = tool._run(json.dumps(params))
                    tools_used.append(tool.name)
                    
                    # تقویت نتیجه با LLM
                    enhanced_result = self._enhance_with_llm(tool_result, query)
                    return enhanced_result
                    
                except Exception as e:
                    logger.error(f"❌ Tool execution error: {e}")
                    # ادامه با سایر روش‌ها
            else:
                logger.info(f"🔍 No static tool found, trying dynamic tools")
                
                # تلاش برای یافتن ابزار داینامیک
                if self.dynamic_manager:
                    try:
                        dynamic_tool = self.dynamic_manager.find_or_create_tool(query, normalized_user_id)
                        if dynamic_tool:
                            params = self._extract_parameters_from_query(query, normalized_user_id)
                            tool_result = dynamic_tool._run(json.dumps(params))
                            tools_used.append(dynamic_tool.name)
                            
                            enhanced_result = self._enhance_with_llm(tool_result, query)
                            return enhanced_result
                    except Exception as e:
                        logger.error(f"❌ Dynamic tool error: {e}")
            
            # اگر هیچ ابزاری پیدا نشد، مستقیماً از LLM استفاده کن
            logger.info(f"💬 No tools found, using direct LLM")
            return self._ask_llm_directly(query, normalized_user_id)
            
        except Exception as e:
            logger.error(f"❌ Error in data analysis: {e}")
            return f"خطا در تحلیل داده: {str(e)}"

    def _handle_no_data_query(self, query: str, session_id: str, user_id: str = None) -> str:
        """پردازش سوالات بدون داده"""
        try:
            if self._is_data_related_query(query.lower()):
                response = """
📂 **برای تحلیل داده‌های حسابداری شما، ابتدا لطفاً فایل اکسل اسناد را آپلود کنید.**

**فایل شما باید شامل ستون‌های زیر باشد:**
- شماره سند
- تاریخ سند  
- بدهکار
- بستانکار
- توضیحات

**پس از آپلود، می‌توانید سوالاتی مانند:**
- "تراز آزمایشی را نشان بده"
- "مجموع بدهکارها را حساب کن"
- "اسناد بالای ۱۰ میلیون را پیدا کن"
- "روند ماهانه فروش را تحلیل کن"

💡 **برای آپلود، روی دکمه "آپلود فایل" کلیک کنید.**
"""
            else:
                response = self._ask_llm_directly(query, self._normalize_user_id(session_id, user_id))
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in no-data handling: {e}")
            return f"خطا در پردازش درخواست: {str(e)}"

    def _handle_follow_up(self, query: str, session_id: str, user_id: str = None) -> str:
        """پردازش follow-up questions"""
        try:
            normalized_user_id = self._normalize_user_id(session_id, user_id)
            
            # دریافت تاریخچه مکالمه
            if self.memory:
                history = self.memory.get_conversation_history(session_id, last_n=5)
                
                # ساخت prompt با context
                context_messages = []
                for msg in history[-3:]:  # فقط ۳ پیام آخر
                    role = "کاربر" if msg['role'] == 'user' else "دستیار"
                    context_messages.append(f"{role}: {msg['content']}")
                
                context_text = "\n".join(context_messages)
                
                prompt = f"""
**مکالمه قبلی:**
{context_text}

**سوال جدید کاربر:** {query}

لطفاً با در نظر گرفتن مکالمه قبلی، به سوال جدید پاسخ دهید.
"""
            else:
                prompt = query
            
            return self._ask_llm_directly(prompt, normalized_user_id)
            
        except Exception as e:
            logger.error(f"❌ Error in follow-up handling: {e}")
            return f"خطا در پردازش پیگیری: {str(e)}"

    def _handle_general_finance_query(self, query: str, session_id: str, user_id: str = None) -> str:
        """پردازش سوالات عمومی مالی"""
        try:
            normalized_user_id = self._normalize_user_id(session_id, user_id)
            return self._ask_llm_directly(query, normalized_user_id)
        except Exception as e:
            logger.error(f"❌ Error in general finance handling: {e}")
            return f"خطا در پردازش سوال مالی: {str(e)}"

    def _handle_general_query(self, query: str, session_id: str, user_id: str = None) -> str:
        """پردازش سوالات عمومی"""
        try:
            normalized_user_id = self._normalize_user_id(session_id, user_id)
            return self._ask_llm_directly(query, normalized_user_id)
        except Exception as e:
            logger.error(f"❌ Error in general handling: {e}")
            return f"خطا در پردازش سوال: {str(e)}"

    def _find_static_tool(self, query: str) -> Optional[BaseTool]:
        """پیدا کردن ابزار استاتیک مناسب"""
        if not self.static_tools:
            return None
            
        query_lower = query.lower()
        
        # جستجو بر اساس کلیدواژه‌ها
        for tool in self.static_tools:
            tool_name = tool.name.lower()
            
            if 'search' in tool_name and any(keyword in query_lower for keyword in ['جستجو', 'پیدا', 'سند', 'document']):
                return tool
            elif 'calculator' in tool_name and any(keyword in query_lower for keyword in ['جمع', 'مجموع', 'محاسبه', 'آمار', 'sum', 'calculate']):
                return tool
            elif 'analysis' in tool_name and any(keyword in query_lower for keyword in ['تحلیل', 'روند', 'pattern', 'analysis']):
                return tool
            elif 'filter' in tool_name and any(keyword in query_lower for keyword in ['فیلتر', 'جدا', 'filter']):
                return tool
        
        # اگر ابزار خاص پیدا نشد، اولین ابزار مناسب را برگردان
        return self.static_tools[0] if self.static_tools else None

    def _extract_parameters_from_query(self, query: str, user_id: str) -> Dict[str, Any]:
        """استخراج پارامترها از سوال"""
        params = {"user_id": user_id}
        query_lower = query.lower()
        
        # استخراج تاریخ
        date_patterns = [
            r'از\s+(\d{4}/\d{1,2}/\d{1,2})\s+تا\s+(\d{4}/\d{1,2}/\d{1,2})',  # from date1 to date2
            r'(\d{4}/\d{1,2}/\d{1,2})',  # single date
            r'امسال', r'امروز', r'دیروز', r'امسال'  # relative dates
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, query_lower)
            if match:
                if 'from' in pattern:
                    params['date_range'] = {
                        'start': match.group(1),
                        'end': match.group(2)
                    }
                else:
                    params['date'] = match.group(1)
                break
        
        # استخراج مبالغ
        amount_patterns = [
            r'بالای\s+(\d+(?:\.\d+)?)',  # above amount
            r'زیر\s+(\d+(?:\.\d+)?)',    # below amount
            r'(\d+(?:\.\d+)?)\s+تومان'   # amount
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, query_lower)
            if match:
                amount = float(match.group(1))
                if 'بالای' in query_lower:
                    params['min_amount'] = amount
                elif 'زیر' in query_lower:
                    params['max_amount'] = amount
                else:
                    params['amount'] = amount
                break
        
        # تشخیص نوع محاسبه
        if any(keyword in query_lower for keyword in ['تراز', 'trial balance', 'آزمایشی']):
            params['calculation_type'] = 'trial_balance'
        elif any(keyword in query_lower for keyword in ['آمار', 'statistics', 'پایه']):
            params['calculation_type'] = 'basic_stats'
        elif any(keyword in query_lower for keyword in ['نسبت', 'ratio', 'مالی']):
            params['calculation_type'] = 'financial_ratios'
        elif any(keyword in query_lower for keyword in ['روند', 'trend', 'تحلیل']):
            params['calculation_type'] = 'trend_analysis'
        else:
            params['calculation_type'] = 'basic_stats'
        
        logger.info(f"🔧 Extracted parameters: {params}")
        return params

    def _enhance_with_llm(self, tool_result: str, original_query: str) -> str:
        """تقویت نتیجه ابزار با LLM"""
        try:
            if not self.llm:
                return tool_result
                
            prompt = f"""
**نتیجه ابزار:**
{tool_result}

**سوال اصلی کاربر:**
{original_query}

لطفاً نتیجه بالا را به زبان فارسی و به صورت کاربرپسند توضیح دهید. تحلیل باید شامل:
1. خلاصه نتایج
2. نکات مهم و قابل توجه
3. توصیه‌های عملی (در صورت نیاز)
4. استفاده از اصطلاحات حرفه‌ای حسابداری

**مهم:** فقط روی داده‌های ارائه شده تمرکز کنید و از اطلاعات خارج از نتیجه ابزار استفاده نکنید.
"""
            
            enhanced_result = self.llm.generate(prompt)
            return enhanced_result
            
        except Exception as e:
            logger.error(f"❌ Error enhancing with LLM: {e}")
            return tool_result

    def _ask_llm_directly(self, query: str, user_id: str = None) -> str:
        """پرسش مستقیم از LLM"""
        try:
            if not self.llm:
                return "متأسفانه سرویس AI در حال حاضر در دسترس نیست."
            
            system_prompt = """
شما یک دستیار حسابدار هوشمند هستید که تخصص در موارد زیر دارد:
- حسابداری و حسابرسی
- قوانین مالیاتی
- تحلیل مالی و گزارش‌گیری
- استانداردهای حسابداری

**قوانین مهم:**
1. همیشه به زبان فارسی پاسخ دهید
2. از اصطلاحات حرفه‌ای حسابداری استفاده کنید
3. اگر سوال خارج از تخصص شماست، صادقانه بگویید
4. در صورت امکان، مثال‌های عملی ارائه دهید
5. پاسخ‌های کوتاه و مفید بدهید

**برای تحلیل داده‌های حسابداری:** 
اگر کاربر داده‌ای آپلود کرده باشد، از آن استفاده کنید، در غیر این صورت بگویید که ابتدا فایل اکسل آپلود شود.
"""
            
            user_prompt = f"سوال کاربر: {query}"
            
            response = self.llm.generate(user_prompt, system_prompt)
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in direct LLM query: {e}")
            return f"متأسفانه خطایی در پردازش سوال شما رخ داد: {str(e)}"

    def get_available_tools(self) -> Dict[str, Any]:
        """دریافت لیست ابزارهای موجود"""
        try:
            static_tools = [tool.name for tool in self.static_tools] if self.static_tools else []
            dynamic_count = 0
            
            if self.dynamic_manager:
                try:
                    dynamic_count = len(self.dynamic_manager.get_all_tools())
                except:
                    dynamic_count = 0
            
            return {
                'static_tools': static_tools,
                'dynamic_tools_count': dynamic_count,
                'total_tools': len(static_tools) + dynamic_count,
                'rag_available': self.rag is not None,
                'memory_available': self.memory is not None,
                'data_manager_available': self.data_manager is not None
            }
        except Exception as e:
            logger.error(f"❌ Error getting available tools: {e}")
            return {'error': str(e)}

    def get_system_status(self) -> Dict[str, Any]:
        """دریافت وضعیت سیستم"""
        try:
            status = {
                'agent_active': True,
                'components': {},
                'static_tools_count': len(self.static_tools),
                'dynamic_tools_active': self.dynamic_manager is not None,
                'rag_status': 'active' if self.rag else 'inactive',
                'memory_status': 'active' if self.memory else 'inactive',
                'data_manager_status': 'active' if self.data_manager else 'inactive',
                'llm_status': 'active' if self.llm else 'inactive'
            }
            
            # جزئیات components
            if self.rag:
                try:
                    rag_info = self.rag.get_collection_info()
                    status['components']['rag'] = rag_info
                except:
                    status['components']['rag'] = {'status': 'error'}
            
            if self.memory:
                try:
                    # Memory statistics (if available)
                    status['components']['memory'] = {
                        'status': 'active',
                        'sessions_managed': 'unknown'
                    }
                except:
                    status['components']['memory'] = {'status': 'error'}
            
            if self.data_manager:
                try:
                    # Data manager statistics (if available)
                    status['components']['data_manager'] = {
                        'status': 'active',
                        'storage_type': 'redis_with_fallback' if hasattr(self.data_manager, 'redis_client') else 'file_only'
                    }
                except:
                    status['components']['data_manager'] = {'status': 'error'}
            
            if self.llm:
                status['components']['llm'] = {'status': 'active', 'type': 'DeepSeek'}
            
            # Dynamic tools info
            if self.dynamic_manager:
                try:
                    dynamic_stats = self.dynamic_manager.get_tool_statistics()
                    status['dynamic_tools_stats'] = dynamic_stats
                except:
                    status['dynamic_tools_stats'] = {'error': 'Failed to get stats'}
            
            return status
            
        except Exception as e:
            logger.error(f"❌ Error getting system status: {e}")
            return {'error': str(e), 'agent_active': False}

    def clear_memory(self, session_id: str) -> bool:
        """پاک کردن حافظه session"""
        try:
            if self.memory:
                self.memory.clear_session(session_id)
                logger.info(f"🗑️ Memory cleared for session: {session_id}")
                return True
            else:
                logger.warning("⚠️ Memory manager not available")
                return False
        except Exception as e:
            logger.error(f"❌ Error clearing memory: {e}")
            return False

    def debug_user_data(self, user_id: str) -> Dict[str, Any]:
        """دیباگ اطلاعات کاربر"""
        try:
            if not self.data_manager:
                return {'error': 'Data manager not available'}
            
            debug_info = self.data_manager.debug_user_data(user_id)
            debug_info['agent_status'] = self.get_system_status()
            
            logger.info(f"🔍 Debug completed for user {user_id}")
            return debug_info
            
        except Exception as e:
            logger.error(f"❌ Error in user data debug: {e}")
            return {'error': str(e)}
