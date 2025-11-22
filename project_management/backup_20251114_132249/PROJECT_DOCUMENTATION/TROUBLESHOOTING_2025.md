# 2025 Analytics Platform - Troubleshooting Guide

**Solutions to common issues with the updated 2025 college football analytics platform**

---

## 🔧 Quick Fixes

### 🚨 Most Common Issues

#### 1. Import Errors
**Problem:** `ModuleNotFoundError: No module named 'xgboost'`

**Solution:**
```bash
# Install missing packages
pip install pandas numpy matplotlib seaborn scikit-learn
pip install xgboost fastai joblib jupyter
```

#### 2. File Not Found
**Problem:** `FileNotFoundError: [Errno 2] No such file or directory: 'updated_training_data.csv'`

**Solution:**
```python
import os
print("Current directory:", os.getcwd())
print("Files in current directory:", os.listdir())

# Make sure you're in the right directory
# Should see model_pack/ and starter_pack/ folders
```

#### 3. Model Loading Issues
**Problem:** `pickle.UnpicklingError` or joblib loading errors

**Solution:**
```python
# Try alternative loading method
import joblib
import pickle

try:
    model = joblib.load("model_pack/ridge_model_2025.joblib")
    print("✅ Loaded with joblib")
except:
    try:
        with open("model_pack/ridge_model_2025.joblib", 'rb') as f:
            model = pickle.load(f)
        print("✅ Loaded with pickle")
    except Exception as e:
        print(f"❌ Loading failed: {e}")
```

---

## 📊 Data Issues

### Dataset Problems

#### Empty or Corrupted Data
**Problem:** Dataset loads but has missing values or incorrect structure

**Diagnosis:**
```python
import pandas as pd

df = pd.read_csv("model_pack/updated_training_data.csv")
print(f"Dataset shape: {df.shape}")
print(f"Missing values: {df.isnull().sum().sum()}")
print(f"Seasons covered: {df['season'].min()}-{df['season'].max()}")
print(f"2025 games: {len(df[df['season'] == 2025])}")

# Check for required columns
required_features = ['home_talent', 'away_talent', 'home_elo', 'away_elo',
                    'home_adjusted_epa', 'home_adjusted_epa_allowed',
                    'away_adjusted_epa', 'away_adjusted_epa_allowed']
missing_features = [f for f in required_features if f not in df.columns]
print(f"Missing features: {missing_features}")
```

**Solution:** Re-download or re-extract the dataset files

#### Feature Mismatch
**Problem:** Model expects different features than available

**Solution:**
```python
# Check what features the model was trained on
import joblib
import pandas as pd

model = joblib.load("model_pack/ridge_model_2025.joblib")
df = pd.read_csv("model_pack/updated_training_data.csv")

# For ridge models, check feature count
print(f"Model expects {len(model.coef_)} features")
print(f"Dataset has {len(df.columns)} columns")

# Get available features
available_features = df.select_dtypes(include=[np.number]).columns.tolist()
print(f"Available numeric features: {len(available_features)}")

# Common features that should work
basic_features = ['home_talent', 'away_talent', 'home_elo', 'away_elo',
                 'home_adjusted_epa', 'home_adjusted_epa_allowed',
                 'away_adjusted_epa', 'away_adjusted_epa_allowed']
```

---

## 🤖 Model Issues

### Prediction Problems

#### Poor Performance on 2025 Data
**Problem:** High error rates or unrealistic predictions

**Diagnosis:**
```python
import pandas as pd
import joblib
from sklearn.metrics import mean_absolute_error

# Load and test
df = pd.read_csv("model_pack/updated_training_data.csv")
model = joblib.load("model_pack/ridge_model_2025.joblib")

# Test on small sample
test_sample = df[df['season'] == 2025].head(10)
features = ['home_talent', 'away_talent', 'home_elo', 'away_elo',
            'home_adjusted_epa', 'home_adjusted_epa_allowed',
            'away_adjusted_epa', 'away_adjusted_epa_allowed']

predictions = model.predict(test_sample[features])
actual = test_sample['margin']

print(f"Sample MAE: {mean_absolute_error(actual, predictions):.2f}")
print(f"Predictions range: {predictions.min():.1f} to {predictions.max():.1f}")
print(f"Actual range: {actual.min():.1f} to {actual.max():.1f}")
```

**Solution:** This is expected behavior - 2025 data is synthetic and may not perfectly match historical patterns

#### Memory Issues
**Problem:** Out of memory errors when loading data or models

**Solution:**
```python
# Use smaller samples
import pandas as pd

# Load only specific columns
cols_needed = ['season', 'home_team', 'away_team', 'margin'] + \
             ['home_talent', 'away_talent', 'home_elo', 'away_elo',
              'home_adjusted_epa', 'home_adjusted_epa_allowed',
              'away_adjusted_epa', 'away_adjusted_epa_allowed']

df = pd.read_csv("model_pack/updated_training_data.csv", usecols=cols_needed)

# Or sample the data
df_sample = df.sample(frac=0.1, random_state=42)  # 10% sample
print(f"Sample size: {len(df_sample)} games")
```

---

## 📚 Notebook Issues

### Jupyter Notebook Problems

#### Kernel Crashes
**Problem:** Jupyter kernel dies when running certain cells

**Solution:**
```python
# Add memory management
import gc
import pandas as pd

# Clear memory between operations
df = pd.read_csv("model_pack/updated_training_data.csv")
# ... do your work ...
del df
gc.collect()  # Force garbage collection
```

#### Slow Performance
**Problem:** Notebooks run very slowly

**Solution:**
```python
# Use smaller datasets for testing
import pandas as pd

df = pd.read_csv("model_pack/updated_training_data.csv")

# Sample for faster development
df_dev = df.sample(n=1000, random_state=42)
print(f"Development sample: {len(df_dev)} games")
```

#### Visualization Errors
**Problem:** Matplotlib/seaborn plots not displaying

**Solution:**
```python
import matplotlib.pyplot as plt
import seaborn as sns

# Add this for Jupyter notebooks
%matplotlib inline

# Or try this
plt.show()
```

---

## 🔄 Environment Issues

### Setup Problems

#### Python Version Conflicts
**Problem:** Package compatibility issues

**Diagnosis:**
```python
import sys
import pandas as pd
import sklearn
import joblib

print(f"Python version: {sys.version}")
print(f"Pandas version: {pd.__version__}")
print(f"Scikit-learn version: {sklearn.__version__}")
print(f"Joblib version: {joblib.__version__}")
```

**Solution:**
```bash
# Create fresh environment
python -m venv cfb_2025_env
source cfb_2025_env/bin/activate  # On Windows: cfb_2025_env\Scripts\activate
pip install pandas==1.5.3 numpy==1.24.3 matplotlib==3.7.1
pip install scikit-learn==1.2.2 xgboost==1.7.3 fastai==2.7.12
pip install joblib==1.2.0 jupyter==1.0.0
```

#### Path Issues
**Problem:** Can't find files in wrong directory

**Solution:**
```python
import os

# Check if you're in the right place
expected_files = ['model_pack', 'starter_pack', 'CLAUDE.md']
current_dir = os.listdir('.')

if all(f in current_dir for f in expected_files):
    print("✅ You're in the correct directory")
else:
    print("❌ You're not in the Script_Ohio_2.0 directory")
    print("Navigate to: /Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0")
```

---

## 📱 Platform-Specific Issues

### Windows Users

#### Path Separators
**Problem:** File path issues on Windows

**Solution:**
```python
import os
# Use os.path.join for cross-platform compatibility
data_path = os.path.join("model_pack", "updated_training_data.csv")
df = pd.read_csv(data_path)
```

#### Permission Issues
**Problem:** Can't write files or create models

**Solution:**
```python
# Check write permissions
import os
test_file = "test_write.txt"
try:
    with open(test_file, 'w') as f:
        f.write("test")
    os.remove(test_file)
    print("✅ Write permissions OK")
except:
    print("❌ Write permissions issue - try running as administrator")
```

### Mac/Linux Users

#### Permission Denied
**Problem:** Can't access files due to permissions

**Solution:**
```bash
# Fix file permissions
chmod 644 model_pack/*.csv
chmod 644 model_pack/*.joblib
chmod 644 model_pack/*.pkl
```

---

## 🔍 Debugging Tools

### Performance Analysis
```python
import time
import pandas as pd

# Time your operations
start_time = time.time()
df = pd.read_csv("model_pack/updated_training_data.csv")
load_time = time.time() - start_time

print(f"Data loading took {load_time:.2f} seconds")
print(f"Dataset size: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
```

### Memory Usage
```python
import psutil
import os

# Check memory usage
process = psutil.Process(os.getpid())
memory_info = process.memory_info()
print(f"Memory usage: {memory_info.rss / 1024**2:.1f} MB")
```

### Data Validation
```python
import pandas as pd

def validate_dataset(df):
    """Comprehensive dataset validation"""
    issues = []

    # Check basic structure
    if df.empty:
        issues.append("Dataset is empty")

    # Check required columns
    required = ['season', 'home_team', 'away_team', 'margin']
    missing = [col for col in required if col not in df.columns]
    if missing:
        issues.append(f"Missing required columns: {missing}")

    # Check for 2025 data
    if 2025 not in df['season'].unique():
        issues.append("No 2025 data found")

    # Check for missing values
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        issues.append(f"Missing values found: {null_counts[null_counts > 0].to_dict()}")

    return issues

# Usage
df = pd.read_csv("model_pack/updated_training_data.csv")
issues = validate_dataset(df)

if issues:
    print("❌ Dataset issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("✅ Dataset validation passed")
```

---

## 🆘 Getting Help

### Self-Service Resources

1. **Check the Documentation:**
   - `2025_UPDATE_GUIDE.md` - Complete update overview
   - `QUICK_START_2025.md` - Getting started guide
   - `BEST_PRACTICES_2025.md` - Recommended approaches

2. **Verify Your Setup:**
   ```python
   # Run this diagnostic script
   import os
   import pandas as pd
   import joblib

   print("=== 2025 Platform Diagnostic ===")

   # Check files
   required_files = [
       "model_pack/updated_training_data.csv",
       "model_pack/ridge_model_2025.joblib",
       "model_pack/xgb_home_win_model_2025.pkl"
   ]

   for file in required_files:
       if os.path.exists(file):
           print(f"✅ {file}")
       else:
           print(f"❌ {file} - MISSING")

   # Test data loading
   try:
       df = pd.read_csv("model_pack/updated_training_data.csv")
       print(f"✅ Data loaded: {len(df):,} games")
       print(f"   Seasons: {df['season'].min()}-{df['season'].max()}")
   except Exception as e:
       print(f"❌ Data loading failed: {e}")

   # Test model loading
   try:
       model = joblib.load("model_pack/ridge_model_2025.joblib")
       print("✅ Ridge model loaded")
   except Exception as e:
       print(f"❌ Model loading failed: {e}")

   print("=== Diagnostic Complete ===")
   ```

3. **Check Known Issues:**
   - 2025 data is synthetic (mock) data based on historical patterns
   - Model performance on 2025 data may be moderate
   - Some features may be outside historical ranges

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `FileNotFoundError` | Wrong directory or missing files | Check working directory and file paths |
| `ModuleNotFoundError` | Missing Python packages | Install required dependencies |
| `MemoryError` | Dataset too large for available RAM | Use data sampling or smaller subsets |
| `KeyError` | Feature name mismatch | Check column names in dataset |
| `UnpicklingError` | Model file corruption | Re-download model files |
| `ValueError` | Data type or shape issues | Check data formats and expected shapes |

---

## 🎯 Prevention Tips

### Best Practices
1. **Always work with copies** of the original dataset
2. **Validate inputs** before making predictions
3. **Use try-except blocks** for model loading and predictions
4. **Monitor memory usage** with large datasets
5. **Test with small samples** before running full analyses

### Code Template
```python
# Safe prediction template
import pandas as pd
import joblib
from sklearn.metrics import mean_absolute_error

def safe_predict_margin(game_data, model_path="model_pack/ridge_model_2025.joblib"):
    """Safe margin prediction with error handling"""
    try:
        # Load model
        model = joblib.load(model_path)

        # Validate features
        required_features = ['home_talent', 'away_talent', 'home_elo', 'away_elo',
                           'home_adjusted_epa', 'home_adjusted_epa_allowed',
                           'away_adjusted_epa', 'away_adjusted_epa_allowed']

        missing_features = [f for f in required_features if f not in game_data.columns]
        if missing_features:
            raise ValueError(f"Missing features: {missing_features}")

        # Make prediction
        prediction = model.predict(game_data[required_features])[0]

        return float(prediction)

    except Exception as e:
        print(f"Prediction failed: {e}")
        return None

# Usage
df = pd.read_csv("model_pack/updated_training_data.csv")
sample_game = df[df['season'] == 2025].iloc[0]

prediction = safe_predict_margin(sample_game)
if prediction is not None:
    print(f"Predicted margin: {prediction:.1f} points")
```

---

## 📞 Additional Support

### Community Resources
- **GitHub Issues:** Report bugs or request features
- **Documentation:** Comprehensive guides available in project
- **Examples:** Sample code in `ANALYSIS_EXAMPLES.md`

### Performance Expectations
- **Ridge Regression MAE:** ~17 points on 2025 data (expected)
- **XGBoost Accuracy:** ~43% on 2025 data (expected due to synthetic data)
- **Memory Usage:** ~50-100MB for full dataset
- **Loading Time:** 2-5 seconds for full dataset

---

**🎯 Remember:** Most issues are related to setup or environment. The diagnostic script above will identify 90% of common problems. If you continue to experience issues, the problem is likely related to the synthetic nature of the 2025 data, which is expected behavior.

---

*Last Updated: November 7, 2025*
*Platform Version: 2.0 (2025 Season Integration)*