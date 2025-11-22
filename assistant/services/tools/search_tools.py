# assistant/services/tools/search_tools.py
import pandas as pd
import json
import re
import logging
from typing import Dict, List, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class DocumentSearchInput(BaseModel):
    user_id: str = Field(description="شناسه کاربر")
    criteria: Dict = Field(default={}, description="معیارهای جستجو")

class DocumentSearchTool(BaseTool):
    name: str = "document_search"
    description: str = "جستجوی اسناد بر اساس شماره سند، تاریخ، شرح یا سایر معیارها"
    args_schema: type = DocumentSearchInput
    
    def __init__(self, data_manager):
        super().__init__()
        self._data_manager = data_manager
    
    def _run(self, user_input: str) -> str:
        try:
            data = json.loads(user_input) if isinstance(user_input, str) else user_input
            user_id = data.get("user_id", "default")
            search_criteria = data.get("criteria", {})
            
            df = self._data_manager.get_dataframe(user_id, 'accounting_data')
            if df is None or df.empty:
                return "⚠️ هیچ داده‌ای برای جستجو موجود نیست."
            
            # فیلتر کردن داده‌ها
            filtered_df = self._apply_filters(df, search_criteria)
            
            if filtered_df.empty:
                return "❌ هیچ سندی با معیارهای جستجو یافت نشد."
            
            return self._format_search_results(filtered_df, search_criteria)
            
        except Exception as e:
            return f"خطا در جستجو: {str(e)}"
    
    def _apply_filters(self, df: pd.DataFrame, criteria: Dict) -> pd.DataFrame:
        """اعمال فیلترهای مختلف روی داده‌ها"""
        filtered_df = df.copy()
        
        # فیلتر شماره سند
        if 'document_number' in criteria:
            doc_numbers = criteria['document_number']
            if isinstance(doc_numbers, list):
                filtered_df = filtered_df[filtered_df['شماره سند'].isin(doc_numbers)]
            else:
                filtered_df = filtered_df[filtered_df['شماره سند'] == doc_numbers]
        
        # فیلتر تاریخ
        if 'date' in criteria:
            date_filter = criteria['date']
            if 'start' in date_filter and 'end' in date_filter:
                filtered_df = filtered_df[
                    (filtered_df['تاریخ سند'] >= date_filter['start']) & 
                    (filtered_df['تاریخ سند'] <= date_filter['end'])
                ]
            elif 'exact' in date_filter:
                filtered_df = filtered_df[filtered_df['تاریخ سند'] == date_filter['exact']]
        
        # فیلتر شرح
        if 'description' in criteria:
            search_text = criteria['description']
            if 'exact' in search_text:
                filtered_df = filtered_df[filtered_df['توضیحات'] == search_text['exact']]
            elif 'contains' in search_text:
                filtered_df = filtered_df[filtered_df['توضیحات'].str.contains(
                    search_text['contains'], case=False, na=False
                )]
            elif 'keywords' in search_text:
                keywords = search_text['keywords']
                pattern = '|'.join(keywords)
                filtered_df = filtered_df[filtered_df['توضیحات'].str.contains(
                    pattern, case=False, na=False
                )]
        
        # فیلتر مبلغ
        if 'amount' in criteria:
            amount_filter = criteria['amount']
            if 'min' in amount_filter:
                filtered_df = filtered_df[filtered_df['بدهکار'] >= amount_filter['min']]
            if 'max' in amount_filter:
                filtered_df = filtered_df[filtered_df['بدهکار'] <= amount_filter['max']]
        
        return filtered_df
    
    def _format_search_results(self, df: pd.DataFrame, criteria: Dict) -> str:
        """فرمت‌دهی نتایج جستجو"""
        result_count = len(df)
        total_debit = df['بدهکار'].sum()
        total_credit = df['بستانکار'].sum()
        
        results = f"""
🔍 نتایج جستجو:

• تعداد اسناد یافت شده: {result_count}
• جمع بدهکار: {total_debit:,.0f} ریال
• جمع بستانکار: {total_credit:,.0f} ریال

📋 نمونه اسناد (۵ مورد اول):
"""
        
        # نمایش ۵ سند اول
        for i, (_, row) in enumerate(df.head(5).iterrows()):
            results += f"\n{i+1}. سند {row.get('شماره سند', '')} - تاریخ {row.get('تاریخ سند', '')}"
            results += f"\n   بدهکار: {row.get('بدهکار', 0):,.0f} | بستانکار: {row.get('بستانکار', 0):,.0f}"
            results += f"\n   شرح: {row.get('توضیحات', '')[:50]}..."
        
        if result_count > 5:
            results += f"\n\n... و {result_count - 5} سند دیگر"
        
        return results

class AdvancedFilterInput(BaseModel):
    user_id: str = Field(description="شناسه کاربر")
    filters: List[Dict] = Field(default=[], description="لیست فیلترها")

class AdvancedFilterTool(BaseTool):
    name: str = "advanced_filter"
    description: str = "فیلتر پیشرفته اسناد بر اساس معیارهای ترکیبی و شرطی"
    args_schema: type = AdvancedFilterInput
    
    def __init__(self, data_manager):
        super().__init__()
        self._data_manager = data_manager
    
    def _run(self, user_input: str) -> str:
        try:
            data = json.loads(user_input) if isinstance(user_input, str) else user_input
            user_id = data.get("user_id", "default")
            filters = data.get("filters", [])
            
            df = self._data_manager.get_dataframe(user_id, 'accounting_data')
            if df is None or df.empty:
                return "⚠️ هیچ داده‌ای برای فیلتر موجود نیست."
            
            # اعمال فیلترهای ترکیبی
            filtered_df = self._apply_advanced_filters(df, filters)
            
            if filtered_df.empty:
                return "❌ هیچ سندی با فیلترهای اعمال شده یافت نشد."
            
            return self._format_advanced_results(filtered_df, filters)
            
        except Exception as e:
            return f"خطا در فیلتر پیشرفته: {str(e)}"
    
    def _apply_advanced_filters(self, df: pd.DataFrame, filters: List[Dict]) -> pd.DataFrame:
        """اعمال فیلترهای پیشرفته"""
        filtered_df = df.copy()
        
        for filter_item in filters:
            field = filter_item.get('field')
            operator = filter_item.get('operator')
            value = filter_item.get('value')
            
            if field not in df.columns:
                continue
                
            if operator == 'equals':
                filtered_df = filtered_df[filtered_df[field] == value]
            elif operator == 'contains':
                filtered_df = filtered_df[filtered_df[field].str.contains(value, na=False)]
            elif operator == 'greater_than':
                filtered_df = filtered_df[filtered_df[field] > value]
            elif operator == 'less_than':
                filtered_df = filtered_df[filtered_df[field] < value]
            elif operator == 'between':
                filtered_df = filtered_df[
                    (filtered_df[field] >= value[0]) & 
                    (filtered_df[field] <= value[1])
                ]
        
        return filtered_df
    
    def _format_advanced_results(self, df: pd.DataFrame, filters: List[Dict]) -> str:
        """فرمت‌دهی نتایج پیشرفته"""
        result_count = len(df)
        
        results = f"""
🔍 نتایج فیلتر پیشرفته:

• تعداد اسناد: {result_count}
• تعداد فیلترها: {len(filters)}

📊 خلاصه نتایج:
"""
        
        # آمارهای مختلف
        if 'بدهکار' in df.columns:
            results += f"• جمع بدهکار: {df['بدهکار'].sum():,.0f} ریال\n"
        if 'بستانکار' in df.columns:
            results += f"• جمع بستانکار: {df['بستانکار'].sum():,.0f} ریال\n"
        
        return results