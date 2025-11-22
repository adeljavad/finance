# create_project_summary.py
import os
from pathlib import Path

def generate_project_overview():
    """تولید خودکار فایل PROJECT_OVERVIEW.md بر اساس ساختار پروژه Django"""
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # شناسایی ساختار پروژه
    project_structure = analyze_django_structure(BASE_DIR)
    
    # تولید محتوای فایل
    content = generate_markdown_content(project_structure)
    
    # ذخیره فایل
    output_path = BASE_DIR / "PROJECT_OVERVIEW.md"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ فایل PROJECT_OVERVIEW.md در مسیر {output_path} ایجاد شد")
    return output_path

def analyze_django_structure(base_dir):
    """آنالیز ساختار پروژه Django"""
    
    structure = {
        "project_name": base_dir.name,
        "apps": [],
        "static_folders": [],
        "templates_folders": [],
        "media_folders": [],
        "requirements": [],
        "settings_files": [],
        "url_files": [],
        "model_files": [],
        "view_files": [],
        "management_commands": []
    }
    
    for item in base_dir.iterdir():
        if item.is_dir():
            if (item / "apps.py").exists() or (item / "models.py").exists():
                structure["apps"].append({
                    "name": item.name,
                    "models": list_models_in_app(item),
                    "views": list_views_in_app(item),
                    "urls": (item / "urls.py").exists(),
                    "migrations": (item / "migrations").exists(),
                    "tests": (item / "tests.py").exists() or (item / "tests").exists()
                })

            if item.name in ["static", "assets"]:
                structure["static_folders"].append(item.name)

            if item.name in ["templates", "template"]:
                structure["templates_folders"].append(item.name)

            if item.name == "media":
                structure["media_folders"].append(item.name)

    req_files = ["requirements.txt", "requirements-dev.txt", "pyproject.toml", "Pipfile"]
    for req_file in req_files:
        if (base_dir / req_file).exists():
            structure["requirements"].append(req_file)

    settings_dir = base_dir / structure["project_name"]
    if settings_dir.exists():
        for settings_file in settings_dir.glob("settings*.py"):
            structure["settings_files"].append(settings_file.name)

    if (base_dir / "urls.py").exists():
        structure["url_files"].append("urls.py")
    project_urls = base_dir / structure["project_name"] / "urls.py"
    if project_urls.exists():
        structure["url_files"].append(f"{structure['project_name']}/urls.py")

    return structure

def list_models_in_app(app_dir):
    models = []
    models_file = app_dir / "models.py"
    if models_file.exists():
        models.append("models.py")

    models_dir = app_dir / "models"
    if models_dir.exists():
        for model_file in models_dir.glob("*.py"):
            if model_file.name != "__init__.py":
                models.append(f"models/{model_file.name}")
    return models

def list_views_in_app(app_dir):
    views = []
    views_file = app_dir / "views.py"
    if views_file.exists():
        views.append("views.py")

    views_dir = app_dir / "views"
    if views_dir.exists():
        for view_file in views_dir.glob("*.py"):
            if view_file.name != "__init__.py":
                views.append(f"views/{view_file.name}")

    api_file = app_dir / "api.py"
    if api_file.exists():
        views.append("api.py")

    return views


def generate_markdown_content(structure: dict) -> str:
    nl = "\n"                       # newline
    indent = "    "                 # 4-space برای هر سطح

    # --- بخش هدر ---
    header = f"""# 📊 پروژه {structure['project_name']} - تحلیل کلی

    ## 🎯 هدف پروژه
    دستیار هوشمند مالی و حسابرسی با قابلیت تحلیل خودکار داده‌های مالی و پاسخ به سوالات تخصصی

    ## 🏗️ معماری فنی
    ### تکنولوژی‌های اصلی
    - **Backend Framework**: Django
    - **Database**: SQL Server
    - **AI/ML**: LangChain + DeepSeek + Scikit-learn
    - **Authentication**: Google OAuth + django-allauth
    - **Data Processing**: Pandas + Openpyxl + xlrd

    ### ساختار پروژه
    {structure['project_name']}/
    """
        # --- تنظیمات اصلی پروژه ---
    header += f"{indent}📁 {structure['project_name']}/\n"
    for sf in structure['settings_files']:
        header += f"{indent*2}⚙️  {sf}\n"
    for uf in structure['url_files']:
        header += f"{indent*2}🔗 {uf}\n"

    # --- اپلیکیشن‌ها ---
    if structure["apps"]:
        header += f"{indent}📁 Applications/\n"
        for app in structure["apps"]:
            header += f"{indent*2}📁 {app['name']}/\n"
            if app["models"]:
                header += f"{indent*3}🗂️  Models: {', '.join(app['models'])}\n"
            if app["views"]:
                header += f"{indent*3}🖥️  Views: {', '.join(app['views'][:3])}{' ...' if len(app['views'])>3 else ''}\n"
            if app["urls"]:
                header += f"{indent*3}🔗 urls.py\n"
            if app["migrations"]:
                header += f"{indent*3}📦 migrations/\n"
            if app["tests"]:
                header += f"{indent*3}✅ tests.py\n"

    # --- پوشه‌های static، templates، media ---
    for folder in structure["static_folders"]:
        header += f"{indent}📁 {folder}/\n"
    for folder in structure["templates_folders"]:
        header += f"{indent}📁 {folder}/\n"
    for folder in structure["media_folders"]:
        header += f"{indent}📁 {folder}/\n"

    # --- فایل‌های Requirements ---
    if structure["requirements"]:
        header += f"{indent}📄 {', '.join(structure['requirements'])}\n"

    header += "\n```\n\n## 📈 وضعیت توسعه\nدر حال توسعه اولیه و تحلیل ساختار برای هوش مصنوعی.\n"
    return header.strip()




        # اجرای اسکریپت
if __name__ == "__main__":
    generate_project_overview()