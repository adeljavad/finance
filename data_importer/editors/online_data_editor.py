# data_importer/editors/online_data_editor.py
"""
ویرایشگر آنلاین داده‌های مالی
"""

import logging
import json
from typing import Dict, List, Optional, Any
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from data_importer.models import FinancialFile
from data_importer.validators.staged_validation_service import StagedValidationService
import pandas as pd

logger = logging.getLogger(__name__)


class OnlineDataEditor:
    """ویرایشگر آنلاین داده‌های مالی"""
    
    def __init__(self, financial_file: FinancialFile):
        self.financial_file = financial_file
        self.validator = StagedValidationService()
        self.data = None
        self.changes = []
        
    def load_data(self) -> Dict:
        """بارگذاری داده‌ها از فایل مالی"""
        try:
            logger.info(f"بارگذاری داده‌ها از فایل: {self.financial_file.file_path}")
            
            # خواندن فایل اکسل
            df = pd.read_excel(self.financial_file.file_path)
            
            # تبدیل به فرمت مناسب برای ویرایشگر
            self.data = {
                'columns': self._get_columns_info(df),
                'rows': self._convert_to_editor_format(df),
                'metadata': {
                    'total_rows': len(df),
                    'total_columns': len(df.columns),
                    'file_name': self.financial_file.file_name
                }
            }
            
            return {
                'success': True,
                'data': self.data,
                'validation': self.validator.validate_dataframe(df)
            }
            
        except Exception as e:
            logger.error(f"خطا در بارگذاری داده‌ها: {e}")
            return {'success': False, 'error': str(e)}
    
    def apply_changes(self, changes: List[Dict]) -> Dict:
        """اعمال تغییرات روی داده‌ها"""
        try:
            logger.info(f"اعمال {len(changes)} تغییر")
            
            # بارگذاری داده‌ها اگر هنوز بارگذاری نشده
            if self.data is None:
                load_result = self.load_data()
                if not load_result['success']:
                    return load_result
            
            # اعمال تغییرات
            for change in changes:
                self._apply_single_change(change)
            
            # ذخیره تغییرات موقت
            self.changes.extend(changes)
            
            # اعتبارسنجی داده‌های تغییر یافته
            df_modified = self._convert_to_dataframe()
            validation_result = self.validator.validate_dataframe(df_modified)
            
            return {
                'success': True,
                'changes_applied': len(changes),
                'validation': validation_result,
                'preview': self._get_preview_data()
            }
            
        except Exception as e:
            logger.error(f"خطا در اعمال تغییرات: {e}")
            return {'success': False, 'error': str(e)}
    
    def save_changes(self) -> Dict:
        """ذخیره تغییرات در فایل"""
        try:
            if not self.changes:
                return {'success': True, 'message': 'هیچ تغییری برای ذخیره وجود ندارد'}
            
            logger.info(f"ذخیره {len(self.changes)} تغییر در فایل")
            
            # تبدیل داده‌های ویرایش شده به DataFrame
            df_modified = self._convert_to_dataframe()
            
            # ذخیره در فایل اصلی
            df_modified.to_excel(self.financial_file.file_path, index=False)
            
            # پاک کردن تاریخچه تغییرات
            self.changes.clear()
            
            return {
                'success': True,
                'message': f'{len(self.changes)} تغییر با موفقیت ذخیره شد',
                'file_path': self.financial_file.file_path
            }
            
        except Exception as e:
            logger.error(f"خطا در ذخیره تغییرات: {e}")
            return {'success': False, 'error': str(e)}
    
    def validate_cell(self, row_index: int, column_name: str, value: Any) -> Dict:
        """اعتبارسنجی لحظه‌ای یک سلول"""
        try:
            # این تابع می‌تواند اعتبارسنجی خاص برای هر ستون انجام دهد
            validation_result = {
                'is_valid': True,
                'message': '',
                'suggestions': []
            }
            
            # اعتبارسنجی بر اساس نوع ستون
            if column_name in ['بدهکار', 'بستانکار']:
                # اعتبارسنجی مقادیر عددی
                try:
                    numeric_value = float(value) if value else 0
                    if numeric_value < 0:
                        validation_result.update({
                            'is_valid': False,
                            'message': 'مقدار نمی‌تواند منفی باشد',
                            'suggestions': ['استفاده از مقدار مثبت']
                        })
                    elif numeric_value > 1e15:  # بیشتر از ۱ کوادریلیون
                        validation_result.update({
                            'is_valid': False,
                            'message': 'مقدار بسیار بزرگ است',
                            'suggestions': ['بررسی صحت مقدار', 'تقسیم به چند سند']
                        })
                except (ValueError, TypeError):
                    validation_result.update({
                        'is_valid': False,
                        'message': 'مقدار باید عددی باشد',
                        'suggestions': ['تبدیل به عدد', 'حذف کاراکترهای غیرعددی']
                    })
            
            elif column_name == 'کد حساب':
                # اعتبارسنجی کد حساب
                if value and len(str(value).strip()) < 2:
                    validation_result.update({
                        'is_valid': False,
                        'message': 'کد حساب باید حداقل ۲ کاراکتر باشد',
                        'suggestions': ['استفاده از کد حساب معتبر']
                    })
            
            elif column_name == 'تاریخ سند':
                # اعتبارسنجی تاریخ
                if value and not self._is_valid_persian_date(str(value)):
                    validation_result.update({
                        'is_valid': False,
                        'message': 'فرمت تاریخ نامعتبر است',
                        'suggestions': ['استفاده از فرمت شمسی (YYYY/MM/DD)']
                    })
            
            return validation_result
            
        except Exception as e:
            logger.error(f"خطا در اعتبارسنجی سلول: {e}")
            return {'is_valid': False, 'message': f'خطا در اعتبارسنجی: {str(e)}'}
    
    def get_suggestions(self, row_index: int, column_name: str) -> List[str]:
        """دریافت پیشنهادات برای یک سلول"""
        suggestions = []
        
        if column_name == 'کد حساب':
            suggestions.extend([
                'استفاده از کدهای حساب از چارت حساب',
                'اطمینان از صحت فرمت کد حساب',
                'پر کردن کد حساب‌های خالی'
            ])
        
        elif column_name in ['بدهکار', 'بستانکار']:
            suggestions.extend([
                'استفاده از مقادیر عددی',
                'پرهیز از مقادیر منفی',
                'تقسیم مقادیر بزرگ به چند سند'
            ])
        
        elif column_name == 'تاریخ سند':
            suggestions.extend([
                'استفاده از فرمت شمسی (YYYY/MM/DD)',
                'اطمینان از قرارگیری در دوره مالی',
                'پر کردن تاریخ‌های خالی'
            ])
        
        return suggestions
    
    def _get_columns_info(self, df: pd.DataFrame) -> List[Dict]:
        """دریافت اطلاعات ستون‌ها"""
        columns_info = []
        
        for col in df.columns:
            column_info = {
                'name': col,
                'type': self._detect_column_type(df[col]),
                'editable': True,
                'required': col in ['شماره سند', 'کد حساب', 'بدهکار', 'بستانکار']
            }
            columns_info.append(column_info)
        
        return columns_info
    
    def _convert_to_editor_format(self, df: pd.DataFrame) -> List[Dict]:
        """تبدیل DataFrame به فرمت ویرایشگر"""
        rows = []
        
        for idx, row in df.iterrows():
            row_data = {
                'id': idx,
                'cells': {},
                'validation': {'is_valid': True, 'errors': []}
            }
            
            for col in df.columns:
                row_data['cells'][col] = {
                    'value': row[col] if pd.notna(row[col]) else '',
                    'original_value': row[col] if pd.notna(row[col]) else '',
                    'validation': self.validate_cell(idx, col, row[col])
                }
            
            rows.append(row_data)
        
        return rows
    
    def _convert_to_dataframe(self) -> pd.DataFrame:
        """تبدیل داده‌های ویرایش شده به DataFrame"""
        if not self.data:
            raise ValueError("داده‌ها بارگذاری نشده‌اند")
        
        # ایجاد DataFrame از داده‌های ویرایش شده
        rows_data = []
        for row in self.data['rows']:
            row_dict = {}
            for col_name, cell_data in row['cells'].items():
                row_dict[col_name] = cell_data['value']
            rows_data.append(row_dict)
        
        return pd.DataFrame(rows_data)
    
    def _apply_single_change(self, change: Dict):
        """اعمال یک تغییر واحد"""
        row_id = change.get('rowId')
        column_name = change.get('columnName')
        new_value = change.get('newValue')
        
        if row_id is None or column_name is None:
            raise ValueError("تغییر نامعتبر: rowId یا columnName مشخص نشده")
        
        # پیدا کردن ردیف مورد نظر
        target_row = None
        for row in self.data['rows']:
            if row['id'] == row_id:
                target_row = row
                break
        
        if not target_row:
            raise ValueError(f"ردیف با شناسه {row_id} یافت نشد")
        
        # اعمال تغییر
        if column_name in target_row['cells']:
            target_row['cells'][column_name]['value'] = new_value
            
            # اعتبارسنجی لحظه‌ای
            validation = self.validate_cell(row_id, column_name, new_value)
            target_row['cells'][column_name]['validation'] = validation
            
            # به‌روزرسانی وضعیت ردیف
            target_row['validation'] = self._validate_row(target_row)
    
    def _validate_row(self, row_data: Dict) -> Dict:
        """اعتبارسنجی یک ردیف کامل"""
        errors = []
        
        # بررسی مقادیر ضروری
        required_columns = ['شماره سند', 'کد حساب']
        for col in required_columns:
            if col in row_data['cells'] and not row_data['cells'][col]['value']:
                errors.append(f'ستون {col} نمی‌تواند خالی باشد')
        
        # بررسی اعتبارسنجی سلول‌ها
        for col_name, cell_data in row_data['cells'].items():
            if not cell_data['validation']['is_valid']:
                errors.append(f'{col_name}: {cell_data["validation"]["message"]}')
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    def _get_preview_data(self) -> Dict:
        """دریافت پیش‌نمایش داده‌های تغییر یافته"""
        if not self.data:
            return {}
        
        return {
            'first_five_rows': self.data['rows'][:5],
            'validation_summary': self._get_validation_summary(),
            'changes_summary': {
                'total_changes': len(self.changes),
                'recent_changes': self.changes[-5:] if self.changes else []
            }
        }
    
    def _get_validation_summary(self) -> Dict:
        """دریافت خلاصه اعتبارسنجی"""
        if not self.data:
            return {}
        
        total_rows = len(self.data['rows'])
        valid_rows = sum(1 for row in self.data['rows'] if row['validation']['is_valid'])
        
        return {
            'total_rows': total_rows,
            'valid_rows': valid_rows,
            'invalid_rows': total_rows - valid_rows,
            'valid_percentage': (valid_rows / total_rows * 100) if total_rows > 0 else 0
        }
    
    def _detect_column_type(self, series: pd.Series) -> str:
        """تشخیص نوع ستون"""
        if pd.api.types.is_numeric_dtype(series):
            return 'numeric'
        elif pd.api.types.is_datetime64_any_dtype(series):
            return 'date'
        else:
            return 'text'
    
    def _is_valid_persian_date(self, date_str: str) -> bool:
        """اعتبارسنجی تاریخ شمسی"""
        import re
        persian_date_pattern = r'\d{4}/\d{2}/\d{2}'
        return bool(re.match(persian_date_pattern, str(date_str)))


# ویوهای Django برای ویرایشگر آنلاین
@method_decorator(csrf_exempt, name='dispatch')
class DataEditorView(View):
    """ویو اصلی ویرایشگر داده‌ها"""
    
    def get(self, request, file_id: int):
        """دریافت داده‌ها برای ویرایش"""
        try:
            financial_file = FinancialFile.objects.get(id=file_id)
            editor = OnlineDataEditor(financial_file)
            result = editor.load_data()
            
            return JsonResponse(result)
            
        except FinancialFile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'فایل یافت نشد'}, status=404)
        except Exception as e:
            logger.error(f"خطا در دریافت داده‌ها: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    def post(self, request, file_id: int):
        """اعمال تغییرات روی داده‌ها"""
        try:
            financial_file = FinancialFile.objects.get(id=file_id)
            editor = OnlineDataEditor(financial_file)
            
            data = json.loads(request.body)
            changes = data.get('changes', [])
            
            result = editor.apply_changes(changes)
            return JsonResponse(result)
            
        except FinancialFile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'فایل یافت نشد'}, status=404)
        except Exception as e:
            logger.error(f"خطا در اعمال تغییرات: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SaveChangesView(View):
    """ویو ذخیره تغییرات"""
    
    def post(self, request, file_id: int):
        """ذخیره تغییرات در فایل"""
        try:
            financial_file = FinancialFile.objects.get(id=file_id)
            editor = OnlineDataEditor(financial_file)
            
            result = editor.save_changes()
            return JsonResponse(result)
            
        except FinancialFile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'فایل یافت نشد'}, status=404)
        except Exception as e:
            logger.error(f"خطا در ذخیره تغییرات: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ValidateCellView(View):
    """ویو اعتبارسنجی سلول"""
    
    def post(self, request, file_id: int):
        """اعتبارسنجی یک سلول خاص"""
        try:
            financial_file = FinancialFile.objects.get(id=file_id)
            editor = OnlineDataEditor(financial_file)
            
            data = json.loads(request.body)
            row_index = data.get('rowIndex')
            column_name = data.get('columnName')
            value = data.get('value')
            
            if row_index is None or column_name is None:
                return JsonResponse({'success': False, 'error': 'پارامترهای نامعتبر'}, status=400)
            
            result = editor.validate_cell(row_index, column_name, value)
            return JsonResponse({'success': True, 'validation': result})
            
        except FinancialFile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'فایل یافت نشد'}, status=404)
        except Exception as e:
            logger.error(f"خطا در اعتبارسنجی سلول: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
