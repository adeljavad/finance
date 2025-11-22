# 📊 پروژه finance - تحلیل کلی

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
    finance/
        📁 finance/
    📁 Applications/
        📁 coding_manager/
            🗂️  Models: models.py
            🖥️  Views: views.py
            📦 migrations/
            ✅ tests.py
        📁 data_importer/
            🗂️  Models: models.py
            🖥️  Views: views.py
            📦 migrations/
            ✅ tests.py
        📁 dynamicFrm/
            🗂️  Models: models.py
            🖥️  Views: views.py
            🔗 urls.py
            📦 migrations/
        📁 financial_system/
            🗂️  Models: models.py, models/base_models.py, models/coding_models.py, models/document_models.py, models/software_mapping.py, models/transaction_models.py
            🖥️  Views: views.py, views/financial_chat.py
            📦 migrations/
            ✅ tests.py
        📁 itapp/
            🗂️  Models: models.py
            🖥️  Views: views.py
            🔗 urls.py
            📦 migrations/
            ✅ tests.py
        📁 jobApp/
            🗂️  Models: models.py
            🖥️  Views: views.py
            🔗 urls.py
            📦 migrations/
            ✅ tests.py
        📁 tblApp/
            🗂️  Models: models.py
            🖥️  Views: views.py
            🔗 urls.py
            📦 migrations/
            ✅ tests.py
        📁 users/
            🗂️  Models: models.py
            🖥️  Views: views.py
            🔗 urls.py
            📦 migrations/
            ✅ tests.py
    📁 static/
    📁 templates/
    📁 media/
    📄 requirements.txt

```

## 📈 وضعیت توسعه
در حال توسعه اولیه و تحلیل ساختار برای هوش مصنوعی.