"""Simplified configuration management for Polymarket Position Notifier."""

import os
import yaml
import re
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Simple configuration manager with YAML and environment variable support."""
    
    def __init__(self):
        self.config_dir = Path("config")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self._config: Optional[Dict[str, Any]] = None
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        if self._config is None:
            self._load_config()
        
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def _load_config(self) -> None:
        """Load and process configuration files."""
        # Load base config
        base_path = self.config_dir / "base.yaml"
        with open(base_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Load environment overrides if they exist
        env_path = self.config_dir / f"{self.environment}.yaml"
        if env_path.exists():
            with open(env_path, 'r') as f:
                env_config = yaml.safe_load(f)
                self._merge_dict(config, env_config)
        
        # Process environment variables
        self._config = self._process_env_vars(config)
    
    def _merge_dict(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Merge override dict into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_dict(base[key], value)
            else:
                base[key] = value
    
    def _process_env_vars(self, obj: Any) -> Any:
        """Process environment variables in config."""
        if isinstance(obj, dict):
            return {k: self._process_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._process_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            return self._substitute_env_var(obj)
        else:
            return obj
    
    def _substitute_env_var(self, value: str) -> Any:
        """Substitute single environment variable."""
        var_expr = value[2:-1]  # Remove ${ and }
        
        if ':-' in var_expr:
            var_name, default_val = var_expr.split(':-', 1)
            result = os.getenv(var_name.strip(), default_val)
        else:
            var_name = var_expr.strip()
            result = os.getenv(var_name)
            if result is None:
                raise ValueError(f"Required environment variable '{var_name}' is not set")
        
        # Convert types
        if result.lower() in ('true', 'false'):
            return result.lower() == 'true'
        elif result.isdigit():
            return int(result)
        elif re.match(r'^\d+\.\d+$', result):
            return float(result)
        else:
            return result


# Global instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
