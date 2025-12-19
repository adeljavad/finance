# financial_system/core/financial_tools_manager.py
class FinancialToolsManager:
    def __init__(self):
        self.tools = {}
        self.setup_all_tools()
    
    def setup_all_tools(self):
        """راه‌اندازی تمام ابزارهای مالی"""
        # import کردن تمام آنالایزرها برای ثبت خودکار
        from ..analyzers.current_assets_analyzer import CurrentAssetsAnalyzer
        from ..analyzers.current_liabilities_analyzer import CurrentLiabilitiesAnalyzer
        from ..analyzers.equity_analyzer import EquityAnalyzer
        from ..analyzers.balance_sheet_analyzer import BalanceSheetAnalyzer
        
        print(f"🎯 {len(FINANCIAL_TOOLS)} ابزار مالی فعال شد:")
        for tool_name in FINANCIAL_TOOLS.keys():
            print(f"   📊 {tool_name}")
    
    def get_tool(self, tool_name: str):
        """دریافت یک ابزار خاص"""
        return FINANCIAL_TOOLS.get(tool_name)
    
    def get_all_tools(self):
        """دریافت تمام ابزارها"""
        return list(FINANCIAL_TOOLS.values())
    
    def execute_financial_analysis(self, tool_name: str, **kwargs):
        """اجرای تحلیل مالی"""
        tool = self.get_tool(tool_name)
        if tool:
            return tool._run(**kwargs)
        else:
            return f"ابزار {tool_name} یافت نشد"