# استفاده از یک image پایه پایتون سبک
FROM python:3.11-slim

# جلوگیری از نوشتن فایل‌های .pyc و بافر کردن خروجی
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# تنظیم مسیر کاری
WORKDIR /app

# نصب system dependencies و سپس Python dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# کپی فایل requirements و نصب آن‌ها
COPY ./requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# کپی کردن کل پروژه
COPY . .

# اجرای Django (ممکن است نیاز به تغییر دستور داشته باشید)
CMD ["gunicorn", "accounting_chatbot.wsgi:application", "--bind", "0.0.0.0:8000"]