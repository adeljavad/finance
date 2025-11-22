import json
import os
import logging
from typing import Dict, List, Any, Optional
from django.conf import settings
import uuid
import time

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    مدیریت حافظه مکالمات برای چت بات
    """
    
    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.path.join(settings.BASE_DIR, "data", "memory")
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # ذخیره sessionهای فعال در memory
        self.active_sessions = {}
        
        # تنظیمات memory
        self.max_history_length = 10  # حداکثر تعداد پیام‌های ذخیره شده
    
    def get_session_file(self, session_id: str) -> str:
        """مسیر فایل ذخیره session"""
        return os.path.join(self.storage_dir, f"{session_id}.json")
    
    def create_session(self, session_id: str = None) -> str:
        """ایجاد session جدید"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        session_data = {
            "session_id": session_id,
            "messages": [],
            "created_at": time.time(),
            "last_activity": time.time()
        }
        
        self.active_sessions[session_id] = session_data
        self._save_session(session_id)
        
        logger.info(f"Session created: {session_id}")
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None):
        """اضافه کردن پیام به history"""
        if session_id not in self.active_sessions:
            self._load_session(session_id)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        
        self.active_sessions[session_id]["messages"].append(message)
        
        # محدود کردن طول history
        if len(self.active_sessions[session_id]["messages"]) > self.max_history_length:
            self.active_sessions[session_id]["messages"] = self.active_sessions[session_id]["messages"][-self.max_history_length:]
        
        self.active_sessions[session_id]["last_activity"] = time.time()
        self._save_session(session_id)
    
    def get_conversation_history(self, session_id: str, last_n: int = 5) -> List[Dict]:
        """دریافت تاریخچه مکالمه"""
        if session_id not in self.active_sessions:
            self._load_session(session_id)
        
        if session_id not in self.active_sessions:
            return []
        
        messages = self.active_sessions[session_id]["messages"]
        return messages[-last_n:] if last_n > 0 else messages
    
    def get_last_user_message(self, session_id: str) -> Optional[str]:
        """دریافت آخرین پیام کاربر"""
        history = self.get_conversation_history(session_id)
        for message in reversed(history):
            if message["role"] == "user":
                return message["content"]
        return None
    
    def get_context_summary(self, session_id: str) -> str:
        """خلاصه‌ای از context مکالمه"""
        history = self.get_conversation_history(session_id, last_n=3)
        
        if not history:
            return "مکالمه جدید"
        
        context_parts = []
        for msg in history:
            role = "کاربر" if msg["role"] == "user" else "دستیار"
            content_preview = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            context_parts.append(f"{role}: {content_preview}")
        
        return " | ".join(context_parts)
    
    def _load_session(self, session_id: str):
        """لود session از فایل"""
        session_file = self.get_session_file(session_id)
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    self.active_sessions[session_id] = json.load(f)
                logger.info(f"Session loaded: {session_id}")
            except Exception as e:
                logger.error(f"Error loading session {session_id}: {e}")
                self.create_session(session_id)
        else:
            self.create_session(session_id)
    
    def _save_session(self, session_id: str):
        """ذخیره session در فایل"""
        try:
            session_file = self.get_session_file(session_id)
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(self.active_sessions[session_id], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving session {session_id}: {e}")
    
    def clear_session(self, session_id: str):
        """پاک کردن session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        session_file = self.get_session_file(session_id)
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
                logger.info(f"Session cleared: {session_id}")
            except Exception as e:
                logger.error(f"Error clearing session {session_id}: {e}")