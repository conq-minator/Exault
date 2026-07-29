"""
ExcelPlorer — Ollama Adapter (Stub)
"""
from backend.ai.base import AIAdapter

class OllamaAdapter(AIAdapter):
    @property
    def provider_name(self) -> str:
        return "Ollama"
        
    def generate_json(self, prompt: str) -> str:
        raise NotImplementedError("Ollama API integration not yet implemented.")
