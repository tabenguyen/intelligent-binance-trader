"""
Centralized environment variable loader for the trading bot.

This module provides a centralized way to load environment variables from .env files
and ensures that the loading is done only once across the entire application.

Usage Examples:
    # Instead of using os.getenv() and load_dotenv() directly:
    from src.utils.env_loader import get_env_int, get_env_bool
    
    # Before (duplicated in multiple files):
    from dotenv import load_dotenv
    import os
    load_dotenv()
    value = int(os.getenv('SOME_VAR', '10'))
    
    # After (centralized):
    value = get_env_int('SOME_VAR', 10)

Migration Guide:
    Replace these patterns:
    - os.getenv('VAR', 'default') → get_env('VAR', 'default')
    - int(os.getenv('VAR', '10')) → get_env_int('VAR', 10)
    - float(os.getenv('VAR', '1.5')) → get_env_float('VAR', 1.5)
    - os.getenv('VAR', 'true').lower() == 'true' → get_env_bool('VAR', True)
    
    Remove these imports and calls:
    - from dotenv import load_dotenv
    - load_dotenv() or load_dotenv(path)
"""

import os
from pathlib import Path
from typing import Optional


_env_loaded = False


def load_environment(force_reload: bool = False) -> bool:
    """
    Load environment variables from .env file.
    
    This function ensures environment variables are loaded only once unless
    force_reload is True. It searches for .env files in multiple locations.
    
    Args:
        force_reload: If True, reload environment even if already loaded
        
    Returns:
        True if .env file was found and loaded, False otherwise
    """
    global _env_loaded
    
    if _env_loaded and not force_reload:
        return True
    
    from dotenv import load_dotenv
    
    # Look for .env file in multiple locations
    env_paths = [
        Path.cwd() / ".env",  # Root directory
        Path.cwd() / "config" / ".env",  # Config directory
        Path.cwd() / "config" / ".env.test"  # Test config
    ]
    
    env_file_found = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            env_file_found = True
            break
    
    if not env_file_found:
        # If no .env file found, try loading without path (uses system env vars)
        load_dotenv()
    
    _env_loaded = True
    return env_file_found


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get environment variable value, ensuring environment is loaded first.
    
    Args:
        key: Environment variable name
        default: Default value if variable is not found
        
    Returns:
        Environment variable value or default
    """
    load_environment()
    return os.getenv(key, default)


def get_env_int(key: str, default: int) -> int:
    """
    Get environment variable as integer.
    
    Args:
        key: Environment variable name
        default: Default value if variable is not found or invalid
        
    Returns:
        Environment variable value as integer or default
    """
    value = get_env(key)
    if value is None:
        return default
    
    try:
        return int(value)
    except ValueError:
        return default


def get_env_float(key: str, default: float) -> float:
    """
    Get environment variable as float.
    
    Args:
        key: Environment variable name
        default: Default value if variable is not found or invalid
        
    Returns:
        Environment variable value as float or default
    """
    value = get_env(key)
    if value is None:
        return default
    
    try:
        return float(value)
    except ValueError:
        return default


def get_env_bool(key: str, default: bool = False) -> bool:
    """
    Get environment variable as boolean.
    
    Args:
        key: Environment variable name
        default: Default value if variable is not found
        
    Returns:
        Environment variable value as boolean or default
    """
    value = get_env(key)
    if value is None:
        return default
    
    return value.lower() in ('true', '1', 'yes', 'on')
