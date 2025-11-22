from .ledger_tool import ledger_summary

def generate_trial_balance(period: str = None):
    # In a real app, query DB for all accounts in period. Here we return a sample structure or call ledger_summary in a loop.
    # For MVP we'll return a placeholder
    sample = {
        'period': period or '2025-10',
        'accounts': [
            {'code': '101', 'title': 'صندوق', 'debit': 100000, 'credit': 0},
            {'code': '201', 'title': 'حسابهای پرداختنی', 'debit': 0, 'credit': 40000},
            {'code': '301', 'title': 'موجودی کالا', 'debit': 50000, 'credit': 0}
        ]
    }
    return sample
