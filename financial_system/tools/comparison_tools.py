# financial_system/tools/comparison_tools.py
from typing import Dict, Any

def compare_financial_ratios_tool(company_id: int, period1_id: int, period2_id: int, ratio_type: str = "نسبت آنی") -> str:
    """ابزار مقایسه نسبت‌های مالی بین دو دوره از داده‌های واقعی"""
    try:
        from django.db.models import Sum
        from financial_system.models.document_models import DocumentItem
        
        def calculate_ratio(company_id, period_id, ratio_type):
            """محاسبه نسبت مالی برای یک دوره خاص"""
            if ratio_type == "نسبت جاری":
                # محاسبه نسبت جاری
                current_assets_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='11'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                current_liabilities_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='21'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                current_assets = (current_assets_data['total_debit'] or 0) - (current_assets_data['total_credit'] or 0)
                current_liabilities = (current_liabilities_data['total_credit'] or 0) - (current_liabilities_data['total_debit'] or 0)
                
                return current_assets / current_liabilities if current_liabilities != 0 else 0
                
            elif ratio_type == "نسبت آنی":
                # محاسبه نسبت آنی
                current_assets_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='11'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                inventory_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='114'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                current_liabilities_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='21'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                current_assets = (current_assets_data['total_debit'] or 0) - (current_assets_data['total_credit'] or 0)
                inventory = (inventory_data['total_debit'] or 0) - (inventory_data['total_credit'] or 0)
                current_liabilities = (current_liabilities_data['total_credit'] or 0) - (current_liabilities_data['total_debit'] or 0)
                
                return (current_assets - inventory) / current_liabilities if current_liabilities != 0 else 0
                
            elif ratio_type == "بازده دارایی":
                # محاسبه بازده دارایی‌ها
                total_assets_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='1'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                revenue_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='4'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                expense_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='5'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                total_assets = (total_assets_data['total_debit'] or 0) - (total_assets_data['total_credit'] or 0)
                total_revenue = (revenue_data['total_credit'] or 0) - (revenue_data['total_debit'] or 0)
                total_expenses = (expense_data['total_debit'] or 0) - (expense_data['total_credit'] or 0)
                net_income = total_revenue - total_expenses
                
                return (net_income / total_assets * 100) if total_assets != 0 else 0
                
            elif ratio_type == "حاشیه سود":
                # محاسبه حاشیه سود
                revenue_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='4'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                expense_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='5'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                total_revenue = (revenue_data['total_credit'] or 0) - (revenue_data['total_debit'] or 0)
                total_expenses = (expense_data['total_debit'] or 0) - (expense_data['total_credit'] or 0)
                net_income = total_revenue - total_expenses
                
                return (net_income / total_revenue * 100) if total_revenue != 0 else 0
                
            else:
                return 0
        
        # محاسبه نسبت‌ها برای دو دوره
        ratio1 = calculate_ratio(company_id, period1_id, ratio_type)
        ratio2 = calculate_ratio(company_id, period2_id, ratio_type)
        
        # تحلیل تغییرات
        change = ratio2 - ratio1
        change_percent = (change / ratio1 * 100) if ratio1 != 0 else 0
        
        trend = "مثبت" if change > 0 else "منفی"
        recommendation = "ادامه روند فعلی" if change > 0 else "بررسی علل کاهش"
        
        return f"""
        📊 مقایسه {ratio_type} - شرکت {company_id}
        
        | دوره | مقدار | تغییر |
        |------|-------|--------|
        | دوره {period1_id} | {ratio1:.2f} | - |
        | دوره {period2_id} | {ratio2:.2f} | {change:+.2f} ({change_percent:+.1f}%) |
        
        تحلیل:
        - {ratio_type} در دوره {period2_id} نسبت به دوره {period1_id} {'افزایش' if change > 0 else 'کاهش'} یافته است
        - روند: {trend}
        - میزان تغییر: {change_percent:+.1f}%
        - توصیه: {recommendation}
        """
        
    except Exception as e:
        return f"خطا در مقایسه نسبت‌ها: {str(e)}"

def analyze_trend_tool(company_id: int, metric: str, periods: list) -> str:
    """ابزار تحلیل روند شاخص‌های مالی از داده‌های واقعی"""
    try:
        from django.db.models import Sum
        from financial_system.models.document_models import DocumentItem
        
        def calculate_metric(company_id, period_id, metric):
            """محاسبه متریک مالی برای یک دوره خاص"""
            if metric == "نسبت آنی":
                # محاسبه نسبت آنی
                current_assets_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='11'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                inventory_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='114'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                current_liabilities_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='21'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                current_assets = (current_assets_data['total_debit'] or 0) - (current_assets_data['total_credit'] or 0)
                inventory = (inventory_data['total_debit'] or 0) - (inventory_data['total_credit'] or 0)
                current_liabilities = (current_liabilities_data['total_credit'] or 0) - (current_liabilities_data['total_debit'] or 0)
                
                return (current_assets - inventory) / current_liabilities if current_liabilities != 0 else 0
                
            elif metric == "نسبت جاری":
                # محاسبه نسبت جاری
                current_assets_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='11'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                current_liabilities_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='21'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                current_assets = (current_assets_data['total_debit'] or 0) - (current_assets_data['total_credit'] or 0)
                current_liabilities = (current_liabilities_data['total_credit'] or 0) - (current_liabilities_data['total_debit'] or 0)
                
                return current_assets / current_liabilities if current_liabilities != 0 else 0
                
            elif metric == "درآمد":
                # محاسبه درآمد
                revenue_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='4'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                total_revenue = (revenue_data['total_credit'] or 0) - (revenue_data['total_debit'] or 0)
                return total_revenue / 1000000  # تبدیل به میلیون ریال
                
            elif metric == "سود خالص":
                # محاسبه سود خالص
                revenue_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='4'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                expense_data = DocumentItem.objects.filter(
                    document__company_id=company_id,
                    document__period_id=period_id,
                    account__code__startswith='5'
                ).aggregate(
                    total_debit=Sum('debit'),
                    total_credit=Sum('credit')
                )
                
                total_revenue = (revenue_data['total_credit'] or 0) - (revenue_data['total_debit'] or 0)
                total_expenses = (expense_data['total_debit'] or 0) - (expense_data['total_credit'] or 0)
                net_income = total_revenue - total_expenses
                
                return net_income / 1000000  # تبدیل به میلیون ریال
                
            else:
                return 0
        
        # محاسبه متریک برای تمام دوره‌ها
        values = []
        for period_id in periods:
            value = calculate_metric(company_id, period_id, metric)
            values.append(value)
        
        # تحلیل روند
        if len(values) > 1:
            trend = "صعودی" if values[-1] > values[0] else "نزولی"
            growth = ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0
            average = sum(values) / len(values) if values else 0
            volatility = max(values) - min(values) if values else 0
        else:
            trend = "ثابت"
            growth = 0
            average = values[0] if values else 0
            volatility = 0
        
        # پیش‌بینی ساده
        if len(values) >= 2:
            last_change = values[-1] - values[-2] if len(values) >= 2 else 0
            prediction = "ادامه روند صعودی" if last_change > 0 else "ادامه روند نزولی" if last_change < 0 else "ثبات"
        else:
            prediction = "داده کافی برای پیش‌بینی نیست"
        
        return f"""
        📈 تحلیل روند {metric} - شرکت {company_id}
        
        روند {len(periods)} دوره اخیر:
        {chr(10).join([f'  - دوره {periods[i]}: {values[i]:.2f}' for i in range(len(values))])}
        
        نتیجه‌گیری:
        - روند کلی: {trend}
        - رشد کل: {growth:+.1f}%
        - میانگین: {average:.2f}
        - نوسان: {volatility:.2f}
        
        پیش‌بینی: {prediction}
        
        تاریخ تحلیل: امروز
        """
        
    except Exception as e:
        return f"خطا در تحلیل روند: {str(e)}"
