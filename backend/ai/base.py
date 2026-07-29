"""
ExcelPlorer — AI Adapter Base Class
"""

from abc import ABC, abstractmethod


class AIAdapter(ABC):
    """
    Abstract Base Class for AI Adapters.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the AI provider."""
        pass

    @abstractmethod
    def generate_json(self, prompt: str) -> str:
        """
        Sends the prompt to the AI provider and returns the raw JSON string.
        """
        pass
