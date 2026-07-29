"""
ExcelPlorer — Plugin Registry

Discovers, registers, and provides access to marketplace plugins.
"""

import importlib
import inspect
import logging
from pathlib import Path

from backend.core.schema import WorkbookSchema
from backend.plugins.base import MarketplacePlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Manages the discovery and lifecycle of MarketplacePlugins."""
    
    _plugins: dict[str, MarketplacePlugin] = {}
    _is_initialized = False

    @classmethod
    def initialize(cls) -> None:
        """Dynamically load all plugins in the backend/plugins directory."""
        if cls._is_initialized:
            return
            
        cls._plugins.clear()
        
        plugins_dir = Path(__file__).parent
        
        for file_path in plugins_dir.glob("*.py"):
            if file_path.name.startswith("__") or file_path.name in ("base.py", "registry.py"):
                continue
                
            module_name = f"backend.plugins.{file_path.stem}"
            try:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if it's a subclass of MarketplacePlugin, but not the ABC itself
                    if issubclass(obj, MarketplacePlugin) and obj is not MarketplacePlugin:
                        plugin_instance = obj()
                        cls._plugins[plugin_instance.name.lower()] = plugin_instance
                        logger.debug(f"Loaded plugin: {plugin_instance.name}")
            except Exception as e:
                logger.error(f"Failed to load plugin {module_name}: {e}", exc_info=True)
                
        cls._is_initialized = True
        logger.info(f"Initialized PluginRegistry. Loaded {len(cls._plugins)} plugins.")

    @classmethod
    def get_plugin(cls, name: str) -> MarketplacePlugin | None:
        """Retrieve a specific plugin by name."""
        if not cls._is_initialized:
            cls.initialize()
        return cls._plugins.get(name.lower())

    @classmethod
    def detect_marketplace(cls, schema: WorkbookSchema) -> MarketplacePlugin | None:
        """
        Ask all plugins to score the schema. 
        Returns the highest-scoring plugin if score > 0.5.
        """
        if not cls._is_initialized:
            cls.initialize()
            
        best_plugin = None
        highest_score = 0.0
        
        for plugin in cls._plugins.values():
            try:
                score = plugin.detect(schema)
                if score > highest_score:
                    highest_score = score
                    best_plugin = plugin
            except Exception as e:
                logger.warning(f"Plugin {plugin.name} crashed during detection: {e}")
                
        if highest_score > 0.5:
            logger.info(f"Detected marketplace: {best_plugin.name} (score: {highest_score:.2f})")
            return best_plugin
            
        return None
