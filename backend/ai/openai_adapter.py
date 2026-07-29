"""
ExcelPlorer — OpenAI Adapter (Stub)
"""
from backend.ai.base import AIAdapter

class OpenAIAdapter(AIAdapter):
    @property
    def provider_name(self) -> str:
        return "OpenAI"
        
    def generate_json(self, prompt: str) -> str:
        raise NotImplementedError("OpenAI API integration not yet implemented.")
