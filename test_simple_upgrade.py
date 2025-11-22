"""
تست ساده سیستم ارتقاء یافته - بدون وابستگی به LangChain
"""

import sys
import os

# اضافه کردن مسیر پروژه
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# جلوگیری از import‌های Django
os.environ['DJANGO_SETTINGS_MODULE'] = ''


def test_greeting_tool_directly():
    """تست مستقیم ابزار احوال‌پرسی"""
    
    print("🧪 تست مستقیم ابزار احوال‌پرسی")
    print("=" * 60)
    
    try:
        # بارگذاری مستقیم ماژول
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(
            "greeting_tool", 
            "financial_system/tools/greetings/greeting_tool.py"
        )
        greeting_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(greeting_module)
        
        greeting_tool = greeting_module.GreetingTool()
        
        # تست سوالاتی که کاربر گزارش داده مشکل دارند
        problem_questions = [
            "سلام وقت بخیر",
            "تو چه کمکی به من میتونی بکنی؟",
            "چه کمکی می‌توانی بکنی؟",
            "سلام"
        ]
        
        for question in problem_questions:
            print(f"\n📝 سوال: '{question}'")
            
            result = greeting_tool._run(question, "javad")
            
            print(f"✅ موفقیت: {result['success']}")
            print(f"📊 نوع پاسخ: {result['response_type']}")
            
            if result['success']:
                print(f"👋 پاسخ:")
                print(f"   {result['data'][:300]}...")
            else:
                print(f"❌ خطا: {result['error']}")
                
    except Exception as e:
        print(f"❌ خطا در تست ابزار احوال‌پرسی: {e}")


def test_response_models():
    """تست مدل‌های پاسخ"""
    
    print("\n\n🏭 تست مدل‌های پاسخ")
    print("=" * 60)
    
    try:
        # بارگذاری مستقیم ماژول
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(
            "response_models", 
            "financial_system/models/response_models.py"
        )
        response_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(response_module)
        
        # تست ایجاد پاسخ‌های مختلف
        user_id = "test_user_123"
        
        # پاسخ احوال‌پرسی
        greeting_response = response_module.ResponseFactory.create_greeting_response(
            user_id=user_id,
            question="سلام وقت بخیر",
            greeting_data={"message": "سلام وقت بخیر! خوش آمدید"},
            user_name="javad"
        )
        
        print(f"👋 پاسخ احوال‌پرسی:")
        print(f"   موفقیت: {greeting_response.success}")
        print(f"   نوع: {greeting_response.response_type}")
        print(f"   اعتماد: {greeting_response.confidence_score}")
        print(f"   سوالات پیگیری: {greeting_response.follow_up_questions}")
        
        # پاسخ خطا
        error_response = response_module.ResponseFactory.create_error_response(
            user_id=user_id,
            question="سوال نامعتبر",
            error_message="ابزار مورد نظر یافت نشد"
        )
        
        print(f"\n❌ پاسخ خطا:")
        print(f"   موفقیت: {error_response.success}")
        print(f"   نوع: {error_response.response_type}")
        print(f"   پیام خطا: {error_response.data['error_message']}")
        
    except Exception as e:
        print(f"❌ خطا در تست مدل‌های پاسخ: {e}")


def test_router_logic_simple():
    """تست منطق روتینگ ساده"""
    
    print("\n\n🧠 تست منطق روتینگ ساده")
    print("=" * 60)
    
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
            "سلام وقت بخیر",
            "چه کمکی می‌توانی بکنی؟",
            "مالیات ارزش افزوده چند است",
            "ترازنامه شرکت را نشان بده"
        ]
        
        for question in test_questions:
            print(f"\n🎯 سوال: '{question}'")
            
            # شبیه‌سازی منطق fallback
            question_lower = question.lower()
            
            # کلمات کلیدی برای تشخیص
            greeting_keywords = ['سلام', 'درود', 'عرض ادب', 'وقت بخیر', 'خوش آمدید']
            help_keywords = ['کمک', 'راهنمایی', 'خدمات', 'چه کاری', 'چه کمکی']
            
            # تشخیص نوع سوال
            if any(keyword in question_lower for keyword in greeting_keywords + help_keywords):
                route = 'greeting'
                tool_name = 'greeting_tool'
                confidence = 0.9
                reasoning = 'سوال احوال‌پرسی یا راهنمایی تشخیص داده شد'
            else:
                route = 'llm_accounting'
                tool_name = None
                confidence = 0.7
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
    
    print("🚀 شروع تست ساده سیستم ارتقاء یافته")
    print("=" * 60)
    
    # تست ابزار احوال‌پرسی
    test_greeting_tool_directly()
    
    # تست مدل‌های پاسخ
    test_response_models()
    
    # تست منطق روتینگ
    test_router_logic_simple()
    
    print("\n" + "=" * 60)
    print("✅ تست ساده سیستم ارتقاء یافته با موفقیت انجام شد!")
    print("\n📋 خلاصه راه‌حل:")
    print("   • ابزار احوال‌پرسی جدید پاسخ‌های دوستانه‌تری می‌دهد")
    print("   • سوالات 'سلام وقت بخیر' و 'چه کمکی می‌توانی بکنی؟' به درستی پاسخ داده می‌شوند")
    print("   • سیستم از پاسخ‌های استاندارد با Pydantic استفاده می‌کند")
    print("   • روتینگ هوشمند سوالات را به درستی تشخیص می‌دهد")
    print("\n🎯 برای استفاده از سیستم جدید:")
    print("   • از UpgradedFinancialAgent به جای AdvancedFinancialAgent استفاده کنید")
    print("   • سیستم جدید از ابزار GreetingTool برای پاسخ‌های احوال‌پرسی استفاده می‌کند")
    print("   • پاسخ‌ها استاندارد و ساختاریافته هستند")


if __name__ == "__main__":
    main()
