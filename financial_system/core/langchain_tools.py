# financial_system/core/langchain_tools.py
from typing import Dict, Any
import json

try:
    # Try different import patterns for different LangChain versions
    try:
        from langchain.tools import tool
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        try:
            from langchain.agents import tool
            LANGCHAIN_AVAILABLE = True
        except ImportError:
            try:
                from langchain_core.tools import tool
                LANGCHAIN_AVAILABLE = True
            except ImportError:
                LANGCHAIN_AVAILABLE = False
                print("⚠️ LangChain نصب نیست - از نسخه جایگزین استفاده می‌شود")
except Exception as e:
    LANGCHAIN_AVAILABLE = False
    print(f"⚠️ خطا در بارگذاری LangChain: {e} - از نسخه جایگزین استفاده می‌شود")

# ثبت تمام ابزارهای مالی در یک دیکشنری مرکزی
FINANCIAL_TOOLS: Dict[str, Any] = {}

def register_financial_tool(name: str, description: str):
    """ثبت ابزار مالی در سیستم LangChain"""
    def decorator(func):
        if LANGCHAIN_AVAILABLE:
            try:
                # روش ۱: نسخه جدید LangChain
                tool_instance = tool(description=description)(func)
                tool_instance.name = name  # تنظیم نام جداگانه
                FINANCIAL_TOOLS[name] = tool_instance
            except TypeError:
                try:
                    # روش ۲: نسخه قدیمی LangChain
                    tool_instance = tool(name=name, description=description)(func)
                    FINANCIAL_TOOLS[name] = tool_instance
                except Exception as e:
                    print(f"⚠️ خطا در ثبت ابزار {name}: {e}")
                    # روش ۳: استفاده از تابع اصلی
                    FINANCIAL_TOOLS[name] = func
        else:
            # اگر LangChain نصب نیست، تابع اصلی را برگردان
            FINANCIAL_TOOLS[name] = func
        
        return func
    return decorator

def get_all_financial_tools():
    """دریافت تمام ابزارهای مالی ثبت شده"""
    if not FINANCIAL_TOOLS:
        setup_financial_tools()
    return list(FINANCIAL_TOOLS.values())

def setup_financial_tools():
    """راه‌اندازی و ثبت تمام ابزارهای مالی"""
    try:
        # import کردن تمام ماژول‌های حاوی ابزارها برای ثبت خودکار
        from ..tools import financial_analysis_tools
        from ..tools import comparison_tools
        
        print(f"✅ {len(FINANCIAL_TOOLS)} ابزار مالی برای LangChain بارگذاری شد")
        
        for tool_name in FINANCIAL_TOOLS.keys():
            tool_obj = FINANCIAL_TOOLS[tool_name]
            if hasattr(tool_obj, 'name'):
                print(f"  - {tool_obj.name}")
            else:
                print(f"  - {tool_name}")
        
        return FINANCIAL_TOOLS
        
    except ImportError as e:
        print(f"⚠️ خطا در بارگذاری تحلیل‌گرها: {e}")
        return {}

def execute_tool(tool_name: str, **kwargs) -> Any:
    """اجرای یک ابزار مالی"""
    if tool_name not in FINANCIAL_TOOLS:
        raise ValueError(f"ابزار {tool_name} یافت نشد")
    
    tool_func = FINANCIAL_TOOLS[tool_name]
    
    try:
        # روش ساده: مستقیماً تابع اصلی را فراخوانی کنیم
        # این روش از تمام خطاهای مربوط به self و tool_input جلوگیری می‌کند
        if hasattr(tool_func, 'func'):
            # اگر تابع اصلی در دسترس است، مستقیماً فراخوانی کنیم
            return tool_func.func(**kwargs)
        else:
            # اگر تابع اصلی در دسترس نیست، سعی کنیم از روش‌های دیگر استفاده کنیم
            # اولویت: فراخوانی مستقیم
            try:
                return tool_func(**kwargs)
            except Exception as e1:
                # اگر خطای self داریم، سعی کنیم از _run استفاده کنیم
                if "missing 1 required positional argument: 'self'" in str(e1):
                    if hasattr(tool_func, '_run'):
                        return tool_func._run(**kwargs)
                    elif hasattr(tool_func, 'run'):
                        return tool_func.run(**kwargs)
                    else:
                        raise
                else:
                    raise
                
    except Exception as e:
        # لاگ خطا برای دیباگ
        print(f"❌ خطا در اجرای ابزار {tool_name}: {e}")
        raise
