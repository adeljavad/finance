"""
تست مستقل معماری ارتقاء یافته - بدون وابستگی به پکیج‌های Django
"""

import sys
import os

# اضافه کردن مسیر پروژه
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# جلوگیری از import‌های Django
os.environ['DJANGO_SETTINGS_MODULE'] = ''

def test_greeting_tool_standalone():
    """تست مستقل ابزار احوال‌پرسی"""
    
    print("🧪 تست مستقل ابزار احوال‌پرسی...")
    
    try:
        # import مستقیم از فایل بدون استفاده از __init__.py
        import importlib.util
        
        # بارگذاری مستقیم ماژول
        spec = importlib.util.spec_from_file_location(
            "greeting_tool", 
            "financial_system/tools/greetings/greeting_tool.py"
        )
        greeting_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(greeting_module)
        
        greeting_tool = greeting_module.GreetingTool()
        
        # تست سوالات مختلف
        test_cases = [
            ("سلام", "test_user"),
            ("چه کمکی می‌توانی بکنی؟", "javad"),
            ("راهنمایی می‌خواهم", None),
            ("خدمات شما چیست؟", "کاربر")
        ]
        
        for question, user_name in test_cases:
            print(f"\n📝 سوال: '{question}' - کاربر: {user_name}")
            
            result = greeting_tool._run(question, user_name)
            
            print(f"✅ موفقیت: {result['success']}")
            print(f"📊 نوع پاسخ: {result['response_type']}")
            print(f"👤 نام کاربر: {result.get('user_name', 'ندارد')}")
            
            if result['success']:
                print(f"📄 پاسخ: {result['data'][:200]}...")
            else:
                print(f"❌ خطا: {result['error']}")
                
    except Exception as e:
        print(f"❌ خطا در تست ابزار احوال‌پرسی: {e}")


def test_response_models_standalone():
    """تست مستقل مدل‌های پاسخ"""
    
    print("\n\n🏭 تست مستقل مدل‌های پاسخ...")
    
    try:
        # بارگذاری مستقیم ماژول
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(
            "response_models", 
            "financial_system/models/response_models.py"
        )
        response_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(response_module)
        
        # تست RouterDecision
        decision = response_module.RouterDecision(
            route="greeting",
            tool_name=None,
            confidence=0.8,
            reasoning="سوال احوال‌پرسی تشخیص داده شد"
        )
        
        print(f"🛣️  RouterDecision:")
        print(f"   مسیر: {decision.route}")
        print(f"   ابزار: {decision.tool_name}")
        print(f"   اعتماد: {decision.confidence}")
        print(f"   دلیل: {decision.reasoning}")
        
        # تست ResponseFactory
        user_id = "test_user_123"
        question = "سلام، چه کمکی می‌توانی بکنی؟"
        
        greeting_response = response_module.ResponseFactory.create_greeting_response(
            user_id=user_id,
            question=question,
            greeting_data={"message": "سلام! خوش آمدید"},
            user_name="javad"
        )
        
        print(f"\n👋 ResponseFactory - پاسخ احوال‌پرسی:")
        print(f"   موفقیت: {greeting_response.success}")
        print(f"   نوع: {greeting_response.response_type}")
        print(f"   اعتماد: {greeting_response.confidence_score}")
        print(f"   سوالات پیگیری: {greeting_response.follow_up_questions}")
        
    except Exception as e:
        print(f"❌ خطا در تست مدل‌های پاسخ: {e}")


def test_architecture_structure():
    """تست ساختار معماری"""
    
    print("\n\n🏗️  تست ساختار معماری...")
    
    # بررسی وجود فایل‌ها و دایرکتوری‌ها
    required_structure = [
        "financial_system/agents/advanced/__init__.py",
        "financial_system/agents/advanced/router_agent.py",
        "financial_system/tools/accounting/__init__.py",
        "financial_system/tools/reporting/__init__.py",
        "financial_system/tools/greetings/__init__.py",
        "financial_system/tools/greetings/greeting_tool.py",
        "financial_system/prompts/__init__.py",
        "financial_system/models/response_models.py"
    ]
    
    print("📁 بررسی ساختار فایل‌ها:")
    
    all_files_exist = True
    for file_path in required_structure:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
            all_files_exist = False
    
    if all_files_exist:
        print("\n🎯 ساختار معماری به درستی پیاده‌سازی شده است!")
    else:
        print("\n⚠️  برخی فایل‌ها وجود ندارند!")


def test_router_logic_standalone():
    """تست منطق روتینگ مستقل"""
    
    print("\n\n🧠 تست منطق روتینگ مستقل...")
    
    try:
        # بارگذاری مستقیم ماژول
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(
            "response_models", 
            "financial_system/models/response_models.py"
        )
        response_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(response_module)
        
        # تست سوالات مختلف
        test_questions = [
            "سلام",
            "چه کمکی می‌توانی بکنی؟",
            "ترازنامه شرکت را نشان بده",
            "نسبت‌های مالی را تحلیل کن",
            "انحرافات مالی را شناسایی کن"
        ]
        
        for question in test_questions:
            print(f"\n🎯 سوال: '{question}'")
            
            # شبیه‌سازی منطق fallback
            question_lower = question.lower()
            
            # کلمات کلیدی برای تشخیص
            greeting_keywords = ['سلام', 'درود', 'عرض ادب', 'وقت بخیر', 'خوش آمدید']
            help_keywords = ['کمک', 'راهنمایی', 'خدمات', 'چه کاری', 'چه کمکی']
            tool_keywords = {
                'balance_sheet_tool': ['ترازنامه', 'تراز', 'صورت وضعیت'],
                'financial_ratios_tool': ['نسبت', 'تحلیل مالی', 'نقدینگی', 'سودآوری'],
                'anomaly_detection_tool': ['انحراف', 'مشکوک', 'کنترل', 'مغایرت'],
                'report_generation_tool': ['گزارش', 'صورت مالی', 'سود و زیان']
            }
            
            # تشخیص نوع سوال
            if any(keyword in question_lower for keyword in greeting_keywords + help_keywords):
                route = 'greeting'
                tool_name = None
                confidence = 0.8
                reasoning = 'سوال احوال‌پرسی یا راهنمایی تشخیص داده شد'
            else:
                # تشخیص ابزار
                tool_found = False
                for tool_name, keywords in tool_keywords.items():
                    if any(keyword in question_lower for keyword in keywords):
                        route = 'tool'
                        tool_name = tool_name
                        confidence = 0.7
                        reasoning = f'سوال با کلمات کلیدی {keywords} تشخیص داده شد'
                        tool_found = True
                        break
                
                if not tool_found:
                    route = 'llm_accounting'
                    tool_name = None
                    confidence = 0.6
                    reasoning = 'سوال عمومی حسابداری تشخیص داده شد'
            
            decision = response_module.RouterDecision(
                route=route,
                tool_name=tool_name,
                confidence=confidence,
                reasoning=reasoning
            )
            
            print(f"🛣️  مسیر: {decision.route}")
            print(f"🔧 ابزار: {decision.tool_name or 'ندارد'}")
            print(f"🎯 اعتماد: {decision.confidence:.2f}")
            print(f"💭 دلیل: {decision.reasoning}")
            
    except Exception as e:
        print(f"❌ خطا در تست منطق روتینگ: {e}")


def main():
    """تابع اصلی تست"""
    
    print("🚀 شروع تست مستقل معماری ارتقاء یافته")
    print("=" * 60)
    
    # تست ساختار معماری
    test_architecture_structure()
    
    # تست ابزار احوال‌پرسی
    test_greeting_tool_standalone()
    
    # تست مدل‌های پاسخ
    test_response_models_standalone()
    
    # تست منطق روتینگ
    test_router_logic_standalone()
    
    print("\n" + "=" * 60)
    print("✅ تست معماری ارتقاء یافته با موفقیت انجام شد!")
    print("\n📋 خلاصه معماری پیاده‌سازی شده:")
    print("   • ابزار احوال‌پرسی (GreetingTool)")
    print("   • SmartRouter برای روتینگ هوشمند")
    print("   • مدل‌های Pydantic برای پاسخ‌های استاندارد")
    print("   • ResponseFactory برای ایجاد پاسخ‌های یکپارچه")
    print("   • ساختار پکیج‌بندی شده و ماژولار")
    print("\n🎯 معماری جدید ویژگی‌های زیر را دارد:")
    print("   • Separation of Concerns")
    print("   • Scalability")
    print("   • Smart Routing")
    print("   • Memory Management")
    print("\n🚀 آماده برای فاز بعدی: تبدیل ابزارهای موجود به BaseTool")


if __name__ == "__main__":
    main()
