"""
Custom database backend for SQL Server that uses the exact connection string format that works.
"""
import pyodbc
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.client import BaseDatabaseClient
from django.db.backends.base.creation import BaseDatabaseCreation
from django.db.backends.base.introspection import BaseDatabaseIntrospection
from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.backends.base.validation import BaseDatabaseValidation


class DatabaseWrapper(BaseDatabaseWrapper):
    vendor = 'microsoft'
    display_name = 'SQL Server'

    def get_connection_params(self):
        settings_dict = self.settings_dict
        return {
            'driver': settings_dict['OPTIONS'].get('driver', 'ODBC Driver 17 for SQL Server'),
            'server': settings_dict.get('HOST', 'DESKTOP-IVONUCU\\SQL22'),
            'database': settings_dict.get('NAME', 'chatbot'),
            'trusted_connection': 'yes',
            'trustservercertificate': 'yes',
        }

    def get_new_connection(self, conn_params):
        connection_string = (
            f"DRIVER={{{conn_params['driver']}}};"
            f"SERVER={conn_params['server']};"
            f"DATABASE={conn_params['database']};"
            f"Trusted_Connection={conn_params['trusted_connection']};"
            f"TrustServerCertificate={conn_params['trustservercertificate']};"
        )
        return pyodbc.connect(connection_string)

    def init_connection_state(self):
        pass

    def create_cursor(self, name=None):
        return self.connection.cursor()

    def _set_autocommit(self, autocommit):
        self.connection.autocommit = autocommit

    def is_usable(self):
        try:
            self.connection.cursor().execute("SELECT 1")
        except Exception:
            return False
        return True

    def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None


class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = "django.db.backends.sql_server.compiler"


class DatabaseIntrospection(BaseDatabaseIntrospection):
    pass


class DatabaseClient(BaseDatabaseClient):
    pass


class DatabaseCreation(BaseDatabaseCreation):
    pass


class DatabaseValidation(BaseDatabaseValidation):
    pass
