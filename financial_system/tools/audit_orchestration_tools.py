from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Q, Sum, Count, F
from django.db.models.functions import Coalesce
from financial_system.models import FinancialPeriod, DocumentItem, DocumentHeader
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
import asyncio
from typing import List, Dict, Any


class ComprehensiveAuditInput(BaseModel):
    period_id: int = Field(description="ID دوره مالی مورد نظر")
    previous_period_id: int = Field(description="ID دوره مالی قبلی برای مقایسه")
    audit_types: List[str] = Field(
        description="انواع حسابرسی مورد نیاز",
        default=["integrity", "fraud", "ratios", "cash_flow"]
    )


class ComprehensiveAuditTool(BaseTool):
    name: str = "comprehensive_audit"
    description: str = "حسابرسی جامع شامل تمامی تست‌های یکپارچه"
    args_schema: type = ComprehensiveAuditInput

    def _run(self, period_id: int, previous_period_id: int, audit_types: List[str]) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
            p_prev = FinancialPeriod.objects.get(pk=previous_period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        audit_results = {
            "period_title": str(p),
            "previous_period_title": str(p_prev),
            "audit_timestamp": datetime.now().isoformat(),
            "audit_types": audit_types,
            "results": {}
        }

        # اجرای تست‌های یکپارچگی
        if "integrity" in audit_types:
            audit_results["results"]["integrity"] = self._run_integrity_audit(p)

        # اجرای تست‌های تقلب
        if "fraud" in audit_types:
            audit_results["results"]["fraud"] = self._run_fraud_audit(p)

        # اجرای تست‌های مالی
        if "ratios" in audit_types:
            audit_results["results"]["ratios"] = self._run_financial_ratios_audit(p, p_prev)

        # اجرای تست‌های جریان وجوه نقد
        if "cash_flow" in audit_types:
            audit_results["results"]["cash_flow"] = self._run_cash_flow_audit(p)

        # محاسبه امتیاز کلی حسابرسی
        audit_results["overall_score"] = self._calculate_audit_score(audit_results["results"])
        audit_results["risk_level"] = self._determine_risk_level(audit_results["overall_score"])

        return audit_results

    def _run_integrity_audit(self, period) -> Dict[str, Any]:
        """اجرای تست‌های یکپارچگی"""
        integrity_results = {}

        # 1. بررسی تراز بودن اسناد
        unbalanced_docs = DocumentHeader.objects.filter(
            period=period
        ).annotate(
            diff=F('total_debit') - F('total_credit')
        ).exclude(diff=0).count()
        integrity_results["balance_check"] = {
            "unbalanced_documents": unbalanced_docs,
            "status": "PASS" if unbalanced_docs == 0 else "FAIL",
            "severity": "HIGH" if unbalanced_docs > 0 else "LOW"
        }

        # 2. آرتیکل‌های بدون شرح
        empty_desc_count = DocumentItem.objects.filter(
            document__period=period
        ).filter(
            Q(description__isnull=True) | Q(description='')
        ).count()
        integrity_results["empty_description"] = {
            "count": empty_desc_count,
            "status": "PASS" if empty_desc_count == 0 else "WARNING",
            "severity": "MEDIUM" if empty_desc_count > 0 else "LOW"
        }

        # 3. اسناد بدون آرتیکل
        orphan_headers = DocumentHeader.objects.filter(
            period=period,
            items__isnull=True
        ).count()
        integrity_results["orphan_headers"] = {
            "count": orphan_headers,
            "status": "PASS" if orphan_headers == 0 else "FAIL",
            "severity": "HIGH" if orphan_headers > 0 else "LOW"
        }

        # 4. مبالغ منفی
        negative_amounts = DocumentItem.objects.filter(
            document__period=period
        ).filter(
            Q(debit__lt=0) | Q(credit__lt=0)
        ).count()
        integrity_results["negative_amounts"] = {
            "count": negative_amounts,
            "status": "PASS" if negative_amounts == 0 else "FAIL",
            "severity": "HIGH" if negative_amounts > 0 else "LOW"
        }

        # 5. توالی شماره اسناد
        document_numbers = list(DocumentHeader.objects.filter(
            period=period
        ).order_by('document_number').values_list('document_number', flat=True))
        
        if document_numbers:
            min_num = min(document_numbers)
            max_num = max(document_numbers)
            missing_sequences = len(set(range(min_num, max_num + 1)) - set(document_numbers))
        else:
            missing_sequences = 0

        integrity_results["sequence_gap"] = {
            "missing_sequences": missing_sequences,
            "status": "PASS" if missing_sequences == 0 else "WARNING",
            "severity": "MEDIUM" if missing_sequences > 0 else "LOW"
        }

        return integrity_results

    def _run_fraud_audit(self, period) -> Dict[str, Any]:
        """اجرای تست‌های تقلب"""
        fraud_results = {}

        # 1. شناسایی مبالغ بالای سقف مجاز
        LIMIT = Decimal('50000000')
        threshold_hits = DocumentItem.objects.filter(
            document__period=period
        ).filter(
            Q(debit__gte=LIMIT) | Q(credit__gte=LIMIT)
        ).count()
        fraud_results["threshold_hits"] = {
            "count": threshold_hits,
            "status": "PASS" if threshold_hits == 0 else "FAIL",
            "severity": "HIGH" if threshold_hits > 0 else "LOW"
        }

        # 2. شناسایی مبالغ گرد
        round_number_count = 0
        items = DocumentItem.objects.filter(document__period=period)
        for item in items:
            if (item.debit > 0 and item.debit % 10 == 0) or (item.credit > 0 and item.credit % 10 == 0):
                round_number_count += 1

        fraud_results["round_number_bias"] = {
            "count": round_number_count,
            "status": "PASS" if round_number_count == 0 else "WARNING",
            "severity": "MEDIUM" if round_number_count > 10 else "LOW"
        }

        # 3. شناسایی اسناد پایانی دوره
        last_week_start = period.end_date - timedelta(days=7)
        eop_documents = DocumentHeader.objects.filter(
            period=period,
            document_date__gte=last_week_start,
            document_date__lte=period.end_date
        ).count()
        total_documents = DocumentHeader.objects.filter(period=period).count()
        eop_percentage = (eop_documents / total_documents * 100) if total_documents > 0 else 0

        fraud_results["end_of_period_rush"] = {
            "count": eop_documents,
            "percentage": round(eop_percentage, 2),
            "status": "PASS" if eop_percentage < 30 else "WARNING",
            "severity": "HIGH" if eop_percentage > 50 else "MEDIUM" if eop_percentage > 30 else "LOW"
        }

        # 4. شناسایی اسناد تکراری
        duplicates = DocumentHeader.objects.filter(
            period=period
        ).values('document_number').annotate(
            count=Count('id')
        ).filter(count__gt=1).count()
        fraud_results["duplicate_documents"] = {
            "count": duplicates,
            "status": "PASS" if duplicates == 0 else "FAIL",
            "severity": "HIGH" if duplicates > 0 else "LOW"
        }

        return fraud_results

    def _run_financial_ratios_audit(self, period, previous_period) -> Dict[str, Any]:
        """اجرای تست‌های نسبت‌های مالی"""
        ratio_results = {}

        # محاسبه نسبت‌های مالی
        try:
            # نسبت جاری
            current_assets = DocumentItem.objects.filter(
                document__period=period,
                account__code__startswith=['11', '12', '13']
            ).aggregate(
                total=Coalesce(Sum('debit'), Decimal(0)) - Coalesce(Sum('credit'), Decimal(0))
            )['total'] or Decimal(0)

            current_liabilities = DocumentItem.objects.filter(
                document__period=period,
                account__code__startswith=['21', '22']
            ).aggregate(
                total=Coalesce(Sum('credit'), Decimal(0)) - Coalesce(Sum('debit'), Decimal(0))
            )['total'] or Decimal(0)

            current_ratio = current_assets / current_liabilities if current_liabilities > 0 else None
            ratio_results["current_ratio"] = {
                "value": float(current_ratio) if current_ratio else None,
                "status": "PASS" if current_ratio and current_ratio > 1.5 else "WARNING",
                "severity": "HIGH" if current_ratio and current_ratio < 1 else "MEDIUM" if current_ratio and current_ratio < 1.5 else "LOW"
            }

            # نسبت بدهی به حقوق صاحبان سهام
            total_liabilities = DocumentItem.objects.filter(
                document__period=period,
                account__code__startswith='2'
            ).aggregate(
                total=Coalesce(Sum('credit'), Decimal(0)) - Coalesce(Sum('debit'), Decimal(0))
            )['total'] or Decimal(0)

            total_equity = DocumentItem.objects.filter(
                document__period=period,
                account__code__startswith='4'
            ).aggregate(
                total=Coalesce(Sum('credit'), Decimal(0)) - Coalesce(Sum('debit'), Decimal(0))
            )['total'] or Decimal(0)

            debt_to_equity = total_liabilities / total_equity if total_equity > 0 else None
            ratio_results["debt_to_equity"] = {
                "value": float(debt_to_equity) if debt_to_equity else None,
                "status": "PASS" if debt_to_equity and debt_to_equity < 1 else "WARNING",
                "severity": "HIGH" if debt_to_equity and debt_to_equity > 2 else "MEDIUM" if debt_to_equity and debt_to_equity > 1 else "LOW"
            }

            # ROA
            revenue = DocumentItem.objects.filter(
                document__period=period,
                account__group='Revenue'
            ).aggregate(total=Coalesce(Sum('credit'), Decimal(0)))['total']

            expense = DocumentItem.objects.filter(
                document__period=period,
                account__group='Expense'
            ).aggregate(total=Coalesce(Sum('debit'), Decimal(0)))['total']

            net_income = revenue - expense

            current_assets_total = DocumentItem.objects.filter(
                document__period=period,
                account__code__startswith='1'
            ).aggregate(
                total=Coalesce(Sum('debit'), Decimal(0)) - Coalesce(Sum('credit'), Decimal(0))
            )['total'] or Decimal(0)

            previous_assets = DocumentItem.objects.filter(
                document__period=previous_period,
                account__code__startswith='1'
            ).aggregate(
                total=Coalesce(Sum('debit'), Decimal(0)) - Coalesce(Sum('credit'), Decimal(0))
            )['total'] or Decimal(0)

            average_assets = (current_assets_total + previous_assets) / 2
            roa = (net_income / average_assets) * 100 if average_assets > 0 else None

            ratio_results["roa"] = {
                "value": float(roa) if roa else None,
                "status": "PASS" if roa and roa > 5 else "WARNING",
                "severity": "HIGH" if roa and roa < 0 else "MEDIUM" if roa and roa < 5 else "LOW"
            }

        except Exception as e:
            ratio_results["error"] = str(e)

        return ratio_results

    def _run_cash_flow_audit(self, period) -> Dict[str, Any]:
        """اجرای تست‌های جریان وجوه نقد"""
        cash_flow_results = {}

        try:
            # شبیه‌سازی جریان وجوه نقد
            # درآمدها و هزینه‌ها
            revenue = DocumentItem.objects.filter(
                document__period=period,
                account__group='Revenue'
            ).aggregate(total=Coalesce(Sum('credit'), Decimal(0)))['total']

            expense = DocumentItem.objects.filter(
                document__period=period,
                account__group='Expense'
            ).aggregate(total=Coalesce(Sum('debit'), Decimal(0)))['total']

            net_income = revenue - expense

            # استهلاک
            dep = DocumentItem.objects.filter(
                document__period=period,
                account__code__startswith='69'
            ).aggregate(total=Coalesce(Sum('debit'), Decimal(0)))['total'] or Decimal(0)

            # تغییرات سرمایه در گردش
            wc_dr = DocumentItem.objects.filter(
                document__period=period,
                account__code__startswith=['11', '12', '13', '14']
            ).aggregate(total=Coalesce(Sum('debit'), Decimal(0)))['total'] or Decimal(0)

            wc_cr = DocumentItem.objects.filter(
                document__period=period,
                account__code__startswith=['11', '12', '13', '14']
            ).aggregate(total=Coalesce(Sum('credit'), Decimal(0)))['total'] or Decimal(0)

            delta_wc = wc_dr - wc_cr
            operating = net_income + dep - delta_wc

            cash_flow_results["operating_cash_flow"] = {
                "value": float(operating),
                "status": "PASS" if operating > 0 else "WARNING",
                "severity": "HIGH" if operating < 0 else "LOW"
            }

        except Exception as e:
            cash_flow_results["error"] = str(e)

        return cash_flow_results

    def _calculate_audit_score(self, results: Dict[str, Any]) -> float:
        """محاسبه امتیاز کلی حسابرسی"""
        total_tests = 0
        passed_tests = 0

        for category, category_results in results.items():
            for test_name, test_result in category_results.items():
                if test_name != "error":
                    total_tests += 1
                    if test_result.get("status") == "PASS":
                        passed_tests += 1

        return (passed_tests / total_tests * 100) if total_tests > 0 else 0

    def _determine_risk_level(self, score: float) -> str:
        """تعیین سطح ریسک بر اساس امتیاز"""
        if score >= 90:
            return "کم"
        elif score >= 70:
            return "متوسط"
        elif score >= 50:
            return "بالا"
        else:
            return "بسیار بالا"

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)


class AuditReportGeneratorTool(BaseTool):
    name: str = "audit_report_generator"
    description: str = "تولید گزارش حسابرسی جامع با قالب‌بندی پیشرفته"
    args_schema: type = ComprehensiveAuditInput

    def _run(self, period_id: int, previous_period_id: int, audit_types: List[str]) -> dict:
        try:
            p = FinancialPeriod.objects.get(pk=period_id)
            p_prev = FinancialPeriod.objects.get(pk=previous_period_id)
        except FinancialPeriod.DoesNotExist:
            return {"error": "دوره مالی یافت نشد"}

        # اجرای حسابرسی جامع
        comprehensive_audit = ComprehensiveAuditTool()
        audit_results = comprehensive_audit._run(period_id, previous_period_id, audit_types)

        # تولید گزارش
        report = self._generate_detailed_report(audit_results, p, p_prev)
        return report

    def _generate_detailed_report(self, audit_results: Dict[str, Any], period, previous_period) -> Dict[str, Any]:
        """تولید گزارش تفصیلی"""
        
        report = {
            "report_metadata": {
                "title": f"گزارش حسابرسی جامع - دوره {period}",
                "generated_at": datetime.now().isoformat(),
                "period": str(period),
                "previous_period": str(previous_period),
                "auditor": "سیستم هوشمند حسابرسی"
            },
            "executive_summary": self._generate_executive_summary(audit_results),
            "detailed_findings": self._generate_detailed_findings(audit_results),
            "recommendations": self._generate_recommendations(audit_results),
            "risk_assessment": self._generate_risk_assessment(audit_results)
        }

        return report

    def _generate_executive_summary(self, audit_results: Dict[str, Any]) -> Dict[str, Any]:
        """تولید خلاصه مدیریتی"""
        overall_score = audit_results.get("overall_score", 0)
        risk_level = audit_results.get("risk_level", "نامشخص")

        summary = {
            "overall_score": overall_score,
            "risk_level": risk_level,
            "audit_scope": audit_results.get("audit_types", []),
            "key_findings": []
        }

        # یافته‌های کلیدی
        for category, category_results in audit_results.get("results", {}).items():
            for test_name, test_result in category_results.items():
                if test_name != "error" and test_result.get("status") in ["FAIL", "WARNING"]:
                    summary["key_findings"].append({
                        "category": category,
                        "test": test_name,
                        "status": test_result.get("status"),
                        "severity": test_result.get("severity"),
                        "details": test_result
                    })

        return summary

    def _generate_detailed_findings(self, audit_results: Dict[str, Any]) -> Dict[str, Any]:
        """تولید یافته‌های تفصیلی"""
        findings = {}

        for category, category_results in audit_results.get("results", {}).items():
            findings[category] = {}
            for test_name, test_result in category_results.items():
                if test_name != "error":
                    findings[category][test_name] = {
                        "status": test_result.get("status"),
                        "severity": test_result.get("severity"),
                        "details": test_result,
                        "explanation": self._get_test_explanation(test_name)
                    }

        return findings

    def _generate_recommendations(self, audit_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """تولید توصیه‌ها"""
        recommendations = []

        # تجزیه و تحلیل یافته‌ها و تولید توصیه‌ها
        results = audit_results.get("results", {})
        
        # توصیه‌های یکپارچگی
        if "integrity" in results:
            integrity_results = results["integrity"]
            
            if integrity_results.get("balance_check", {}).get("status") == "FAIL":
                recommendations.append({
                    "category": "یکپارچگی",
                    "priority": "بالا",
                    "recommendation": "بررسی و اصلاح اسناد نامتوازن",
                    "action": "اصلاح تفاوت بدهکار و بستانکار در اسناد نامتوازن"
                })

            if integrity_results.get("orphan_headers", {}).get("status") == "FAIL":
                recommendations.append({
                    "category": "یکپارچگی",
                    "priority": "بالا",
                    "recommendation": "حذف یا تکمیل اسناد بدون آرتیکل",
                    "action": "بررسی اسناد بدون آرتیکل و تکمیل یا حذف آنها"
                })

        # توصیه‌های تقلب
        if "fraud" in results:
            fraud_results = results["fraud"]
            
            if fraud_results.get("threshold_hits", {}).get("status") == "FAIL":
                recommendations.append({
                    "category": "تقلب",
                    "priority": "بالا",
                    "recommendation": "بررسی مبالغ بالای سقف مجاز",
                    "action": "بررسی و توجیه مبالغ بالای سقف مجاز انتقال وجه"
                })

            if fraud_results.get("duplicate_documents", {}).get("status") == "FAIL":
                recommendations.append({
                    "category": "تقلب",
                    "priority": "بالا",
                    "recommendation": "بررسی اسناد تکراری",
                    "action": "شناسایی و اصلاح اسناد با شماره تکراری"
                })

        # توصیه‌های مالی
        if "ratios" in results:
            ratio_results = results["ratios"]
            
            if ratio_results.get("current_ratio", {}).get("status") == "WARNING":
                recommendations.append({
                    "category": "مالی",
                    "priority": "متوسط",
                    "recommendation": "بهبود نسبت جاری",
                    "action": "مدیریت بدهی‌های جاری و دارایی‌های جاری"
                })

            if ratio_results.get("debt_to_equity", {}).get("status") == "WARNING":
                recommendations.append({
                    "category": "مالی",
                    "priority": "متوسط",
                    "recommendation": "بهبود ساختار مالی",
                    "action": "کاهش اهرم مالی و بهبود نسبت بدهی به حقوق صاحبان سهام"
                })

        return recommendations

    def _generate_risk_assessment(self, audit_results: Dict[str, Any]) -> Dict[str, Any]:
        """تولید ارزیابی ریسک"""
        risk_assessment = {
            "overall_risk_level": audit_results.get("risk_level", "نامشخص"),
            "overall_score": audit_results.get("overall_score", 0),
            "risk_breakdown": {}
        }

        # تجزیه ریسک بر اساس دسته‌بندی
        results = audit_results.get("results", {})
        for category, category_results in results.items():
            category_risks = []
            for test_name, test_result in category_results.items():
                if test_name != "error":
                    category_risks.append({
                        "test": test_name,
                        "severity": test_result.get("severity"),
                        "status": test_result.get("status")
                    })
            risk_assessment["risk_breakdown"][category] = category_risks

        return risk_assessment

    def _get_test_explanation(self, test_name: str) -> str:
        """توضیح برای هر تست"""
        explanations = {
            "balance_check": "بررسی تراز بودن هر سند (مجموع بدهکار = بستانکار)",
            "empty_description": "شناسایی آرتیکل‌های بدون شرح",
            "orphan_headers": "شناسایی اسناد بدون آرتیکل",
            "negative_amounts": "شناسایی مبالغ منفی در بدهکار/بستانکار",
            "sequence_gap": "شناسایی فاصله در توالی شماره اسناد",
            "threshold_hits": "شناسایی مبالغ بالای سقف مجاز انتقال وجه",
            "round_number_bias": "شناسایی مبالغ گرد (ریسک تقلب)",
            "end_of_period_rush": "شناسایی اسناد ثبت شده در روزهای پایانی دوره",
            "duplicate_documents": "شناسایی اسناد تکراری",
            "current_ratio": "محاسبه نسبت جاری (نقدینگی کوتاه مدت)",
            "debt_to_equity": "محاسبه نسبت بدهی به حقوق صاحبان سهام",
            "roa": "محاسبه بازده دارایی‌ها",
            "operating_cash_flow": "محاسبه جریان وجوه نقد عملیاتی"
        }
        return explanations.get(test_name, "توضیح موجود نیست")

    async def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)
