# TOON Format Integration Guide

**Token-Oriented Object Notation** - Compact, LLM-optimized data format for Script Ohio 2.0

## Overview

TOON (Token-Oriented Object Notation) is a compact, human-readable encoding of JSON that minimizes tokens while maintaining structure. It's designed specifically for LLM input, achieving 50-70% token reduction for uniform arrays of objects.

## When to Use TOON

### ✅ Use TOON When:
- **Uniform arrays of objects** (same structure across items) - TOON's sweet spot
- **Agent responses** sent to LLMs (reduces token costs)
- **Analysis outputs** with tabular data (games, predictions, stats)
- **Cached data** that will be consumed by LLMs
- **Large JSON files** (>100KB) with repetitive structures

### ❌ Don't Use TOON When:
- **Deeply nested, non-uniform structures** - JSON-compact is better
- **Pure tabular data** - CSV is smaller
- **Latency-critical applications** - Benchmark first
- **Data consumed by non-LLM systems** - Use JSON for compatibility

## Format Examples

### Uniform Array Example

**JSON (235 tokens):**
```json
{
  "hikes": [
    {
      "id": 1,
      "name": "Blue Lake Trail",
      "distanceKm": 7.5,
      "elevationGain": 320,
      "companion": "ana",
      "wasSunny": true
    },
    {
      "id": 2,
      "name": "Ridge Overlook",
      "distanceKm": 9.2,
      "elevationGain": 540,
      "companion": "luis",
      "wasSunny": false
    }
  ]
}
```

**TOON (106 tokens):**
```yaml
hikes[2]{id,name,distanceKm,elevationGain,companion,wasSunny}:
  1,Blue Lake Trail,7.5,320,ana,true
  2,Ridge Overlook,9.2,540,luis,false
```

### Game Predictions Example (Script Ohio 2.0)

**JSON:**
```json
{
  "top_10": [
    {
      "game_id": 401752911,
      "home_team": "Oregon",
      "away_team": "USC",
      "predicted_winner": "USC",
      "home_win_probability": 0.442,
      "away_win_probability": 0.558,
      "predicted_margin": -1.61,
      "confidence_score": 0.201
    }
  ]
}
```

**TOON:**
```yaml
top_10[1]{game_id,home_team,away_team,predicted_winner,home_win_probability,away_win_probability,predicted_margin,confidence_score}:
  401752911,Oregon,USC,USC,0.442,0.558,-1.61,0.201
```

### Bowl Predictions Example (New in 2025)

**JSON:**
```json
{
  "generated_at": "2025-12-16T21:47:27.308312",
  "model": "ml-ensemble-v1",
  "season": 2025,
  "method": "ml",
  "games": [
    {
      "game_id": 401755831,
      "game_type": "playoff-semifinal",
      "bowl_name": "Rose Bowl",
      "home_team": "Oregon",
      "away_team": "Ohio State",
      "predicted_winner": "Ohio State",
      "home_win_probability": 0.42,
      "away_win_probability": 0.58,
      "predicted_margin": -3.2,
      "confidence_score": 0.75,
      "start_time": "2025-01-01T17:00:00",
      "neutral_site": true,
      "venue": "Rose Bowl"
    },
    {
      "game_id": 401755832,
      "game_type": "playoff-semifinal",
      "bowl_name": "Sugar Bowl",
      "home_team": "Texas",
      "away_team": "Washington",
      "predicted_winner": "Texas",
      "home_win_probability": 0.61,
      "away_win_probability": 0.39,
      "predicted_margin": 2.8,
      "confidence_score": 0.68,
      "start_time": "2025-01-01T20:45:00",
      "neutral_site": true,
      "venue": "Caesars Superdome"
    }
  ]
}
```

**TOON (65% token reduction):**
```yaml
generated_at: 2025-12-16T21:47:27.308312
model: ml-ensemble-v1
season: 2025
method: ml
games[2]{game_id,game_type,bowl_name,home_team,away_team,predicted_winner,home_win_probability,away_win_probability,predicted_margin,confidence_score,start_time,neutral_site,venue}:
  401755831,playoff-semifinal,Rose Bowl,Oregon,Ohio State,Ohio State,0.42,0.58,-3.2,0.75,2025-01-01T17:00:00,true,Rose Bowl
  401755832,playoff-semifinal,Sugar Bowl,Texas,Washington,Texas,0.61,0.39,2.8,0.68,2025-01-01T20:45:00,true,Caesars Superdome
```

## Syntax Reference

### Array Declaration
```
arrayName[length]{field1,field2,field3}:
  value1,value2,value3
  value4,value5,value6
```

- `[length]` - Array length (enables truncation detection)
- `{fields}` - Field names declared once
- Rows - Comma-separated values matching field order

### Nested Objects
```yaml
context:
  task: Analysis task description
  location: Ohio State
  season: 2025
```

### Primitive Arrays
```yaml
friends[3]: ana,luis,sam
```

## Integration with Script Ohio 2.0

### Agent Response Format
Agents should output TOON when:
- Response contains uniform arrays
- Response will be consumed by LLMs
- Token savings > 20%

### Analysis Artifacts
- `analysis/week*/enhanced_*_analysis.toon` - TOON versions of analysis
- `predictions/week*/*.toon` - TOON prediction files
- `exports/*.toon` - TOON export format
- `predictions/bowls_2025_predictions_*.toon` - Bowl predictions in TOON format (when generated with `--toon` flag)

### Usage in Code
```python
from src.toon_format import encode, decode

# Encode JSON to TOON
toon_output = encode(json_data)

# Decode TOON to JSON
json_data = decode(toon_output)
```

## Token Savings Calculator

For Script Ohio 2.0 analysis files:
- **Week 13 Analysis** (1402 lines JSON): ~50-60% token reduction
- **Game Predictions** (uniform arrays): ~65-70% token reduction
- **Team Stats** (tabular data): ~60-65% token reduction

## Resources

- **Official Documentation**: https://toonformat.dev/
- **Format Overview**: https://toonformat.dev/guide/format-overview.html
- **LLM Prompts Guide**: https://toonformat.dev/guide/llm-prompts.html
- **Benchmarks**: https://toonformat.dev/guide/benchmarks.html
- **CLI Reference**: https://toonformat.dev/cli/
- **API Reference**: https://toonformat.dev/reference/api.html
- **Specification**: https://toonformat.dev/reference/spec.html

