import os
import requests
import json
from typing import Dict, Any, List


class DeepSeekLLM:
    """
    کلاس برای ارتباط با API دیپ‌سیک
    """

    def __init__(self):
        # در حالت standalone از environment variable استفاده می‌کنیم
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        
        if not self.api_key:
            # اگر API_KEY وجود نداشت، از یک مقدار پیش‌فرض استفاده می‌کنیم
            # (در حالت واقعی باید از فایل .env یا تنظیمات دیگر خوانده شود)
            self.api_key = "dummy_key_for_testing"
            print("⚠️  هشدار: DEEPSEEK_API_KEY پیدا نشد. از کلید تست استفاده می‌شود.")

    def invoke(self, messages: List[Dict[str, str]]) -> str:
        """
        ارسال درخواست به API دیپ‌سیک
        
        Args:
            messages: لیست پیام‌ها به فرمت [{"role": "user", "content": "متن"}]
            
        Returns:
            پاسخ مدل به صورت متن
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "stream": False,
            "temperature": 0.3,
            "max_tokens": 2000
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"خطا در ارتباط با DeepSeek API: {str(e)}")
        except KeyError as e:
            raise Exception(f"خطا در پردازش پاسخ API: {str(e)}")
        except Exception as e:
            raise Exception(f"خطای ناشناخته: {str(e)}")

    async def ainvoke(self, messages: List[Dict[str, str]]) -> str:
        """
        نسخه async برای استفاده در LangGraph
        """
        return self.invoke(messages)

    def __call__(self, messages: List[Dict[str, str]]) -> str:
        """پشتیبانی از callable برای سازگاری"""
        return self.invoke(messages)
