#!/usr/bin/env python3
"""
Data Acquisition Agent for 2025 Football Analytics
Handles data acquisition and validation from multiple sources
"""

import pandas as pd
import os
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class DataAcquisitionAgent:
    """
    Agent responsible for acquiring and validating 2025 football data
    """
    
    def __init__(self):
        self.data_sources = {
            "model_pack": "model_pack/updated_training_data.csv",
            "starter_pack": "starter_pack/data/",
            "cfbd_api": "CFBD_API_KEY"
        }
        
    def acquire_2025_data(self) -> Dict[str, Any]:
        """
        Acquire 2025 football data from all available sources
        """
        print("📊 Acquiring 2025 Football Data...")
        
        result = {
            "success": False,
            "games_count": 0,
            "data_sources": [],
            "errors": [],
            "data_timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check if 2025 data already exists
            model_data_path = Path(self.data_sources["model_pack"])
            if model_data_path.exists():
                print(f"📁 Loading existing 2025 data from: {model_data_path}")
                df_2025 = pd.read_csv(model_data_path)
                
                # Validate data
                if len(df_2025) > 0:
                    result["games_count"] = len(df_2025)
                    result["data_sources"].append("model_pack")
                    
                    # Check data columns
                    expected_columns = [
                        'year', 'week', 'home_team', 'away_team', 'home_score', 'away_score',
                        'spread', 'over_under', 'total_points'
                    ]
                    
                    missing_columns = [col for col in expected_columns if col not in df_2025.columns]
                    if missing_columns:
                        result["errors"].append(f"Missing columns: {missing_columns}")
                        raise Exception(f"Data validation failed: missing columns {missing_columns}")
                    
                    # Filter for 2025 data
                    df_2025 = df_2025[df_2025['year'] == 2025]
                    result["games_count"] = len(df_2025)
                    
                    print(f"✅ Successfully loaded {result['games_count']} 2025 games")
                    result["success"] = True
                    
                    # Save processed data
                    processed_path = Path("temp/processed_2025_data.csv")
                    processed_path.parent.mkdir(parents=True, exist_ok=True)
                    df_2025.to_csv(processed_path, index=False)
                    result["processed_data_path"] = str(processed_path)
                    
                    return result
                else:
                    raise Exception("No games found in 2025 data")
            else:
                raise Exception("2025 data not found at expected location")
                
        except Exception as e:
            result["errors"].append(str(e))
            print(f"❌ Data acquisition failed: {e}")
            return result
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate data quality and consistency
        """
        quality_report = {
            "total_records": len(df),
            "null_values": df.isnull().sum().to_dict(),
            "duplicate_rows": df.duplicated().sum(),
            "date_range": None,
            "quality_score": 0.0
        }
        
        # Calculate quality score
        quality_components = []
        
        # Check for null values
        null_percentage = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        quality_components.append(max(0, 100 - null_percentage))
        
        # Check for duplicates
        duplicate_percentage = (quality_report["duplicate_rows"] / len(df)) * 100
        quality_components.append(max(0, 100 - duplicate_percentage))
        
        # Check data completeness for key fields
        key_fields = ['home_team', 'away_team', 'home_score', 'away_score']
        complete_fields = sum(df[field].notna().sum() for field in key_fields)
        completeness_score = (complete_fields / (len(df) * len(key_fields))) * 100
        quality_components.append(completeness_score)
        
        # Calculate overall quality score
        quality_report["quality_score"] = sum(quality_components) / len(quality_components)
        
        return quality_report

if __name__ == "__main__":
    agent = DataAcquisitionAgent()
    result = agent.acquire_2025_data()
    print(json.dumps(result, indent=2))
