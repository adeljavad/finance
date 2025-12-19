import pandas as pd
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
    مدیریت داده‌های هر کاربر به صورت جداگانه - نسخه بهبود یافته با مدیریت خطا
    """
    def __init__(self):
        self.redis_client = None
        self.fallback_storage_dir = "user_data"
        self.user_data_prefix = "user_data:"
        self.user_session_prefix = "user_session:"
        self.column_mapper = ExcelColumnMapper()
        
        # تلاش برای اتصال به Redis
        try:
            import redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=1,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # تست اتصال
            self.redis_client.ping()
            logger.info("✅ Redis connection successful")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available, using file storage: {e}")
            self.redis_client = None
            
        # ایجاد پوشه fallback
        import os
        os.makedirs(self.fallback_storage_dir, exist_ok=True)

    def _get_session_data_key(self, user_id: str) -> str:
        """تولید کلید منحصر به فرد برای session"""
        return f"{self.user_session_prefix}{user_id}"

    def _get_dataframe_key(self, user_id: str, df_name: str) -> str:
        """تولید کلید منحصر به فرد برای DataFrame"""
        return f"{self.user_data_prefix}{user_id}:{df_name}"

    def _save_to_redis(self, key: str, data: str, expire_seconds: int = 3600 * 24 * 7):
        """ذخیره در Redis با fallback"""
        if self.redis_client:
            try:
                self.redis_client.setex(key, expire_seconds, data)
                return True
            except Exception as e:
                logger.error(f"Redis save error: {e}")
                
        # Fallback to file storage
        try:
            import os
            file_path = os.path.join(self.fallback_storage_dir, f"{key.replace(':', '_')}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(data)
            logger.info(f"✅ Saved to file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"File save error: {e}")
            return False

    def _load_from_redis(self, key: str) -> Optional[str]:
        """بارگذاری از Redis با fallback"""
        if self.redis_client:
            try:
                data = self.redis_client.get(key)
                if data:
                    return data
            except Exception as e:
                logger.error(f"Redis load error: {e}")
                
        # Fallback from file storage
        try:
            import os
            file_path = os.path.join(self.fallback_storage_dir, f"{key.replace(':', '_')}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = f.read()
                logger.info(f"✅ Loaded from file: {file_path}")
                return data
        except Exception as e:
            logger.error(f"File load error: {e}")
            
        return None

    def _delete_from_redis(self, key: str) -> bool:
        """حذف از Redis با fallback"""
        deleted = False
        
        if self.redis_client:
            try:
                self.redis_client.delete(key)
                deleted = True
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
                
        # Fallback from file storage
        try:
            import os
            file_path = os.path.join(self.fallback_storage_dir, f"{key.replace(':', '_')}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted = True
        except Exception as e:
            logger.error(f"File delete error: {e}")
            
        return deleted

    def create_user_session(self, user_id: str = None) -> str:
        """ایجاد session جدید برای کاربر با مدیریت خطا"""
        if not user_id:
            user_id = str(uuid.uuid4())

        session_data = {
            'user_id': user_id,
            'created_at': pd.Timestamp.now().isoformat(),
            'dataframes': {},
            'uploaded_files': [],
            'analysis_history': []
        }

        session_key = self._get_session_data_key(user_id)
        if self._save_to_redis(session_key, json.dumps(session_data, default=str)):
            logger.info(f"✅ User session created: {user_id}")
            return user_id
        else:
            logger.error(f"❌ Failed to create session for user: {user_id}")
            return user_id  # Still return the ID for backward compatibility

    def get_user_session(self, user_id: str) -> Dict[str, Any]:
        """دریافت session کاربر با مدیریت خطا"""
        session_key = self._get_session_data_key(user_id)
        session_data = self._load_from_redis(session_key)
        
        if session_data:
            try:
                return json.loads(session_data)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for user {user_id}: {e}")
                
        # ایجاد session جدید در صورت عدم وجود
        logger.info(f"🔄 Creating new session for user: {user_id}")
        return self.create_user_session(user_id)

    def save_dataframe(self, user_id: str, df_name: str, dataframe: pd.DataFrame):
        """ذخیره DataFrame با مدیریت خطای بهبود یافته"""
        try:
            logger.info(f"💾 Saving DataFrame '{df_name}' for user '{user_id}' - Shape: {dataframe.shape}")
            
            # بررسی خالی نبودن DataFrame
            if dataframe.empty:
                logger.warning(f"⚠️ DataFrame is empty for user {user_id}: {df_name}")
                return
                
            # پاکسازی داده‌ها
            cleaned_df = dataframe.copy()
            
            # بررسی و پاکسازی ستون‌های datetime
            for col in cleaned_df.columns:
                if cleaned_df[col].dtype == 'datetime64[ns]':
                    # تبدیل datetime به string برای JSON serialization
                    cleaned_df[col] = cleaned_df[col].astype(str)
                elif cleaned_df[col].dtype == 'object':
                    # پاکسازی رشته‌ها
                    cleaned_df[col] = cleaned_df[col].fillna('').astype(str)
            
            # تبدیل به JSON با تنظیمات مناسب
            df_json = cleaned_df.to_json(
                orient='split', 
                date_format='iso',
                force_ascii=False,
                default=str
            )
            
            # ذخیره در Redis/Fallback
            data_key = self._get_dataframe_key(user_id, df_name)
            if self._save_to_redis(data_key, df_json):
                # آپدیت session
                session = self.get_user_session(user_id)
                session['dataframes'][df_name] = {
                    'created_at': pd.Timestamp.now().isoformat(),
                    'rows': len(cleaned_df),
                    'columns': list(cleaned_df.columns),
                    'data_types': {col: str(dtype) for col, dtype in cleaned_df.dtypes.items()}
                }
                
                session_key = self._get_session_data_key(user_id)
                self._save_to_redis(session_key, json.dumps(session, default=str))
                logger.info(f"✅ DataFrame saved successfully for user {user_id}: {df_name} ({len(cleaned_df)} rows)")
            else:
                logger.error(f"❌ Failed to save DataFrame for user {user_id}: {df_name}")
                
        except Exception as e:
            logger.error(f"❌ Error saving dataframe for user {user_id}: {e}")
            logger.error(f"DataFrame info - Shape: {dataframe.shape}, Columns: {list(dataframe.columns)}")
            raise

    def get_dataframe(self, user_id: str, df_name: str) -> Optional[pd.DataFrame]:
        """دریافت DataFrame با مدیریت خطای بهبود یافته"""
        try:
            data_key = self._get_dataframe_key(user_id, df_name)
            df_json = self._load_from_redis(data_key)
            
            if df_json:
                # بازخوانی JSON به DataFrame
                dataframe = pd.read_json(df_json, orient='split', dtype=False)
                logger.info(f"✅ DataFrame loaded successfully for user {user_id}: {df_name} (Shape: {dataframe.shape})")
                return dataframe
            else:
                logger.warning(f"⚠️ DataFrame not found for user {user_id}: {df_name}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error loading dataframe for user {user_id}: {e}")
            logger.error(f"Attempted to load key: {self._get_dataframe_key(user_id, df_name)}")
            return None

    def add_uploaded_file(self, user_id: str, file_info: Dict[str, Any]):
        """اضافه کردن اطلاعات فایل آپلود شده"""
        try:
            session = self.get_user_session(user_id)
            session['uploaded_files'].append({
                **file_info,
                'uploaded_at': pd.Timestamp.now().isoformat()
            })
            session_key = self._get_session_data_key(user_id)
            self._save_to_redis(session_key, json.dumps(session, default=str))
            logger.info(f"✅ File info added for user {user_id}: {file_info.get('filename', 'unknown')}")
        except Exception as e:
            logger.error(f"❌ Error adding file info for user {user_id}: {e}")

    def get_user_dataframes_info(self, user_id: str) -> Dict[str, Any]:
        """دریافت اطلاعات DataFrameهای کاربر"""
        try:
            session = self.get_user_session(user_id)
            info = session.get('dataframes', {})
            logger.info(f"📊 Found {len(info)} DataFrames for user {user_id}")
            return info
        except Exception as e:
            logger.error(f"❌ Error getting dataframes info for user {user_id}: {e}")
            return {}

    def get_uploaded_files_info(self, user_id: str) -> List[Dict[str, Any]]:
        """دریافت اطلاعات فایل‌های آپلود شده"""
        try:
            session = self.get_user_session(user_id)
            files = session.get('uploaded_files', [])
            logger.info(f"📁 Found {len(files)} uploaded files for user {user_id}")
            return files
        except Exception as e:
            logger.error(f"❌ Error getting uploaded files info for user {user_id}: {e}")
            return []

    def clear_user_data(self, user_id: str):
        """پاک کردن تمام داده‌های کاربر"""
        try:
            logger.info(f"🗑️ Clearing all data for user: {user_id}")
            
            # پاک کردن session
            session_key = self._get_session_data_key(user_id)
            self._delete_from_redis(session_key)

            # پاک کردن DataFrameها
            if self.redis_client:
                pattern = f"{self.user_data_prefix}{user_id}:*"
                try:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                        logger.info(f"🗑️ Deleted {len(keys)} DataFrame keys for user {user_id}")
                except Exception as e:
                    logger.error(f"Redis pattern delete error: {e}")
            else:
                # Fallback file cleanup
                import os
                import glob
                pattern = os.path.join(self.fallback_storage_dir, f"{self.user_data_prefix.replace(':', '_')}{user_id}:*.json")
                files = glob.glob(pattern)
                for file_path in files:
                    try:
                        os.remove(file_path)
                        logger.info(f"🗑️ Deleted file: {file_path}")
                    except Exception as e:
                        logger.error(f"File delete error: {e}")

            logger.info(f"✅ All data cleared for user: {user_id}")
        except Exception as e:
            logger.error(f"❌ Error clearing user data {user_id}: {e}")

    def debug_user_data(self, user_id: str) -> Dict[str, Any]:
        """دیباگ اطلاعات کاربر برای troubleshooting"""
        debug_info = {
            'user_id': user_id,
            'has_data': False,
            'dataframes': {},
            'uploaded_files': [],
            'storage_type': 'redis' if self.redis_client else 'file',
            'session_exists': False
        }
        
        try:
            # بررسی وجود session
            session = self.get_user_session(user_id)
            debug_info['session_exists'] = True
            
            # بررسی DataFrameها
            df_info = self.get_user_dataframes_info(user_id)
            debug_info['dataframes'] = df_info
            debug_info['has_data'] = len(df_info) > 0
            
            # تست load کردن DataFrame اصلی
            test_df = self.get_dataframe(user_id, 'accounting_data')
            if test_df is not None and not test_df.empty:
                debug_info['accounting_data_status'] = {
                    'loaded': True,
                    'shape': list(test_df.shape),
                    'columns': list(test_df.columns)
                }
                debug_info['has_data'] = True
            else:
                debug_info['accounting_data_status'] = {'loaded': False}
            
            # بررسی فایل‌های آپلود شده
            files_info = self.get_uploaded_files_info(user_id)
            debug_info['uploaded_files'] = files_info
            
            logger.info(f"🔍 Debug info for user {user_id}: {debug_info}")
            return debug_info
            
        except Exception as e:
            debug_info['error'] = str(e)
            logger.error(f"❌ Debug error for user {user_id}: {e}")
            return debug_info

    def process_accounting_file(self, user_id: str, file_content, filename: str) -> pd.DataFrame:
        """پردازش هوشمند فایل حسابداری با مدیریت خطای بهبود یافته"""
        try:
            logger.info(f"🔄 Processing accounting file: {filename} for user: {user_id}")
            
            # تشخیص نوع فایل
            if filename.lower().endswith('.csv'):
                # برای CSV
                if hasattr(file_content, 'read'):
                    dataframe = pd.read_csv(file_content)
                else:
                    dataframe = pd.read_csv(io.StringIO(file_content))
            elif filename.lower().endswith(('.xlsx', '.xls')):
                # برای Excel
                if hasattr(file_content, 'read'):
                    dataframe = pd.read_excel(file_content)
                else:
                    dataframe = pd.read_excel(io.BytesIO(file_content))
            else:
                raise ValueError("فرمت فایل پشتیبانی نمی‌شود. فقط CSV و Excel مجاز هستند.")

            # بررسی خالی نبودن
            if dataframe.empty:
                raise ValueError("فایل آپلود شده خالی است یا داده‌ای ندارد.")

            logger.info(f"📊 File loaded - Shape: {dataframe.shape}, Columns: {list(dataframe.columns)}")

            # اعتبارسنجی ستون‌های ضروری (با انعطاف بیشتر)
            required_columns = ['شماره سند', 'تاریخ سند', 'بدهکار', 'بستانکار', 'توضیحات']
            dataframe_columns_lower = [str(col).strip().lower() for col in dataframe.columns]
            required_columns_lower = [col.lower() for col in required_columns]
            
            missing_columns = []
            for req_col, req_col_lower in zip(required_columns, required_columns_lower):
                if req_col_lower not in dataframe_columns_lower:
                    missing_columns.append(req_col)
                    
            if missing_columns:
                logger.warning(f"⚠️ Missing columns: {missing_columns}")
                # به جای خطا، ستون‌ها را mapping کنیم
                # (این قسمت را می‌توان با ExcelColumnMapper پیشرفته‌تر کرد)

            # تبدیل انواع داده
            if 'تاریخ سند' in dataframe.columns:
                try:
                    dataframe['تاریخ سند'] = pd.to_datetime(
                        dataframe['تاریخ سند'],
                        errors='coerce',
                        infer_datetime_format=True
                    )
                    # تبدیل به string برای ذخیره‌سازی
                    dataframe['تاریخ سند'] = dataframe['تاریخ سند'].astype(str)
                except Exception as e:
                    logger.warning(f"Date conversion warning: {e}")
                    
            if 'بدهکار' in dataframe.columns:
                dataframe['بدهکار'] = pd.to_numeric(dataframe['بدهکار'], errors='coerce').fillna(0)
            if 'بستانکار' in dataframe.columns:
                dataframe['بستانکار'] = pd.to_numeric(dataframe['بستانکار'], errors='coerce').fillna(0)

            # پاکسازی کلی داده‌ها
            dataframe = dataframe.fillna('')
            
            # ذخیره DataFrame
            self.save_dataframe(user_id, 'accounting_data', dataframe)

            # ثبت اطلاعات فایل
            self.add_uploaded_file(user_id, {
                'filename': filename,
                'rows': len(dataframe),
                'columns': list(dataframe.columns),
                'total_debit': float(dataframe['بدهکار'].sum()) if 'بدهکار' in dataframe.columns else 0,
                'total_credit': float(dataframe['بستانکار'].sum()) if 'بستانکار' in dataframe.columns else 0,
                'date_range': {
                    'start': dataframe['تاریخ سند'].min() if 'تاریخ سند' in dataframe.columns else 'N/A',
                    'end': dataframe['تاریخ سند'].max() if 'تاریخ سند' in dataframe.columns else 'N/A'
                }
            })

            logger.info(f"✅ Accounting file processed successfully for user {user_id}: {filename} ({len(dataframe)} rows)")
            return dataframe
            
        except Exception as e:
            logger.error(f"❌ Error processing accounting file for user {user_id}: {e}")
            raise

    def get_accounting_summary(self, user_id: str) -> Dict[str, Any]:
        """دریافت خلاصه اطلاعات حسابداری کاربر"""
        try:
            df = self.get_dataframe(user_id, 'accounting_data')
            
            if df is None or df.empty:
                return {
                    'has_data': False,
                    'message': 'هیچ داده حسابداری موجود نیست',
                    'debug_info': self.debug_user_data(user_id)
                }

            summary = {
                'has_data': True,
                'total_records': len(df),
                'columns': list(df.columns),
                'date_range': {},
                'financial_totals': {},
                'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
            }

            # محدوده تاریخ
            if 'تاریخ سند' in df.columns:
                try:
                    # تاریخ‌ها را به datetime تبدیل کنیم برای محاسبه
                    date_col = pd.to_datetime(df['تاریخ سند'], errors='coerce')
                    if not date_col.isna().all():
                        summary['date_range'] = {
                            'start': date_col.min().strftime('%Y/%m/%d'),
                            'end': date_col.max().strftime('%Y/%m/%d')
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
            logger.error(f"❌ Error getting accounting summary for user {user_id}: {e}")
            return {
                'has_data': False,
                'error': str(e),
                'debug_info': self.debug_user_data(user_id)
            }

    def _save_mapping_info(self, user_id: str, mapping_result: Dict, filename: str):
        """ذخیره اطلاعات مپینگ برای بررسی بعدی"""
        try:
            mapping_key = f"{self.user_data_prefix}{user_id}:mapping_info"
            mapping_data = {
                'filename': filename,
                'timestamp': pd.Timestamp.now().isoformat(),
                'mapping_result': mapping_result
            }
            
            # لود کردن لیست موجود
            existing_mappings_json = self._load_from_redis(mapping_key)
            if existing_mappings_json:
                mappings_list = json.loads(existing_mappings_json)
            else:
                mappings_list = []
                
            # اضافه کردن مپینگ جدید
            mappings_list.append(mapping_data)
            
            # ذخیره لیست به‌روز شده
            self._save_to_redis(mapping_key, json.dumps(mappings_list, default=str))
            
        except Exception as e:
            logger.error(f"❌ خطا در ذخیره اطلاعات مپینگ: {e}")

    def get_mapping_history(self, user_id: str) -> List[Dict]:
        """دریافت تاریخچه مپینگ‌های کاربر"""
        try:
            mapping_key = f"{self.user_data_prefix}{user_id}:mapping_info"
            mappings_data = self._load_from_redis(mapping_key)
            
            if mappings_data:
                return json.loads(mappings_data)
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ خطا در دریافت تاریخچه مپینگ: {e}")
            return []