"""
مدل‌های Pydantic برای پاسخ‌های استاندارد سیستم مالی
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class ResponseType(str, Enum):
    """انواع پاسخ‌های سیستم"""
    TOOL_RESULT = "tool_result"
    EXPERT_OPINION = "expert_opinion"
    GREETING = "greeting"
    ERROR = "error"
    FALLBACK = "fallback"


class RouterDecision(BaseModel):
    """تصمیم روتینگ هوشمند"""
    
    route: str = Field(
        ..., 
        description="مسیر تصمیم‌گیری: tool, llm_accounting, llm_general, greeting"
    )
    tool_name: Optional[str] = Field(
        None, 
        description="نام ابزار در صورت انتخاب مسیر tool"
    )
    confidence: float = Field(
        ..., 
        description="میزان اطمینان تصمیم (0-1)"
    )
    reasoning: str = Field(
        ..., 
        description="دلیل تصمیم‌گیری"
    )


class ToolSelection(BaseModel):
    """انتخاب ابزار توسط LLM"""
    
    tool_name: str = Field(
        ..., 
        description="نام ابزار انتخاب شده"
    )
    confidence: float = Field(
        ..., 
        description="میزان اطمینان انتخاب (0-1)"
    )
    required_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="پارامترهای مورد نیاز برای اجرای ابزار"
    )
    reasoning: str = Field(
        ..., 
        description="دلیل انتخاب ابزار"
    )


class UserContext(BaseModel):
    """Context کاربر برای شخصی‌سازی پاسخ‌ها"""
    
    user_id: str = Field(
        ..., 
        description="شناسه یکتا کاربر"
    )
    user_name: Optional[str] = Field(
        None, 
        description="نام کاربر (اختیاری)"
    )
    company_id: int = Field(
        default=1,
        description="شناسه شرکت پیش‌فرض"
    )
    period_id: int = Field(
        default=1,
        description="شناسه دوره مالی پیش‌فرض"
    )
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="تاریخچه مکالمات کاربر"
    )
    preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="ترجیحات کاربر"
    )


class FinancialResponse(BaseModel):
    """پاسخ استاندارد سیستم مالی"""
    
    success: bool = Field(
        ..., 
        description="وضعیت موفقیت عملیات"
    )
    response_type: ResponseType = Field(
        ..., 
        description="نوع پاسخ"
    )
    user_id: str = Field(
        ..., 
        description="شناسه کاربر"
    )
    question: str = Field(
        ..., 
        description="سوال کاربر"
    )
    data: Dict[str, Any] = Field(
        ..., 
        description="داده‌های پاسخ"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="متادیتای پاسخ"
    )
    follow_up_questions: Optional[List[str]] = Field(
        None,
        description="سوالات پیگیری برای کاربر"
    )
    confidence_score: float = Field(
        default=0.0,
        description="امتیاز اطمینان پاسخ (0-1)"
    )
    execution_time: Optional[float] = Field(
        None,
        description="زمان اجرا به ثانیه"
    )


class ToolExecutionResult(BaseModel):
    """نتیجه اجرای ابزار"""
    
    success: bool = Field(
        ..., 
        description="وضعیت موفقیت اجرا"
    )
    tool_name: str = Field(
        ..., 
        description="نام ابزار اجرا شده"
    )
    result: Dict[str, Any] = Field(
        ..., 
        description="نتیجه اجرای ابزار"
    )
    execution_time: float = Field(
        ..., 
        description="زمان اجرا به ثانیه"
    )
    error_message: Optional[str] = Field(
        None,
        description="پیام خطا در صورت شکست"
    )


class ConversationMessage(BaseModel):
    """پیام مکالمه"""
    
    role: str = Field(
        ..., 
        description="نقش: user, assistant, system"
    )
    content: str = Field(
        ..., 
        description="محتوای پیام"
    )
    timestamp: float = Field(
        ..., 
        description="زمان ارسال پیام"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="متادیتای پیام"
    )


class ConversationHistory(BaseModel):
    """تاریخچه مکالمه"""
    
    user_id: str = Field(
        ..., 
        description="شناسه کاربر"
    )
    messages: List[ConversationMessage] = Field(
        default_factory=list,
        description="لیست پیام‌ها"
    )
    created_at: float = Field(
        ..., 
        description="زمان ایجاد تاریخچه"
    )
    updated_at: float = Field(
        ..., 
        description="زمان آخرین به‌روزرسانی"
    )


class SystemMetrics(BaseModel):
    """متریک‌های سیستم"""
    
    total_requests: int = Field(
        default=0,
        description="تعداد کل درخواست‌ها"
    )
    successful_requests: int = Field(
        default=0,
        description="تعداد درخواست‌های موفق"
    )
    average_response_time: float = Field(
        default=0.0,
        description="میانگین زمان پاسخ‌دهی"
    )
    tool_usage: Dict[str, int] = Field(
        default_factory=dict,
        description="استفاده از ابزارها"
    )
    error_rate: float = Field(
        default=0.0,
        description="نرخ خطا"
    )


# Factory functions برای ایجاد نمونه‌های استاندارد
class ResponseFactory:
    """Factory برای ایجاد پاسخ‌های استاندارد"""
    
    @staticmethod
    def create_tool_response(
        user_id: str,
        question: str,
        tool_result: ToolExecutionResult,
        follow_up_questions: Optional[List[str]] = None
    ) -> FinancialResponse:
        """ایجاد پاسخ ابزار"""
        
        return FinancialResponse(
            success=tool_result.success,
            response_type=ResponseType.TOOL_RESULT,
            user_id=user_id,
            question=question,
            data=tool_result.result,
            metadata={
                "tool_name": tool_result.tool_name,
                "execution_time": tool_result.execution_time
            },
            follow_up_questions=follow_up_questions,
            confidence_score=0.95 if tool_result.success else 0.3,
            execution_time=tool_result.execution_time
        )
    
    @staticmethod
    def create_greeting_response(
        user_id: str,
        question: str,
        greeting_data: Dict[str, Any],
        user_name: Optional[str] = None
    ) -> FinancialResponse:
        """ایجاد پاسخ احوال‌پرسی"""
        
        return FinancialResponse(
            success=True,
            response_type=ResponseType.GREETING,
            user_id=user_id,
            question=question,
            data=greeting_data,
            metadata={
                "user_name": user_name,
                "is_welcome": True
            },
            follow_up_questions=[
                "چه کمکی می‌توانی بکنی؟",
                "ترازنامه شرکت را نشان بده",
                "نسبت‌های مالی را تحلیل کن"
            ],
            confidence_score=0.98,
            execution_time=0.1
        )
    
    @staticmethod
    def create_error_response(
        user_id: str,
        question: str,
        error_message: str,
        error_type: str = "general"
    ) -> FinancialResponse:
        """ایجاد پاسخ خطا"""
        
        return FinancialResponse(
            success=False,
            response_type=ResponseType.ERROR,
            user_id=user_id,
            question=question,
            data={
                "error_message": error_message,
                "error_type": error_type
            },
            metadata={},
            confidence_score=0.0,
            execution_time=0.0
        )
    
    @staticmethod
    def create_expert_response(
        user_id: str,
        question: str,
        expert_opinion: str,
        domain: str,
        confidence: float = 0.8
    ) -> FinancialResponse:
        """ایجاد پاسخ متخصص"""
        
        return FinancialResponse(
            success=True,
            response_type=ResponseType.EXPERT_OPINION,
            user_id=user_id,
            question=question,
            data={
                "expert_opinion": expert_opinion,
                "domain": domain
            },
            metadata={
                "expert_domain": domain
            },
            confidence_score=confidence,
            execution_time=0.5
        )
