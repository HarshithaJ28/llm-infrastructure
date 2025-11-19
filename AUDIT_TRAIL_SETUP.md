# Audit Trail System & Compliance API

## ✅ What Was Implemented

### 1. **Audit Logger** (`src/audit_logger.py`)
Production-ready audit logging system:
- SQLite database for audit logs
- Comprehensive schema with indexes
- Request tracking with SHA256 hashing
- Support for tenant/user isolation
- Statistics and querying capabilities

**Features:**
- Request ID tracking
- Input hash for duplicate detection
- Model version and parameters logging
- Processing time and token usage
- Status tracking (success/error)
- Timestamp indexing for time-range queries

### 2. **Explainability Module** (`src/explainability.py`)
LLM decision explanations:
- LIME integration for feature importance
- Fallback to keyword extraction if LIME unavailable
- Batch explanation support

**Features:**
- Feature importance scoring
- Financial keyword extraction
- Configurable number of features
- Error handling and fallbacks

### 3. **Compliance API** (`src/compliance_api.py`)
REST API for regulatory compliance:
- Query audit logs
- Export to CSV
- Statistics and reporting
- Duplicate detection

**Endpoints:**
- `POST /api/compliance/query` - Query logs with filters
- `GET /api/compliance/request/<id>` - Get specific request
- `GET /api/compliance/duplicates/<hash>` - Find duplicates
- `GET /api/compliance/statistics` - Get statistics
- `POST /api/compliance/export` - Export to CSV

### 4. **Integration with Kafka Processor**
- Automatic audit logging for all requests
- Configurable via environment variables
- Non-blocking (errors don't stop processing)

## 🚀 Quick Start

### Step 1: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 2: Start Compliance API
```powershell
python src/compliance_api.py
```

API runs on `http://localhost:5000`

### Step 3: Process Documents (Audit Logging Automatic)
```powershell
# Your existing processor now logs automatically
python src/kafka_llm_processor.py
```

### Step 4: Query Audit Logs
```powershell
python src/test_compliance_api.py
```

Or use curl:
```powershell
# Get statistics
curl http://localhost:5000/api/compliance/statistics

# Query logs
curl -X POST http://localhost:5000/api/compliance/query -H "Content-Type: application/json" -d '{"status":"success","limit":10}'
```

## 📊 Database Schema

Audit logs stored in `audit_logs.db` (SQLite) with:
- Request tracking (request_id, timestamp)
- Input hashing (input_hash for deduplication)
- Model information (version, parameters)
- Output tracking (output_text, tokens_used)
- Metadata (tenant_id, user_id, source)
- Status and error tracking

## 🔍 Example Queries

### Find All Requests for a Document (by hash)
```python
import requests
response = requests.post('http://localhost:5000/api/compliance/query', json={
    'input_hash': 'abc123...',
    'limit': 100
})
```

### Get All Errors
```python
response = requests.post('http://localhost:5000/api/compliance/query', json={
    'status': 'error',
    'limit': 50
})
```

### Export Logs for Date Range
```python
response = requests.post('http://localhost:5000/api/compliance/export', json={
    'start_time': '2025-11-19T00:00:00Z',
    'end_time': '2025-11-20T00:00:00Z'
})
# Returns CSV file
```

## ⚙️ Configuration

Environment variables:
- `ENABLE_AUDIT_LOGGING=true` - Enable/disable audit logging
- `AUDIT_DB_PATH=audit_logs.db` - Database path
- `COMPLIANCE_API_PORT=5000` - API port
- `COMPLIANCE_API_HOST=0.0.0.0` - API host

## 📈 Compliance Features

✅ **SEC/FINRA Compliance:**
- Complete audit trail
- Request deduplication
- Time-range queries
- Export capabilities
- Explainability support

✅ **Production Ready:**
- Error handling
- Database indexes
- Query optimization
- CSV export
- Statistics

## 🎯 Next Steps

1. **Add LIME explanations** (requires: `pip install lime`)
2. **Deploy Compliance API** to production
3. **Add encryption** for sensitive data
4. **Set up monitoring** for audit logs
5. **Add drift detection** (Week 2, Day 11-14)

---

**Deliverable Complete:** Audit trail system with explainability and compliance API!

