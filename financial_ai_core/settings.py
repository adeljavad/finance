# financial_ai_core/settings.py
from django.conf import settings

# مقادیر پیش‌فرض
FINANCIAL_AI_MODEL_NAME = getattr(settings, 'FINANCIAL_AI_MODEL_NAME', 'financial-ai-core-v1')
FINANCIAL_AI_DEBUG = getattr(settings, 'FINANCIAL_AI_DEBUG', settings.DEBUG)
FINANCIAL_AI_LOG_INTERACTIONS = getattr(settings, 'FINANCIAL_AI_LOG_INTERACTIONS', True)

# آستانه اعتماد برای تصمیم‌گیری
MIN_CONFIDENCE_THRESHOLD = getattr(settings, 'FINANCIAL_AI_MIN_CONFIDENCE', 0.3)