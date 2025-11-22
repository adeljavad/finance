# assistant/services/tools/calculation_tools.py
import pandas as pd
import json
import logging
from typing import Dict, Any
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class DataCalculatorInput(BaseModel):
    user_id: str = Field(description="شناسه کاربر")
    calculation_type: str = Field(default="basic_stats", description="نوع محاسبه")

class DataCalculatorTool(BaseTool):
    name: str = "data_calculator"
    description: str = "انجام محاسبات پیچیده روی داده‌ها و آماده‌سازی برای تحلیل LLM"
    args_schema: type = DataCalculatorInput
    
    def __init__(self, data_manager):
        super().__init__()
        self._data_manager = data_manager  # استفاده از underscore برای فیلدهای غیر Pydantic
    
    def _run(self, user_input: str) -> str:
        try:
            data = json.loads(user_input) if isinstance(user_input, str) else user_input
            user_id = data.get("user_id", "default")
            calculation_type = data.get("calculation_type", "basic_stats")
            
            df = self._data_manager.get_dataframe(user_id, 'accounting_data')
            if df is None or df.empty:
                return "⚠️ هیچ داده‌ای برای محاسبه موجود نیست."
            
            # انجام محاسبات بر اساس نوع
            calculations = self._perform_calculations(df, calculation_type)
            
            # فرمت‌دهی برای ارسال به LLM
            return self._format_for_llm(calculations, calculation_type)
            
        except Exception as e:
            return f"خطا در محاسبات: {str(e)}"
    
    def _perform_calculations(self, df: pd.DataFrame, calc_type: str) -> Dict:
        """انجام محاسبات مختلف"""
        calculations = {}
        
        if calc_type == "basic_stats":
            calculations = self._basic_statistics(df)
        elif calc_type == "financial_ratios":
            calculations = self._financial_ratios(df)
        elif calc_type == "trend_analysis":
            calculations = self._trend_analysis(df)
        elif calc_type == "distribution_analysis":
            calculations = self._distribution_analysis(df)
        
        return calculations
    
    def _basic_statistics(self, df: pd.DataFrame) -> Dict:
        """آمارهای پایه"""
        return {
            "total_records": len(df),
            "date_range": {
                "start": df['تاریخ سند'].min() if 'تاریخ سند' in df.columns else "N/A",
                "end": df['تاریخ سند'].max() if 'تاریخ سند' in df.columns else "N/A"
            },
            "debit_stats": {
                "total": df['بدهکار'].sum(),
                "mean": df['بدهکار'].mean(),
                "median": df['بدهکار'].median(),
                "std": df['بدهکار'].std(),
                "max": df['بدهکار'].max(),
                "min": df['بدهکار'].min()
            },
            "credit_stats": {
                "total": df['بستانکار'].sum(),
                "mean": df['بستانکار'].mean(),
                "median": df['بستانکار'].median(),
                "std": df['بستانکار'].std(),
                "max": df['بستانکار'].max(),
                "min": df['بستانکار'].min()
            },
            "balance": df['بدهکار'].sum() - df['بستانکار'].sum()
        }
    
    def _financial_ratios(self, df: pd.DataFrame) -> Dict:
        """محاسبه نسبت‌های مالی"""
        total_debit = df['بدهکار'].sum()
        total_credit = df['بستانکار'].sum()
        total_turnover = total_debit + total_credit
        
        return {
            "debit_credit_ratio": total_debit / total_credit if total_credit > 0 else float('inf'),
            "balance_ratio": abs(total_debit - total_credit) / total_turnover if total_turnover > 0 else 0,
            "concentration_ratios": {
                "top_5_debit": df.nlargest(5, 'بدهکار')['بدهکار'].sum() / total_debit if total_debit > 0 else 0,
                "top_5_credit": df.nlargest(5, 'بستانکار')['بستانکار'].sum() / total_credit if total_credit > 0 else 0
            }
        }
    
    def _trend_analysis(self, df: pd.DataFrame) -> Dict:
        """تحلیل روند"""
        if 'تاریخ سند' not in df.columns:
            return {"error": "ستون تاریخ موجود نیست"}
        
        try:
            # استخراج ماه از تاریخ
            df['month'] = df['تاریخ سند'].str[5:7]  # MM from YYYY/MM/DD
            monthly_totals = df.groupby('month').agg({
                'بدهکار': 'sum',
                'بستانکار': 'sum',
                'شماره سند': 'count'
            }).reset_index()
            
            return {
                "monthly_analysis": monthly_totals.to_dict('records'),
                "trend_indicators": {
                    "debit_growth": (monthly_totals['بدهکار'].iloc[-1] - monthly_totals['بدهکار'].iloc[0]) if len(monthly_totals) > 1 else 0,
                    "credit_growth": (monthly_totals['بستانکار'].iloc[-1] - monthly_totals['بستانکار'].iloc[0]) if len(monthly_totals) > 1 else 0
                }
            }
        except Exception as e:
            return {"error": f"خطا در تحلیل روند: {str(e)}"}
    
    def _distribution_analysis(self, df: pd.DataFrame) -> Dict:
        """تحلیل توزیع"""
        try:
            # توزیع مبالغ
            debit_bins = pd.cut(df['بدهکار'], bins=5)
            credit_bins = pd.cut(df['بستانکار'], bins=5)
            
            debit_dist = df.groupby(debit_bins).size().to_dict()
            credit_dist = df.groupby(credit_bins).size().to_dict()
            
            return {
                "debit_distribution": {str(k): int(v) for k, v in debit_dist.items()},
                "credit_distribution": {str(k): int(v) for k, v in credit_dist.items()},
                "skewness": {
                    "debit": df['بدهکار'].skew(),
                    "credit": df['بستانکار'].skew()
                }
            }
        except Exception as e:
            return {"error": f"خطا در تحلیل توزیع: {str(e)}"}
    
    def _format_for_llm(self, calculations: Dict, calc_type: str) -> str:
        """فرمت‌دهی نتایج برای ارسال به LLM"""
        return f"""
📊 RESULTS_FOR_LLM_ANALYSIS:
CALCULATION_TYPE: {calc_type}
DATA_SUMMARY:
{json.dumps(calculations, indent=2, ensure_ascii=False, default=str)}

🔍 INSTRUCTIONS_FOR_LLM:
لطفا بر اساس داده‌های محاسباتی بالا، یک تحلیل حرفه‌ای مالی ارائه دهید. 
تحلیل باید شامل موارد زیر باشد:
- تفسیر اعداد و نسبت‌ها
- شناسایی نقاط قوت و ضعف
- ارائه راهکارهای عملی
- استفاده از اصطلاحات حرفه‌ای حسابداری
"""