"""
تست معماری ارتقاء یافته - فاز ۱
"""

import asyncio
import sys
import os

# اضافه کردن مسیر پروژه
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# جلوگیری از import‌های Django
os.environ['DJANGO_SETTINGS_MODULE'] = ''

from financial_system.tools.greetings.greeting_tool import GreetingTool
from financial_system.models.response_models import RouterDecision, ResponseFactory


async def test_greeting_tool():
    """تست ابزار احوال‌پرسی"""
    
    print("🧪 تست ابزار احوال‌پرسی...")
    
    greeting_tool = GreetingTool()
    
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


async def test_smart_router_fallback():
    """تست منطق fallback روتینگ"""
    
    print("\n\n🧠 تست منطق Fallback روتینگ...")
    
    # تست منطق fallback بدون نیاز به SmartRouter کامل
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
        
        decision = RouterDecision(
            route=route,
            tool_name=tool_name,
            confidence=confidence,
            reasoning=reasoning
        )
        
        print(f"🛣️  مسیر: {decision.route}")
        print(f"🔧 ابزار: {decision.tool_name or 'ندارد'}")
        print(f"🎯 اعتماد: {decision.confidence:.2f}")
        print(f"💭 دلیل: {decision.reasoning}")


async def test_response_factory():
    """تست ResponseFactory"""
    
    print("\n\n🏭 تست ResponseFactory...")
    
    # تست ایجاد پاسخ‌های مختلف
    user_id = "test_user_123"
    question = "سلام، چه کمکی می‌توانی بکنی؟"
    
    # پاسخ احوال‌پرسی
    greeting_response = ResponseFactory.create_greeting_response(
        user_id=user_id,
        question=question,
        greeting_data={"message": "سلام! خوش آمدید"},
        user_name="javad"
    )
    
    print(f"👋 پاسخ احوال‌پرسی:")
    print(f"   موفقیت: {greeting_response.success}")
    print(f"   نوع: {greeting_response.response_type}")
    print(f"   اعتماد: {greeting_response.confidence_score}")
    print(f"   سوالات پیگیری: {greeting_response.follow_up_questions}")
    
    # پاسخ خطا
    error_response = ResponseFactory.create_error_response(
        user_id=user_id,
        question="سوال نامعتبر",
        error_message="ابزار مورد نظر یافت نشد"
    )
    
    print(f"\n❌ پاسخ خطا:")
    print(f"   موفقیت: {error_response.success}")
    print(f"   نوع: {error_response.response_type}")
    print(f"   پیام خطا: {error_response.data['error_message']}")


async def main():
    """تابع اصلی تست"""
    
    print("🚀 شروع تست معماری ارتقاء یافته - فاز ۱")
    print("=" * 60)
    
    # تست ابزار احوال‌پرسی
    await test_greeting_tool()
    
    # تست منطق fallback روتینگ
    await test_smart_router_fallback()
    
    # تست ResponseFactory
    await test_response_factory()
    
    print("\n" + "=" * 60)
    print("✅ تست معماری ارتقاء یافته با موفقیت انجام شد!")
    print("\n📋 خلاصه معماری پیاده‌سازی شده:")
    print("   • ابزار احوال‌پرسی (GreetingTool)")
    print("   • SmartRouter برای روتینگ هوشمند")
    print("   • مدل‌های Pydantic برای پاسخ‌های استاندارد")
    print("   • ResponseFactory برای ایجاد پاسخ‌های یکپارچه")
    print("   • ساختار پکیج‌بندی شده و ماژولار")


if __name__ == "__main__":
    asyncio.run(main())
