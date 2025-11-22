# financial_system/tools/__init__.py
from .financial_analysis_tools import *

from .balance_tool import BalanceSheetTool

def load_tools():
    return {
        "balance_sheet": BalanceSheetTool(),
        # بقیه ابزارها را بعدا اضافه می‌کنیم
    }
