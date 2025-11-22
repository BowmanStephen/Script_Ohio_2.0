#!/usr/bin/env python3
"""
TOON Format Utility Module

Token-Oriented Object Notation encoding/decoding for Script Ohio 2.0.
Provides Python interface to TOON format for token-optimized LLM communication.

References:
- https://toonformat.dev/
- https://toonformat.dev/reference/spec.html
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


def _check_toon_cli() -> bool:
    """Check if TOON CLI is available"""
    try:
        result = subprocess.run(
            ["npx", "@toon-format/cli", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def encode(data: Union[Dict, List, Any]) -> str:
    """
    Encode JSON-serializable data to TOON format.
    
    Args:
        data: JSON-serializable data (dict, list, etc.)
        
    Returns:
        TOON-formatted string
        
    Raises:
        RuntimeError: If TOON CLI is not available
    """
    if not _check_toon_cli():
        logger.warning("TOON CLI not available. Install with: npm install -g @toon-format/cli")
        raise RuntimeError(
            "TOON CLI not available. Install with: npm install -g @toon-format/cli\n"
            "Or use: npx @toon-format/cli input.json -o output.toon"
        )
    
    # Convert to JSON first
    json_str = json.dumps(data, default=str)
    
    # Use TOON CLI to convert
    try:
        result = subprocess.run(
            ["npx", "@toon-format/cli", "-"],
            input=json_str,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"TOON encoding failed: {result.stderr}")
        
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise RuntimeError("TOON encoding timed out")
    except Exception as e:
        raise RuntimeError(f"TOON encoding error: {e}")


def decode(toon_str: str) -> Union[Dict, List, Any]:
    """
    Decode TOON format string to Python data structure.
    
    Args:
        toon_str: TOON-formatted string
        
    Returns:
        Python data structure (dict, list, etc.)
        
    Raises:
        RuntimeError: If TOON CLI is not available or decoding fails
    """
    if not _check_toon_cli():
        raise RuntimeError(
            "TOON CLI not available. Install with: npm install -g @toon-format/cli"
        )
    
    try:
        result = subprocess.run(
            ["npx", "@toon-format/cli", "--decode", "-"],
            input=toon_str,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"TOON decoding failed: {result.stderr}")
        
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        raise RuntimeError("TOON decoding timed out")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"TOON decoding JSON error: {e}")
    except Exception as e:
        raise RuntimeError(f"TOON decoding error: {e}")


def encode_file(input_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Encode JSON file to TOON format.
    
    Args:
        input_path: Path to input JSON file
        output_path: Optional path for output TOON file (default: input_path.toon)
        
    Returns:
        Path to output TOON file
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if output_path is None:
        output_path = input_path.with_suffix('.toon')
    else:
        output_path = Path(output_path)
    
    if not _check_toon_cli():
        raise RuntimeError("TOON CLI not available")
    
    try:
        result = subprocess.run(
            ["npx", "@toon-format/cli", str(input_path), "-o", str(output_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"TOON encoding failed: {result.stderr}")
        
        logger.info(f"Encoded {input_path} to {output_path}")
        return output_path
    except subprocess.TimeoutExpired:
        raise RuntimeError("TOON encoding timed out")
    except Exception as e:
        raise RuntimeError(f"TOON encoding error: {e}")


def decode_file(input_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Decode TOON file to JSON format.
    
    Args:
        input_path: Path to input TOON file
        output_path: Optional path for output JSON file (default: input_path.json)
        
    Returns:
        Path to output JSON file
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if output_path is None:
        output_path = input_path.with_suffix('.json')
    else:
        output_path = Path(output_path)
    
    if not _check_toon_cli():
        raise RuntimeError("TOON CLI not available")
    
    try:
        # Read TOON file and decode
        with open(input_path, 'r') as f:
            toon_content = f.read()
        
        decoded = decode(toon_content)
        
        # Write JSON output
        with open(output_path, 'w') as f:
            json.dump(decoded, f, indent=2, default=str)
        
        logger.info(f"Decoded {input_path} to {output_path}")
        return output_path
    except Exception as e:
        raise RuntimeError(f"TOON decoding error: {e}")


def estimate_token_savings(json_data: Union[Dict, List], toon_data: str) -> Dict[str, float]:
    """
    Estimate token savings from TOON encoding.
    
    Args:
        json_data: Original JSON data
        toon_data: TOON-encoded string
        
    Returns:
        Dictionary with savings metrics
    """
    json_str = json.dumps(json_data, default=str)
    json_tokens = len(json_str.split())  # Rough token estimate
    toon_tokens = len(toon_data.split())  # Rough token estimate
    
    savings = ((json_tokens - toon_tokens) / json_tokens * 100) if json_tokens > 0 else 0
    
    return {
        "json_tokens_estimate": json_tokens,
        "toon_tokens_estimate": toon_tokens,
        "token_savings_percent": savings,
        "token_reduction": json_tokens - toon_tokens
    }


def has_uniform_arrays(data: Union[Dict, List], min_items: int = 2) -> bool:
    """
    Check if data structure contains uniform arrays suitable for TOON encoding.
    
    Args:
        data: Data structure to check
        min_items: Minimum items in array to consider
        
    Returns:
        True if structure has uniform arrays suitable for TOON
    """
    if isinstance(data, list):
        if len(data) >= min_items:
            # Check if all items have same structure
            if all(isinstance(item, dict) for item in data):
                first_keys = set(data[0].keys()) if data else set()
                return all(set(item.keys()) == first_keys for item in data)
        return False
    
    if isinstance(data, dict):
        return any(has_uniform_arrays(value, min_items) for value in data.values())
    
    return False


if __name__ == "__main__":
    # Example usage
    test_data = {
        "games": [
            {"id": 1, "home": "Ohio State", "away": "Michigan", "score": 42},
            {"id": 2, "home": "Alabama", "away": "Georgia", "score": 35}
        ]
    }
    
    try:
        toon_output = encode(test_data)
        print("TOON Output:")
        print(toon_output)
        
        decoded = decode(toon_output)
        print("\nDecoded (should match original):")
        print(json.dumps(decoded, indent=2))
        
        savings = estimate_token_savings(test_data, toon_output)
        print(f"\nToken Savings: {savings['token_savings_percent']:.1f}%")
    except RuntimeError as e:
        print(f"Error: {e}")
        print("\nInstall TOON CLI with: npm install -g @toon-format/cli")
        sys.exit(1)

