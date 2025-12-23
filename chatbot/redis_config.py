# chatbot/redis_config.py

# تنظیمات Redis - اگر در Docker از localhost استفاده می‌کنید
REDIS_HOST = 'localhost'  # یا '127.0.0.1'
REDIS_PORT = 6379

# اگر می‌خواهید از کانتینر موجود استفاده کنید:
# REDIS_HOST = 'acc-bot-redis-1'  # نام کانتینر Redis
# REDIS_PORT = 6379

# یا با environment variables
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))