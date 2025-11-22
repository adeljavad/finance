# data_importer/validators/coding_validator.py
from django.db.models import Q
from financial_system.models import ChartOfAccounts
from typing import List, Dict, Set, Tuple

class CodingExistenceValidator:
    def __init__(self, company_id: int):
        self.company_id = company_id
        self.existing_codes_cache = None
    
    def validate_coding_existence(self, document_items: List[Dict]) -> Dict[str, List]:
        """اعتبارسنجی وجود کدینگ‌های مورد استفاده در اسناد"""
        validation_result = {
            'missing_codes': [],      # کدهای موجود در سند اما موجود در دیتابیس
            'invalid_levels': [],     # کدهای با سطح نامعتبر
            'suggestions': [],        # پیشنهادات برای کدهای مشابه
            'auto_created': []        # کدهایی که به صورت خودکار ایجاد شدند
        }
        
        if not document_items:
            return validation_result
        
        # جمع‌آوری تمام کدهای استفاده شده
        used_codes = self._extract_used_codes(document_items)
        
        # بررسی وجود کدها در دیتابیس
        self._check_missing_codes(used_codes, validation_result)
        
        # بررسی سطوح کدینگ
        self._validate_code_levels(used_codes, validation_result)
        
        # تولید پیشنهادات برای کدهای مشابه
        self._generate_suggestions(used_codes, validation_result)
        
        return validation_result
    
    def _extract_used_codes(self, document_items: List[Dict]) -> Set[str]:
        """استخراج تمام کدهای استفاده شده در اسناد"""
        used_codes = set()
        
        for item in document_items:
            account_code = item.get('account_code')
            if account_code:
                used_codes.add(str(account_code).strip())
            
            # همچنین کدهای مرکز هزینه و پروژه
            cost_center = item.get('cost_center')
            if cost_center:
                used_codes.add(f"CC_{cost_center}".strip())
            
            project_code = item.get('project_code')
            if project_code:
                used_codes.add(f"PRJ_{project_code}".strip())
        
        return used_codes
    
    def _check_missing_codes(self, used_codes: Set[str], validation_result: Dict):
        """بررسی کدهای موجود در سند اما موجود در دیتابیس"""
        existing_codes = self._get_existing_codes()
        
        missing_codes = used_codes - existing_codes
        
        for code in missing_codes:
            validation_result['missing_codes'].append({
                'code': code,
                'suggested_level': self._suggest_code_level(code),
                'usage_count': self._count_code_usage(code, used_codes)
            })
    
    def _get_existing_codes(self) -> Set[str]:
        """دریافت کدهای موجود از دیتابیس (با کش)"""
        if self.existing_codes_cache is None:
            existing_accounts = ChartOfAccounts.objects.filter(
                is_active=True
            ).values_list('code', flat=True)
            self.existing_codes_cache = set(existing_accounts)
        
        return self.existing_codes_cache
    
    def _validate_code_levels(self, used_codes: Set[str], validation_result: Dict):
        """اعتبارسنجی سطوح کدینگ"""
        for code in used_codes:
            expected_level = self._suggest_code_level(code)
            actual_level = self._get_actual_code_level(code)
            
            if actual_level and actual_level != expected_level:
                validation_result['invalid_levels'].append({
                    'code': code,
                    'expected_level': expected_level,
                    'actual_level': actual_level,
                    'suggestion': f"سطح کد باید {expected_level} باشد نه {actual_level}"
                })
    
    def _suggest_code_level(self, code: str) -> str:
        """پیشنهاد سطح کد بر اساس ساختار آن"""
        if code.startswith(('CC_', 'PRJ_')):
            return 'COST_CENTER' if code.startswith('CC_') else 'PROJECT'
        
        clean_code = ''.join(filter(str.isdigit, code))
        
        if not clean_code:
            return 'UNKNOWN'
        
        code_length = len(clean_code)
        
        if code_length <= 2:
            return 'CLASS'
        elif code_length <= 4:
            return 'SUBCLASS'
        elif code_length <= 6:
            return 'DETAIL'
        else:
            return 'DETAIL'  # سطوح پایین‌تر
    
    def _get_actual_code_level(self, code: str) -> str:
        """دریافت سطح واقعی کد از دیتابیس"""
        try:
            account = ChartOfAccounts.objects.get(code=code)
            return account.level
        except ChartOfAccounts.DoesNotExist:
            return None
    
    def _count_code_usage(self, target_code: str, all_codes: Set[str]) -> int:
        """شمارش استفاده از یک کد خاص"""
        return sum(1 for code in all_codes if code == target_code)
    
    def _generate_suggestions(self, used_codes: Set[str], validation_result: Dict):
        """تولید پیشنهادات برای کدهای مشابه"""
        existing_codes = self._get_existing_codes()
        
        for missing_code in validation_result['missing_codes']:
            code = missing_code['code']
            similar_codes = self._find_similar_codes(code, existing_codes)
            
            if similar_codes:
                validation_result['suggestions'].append({
                    'missing_code': code,
                    'similar_codes': similar_codes,
                    'suggestion': f"آیا منظور شما یکی از کدهای {', '.join(similar_codes)} بوده است؟"
                })
    
    def _find_similar_codes(self, target_code: str, existing_codes: Set[str], max_suggestions: int = 3) -> List[str]:
        """پیدا کردن کدهای مشابه"""
        target_clean = ''.join(filter(str.isdigit, target_code))
        
        if not target_clean:
            return []
        
        # پیدا کردن کدهایی که با همان الگو شروع می‌شوند
        similar = []
        for code in existing_codes:
            code_clean = ''.join(filter(str.isdigit, code))
            if code_clean.startswith(target_clean[:2]):  # حداقل ۲ رقم اول مشترک
                similar.append(code)
            
            if len(similar) >= max_suggestions:
                break
        
        return similar
    
    def auto_create_missing_codes(self, missing_codes_info: List[Dict]) -> List[Dict]:
        """ایجاد خودکار کدهای مفقود (با تأیید کاربر)"""
        created_codes = []
        
        for code_info in missing_codes_info:
            code = code_info['code']
            level = code_info['suggested_level']
            
            # ایجاد کد جدید
            new_account = ChartOfAccounts.objects.create(
                code=code,
                name=f"کد {code} - ایجاد خودکار",
                level=level,
                is_active=True,
                description="این کد به صورت خودکار در هنگام وارد کردن اسناد ایجاد شد"
            )
            
            created_codes.append({
                'code': code,
                'level': level,
                'account_id': new_account.id,
                'account_name': new_account.name
            })
        
        # به‌روزرسانی کش
        self.existing_codes_cache = None
        
        return created_codes