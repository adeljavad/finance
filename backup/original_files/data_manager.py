import pandas as pd
import redis
import json
import uuid
import logging
import io
from typing import Dict, Any, Optional, List
from django.conf import settings
from .tools.excel_column_mapper import ExcelColumnMapper 
 
logger = logging.getLogger(__name__)

class UserDataManager:
    """
    مدیریت داده‌های هر کاربر به صورت جداگانه با Redis - نسخه هوشمند
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost', 
            port=6379, 
            db=1, 
            decode_responses=True
        )
        self.user_data_prefix = "user_data:"
        self.user_session_prefix = "user_session:"
        self.column_mapper = ExcelColumnMapper()  # اضافه کردن mapper


    def create_user_session(self, user_id: str = None) -> str:
        """ایجاد session جدید برای کاربر"""
        if not user_id:
            user_id = str(uuid.uuid4())
        
        session_data = {
            'user_id': user_id,
            'created_at': pd.Timestamp.now().isoformat(),
            'dataframes': {},
            'uploaded_files': [],
            'analysis_history': []
        }
        
        # ذخیره در Redis
        session_key = f"{self.user_session_prefix}{user_id}"
        self.redis_client.setex(
            session_key, 
            3600 * 24 * 7,  # 1 week expiry
            json.dumps(session_data, default=str)
        )
        
        logger.info(f"User session created: {user_id}")
        return user_id
    
    def get_user_session(self, user_id: str) -> Dict[str, Any]:
        """دریافت session کاربر"""
        session_key = f"{self.user_session_prefix}{user_id}"
        session_data = self.redis_client.get(session_key)
        
        if session_data:
            return json.loads(session_data)
        else:
            # ایجاد session جدید اگر وجود نداشت
            return self.create_user_session(user_id)
    
    def save_dataframe(self, user_id: str, df_name: str, dataframe: pd.DataFrame):
        """ذخیره DataFrame برای کاربر"""
        try:
            # تبدیل DataFrame به JSON
            df_json = dataframe.to_json(orient='split', date_format='iso')
            
            # ذخیره در Redis
            data_key = f"{self.user_data_prefix}{user_id}:{df_name}"
            self.redis_client.setex(data_key, 3600 * 24 * 7, df_json)
            
            # آپدیت session
            session = self.get_user_session(user_id)
            if df_name not in session['dataframes']:
                session['dataframes'][df_name] = {
                    'created_at': pd.Timestamp.now().isoformat(),
                    'rows': len(dataframe),
                    'columns': list(dataframe.columns)
                }
            
            session_key = f"{self.user_session_prefix}{user_id}"
            self.redis_client.setex(session_key, 3600 * 24 * 7, json.dumps(session, default=str))
            
            logger.info(f"DataFrame saved for user {user_id}: {df_name} ({len(dataframe)} rows)")
            
        except Exception as e:
            logger.error(f"Error saving dataframe for user {user_id}: {e}")
            raise
    
    def get_dataframe(self, user_id: str, df_name: str) -> Optional[pd.DataFrame]:
        """دریافت DataFrame کاربر"""
        try:
            data_key = f"{self.user_data_prefix}{user_id}:{df_name}"
            df_json = self.redis_client.get(data_key)
            
            if df_json:
                dataframe = pd.read_json(df_json, orient='split')
                logger.info(f"DataFrame loaded for user {user_id}: {df_name}")
                return dataframe
            else:
                logger.warning(f"DataFrame not found for user {user_id}: {df_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading dataframe for user {user_id}: {e}")
            return None
    
    def add_uploaded_file(self, user_id: str, file_info: Dict[str, Any]):
        """اضافه کردن اطلاعات فایل آپلود شده"""
        session = self.get_user_session(user_id)
        session['uploaded_files'].append({
            **file_info,
            'uploaded_at': pd.Timestamp.now().isoformat()
        })
        
        session_key = f"{self.user_session_prefix}{user_id}"
        self.redis_client.setex(session_key, 3600 * 24 * 7, json.dumps(session, default=str))
    
    def get_user_dataframes_info(self, user_id: str) -> Dict[str, Any]:
        """دریافت اطلاعات DataFrameهای کاربر"""
        session = self.get_user_session(user_id)
        return session.get('dataframes', {})
    
    def clear_user_data(self, user_id: str):
        """پاک کردن تمام داده‌های کاربر"""
        try:
            # پاک کردن session
            session_key = f"{self.user_session_prefix}{user_id}"
            self.redis_client.delete(session_key)
            
            # پاک کردن داده‌ها
            pattern = f"{self.user_data_prefix}{user_id}:*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            
            logger.info(f"All data cleared for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Error clearing user data {user_id}: {e}")
    
    def process_accounting_file(self, user_id: str, file_content, filename: str) -> pd.DataFrame:
        """پردازش فایل حسابداری و ایجاد DataFrame - نسخه اصلاح شده برای فایل Excel"""
        try:
            logger.info(f"Processing accounting file: {filename} for user: {user_id}")
            
            # بررسی نوع فایل و پردازش مناسب
            if filename.lower().endswith('.csv'):
                # برای فایل CSV
                if hasattr(file_content, 'read'):
                    # اگر file_content یک فایل آپلود شده است
                    dataframe = pd.read_csv(file_content)
                else:
                    # اگر string است
                    dataframe = pd.read_csv(io.StringIO(file_content))
                    
            elif filename.lower().endswith(('.xlsx', '.xls')):
                # برای فایل Excel
                if hasattr(file_content, 'read'):
                    # اگر file_content یک فایل آپلود شده است
                    dataframe = pd.read_excel(file_content)
                else:
                    # اگر bytes است
                    dataframe = pd.read_excel(io.BytesIO(file_content))
            else:
                raise ValueError("فرمت فایل پشتیبانی نمی‌شود. فقط CSV و Excel مجاز هستند.")
            
            # بررسی اینکه فایل خالی نباشد
            if dataframe.empty:
                raise ValueError("فایل آپلود شده خالی است یا داده‌ای ندارد.")
            
            # اعتبارسنجی ستون‌های ضروری
            required_columns = ['شماره سند', 'تاریخ سند', 'بدهکار', 'بستانکار', 'توضیحات']
            
            # بررسی وجود ستون‌های ضروری (با تطبیق case-insensitive)
            dataframe_columns_lower = [str(col).strip().lower() for col in dataframe.columns]
            required_columns_lower = [col.lower() for col in required_columns]
            
            missing_columns = []
            for req_col, req_col_lower in zip(required_columns, required_columns_lower):
                if req_col_lower not in dataframe_columns_lower:
                    missing_columns.append(req_col)
            
            if missing_columns:
                logger.warning(f"Missing columns: {missing_columns}")
                # به جای خطا، فقط هشدار می‌دهیم و ادامه می‌دهیم
            
            # تبدیل انواع داده
            if 'تاریخ سند' in dataframe.columns:
                # سعی در تبدیل تاریخ با فرمت‌های مختلف
                dataframe['تاریخ سند'] = pd.to_datetime(
                    dataframe['تاریخ سند'], 
                    errors='coerce',
                    format='mixed'  # برای پشتیبانی از فرمت‌های مختلف
                )
            
            if 'بدهکار' in dataframe.columns:
                dataframe['بدهکار'] = pd.to_numeric(dataframe['بدهکار'], errors='coerce').fillna(0)
            
            if 'بستانکار' in dataframe.columns:
                dataframe['بستانکار'] = pd.to_numeric(dataframe['بستانکار'], errors='coerce').fillna(0)
            
            # ذخیره DataFrame
            self.save_dataframe(user_id, 'accounting_data', dataframe)
            
            # ثبت اطلاعات فایل
            self.add_uploaded_file(user_id, {
                'filename': filename,
                'rows': len(dataframe),
                'columns': list(dataframe.columns),
                'total_debit': float(dataframe['بدهکار'].sum()) if 'بدهکار' in dataframe.columns else 0,
                'total_credit': float(dataframe['بستانکار'].sum()) if 'بستانکار' in dataframe.columns else 0
            })
            
            logger.info(f"Accounting file processed successfully for user {user_id}: {filename} ({len(dataframe)} rows)")
            return dataframe
            
        except Exception as e:
            logger.error(f"Error processing accounting file for user {user_id}: {e}")
            raise

    def get_accounting_summary(self, user_id: str) -> Dict[str, Any]:
        """دریافت خلاصه اطلاعات حسابداری کاربر"""
        try:
            df = self.get_dataframe(user_id, 'accounting_data')
            if df is None or df.empty:
                return {
                    'has_data': False,
                    'message': 'هیچ داده حسابداری موجود نیست'
                }
            
            summary = {
                'has_data': True,
                'total_records': len(df),
                'columns': list(df.columns),
                'date_range': {},
                'financial_totals': {}
            }
            
            # محدوده تاریخ - به صورت رشته‌ای
            if 'تاریخ سند' in df.columns:
                try:
                    # تاریخ‌ها را به صورت رشته نگه داریم
                    date_col = df['تاریخ سند'].astype(str)
                    # فیلتر کردن تاریخ‌های معتبر (رشته‌های ۱۰ کاراکتری)
                    valid_dates = date_col[date_col.str.match(r'\d{4}/\d{2}/\d{2}', na=False)]
                    if not valid_dates.empty:
                        summary['date_range'] = {
                            'start': valid_dates.min(),
                            'end': valid_dates.max()
                        }
                except Exception as e:
                    logger.warning(f"خطا در پردازش تاریخ: {e}")
            
            # مجموع‌های مالی
            if 'بدهکار' in df.columns:
                summary['financial_totals']['total_debit'] = float(df['بدهکار'].sum())
            if 'بستانکار' in df.columns:
                summary['financial_totals']['total_credit'] = float(df['بستانکار'].sum())
            if 'بدهکار' in df.columns and 'بستانکار' in df.columns:
                summary['financial_totals']['balance'] = float(df['بدهکار'].sum() - df['بستانکار'].sum())
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting accounting summary for user {user_id}: {e}")
            return {
                'has_data': False,
                'error': str(e)
            }
# -------------------------------------------            # 

   
    def process_accounting_file(self, user_id: str, file_content, filename: str) -> pd.DataFrame:
        """پردازش هوشمند فایل حسابداری با تشخیص خودکار ستون‌ها"""
        try:
            logger.info(f"پردازش هوشمند فایل: {filename} برای کاربر: {user_id}")
            
            # خواندن فایل Excel
            if hasattr(file_content, 'read'):
                dataframe = pd.read_excel(file_content)
            else:
                dataframe = pd.read_excel(io.BytesIO(file_content))
            
            if dataframe.empty:
                raise ValueError("فایل آپلود شده خالی است")
            
            # تشخیص خودکار ستون‌ها با LLM
            headers = list(dataframe.columns)
            sample_data = dataframe.head(3).to_dict('records')
            
            mapping_result = self.column_mapper.detect_columns_mapping(headers, sample_data)
            
            logger.info(f"نتیجه تشخیص ستون‌ها: {mapping_result.get('confidence')}")
            logger.info(f"مپینگ: {mapping_result.get('mapping', {})}")
            
            # نرمالایز کردن DataFrame
            normalized_df = self.column_mapper.normalize_dataframe(
                dataframe, 
                mapping_result.get('mapping', {})
            )
            
            # ذخیره اطلاعات مپینگ
            self._save_mapping_info(user_id, mapping_result, filename)
            
            # ذخیره DataFrame
            self.save_dataframe(user_id, 'accounting_data', normalized_df)
            
            # ثبت اطلاعات فایل
            self.add_uploaded_file(user_id, {
                'filename': filename,
                'original_columns': headers,
                'mapped_columns': list(normalized_df.columns),
                'mapping_confidence': mapping_result.get('confidence', 'unknown'),
                'rows': len(normalized_df),
                'total_debit': float(normalized_df['بدهکار'].sum()) if 'بدهکار' in normalized_df.columns else 0,
                'total_credit': float(normalized_df['بستانکار'].sum()) if 'بستانکار' in normalized_df.columns else 0,
                'mapping_notes': mapping_result.get('notes', '')
            })
            
            logger.info(f"فایل با موفقیت پردازش شد. ستون‌ها: {list(normalized_df.columns)}")
            return normalized_df
            
        except Exception as e:
            logger.error(f"خطا در پردازش هوشمند فایل: {e}")
            raise
    
    def _save_mapping_info(self, user_id: str, mapping_result: Dict, filename: str):
        """ذخیره اطلاعات مپینگ برای بررسی بعدی"""
        try:
            mapping_key = f"{self.user_data_prefix}{user_id}:mapping_info"
            mapping_data = {
                'filename': filename,
                'timestamp': pd.Timestamp.now().isoformat(),
                'mapping_result': mapping_result
            }
            
            # ذخیره در Redis (لیست تاریخچه مپینگ‌ها)
            existing_mappings = self.redis_client.get(mapping_key)
            if existing_mappings:
                mappings_list = json.loads(existing_mappings)
            else:
                mappings_list = []
            
            mappings_list.append(mapping_data)
            self.redis_client.setex(mapping_key, 3600 * 24 * 30, json.dumps(mappings_list, default=str))
            
        except Exception as e:
            logger.error(f"خطا در ذخیره اطلاعات مپینگ: {e}")
    
    def get_mapping_history(self, user_id: str) -> List[Dict]:
        """دریافت تاریخچه مپینگ‌های کاربر"""
        try:
            mapping_key = f"{self.user_data_prefix}{user_id}:mapping_info"
            mappings_data = self.redis_client.get(mapping_key)
            
            if mappings_data:
                return json.loads(mappings_data)
            else:
                return []
                
        except Exception as e:
            logger.error(f"خطا در دریافت تاریخچه مپینگ: {e}")
            return []