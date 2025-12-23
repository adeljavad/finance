import sys
import os
from typing import List, Dict, Any, Optional

# Add the parent directory to sys.path to import from assistant.services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from assistant.services.deepseek_api import DeepSeekLLM as OriginalDeepSeekLLM

class DeepSeekLLM(OriginalDeepSeekLLM):
    """
    Wrapper class for DeepSeekLLM that adds a 'generate' method for compatibility
    with fixed_agent_engine.py
    """
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, user_id: Optional[str] = None) -> str:
        """
        Generate a response from the LLM.
        
        This method adapts the different calling patterns used in fixed_agent_engine.py:
        1. generate(prompt) - single prompt
        2. generate(user_prompt, system_prompt) - user prompt with system prompt
        3. generate(prompt, normalized_user_id) - prompt with user_id (ignored)
        
        Args:
            prompt: The main prompt text
            system_prompt: Optional system prompt (for method signature 2)
            user_id: Optional user ID (for method signature 3, ignored)
            
        Returns:
            The generated response text
        """
        # Handle different calling patterns
        messages = []
        
        # If system_prompt is provided and is a string (not None), use it
        if system_prompt is not None and isinstance(system_prompt, str):
            messages.append({"role": "system", "content": system_prompt})
        
        # Add the user prompt
        messages.append({"role": "user", "content": prompt})
        
        # Call the parent's invoke method
        return self.invoke(messages)
    
    # Also add ainvoke for async compatibility
    async def agenerate(self, prompt: str, system_prompt: Optional[str] = None, user_id: Optional[str] = None) -> str:
        """Async version of generate"""
        messages = []
        
        if system_prompt is not None and isinstance(system_prompt, str):
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        return await self.ainvoke(messages)
