"""
ExcelPlorer — Marketplace Plugin Base Class

Defines the interface for all marketplace-specific plugins.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable

from backend.core.schema import WorkbookSchema
from backend.core.validator import ValidationIssue


class MarketplacePlugin(ABC):
    """
    Abstract Base Class for Marketplace Plugins.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the unique name of the marketplace (e.g., 'Flipkart')."""
        pass

    @abstractmethod
    def detect(self, schema: WorkbookSchema) -> float:
        """
        Calculates how likely this template belongs to this marketplace.
        
        Args:
            schema: The parsed WorkbookSchema.
            
        Returns:
            A float between 0.0 and 1.0 (confidence score).
        """
        pass

    def get_prompt_additions(self, schema: WorkbookSchema) -> str:
        """
        Returns marketplace-specific rules to append to the AI prompt.
        """
        return ""

    def get_validation_rules(self, schema: WorkbookSchema) -> list[Callable[[dict, int], list[ValidationIssue]]]:
        """
        Returns a list of custom validation functions.
        Each function should take a (row_data: dict, index: int) and return a list of ValidationIssues.
        """
        return []

    def apply_auto_corrections(self, item: dict[str, Any], schema: WorkbookSchema) -> list[ValidationIssue]:
        """
        Applies marketplace-specific auto-corrections.
        Modifies 'item' in-place and returns a list of INFO ValidationIssues describing the changes.
        """
        return []
