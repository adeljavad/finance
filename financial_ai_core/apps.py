from django.apps import AppConfig

class FinancialAICoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'financial_ai_core'
    verbose_name = 'Financial AI Core'

    def ready(self):
        pass
