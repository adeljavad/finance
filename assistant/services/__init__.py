# assistant/services/__init__.py
try:
    from .deepseek_api import DeepSeekLLM
    from .rag_engine import StableRAGEngine
    from .agent_engine import AgentEngine
except ImportError as e:
    print(f"Import error in services: {e}")
    # تعریف fallback برای زمانی که import با مشکل مواجه شود
    class DeepSeekLLM:
        def __init__(self):
            raise ImportError("DeepSeekLLM not available")
    
    class StableRAGEngine:
        def __init__(self):
            raise ImportError("StableRAGEngine not available")
    
    class AgentEngine:
        def __init__(self):
            raise ImportError("AgentEngine not available")

__all__ = ['DeepSeekLLM', 'StableRAGEngine', 'AgentEngine']