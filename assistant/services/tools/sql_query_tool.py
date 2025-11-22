from django.db import connection

def run_sql(query, params=None):
    params = params or []
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        cols = [c[0] for c in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        result = [dict(zip(cols, r)) for r in rows]
        return result
