# assistant/services/tools/analytical_tools.py
import pandas as pd
import json
import logging
from typing import Dict
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class PatternAnalysisInput(BaseModel):
    user_id: str = Field(description="شناسه کاربر")
    analysis_type: str = Field(default="seasonality", description="نوع تحلیل")

class PatternAnalysisTool(BaseTool):
    name: str = "pattern_analysis"
    description: str = "تحلیل الگوها و روندهای موجود در داده‌های مالی"
    args_schema: type = PatternAnalysisInput
    
    def __init__(self, data_manager):
        super().__init__()
        self._data_manager = data_manager
    
    def _run(self, user_input: str) -> str:
        try:
            data = json.loads(user_input) if isinstance(user_input, str) else user_input
            user_id = data.get("user_id", "default")
            analysis_type = data.get("analysis_type", "seasonality")
            
            df = self._data_manager.get_dataframe(user_id, 'accounting_data')
            if df is None or df.empty:
                return "⚠️ هیچ داده‌ای برای تحلیل الگو موجود نیست."
            
            patterns = self._analyze_patterns(df, analysis_type)
            return self._format_pattern_results(patterns, analysis_type)
            
        except Exception as e:
            return f"خطا در تحلیل الگو: {str(e)}"
    
    def _analyze_patterns(self, df: pd.DataFrame, analysis_type: str) -> Dict:
        """تحلیل الگوهای مختلف"""
        patterns = {}
        
        if analysis_type == "seasonality":
            patterns = self._seasonality_analysis(df)
        elif analysis_type == "outlier_detection":
            patterns = self._outlier_analysis(df)
        elif analysis_type == "cluster_analysis":
            patterns = self._cluster_analysis(df)
        
        return patterns
    
    def _seasonality_analysis(self, df: pd.DataFrame) -> Dict:
        """تحلیل فصلی"""
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
                "seasonal_peaks": {
                    "highest_debit_month": monthly_totals.loc[monthly_totals['بدهکار'].idxmax()]['month'],
                    "highest_credit_month": monthly_totals.loc[monthly_totals['بستانکار'].idxmax()]['month']
                }
            }
        except Exception as e:
            return {"error": f"خطا در تحلیل فصلی: {str(e)}"}
    
    def _outlier_analysis(self, df: pd.DataFrame) -> Dict:
        """تشخیص داده‌های پرت"""
        try:
            # محاسبه outlier بر اساس انحراف معیار
            debit_mean = df['بدهکار'].mean()
            debit_std = df['بدهکار'].std()
            credit_mean = df['بستانکار'].mean()
            credit_std = df['بستانکار'].std()
            
            debit_outliers = df[abs(df['بدهکار'] - debit_mean) > 2 * debit_std]
            credit_outliers = df[abs(df['بستانکار'] - credit_mean) > 2 * credit_std]
            
            return {
                "debit_outliers_count": len(debit_outliers),
                "credit_outliers_count": len(credit_outliers),
                "largest_debit": df['بدهکار'].max(),
                "largest_credit": df['بستانکار'].max()
            }
        except Exception as e:
            return {"error": f"خطا در تشخیص outlier: {str(e)}"}
    
    def _cluster_analysis(self, df: pd.DataFrame) -> Dict:
        """تحلیل خوشه‌ای ساده"""
        try:
            # گروه‌بندی بر اساس محدوده مبالغ
            debit_bins = pd.cut(df['بدهکار'], bins=5)
            credit_bins = pd.cut(df['بستانکار'], bins=5)
            
            debit_distribution = df.groupby(debit_bins).size().to_dict()
            credit_distribution = df.groupby(credit_bins).size().to_dict()
            
            return {
                "debit_distribution": {str(k): v for k, v in debit_distribution.items()},
                "credit_distribution": {str(k): v for k, v in credit_distribution.items()}
            }
        except Exception as e:
            return {"error": f"خطا در تحلیل خوشه‌ای: {str(e)}"}
    
    def _format_pattern_results(self, patterns: Dict, analysis_type: str) -> str:
        """فرمت‌دهی نتایج تحلیل الگو"""
        return f"""
📊 RESULTS_FOR_LLM_ANALYSIS:
ANALYSIS_TYPE: {analysis_type}
PATTERN_RESULTS:
{json.dumps(patterns, indent=2, ensure_ascii=False, default=str)}

🔍 INSTRUCTIONS_FOR_LLM:
لطفا بر اساس نتایج تحلیل الگوهای بالا، یک تحلیل حرفه‌ای ارائه دهید. 
تحلیل باید شامل موارد زیر باشد:
- تفسیر الگوهای شناسایی شده
- اهمیت آماری یافته‌ها
- پیشنهادات برای مدیریت ریسک
- راهکارهای بهبود بر اساس الگوها
"""