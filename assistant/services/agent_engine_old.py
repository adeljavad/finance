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


# -------------------------
# 🎯 تعریف ابزارهای مالی جدید مبتنی بر داده‌های کاربر
# -------------------------

class AccountingBalanceTool(BaseTool):
    name: str = "accounting_balance"
    description: str = "محاسبه تراز و مانده حساب‌ها بر اساس داده‌های حسابداری کاربر"
    
    def __init__(self, data_manager: UserDataManager):
        super().__init__()
        self.data_manager = data_manager
    
    def _run(self, user_input: str) -> str:
        """محاسبه تراز بر اساس داده‌های کاربر"""
        try:
            # استخراج user_id از ورودی
            data = json.loads(user_input) if isinstance(user_input, str) else user_input
            user_id = data.get("user_id", "default")
            
            # دریافت داده‌های کاربر
            df = self.data_manager.get_dataframe(user_id, 'accounting_data')
            
            if df is None or df.empty:
                return "⚠️ هیچ داده حسابداری برای تحلیل موجود نیست."
            
            # محاسبات اصلی
            total_debit = df['بدهکار'].sum()
            total_credit = df['بستانکار'].sum()
            balance = total_debit - total_credit
            
            # تحلیل تاریخ‌ها
            date_info = ""
            if 'تاریخ سند' in df.columns:
                dates = df['تاریخ سند'].dropna()
                if not dates.empty:
                    date_info = f"📅 محدوده تاریخ: از {dates.min()} تا {dates.max()}\n"
            
            analysis = f"""
📊 تحلیل تراز کلی بر اساس داده‌های شما:

{date_info}
• جمع بدهکار: {total_debit:,.0f} ریال
• جمع بستانکار: {total_credit:,.0f} ریال  
• مانده تراز: {balance:,.0f} ریال
• تعداد اسناد: {len(df):,} سند

💡 وضعیت: """
            
            if abs(balance) < 1000:  # tolerance برای خطاهای گرد کردن
                analysis += "✅ ترازنامه متعادل است"
            elif balance > 0:
                analysis += f"📈 مازاد بدهکار به میزان {balance:,.0f} ریال"
            else:
                analysis += f"📉 مازاد بستانکار به میزان {abs(balance):,.0f} ریال"
                
            return analysis
            
        except Exception as e:
            return f"خطا در تحلیل تراز: {str(e)}"


class FinancialRatiosTool(BaseTool):
    name: str = "financial_ratios"
    description: str = "محاسبه نسبت‌های مالی از داده‌های حسابداری کاربر"
    
    def __init__(self, data_manager: UserDataManager):
        super().__init__()
        self.data_manager = data_manager
    
    def _run(self, user_input: str) -> str:
        """محاسبه نسبت‌های مالی"""
        try:
            data = json.loads(user_input) if isinstance(user_input, str) else user_input
            user_id = data.get("user_id", "default")
            
            df = self.data_manager.get_dataframe(user_id, 'accounting_data')
            if df is None or df.empty:
                return "⚠️ هیچ داده حسابداری برای تحلیل موجود نیست."
            
            # محاسبه نسبت‌های مختلف
            total_debit = df['بدهکار'].sum()
            total_credit = df['بستانکار'].sum()
            total_turnover = total_debit + total_credit
            
            # نسبت‌های مبتنی بر ساختار حساب‌ها
            ratios = self._calculate_account_based_ratios(df)
            
            analysis = f"""
💧 تحلیل نسبت‌های مالی:

💰 حجم معاملات:
• گردش کل: {total_turnover:,.0f} ریال
• میانگین روزانه: {total_turnover/30:,.0f} ریال

📊 نسبت‌های ساختاری:
{ratios}

🎯 نکات کلیدی: """
            
            if total_turnover > 1000000000:  # 1 میلیارد
                analysis += "حجم معاملات قابل توجه ✅"
            else:
                analysis += "حجم معاملات متوسط ⚡"
                
            return analysis
            
        except Exception as e:
            return f"خطا در محاسبه نسبت‌ها: {str(e)}"
    
    def _calculate_account_based_ratios(self, df: pd.DataFrame) -> str:
        """محاسبه نسبت‌های مبتنی بر ساختار حساب‌ها"""
        ratios_text = ""
        
        try:
            # اگر ستون معین وجود دارد
            if 'معین' in df.columns:
                # گروه‌بندی بر اساس معین
                by_subsidiary = df.groupby('معین').agg({
                    'بدهکار': 'sum',
                    'بستانکار': 'sum'
                }).reset_index()
                
                ratios_text += "• تحلیل بر اساس معین:\n"
                for _, row in by_subsidiary.head(5).iterrows():  # فقط ۵ معین اول
                    ratios_text += f"  - معین {row['معین']}: بدهکار {row['بدهکار']:,.0f} | بستانکار {row['بستانکار']:,.0f}\n"
            
            # تحلیل تمرکز
            top_debit = df.nlargest(5, 'بدهکار')[['بدهکار', 'توضیحات']].sum() if 'توضیحات' in df.columns else df.nlargest(5, 'بدهکار')['بدهکار'].sum()
            top_credit = df.nlargest(5, 'بستانکار')[['بستانکار', 'توضیحات']].sum() if 'توضیحات' in df.columns else df.nlargest(5, 'بستانکار')['بستانکار'].sum()
            
            debit_concentration = top_debit / df['بدهکار'].sum() * 100
            credit_concentration = top_credit / df['بستانکار'].sum() * 100
            
            ratios_text += f"\n• تمرکز معاملات:\n"
            ratios_text += f"  - ۵ سند برتر بدهکار: {debit_concentration:.1f}% از کل\n"
            ratios_text += f"  - ۵ سند برتر بستانکار: {credit_concentration:.1f}% از کل\n"
            
        except Exception as e:
            ratios_text = f"• امکان محاسبه نسبت‌های پیشرفته وجود ندارد: {str(e)}"
        
        return ratios_text


class TransactionAnalysisTool(BaseTool):
    name: str = "transaction_analysis"
    description: str = "تحلیل پیشرفته تراکنش‌ها و الگوهای مالی"
    
    def __init__(self, data_manager: UserDataManager):
        super().__init__()
        self.data_manager = data_manager
    
    def _run(self, user_input: str) -> str:
        """تحلیل پیشرفته تراکنش‌ها"""
        try:
            data = json.loads(user_input) if isinstance(user_input, str) else user_input
            user_id = data.get("user_id", "default")
            
            df = self.data_manager.get_dataframe(user_id, 'accounting_data')
            if df is None or df.empty:
                return "⚠️ هیچ داده حسابداری برای تحلیل موجود نیست."
            
            analysis = self._analyze_transaction_patterns(df)
            return analysis
            
        except Exception as e:
            return f"خطا در تحلیل تراکنش‌ها: {str(e)}"
    
    def _analyze_transaction_patterns(self, df: pd.DataFrame) -> str:
        """تحلیل الگوهای تراکنش"""
        analysis = "🔍 تحلیل الگوهای تراکنش:\n\n"
        
        # تحلیل توزیع مبالغ
        debit_stats = df['بدهکار'].describe()
        credit_stats = df['بستانکار'].describe()
        
        analysis += f"📈 آمار بدهکار:\n"
        analysis += f"  - میانگین: {debit_stats['mean']:,.0f} ریال\n"
        analysis += f"  - بیشترین: {debit_stats['max']:,.0f} ریال\n"
        analysis += f"  - کمترین: {debit_stats['min']:,.0f} ریال\n"
        
        analysis += f"\n📉 آمار بستانکار:\n"
        analysis += f"  - میانگین: {credit_stats['mean']:,.0f} ریال\n"
        analysis += f"  - بیشترین: {credit_stats['max']:,.0f} ریال\n"
        analysis += f"  - کمترین: {credit_stats['min']:,.0f} ریال\n"
        
        # تحلیل تاریخ‌ها اگر موجود باشد
        if 'تاریخ سند' in df.columns:
            try:
                # شمارش تراکنش‌ها بر اساس ماه
                df['ماه'] = df['تاریخ سند'].str[:7]  # YYYY/MM
                monthly = df.groupby('ماه').size()
                
                analysis += f"\n📅 توزیع ماهانه:\n"
                for month, count in monthly.head(6).items():  # ۶ ماه اول
                    analysis += f"  - {month}: {count} سند\n"
                    
            except Exception as e:
                analysis += f"\n⚠️ خطا در تحلیل زمانی: {str(e)}\n"
        
        return analysis


class AgentEngine:
    def __init__(self):
        self.llm = DeepSeekLLM()
        self.rag = StableRAGEngine()
        self.memory = MemoryManager()
        self.data_manager = UserDataManager()
        
        # import ابزارهای جدید
        from .tools.search_tools import DocumentSearchTool, AdvancedFilterTool
        from .tools.calculation_tools import DataCalculatorTool
        from .tools.analytical_tools import PatternAnalysisTool
        
        # تعریف تمام ابزارها
        self.tools = [
            # ابزارهای جستجو
            DocumentSearchTool(self.data_manager),
            AdvancedFilterTool(self.data_manager),
            
            # ابزارهای محاسباتی
            DataCalculatorTool(self.data_manager),
            
            # ابزارهای تحلیلی
            PatternAnalysisTool(self.data_manager),
        ]
        
        self.tool_map = {tool.name: tool for tool in self.tools}
    
    def run(self, query: str, session_id: str = "default", user_id: str = None) -> str:
        # تشخیص نوع ابزار مورد نیاز
        tool_to_use = self._select_appropriate_tool(query)
        
        if tool_to_use:
            # انجام محاسبات و آماده‌سازی داده‌ها
            tool_input = json.dumps({
                "user_id": user_id,
                "query": query,
                # پارامترهای خاص هر ابزار
            }, ensure_ascii=False)
            
            # اجرای ابزار برای محاسبات
            calculation_result = tool_to_use.run(tool_input)
            
            # ارسال به LLM برای تحلیل حرفه‌ای
            llm_analysis = self._get_llm_analysis(query, calculation_result)
            
            return llm_analysis
        else:
            return self._ask_llm_directly(query)
    
    def _select_appropriate_tool(self, query: str) -> BaseTool:
        """انتخاب ابزار مناسب بر اساس سوال"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['جستجو', 'پیدا کن', 'سند', 'تاریخ']):
            return self.tool_map['document_search']
        elif any(word in query_lower for word in ['فیلتر', 'شرط']):
            return self.tool_map['advanced_filter']
        elif any(word in query_lower for word in ['محاسبه', 'نسبت', 'آمار']):
            return self.tool_map['data_calculator']
        elif any(word in query_lower for word in ['الگو', 'روند', 'تحلیل']):
            return self.tool_map['pattern_analysis']
        
        return None
    
    def _get_llm_analysis(self, query: str, calculation_result: str) -> str:
        """دریافت تحلیل حرفه‌ای از LLM"""
        prompt = f"""
        شما یک تحلیل‌گر مالی بسیار حرفه‌ای هستید. بر اساس نتایج محاسبات زیر و سوال کاربر، یک تحلیل جامع و حرفه‌ای ارائه دهید.

        سوال کاربر: {query}

        نتایج محاسبات:
        {calculation_result}

        لطفاً تحلیل خود را به صورت حرفه‌ای و شامل موارد زیر ارائه دهید:
        1. تفسیر اعداد و شاخص‌ها
        2. شناسایی نقاط قوت و ضعف
        3️. ارائه راهکارهای عملی و قابل اجرا
        4️. استفاده از اصطلاحات تخصصی حسابداری
        5️. پیشنهادات برای بهبود

        تحلیل باید کاملاً حرفه‌ای، مبتنی بر داده و کاربردی باشد.
        """
        
        messages = [
            {
                "role": "system", 
                "content": "شما یک مشاور مالی ارشد با ۲۰ سال سابقه هستید. تحلیل‌های شما باید بسیار حرفه‌ای، مبتنی بر داده و قابل اجرا باشد."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        return self.llm.invoke(messages)
        

# -------------------------
# 🎯 کلاس Agent Engine - نسخه اصلاح شده
# -------------------------

class AgentEngine_old:
    """
    موتور ایجنت هوشمند با قابلیت تحلیل داده‌های واقعی کاربر
    """

    def __init__(self):
        self.llm = DeepSeekLLM()
        self.rag = StableRAGEngine()
        self.memory = MemoryManager()
        self.data_manager = UserDataManager()
        
        # تعریف ابزارهای جدید مبتنی بر داده‌های کاربر
        self.tools = [
            AccountingBalanceTool(self.data_manager),
            FinancialRatiosTool(self.data_manager),
            TransactionAnalysisTool(self.data_manager),
        ]
        
        self.tool_map = {tool.name: tool for tool in self.tools}
        logger.info("✅ AgentEngine با ابزارهای مبتنی بر داده‌های کاربر راه‌اندازی شد")

    def _classify_query(self, query: str, context: str = "") -> str:
        """طبقه‌بندی سوال - نسخه بهبود یافته"""
        query_lower = query.lower().strip()
        
        # 1. سوالات ادامه‌دار
        follow_up_patterns = [
            r'^(آره|بله|بلی|حتما|مایلم|می‌خواهم|بفرمایید|ادامه|بیشتر|توضیح|شرح)',
            r'^(yes|yeah|sure|ok|okay|please|more|explain)',
        ]
        
        if context and any(re.search(pattern, query_lower) for pattern in follow_up_patterns):
            return 'follow_up'
        
        # 2. سوالات مبتنی بر داده‌های کاربر
        if self._needs_accounting_data(query):
            return 'accounting'
        
        # 3. سوالات نیازمند ابزار
        tool_patterns = [
            r'\b(تراز|مانده|جمع کل)\b',
            r'\b(نسبت|تحلیل مالی|شاخص)\b',
            r'\b(الگو|رفتار|توزیع)\b.*\b(تراکنش|معامله)\b',
            r'\b(میانگین|بیشترین|کمترین)\b.*\b(مبلغ)\b'
        ]
        
        for pattern in tool_patterns:
            if re.search(pattern, query_lower):
                return 'tool'
        
        # 4. سوالات RAG
        rag_patterns = [
            r'\b(شرکت|سازمان|پروژه)\b.*\b(ما|خودمان)\b',
            r'\b(اسناد|مستندات)\b.*\b(ذخیره|آرشیو)\b'
        ]
        
        for pattern in rag_patterns:
            if re.search(pattern, query_lower):
                return 'rag'
        
        # 5. سوالات عمومی مالی
        financial_keywords = [
            'مالیات', 'حسابداری', 'حسابدار', 'مالی', 'بودجه', 'هزینه', 'درآمد',
            'سود', 'زیان', 'دارایی', 'بدهی', 'سرمایه', 'ترازنامه', 'صورت مالی'
        ]
        
        if any(keyword in query_lower for keyword in financial_keywords):
            return 'general'
        
        return 'general'

    def _needs_accounting_data(self, query: str) -> bool:
        """تشخیص نیاز به داده‌های حسابداری"""
        accounting_keywords = [
            'تراز', 'ترازنامه', 'صورت مالی', 'سود', 'زیان', 'درآمد', 'هزینه',
            'نسبت جاری', 'نسبت آنی', 'نقدینگی', 'دارایی', 'بدهی', 'سرمایه',
            'گردش', 'مانده', 'جمع کل', 'مبلغ', 'ریال', 'اسناد', 'معین', 'تفصیلی'
        ]
        return any(keyword in query for keyword in accounting_keywords)

    def _process_accounting_query(self, query: str, user_id: str) -> Optional[str]:
        """پردازش سوالات حسابداری با داده‌های واقعی"""
        try:
            df = self.data_manager.get_dataframe(user_id, 'accounting_data')
            
            if df is None or df.empty:
                return "⚠️ هیچ داده حسابداری برای تحلیل موجود نیست. لطفاً ابتدا فایل اسناد خود را آپلود کنید."
            
            # تحلیل‌های پیشرفته‌تر بر اساس سوال کاربر
            if any(word in query for word in ['تراز', 'مانده', 'جمع']):
                return self._calculate_comprehensive_balance(df, query)
            elif any(word in query for word in ['نسبت', 'شاخص']):
                return self._calculate_advanced_ratios(df, query)
            elif any(word in query for word in ['الگو', 'توزیع', 'میانگین']):
                return self._analyze_patterns(df, query)
            else:
                return self._general_accounting_analysis(df, query)
                
        except Exception as e:
            logger.error(f"Error processing accounting query: {e}")
            return None

    def _calculate_comprehensive_balance(self, df: pd.DataFrame, query: str) -> str:
        """محاسبه تراز جامع"""
        total_debit = df['بدهکار'].sum()
        total_credit = df['بستانکار'].sum()
        balance = total_debit - total_credit
        
        # اطلاعات پیشرفته
        max_debit = df['بدهکار'].max()
        max_credit = df['بستانکار'].max()
        avg_debit = df['بدهکار'].mean()
        avg_credit = df['بستانکار'].mean()
        
        analysis = f"""
📊 تحلیل جامع تراز:

• جمع بدهکار: {total_debit:,.0f} ریال
• جمع بستانکار: {total_credit:,.0f} ریال
• مانده تراز: {balance:,.0f} ریال

📈 آمار پیشرفته:
• بیشترین بدهکار: {max_debit:,.0f} ریال
• بیشترین بستانکار: {max_credit:,.0f} ریال
• میانگین بدهکار: {avg_debit:,.0f} ریال
• میانگین بستانکار: {avg_credit:,.0f} ریال

💡 تحلیل: """
        
        if abs(balance) < total_debit * 0.01:  # 1% tolerance
            analysis += "ترازنامه کاملاً متعادل ✅"
        else:
            analysis += f"نیاز به بررسی اختلاف {abs(balance):,.0f} ریال ⚠️"
            
        return analysis

    def _calculate_advanced_ratios(self, df: pd.DataFrame, query: str) -> str:
        """محاسبه نسبت‌های پیشرفته"""
        total_debit = df['بدهکار'].sum()
        total_credit = df['بستانکار'].sum()
        total_turnover = total_debit + total_credit
        
        # نسبت‌های مختلف
        debit_ratio = (total_debit / total_turnover) * 100 if total_turnover > 0 else 0
        credit_ratio = (total_credit / total_turnover) * 100 if total_turnover > 0 else 0
        balance_ratio = (abs(total_debit - total_credit) / total_turnover) * 100 if total_turnover > 0 else 0
        
        analysis = f"""
📊 نسبت‌های مالی پیشرفته:

• نسبت بدهکار: {debit_ratio:.1f}%
• نسبت بستانکار: {credit_ratio:.1f}%
• نسبت اختلاف: {balance_ratio:.1f}%

💡 تفسیر: """
        
        if balance_ratio < 5:
            analysis += "تعادل مالی عالی ✅"
        elif balance_ratio < 10:
            analysis += "تعادل مالی قابل قبول ⚡"
        else:
            analysis += "نیاز به بررسی تعادل مالی ⚠️"
            
        return analysis

    def _analyze_patterns(self, df: pd.DataFrame, query: str) -> str:
        """تحلیل الگوها"""
        # توزیع مبالغ
        debit_distribution = df['بدهکار'].value_counts(bins=5)
        credit_distribution = df['بستانکار'].value_counts(bins=5)
        
        analysis = "🔍 تحلیل الگوهای تراکنش:\n\n"
        analysis += "📊 توزیع مبالغ بدهکار:\n"
        for bin_range, count in debit_distribution.items():
            analysis += f"  - {bin_range}: {count} تراکنش\n"
        
        analysis += "\n📊 توزیع مبالغ بستانکار:\n"
        for bin_range, count in credit_distribution.items():
            analysis += f"  - {bin_range}: {count} تراکنش\n"
        
        return analysis

    def _general_accounting_analysis(self, df: pd.DataFrame, query: str) -> str:
        """تحلیل عمومی"""
        summary = self.data_manager.get_accounting_summary("default")  # استفاده از summary موجود
        
        analysis = f"""
📈 تحلیل کلی داده‌های حسابداری شما:

• تعداد اسناد: {summary.get('total_records', 0):,}
• جمع بدهکار: {summary.get('financial_totals', {}).get('total_debit', 0):,.0f} ریال
• جمع بستانکار: {summary.get('financial_totals', {}).get('total_credit', 0):,.0f} ریال
• مانده: {summary.get('financial_totals', {}).get('balance', 0):,.0f} ریال

💡 برای تحلیل‌های تخصصی‌تر می‌توانید سوالات زیر را بپرسید:
• "تراز کلی را محاسبه کن"
• "نسبت‌های مالی را تحلیل کن" 
• "الگوهای تراکنش را بررسی کن"
"""
        return analysis

    def run(self, query: str, session_id: str = "default", user_id: str = None) -> str:
        """اجرای اصلی - نسخه بهبود یافته"""
        if not query or not query.strip():
            return "لطفاً یک سوال معتبر وارد کنید."
        
        if not user_id:
            user_id = session_id
        
        logger.info(f"پردازش سوال: {query} - User: {user_id}")
        
        try:
            if session_id not in self.memory.active_sessions:
                self.memory.create_session(session_id)
            
            self.memory.add_message(session_id, "user", query)
            context = self.memory.get_context_summary(session_id)
            
            query_type = self._classify_query(query, context)
            logger.info(f"سوال طبقه‌بندی شد به: {query_type}")
            
            # پردازش بر اساس نوع سوال
            if query_type == 'follow_up':
                response = self._handle_follow_up(session_id, query)
            
            elif query_type == 'accounting':
                accounting_result = self._process_accounting_query(query, user_id)
                response = accounting_result or self._ask_llm_directly(query)
            
            elif query_type == 'tool':
                # استفاده از ابزارهای جدید
                tool_input = json.dumps({"user_id": user_id}, ensure_ascii=False)
                
                if 'تراز' in query.lower():
                    tool = self.tool_map['accounting_balance']
                elif 'نسبت' in query.lower():
                    tool = self.tool_map['financial_ratios']
                elif 'الگو' in query.lower() or 'تحلیل' in query.lower():
                    tool = self.tool_map['transaction_analysis']
                else:
                    tool = self.tool_map['accounting_balance']  # default
                
                tool_result = tool.run(tool_input)
                response = self._enhance_with_llm(query, tool_result)
            
            elif query_type == 'rag':
                rag_result = self.rag.search(query)
                if rag_result and "پاسخ مرتبطی" not in rag_result:
                    response = f"📚 بر اساس اسناد مالی:\n\n{rag_result}"
                else:
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

    
    def _handle_follow_up(self, session_id: str, query: str) -> str:
        """پردازش سوالات ادامه‌دار"""
        history = self.memory.get_conversation_history(session_id)
        last_assistant_message = None
        
        # پیدا کردن آخرین پیام دستیار
        for msg in reversed(history):
            if msg["role"] == "assistant":
                last_assistant_message = msg["content"]
                break
        
        if last_assistant_message:
            # تحلیل آخرین پیام دستیار برای فهمیدن context
            prompt = f"""
            کاربر در پاسخ به پیام قبلی من گفته: "{query}"
            
            پیام قبلی من به کاربر:
            {last_assistant_message}
            
            لطفاً بر اساس این context، پاسخ مناسب و ادامه‌دار بدهید.
            اگر من سوالی پرسیده بودم یا پیشنهادی داده بودم، به آن پاسخ دهید.
            """
            
            messages = [
                {"role": "system", "content": "شما یک دستیار مالی هستید که مکالمات را به خاطر می‌سپارد و به صورت context-aware پاسخ می‌دهد."},
                {"role": "user", "content": prompt}
            ]
            
            try:
                return self.llm.invoke(messages)
            except Exception as e:
                logger.error(f"خطا در پردازش follow-up: {e}")
        
        # fallback به پاسخ عمومی
        return self._ask_llm_directly(query)

    def _build_contextual_messages(self, session_id: str, query: str) -> List[Dict]:
        """ساخت لیست پیام‌ها با درنظرگیری تاریخچه"""
        history = self.memory.get_conversation_history(session_id, last_n=3)
        
        messages = [
            {"role": "system", "content": """
            شما یک دستیار مالی متخصص و خوش‌برخورد هستید. 
            شما حافظه مکالمه دارید و می‌توانید context گفتگو را حفظ کنید.
            به سوالات مالی و حسابداری پاسخ تخصصی دهید.
            
            ویژگی‌های پاسخ‌دهی:
            - حفظ context مکالمه
            - پاسخ‌های连贯 و ادامه‌دار
            - دقیق و مبتنی بر اصول حسابداری
            - ساختارمند و قابل فهم
            - استفاده از مثال‌های کاربردی
            - ارائه راهکارهای عملی
            - پاسخ به زبان فارسی روان و سلیس
            """}
        ]
        
        # اضافه کردن تاریخچه مکالمه
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # اضافه کردن سوال فعلی
        messages.append({"role": "user", "content": query})
        
        return messages

    def _needs_accounting_data(self, query: str) -> bool:
        """تشخیص نیاز سوال به داده‌های حسابداری"""
        accounting_keywords = [
            'تراز', 'ترازنامه', 'صورت مالی', 'سود', 'زیان', 'درآمد', 'هزینه',
            'نسبت جاری', 'نسبت آنی', 'نقدینگی', 'دارایی', 'بدهی', 'سرمایه',
            'گردش', 'مانده', 'جمع کل', 'مبلغ', 'ریال'
        ]
        return any(keyword in query for keyword in accounting_keywords)

    def _process_accounting_query(self, query: str, user_id: str) -> Optional[str]:
        """پردازش سوالات مربوط به داده‌های حسابداری"""
        try:
            # دریافت داده‌های کاربر
            df = self.data_manager.get_dataframe(user_id, 'accounting_data')
            
            if df is None or df.empty:
                return "⚠️ هیچ داده حسابداری برای تحلیل موجود نیست. لطفاً ابتدا فایل اسناد خود را آپلود کنید."
            
            # تحلیل بر اساس نوع سوال
            if 'تراز' in query or 'مانده' in query:
                return self._calculate_balance(df, query)
            elif 'نسبت جاری' in query:
                return self._calculate_current_ratio(df)
            elif 'سود' in query or 'زیان' in query:
                return self._calculate_profit_loss(df)
            elif 'گردش' in query:
                return self._calculate_turnover(df)
            else:
                return self._general_accounting_analysis(df, query)
                
        except Exception as e:
            logger.error(f"Error processing accounting query: {e}")
            return None

    def _calculate_balance(self, df: pd.DataFrame, query: str) -> str:
        """محاسبه تراز و مانده"""
        total_debit = df['بدهکار'].sum()
        total_credit = df['بستانکار'].sum()
        balance = total_debit - total_credit
        
        # تاریخ‌ها به صورت رشته
        if 'تاریخ سند' in df.columns:
            dates = df['تاریخ سند'].dropna()
            if not dates.empty:
                date_range = f"از {dates.min()} تا {dates.max()}"
            else:
                date_range = "تاریخ معتبری وجود ندارد"
        else:
            date_range = "ستون تاریخ موجود نیست"
        
        analysis = f"""
    📊 تحلیل تراز کلی:

    • محدوده تاریخ: {date_range}
    • جمع بدهکار: {total_debit:,.0f} ریال
    • جمع بستانکار: {total_credit:,.0f} ریال
    • مانده تراز: {balance:,.0f} ریال

    """
        if balance == 0:
            analysis += "✅ ترازنامه متعادل است"
        elif balance > 0:
            analysis += "📈 مازاد بدهکار وجود دارد"
        else:
            analysis += "📉 مازاد بستانکار وجود دارد"
            
        return analysis
        
    def _calculate_current_ratio(self, df: pd.DataFrame) -> str:
        """محاسبه نسبت جاری (شبیه‌سازی)"""
        # اینجا می‌تونی منطق پیچیده‌تری برای محاسبه نسبت‌ها پیاده‌سازی کنی
        current_assets = df[df['معین'] == 1]['بدهکار'].sum()  # فرض: معین 1 دارایی جاری
        current_liabilities = df[df['معین'] == 2]['بستانکار'].sum()  # فرض: معین 2 بدهی جاری
        
        if current_liabilities > 0:
            current_ratio = current_assets / current_liabilities
        else:
            current_ratio = float('inf')
        
        analysis = f"""
💧 تحلیل نسبت جاری:

• دارایی‌های جاری: {current_assets:,.0f} ریال
• بدهی‌های جاری: {current_liabilities:,.0f} ریال
• نسبت جاری: {current_ratio:.2f}

"""
        if current_ratio > 2:
            analysis += "✅ وضعیت نقدینگی عالی"
        elif current_ratio > 1:
            analysis += "⚡ وضعیت نقدینگی قابل قبول"
        else:
            analysis += "⚠️ نیاز به توجه به نقدینگی"
            
        return analysis

    def _calculate_profit_loss(self, df: pd.DataFrame) -> str:
        """محاسبه سود و زیان (شبیه‌سازی)"""
        revenue = df[df['معین'] == 3]['بستانکار'].sum()  # فرض: معین 3 درآمد
        expenses = df[df['معین'] == 4]['بدهکار'].sum()  # فرض: معین 4 هزینه
        
        profit_loss = revenue - expenses
        
        analysis = f"""
💰 تحلیل سود و زیان:

• کل درآمد: {revenue:,.0f} ریال
• کل هزینه: {expenses:,.0f} ریال
• سود/زیان خالص: {profit_loss:,.0f} ریال

"""
        if profit_loss > 0:
            analysis += "📈 سوددهی مثبت"
        elif profit_loss < 0:
            analysis += "📉 زیان دهی"
        else:
            analysis += "⚖️ نقطه سربه‌سر"
            
        return analysis

    def _calculate_turnover(self, df: pd.DataFrame) -> str:
        """محاسبه گردش (شبیه‌سازی)"""
        total_turnover = df['بدهکار'].sum() + df['بستانکار'].sum()
        
        analysis = f"""
🔄 تحلیل گردش مالی:

• گردش کل: {total_turnover:,.0f} ریال
• میانگین گردش روزانه: {total_turnover / 30:,.0f} ریال

📊 فعالیت مالی قابل توجه"""
        
        return analysis

    def _general_accounting_analysis(self, df: pd.DataFrame, query: str) -> str:
        """تحلیل عمومی حسابداری"""
        total_debit = df['بدهکار'].sum()
        total_credit = df['بستانکار'].sum()
        total_transactions = len(df)
        
        analysis = f"""
📈 تحلیل کلی داده‌های حسابداری:

• تعداد تراکنش‌ها: {total_transactions}
• جمع بدهکار: {total_debit:,.0f} ریال
• جمع بستانکار: {total_credit:,.0f} ریال
• مانده: {total_debit - total_credit:,.0f} ریال

💡 این تحلیل بر اساس داده‌های حسابداری آپلود شده شما انجام شده است.
"""
        return analysis

    def run(self, query: str, session_id: str = "default", user_id: str = None) -> str:
        """
        اجرای اصلی با Memory و Context Awareness و پشتیبانی از داده‌های کاربر
        """
        if not query or not query.strip():
            return "لطفاً یک سوال معتبر وارد کنید."
        
        if not user_id:
            user_id = session_id  # Fallback به session_id اگر user_id ارائه نشده
        
        logger.info(f"پردازش سوال: {query} - Session: {session_id} - User: {user_id}")
        
        try:
            # ایجاد یا لود session
            if session_id not in self.memory.active_sessions:
                self.memory.create_session(session_id)
            
            # ذخیره پیام کاربر
            self.memory.add_message(session_id, "user", query)
            
            # دریافت context
            context = self.memory.get_context_summary(session_id)
            
            # 1. طبقه‌بندی سوال
            query_type = self._classify_query(query, context)
            logger.info(f"سوال طبقه‌بندی شد به: {query_type}")
            
            # 2. پردازش بر اساس نوع سوال
            if query_type == 'follow_up':
                response = self._handle_follow_up(session_id, query)
            
            elif query_type == 'accounting':
                accounting_result = self._process_accounting_query(query, user_id)
                if accounting_result:
                    response = accounting_result
                else:
                    # اگر تحلیل حسابداری موفق نبود، از LLM استفاده کن
                    messages = self._build_contextual_messages(session_id, query)
                    response = self.llm.invoke(messages)
            
            elif query_type == 'tool':
                needs_tool, tool_name, tool_input = self._detect_tool_need(query)
                if needs_tool and tool_name in self.tool_map:
                    tool = self.tool_map[tool_name]
                    tool_result = tool.run(tool_input)
                    response = self._enhance_with_llm(query, tool_result)
                else:
                    messages = self._build_contextual_messages(session_id, query)
                    response = self.llm.invoke(messages)
            
            elif query_type == 'rag':
                rag_result = self.rag.search(query)
                if rag_result and "پاسخ مرتبطی" not in rag_result and "خطا" not in rag_result:
                    response = f"📚 بر اساس اسناد مالی:\n\n{rag_result}"
                else:
                    messages = self._build_contextual_messages(session_id, query)
                    response = self.llm.invoke(messages)
            
            else:  # query_type == 'general'
                messages = self._build_contextual_messages(session_id, query)
                response = self.llm.invoke(messages)
            
            # ذخیره پاسخ دستیار
            self.memory.add_message(session_id, "assistant", response)
            
            return response
            
        except Exception as e:
            logger.error(f"خطا در پردازش سوال: {e}")
            error_msg = f"متأسفانه در پردازش سوال خطایی رخ داد: {str(e)}"
            self.memory.add_message(session_id, "assistant", error_msg)
            return error_msg

    def _enhance_with_llm(self, query: str, tool_result: str) -> str:
        """ترکیب نتیجه ابزار با تحلیل LLM"""
        prompt = f"""
        شما یک تحلیل‌گر مالی حرفه‌ای هستید. بر اساس نتیجه ابزار و سوال کاربر، یک تحلیل جامع ارائه دهید.
        
        سوال کاربر: {query}
        
        نتیجه تحلیل ابزار: {tool_result}
        
        لطفاً تحلیل خود را به فارسی و به صورت حرفه‌ای ارائه دهید:
        """
        
        messages = [
            {"role": "system", "content": "شما یک دستیار مالی متخصص هستید."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            llm_analysis = self.llm.invoke(messages)
            return f"🔧 تحلیل تخصصی:\n\n{tool_result}\n\n💡 تحلیل پیشرفته:\n{llm_analysis}"
        except Exception as e:
            logger.warning(f"خطا در تحلیل LLM، برگشت به نتیجه ابزار: {e}")
            return f"📊 نتیجه تحلیل:\n\n{tool_result}"

    def _ask_llm_directly(self, query: str) -> str:
        """استفاده مستقیم از LLM برای سوالات عمومی"""
        messages = [
            {"role": "system", "content": """
            شما یک دستیار مالی متخصص و خوش‌برخورد هستید. 
            به سوالات مالی و حسابداری پاسخ تخصصی دهید.
            برای سوالات غیرمرتبط، مودبانه توضیح دهید که تخصص شما امور مالی است.
            
            ویژگی‌های پاسخ‌دهی:
            - دقیق و مبتنی بر اصول حسابداری
            - ساختارمند و قابل فهم
            - استفاده از مثال‌های کاربردی
            - ارائه راهکارهای عملی
            - پاسخ به زبان فارسی روان و سلیس
            """},
            {"role": "user", "content": query}
        ]
        
        try:
            return self.llm.invoke(messages)
        except Exception as e:
            logger.error(f"خطا در ارتباط با LLM: {e}")
            return "متأسفانه در حال حاضر امکان پاسخگویی وجود ندارد. لطفا بعدا تلاش کنید。"

    def get_available_tools(self) -> List[str]:
        """دریافت لیست ابزارهای موجود"""
        return [tool.name for tool in self.tools]

    def get_system_status(self) -> Dict[str, Any]:
        """دریافت وضعیت سیستم"""
        try:
            rag_info = self.rag.get_collection_info()
            return {
                "status": "active",
                "tools_count": len(self.tools),
                "available_tools": self.get_available_tools(),
                "rag_documents": rag_info.get("total_documents", 0),
                "rag_engine": rag_info.get("engine", "unknown"),
                "llm_status": "connected",
                "memory_sessions": len(self.memory.active_sessions),
                "data_manager": "active"
            }
        except Exception as e:
            logger.error(f"خطا در دریافت وضعیت سیستم: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def clear_memory(self, session_id: str = "default"):
        """پاک کردن memory یک session"""
        try:
            self.memory.clear_session(session_id)
            logger.info(f"Memory cleared for session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing memory: {e}")
            return False