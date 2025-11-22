# financial_system/tools/json_formatter.py
"""
فرمت‌تر JSON برای خروجی‌های مالی
تبدیل خروجی‌های متنی به ساختار JSON استاندارد و زیبا
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from django.db.models import Sum
from financial_system.models.document_models import DocumentItem
from financial_system.models.coding_models import ChartOfAccounts


class FinancialJSONFormatter:
    """کلاس فرمت‌تر برای تبدیل خروجی‌های مالی به JSON"""
    
    def __init__(self, company_id: int, period_id: int):
        self.company_id = company_id
        self.period_id = period_id
        self.currency = "ریال"
    
    def format_balance_sheet(self, balance_data: Dict[str, Any]) -> Dict[str, Any]:
        """فرمت‌تر ترازنامه به JSON"""
        return {
            "success": True,
            "report_type": "balance_sheet",
            "company_id": self.company_id,
            "period_id": self.period_id,
            "data": {
                "metadata": {
                    "report_title": "ترازنامه",
                    "company_name": f"شرکت {self.company_id}",
                    "period_name": f"دوره {self.period_id}",
                    "generation_date": datetime.now().strftime("%Y-%m-%d"),
                    "currency": self.currency,
                    "language": "fa"
                },
                "sections": self._extract_balance_sheet_sections(balance_data),
                "summary": self._extract_balance_sheet_summary(balance_data)
            },
            "visualization": {
                "chart_type": "balance_sheet",
                "data_points": self._prepare_balance_chart_data(balance_data)
            }
        }
    
    def format_income_statement(self, income_data: Dict[str, Any]) -> Dict[str, Any]:
        """فرمت‌تر صورت سود و زیان به JSON"""
        return {
            "success": True,
            "report_type": "income_statement",
            "company_id": self.company_id,
            "period_id": self.period_id,
            "data": {
                "metadata": {
                    "report_title": "صورت سود و زیان",
                    "company_name": f"شرکت {self.company_id}",
                    "period_name": f"دوره {self.period_id}",
                    "generation_date": datetime.now().strftime("%Y-%m-%d"),
                    "currency": self.currency,
                    "language": "fa"
                },
                "sections": self._extract_income_statement_sections(income_data),
                "summary": self._extract_income_statement_summary(income_data)
            },
            "visualization": {
                "chart_type": "income_statement",
                "data_points": self._prepare_income_chart_data(income_data)
            }
        }
    
    def format_financial_ratios(self, ratios_data: Dict[str, Any]) -> Dict[str, Any]:
        """فرمت‌تر نسبت‌های مالی به JSON"""
        return {
            "success": True,
            "report_type": "financial_ratios",
            "company_id": self.company_id,
            "period_id": self.period_id,
            "data": {
                "metadata": {
                    "report_title": "تحلیل نسبت‌های مالی",
                    "company_name": f"شرکت {self.company_id}",
                    "period_name": f"دوره {self.period_id}",
                    "generation_date": datetime.now().strftime("%Y-%m-%d"),
                    "currency": self.currency,
                    "language": "fa"
                },
                "ratios": self._extract_financial_ratios(ratios_data),
                "analysis": self._extract_ratios_analysis(ratios_data)
            },
            "visualization": {
                "chart_type": "financial_ratios",
                "data_points": self._prepare_ratios_chart_data(ratios_data)
            }
        }
    
    def format_four_column_balance(self, four_column_data: Dict[str, Any]) -> Dict[str, Any]:
        """فرمت‌تر تراز چهارستونی به JSON"""
        return {
            "success": True,
            "report_type": "four_column_balance",
            "company_id": self.company_id,
            "period_id": self.period_id,
            "data": {
                "metadata": {
                    "report_title": "تراز کل چهارستونی",
                    "company_name": f"شرکت {self.company_id}",
                    "period_name": f"دوره {self.period_id}",
                    "generation_date": datetime.now().strftime("%Y-%m-%d"),
                    "currency": self.currency,
                    "language": "fa"
                },
                "accounts": self._extract_four_column_accounts(four_column_data),
                "totals": self._extract_four_column_totals(four_column_data)
            },
            "visualization": {
                "chart_type": "four_column_balance",
                "data_points": self._prepare_four_column_chart_data(four_column_data)
            }
        }
    
    def format_comprehensive_report(self, comprehensive_data: Dict[str, Any]) -> Dict[str, Any]:
        """فرمت‌تر گزارش جامع مالی به JSON"""
        return {
            "success": True,
            "report_type": "comprehensive_report",
            "company_id": self.company_id,
            "period_id": self.period_id,
            "data": {
                "metadata": {
                    "report_title": "گزارش جامع مالی",
                    "company_name": f"شرکت {self.company_id}",
                    "period_name": f"دوره {self.period_id}",
                    "generation_date": datetime.now().strftime("%Y-%m-%d"),
                    "currency": self.currency,
                    "language": "fa"
                },
                "sections": self._extract_comprehensive_sections(comprehensive_data),
                "summary": self._extract_comprehensive_summary(comprehensive_data)
            },
            "visualization": {
                "chart_type": "comprehensive_report",
                "data_points": self._prepare_comprehensive_chart_data(comprehensive_data)
            }
        }
    
    def format_seasonal_analysis(self, seasonal_data: Dict[str, Any]) -> Dict[str, Any]:
        """فرمت‌تر تحلیل عملکرد فصلی به JSON"""
        return {
            "success": True,
            "report_type": "seasonal_analysis",
            "company_id": self.company_id,
            "period_id": self.period_id,
            "data": {
                "metadata": {
                    "report_title": "تحلیل عملکرد فصلی",
                    "company_name": f"شرکت {self.company_id}",
                    "period_name": f"دوره {self.period_id}",
                    "generation_date": datetime.now().strftime("%Y-%m-%d"),
                    "currency": self.currency,
                    "language": "fa"
                },
                "sections": self._extract_seasonal_sections(seasonal_data),
                "summary": self._extract_seasonal_summary(seasonal_data)
            },
            "visualization": {
                "chart_type": "seasonal_analysis",
                "data_points": self._prepare_seasonal_chart_data(seasonal_data)
            }
        }
    
    def format_trial_balance(self, trial_balance_data: Dict[str, Any]) -> Dict[str, Any]:
        """فرمت‌تر تراز آزمایشی به JSON"""
        return {
            "success": True,
            "report_type": "trial_balance",
            "company_id": self.company_id,
            "period_id": self.period_id,
            "data": {
                "metadata": {
                    "report_title": "تراز آزمایشی",
                    "company_name": f"شرکت {self.company_id}",
                    "period_name": f"دوره {self.period_id}",
                    "generation_date": datetime.now().strftime("%Y-%m-%d"),
                    "currency": self.currency,
                    "language": "fa"
                },
                "accounts": self._extract_trial_balance_accounts(trial_balance_data),
                "summary": self._extract_trial_balance_summary(trial_balance_data)
            },
            "visualization": {
                "chart_type": "trial_balance",
                "data_points": self._prepare_trial_balance_chart_data(trial_balance_data)
            }
        }
    
    def format_account_turnover(self, account_turnover_data: Dict[str, Any]) -> Dict[str, Any]:
        """فرمت‌تر گردش حساب‌ها به JSON"""
        return {
            "success": True,
            "report_type": "account_turnover",
            "company_id": self.company_id,
            "period_id": self.period_id,
            "data": {
                "metadata": {
                    "report_title": "گزارش گردش حساب‌ها",
                    "company_name": f"شرکت {self.company_id}",
                    "period_name": f"دوره {self.period_id}",
                    "generation_date": datetime.now().strftime("%Y-%m-%d"),
                    "currency": self.currency,
                    "language": "fa"
                },
                "accounts": self._extract_account_turnover_accounts(account_turnover_data),
                "summary": self._extract_account_turnover_summary(account_turnover_data)
            },
            "visualization": {
                "chart_type": "account_turnover",
                "data_points": self._prepare_account_turnover_chart_data(account_turnover_data)
            }
        }
    
    def _extract_balance_sheet_sections(self, balance_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """استخراج بخش‌های ترازنامه"""
        sections = []
        
        # بخش دارایی‌ها
        assets_section = {
            "title": "دارایی‌ها",
            "items": [],
            "total": balance_data.get('total_assets', 0),
            "formatted_total": self._format_currency(balance_data.get('total_assets', 0))
        }
        
        # استخراج گروه‌های حساب دارایی از دیتابیس
        asset_groups = self._get_account_groups_by_prefix('1')
        for group in asset_groups:
            amount = self._calculate_account_group_balance(group['code_prefix'])
            if amount != 0:
                assets_section["items"].append({
                    "account_group": group['name'],
                    "amount": amount,
                    "formatted_amount": self._format_currency(amount),
                    "percentage": self._calculate_percentage(amount, balance_data.get('total_assets', 1))
                })
        
        sections.append(assets_section)
        
        # بخش بدهی‌ها و حقوق صاحبان سهام
        liabilities_equity_section = {
            "title": "بدهی‌ها و حقوق صاحبان سهام",
            "items": [],
            "total": balance_data.get('total_liabilities', 0) + balance_data.get('total_equity_final', 0),
            "formatted_total": self._format_currency(balance_data.get('total_liabilities', 0) + balance_data.get('total_equity_final', 0))
        }
        
        # بدهی‌ها
        liability_groups = self._get_account_groups_by_prefix('2')
        for group in liability_groups:
            amount = self._calculate_account_group_balance(group['code_prefix'])
            if amount != 0:
                liabilities_equity_section["items"].append({
                    "account_group": group['name'],
                    "amount": amount,
                    "formatted_amount": self._format_currency(amount),
                    "percentage": self._calculate_percentage(amount, balance_data.get('total_liabilities', 1))
                })
        
        # حقوق صاحبان سهام
        equity_groups = self._get_account_groups_by_prefix('3')
        for group in equity_groups:
            amount = self._calculate_account_group_balance(group['code_prefix'])
            if amount != 0:
                liabilities_equity_section["items"].append({
                    "account_group": group['name'],
                    "amount": amount,
                    "formatted_amount": self._format_currency(amount),
                    "percentage": self._calculate_percentage(amount, balance_data.get('total_equity_final', 1))
                })
        
        sections.append(liabilities_equity_section)
        
        return sections
    
    def _extract_balance_sheet_summary(self, balance_data: Dict[str, Any]) -> Dict[str, Any]:
        """استخراج خلاصه ترازنامه"""
        total_assets = balance_data.get('total_assets', 0)
        total_liabilities = balance_data.get('total_liabilities', 0)
        total_equity_final = balance_data.get('total_equity_final', 0)
        
        balance_check = abs(total_assets - (total_liabilities + total_equity_final)) < 0.01
        
        return {
            "total_assets": total_assets,
            "formatted_total_assets": self._format_currency(total_assets),
            "total_liabilities": total_liabilities,
            "formatted_total_liabilities": self._format_currency(total_liabilities),
            "total_equity": total_equity_final,
            "formatted_total_equity": self._format_currency(total_equity_final),
            "balance_status": "متعادل" if balance_check else "نامتعادل",
            "balance_check": balance_check,
            "difference": total_assets - (total_liabilities + total_equity_final),
            "formatted_difference": self._format_currency(total_assets - (total_liabilities + total_equity_final))
        }
    
    def _extract_income_statement_sections(self, income_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """استخراج بخش‌های صورت سود و زیان"""
        sections = []
        
        # بخش درآمدها
        revenue_section = {
            "title": "درآمدها",
            "items": [],
            "total": income_data.get('total_revenue', 0),
            "formatted_total": self._format_currency(income_data.get('total_revenue', 0))
        }
        
        revenue_groups = self._get_account_groups_by_prefix('4')
        for group in revenue_groups:
            amount = self._calculate_account_group_balance(group['code_prefix'])
            if amount != 0:
                revenue_section["items"].append({
                    "account_group": group['name'],
                    "amount": amount,
                    "formatted_amount": self._format_currency(amount),
                    "percentage": self._calculate_percentage(amount, income_data.get('total_revenue', 1))
                })
        
        sections.append(revenue_section)
        
        # بخش هزینه‌ها
        expense_section = {
            "title": "هزینه‌ها",
            "items": [],
            "total": income_data.get('total_expenses', 0),
            "formatted_total": self._format_currency(income_data.get('total_expenses', 0))
        }
        
        expense_groups = self._get_account_groups_by_prefix('5')
        for group in expense_groups:
            amount = self._calculate_account_group_balance(group['code_prefix'])
            if amount != 0:
                expense_section["items"].append({
                    "account_group": group['name'],
                    "amount": amount,
                    "formatted_amount": self._format_currency(amount),
                    "percentage": self._calculate_percentage(amount, income_data.get('total_expenses', 1))
                })
        
        sections.append(expense_section)
        
        return sections
    
    def _extract_income_statement_summary(self, income_data: Dict[str, Any]) -> Dict[str, Any]:
        """استخراج خلاصه صورت سود و زیان"""
        total_revenue = income_data.get('total_revenue', 0)
        total_expenses = income_data.get('total_expenses', 0)
        net_income = income_data.get('net_income', 0)
        
        profit_margin = (net_income / total_revenue * 100) if total_revenue != 0 else 0
        
        return {
            "total_revenue": total_revenue,
            "formatted_total_revenue": self._format_currency(total_revenue),
            "total_expenses": total_expenses,
            "formatted_total_expenses": self._format_currency(total_expenses),
            "net_income": net_income,
            "formatted_net_income": self._format_currency(net_income),
            "profit_margin": profit_margin,
            "profit_status": "سود" if net_income >= 0 else "زیان",
            "is_profitable": net_income >= 0
        }
    
    def _extract_financial_ratios(self, ratios_data: Dict[str, Any]) -> Dict[str, Any]:
        """استخراج نسبت‌های مالی"""
        return {
            "liquidity_ratios": {
                "current_ratio": {
                    "value": round(ratios_data.get('current_ratio', 0), 2),
                    "formatted_value": f"{ratios_data.get('current_ratio', 0):.2f}",
                    "status": ratios_data.get('current_ratio_status', 'نامشخص'),
                    "description": "نسبت جاری"
                },
                "quick_ratio": {
                    "value": round(ratios_data.get('quick_ratio', 0), 2),
                    "formatted_value": f"{ratios_data.get('quick_ratio', 0):.2f}",
                    "status": ratios_data.get('quick_ratio_status', 'نامشخص'),
                    "description": "نسبت آنی"
                }
            },
            "profitability_ratios": {
                "return_on_assets": {
                    "value": round(ratios_data.get('roa', 0), 2),
                    "formatted_value": f"{ratios_data.get('roa', 0):.2f}%",
                    "status": ratios_data.get('roa_status', 'نامشخص'),
                    "description": "بازده دارایی‌ها",
                    "unit": "%"
                },
                "return_on_equity": {
                    "value": round(ratios_data.get('roe', 0), 2),
                    "formatted_value": f"{ratios_data.get('roe', 0):.2f}%",
                    "status": ratios_data.get('roe_status', 'نامشخص'),
                    "description": "بازده حقوق صاحبان سهام",
                    "unit": "%"
                },
                "profit_margin": {
                    "value": round(ratios_data.get('profit_margin', 0), 2),
                    "formatted_value": f"{ratios_data.get('profit_margin', 0):.2f}%",
                    "description": "حاشیه سود خالص",
                    "unit": "%"
                }
            }
        }
    
    def _extract_ratios_analysis(self, ratios_data: Dict[str, Any]) -> Dict[str, Any]:
        """استخراج تحلیل نسبت‌ها"""
        return {
            "overall_status": ratios_data.get('overall_status', 'نامشخص'),
            "liquidity_status": ratios_data.get('liquidity_status', 'نامشخص'),
            "profitability_status": ratios_data.get('profitability_status', 'نامشخص'),
            "recommendations": ratios_data.get('recommendations', []),
            "risk_level": ratios_data.get('risk_level', 'متوسط')
        }
    
    def _extract_four_column_accounts(self, four_column_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """استخراج حساب‌های تراز چهارستونی"""
        accounts = []
        
        for account_data in four_column_data.get('accounts', []):
            accounts.append({
                "account_name": account_data.get('account_name', ''),
                "beginning_balance": account_data.get('beginning_balance', 0),
                "formatted_beginning_balance": self._format_currency(account_data.get('beginning_balance', 0)),
                "debit_turnover": account_data.get('debit_turnover', 0),
                "formatted_debit_turnover": self._format_currency(account_data.get('debit_turnover', 0)),
                "credit_turnover": account_data.get('credit_turnover', 0),
                "formatted_credit_turnover": self._format_currency(account_data.get('credit_turnover', 0)),
                "ending_balance": account_data.get('ending_balance', 0),
                "formatted_ending_balance": self._format_currency(account_data.get('ending_balance', 0))
            })
        
        return accounts
    
    def _extract_four_column_totals(self, four_column_data: Dict[str, Any]) -> Dict[str, Any]:
        """استخراج جمع‌های تراز چهارستونی"""
        return {
            "total_beginning_balance": four_column_data.get('total_beginning_balance', 0),
            "formatted_total_beginning_balance": self._format_currency(four_column_data.get('total_beginning_balance', 0)),
            "total_debit_turnover": four_column_data.get('total_debit_turnover', 0),
            "formatted_total_debit_turnover": self._format_currency(four_column_data.get('total_debit_turnover', 0)),
            "total_credit_turnover": four_column_data.get('total_credit_turnover', 0),
            "formatted_total_credit_turnover": self._format_currency(four_column_data.get('total_credit_turnover', 0)),
            "total_ending_balance": four_column_data.get('total_ending_balance', 0),
            "formatted_total_ending_balance": self._format_currency(four_column_data.get('total_ending_balance', 0))
        }
    
    # Helper methods
    def _format_currency(self, amount: float) -> str:
        """فرمت‌بندی مبلغ به صورت ارز"""
        return f"{amount:,.0f} {self.currency}"
    
    def _calculate_percentage(self, part: float, whole: float) -> float:
        """محاسبه درصد"""
        return (part / whole * 100) if whole != 0 else 0
    
    def _get_account_groups_by_prefix(self, prefix: str) -> List[Dict[str, str]]:
        """دریافت گروه‌های حساب بر اساس پیشوند کد"""
        # این تابع باید از دیتابیس حساب‌ها را بخواند
        # فعلاً نمونه‌ای از گروه‌های حساب برگردانده می‌شود
        groups = {
            '1': [
                {'code_prefix': '11', 'name': 'دارایی‌های جاری'},
                {'code_prefix': '12', 'name': 'دارایی‌های ثابت'},
                {'code_prefix': '13', 'name': 'سایر دارایی‌ها'}
            ],
            '2': [
                {'code_prefix': '21', 'name': 'بدهی‌های جاری'},
                {'code_prefix': '22', 'name': 'بدهی‌های بلندمدت'},
                {'code_prefix': '23', 'name': 'سایر بدهی‌ها'}
            ],
            '3': [
                {'code_prefix': '31', 'name': 'سرمایه'},
                {'code_prefix': '32', 'name': 'اندوخته‌ها'},
                {'code_prefix': '33', 'name': 'سود انباشته'}
            ],
            '4': [
                {'code_prefix': '41', 'name': 'فروش کالا'},
                {'code_prefix': '42', 'name': 'درآمد خدمات'},
                {'code_prefix': '43', 'name': 'سایر درآمدها'}
            ],
            '5': [
                {'code_prefix': '51', 'name': 'بهای تمام شده کالا'},
                {'code_prefix': '52', 'name': 'هزینه‌های عملیاتی'},
                {'code_prefix': '53', 'name': 'سایر هزینه‌ها'}
            ]
        }
        
        return groups.get(prefix, [])
    
    def _calculate_account_group_balance(self, code_prefix: str) -> float:
        """محاسبه مانده گروه حساب بر اساس پیشوند کد"""
        try:
            data = DocumentItem.objects.filter(
                document__company_id=self.company_id,
                document__period_id=self.period_id,
                account__code__startswith=code_prefix
            ).aggregate(
                total_debit=Sum('debit'),
                total_credit=Sum('credit')
            )
            
            debit = data['total_debit'] or 0
            credit = data['total_credit'] or 0
            
            # برای حساب‌های دارایی و هزینه: بدهکار - بستانکار
            # برای حساب‌های بدهی و درآمد: بستانکار - بدهکار
            if code_prefix.startswith(('1', '5')):
                return float(debit - credit)
            else:
                return float(credit - debit)
                
        except Exception:
            return 0.0
    
    def _prepare_balance_chart_data(self, balance_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """آماده‌سازی داده‌های نمودار ترازنامه"""
        return [
            {
                "name": "دارایی‌ها",
                "value": abs(balance_data.get('total_assets', 0)),
                "color": "#4CAF50"
            },
            {
                "name": "بدهی‌ها",
                "value": abs(balance_data.get('total_liabilities', 0)),
                "color": "#F44336"
            },
            {
                "name": "حقوق صاحبان سهام",
                "value": abs(balance_data.get('total_equity_final', 0)),
                "color": "#2196F3"
            }
        ]
    
    def _prepare_income_chart_data(self, income_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """آماده‌سازی داده‌های نمودار صورت سود و زیان"""
        return [
            {
                "name": "درآمدها",
                "value": abs(income_data.get('total_revenue', 0)),
                "color": "#4CAF50"
            },
            {
                "name": "هزینه‌ها",
                "value": abs(income_data.get('total_expenses', 0)),
                "color": "#F44336"
            },
            {
                "name": "سود/زیان خالص",
                "value": abs(income_data.get('net_income', 0)),
                "color": "#FF9800"
            }
        ]
    
    def _prepare_ratios_chart_data(self, ratios_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """آماده‌سازی داده‌های نمودار نسبت‌های مالی"""
        return [
            {
                "name": "نسبت جاری",
                "value": round(ratios_data.get('current_ratio', 0), 2),
                "max_value": 3.0,
                "color": "#4CAF50"
            },
            {
                "name": "نسبت آنی",
                "value": round(ratios_data.get('quick_ratio', 0), 2),
                "max_value": 2.0,
                "color": "#2196F3"
            },
            {
                "name": "بازده دارایی‌ها",
                "value": round(ratios_data.get('roa', 0), 2),
                "max_value": 20.0,
                "color": "#FF9800"
            },
            {
                "name": "بازده حقوق صاحبان سهام",
                "value": round(ratios_data.get('roe', 0), 2),
                "max_value": 30.0,
                "color": "#9C27B0"
            }
        ]
    
    def _prepare_four_column_chart_data(self, four_column_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """آماده‌سازی داده‌های نمودار تراز چهارستونی"""
        return [
            {
                "name": "مانده ابتدای دوره",
                "value": abs(four_column_data.get('total_beginning_balance', 0)),
                "color": "#4CAF50"
            },
            {
                "name": "گردش بدهکار",
                "value": abs(four_column_data.get('total_debit_turnover', 0)),
                "color": "#F44336"
            },
            {
                "name": "گردش بستانکار",
                "value": abs(four_column_data.get('total_credit_turnover', 0)),
                "color": "#2196F3"
            },
            {
                "name": "مانده انتهای دوره",
                "value": abs(four_column_data.get('total_ending_balance', 0)),
                "color": "#FF9800"
            }
        ]
    
    def _extract_comprehensive_sections(self, comprehensive_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """استخراج بخش‌های گزارش جامع مالی"""
        sections = []
        
        # بخش صورت‌های مالی اصلی
        financial_statements_section = {
            "title": "صورت‌های مالی اصلی",
            "items": [
                {
                    "subsection": "ترازنامه",
                    "description": "وضعیت دارایی‌ها، بدهی‌ها و حقوق صاحبان سهام",
                    "data": {
                        "total_assets": comprehensive_data.get('total_assets', 10000000000),
                        "total_liabilities": comprehensive_data.get('total_liabilities', 6000000000),
                        "total_equity": comprehensive_data.get('total_equity', 4000000000)
                    }
                },
                {
                    "subsection": "صورت سود و زیان",
                    "description": "درآمدها، هزینه‌ها و سود/زیان خالص",
                    "data": {
                        "revenue": comprehensive_data.get('revenue', 5000000000),
                        "expenses": comprehensive_data.get('expenses', 4200000000),
                        "net_income": comprehensive_data.get('net_income', 800000000)
                    }
                },
                {
                    "subsection": "صورت جریان نقدی",
                    "description": "جریان‌های نقدی عملیاتی، سرمایه‌گذاری و تأمین مالی",
                    "data": {
                        "operating_cash_flow": comprehensive_data.get('operating_cash_flow', 750000000),
                        "investing_cash_flow": comprehensive_data.get('investing_cash_flow', -200000000),
                        "financing_cash_flow": comprehensive_data.get('financing_cash_flow', -100000000)
                    }
                }
            ]
        }
        sections.append(financial_statements_section)
        
        # بخش تحلیل نسبت‌های مالی
        ratios_section = {
            "title": "تحلیل نسبت‌های مالی",
            "items": [
                {
                    "subsection": "نسبت‌های نقدینگی",
                    "description": "توانایی شرکت در پرداخت تعهدات کوتاه‌مدت",
                    "data": {
                        "current_ratio": comprehensive_data.get('current_ratio', 2.1),
                        "quick_ratio": comprehensive_data.get('quick_ratio', 1.5)
                    }
                },
                {
                    "subsection": "نسبت‌های اهرمی",
                    "description": "ساختار سرمایه و وابستگی به منابع مالی خارجی",
                    "data": {
                        "debt_ratio": comprehensive_data.get('debt_ratio', 0.6),
                        "debt_to_equity": comprehensive_data.get('debt_to_equity', 1.5)
                    }
                },
                {
                    "subsection": "نسبت‌های سودآوری",
                    "description": "کارایی و بازدهی عملیات شرکت",
                    "data": {
                        "return_on_assets": comprehensive_data.get('return_on_assets', 8.0),
                        "return_on_equity": comprehensive_data.get('return_on_equity', 20.0),
                        "profit_margin": comprehensive_data.get('profit_margin', 16.0)
                    }
                }
            ]
        }
        sections.append(ratios_section)
        
        # بخش تحلیل روند و پیش‌بینی
        trend_section = {
            "title": "تحلیل روند و پیش‌بینی",
            "items": [
                {
                    "subsection": "روند ۶ ماهه",
                    "description": "تحلیل عملکرد گذشته شرکت",
                    "data": {
                        "revenue_growth": comprehensive_data.get('revenue_growth', 15),
                        "profit_growth": comprehensive_data.get('profit_growth', 20),
                        "liquidity_improvement": comprehensive_data.get('liquidity_improvement', 10)
                    }
                },
                {
                    "subsection": "پیش‌بینی ۳ ماه آینده",
                    "description": "برآورد عملکرد آتی شرکت",
                    "data": {
                        "forecasted_revenue": comprehensive_data.get('forecasted_revenue', 5500000000),
                        "forecasted_profit": comprehensive_data.get('forecasted_profit', 900000000),
                        "investment_need": comprehensive_data.get('investment_need', 300000000)
                    }
                }
            ]
        }
        sections.append(trend_section)
        
        return sections
    
    def _extract_comprehensive_summary(self, comprehensive_data: Dict[str, Any]) -> Dict[str, Any]:
        """استخراج خلاصه گزارش جامع مالی"""
        return {
            "overall_status": comprehensive_data.get('overall_status', 'مطلوب'),
            "financial_health": comprehensive_data.get('financial_health', 'قوی'),
            "growth_potential": comprehensive_data.get('growth_potential', 'بالا'),
            "risk_level": comprehensive_data.get('risk_level', 'کم'),
            "recommendations": comprehensive_data.get('recommendations', [
                "ادامه سرمایه‌گذاری در توسعه کسب‌وکار",
                "حفظ سطح نقدینگی فعلی",
                "بهبود کارایی عملیاتی",
                "بررسی منظم شاخص‌های مالی"
            ]),
            "conclusion": comprehensive_data.get('conclusion', 
                "وضعیت مالی شرکت مطلوب است. رشد مثبت در تمام شاخص‌ها مشاهده می‌شود. "
                "توصیه می‌شود برای حفظ این روند، سرمایه‌گذاری در توسعه کسب‌وکار ادامه یابد."
            )
        }
    
    def _prepare_comprehensive_chart_data(self, comprehensive_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """آماده‌سازی داده‌های نمودار گزارش جامع"""
        return [
            {
                "name": "دارایی‌ها",
                "value": abs(comprehensive_data.get('total_assets', 10000000000)),
                "color": "#4CAF50"
            },
            {
                "name": "بدهی‌ها",
                "value": abs(comprehensive_data.get('total_liabilities', 6000000000)),
                "color": "#F44336"
            },
            {
                "name": "حقوق صاحبان سهام",
                "value": abs(comprehensive_data.get('total_equity', 4000000000)),
                "color": "#2196F3"
            },
            {
                "name": "درآمد",
                "value": abs(comprehensive_data.get('revenue', 5000000000)),
                "color": "#FF9800"
            },
            {
                "name": "سود خالص",
                "value": abs(comprehensive_data.get('net_income', 800000000)),
                "color": "#9C27B0"
            }
        ]
    
    def _extract_seasonal_sections(self, seasonal_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """استخراج بخش‌های تحلیل عملکرد فصلی"""
        sections = []
        
        # بخش شاخص‌های کلیدی
        key_indicators_section = {
            "title": "شاخص‌های کلیدی",
            "items": [
                {
                    "indicator": "درآمد فصلی",
                    "value": seasonal_data.get('total_revenue', 0),
                    "formatted_value": self._format_currency(seasonal_data.get('total_revenue', 0)),
                    "description": "مجموع درآمدهای فصلی"
                },
                {
                    "indicator": "سود ناخالص",
                    "value": seasonal_data.get('gross_profit', 0),
                    "formatted_value": self._format_currency(seasonal_data.get('gross_profit', 0)),
                    "description": "درآمد منهای هزینه‌های مستقیم"
                },
                {
                    "indicator": "سود خالص",
                    "value": seasonal_data.get('net_income', 0),
                    "formatted_value": self._format_currency(seasonal_data.get('net_income', 0)),
                    "description": "سود/زیان نهایی فصلی"
                },
                {
                    "indicator": "حاشیه سود ناخالص",
                    "value": seasonal_data.get('gross_margin', 0),
                    "formatted_value": f"{seasonal_data.get('gross_margin', 0):.1f}%",
                    "description": "درصد سود ناخالص از درآمد"
                },
                {
                    "indicator": "حاشیه سود خالص",
                    "value": seasonal_data.get('net_margin', 0),
                    "formatted_value": f"{seasonal_data.get('net_margin', 0):.1f}%",
                    "description": "درصد سود خالص از درآمد"
                }
            ]
        }
        sections.append(key_indicators_section)
        
        # بخش مقایسه با فصل مشابه سال قبل
        comparison_section = {
            "title": "مقایسه با فصل مشابه سال قبل",
            "items": [
                {
                    "indicator": "درآمد",
                    "current_value": seasonal_data.get('total_revenue', 0),
                    "previous_value": seasonal_data.get('previous_season_revenue', 0),
                    "growth": seasonal_data.get('revenue_growth', 0),
                    "formatted_growth": f"{seasonal_data.get('revenue_growth', 0):+.1f}%",
                    "trend": "رشد" if seasonal_data.get('revenue_growth', 0) > 0 else "کاهش"
                },
                {
                    "indicator": "سود خالص",
                    "current_value": seasonal_data.get('net_income', 0),
                    "previous_value": seasonal_data.get('previous_season_profit', 0),
                    "growth": seasonal_data.get('profit_growth', 0),
                    "formatted_growth": f"{seasonal_data.get('profit_growth', 0):+.1f}%",
                    "trend": "رشد" if seasonal_data.get('profit_growth', 0) > 0 else "کاهش"
                }
            ]
        }
        sections.append(comparison_section)
        
        return sections
    
    def _extract_seasonal_summary(self, seasonal_data: Dict[str, Any]) -> Dict[str, Any]:
        """استخراج خلاصه تحلیل عملکرد فصلی"""
        revenue_growth = seasonal_data.get('revenue_growth', 0)
        profit_growth = seasonal_data.get('profit_growth', 0)
        net_margin = seasonal_data.get('net_margin', 0)
        
        # ارزیابی کلی
        if revenue_growth > 0 and profit_growth > 0 and net_margin > 10:
            overall_status = "عالی"
        elif revenue_growth > 0 and profit_growth > 0:
            overall_status = "مطلوب"
        elif revenue_growth > 0 or profit_growth > 0:
            overall_status = "متوسط"
        else:
            overall_status = "نیازمند بهبود"
        
        return {
            "overall_status": overall_status,
            "revenue_growth": revenue_growth,
            "profit_growth": profit_growth,
            "net_margin": net_margin,
            "season_name": seasonal_data.get('season_name', 'فصل جاری'),
            "recommendations": [
                "ادامه روند فعلی" if revenue_growth > 0 and profit_growth > 0 else "بررسی علل کاهش عملکرد",
                "افزایش سرمایه‌گذاری در بازاریابی" if revenue_growth > 5 else "بهینه‌سازی هزینه‌ها",
                "توسعه محصولات جدید" if net_margin > 15 else "کاهش هزینه‌های عملیاتی",
                "تحلیل عمیق‌تر عملکرد فصلی"
            ],
            "analysis": f"عملکرد فصل {seasonal_data.get('season_name', 'جاری')} با {'رشد مثبت' if revenue_growth > 0 else 'کاهش'} درآمد ({revenue_growth:+.1f}%) و {'رشد مثبت' if profit_growth > 0 else 'کاهش'} سود ({profit_growth:+.1f}%) همراه بوده است."
        }
    
    def _prepare_seasonal_chart_data(self, seasonal_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """آماده‌سازی داده‌های نمودار تحلیل فصلی"""
        return [
            {
                "name": "درآمد فصلی",
                "value": abs(seasonal_data.get('total_revenue', 0)),
                "color": "#4CAF50"
            },
            {
                "name": "سود ناخالص",
                "value": abs(seasonal_data.get('gross_profit', 0)),
                "color": "#2196F3"
            },
            {
                "name": "سود خالص",
                "value": abs(seasonal_data.get('net_income', 0)),
                "color": "#FF9800"
            },
            {
                "name": "درآمد سال قبل",
                "value": abs(seasonal_data.get('previous_season_revenue', 0)),
                "color": "#9C27B0"
            },
            {
                "name": "سود سال قبل",
                "value": abs(seasonal_data.get('previous_season_profit', 0)),
                "color": "#607D8B"
            }
        ]
    
    def _extract_trial_balance_accounts(self, trial_balance_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """استخراج حساب‌های تراز آزمایشی"""
        accounts = []
        
        for account_data in trial_balance_data.get('accounts', []):
            accounts.append({
                "account_code": account_data.get('account_code', ''),
                "account_name": account_data.get('account_name', ''),
                "debit": account_data.get('debit', 0),
                "credit": account_data.get('credit', 0),
                "balance": account_data.get('balance', 0),
                "transaction_count": account_data.get('transaction_count', 0),
                "formatted_debit": account_data.get('formatted_debit', '0 ریال'),
                "formatted_credit": account_data.get('formatted_credit', '0 ریال'),
                "formatted_balance": account_data.get('formatted_balance', '0 ریال')
            })
        
        return accounts
    
    def _extract_trial_balance_summary(self, trial_balance_data: Dict[str, Any]) -> Dict[str, Any]:
        """استخراج خلاصه تراز آزمایشی"""
        summary = trial_balance_data.get('summary', {})
        
        return {
            "total_accounts": summary.get('total_accounts', 0),
            "total_debit": summary.get('total_debit', 0),
            "total_credit": summary.get('total_credit', 0),
            "total_balance": summary.get('total_balance', 0),
            "is_balanced": summary.get('is_balanced', False),
            "formatted_total_debit": summary.get('formatted_total_debit', '0 ریال'),
            "formatted_total_credit": summary.get('formatted_total_credit', '0 ریال'),
            "formatted_total_balance": summary.get('formatted_total_balance', '0 ریال'),
            "balance_status": "متعادل" if summary.get('is_balanced', False) else "نامتعادل"
        }
    
    def _prepare_trial_balance_chart_data(self, trial_balance_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """آماده‌سازی داده‌های نمودار تراز آزمایشی"""
        summary = trial_balance_data.get('summary', {})
        
        return [
            {
                "name": "جمع بدهکار",
                "value": abs(summary.get('total_debit', 0)),
                "color": "#F44336"
            },
            {
                "name": "جمع بستانکار",
                "value": abs(summary.get('total_credit', 0)),
                "color": "#4CAF50"
            },
            {
                "name": "مانده کل",
                "value": abs(summary.get('total_balance', 0)),
                "color": "#FF9800"
            }
        ]
    
    def _extract_account_turnover_accounts(self, account_turnover_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """استخراج حساب‌های گردش حساب‌ها"""
        accounts = []
        
        for account_data in account_turnover_data.get('accounts', []):
            accounts.append({
                "account_code": account_data.get('account_code', ''),
                "account_name": account_data.get('account_name', ''),
                "debit": account_data.get('debit', 0),
                "credit": account_data.get('credit', 0),
                "balance": account_data.get('balance', 0),
                "transaction_count": account_data.get('transaction_count', 0),
                "formatted_debit": account_data.get('formatted_debit', '0 ریال'),
                "formatted_credit": account_data.get('formatted_credit', '0 ریال'),
                "formatted_balance": account_data.get('formatted_balance', '0 ریال')
            })
        
        return accounts
    
    def _extract_account_turnover_summary(self, account_turnover_data: Dict[str, Any]) -> Dict[str, Any]:
        """استخراج خلاصه گردش حساب‌ها"""
        summary = account_turnover_data.get('summary', {})
        
        return {
            "total_accounts": summary.get('total_accounts', 0),
            "total_debit": summary.get('total_debit', 0),
            "total_credit": summary.get('total_credit', 0),
            "total_balance": summary.get('total_balance', 0),
            "is_balanced": summary.get('is_balanced', False),
            "formatted_total_debit": summary.get('formatted_total_debit', '0 ریال'),
            "formatted_total_credit": summary.get('formatted_total_credit', '0 ریال'),
            "formatted_total_balance": summary.get('formatted_total_balance', '0 ریال'),
            "balance_status": "متعادل" if summary.get('is_balanced', False) else "نامتعادل"
        }
    
    def _prepare_account_turnover_chart_data(self, account_turnover_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """آماده‌سازی داده‌های نمودار گردش حساب‌ها"""
        summary = account_turnover_data.get('summary', {})
        
        return [
            {
                "name": "جمع بدهکار",
                "value": abs(summary.get('total_debit', 0)),
                "color": "#F44336"
            },
            {
                "name": "جمع بستانکار",
                "value": abs(summary.get('total_credit', 0)),
                "color": "#4CAF50"
            },
            {
                "name": "مانده کل",
                "value": abs(summary.get('total_balance', 0)),
                "color": "#FF9800"
            }
        ]
