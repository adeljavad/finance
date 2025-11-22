# data_importer/reports/validation_report.py
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML
import pandas as pd
from typing import Dict, List, Any
import json

class ValidationReportGenerator:
    def __init__(self, company_name: str, period_name: str):
        self.company_name = company_name
        self.period_name = period_name
        self.report_date = timezone.now()
    
    def generate_comprehensive_report(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """تولید گزارش جامع اعتبارسنجی"""
        report_data = {
            'metadata': self._generate_metadata(),
            'executive_summary': self._generate_executive_summary(validation_results),
            'detailed_analysis': self._generate_detailed_analysis(validation_results),
            'recommendations': self._generate_recommendations(validation_results),
            'statistics': self._generate_statistics(validation_results)
        }
        
        return {
            'report_data': report_data,
            'formats': {
                'html': self._generate_html_report(report_data),
                'pdf': self._generate_pdf_report(report_data),
                'excel': self._generate_excel_report(validation_results)
            }
        }
    
    def _generate_metadata(self) -> Dict[str, Any]:
        """تولید متادیتای گزارش"""
        return {
            'company_name': self.company_name,
            'period_name': self.period_name,
            'report_date': self.report_date.strftime('%Y/%m/%d %H:%M'),
            'report_id': f"VR_{self.report_date.strftime('%Y%m%d_%H%M%S')}",
            'report_type': 'گزارش اعتبارسنجی داده‌های مالی'
        }
    
    def _generate_executive_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """تولید خلاصه مدیریتی"""
        total_issues = 0
        critical_issues = 0
        warning_issues = 0
        
        # محاسبه آمار خطاها
        for validator_type, issues in results.items():
            if isinstance(issues, dict) and 'issues' in issues:
                for severity, issue_list in issues.get('issues', {}).items():
                    total_issues += len(issue_list)
                    if severity in ['critical', 'CRITICAL']:
                        critical_issues += len(issue_list)
                    elif severity in ['warning', 'WARNING', 'MEDIUM']:
                        warning_issues += len(issue_list)
        
        return {
            'total_documents_processed': results.get('document_count', 0),
            'total_issues_found': total_issues,
            'critical_issues': critical_issues,
            'warning_issues': warning_issues,
            'data_quality_score': self._calculate_quality_score(total_issues, results.get('document_count', 1)),
            'import_recommendation': 'توصیه می‌شود' if critical_issues == 0 else 'توصیه نمی‌شود',
            'summary_message': self._generate_summary_message(total_issues, critical_issues)
        }
    
    def _generate_detailed_analysis(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """تولید تحلیل جزئی"""
        detailed_sections = []
        
        validators_mapping = {
            'duplicate': 'بررسی اسناد تکراری',
            'sequence': 'بررسی توالی اسناد',
            'coding': 'بررسی کدینگ',
            'balance': 'بررسی توازن اسناد'
        }
        
        for validator_key, validator_name in validators_mapping.items():
            if validator_key in results:
                section = {
                    'title': validator_name,
                    'issues': self._extract_issues_for_section(results[validator_key]),
                    'statistics': self._extract_statistics_for_section(results[validator_key]),
                    'severity': self._calculate_section_severity(results[validator_key])
                }
                detailed_sections.append(section)
        
        return detailed_sections
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """تولید توصیه‌های عملی"""
        recommendations = []
        
        # توصیه‌های مبتنی بر خطاهای تکراری
        if 'duplicate' in results and results['duplicate'].get('exact_duplicates'):
            recommendations.append({
                'type': 'CRITICAL',
                'title': 'حذف اسناد تکراری',
                'description': 'اسناد کاملاً تکراری شناسایی شدند. توصیه می‌شود قبل از وارد کردن، این اسناد بررسی شوند.',
                'action': 'REVIEW_AND_DELETE',
                'affected_count': len(results['duplicate']['exact_duplicates'])
            })
        
        # توصیه‌های مبتنی بر کدینگ مفقود
        if 'coding' in results and results['coding'].get('missing_codes'):
            recommendations.append({
                'type': 'HIGH',
                'title': 'ایجاد کدینگ‌های جدید',
                'description': 'کدینگ‌های استفاده شده در اسناد در سیستم وجود ندارند.',
                'action': 'AUTO_CREATE_CODES',
                'affected_count': len(results['coding']['missing_codes'])
            })
        
        # توصیه‌های مبتنی بر شکاف توالی
        if 'sequence' in results and results['sequence'].get('gaps'):
            total_gaps = sum(gap['missing_count'] for gap in results['sequence']['gaps'])
            recommendations.append({
                'type': 'MEDIUM',
                'title': 'بررسی شکاف توالی اسناد',
                'description': f'شکاف در توالی شماره اسناد مشاهده شد. {total_gaps} سند احتمالی مفقود است.',
                'action': 'INVESTIGATE_GAPS',
                'affected_count': total_gaps
            })
        
        # توصیه کلی
        if not any(recommendations):
            recommendations.append({
                'type': 'SUCCESS',
                'title': 'داده‌های معتبر',
                'description': 'هیچ مشکل جدی در داده‌ها شناسایی نشد. می‌توانید با اطمینان ادامه دهید.',
                'action': 'PROCEED',
                'affected_count': 0
            })
        
        return recommendations
    
    def _generate_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """تولید آمار و ارقام"""
        doc_count = results.get('document_count', 0)
        item_count = results.get('item_count', 0)
        
        return {
            'documents': {
                'total': doc_count,
                'with_issues': self._count_documents_with_issues(results),
                'valid': doc_count - self._count_documents_with_issues(results)
            },
            'items': {
                'total': item_count,
                'with_coding_issues': len(results.get('coding', {}).get('missing_codes', [])),
                'valid': item_count - len(results.get('coding', {}).get('missing_codes', []))
            },
            'financial_totals': {
                'total_debit': results.get('total_debit', 0),
                'total_credit': results.get('total_credit', 0),
                'balance_difference': results.get('balance_difference', 0)
            }
        }
    
    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """تولید گزارش HTML"""
        return render_to_string('reports/validation_report.html', {
            'report': report_data,
            'generation_time': timezone.now()
        })
    
    def _generate_pdf_report(self, report_data: Dict[str, Any]) -> bytes:
        """تولید گزارش PDF"""
        html_content = self._generate_html_report(report_data)
        return HTML(string=html_content).write_pdf()
    
    def _generate_excel_report(self, results: Dict[str, Any]) -> bytes:
        """تولید گزارش Excel"""
        with pd.ExcelWriter('validation_report.xlsx', engine='openpyxl') as writer:
            # برگه خلاصه
            summary_data = []
            for section in self._generate_detailed_analysis(results):
                summary_data.append({
                    'بخش': section['title'],
                    'تعداد خطاها': len(section['issues']),
                    'سطح شدت': section['severity']
                })
            
            if summary_data:
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='خلاصه', index=False)
            
            # برگه خطاهای جزئی
            detailed_data = []
            for validator_key, validator_results in results.items():
                if isinstance(validator_results, dict) and 'issues' in validator_results:
                    for severity, issues in validator_results['issues'].items():
                        for issue in issues:
                            detailed_data.append({
                                'نوع اعتبارسنجی': validator_key,
                                'سطح شدت': severity,
                                'شرح خطا': issue.get('reason', ''),
                                'شماره سند': issue.get('document', {}).get('document_number', ''),
                                'مقدار مشکل‌دار': issue.get('original_value', '')
                            })
            
            if detailed_data:
                pd.DataFrame(detailed_data).to_excel(writer, sheet_name='خطاهای جزئی', index=False)
            
            # ذخیره در بایت
            writer.close()
            with open('validation_report.xlsx', 'rb') as f:
                return f.read()
    
    def _calculate_quality_score(self, total_issues: int, total_documents: int) -> float:
        """محاسبه امتیاز کیفیت داده‌ها"""
        if total_documents == 0:
            return 100.0
        
        issue_ratio = total_issues / total_documents
        score = max(0, 100 - (issue_ratio * 100))
        return round(score, 2)
    
    def _generate_summary_message(self, total_issues: int, critical_issues: int) -> str:
        """تولید پیام خلاصه"""
        if critical_issues > 0:
            return f"⚠️ {critical_issues} خطای بحرانی وجود دارد. وارد کردن داده‌ها توصیه نمی‌شود."
        elif total_issues > 0:
            return f"ℹ️ {total_issues} خطا شناسایی شد. می‌توانید پس از بررسی ادامه دهید."
        else:
            return "✅ داده‌ها کاملاً معتبر هستند. می‌توانید با اطمینان ادامه دهید."
    
    def _extract_issues_for_section(self, section_results: Dict) -> List[Dict]:
        """استخراج خطاهای یک بخش"""
        issues = []
        if 'issues' in section_results:
            for severity, issue_list in section_results['issues'].items():
                for issue in issue_list:
                    issues.append({
                        'severity': severity,
                        'description': issue.get('reason', ''),
                        'details': issue
                    })
        return issues
    
    def _extract_statistics_for_section(self, section_results: Dict) -> Dict:
        """استخراج آمار یک بخش"""
        return {
            'total_issues': sum(len(issues) for issues in section_results.get('issues', {}).values()),
            'by_severity': {severity: len(issues) for severity, issues in section_results.get('issues', {}).items()}
        }
    
    def _calculate_section_severity(self, section_results: Dict) -> str:
        """محاسبه سطح شدت یک بخش"""
        if not section_results.get('issues'):
            return 'SUCCESS'
        
        severities = list(section_results.get('issues', {}).keys())
        if any(s in ['CRITICAL', 'critical'] for s in severities):
            return 'CRITICAL'
        elif any(s in ['HIGH', 'high'] for s in severities):
            return 'HIGH'
        elif any(s in ['MEDIUM', 'medium'] for s in severities):
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _count_documents_with_issues(self, results: Dict) -> int:
        """شمارش اسناد دارای مشکل"""
        documents_with_issues = set()
        
        # از خطاهای تکراری
        for duplicate in results.get('duplicate', {}).get('exact_duplicates', []):
            if 'document' in duplicate:
                doc_num = duplicate['document'].get('document_number')
                if doc_num:
                    documents_with_issues.add(doc_num)
        
        # از خطاهای توالی
        for sequence_issue in results.get('sequence', {}).get('issues', {}).get('duplicates', []):
            if 'document_number' in sequence_issue:
                documents_with_issues.add(sequence_issue['document_number'])
        
        return len(documents_with_issues)