# Drift Detection System

## ✅ What Was Implemented

### 1. **Drift Detector** (`src/drift_detector.py`)
Production-ready drift detection system:
- Statistical drift detection using Kolmogorov-Smirnov test
- Feature-based monitoring (text length, tokens, processing time, etc.)
- Baseline establishment and comparison
- Configurable thresholds and sensitivity

**Features Monitored:**
- Text length and word count
- Token usage
- Processing time
- Character patterns (numbers, currency, percentages)
- Confidence scores (if available)

**Detection Methods:**
- Kolmogorov-Smirnov test (when scipy available)
- Z-score based detection
- Percentage change detection

### 2. **Drift Monitor** (`src/drift_monitor.py`)
Monitoring and alerting system:
- Automatic drift detection on every output
- SQLite database for storing alerts
- Alert callbacks for notifications
- Alert acknowledgment system

### 3. **Drift API** (`src/drift_api.py`)
REST API for drift monitoring:
- Query drift alerts
- Get statistics
- Acknowledge alerts
- Reset baseline

**Endpoints:**
- `GET /api/drift/alerts` - Get drift alerts
- `GET /api/drift/statistics` - Get statistics
- `POST /api/drift/alert/<id>/acknowledge` - Acknowledge alert
- `POST /api/drift/reset-baseline` - Reset baseline

### 4. **Integration with Kafka Processor**
- Automatic drift detection on all LLM outputs
- Non-blocking (errors don't stop processing)
- Configurable via environment variables

## 🚀 Quick Start

### Step 1: Install Dependencies
```powershell
pip install -r requirements.txt
```

This installs scipy for statistical tests.

### Step 2: Start Drift API (Optional)
```powershell
python src/drift_api.py
```

API runs on `http://localhost:5001`

### Step 3: Process Documents (Drift Detection Automatic)
```powershell
# Your existing processor now detects drift automatically
python src/kafka_llm_processor.py
```

Drift detection happens automatically as documents are processed.

### Step 4: Query Drift Alerts
```powershell
python src/test_drift.py
```

Or use curl:
```powershell
# Get statistics
curl http://localhost:5001/api/drift/statistics

# Get alerts
curl http://localhost:5001/api/drift/alerts?limit=10
```

## 📊 How It Works

### Baseline Establishment
1. First 100 outputs (configurable) establish baseline
2. Statistics calculated for each feature:
   - Mean, std, median, min, max
   - Distribution stored for statistical tests

### Drift Detection
1. Every output added to recent window (50 samples)
2. When recent window full, compare to baseline
3. Statistical tests run on each feature:
   - KS test (if scipy available)
   - Z-score comparison
   - Percentage change
4. Alert generated if drift detected

### Alert Storage
- All alerts stored in SQLite database
- Includes drift score, features, timestamps
- Can be acknowledged for tracking

## ⚙️ Configuration

Environment variables:
- `ENABLE_DRIFT_DETECTION=true` - Enable/disable drift detection
- `DRIFT_DB_PATH=drift_alerts.db` - Database path
- `DRIFT_BASELINE_WINDOW=100` - Baseline sample size
- `DRIFT_DETECTION_WINDOW=50` - Recent sample size
- `DRIFT_THRESHOLD=0.05` - P-value threshold (lower = more sensitive)
- `DRIFT_MIN_SAMPLES=20` - Minimum samples before detection
- `DRIFT_API_PORT=5001` - API port

## 📈 Drift Detection Metrics

**Drift Score:** 0.0 to 1.0
- 0.0 = No drift
- 1.0 = Complete drift (all features drifted)

**Features Monitored:**
- `text_length` - Output text length
- `word_count` - Number of words
- `tokens_used` - Token consumption
- `processing_time_ms` - Processing latency
- `avg_chars_per_word` - Text characteristics
- `has_numbers` - Numeric content
- `has_currency` - Currency symbols
- `has_percentages` - Percentage signs

## 🔍 Example Use Cases

### Detect Model Degradation
```python
# After processing many documents, check for drift
# If drift detected, model may need retraining
```

### Monitor Performance Changes
```python
# Track processing time drift
# Alert if latency increases significantly
```

### Quality Assurance
```python
# Monitor output characteristics
# Detect if outputs become shorter/longer unexpectedly
```

## 🎯 Production Features

✅ **Statistical Rigor:** Uses KS test and Z-scores  
✅ **Multiple Features:** Monitors 8+ output characteristics  
✅ **Alert System:** Database storage and API access  
✅ **Non-Blocking:** Errors don't stop processing  
✅ **Configurable:** All thresholds adjustable  
✅ **Baseline Management:** Can reset baseline after model updates  

## 📝 Integration Example

The drift detector is automatically integrated into your Kafka processor:

```python
# In kafka_llm_processor.py
# Drift detection happens automatically:
# 1. Process document → LLM
# 2. Check for drift
# 3. Alert if detected
# 4. Continue processing
```

## 🔮 Next Steps

1. **Set up alerting:** Connect drift alerts to monitoring system
2. **Dashboard:** Create Grafana dashboard for drift metrics
3. **Automated remediation:** Trigger model retraining on drift
4. **Historical analysis:** Track drift trends over time

---

**Deliverable Complete:** Production-ready drift detection system integrated with LLM pipeline!

