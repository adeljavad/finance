# tools/excel_column_mapper.py
import pandas as pd
import json
import logging
from typing import Dict, List, Any, Optional
from ..deepseek_api import DeepSeekLLM

logger = logging.getLogger(__name__)

class ExcelColumnMapper:
    """
    ابزار هوشمند برای تشخیص خودکار ستون‌های فایل Excel با استفاده از LLM
    """
    
    def __init__(self):
        self.llm = DeepSeekLLM()
        self.standard_columns = {
            'شماره سند': ['شماره سند', 'شماره', 'سند', 'ش سند', 'ش.سند', 'ش سند', 'document_number', 'doc_no'],
            'تاریخ سند': ['تاریخ سند', 'تاریخ', 'ت سند', 'ت.سند', 'ت سند', 'date', 'doc_date', 'document_date'],
            'بدهکار': ['بدهکار', 'بده', 'مبلغ بدهکار', 'بدهکار ریال', 'debit', 'debit_amount'],
            'بستانکار': ['بستانکار', 'بستان', 'مبلغ بستانکار', 'بستانکار ریال', 'credit', 'credit_amount'],
            'توضیحات': ['توضیحات', 'شرح', 'شرح سند', 'description', 'narration', 'remarks'],
            'معین': ['معین', 'کد معین', 'شماره معین', 'کد حساب معین', 'subsidiary', 'subsidiary_code'],
            'تفصیلی': ['تفصیلی', 'کد تفصیلی', 'شماره تفصیلی', 'detail', 'detail_code'],
            'کل': ['کل', 'کد کل', 'شماره کل', 'کد حساب کل', 'general', 'general_ledger'],
            'شماره عطف': ['شماره عطف', 'عطف', 'ش عطف', 'reference', 'ref_no'],
            'شماره ردیف': ['شماره ردیف', 'ردیف', 'ش ردیف', 'row', 'row_number']
        }
    
    def detect_columns_mapping(self, headers: List[str], sample_data: List[Dict]) -> Dict[str, Any]:
        """
        تشخیص خودکار مپینگ ستون‌ها با استفاده از LLM
        """
        try:
            # آماده‌سازی نمونه داده برای LLM
            sample_text = self._prepare_sample_for_llm(headers, sample_data)
            
            prompt = f"""
            شما یک متخصص حسابداری و مالی هستید. لطفا ستون‌های فایل Excel را به استانداردهای حسابداری فارسی مپ کنید.

            سرستون‌های فایل:
            {headers}

            نمونه داده‌ها (۳ ردیف اول):
            {sample_text}

            لطفا هر ستون را به یکی از این دسته‌های استاندارد مپ کنید:
            ۱. شماره سند - شماره منحصربفرد سند حسابداری
            ۲. تاریخ سند - تاریخ سند به صورت 1404/01/01
            ۳. بدهکار - مبلغ بدهکار (ممکن است با جداکننده هزارگان باشد)
            ۴. بستانکار - مبلغ بستانکار (ممکن است با جداکننده هزارگان باشد)
            ۵. توضیحات - شرح عملیات مالی
            ۶. معین - کد معین حساب
            ۷. تفصیلی - کد تفصیلی
            ۸. کل - کد حساب کل
            ۹. شماره عطف - شماره مرجع
            ۱۰. شماره ردیف - شماره ردیف در سند

            اگر ستونی مربوط به این دسته‌ها نبود، نام اصلی آن را حفظ کنید.

            خروجی باید یک JSON باشد به این فرمت:
            {{
                "mapping": {{
                    "نام ستون اصلی": "نام استاندارد",
                    ...
                }},
                "confidence": "high/medium/low",
                "notes": "یادداشت‌های مهم"
            }}

            مهم: فقط JSON خالص برگردانید، بدون هیچ متن اضافی.
            """
            
            messages = [
                {
                    "role": "system", 
                    "content": "شما یک کارشناس حسابداری حرفه‌ای هستید که در تشخیص ساختار فایل‌های مالی تخصص دارید. پاسخ‌ها باید به صورت JSON ساختاریافته باشد. فقط JSON برگردانید."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            response = self.llm.invoke(messages)
            
            # پردازش پاسخ LLM
            mapping_result = self._parse_llm_response(response)
            
            logger.info(f"تشخیص ستون‌ها انجام شد. confidence: {mapping_result.get('confidence', 'unknown')}")
            
            return mapping_result
            
        except Exception as e:
            logger.error(f"خطا در تشخیص ستون‌ها: {e}")
            return self._fallback_mapping(headers)
    
    def _prepare_sample_for_llm(self, headers: List[str], sample_data: List[Dict]) -> str:
        """آماده‌سازی نمونه داده برای ارسال به LLM"""
        sample_text = ""
        for i, row in enumerate(sample_data[:3]):  # فقط ۳ ردیف اول
            sample_text += f"\nردیف {i+1}:\n"
            for header in headers:
                value = row.get(header, '')
                # محدود کردن طول مقادیر طولانی
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                sample_text += f"  {header}: {value}\n"
        
        return sample_text
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """پردازش پاسخ LLM و استخراج JSON"""
        try:
            # پیدا کردن JSON در پاسخ
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                result = json.loads(json_str)
                return result
            else:
                logger.warning("JSON در پاسخ یافت نشد. استفاده از fallback")
                return {"mapping": {}, "confidence": "low", "notes": "JSON در پاسخ یافت نشد"}
                
        except json.JSONDecodeError as e:
            logger.warning(f"خطا در decode کردن JSON از LLM: {e}")
            # تلاش برای تمیز کردن پاسخ
            cleaned_response = self._clean_llm_response(response)
            try:
                return json.loads(cleaned_response)
            except:
                return {"mapping": {}, "confidence": "low", "notes": "خطا در پردازش پاسخ LLM"}
    
    def _clean_llm_response(self, response: str) -> str:
        """تمیز کردن پاسخ LLM برای استخراج JSON"""
        # حذف markdown code blocks
        response = response.replace('```json', '').replace('```', '')
        
        # پیدا کردن اولین { و آخرین }
        start_idx = response.find('{')
        end_idx = response.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            return response[start_idx:end_idx]
        
        return response
    
    def _fallback_mapping(self, headers: List[str]) -> Dict[str, Any]:
        """مپینگ fallback در صورت شکست LLM"""
        mapping = {}
        
        for header in headers:
            header_lower = str(header).strip().lower()
            mapped = False
            
            # جستجوی مشابهت با ستون‌های استاندارد
            for std_col, variations in self.standard_columns.items():
                for variation in variations:
                    if variation.lower() in header_lower:
                        mapping[header] = std_col
                        mapped = True
                        break
                if mapped:
                    break
            
            if not mapped:
                # اگر ستون استاندارد نبود، نام اصلی حفظ شود
                mapping[header] = header
        
        return {
            "mapping": mapping,
            "confidence": "low", 
            "notes": "استفاده از مپینگ fallback"
        }
    
    def normalize_dataframe(self, df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
        """
        نرمالایز کردن DataFrame بر اساس مپینگ
        """
        try:
            # ایجاد کپی از DataFrame
            normalized_df = df.copy()
            
            # تغییر نام ستون‌ها
            column_rename = {}
            for original_col, mapped_col in mapping.items():
                if original_col in normalized_df.columns:
                    column_rename[original_col] = mapped_col
            
            if column_rename:
                normalized_df = normalized_df.rename(columns=column_rename)
            
            # نرمالایز کردن داده‌ها
            normalized_df = self._normalize_numeric_columns(normalized_df)
            normalized_df = self._normalize_date_columns(normalized_df)
            
            return normalized_df
            
        except Exception as e:
            logger.error(f"خطا در نرمالایز کردن DataFrame: {e}")
            return df
    
    def _normalize_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """نرمالایز کردن ستون‌های عددی"""
        numeric_columns = ['بدهکار', 'بستانکار']
        
        for col in numeric_columns:
            if col in df.columns:
                try:
                    # تبدیل به string و حذف جداکننده‌های هزارگان
                    df[col] = df[col].astype(str).str.replace(',', '').str.replace(' ', '')
                    
                    # تبدیل به عدد
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                except Exception as e:
                    logger.warning(f"خطا در نرمالایز کردن ستون {col}: {e}")
        
        return df
    
    def _normalize_date_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """نرمالایز کردن ستون‌های تاریخ - به صورت رشته‌ای"""
        date_columns = ['تاریخ سند']
        
        for col in date_columns:
            if col in df.columns:
                try:
                    # فقط استانداردسازی فرمت، بدون تبدیل به datetime
                    df[col] = df[col].astype(str).apply(self._convert_persian_date)
                    
                    # اطمینان از فرمت صحیح YYYY/MM/DD
                    df[col] = df[col].str.replace(r'^(\d{4})/(\d{1})/(\d{1})$', r'\1/0\2/0\3', regex=True)
                    df[col] = df[col].str.replace(r'^(\d{4})/(\d{1})/(\d{2})$', r'\1/0\2/\3', regex=True)
                    df[col] = df[col].str.replace(r'^(\d{4})/(\d{2})/(\d{1})$', r'\1/\2/0\3', regex=True)
                    
                except Exception as e:
                    logger.warning(f"خطا در نرمالایز کردن تاریخ {col}: {e}")
        
        return df

    def _convert_persian_date(self, date_str: str) -> str:
        """تبدیل تاریخ فارسی به استاندارد YYYY/MM/DD"""
        try:
            if not date_str or pd.isna(date_str) or date_str == 'nan' or date_str == 'None':
                return ''
            
            date_str = str(date_str).strip()
            
            # الگوهای مختلف تاریخ فارسی
            patterns = [
                r'^(\d{4})/(\d{1,2})/(\d{1,2})$',  # 1404/01/01
                r'^(\d{4})-(\d{1,2})-(\d{1,2})$',  # 1404-01-01
            ]
            
            for pattern in patterns:
                import re
                match = re.match(pattern, date_str)
                if match:
                    year, month, day = match.groups()
                    # اطمینان از دو رقمی بودن ماه و روز
                    month = month.zfill(2)
                    day = day.zfill(2)
                    return f"{year}/{month}/{day}"
            
            return date_str  # اگر فرمت شناخته شده نبود، همان را برگردان
            
        except Exception:
            return date_str