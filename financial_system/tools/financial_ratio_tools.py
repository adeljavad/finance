from decimal import Decimal
from django.db.models import Q, Sum, F
from django.db.models.functions import Coalesce
from financial_system.models import FinancialPeriod, DocumentItem
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class FinancialRatioInput(BaseModel):
    period_id: int = Field(description="ID دوره مالی مورد نظر")
    previous_period_id: int = Field(description="ID دوره مالی قبلی برای مقایسه")


class CurrentRatioTool(BaseTool):
    name: str = "current_ratio_calculation"
    description: str = "محاسبه نسبت جاری (Current Ratio)"
    args_schema: type = FinancialRatioInput

    def _run(self, period_id: int, previous_period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
            p_prev = FinancialPeriod.objects.get(pk=previous_period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        # دارایی‌های جاری (حساب‌های 11, 12, 13)
        current_assets = DocumentItem.objects.filter(
            document__period=p,
            account__code__startswith=['11', '12', '13']
        ).aggregate(
            total=Coalesce(Sum('debit'), Decimal(0)) - Coalesce(Sum('credit'), Decimal(0))
        )['total'] or Decimal(0)

        # بدهی‌های جاری (حساب‌های 21, 22)
        current_liabilities = DocumentItem.objects.filter(
            document__period=p,
            account__code__startswith=['21', '22']
        ).aggregate(
            total=Coalesce(Sum('credit'), Decimal(0)) - Coalesce(Sum('debit'), Decimal(0))
        )['total'] or Decimal(0)

        current_ratio = current_assets / current_liabilities if current_liabilities > 0 else None

        return {
            "period_title": str(p),
            "current_assets": float(current_assets),
            "current_liabilities": float(current_liabilities),
            "current_ratio": float(current_ratio) if current_ratio else None,
            "interpretation": self._interpret_current_ratio(current_ratio)
        }

    def _interpret_current_ratio(self, ratio):
        if ratio is None:
            return "عدم امکان محاسبه"
        elif ratio > 2:
            return "عالی - نقدینگی بسیار خوب"
        elif ratio > 1.5:
            return "خوب - نقدینگی مناسب"
        elif ratio > 1:
            return "متوسط - نیاز به توجه"
        else:
            return "ضعیف - ریسک نقدینگی بالا"

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class QuickRatioTool(BaseTool):
    name: str = "quick_ratio_calculation"
    description: str = "محاسبه نسبت آنی (Quick Ratio) - بدون موجودی کالا"
    args_schema: type = FinancialRatioInput

    def _run(self, period_id: int, previous_period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
            p_prev = FinancialPeriod.objects.get(pk=previous_period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        # دارایی‌های جاری (حساب‌های 11, 12, 13)
        current_assets = DocumentItem.objects.filter(
            document__period=p,
            account__code__startswith=['11', '12', '13']
        ).aggregate(
            total=Coalesce(Sum('debit'), Decimal(0)) - Coalesce(Sum('credit'), Decimal(0))
        )['total'] or Decimal(0)

        # موجودی کالا (حساب 14)
        inventory = DocumentItem.objects.filter(
            document__period=p,
            account__code__startswith='14'
        ).aggregate(
            total=Coalesce(Sum('debit'), Decimal(0)) - Coalesce(Sum('credit'), Decimal(0))
        )['total'] or Decimal(0)

        # بدهی‌های جاری (حساب‌های 21, 22)
        current_liabilities = DocumentItem.objects.filter(
            document__period=p,
            account__code__startswith=['21', '22']
        ).aggregate(
            total=Coalesce(Sum('credit'), Decimal(0)) - Coalesce(Sum('debit'), Decimal(0))
        )['total'] or Decimal(0)

        quick_assets = current_assets - inventory
        quick_ratio = quick_assets / current_liabilities if current_liabilities > 0 else None

        return {
            "period_title": str(p),
            "current_assets": float(current_assets),
            "inventory": float(inventory),
            "quick_assets": float(quick_assets),
            "current_liabilities": float(current_liabilities),
            "quick_ratio": float(quick_ratio) if quick_ratio else None,
            "interpretation": self._interpret_quick_ratio(quick_ratio)
        }

    def _interpret_quick_ratio(self, ratio):
        if ratio is None:
            return "عدم امکان محاسبه"
        elif ratio > 1:
            return "عالی - توانایی پرداخت بدهی‌های کوتاه مدت"
        elif ratio > 0.5:
            return "خوب - وضعیت نقدینگی قابل قبول"
        else:
            return "ضعیف - ریسک نقدینگی بالا"

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class DebtToEquityTool(BaseTool):
    name: str = "debt_to_equity_calculation"
    description: str = "محاسبه نسبت بدهی به حقوق صاحبان سهام (Debt-to-Equity)"
    args_schema: type = FinancialRatioInput

    def _run(self, period_id: int, previous_period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
            p_prev = FinancialPeriod.objects.get(pk=previous_period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        # کل بدهی‌ها (حساب‌های 2)
        total_liabilities = DocumentItem.objects.filter(
            document__period=p,
            account__code__startswith='2'
        ).aggregate(
            total=Coalesce(Sum('credit'), Decimal(0)) - Coalesce(Sum('debit'), Decimal(0))
        )['total'] or Decimal(0)

        # حقوق صاحبان سهام (حساب‌های 4)
        total_equity = DocumentItem.objects.filter(
            document__period=p,
            account__code__startswith='4'
        ).aggregate(
            total=Coalesce(Sum('credit'), Decimal(0)) - Coalesce(Sum('debit'), Decimal(0))
        )['total'] or Decimal(0)

        debt_to_equity = total_liabilities / total_equity if total_equity > 0 else None

        return {
            "period_title": str(p),
            "total_liabilities": float(total_liabilities),
            "total_equity": float(total_equity),
            "debt_to_equity_ratio": float(debt_to_equity) if debt_to_equity else None,
            "interpretation": self._interpret_debt_to_equity(debt_to_equity)
        }

    def _interpret_debt_to_equity(self, ratio):
        if ratio is None:
            return "عدم امکان محاسبه"
        elif ratio < 0.5:
            return "کم - ساختار مالی محافظه‌کارانه"
        elif ratio < 1:
            return "متوسط - ساختار مالی متعادل"
        elif ratio < 2:
            return "بالا - اهرم مالی بالا"
        else:
            return "بسیار بالا - ریسک مالی شدید"

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class ROATool(BaseTool):
    name: str = "return_on_assets_calculation"
    description: str = "محاسبه نرخ بازده دارایی (Return on Assets - ROA)"
    args_schema: type = FinancialRatioInput

    def _run(self, period_id: int, previous_period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
            p_prev = FinancialPeriod.objects.get(pk=previous_period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        # سود خالص (درآمدها - هزینه‌ها)
        revenue = DocumentItem.objects.filter(
            document__period=p,
            account__group='Revenue'
        ).aggregate(total=Coalesce(Sum('credit'), Decimal(0)))['total']

        expense = DocumentItem.objects.filter(
            document__period=p,
            account__group='Expense'
        ).aggregate(total=Coalesce(Sum('debit'), Decimal(0)))['total']

        net_income = revenue - expense

        # میانگین دارایی‌ها (دوره جاری و قبلی)
        current_assets = DocumentItem.objects.filter(
            document__period=p,
            account__code__startswith='1'
        ).aggregate(
            total=Coalesce(Sum('debit'), Decimal(0)) - Coalesce(Sum('credit'), Decimal(0))
        )['total'] or Decimal(0)

        previous_assets = DocumentItem.objects.filter(
            document__period=p_prev,
            account__code__startswith='1'
        ).aggregate(
            total=Coalesce(Sum('debit'), Decimal(0)) - Coalesce(Sum('credit'), Decimal(0))
        )['total'] or Decimal(0)

        average_assets = (current_assets + previous_assets) / 2
        roa = (net_income / average_assets) * 100 if average_assets > 0 else None

        return {
            "period_title": str(p),
            "net_income": float(net_income),
            "current_assets": float(current_assets),
            "previous_assets": float(previous_assets),
            "average_assets": float(average_assets),
            "roa_percentage": float(roa) if roa else None,
            "interpretation": self._interpret_roa(roa)
        }

    def _interpret_roa(self, roa):
        if roa is None:
            return "عدم امکان محاسبه"
        elif roa > 10:
            return "عالی - بازدهی بسیار خوب"
        elif roa > 5:
            return "خوب - بازدهی مناسب"
        elif roa > 0:
            return "ضعیف - بازدهی پایین"
        else:
            return "منفی - زیان دهی"

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class ROETool(BaseTool):
    name: str = "return_on_equity_calculation"
    description: str = "محاسبه نرخ بازده حقوق صاحبان سهام (Return on Equity - ROE)"
    args_schema: type = FinancialRatioInput

    def _run(self, period_id: int, previous_period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
            p_prev = FinancialPeriod.objects.get(pk=previous_period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        # سود خالص (درآمدها - هزینه‌ها)
        revenue = DocumentItem.objects.filter(
            document__period=p,
            account__group='Revenue'
        ).aggregate(total=Coalesce(Sum('credit'), Decimal(0)))['total']

        expense = DocumentItem.objects.filter(
            document__period=p,
            account__group='Expense'
        ).aggregate(total=Coalesce(Sum('debit'), Decimal(0)))['total']

        net_income = revenue - expense

        # میانگین حقوق صاحبان سهام (دوره جاری و قبلی)
        current_equity = DocumentItem.objects.filter(
            document__period=p,
            account__code__startswith='4'
        ).aggregate(
            total=Coalesce(Sum('credit'), Decimal(0)) - Coalesce(Sum('debit'), Decimal(0))
        )['total'] or Decimal(0)

        previous_equity = DocumentItem.objects.filter(
            document__period=p_prev,
            account__code__startswith='4'
        ).aggregate(
            total=Coalesce(Sum('credit'), Decimal(0)) - Coalesce(Sum('debit'), Decimal(0))
        )['total'] or Decimal(0)

        average_equity = (current_equity + previous_equity) / 2
        roe = (net_income / average_equity) * 100 if average_equity > 0 else None

        return {
            "period_title": str(p),
            "net_income": float(net_income),
            "current_equity": float(current_equity),
            "previous_equity": float(previous_equity),
            "average_equity": float(average_equity),
            "roe_percentage": float(roe) if roe else None,
            "interpretation": self._interpret_roe(roe)
        }

    def _interpret_roe(self, roe):
        if roe is None:
            return "عدم امکان محاسبه"
        elif roe > 15:
            return "عالی - بازدهی سهامداران بسیار خوب"
        elif roe > 8:
            return "خوب - بازدهی مناسب"
        elif roe > 0:
            return "ضعیف - بازدهی پایین"
        else:
            return "منفی - زیان دهی"

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class InventoryTurnoverTool(BaseTool):
    name: str = "inventory_turnover_calculation"
    description: str = "محاسبه گردش موجودی کالا (Inventory Turnover)"
    args_schema: type = FinancialRatioInput

    def _run(self, period_id: int, previous_period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
            p_prev = FinancialPeriod.objects.get(pk=previous_period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        # بهای تمام شده کالای فروش رفته (حساب 61)
        cogs = DocumentItem.objects.filter(
            document__period=p,
            account__code__startswith='61'
        ).aggregate(total=Coalesce(Sum('debit'), Decimal(0)))['total'] or Decimal(0)

        # میانگین موجودی کالا (دوره جاری و قبلی)
        current_inventory = DocumentItem.objects.filter(
            document__period=p,
            account__code__startswith='14'
        ).aggregate(
            total=Coalesce(Sum('debit'), Decimal(0)) - Coalesce(Sum('credit'), Decimal(0))
        )['total'] or Decimal(0)

        previous_inventory = DocumentItem.objects.filter(
            document__period=p_prev,
            account__code__startswith='14'
        ).aggregate(
            total=Coalesce(Sum('debit'), Decimal(0)) - Coalesce(Sum('credit'), Decimal(0))
        )['total'] or Decimal(0)

        average_inventory = (current_inventory + previous_inventory) / 2
        inventory_turnover = cogs / average_inventory if average_inventory > 0 else None

        return {
            "period_title": str(p),
            "cost_of_goods_sold": float(cogs),
            "current_inventory": float(current_inventory),
            "previous_inventory": float(previous_inventory),
            "average_inventory": float(average_inventory),
            "inventory_turnover": float(inventory_turnover) if inventory_turnover else None,
            "interpretation": self._interpret_inventory_turnover(inventory_turnover)
        }

    def _interpret_inventory_turnover(self, turnover):
        if turnover is None:
            return "عدم امکان محاسبه"
        elif turnover > 8:
            return "عالی - مدیریت موجودی بسیار کارآمد"
        elif turnover > 4:
            return "خوب - مدیریت موجودی مناسب"
        elif turnover > 2:
            return "متوسط - نیاز به بهبود"
        else:
            return "ضعیف - ریسک انبارگردانی"

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)
