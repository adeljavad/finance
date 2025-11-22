from decimal import Decimal
from django.db.models import Q, Sum, Count, F
from django.db.models.functions import Coalesce
from financial_system.models import FinancialPeriod, DocumentItem, DocumentHeader, ChartOfAccounts
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class IntegrityCheckInput(BaseModel):
    period_id: int = Field(description="ID دوره مالی مورد نظر")


class BalanceCheckTool(BaseTool):
    name: str = "balance_check"
    description: str = "بررسی تراز بودن هر سند (مجموع بدهکار = بستانکار)"
    args_schema: type = IntegrityCheckInput

    def _run(self, period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        # محاسبه تفاوت بدهکار و بستانکار برای هر سند
        unbalanced_docs = DocumentHeader.objects.filter(
            period=p
        ).annotate(
            diff=F('total_debit') - F('total_credit')
        ).exclude(
            diff=0
        ).values(
            'id',
            'document_number',
            'document_date',
            'total_debit',
            'total_credit',
            'diff'
        ).order_by('-diff')
        
        return {
            "period_title": str(p),
            "unbalanced_documents_count": unbalanced_docs.count(),
            "total_documents": DocumentHeader.objects.filter(period=p).count(),
            "unbalanced_documents": list(unbalanced_docs)
        }

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class EmptyDescriptionTool(BaseTool):
    name: str = "empty_description_detection"
    description: str = "شناسایی آرتیکل‌های بدون شرح"
    args_schema: type = IntegrityCheckInput

    def _run(self, period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        empty_description_items = DocumentItem.objects.filter(
            document__period=p
        ).filter(
            Q(description__isnull=True) | Q(description='')
        ).select_related('document', 'account').values(
            'document__document_number',
            'document__document_date',
            'account__code',
            'account__name',
            'debit',
            'credit'
        )
        
        return {
            "period_title": str(p),
            "empty_description_count": empty_description_items.count(),
            "total_items": DocumentItem.objects.filter(document__period=p).count(),
            "empty_description_items": list(empty_description_items)
        }

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class OrphanHeaderTool(BaseTool):
    name: str = "orphan_header_detection"
    description: str = "شناسایی اسناد بدون آرتیکل"
    args_schema: type = IntegrityCheckInput

    def _run(self, period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        orphan_headers = DocumentHeader.objects.filter(
            period=p,
            items__isnull=True
        ).values(
            'id',
            'document_number',
            'document_date',
            'description',
            'total_debit',
            'total_credit'
        )
        
        return {
            "period_title": str(p),
            "orphan_headers_count": orphan_headers.count(),
            "total_headers": DocumentHeader.objects.filter(period=p).count(),
            "orphan_headers": list(orphan_headers)
        }

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class NegativeAmountTool(BaseTool):
    name: str = "negative_amount_detection"
    description: str = "شناسایی مبالغ منفی در بدهکار / بستانکار"
    args_schema: type = IntegrityCheckInput

    def _run(self, period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        negative_amounts = DocumentItem.objects.filter(
            document__period=p
        ).filter(
            Q(debit__lt=0) | Q(credit__lt=0)
        ).select_related('document', 'account').values(
            'document__document_number',
            'document__document_date',
            'account__code',
            'account__name',
            'debit',
            'credit',
            'description'
        )
        
        return {
            "period_title": str(p),
            "negative_amounts_count": negative_amounts.count(),
            "negative_amounts": list(negative_amounts)
        }

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class PeriodBalanceSumTool(BaseTool):
    name: str = "period_balance_sum"
    description: str = "بررسی مجموع بدهکار = بستانکار در سطح دوره"
    args_schema: type = IntegrityCheckInput

    def _run(self, period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        period_aggregate = DocumentItem.objects.filter(
            document__period=p
        ).aggregate(
            total_debit=Coalesce(Sum('debit'), Decimal(0)),
            total_credit=Coalesce(Sum('credit'), Decimal(0))
        )
        
        total_debit = period_aggregate['total_debit']
        total_credit = period_aggregate['total_credit']
        is_balanced = total_debit == total_credit
        difference = total_debit - total_credit
        
        return {
            "period_title": str(p),
            "total_debit": float(total_debit),
            "total_credit": float(total_credit),
            "is_balanced": is_balanced,
            "difference": float(difference),
            "balance_status": "متوازن" if is_balanced else "نامتوازن"
        }

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class BackDateCheckTool(BaseTool):
    name: str = "back_date_detection"
    description: str = "شناسایی اسناد تاریخ‌گذشته (خارج از محدوده دوره)"
    args_schema: type = IntegrityCheckInput

    def _run(self, period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        back_dated_documents = DocumentHeader.objects.filter(
            period=p
        ).filter(
            Q(document_date__lt=p.start_date) | Q(document_date__gt=p.end_date)
        ).values(
            'id',
            'document_number',
            'document_date',
            'description',
            'total_debit',
            'total_credit',
            'period__start_date',
            'period__end_date'
        )
        
        return {
            "period_title": str(p),
            "back_dated_count": back_dated_documents.count(),
            "period_start": p.start_date.isoformat(),
            "period_end": p.end_date.isoformat(),
            "back_dated_documents": list(back_dated_documents)
        }

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class MissingAccountTool(BaseTool):
    name: str = "missing_account_detection"
    description: str = "شناسایی آرتیکل‌های بدون حساب معین"
    args_schema: type = IntegrityCheckInput

    def _run(self, period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        missing_account_items = DocumentItem.objects.filter(
            document__period=p,
            account__isnull=True
        ).select_related('document').values(
            'document__document_number',
            'document__document_date',
            'debit',
            'credit',
            'description'
        )
        
        return {
            "period_title": str(p),
            "missing_account_count": missing_account_items.count(),
            "missing_account_items": list(missing_account_items)
        }

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class SequenceGapTool(BaseTool):
    name: str = "sequence_gap_detection"
    description: str = "شناسایی فاصله در توالی شماره اسناد"
    args_schema: type = IntegrityCheckInput

    def _run(self, period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        document_numbers = list(DocumentHeader.objects.filter(
            period=p
        ).order_by('document_number').values_list('document_number', flat=True))
        
        if not document_numbers:
            return {
                "period_title": str(p),
                "missing_sequences": [],
                "total_documents": 0,
                "sequence_status": "بدون سند"
            }
        
        min_num = min(document_numbers)
        max_num = max(document_numbers)
        missing_sequences = sorted(set(range(min_num, max_num + 1)) - set(document_numbers))
        
        return {
            "period_title": str(p),
            "min_document_number": min_num,
            "max_document_number": max_num,
            "total_documents": len(document_numbers),
            "missing_sequences_count": len(missing_sequences),
            "missing_sequences": missing_sequences,
            "sequence_status": "پیوسته" if len(missing_sequences) == 0 else "ناپیوسته"
        }

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)
