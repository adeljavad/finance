from langchain_core.tools import BaseTool


class BalanceSheetTool(BaseTool):
    name = "balance_sheet"
    description = "محاسبه و استخراج ترازنامه شرکت"

    def _run(self, company_id: int):
        # داده واقعی بعدا اضافه می‌کنیم
        return {
            "company_id": company_id,
            "assets": 1200000,
            "liabilities": 450000,
            "equity": 750000,
        }

    async def _arun(self, company_id: int):
        return self._run(company_id)
