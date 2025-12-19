#!/usr/bin/env python3
"""
اسکریپت خودکار — نسخه‌ی قابل اعتماد
کار می‌کند اگر در همان فولدری اجرا شود که financial_system در آن است
"""

import os
import shutil
import re
from pathlib import Path

# 📌 تعیین مسیر ریشه به‌صورت خودکار
SCRIPT_DIR = Path(__file__).parent.resolve()
SOURCE_ROOT = SCRIPT_DIR / "financial_system"
TARGET_ROOT = SCRIPT_DIR / "financial_ai_core"

# چک کن که SOURCE_ROOT واقعاً وجود دارد
if not SOURCE_ROOT.exists():
    print(f"❌ خطا: فولدر financial_system در این مسیر یافت نشد:")
    print(f"   {SOURCE_ROOT}")
    print("\nلطفاً این اسکریپت را در همان فولدری اجرا کنید که financial_system در آن است.")
    exit(1)

print(f"✅ ریشه‌ی پروژه شناسایی شد: {SCRIPT_DIR}")

# ---------- بقیه‌ی کد بدون تغییر ----------
FILES_TO_COPY = [
    "views/advanced_financial_chat.py",
    "agents/advanced/router_agent.py",
    "agents/financial_router.py",
    "core/langchain_tools.py",
    "core/financial_tools_manager.py",
    "tools/ai_classifier.py",
    "tools/financial_classifier.py",
    "tools/financial_analysis_tools.py",
    "tools/financial_ratio_tools.py",
    "tools/cash_flow_tools.py",
    "tools/fraud_detection_tools.py",
    "tools/integrity_compliance_tools.py",
    "tools/import_assistance_tools.py",
    "tools/accounting/balance_tool.py",
    "services/learning_system.py",
    "services/model_improvement.py",
    "services/intelligent_recommendations.py",
    "models/response_models.py",
    "models/base_models.py",
]

MAIN_FILES = {
    "__init__.py": 'default_app_config = "financial_ai_core.apps.FinancialAICoreConfig"\n',
    "apps.py": '''from django.apps import AppConfig

class FinancialAICoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'financial_ai_core'
    verbose_name = 'Financial AI Core'

    def ready(self):
        pass
''',
    "urls.py": '''from django.urls import path
from .views import advanced_chat_interface

urlpatterns = [
    path('advanced-chat/', advanced_chat_interface, name='advanced_chat'),
]
''',
    "views.py": '''import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .agents.router_agent import route_user_query

@csrf_exempt
@require_http_methods(["POST"])
def advanced_chat_interface(request):
    try:
        data = json.loads(request.body)
        user_query = data.get("query", "").strip()
        user_id = data.get("user_id")

        if not user_query:
            return JsonResponse({"error": "Query is required"}, status=400)

        response = route_user_query(user_query, context={"user_id": user_id})

        return JsonResponse({
            "response": response.get("answer"),
            "tool_used": response.get("tool"),
            "confidence": response.get("confidence")
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
''',
}

def replace_imports_in_file(file_path: Path):
    if not file_path.exists():
        return
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r'from\s+financial_system\.', 'from financial_ai_core.', content)
    content = re.sub(r'import\s+financial_system\.(\w+)', r'import financial_ai_core.\1', content)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def main():
    print("🚀 شروع استخراج ماژول financial_ai_core...")

    if TARGET_ROOT.exists():
        shutil.rmtree(TARGET_ROOT)
    ensure_dir(TARGET_ROOT)

    subdirs = {"agents", "core", "tools", "services", "models", "tools/accounting"}
    for d in subdirs:
        ensure_dir(TARGET_ROOT / d)

    for filename, content in MAIN_FILES.items():
        with open(TARGET_ROOT / filename, "w", encoding="utf-8") as f:
            f.write(content)
    print("✅ فایل‌های اصلی ایجاد شدند.")

    copied = 0
    for rel_path in FILES_TO_COPY:
        src = SOURCE_ROOT / rel_path
        dst = TARGET_ROOT / rel_path
        if src.exists():
            ensure_dir(dst.parent)
            shutil.copy2(src, dst)
            print(f"✅ کپی شد: {rel_path}")
            copied += 1
        else:
            print(f"⚠️  فایل یافت نشد: {rel_path}")

    if copied == 0:
        print("\n❌ هشدار: هیچ فایلی کپی نشد! احتمالاً ساختار متفاوت است.")
        print(f"لطفاً بررسی کن که {SOURCE_ROOT} شامل فایل‌های مورد نظر باشد.")
        return

    print("🔄 در حال به‌روزرسانی imports...")
    for py_file in TARGET_ROOT.rglob("*.py"):
        replace_imports_in_file(py_file)

    root_files = {
        "setup.py": '''from setuptools import setup, find_packages

setup(
    name="django-financial-ai-core",
    version="0.1.0",
    description="A reusable Django app for AI-powered financial analysis",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Adel",
    author_email="your.email@example.com",
    url="https://github.com/adeljavad/finance",
    license="MIT",
    packages=find_packages(include=["financial_ai_core", "financial_ai_core.*"]),
    include_package_data=True,
    install_requires=[
        "Django>=4.0",
        "langchain>=0.1.0",
        "langchain-core>=0.1.0",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Framework :: Django",
        "Programming Language :: Python :: 3",
    ],
)
''',
        "MANIFEST.in": '''include README.md
include LICENSE
recursive-include financial_ai_core *.py
''',
        "README.md": '''# Django Financial AI Core

ماژول هوش مالی پویا برای جنگو.
''',
        "LICENSE": "MIT License\\n\\nCopyright (c) 2025 Adel\\n\\nPermission is hereby granted..."
    }

    for filename, content in root_files.items():
        with open(SCRIPT_DIR / filename, "w", encoding="utf-8") as f:
            f.write(content)
    print("✅ فایل‌های ریشه‌ای ایجاد شدند.")

    print("\n🎉 ماژول financial_ai_core با موفقیت آماده شد!")
    print(f"محل ماژول: {TARGET_ROOT}")
    print("\nمراحل بعدی:")
    print(f"cd {SCRIPT_DIR}")
    print("pip install -e .")

if __name__ == "__main__":
    main()