# Audit Trail System & Compliance API

## Implementation Overview

### 1. Audit Logger (`src/audit_logger.py`)

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

### 2. Explainability Module (`src/explainability.py`)

LLM decision explanations:
- LIME integration for feature importance
- Fallback to keyword extraction if LIME unavailable
- Batch explanation support

**Features:**
- Feature importance scoring
- Financial keyword extraction
- Configurable number of features
- Error handling and fallbacks

### 3. Compliance API (`src/compliance_api.py`)

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

### 4. Integration with Kafka Processor

- Automatic audit logging for all requests
- Configurable via environment variables
- Non-blocking (errors don't stop processing)

## Quick Start

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Start Compliance API

```bash
python src/compliance_api.py
```

API runs on `http://localhost:5000`

### Step 3: Process Documents (Audit Logging Automatic)

```bash
# Processor automatically logs all requests
python src/kafka_llm_processor.py
```

### Step 4: Query Audit Logs

```bash
python src/test_compliance_api.py
```

Or use curl:

```bash
# Get statistics
curl http://localhost:5000/api/compliance/statistics

# Query logs
curl -X POST http://localhost:5000/api/compliance/query \
  -H "Content-Type: application/json" \
  -d '{"status":"success","limit":10}'
```

## Database Schema

Audit logs stored in `audit_logs.db` (SQLite) with:
- Request tracking (request_id, timestamp)
- Input hashing (input_hash for deduplication)
- Model information (version, parameters)
- Output tracking (output_text, tokens_used)
- Metadata (tenant_id, user_id, source)
- Status and error tracking

## Example Queries

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

## Privacy-by-Design Features

### Field Masking & Anonymization

The audit logger includes privacy-by-design features for GDPR/CCPA compliance:

**Automatic Field Masking:**
- Email addresses → `[EMAIL_MASKED]`
- Phone numbers → `[PHONE_MASKED]`
- Credit card numbers → `[CC_MASKED]`
- SSNs → `[SSN_MASKED]`
- Bank account numbers → `[ACCOUNT_MASKED]`

**Enable masking:**

```python
from audit_logger import AuditLogger

audit_logger = AuditLogger(
    mask_sensitive_fields=True,  # Enable PII masking
    anonymize_user_ids=False      # Hash user IDs
)
```

### Database Encryption

Enable encryption for audit database (per-tenant support):

```python
audit_logger = AuditLogger(
    encrypt_db=True,
    encryption_key="your-secure-key-here"  # Or use ENCRYPT_AUDIT_DB_KEY env var
)
```

**Environment variable:**

```bash
export ENCRYPT_AUDIT_DB=true
export ENCRYPT_AUDIT_DB_KEY="your-base64-encoded-key"
```

**Note:** Store encryption keys securely (e.g., AWS Secrets Manager, HashiCorp Vault).

### GDPR Compliance

**Right to Access:**

```python
# Get all data for a user
results = audit_logger.query_logs({
    'user_id': 'user-123',
    'tenant_id': 'tenant-abc'
})
```

**Right to Deletion:**

```python
# Delete all audit logs for a user
deleted_count = audit_logger.delete_user_data(
    user_id='user-123',
    tenant_id='tenant-abc'  # Optional: for multi-tenant isolation
)
```

**Via Compliance API:**

```bash
curl -X POST http://localhost:5000/api/compliance/prebuilt/gdpr \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123", "action": "delete"}'
```

## Multi-Tenancy Support

### Per-Tenant Isolation

The audit system supports secure multi-tenancy with tenant isolation:

**Logging with tenant ID:**

```python
audit_logger.log_request(
    input_text=document,
    model_response=response,
    metadata={
        'tenant_id': 'financial-firm-123',
        'user_id': 'analyst-456',
        'role': 'analyst'  # Optional: for role-based access
    }
)
```

**Querying by tenant:**

```python
# Get all logs for a specific tenant
results = audit_logger.query_logs({
    'tenant_id': 'financial-firm-123',
    'start_time': '2025-01-01T00:00:00Z',
    'end_time': '2025-01-31T23:59:59Z'
})
```

### Role-Based Access Control

**Query by role:**

```python
# Filter by user role (extend query_logs to support role filtering)
results = audit_logger.query_logs({
    'tenant_id': 'financial-firm-123',
    'user_id': 'analyst-456'
    # Add role filtering in custom implementation
})
```

### Per-Tenant Encryption

Enable encryption per tenant:

```python
# Each tenant can have their own encryption key
tenant_keys = {
    'tenant-1': 'key-for-tenant-1',
    'tenant-2': 'key-for-tenant-2'
}

audit_logger = AuditLogger(
    encrypt_db=True,
    encryption_key=tenant_keys.get(tenant_id)
)
```

### Secure Multi-Tenant Deployment

**Best Practices:**

1. **Separate databases per tenant** (for strict isolation):
   ```python
   audit_logger = AuditLogger(db_path=f'audit_logs_{tenant_id}.db')
   ```

2. **Use tenant-scoped encryption keys** (store in secure vault)

3. **Implement tenant validation** in API layer:
   ```python
   def validate_tenant_access(user_id, tenant_id):
       # Check user belongs to tenant
       return user_tenant_map[user_id] == tenant_id
   ```

4. **Audit tenant access** (log who accessed which tenant's data)

## Configuration

Environment variables:
- `ENABLE_AUDIT_LOGGING=true` - Enable/disable audit logging
- `AUDIT_DB_PATH=audit_logs.db` - Database path
- `MASK_SENSITIVE_FIELDS=true` - Enable PII masking (GDPR/CCPA)
- `ANONYMIZE_USER_IDS=false` - Hash user IDs for anonymization
- `ENCRYPT_AUDIT_DB=false` - Enable database encryption
- `ENCRYPT_AUDIT_DB_KEY=` - Encryption key (store securely)
- `COMPLIANCE_API_PORT=5000` - API port
- `COMPLIANCE_API_HOST=0.0.0.0` - API host

## Compliance Features

### Supported Standards

**SEC (Securities and Exchange Commission):**
- Complete audit trail of all transactions
- Request deduplication via input hash
- Time-range queries for reporting periods
- Export capabilities for regulatory filings

**FINRA (Financial Industry Regulatory Authority):**
- Complete request/response logging
- Error tracking and reporting
- Export capabilities for audits
- Model version tracking

**MiFID II (Markets in Financial Instruments Directive):**
- Transaction reporting
- Explainability for algorithmic decisions
- Model version and parameter tracking

**GDPR (General Data Protection Regulation):**
- Privacy-by-design (field masking)
- Right to access (query user data)
- Right to deletion (delete_user_data)
- Data portability (export user data)
- Per-tenant encryption support

**CCPA (California Consumer Privacy Act):**
- Field masking for PII
- Data deletion capabilities
- Privacy-preserving audit logs

### Prebuilt Compliance Queries

**SEC Compliance:**

```bash
curl -X POST http://localhost:5000/api/compliance/prebuilt/sec \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-01-01", "end_date": "2025-01-31", "tenant_id": "firm-123"}'
```

**FINRA Compliance:**

```bash
curl -X POST http://localhost:5000/api/compliance/prebuilt/finra \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-01-01", "end_date": "2025-01-31", "include_errors": true}'
```

**MiFID II Compliance:**

```bash
curl -X POST http://localhost:5000/api/compliance/prebuilt/mifid2 \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2025-01-01", "end_date": "2025-01-31", "require_explanations": true}'
```

**GDPR Compliance:**

```bash
# Right to access
curl -X POST http://localhost:5000/api/compliance/prebuilt/gdpr \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123", "action": "access"}'

# Right to deletion
curl -X POST http://localhost:5000/api/compliance/prebuilt/gdpr \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123", "action": "delete"}'
```

**Production Ready:**
- Error handling
- Database indexes
- Query optimization
- CSV export
- Statistics
- Privacy-by-design
- Multi-tenancy support

## Next Steps

1. Add LIME explanations (requires: `pip install lime`)
2. Deploy Compliance API to production
3. Add encryption for sensitive data
4. Set up monitoring for audit logs
5. Add drift detection integration

---

Audit trail system with explainability and compliance API implementation complete.
