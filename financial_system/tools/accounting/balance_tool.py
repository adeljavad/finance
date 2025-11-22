"""
ابزار تراز چهارستونی برای سیستم مالی
"""

from typing import Dict, Any, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class BalanceInput(BaseModel):
    """ورودی ابزار تراز چهارستونی"""
    company_id: int = Field(
        default=1,
        description="شناسه شرکت"
    )
    period_id: int = Field(
        default=1,
        description="شناسه دوره مالی"
    )
    season: str = Field(
        default="spring",
        description="فصل: spring, summer, autumn, winter"
    )


class BalanceTool(BaseTool):
    """ابزار تولید تراز چهارستونی"""
    
    name: str = "balance_tool"
    description: str = """
    ابزار تولید تراز کل چهارستونی شامل مانده ابتدای دوره، گردش بدهکار، گردش بستانکار و مانده انتهای دوره.
    کاربرد: تراز چهارستونی، تراز چهار ستونی، تراز کل، گردش حساب‌ها
    """
    args_schema: type = BalanceInput

    def _run(
        self, 
        company_id: int = 1,
        period_id: int = 1,
        season: str = "spring"
    ) -> Dict[str, Any]:
        """اجرای ابزار تراز چهارستونی"""
        
        try:
            # مپینگ فصل به نام فارسی
            season_map = {
                "spring": "بهار",
                "summer": "تابستان", 
                "autumn": "پاییز",
                "winter": "زمستان"
            }
            
            season_name = season_map.get(season, season)
            
            # در این نسخه از داده‌های نمونه استفاده می‌کنیم
            # در نسخه واقعی باید از دیتابیس خوانده شود
            balance_data = self._generate_sample_balance_data(company_id, period_id, season_name)
            
            return {
                "success": True,
                "response_type": "balance_sheet",
                "data": balance_data,
                "company_id": company_id,
                "period_id": period_id,
                "season": season_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"خطا در تولید تراز چهارستونی: {str(e)}",
                "response_type": "error"
            }

    def _generate_sample_balance_data(self, company_id: int, period_id: int, season: str) -> Dict[str, Any]:
        """تولید داده‌های نمونه برای تراز چهارستونی"""
        
        # حساب‌های نمونه با گردش مالی
        accounts_data = [
            {
                "account_name": "صندوق",
                "beginning_balance": 50000000,
                "debit_turnover": 25000000,
                "credit_turnover": 15000000,
                "ending_balance": 60000000
            },
            {
                "account_name": "بانک",
                "beginning_balance": 200000000,
                "debit_turnover": 80000000,
                "credit_turnover": 120000000,
                "ending_balance": 160000000
            },
            {
                "account_name": "اسناد دریافتنی",
                "beginning_balance": 150000000,
                "debit_turnover": 100000000,
                "credit_turnover": 80000000,
                "ending_balance": 170000000
            },
            {
                "account_name": "موجودی کالا",
                "beginning_balance": 300000000,
                "debit_turnover": 200000000,
                "credit_turnover": 250000000,
                "ending_balance": 250000000
            },
            {
                "account_name": "دارایی‌های ثابت",
                "beginning_balance": 800000000,
                "debit_turnover": 100000000,
                "credit_turnover": 50000000,
                "ending_balance": 850000000
            },
            {
                "account_name": "اسناد پرداختنی",
                "beginning_balance": 120000000,
                "debit_turnover": 60000000,
                "credit_turnover": 80000000,
                "ending_balance": 140000000
            },
            {
                "account_name": "حساب‌های پرداختنی",
                "beginning_balance": 80000000,
                "debit_turnover": 40000000,
                "credit_turnover": 60000000,
                "ending_balance": 100000000
            },
            {
                "account_name": "وام‌های بلندمدت",
                "beginning_balance": 400000000,
                "debit_turnover": 50000000,
                "credit_turnover": 100000000,
                "ending_balance": 450000000
            },
            {
                "account_name": "سرمایه",
                "beginning_balance": 500000000,
                "debit_turnover": 0,
                "credit_turnover": 0,
                "ending_balance": 500000000
            },
            {
                "account_name": "سود انباشته",
                "beginning_balance": 100000000,
                "debit_turnover": 0,
                "credit_turnover": 50000000,
                "ending_balance": 150000000
            }
        ]
        
        # محاسبه جمع‌ها
        total_beginning_balance = sum(acc["beginning_balance"] for acc in accounts_data)
        total_debit_turnover = sum(acc["debit_turnover"] for acc in accounts_data)
        total_credit_turnover = sum(acc["credit_turnover"] for acc in accounts_data)
        total_ending_balance = sum(acc["ending_balance"] for acc in accounts_data)
        
        # ساخت گزارش
        report = f"""
📊 **تراز کل چهارستونی - فصل {season}**

شرکت: {company_id} | دوره مالی: {period_id}

| حساب | مانده ابتدای دوره | گردش بدهکار | گردش بستانکار | مانده انتهای دوره |
|-------|-------------------|-------------|---------------|-------------------|
"""
        
        for account in accounts_data:
            report += f"| {account['account_name']} | {account['beginning_balance']:,} | {account['debit_turnover']:,} | {account['credit_turnover']:,} | {account['ending_balance']:,} |\n"
        
        report += f"""
| **جمع** | **{total_beginning_balance:,}** | **{total_debit_turnover:,}** | **{total_credit_turnover:,}** | **{total_ending_balance:,}** |

**تحلیل کلی:**
- جمع گردش بدهکار: {total_debit_turnover:,} ریال
- جمع گردش بستانکار: {total_credit_turnover:,} ریال  
- تفاوت گردش: {total_debit_turnover - total_credit_turnover:,} ریال
- جمع نهایی مانده‌ها: {total_ending_balance:,} ریال

**نکات مهم:**
- تراز چهارستونی وضعیت گردش حساب‌ها را به وضوح نشان می‌دهد
- مانده ابتدای دوره + گردش بدهکار - گردش بستانکار = مانده انتهای دوره
- این گزارش برای تحلیل عملکرد فصلی بسیار مفید است

**تاریخ تولید:** امروز
"""
        
        return {
            "report_title": f"تراز کل چهارستونی - فصل {season}",
            "company_id": company_id,
            "period_id": period_id,
            "season": season,
            "accounts": accounts_data,
            "totals": {
                "beginning_balance": total_beginning_balance,
                "debit_turnover": total_debit_turnover,
                "credit_turnover": total_credit_turnover,
                "ending_balance": total_ending_balance
            },
            "formatted_report": report
        }

    async def _arun(
        self, 
        company_id: int = 1,
        period_id: int = 1,
        season: str = "spring"
    ) -> Dict[str, Any]:
        """اجرای Async ابزار تراز چهارستونی"""
        return self._run(company_id, period_id, season)
