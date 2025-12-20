# FastAI Model Resolution Plan - 2025

## 🎯 Issue Summary

**Model**: `fastai_home_win_model_2025.pkl` (213KB)
**Error**: `persistent IDs in protocol 0 must be ASCII strings`
**Impact**: LOW - Core models (Ridge, XGBoost) fully operational
**Priority**: LOW - Can be addressed in next maintenance cycle
**Est. Resolution Time**: 2-4 hours

---

## 🔍 Root Cause Analysis

### **Technical Investigation**

**Error Pattern**:
```
persistent IDs in protocol 0 must be ASCII strings
```

**File Analysis**:
- **File Size**: 213,014 bytes
- **File Header**: `PK\x03\x04` (ZIP container)
- **Pickle Protocol**: Likely protocol 0 with non-ASCII persistent IDs
- **Affected Files**: Both 2025 and legacy FastAI models

**Likely Causes**:
1. **Python Version Incompatibility**: Model saved with different Python version
2. **Pickle Protocol Mismatch**: Protocol 0 vs. current environment
3. **FastAI Library Version**: Different FastAI version used during training
4. **Environment Dependencies**: Missing or incompatible dependencies

### **Environment Context**

**Current Environment**:
- **Python**: 3.13.5
- **FastAI**: Unknown (likely recent version)
- **Pickle Protocol**: Default (likely protocol 5+)

**Training Environment** (Hypothesized):
- **Python**: 3.8-3.9 (common during model development)
- **FastAI**: Version 2.x
- **Pickle Protocol**: Protocol 0 (explicitly set)

---

## 🛠️ Resolution Strategies

### **Strategy 1: Model Retraining (Recommended)**

**Steps**:
1. **Environment Setup**
   ```bash
   pip install fastai==2.7.13 pandas scikit-learn
   # Use same versions as original training if possible
   ```

2. **Data Preparation**
   ```python
   import pandas as pd
   from fastai.tabular.all import *

   # Load training data
   df = pd.read_csv('updated_training_data.csv')
   df['home_team_win'] = (df['margin'] > 0).astype(int)

   # FastAI TabularDataLoaders setup
   cont_names = ['home_talent', 'away_talent', 'home_elo', 'away_elo',
                 'home_adjusted_epa', 'home_adjusted_epa_allowed',
                 'away_adjusted_epa', 'away_adjusted_epa_allowed']
   cat_names = ['home_team', 'away_team']
   procs = [Categorify, FillMissing, Normalize]

   dataloader = TabularPandas(df, procs, cat_names, cont_names,
                              y_names='home_team_win', splits=RandomSplitter()(df))
   ```

3. **Model Training**
   ```python
   dls = dataloader.dataloaders(bs=64)
   learn = tabular_learner(dls, metrics=accuracy)
   learn.fit_one_cycle(10)  # Adjust epochs as needed

   # Save with current protocol
   learn.export('fastai_home_win_model_2025_fixed.pkl')
   ```

**Advantages**:
- ✅ Resolves compatibility issues permanently
- ✅ Uses current 2025 data
- ✅ Updated with latest FastAI improvements
- ✅ Consistent with other 2025 models

**Estimated Time**: 2-3 hours
**Risk**: LOW

### **Strategy 2: Compatibility Layer (Alternative)**

**Approach**: Create wrapper to handle loading with different protocols

```python
import pickle
import sys

def load_fastai_model_compatible(file_path):
    """Try multiple loading approaches for compatibility"""

    # Method 1: Standard loading
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e1:
        print(f"Standard loading failed: {e1}")

    # Method 2: Latin-1 encoding
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f, encoding='latin1')
    except Exception as e2:
        print(f"Latin-1 loading failed: {e2}")

    # Method 3: Python 2 compatibility
    try:
        import pickle5
        with open(file_path, 'rb') as f:
            return pickle5.load(f)
    except Exception as e3:
        print(f"Pickle5 loading failed: {e3}")

    raise ValueError("All loading methods failed")
```

**Advantages**:
- ✅ Faster implementation
- ✅ Preserves original trained model
- ✅ Lower risk of changing model behavior

**Disadvantages**:
- ❌ May not resolve underlying protocol issues
- ❌ Adds dependency complexity
- ❌ Temporary fix

### **Strategy 3: Environment Recreation (Fallback)**

**Steps**:
1. Create Python 3.8 virtual environment
2. Install original FastAI version
3. Load and re-save model with updated protocol

```bash
# Create legacy environment
python3.8 -m venv fastai_legacy_env
source fastai_legacy_env/bin/activate
pip install fastai==2.7.13

# Conversion script
python convert_fastai_model.py
```

**Advantages**:
- ✅ Preserves original model weights exactly
- ✅ Guarantees compatibility

**Disadvantages**:
- ❌ Complex environment setup
- ❌ Maintenance overhead
- ❌ Not future-proof

---

## 📋 Implementation Plan

### **Phase 1: Preparation (30 minutes)**

1. **Environment Setup**
   - [ ] Backup current model file
   - [ ] Create development branch
   - [ ] Install required dependencies
   - [ ] Validate 2025 data availability

2. **Code Preparation**
   - [ ] Locate original training notebook (`04_fastai_win_probability.ipynb`)
   - [ ] Extract training parameters and architecture
   - [ ] Prepare data preprocessing pipeline

### **Phase 2: Model Retraining (1-2 hours)**

1. **Data Loading and Preprocessing**
   ```python
   # Load and validate data
   df = pd.read_csv('updated_training_data.csv')

   # Recreate training/validation split (temporal)
   train_df = df[df['season'] <= 2024]
   val_df = df[df['season'] == 2025]
   ```

2. **Model Training**
   - [ ] Replicate original architecture
   - [ ] Use same hyperparameters
   - [ ] Train on 2016-2024 data
   - [ ] Validate on 2025 data

3. **Model Evaluation**
   ```python
   # Compare with original performance
   accuracy = learn.validate()[0]
   print(f"FastAI 2025 Accuracy: {accuracy:.3f}")
   ```

### **Phase 3: Integration and Testing (30 minutes)**

1. **Model Saving**
   ```python
   # Save with current protocol
   learn.export('fastai_home_win_model_2025_fixed.pkl')
   ```

2. **Integration Testing**
   - [ ] Test model loading
   - [ ] Verify prediction compatibility
   - [ ] Update model execution engine
   - [ ] Run integration tests

3. **Documentation Update**
   - [ ] Update model documentation
   - [ ] Record training parameters
   - [ ] Update deployment procedures

---

## 🧪 Testing Strategy

### **Unit Tests**
```python
def test_fastai_model_loading():
    """Test model can be loaded successfully"""
    model = load_fastai_model('fastai_home_win_model_2025_fixed.pkl')
    assert model is not None

def test_fastai_predictions():
    """Test model produces valid predictions"""
    model = load_fastai_model('fastai_home_win_model_2025_fixed.pkl')
    predictions = model.predict(sample_data)
    assert 0 <= predictions <= 1
```

### **Integration Tests**
```python
def test_model_engine_integration():
    """Test integration with Model Execution Engine"""
    engine = ModelExecutionEngine()
    result = engine.predict_with_model('fastai_home_win_model_2025_fixed', sample_data)
    assert 'prediction' in result
    assert 'confidence' in result
```

### **Performance Tests**
- Compare new model accuracy vs. original target (~42.3%)
- Verify response time <2 seconds
- Test memory usage and computational efficiency

---

## 📊 Success Criteria

### **Technical Requirements**
- ✅ Model loads without serialization errors
- ✅ Predictions fall within valid range [0, 1]
- ✅ Response time <2 seconds
- ✅ Memory usage within acceptable limits

### **Performance Requirements**
- ✅ Accuracy ≥ 40% (matching documented benchmarks)
- ✅ Calibration similar to original model
- ✅ Temporal validation on 2025 data

### **Integration Requirements**
- ✅ Works with Model Execution Engine
- ✅ Compatible with existing prediction pipeline
- ✅ Passes all integration tests

---

## 🚀 Rollout Plan

### **Pre-Deployment**
1. **Validation**: Complete all testing phases
2. **Backup**: Save current model as backup
3. **Documentation**: Update all relevant documentation
4. **Communication**: Notify stakeholders of upcoming change

### **Deployment**
1. **Swap Models**: Replace problematic model with fixed version
2. **Update Configuration**: Update model references
3. **Verification**: Run smoke tests
4. **Monitoring**: Monitor system performance

### **Post-Deployment**
1. **Performance Monitoring**: Track model accuracy and response times
2. **Issue Tracking**: Monitor for any new issues
3. **Documentation**: Update deployment records

---

## 🔄 Contingency Plans

### **If Retraining Fails**
- Deploy with Strategy 2 (compatibility layer)
- Schedule model retraining for next maintenance cycle
- Document limitations and workarounds

### **If Performance Degradation**
- Keep original model as fallback
- Compare new vs. original performance
- Adjust training parameters if needed

### **If Integration Issues**
- Revert to backup model
- Debug integration issues
- Retry deployment after fixes

---

## 📈 Expected Outcomes

### **Immediate Benefits**
- ✅ FastAI model fully operational
- ✅ Complete model suite available
- ✅ Improved system reliability

### **Long-term Benefits**
- ✅ Consistent pickle protocol across all models
- ✅ Future-proof model deployment
- ✅ Simplified maintenance procedures

### **Risk Mitigation**
- ✅ Eliminates serialization compatibility issues
- ✅ Reduces deployment complexity
- ✅ Improves overall system stability

---

*Implementation Timeline: Next maintenance cycle*
*Estimated Effort: 2-4 hours*
*Priority: LOW (Core models operational)*
*Success Probability: HIGH (95%)*