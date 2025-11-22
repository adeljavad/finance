from decimal import Decimal
from datetime import timedelta
from django.db.models import Q, Sum, Count, Window, F
from django.db.models.functions import Lag, TruncDate, Coalesce
from django.utils import timezone
from difflib import SequenceMatcher
from financial_system.models import FinancialPeriod, DocumentItem, DocumentHeader
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import hashlib
import json


class FraudDetectionInput(BaseModel):
    period_id: int = Field(description="ID دوره مالی مورد نظر")


class ThresholdHitTool(BaseTool):
    name: str = "threshold_hit_detection"
    description: str = "شناسایی اسناد با مبالغ برابر یا بیشتر از سقف مجاز انتقال وجه"
    args_schema: type = FraudDetectionInput

    def _run(self, period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        # سقف مجاز انتقال وجه - مثال: 50,000,000 ریال
        LIMIT = Decimal('50000000')
        
        threshold_hits = DocumentItem.objects.filter(
            document__period=p
        ).filter(
            Q(debit__gte=LIMIT) | Q(credit__gte=LIMIT)
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
            "threshold_limit": float(LIMIT),
            "threshold_hits_count": threshold_hits.count(),
            "threshold_hits": list(threshold_hits)
        }

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class RoundNumberBiasTool(BaseTool):
    name: str = "round_number_bias_detection"
    description: str = "شناسایی اسناد با مبالغی که رقم آخرشان صفر است (Round-Number Bias)"
    args_schema: type = FraudDetectionInput

    def _run(self, period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        # شناسایی مبالغی که رقم آخرشان صفر است
        round_number_items = []
        
        items = DocumentItem.objects.filter(
            document__period=p
        ).select_related('document', 'account')
        
        for item in items:
            # بررسی بدهکار
            if item.debit > 0 and item.debit % 10 == 0:
                round_number_items.append({
                    'document_number': item.document.document_number,
                    'document_date': item.document.document_date,
                    'account_code': item.account.code,
                    'account_name': item.account.name,
                    'amount': float(item.debit),
                    'type': 'debit',
                    'description': item.description
                })
            
            # بررسی بستانکار
            if item.credit > 0 and item.credit % 10 == 0:
                round_number_items.append({
                    'document_number': item.document.document_number,
                    'document_date': item.document.document_date,
                    'account_code': item.account.code,
                    'account_name': item.account.name,
                    'amount': float(item.credit),
                    'type': 'credit',
                    'description': item.description
                })
        
        return {
            "period_title": str(p),
            "round_number_items_count": len(round_number_items),
            "round_number_items": round_number_items
        }

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class EndOfPeriodRushTool(BaseTool):
    name: str = "end_of_period_rush_detection"
    description: str = "شناسایی اسنادی که در روزهای پایانی دوره ثبت شده‌اند (End-of-Period Rush)"
    args_schema: type = FraudDetectionInput

    def _run(self, period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        # شناسایی اسناد در هفته پایانی دوره
        last_week_start = p.end_date - timedelta(days=7)
        
        eop_documents = DocumentHeader.objects.filter(
            period=p,
            document_date__gte=last_week_start,
            document_date__lte=p.end_date
        ).select_related('period').annotate(
            total_amount=F('total_debit') + F('total_credit')
        ).values(
            'document_number',
            'document_date',
            'description',
            'total_debit',
            'total_credit',
            'total_amount'
        ).order_by('-document_date')
        
        # محاسبه آمار
        total_eop_amount = sum([doc['total_amount'] for doc in eop_documents])
        total_period_amount = DocumentHeader.objects.filter(
            period=p
        ).aggregate(
            total=Sum(F('total_debit') + F('total_credit'))
        )['total'] or 0
        
        eop_percentage = (total_eop_amount / total_period_amount * 100) if total_period_amount > 0 else 0
        
        return {
            "period_title": str(p),
            "last_week_start": last_week_start.isoformat(),
            "period_end": p.end_date.isoformat(),
            "eop_documents_count": eop_documents.count(),
            "eop_documents_percentage": round(eop_percentage, 2),
            "total_eop_amount": float(total_eop_amount),
            "total_period_amount": float(total_period_amount),
            "eop_documents": list(eop_documents)
        }

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class DuplicateDocumentTool(BaseTool):
    name: str = "duplicate_document_detection"
    description: str = "شناسایی اسناد تکراری در یک دوره مالی"
    args_schema: type = FraudDetectionInput

    def _run(self, period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        # شناسایی شماره اسناد تکراری
        duplicates = DocumentHeader.objects.filter(
            period=p
        ).values('document_number').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        duplicate_details = []
        for dup in duplicates:
            documents = DocumentHeader.objects.filter(
                period=p,
                document_number=dup['document_number']
            ).values(
                'id',
                'document_number',
                'document_date',
                'description',
                'total_debit',
                'total_credit'
            )
            duplicate_details.append({
                'document_number': dup['document_number'],
                'count': dup['count'],
                'documents': list(documents)
            })
        
        return {
            "period_title": str(p),
            "duplicate_groups_count": len(duplicate_details),
            "duplicate_documents_count": sum([group['count'] for group in duplicate_details]),
            "duplicate_details": duplicate_details
        }

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class DescriptionSimilarityTool(BaseTool):
    name: str = "description_similarity_detection"
    description: str = "شناسایی اسناد با توصیف‌های مشابه (تشابه بیش از 90%)"
    args_schema: type = FraudDetectionInput

    def _run(self, period_id: int) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        headers = DocumentHeader.objects.filter(
            period=p
        ).exclude(
            Q(description__isnull=True) | Q(description='')
        ).values('id', 'document_number', 'description')
        
        similar_pairs = []
        processed = set()
        
        for i, a in enumerate(headers):
            for b in headers[i+1:]:
                if a['id'] in processed or b['id'] in processed:
                    continue
                    
                if a['description'] and b['description']:
                    score = SequenceMatcher(None, a['description'], b['description']).ratio()
                    if score > 0.9:
                        similar_pairs.append({
                            'doc1_id': a['id'],
                            'doc1_number': a['document_number'],
                            'doc1_description': a['description'],
                            'doc2_id': b['id'],
                            'doc2_number': b['document_number'],
                            'doc2_description': b['description'],
                            'similarity_score': round(score, 4)
                        })
                        processed.add(a['id'])
                        processed.add(b['id'])
        
        return {
            "period_title": str(p),
            "similar_pairs_count": len(similar_pairs),
            "similar_pairs": similar_pairs
        }

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)
