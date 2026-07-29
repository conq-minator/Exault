"""
ExcelPlorer — Gemini Adapter (Stub)
"""
from backend.ai.base import AIAdapter

class GeminiAdapter(AIAdapter):
    @property
    def provider_name(self) -> str:
        return "Gemini"
        
    def generate_json(self, prompt: str) -> str:
        raise NotImplementedError("Gemini API integration not yet implemented.")
