import pandas as pd
import os
import sys
from typing import Optional, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataManager:
    """
    Standardized data loading and management for the project.
    Centralizes path management and common data operations.
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize DataManager.
        
        Args:
            base_dir: Optional base directory. If None, attempts to find project root.
        """
        self.base_dir = base_dir or self._find_project_root()
        self.data_dir = os.path.join(self.base_dir, 'data')
        
        # Try to integrate with DataConfig
        try:
            if self.base_dir not in sys.path:
                sys.path.append(self.base_dir)
            
            # Import dynamically to avoid hard dependency if config is missing
            from model_pack.config.data_config import DataConfig
            config = DataConfig()
            self.training_data_path = str(config.get_training_data_path())
            logging.info(f"DataManager using config path: {self.training_data_path}")
        except Exception as e:
            logging.debug(f"DataConfig not available: {e}. Using default path.")
            # Prefer updated_training_data.csv if it exists
            updated_path = os.path.join(self.base_dir, 'model_pack', 'updated_training_data.csv')
            if os.path.exists(updated_path):
                self.training_data_path = updated_path
            else:
                self.training_data_path = os.path.join(self.base_dir, 'training_data.csv')
        
    def _find_project_root(self) -> str:
        """
        Attempts to find the project root directory.
        Assumes this script is in 'scripts/' or root.
        """
        current_path = os.path.abspath(os.path.dirname(__file__))
        
        # Check if we are in scripts/
        if os.path.basename(current_path) == 'scripts':
            return os.path.dirname(current_path)
            
        # Check if we are in root (look for requirements.txt)
        if os.path.exists(os.path.join(current_path, 'requirements.txt')):
            return current_path
            
        # Fallback to current working directory
        return os.getcwd()

    def load_training_data(self, filename: Optional[str] = None) -> pd.DataFrame:
        """
        Load training data from CSV.
        
        Args:
            filename: Optional override for filename. If None, uses configured training_data_path.
            
        Returns:
            pd.DataFrame: Loaded data
        """
        if filename:
            # Try direct path first
            file_path = os.path.join(self.base_dir, filename)
            if not os.path.exists(file_path):
                # Try data directory
                file_path = os.path.join(self.data_dir, filename)
        else:
            file_path = self.training_data_path
            
        if not os.path.exists(file_path):
             # Fallback for backward compatibility
             fallback_path = os.path.join(self.base_dir, 'training_data.csv')
             if os.path.exists(fallback_path):
                 file_path = fallback_path
             else:
                 raise FileNotFoundError(f"Could not find training data at {file_path}")
             
        logging.info(f"Loading data from {file_path}")
        return pd.read_csv(file_path)

    def save_data(self, df: pd.DataFrame, filename: str, index: bool = False):
        """
        Save DataFrame to CSV.
        
        Args:
            df: DataFrame to save
            filename: Target filename
            index: Whether to save index
        """
        file_path = os.path.join(self.base_dir, filename)
        logging.info(f"Saving data to {file_path}")
        df.to_csv(file_path, index=index)

if __name__ == "__main__":
    # Simple test
    dm = DataManager()
    print(f"Project Root: {dm.base_dir}")
    try:
        df = dm.load_training_data()
        print(f"Loaded training data shape: {df.shape}")
    except Exception as e:
        print(f"Error loading data: {e}")
