#!/usr/bin/env python3
"""
Template Loader for TOON Plan Templates

Loads and instantiates TOON-formatted plan templates with variable substitution.
"""

import re
from pathlib import Path
from typing import Dict, Any
import sys

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "src"))

from toon_format import decode


def load_template(template_name: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load and instantiate a TOON template with variable substitution.
    
    Args:
        template_name: Name of template (without .toon extension)
        variables: Dictionary of variables to substitute
        
    Returns:
        Instantiated plan data as dictionary
        
    Raises:
        FileNotFoundError: If template file not found
        ValueError: If template parsing fails
    """
    template_dir = Path(__file__).parent
    template_path = template_dir / f"{template_name}.toon"
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    # Read template
    toon_content = template_path.read_text()
    
    # Replace variables
    for key, value in variables.items():
        # Replace {{key}} with value (convert to string)
        pattern = f"{{{{{{key}}}}}}"
        toon_content = toon_content.replace(pattern, str(value))
    
    # Decode to dict
    try:
        plan_data = decode(toon_content)
        return plan_data
    except Exception as e:
        raise ValueError(f"Failed to parse template: {e}")


def list_templates() -> list:
    """
    List all available templates.
    
    Returns:
        List of template names (without .toon extension)
    """
    template_dir = Path(__file__).parent
    templates = []
    
    for template_file in template_dir.glob("*.toon"):
        if template_file.name != "README.md":
            templates.append(template_file.stem)
    
    return sorted(templates)


if __name__ == "__main__":
    # Example usage
    import json
    
    # List templates
    print("Available templates:")
    for template in list_templates():
        print(f"  - {template}")
    
    # Load example template
    try:
        template_data = load_template('weekly_analysis', {
            'week': 13,
            'season': 2025
        })
        print("\nLoaded template:")
        print(json.dumps(template_data, indent=2, default=str))
    except Exception as e:
        print(f"\nError loading template: {e}")

