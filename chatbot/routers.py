class SchemaRouter:
    def db_for_read(self, model, **hints):
        if model._meta.db_table.startswith('inf.'):
            return 'inf'
        elif model._meta.db_table.startswith('log.'):
            return 'log'
        elif model._meta.db_table.startswith('tbl.'):
            return 'tbl'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.db_table.startswith('inf.'):
            return 'inf'
        elif model._meta.db_table.startswith('log.'):
            return 'log'
        elif model._meta.db_table.startswith('tbl.'):
            return 'tbl'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True