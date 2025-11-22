"""Tests for TOON format encoding/decoding functionality."""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

# Add project root to path
import sys
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from toon_format import (
        encode,
        decode,
        encode_file,
        decode_file,
        estimate_token_savings,
        has_uniform_arrays,
        _check_toon_cli
    )
except ImportError:
    pytest.skip("TOON format module not available", allow_module_level=True)


def check_toon_cli_available():
    """Check if TOON CLI is available via npx."""
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


TOON_CLI_AVAILABLE = check_toon_cli_available()


@pytest.fixture
def sample_data():
    """Sample data structure for testing."""
    return {
        "games": [
            {"id": 1, "home": "Ohio State", "away": "Michigan", "score": 42},
            {"id": 2, "home": "Alabama", "away": "Georgia", "score": 35}
        ],
        "metadata": {
            "season": 2025,
            "week": 8
        }
    }


@pytest.fixture
def uniform_array_data():
    """Data with uniform arrays suitable for TOON encoding."""
    return {
        "tasks": [
            {"id": "task_1", "name": "Task 1", "agent": "model_engine", "time": 5.0},
            {"id": "task_2", "name": "Task 2", "agent": "insight_generator", "time": 10.0},
            {"id": "task_3", "name": "Task 3", "agent": "workflow_automator", "time": 8.0}
        ]
    }


@pytest.fixture
def temp_file(tmp_path):
    """Temporary file for testing file operations."""
    return tmp_path / "test.json"


@pytest.mark.skipif(not TOON_CLI_AVAILABLE, reason="TOON CLI not available")
class TestTOONEncoding:
    """Tests for TOON encoding functionality."""
    
    def test_encode_basic_data(self, sample_data):
        """Test encoding basic data structure."""
        toon_output = encode(sample_data)
        assert isinstance(toon_output, str)
        assert len(toon_output) > 0
    
    def test_encode_decode_roundtrip(self, sample_data):
        """Test that encoding and decoding preserves data."""
        toon_output = encode(sample_data)
        decoded = decode(toon_output)
        
        # Compare structure (JSON serialization handles type differences)
        assert json.dumps(decoded, sort_keys=True) == json.dumps(sample_data, sort_keys=True)
    
    def test_encode_uniform_arrays(self, uniform_array_data):
        """Test encoding data with uniform arrays."""
        toon_output = encode(uniform_array_data)
        assert isinstance(toon_output, str)
        
        decoded = decode(toon_output)
        assert len(decoded["tasks"]) == 3
        assert decoded["tasks"][0]["id"] == "task_1"
    
    def test_encode_empty_structure(self):
        """Test encoding empty data structures."""
        empty_data = {}
        toon_output = encode(empty_data)
        decoded = decode(toon_output)
        assert decoded == empty_data


@pytest.mark.skipif(not TOON_CLI_AVAILABLE, reason="TOON CLI not available")
class TestTOONDecoding:
    """Tests for TOON decoding functionality."""
    
    def test_decode_valid_toon(self, sample_data):
        """Test decoding valid TOON format."""
        toon_output = encode(sample_data)
        decoded = decode(toon_output)
        assert isinstance(decoded, dict)
        assert "games" in decoded
    
    def test_decode_invalid_toon(self):
        """Test decoding invalid TOON format."""
        # TOON CLI is forgiving and may return input as-is for invalid content
        # This test verifies the function doesn't crash on invalid input
        try:
            result = decode("invalid toon content that definitely won't parse")
            # If it doesn't raise, that's also acceptable behavior
            assert isinstance(result, (str, dict, list))
        except (RuntimeError, ValueError):
            # Raising an error is also acceptable
            pass


@pytest.mark.skipif(not TOON_CLI_AVAILABLE, reason="TOON CLI not available")
class TestTOONFileOperations:
    """Tests for TOON file operations."""
    
    def test_encode_file(self, sample_data, temp_file):
        """Test encoding JSON file to TOON."""
        # Write JSON file
        with open(temp_file, 'w') as f:
            json.dump(sample_data, f)
        
        # Encode to TOON
        toon_file = encode_file(temp_file)
        assert toon_file.exists()
        assert toon_file.suffix == '.toon'
        
        # Verify content
        toon_content = toon_file.read_text()
        assert len(toon_content) > 0
    
    def test_decode_file(self, sample_data, temp_file):
        """Test decoding TOON file to JSON."""
        # Create TOON file first
        with open(temp_file, 'w') as f:
            json.dump(sample_data, f)
        toon_file = encode_file(temp_file)
        
        # Decode back to JSON
        json_file = decode_file(toon_file)
        assert json_file.exists()
        assert json_file.suffix == '.json'
        
        # Verify content
        with open(json_file, 'r') as f:
            decoded = json.load(f)
        assert decoded["games"][0]["id"] == 1
    
    def test_encode_file_custom_output(self, sample_data, temp_file, tmp_path):
        """Test encoding file with custom output path."""
        with open(temp_file, 'w') as f:
            json.dump(sample_data, f)
        
        custom_output = tmp_path / "custom.toon"
        result = encode_file(temp_file, custom_output)
        assert result == custom_output
        assert custom_output.exists()
    
    def test_encode_file_not_found(self, tmp_path):
        """Test encoding non-existent file raises error."""
        missing_file = tmp_path / "missing.json"
        with pytest.raises(FileNotFoundError):
            encode_file(missing_file)


class TestTOONErrorHandling:
    """Tests for error handling when TOON CLI is unavailable."""
    
    @pytest.mark.skipif(TOON_CLI_AVAILABLE, reason="TOON CLI is available")
    def test_encode_without_cli(self, sample_data):
        """Test that encode raises error when CLI is unavailable."""
        with pytest.raises(RuntimeError, match="TOON CLI not available"):
            encode(sample_data)
    
    @pytest.mark.skipif(TOON_CLI_AVAILABLE, reason="TOON CLI is available")
    def test_decode_without_cli(self):
        """Test that decode raises error when CLI is unavailable."""
        with pytest.raises(RuntimeError, match="TOON CLI not available"):
            decode("some toon content")
    
    def test_check_toon_cli_function(self):
        """Test the CLI check function."""
        result = _check_toon_cli()
        assert isinstance(result, bool)


class TestTOONUtilities:
    """Tests for TOON utility functions."""
    
    def test_estimate_token_savings(self, uniform_array_data):
        """Test token savings estimation."""
        if not TOON_CLI_AVAILABLE:
            pytest.skip("TOON CLI not available")
        
        toon_output = encode(uniform_array_data)
        savings = estimate_token_savings(uniform_array_data, toon_output)
        
        assert "json_tokens_estimate" in savings
        assert "toon_tokens_estimate" in savings
        assert "token_savings_percent" in savings
        assert "token_reduction" in savings
        assert isinstance(savings["token_savings_percent"], (int, float))
    
    def test_has_uniform_arrays(self, uniform_array_data):
        """Test uniform array detection."""
        assert has_uniform_arrays(uniform_array_data) is True
        
        # Non-uniform array
        non_uniform = {
            "items": [
                {"id": 1, "name": "Item 1"},
                {"id": 2}  # Missing 'name' field
            ]
        }
        assert has_uniform_arrays(non_uniform) is False
        
        # Empty array
        empty = {"items": []}
        assert has_uniform_arrays(empty, min_items=1) is False
        
        # Single item (below minimum)
        single = {"items": [{"id": 1}]}
        assert has_uniform_arrays(single, min_items=2) is False
    
    def test_has_uniform_arrays_nested(self):
        """Test uniform array detection in nested structures."""
        nested = {
            "level1": {
                "level2": {
                    "tasks": [
                        {"id": "t1", "name": "Task 1"},
                        {"id": "t2", "name": "Task 2"}
                    ]
                }
            }
        }
        assert has_uniform_arrays(nested) is True

