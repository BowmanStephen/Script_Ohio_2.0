"""
Advanced TOON Format Compression Strategies

Extends TOON format with intelligent compression strategies, adaptive algorithms,
and advanced optimization techniques for maximum token reduction while preserving
data integrity and readability.

Features:
- Adaptive compression based on data patterns
- Multi-level compression strategies
- Semantic compression for domain-specific data
- Progressive compression levels
- Smart field type detection and optimization
"""

import gzip
import json
import logging
import pickle
import re
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CompressionAnalysis:
    """Analysis of compression effectiveness"""

    original_size: int
    compressed_size: int
    compression_ratio: float
    token_reduction_percent: float
    compression_time_ms: float
    strategy_used: str
    field_optimizations: List[str]
    compression_level: int


@dataclass
class TOONCompressionProfile:
    """Profile for optimizing compression of specific data types"""

    profile_name: str
    data_patterns: List[str]
    optimal_strategy: str
    compression_level: int
    field_mappings: Dict[str, str]
    common_values: Dict[str, Any]


class AdvancedTOONCompressor:
    """Advanced TOON format compressor with intelligent strategies"""

    def __init__(self):
        self.compression_strategies = {
            "basic": self._semantic_compression,  # Use semantic as basic
            "adaptive": self._adaptive_compression,
            "semantic": self._semantic_compression,
            "hierarchical": self._hierarchical_compression,
            "progressive": self._progressive_compression,
            "ultra": self._ultra_compression,
        }

        self.compression_profiles = {}
        self.compression_cache = {}
        self.field_type_cache = {}
        self.common_value_cache = {}

        # Initialize default profiles
        self._initialize_default_profiles()

        logger.info("Advanced TOON Compressor initialized")

    def _initialize_default_profiles(self):
        """Initialize default compression profiles for common data types"""

        # CFBD Games Data Profile
        self.compression_profiles["cfbd_games"] = TOONCompressionProfile(
            profile_name="cfbd_games",
            data_patterns=["game_id", "home_team", "away_team", "season", "week"],
            optimal_strategy="semantic",
            compression_level=7,
            field_mappings={
                "game_id": "id",
                "home_team": "home",
                "away_team": "away",
                "season": "yr",
                "week": "wk",
                "home_score": "hs",
                "away_score": "as",
                "predicted_margin": "pm",
            },
            common_values={},
        )

        # Model Predictions Profile
        self.compression_profiles["predictions"] = TOONCompressionProfile(
            profile_name="predictions",
            data_patterns=["prediction_id", "confidence", "model_type"],
            optimal_strategy="adaptive",
            compression_level=8,
            field_mappings={
                "prediction_id": "pid",
                "confidence_score": "conf",
                "model_type": "model",
                "predicted_winner": "winner",
                "predicted_margin": "margin",
            },
            common_values={},
        )

        # Agent Workflow Profile
        self.compression_profiles["workflow"] = TOONCompressionProfile(
            profile_name="workflow",
            data_patterns=["workflow_id", "agent_id", "task_status"],
            optimal_strategy="hierarchical",
            compression_level=6,
            field_mappings={
                "workflow_id": "wid",
                "agent_id": "aid",
                "task_status": "status",
                "timestamp": "ts",
                "completion_time": "ct",
            },
            common_values={
                "task_status": ["pending", "running", "completed", "failed"]
            },
        )

    def compress(
        self,
        data: Any,
        strategy: str = "adaptive",
        profile: str = None,
        compression_level: int = None,
    ) -> Tuple[str, CompressionAnalysis]:
        """
        Compress data using advanced TOON format strategies

        Args:
            data: Data to compress
            strategy: Compression strategy to use
            profile: Named profile for optimization
            compression_level: Compression level (1-10)

        Returns:
            Tuple of (compressed_string, analysis)
        """

        start_time = time.time()

        # Detect data type and select profile
        if not profile:
            profile = self._detect_data_profile(data)

        # Get profile configuration
        profile_config = self.compression_profiles.get(profile)
        if profile_config:
            strategy = profile_config.optimal_strategy
            if compression_level is None:
                compression_level = profile_config.compression_level

        if compression_level is None:
            compression_level = 7

        # Convert data to dict if needed
        if isinstance(data, str):
            try:
                data_dict = json.loads(data)
            except:
                data_dict = {"data": data}
        elif hasattr(data, "__dict__"):
            data_dict = asdict(data)
        else:
            data_dict = data

        # Calculate original size
        original_json = json.dumps(data_dict, separators=(",", ":"))
        original_size = len(original_json)

        # Apply compression strategy
        compression_func = self.compression_strategies.get(
            strategy, self._adaptive_compression
        )

        try:
            compressed_output = compression_func(
                data_dict, profile_config, compression_level
            )
            compressed_size = len(compressed_output)

            # Calculate compression metrics
            compression_ratio = (
                compressed_size / original_size if original_size > 0 else 1
            )
            token_reduction = (1 - compression_ratio) * 100
            compression_time = (time.time() - start_time) * 1000

            # Analyze optimizations applied
            field_optimizations = self._analyze_optimizations_applied(
                data_dict, compressed_output
            )

            analysis = CompressionAnalysis(
                original_size=original_size,
                compressed_size=compressed_size,
                compression_ratio=compression_ratio,
                token_reduction_percent=token_reduction,
                compression_time_ms=compression_time,
                strategy_used=strategy,
                field_optimizations=field_optimizations,
                compression_level=compression_level,
            )

            return compressed_output, analysis

        except Exception as e:
            logger.error(f"Compression failed: {e}")
            # Fallback to basic compression
            return self._fallback_compression(data_dict, original_size, start_time)

    def decompress(self, compressed_data: str, profile: str = None) -> Any:
        """
        Decompress TOON format data

        Args:
            compressed_data: Compressed TOON string
            profile: Profile used for compression

        Returns:
            Decompressed data
        """

        try:
            # Detect compression format and decompress accordingly
            if compressed_data.startswith("TOONv2:"):
                # Advanced TOON format
                return self._decompress_advanced_toon(compressed_data[7:], profile)
            elif "|" in compressed_data and "[" in compressed_data:
                # Basic TOON format
                return self._decompress_basic_toon(compressed_data)
            else:
                # Fallback to JSON
                return json.loads(compressed_data)

        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            raise ValueError(f"Unable to decompress data: {e}")

    def _adaptive_compression(
        self, data: Dict, profile: TOONCompressionProfile = None, level: int = 7
    ) -> str:
        """Adaptive compression that adjusts based on data characteristics"""

        # Analyze data structure
        structure_analysis = self._analyze_data_structure(data)

        # Choose optimal sub-strategies based on data type
        if structure_analysis["is_uniform_array"]:
            return self._compress_uniform_array(data, profile, level)
        elif structure_analysis["has_nested_objects"]:
            return self._hierarchical_compression(data, profile, level)
        elif structure_analysis["has_repeated_patterns"]:
            return self._pattern_based_compression(data, profile, level)
        else:
            return self._semantic_compression(data, profile, level)

    def _semantic_compression(
        self, data: Dict, profile: TOONCompressionProfile = None, level: int = 7
    ) -> str:
        """Semantic compression using domain-specific knowledge"""

        compressed_parts = []

        for key, value in data.items():
            # Apply profile-specific field mappings
            if profile and key in profile.field_mappings:
                compressed_key = profile.field_mappings[key]
            else:
                compressed_key = self._compress_field_name(key, level)

            # Apply semantic value compression
            compressed_value = self._compress_value_semantically(value, profile, level)
            compressed_parts.append(f"{compressed_key}:{compressed_value}")

        return "|".join(compressed_parts)

    def _hierarchical_compression(
        self, data: Dict, profile: TOONCompressionProfile = None, level: int = 7
    ) -> str:
        """Hierarchical compression for nested data structures"""

        def process_hierarchy(obj, depth=0):
            if depth > 3:  # Limit depth to prevent over-complexity
                return str(obj)

            if isinstance(obj, dict):
                if not obj:
                    return "{}"

                items = []
                for k, v in obj.items():
                    compressed_key = self._compress_field_name(k, level)
                    processed_value = process_hierarchy(v, depth + 1)
                    items.append(f"{compressed_key}={processed_value}")

                return "{" + ",".join(items) + "}"

            elif isinstance(obj, list):
                if not obj:
                    return "[]"

                # Check for uniform arrays
                if all(isinstance(x, type(obj[0])) for x in obj):
                    if isinstance(obj[0], dict) and obj:
                        # Array of objects - use object header format
                        first_obj_keys = list(obj[0].keys())
                        header = f"obj[{len(obj)}]{{{','.join(first_obj_keys)}}}"

                        # Extract values in order
                        values = []
                        for item in obj:
                            item_values = []
                            for key in first_obj_keys:
                                val = item.get(key, "")
                                item_values.append(
                                    self._compress_value_semantically(val, None, level)
                                )
                            values.append(",".join(item_values))

                        return header + ":" + ";".join(values)
                    else:
                        # Uniform primitive array
                        return f"{type(obj[0]).__name__}[{len(obj)}]:" + ",".join(
                            str(x) for x in obj
                        )
                else:
                    # Mixed array
                    items = [process_hierarchy(x, depth + 1) for x in obj]
                    return f"[{len(obj)}]:" + ",".join(items)

            else:
                return self._compress_value_semantically(obj, None, level)

        return process_hierarchy(data)

    def _progressive_compression(
        self, data: Dict, profile: TOONCompressionProfile = None, level: int = 7
    ) -> str:
        """Progressive compression with multiple optimization passes"""

        # Pass 1: Basic semantic compression
        pass1_result = self._semantic_compression(data, profile, max(3, level - 2))

        if level <= 3:
            return pass1_result

        # Pass 2: Pattern detection and optimization
        pass2_result = self._apply_pattern_optimizations(pass1_result, level)

        if level <= 6:
            return pass2_result

        # Pass 3: Advanced token optimization
        pass3_result = self._apply_token_optimizations(pass2_result, level)

        return pass3_result

    def _ultra_compression(
        self, data: Dict, profile: TOONCompressionProfile = None, level: int = 10
    ) -> str:
        """Ultra-high compression using all available techniques"""

        # Start with progressive compression
        result = self._progressive_compression(data, profile, level)

        # Apply binary encoding for highly repetitive data
        if len(result) > 1000:  # Only worth it for larger data
            result = self._apply_binary_encoding(result)

        # Apply dictionary compression
        result = self._apply_dictionary_compression(result, profile)

        return result

    def _compress_uniform_array(
        self, data: Dict, profile: TOONCompressionProfile = None, level: int = 7
    ) -> str:
        """Optimized compression for uniform arrays"""

        # Find the main array in the data
        main_array_key = None
        main_array = None

        for key, value in data.items():
            if isinstance(value, list) and len(value) > 1:
                if all(isinstance(item, dict) for item in value):
                    main_array_key = key
                    main_array = value
                    break

        if not main_array:
            return self._semantic_compression(data, profile, level)

        # Extract common keys from objects
        if main_array:
            common_keys = list(main_array[0].keys())

            # Build header
            header_parts = [f"{main_array_key}[{len(main_array)}]"]
            header_parts.extend(f"{key}" for key in common_keys)
            header = ":".join(header_parts)

            # Extract values
            value_rows = []
            for obj in main_array:
                row_values = []
                for key in common_keys:
                    value = obj.get(key, "")
                    compressed_val = self._compress_value_semantically(
                        value, None, level
                    )
                    row_values.append(compressed_val)
                value_rows.append(",".join(row_values))

            # Compress other metadata
            other_data = {k: v for k, v in data.items() if k != main_array_key}
            compressed_metadata = ""
            if other_data:
                compressed_metadata = "|" + self._semantic_compression(
                    other_data, profile, level
                )

            return header + ";" + ";".join(value_rows) + compressed_metadata

        return self._semantic_compression(data, profile, level)

    def _pattern_based_compression(
        self, data: Dict, profile: TOONCompressionProfile = None, level: int = 7
    ) -> str:
        """Compression based on repeated pattern detection"""

        # Flatten data to string for pattern detection
        data_str = json.dumps(data, separators=(",", ":"))

        # Detect repeated patterns
        patterns = self._detect_repeated_patterns(data_str)

        if not patterns:
            return self._semantic_compression(data, profile, level)

        # Apply pattern substitution
        result = data_str
        pattern_dict = {}

        for i, (pattern, count) in enumerate(patterns):
            if count > 2:  # Only substitute patterns that appear 3+ times
                placeholder = f"§{i}§"
                pattern_dict[placeholder] = pattern
                result = result.replace(pattern, placeholder)

        # Combine with semantic compression
        compressed = self._semantic_compression(
            json.loads(result) if result else data, profile, level
        )

        if pattern_dict:
            pattern_dict_str = json.dumps(pattern_dict, separators=(",", ":"))
            return f"PATTERNS:{len(pattern_dict)}:{pattern_dict_str}|{compressed}"

        return compressed

    def _compress_field_name(self, field_name: str, level: int) -> str:
        """Compress field names based on common patterns"""

        # Common field name mappings
        field_mappings = {
            "id": "id",
            "name": "nm",
            "type": "tp",
            "status": "st",
            "timestamp": "ts",
            "created_at": "ca",
            "updated_at": "ua",
            "version": "vr",
            "count": "cnt",
            "value": "val",
            "data": "dt",
            "result": "rs",
            "error": "err",
            "message": "msg",
            "config": "cfg",
            "settings": "set",
            "parameters": "prm",
            "metadata": "meta",
            "season": "yr",
            "week": "wk",
            "team": "tm",
            "game": "gm",
            "player": "ply",
            "score": "sc",
            "points": "pts",
            "rank": "rk",
            "rating": "rtg",
        }

        # Direct mapping for common fields
        if field_name in field_mappings:
            return field_mappings[field_name]

        # Pattern-based compression
        if level >= 7:
            # Remove common prefixes/suffixes
            compressed = field_name
            compressed = re.sub(r"^is_", "", compressed)
            compressed = re.sub(r"^has_", "", compressed)
            compressed = re.sub(r"^can_", "", compressed)
            compressed = re.sub(r"_id$", "", compressed)
            compressed = re.sub(r"_count$", "", compressed)
            compressed = re.sub(r"_time$", "", compressed)
            compressed = re.sub(r"_date$", "", compressed)

            # Camel case to underscores and abbreviate
            compressed = re.sub(r"([A-Z])", r"_\1", compressed).lower()
            words = [w[:3] for w in compressed.split("_") if w]
            if words:
                return "".join(words)

        # Fallback to first few characters
        return field_name[: min(8, len(field_name))]

    def _compress_value_semantically(
        self, value: Any, profile: TOONCompressionProfile = None, level: int = 7
    ) -> str:
        """Compress values using semantic understanding"""

        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "1" if value else "0"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return self._compress_string_value(value, profile, level)
        elif isinstance(value, list):
            if not value:
                return "[]"
            return f"[{len(value)}]:" + ",".join(
                self._compress_value_semantically(v, None, level) for v in value
            )
        elif isinstance(value, dict):
            if not value:
                return "{}"
            items = [
                f"{self._compress_field_name(k, level)}:{self._compress_value_semantically(v, None, level)}"
                for k, v in value.items()
            ]
            return "{" + ",".join(items) + "}"
        else:
            return str(value)

    def _compress_string_value(
        self, value: str, profile: TOONCompressionProfile = None, level: int = 7
    ) -> str:
        """Compress string values intelligently"""

        if not value:
            return ""

        # Check for common values in profile
        if profile and value in profile.common_values:
            return f"${profile.common_values[value]}$"

        # Date/time compression
        if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", value):
            return f"T{value.replace('-', '').replace(':', '').replace('T', '')[:12]}"

        # UUID compression
        if re.match(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", value
        ):
            return f"U{value.replace('-', '')[:16]}"

        # URL compression
        if value.startswith(("http://", "https://")):
            return f"H{hash(value) % 1000000:06d}"

        # High-level compression
        if level >= 8 and len(value) > 20:
            # Use first few chars + hash for long strings
            return f"L{len(value)}:{value[:8]}{hash(value) % 10000:04d}"

        # Escape special characters and return
        escaped = (
            value.replace("|", "\\|")
            .replace(":", "\\:")
            .replace("{", "\\{")
            .replace("}", "\\}")
        )
        return escaped if escaped else value

    def _analyze_data_structure(self, data: Dict) -> Dict[str, Any]:
        """Analyze data structure for optimal compression strategy"""

        analysis = {
            "is_uniform_array": False,
            "has_nested_objects": False,
            "has_repeated_patterns": False,
            "total_fields": 0,
            "nested_depth": 0,
            "data_types": set(),
        }

        def analyze_structure(obj, depth=0):
            analysis["nested_depth"] = max(analysis["nested_depth"], depth)

            if isinstance(obj, dict):
                analysis["total_fields"] += len(obj)
                analysis["has_nested_objects"] = True
                analysis["data_types"].add("dict")

                for value in obj.values():
                    analyze_structure(value, depth + 1)

            elif isinstance(obj, list):
                analysis["data_types"].add("list")

                if len(obj) > 1:
                    # Check if uniform
                    first_type = type(obj[0])
                    if all(isinstance(x, first_type) for x in obj):
                        analysis["is_uniform_array"] = True

                for item in obj:
                    analyze_structure(item, depth + 1)

            else:
                analysis["data_types"].add(type(obj).__name__)

        analyze_structure(data)

        # Check for repeated patterns in JSON representation
        json_str = json.dumps(data, separators=(",", ":"))
        if len(json_str) > 100:
            words = json_str.split('"')
            word_counts = Counter(words)
            repeated_patterns = sum(1 for count in word_counts.values() if count > 3)
            analysis["has_repeated_patterns"] = repeated_patterns > 5

        return analysis

    def _detect_data_profile(self, data: Any) -> str:
        """Detect the most appropriate compression profile for the data"""

        if isinstance(data, dict):
            # Check for known data patterns
            data_keys = set(data.keys())

            # CFBD games pattern
            if {"game_id", "home_team", "away_team", "season"} & data_keys:
                return "cfbd_games"

            # Predictions pattern
            elif {"confidence", "prediction", "model"} & data_keys:
                return "predictions"

            # Workflow pattern
            elif {"workflow_id", "agent_id", "status"} & data_keys:
                return "workflow"

        return "default"

    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression performance statistics"""

        return {
            "available_strategies": list(self.compression_strategies.keys()),
            "available_profiles": list(self.compression_profiles.keys()),
            "cache_size": len(self.compression_cache),
            "field_type_cache_size": len(self.field_type_cache),
            "recommended_strategy": "adaptive",
            "recommended_level": 7,
        }

    def benchmark_strategies(self, test_data: Dict) -> Dict[str, CompressionAnalysis]:
        """Benchmark all compression strategies on test data"""

        results = {}

        for strategy_name, strategy_func in self.compression_strategies.items():
            try:
                _, analysis = self.compress(test_data, strategy=strategy)
                results[strategy_name] = analysis
            except Exception as e:
                logger.warning(f"Benchmark failed for {strategy_name}: {e}")

        return results

    def _analyze_optimizations_applied(
        self, original_data: Dict, compressed_output: str
    ) -> List[str]:
        """Analyze what optimizations were applied during compression"""

        optimizations = []

        if "|" in compressed_output:
            optimizations.append("field_name_compression")

        if "[]" in compressed_output or "[0]:" in compressed_output:
            optimizations.append("array_optimization")

        if "{}" in compressed_output:
            optimizations.append("nested_object_compression")

        if any(char in compressed_output for char in ["§", "$", "T", "U", "H"]):
            optimizations.append("semantic_value_compression")

        if compressed_output.startswith("PATTERNS:"):
            optimizations.append("pattern_substitution")

        return optimizations

    def _fallback_compression(
        self, data: Dict, original_size: int, start_time: float
    ) -> Tuple[str, CompressionAnalysis]:
        """Fallback compression when main strategies fail"""

        compressed = json.dumps(data, separators=(",", ":"))
        compressed_size = len(compressed)

        analysis = CompressionAnalysis(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compressed_size / original_size,
            token_reduction_percent=0,
            compression_time_ms=(time.time() - start_time) * 1000,
            strategy_used="fallback",
            field_optimizations=["json_minification"],
            compression_level=1,
        )

        return compressed, analysis


# Initialize global advanced compressor
advanced_toon_compressor = AdvancedTOONCompressor()
