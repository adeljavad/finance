from decimal import Decimal
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from financial_system.models import FinancialPeriod, DocumentItem, ChartOfAccounts
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class CashFlowInput(BaseModel):
    period_id: int = Field(description="ID دوره مالی مورد نظر")


class CashFlowSimulationTool(BaseTool):
    name: str = "cash_flow_simulation"
    description: str = (
        "شبیه‌سازی جریان وجوه نقد (روش غیرمستقیم) برای یک دوره مالی خاص. "
        "خروجی شامل سه مقدار Operating، Investing و Financing است."
    )
    args_schema: type = CashFlowInput

    def _run(self, period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        # 1) Net Income ≈ Revenue – Expense
        revenue_query = DocumentItem.objects.filter(
            document__period=p,
            account__group='Revenue'
        ).aggregate(s=Coalesce(Sum('credit'), Decimal(0)))
        revenue = revenue_query['s']

        expense_query = DocumentItem.objects.filter(
            document__period=p,
            account__group='Expense'
        ).aggregate(s=Coalesce(Sum('debit'), Decimal(0)))
        expense = expense_query['s']

        net_income = revenue - expense

        # 2) Depreciation / Amortisation (add back)
        dep_query = DocumentItem.objects.filter(
            document__period=p,
            account__code__startswith='69'  # استهلاک
        ).aggregate(s=Coalesce(Sum('debit'), Decimal(0)))
        dep = dep_query['s']

        # 3) ΔWorking-Capital
        # Use Q objects for multiple account code prefixes
        wc_q = Q(account__code__startswith='11') | Q(account__code__startswith='12') | \
               Q(account__code__startswith='13') | Q(account__code__startswith='14')
        wc_dr_query = DocumentItem.objects.filter(
            document__period=p
        ).filter(wc_q).aggregate(s=Coalesce(Sum('debit'), Decimal(0)))
        wc_dr = wc_dr_query['s']

        wc_cr_query = DocumentItem.objects.filter(
            document__period=p
        ).filter(wc_q).aggregate(s=Coalesce(Sum('credit'), Decimal(0)))
        wc_cr = wc_cr_query['s']

        delta_wc = wc_dr - wc_cr

        operating = net_income + dep - delta_wc

        # 4) Investing
        inv_q = Q(account__code__startswith='31') | Q(account__code__startswith='32') | \
                Q(account__code__startswith='33')
        inv_dr_query = DocumentItem.objects.filter(
            document__period=p
        ).filter(inv_q).aggregate(s=Coalesce(Sum('debit'), Decimal(0)))
        inv_dr = inv_dr_query['s']

        inv_cr_query = DocumentItem.objects.filter(
            document__period=p
        ).filter(inv_q).aggregate(s=Coalesce(Sum('credit'), Decimal(0)))
        inv_cr = inv_cr_query['s']

        investing = inv_dr - inv_cr

        # 5) Financing
        fin_q = Q(account__code__startswith='41') | Q(account__code__startswith='42') | \
                Q(account__code__startswith='43') | Q(account__code__startswith='44')
        fin_cr_query = DocumentItem.objects.filter(
            document__period=p
        ).filter(fin_q).aggregate(s=Coalesce(Sum('credit'), Decimal(0)))
        fin_cr = fin_cr_query['s']

        fin_dr_query = DocumentItem.objects.filter(
            document__period=p
        ).filter(fin_q).aggregate(s=Coalesce(Sum('debit'), Decimal(0)))
        fin_dr = fin_dr_query['s']

        financing = fin_cr - fin_dr

        # ذخیره (اختیاری) - commenting out for now as model might not exist
        # from .models import CashFlowResult
        # CashFlowResult.objects.update_or_create(
        #     period=p,
        #     defaults={'operating': operating,
        #               'investing': investing,
        #               'financing': financing}
        # )

        return {
            "period_title": str(p),
            "operating": float(operating),
            "investing": float(investing),
            "financing": float(financing)
        }

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)
