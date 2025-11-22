# financial_system/routers.py
class FinancialRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'financial_system':
            return 'financial_db'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'financial_system':
            return 'financial_db'
        return None