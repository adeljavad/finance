from django.db import connection

def ledger_summary(account_code: str, date_from: str = None, date_to: str = None):
    # Lightweight and safe SQL using parameters
    with connection.cursor() as cursor:
        sql = """SELECT COALESCE(SUM(debit),0) as total_debit, COALESCE(SUM(credit),0) as total_credit
                 FROM ledger
                 WHERE account_code = %s
              """
        params = [account_code]
        cursor.execute(sql, params)
        row = cursor.fetchone()
        total_debit, total_credit = row
        balance = total_debit - total_credit
        return {'account_code': account_code, 'total_debit': float(total_debit), 'total_credit': float(total_credit), 'balance': float(balance)}
