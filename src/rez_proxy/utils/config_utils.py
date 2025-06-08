"""
Configuration management utilities.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from ..config import RezProxyConfig, get_config, get_config_manager


def create_default_config_file(file_path: str) -> None:
    """Create a default configuration file."""
    config = RezProxyConfig()
    config_dict = config.model_dump()
    
    # Remove sensitive fields
    sensitive_fields = ['api_key']
    for field in sensitive_fields:
        config_dict.pop(field, None)
    
    # Ensure directory exists
    config_dir = os.path.dirname(file_path)
    if config_dir:
        os.makedirs(config_dir, exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(config_dict, f, indent=2)
    
    print(f"✅ Default configuration file created: {file_path}")


def validate_config_file(file_path: str) -> Dict[str, Any]:
    """Validate a configuration file."""
    result = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "config": None
    }
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            result["errors"].append(f"Configuration file not found: {file_path}")
            return result
        
        # Load and parse JSON
        with open(file_path, 'r') as f:
            config_data = json.load(f)
        
        # Validate against schema
        try:
            # Create a temporary config to validate
            temp_config = RezProxyConfig(**config_data)
            result["config"] = temp_config.model_dump()
            result["valid"] = True
        except Exception as e:
            result["errors"].append(f"Configuration validation error: {e}")
            return result
        
        # Check for deprecated or unknown fields
        valid_fields = set(RezProxyConfig.model_fields.keys())
        config_fields = set(config_data.keys())
        
        unknown_fields = config_fields - valid_fields
        if unknown_fields:
            result["warnings"].append(f"Unknown configuration fields: {list(unknown_fields)}")
        
        # Check for missing important fields
        important_fields = ['host', 'port', 'api_prefix']
        missing_fields = [field for field in important_fields if field not in config_data]
        if missing_fields:
            result["warnings"].append(f"Missing important fields (using defaults): {missing_fields}")
        
    except json.JSONDecodeError as e:
        result["errors"].append(f"Invalid JSON format: {e}")
    except Exception as e:
        result["errors"].append(f"Unexpected error: {e}")
    
    return result


def merge_config_files(base_file: str, override_file: str, output_file: str) -> None:
    """Merge two configuration files."""
    # Load base configuration
    with open(base_file, 'r') as f:
        base_config = json.load(f)
    
    # Load override configuration
    with open(override_file, 'r') as f:
        override_config = json.load(f)
    
    # Merge configurations (override takes precedence)
    merged_config = {**base_config, **override_config}
    
    # Validate merged configuration
    validation_result = validate_config_file_data(merged_config)
    if not validation_result["valid"]:
        raise ValueError(f"Merged configuration is invalid: {validation_result['errors']}")
    
    # Save merged configuration
    with open(output_file, 'w') as f:
        json.dump(merged_config, f, indent=2)
    
    print(f"✅ Configuration files merged: {base_file} + {override_file} -> {output_file}")


def validate_config_file_data(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate configuration data dictionary."""
    result = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "config": None
    }
    
    try:
        # Validate against schema
        temp_config = RezProxyConfig(**config_data)
        result["config"] = temp_config.model_dump()
        result["valid"] = True
        
        # Check for unknown fields
        valid_fields = set(RezProxyConfig.model_fields.keys())
        config_fields = set(config_data.keys())
        
        unknown_fields = config_fields - valid_fields
        if unknown_fields:
            result["warnings"].append(f"Unknown configuration fields: {list(unknown_fields)}")
        
    except Exception as e:
        result["errors"].append(f"Configuration validation error: {e}")
    
    return result


def backup_config_file(file_path: str, backup_suffix: str = ".backup") -> str:
    """Create a backup of a configuration file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    backup_path = file_path + backup_suffix
    
    # If backup already exists, add timestamp
    if os.path.exists(backup_path):
        import time
        timestamp = int(time.time())
        backup_path = f"{file_path}.backup.{timestamp}"
    
    # Copy file
    import shutil
    shutil.copy2(file_path, backup_path)
    
    print(f"📋 Configuration backup created: {backup_path}")
    return backup_path


def restore_config_from_backup(backup_path: str, target_path: str) -> None:
    """Restore configuration from backup."""
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    # Validate backup file first
    validation_result = validate_config_file(backup_path)
    if not validation_result["valid"]:
        raise ValueError(f"Backup configuration is invalid: {validation_result['errors']}")
    
    # Copy backup to target
    import shutil
    shutil.copy2(backup_path, target_path)
    
    print(f"🔄 Configuration restored from backup: {backup_path} -> {target_path}")


def get_config_diff(file1: str, file2: str) -> Dict[str, Any]:
    """Get differences between two configuration files."""
    with open(file1, 'r') as f:
        config1 = json.load(f)
    
    with open(file2, 'r') as f:
        config2 = json.load(f)
    
    diff = {
        "added": {},
        "removed": {},
        "changed": {},
        "unchanged": {}
    }
    
    all_keys = set(config1.keys()) | set(config2.keys())
    
    for key in all_keys:
        if key in config1 and key in config2:
            if config1[key] != config2[key]:
                diff["changed"][key] = {
                    "old": config1[key],
                    "new": config2[key]
                }
            else:
                diff["unchanged"][key] = config1[key]
        elif key in config1:
            diff["removed"][key] = config1[key]
        else:
            diff["added"][key] = config2[key]
    
    return diff


def apply_config_template(template_file: str, variables: Dict[str, Any], output_file: str) -> None:
    """Apply variables to a configuration template."""
    with open(template_file, 'r') as f:
        template_content = f.read()
    
    # Simple variable substitution
    for key, value in variables.items():
        placeholder = f"${{{key}}}"
        template_content = template_content.replace(placeholder, str(value))
    
    # Parse as JSON to validate
    try:
        config_data = json.loads(template_content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Template resulted in invalid JSON: {e}")
    
    # Validate configuration
    validation_result = validate_config_file_data(config_data)
    if not validation_result["valid"]:
        raise ValueError(f"Template configuration is invalid: {validation_result['errors']}")
    
    # Save output
    with open(output_file, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print(f"📝 Configuration template applied: {template_file} -> {output_file}")


def watch_config_changes(callback_func):
    """Decorator to watch for configuration changes."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Add callback to config manager
            config_manager = get_config_manager()
            config_manager.add_change_callback(callback_func)
            
            try:
                return func(*args, **kwargs)
            finally:
                # Remove callback when done
                config_manager.remove_change_callback(callback_func)
        
        return wrapper
    return decorator
