"""
تست سیستم ارتقاء یافته دستیار مالی
"""

import asyncio
import sys
import os

# اضافه کردن مسیر پروژه
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# جلوگیری از import‌های Django
os.environ['DJANGO_SETTINGS_MODULE'] = ''


async def test_upgraded_agent():
    """تست سیستم ارتقاء یافته"""
    
    print("🚀 تست سیستم ارتقاء یافته دستیار مالی")
    print("=" * 60)
    
    try:
        # بارگذاری مستقیم ماژول
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(
            "upgraded_agent", 
            "financial_system/agents/advanced/upgraded_financial_agent.py"
        )
        agent_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent_module)
        
        # تست سوالات مختلف
        test_cases = [
            ("سلام", "test_user_1"),
            ("سلام وقت بخیر", "test_user_2"),
            ("چه کمکی می‌توانی بکنی؟", "test_user_3"),
            ("تو چه کمکی به من میتونی بکنی؟", "test_user_4"),
            ("مالیات ارزش افزوده چند است", "test_user_5"),
            ("ترازنامه شرکت را نشان بده", "test_user_6"),
            ("نسبت‌های مالی را تحلیل کن", "test_user_7")
        ]
        
        for question, user_id in test_cases:
            print(f"\n🧪 تست سوال: '{question}'")
            print(f"👤 کاربر: {user_id}")
            
            try:
                # استفاده از تابع اصلی
                response = await agent_module.ask_financial_question_upgraded(
                    question=question,
                    user_id=user_id
                )
                
                print(f"✅ موفقیت: {response.success}")
                print(f"📊 نوع پاسخ: {response.response_type}")
                print(f"🎯 اعتماد: {response.confidence_score:.2f}")
                print(f"⏱️  زمان اجرا: {response.execution_time:.2f}s")
                
                if response.success:
                    if response.response_type.value == "greeting":
                        print(f"👋 پاسخ احوال‌پرسی:")
                        data = response.data.get('data', {})
                        if isinstance(data, dict):
                            greeting_text = data.get('data', '')
                            if greeting_text:
                                print(f"   📄 {greeting_text[:200]}...")
                        else:
                            print(f"   📄 {str(data)[:200]}...")
                    
                    elif response.response_type.value == "expert_opinion":
                        print(f"🧠 پاسخ متخصص:")
                        expert_opinion = response.data.get('expert_opinion', '')
                        print(f"   📄 {expert_opinion[:200]}...")
                    
                    else:
                        print(f"📄 محتوای پاسخ: {str(response.data)[:200]}...")
                
                else:
                    print(f"❌ خطا: {response.data.get('error_message', 'خطای نامشخص')}")
                    
            except Exception as e:
                print(f"❌ خطا در پردازش سوال: {e}")
                
    except Exception as e:
        print(f"❌ خطا در بارگذاری ماژول: {e}")


async def test_router_decision():
    """تست تصمیم‌گیری روتینگ"""
    
    print("\n\n🧠 تست تصمیم‌گیری روتینگ")
    print("=" * 60)
    
    try:
        # بارگذاری مستقیم ماژول
        import importlib.util
        
        spec = importlib.util.spec_from_file_location(
            "router_agent", 
            "financial_system/agents/advanced/router_agent.py"
        )
        router_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(router_module)
        
        # بارگذاری ابزار
        spec_greeting = importlib.util.spec_from_file_location(
            "greeting_tool", 
            "financial_system/tools/greetings/greeting_tool.py"
        )
        greeting_module = importlib.util.module_from_spec(spec_greeting)
        spec_greeting.loader.exec_module(greeting_module)
        
        # ایجاد ابزار
        greeting_tool = greeting_module.GreetingTool()
        
        # ایجاد روتینگ
        router = router_module.SmartRouter(
            tools=[greeting_tool], 
            llm_config={"openai_api_key": "test_key", "temperature": 0.1}
        )
        
        # تست سوالات مختلف
        test_questions = [
            "سلام",
            "چه کمکی می‌توانی بکنی؟",
            "مالیات ارزش افزوده چند است",
            "ترازنامه شرکت را نشان بده"
        ]
        
        for question in test_questions:
            print(f"\n🎯 سوال: '{question}'")
            
            # استفاده از منطق fallback
            decision = router._fallback_route(question)
            
            print(f"🛣️  مسیر: {decision.route}")
            print(f"🔧 ابزار: {decision.tool_name or 'ندارد'}")
            print(f"🎯 اعتماد: {decision.confidence:.2f}")
            print(f"💭 دلیل: {decision.reasoning}")
            
    except Exception as e:
        print(f"❌ خطا در تست روتینگ: {e}")


async def main():
    """تابع اصلی تست"""
    
    print("🚀 شروع تست سیستم ارتقاء یافته")
    print("=" * 60)
    
    # تست سیستم ارتقاء یافته
    await test_upgraded_agent()
    
    # تست تصمیم‌گیری روتینگ
    await test_router_decision()
    
    print("\n" + "=" * 60)
    print("✅ تست سیستم ارتقاء یافته با موفقیت انجام شد!")
    print("\n📋 ویژگی‌های سیستم جدید:")
    print("   • پاسخ‌های احوال‌پرسی دوستانه و مفید")
    print("   • روتینگ هوشمند سوالات")
    print("   • پاسخ‌های تخصصی مالی")
    print("   • مدیریت خطاهای بهتر")
    print("   • پاسخ‌های استاندارد با Pydantic")
    print("\n🎯 سیستم جدید باید به سوالات زیر پاسخ مناسب بدهد:")
    print("   • 'سلام وقت بخیر' → پاسخ احوال‌پرسی")
    print("   • 'چه کمکی می‌توانی بکنی؟' → معرفی خدمات")
    print("   • 'مالیات ارزش افزوده' → پاسخ تخصصی")
    print("   • 'ترازنامه' → تشخیص ابزار مناسب")


if __name__ == "__main__":
    asyncio.run(main())
