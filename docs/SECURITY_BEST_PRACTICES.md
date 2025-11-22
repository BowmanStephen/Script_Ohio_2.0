# Security Best Practices Guide

**Last Updated**: November 2025  
**Status**: Active security guidelines

## Overview

This document outlines security best practices for Script Ohio 2.0, covering secrets management, input validation, dependency security, data encryption, and more.

## Secrets Management

### API Keys and Credentials

**NEVER**:
- ❌ Hardcode API keys or credentials in source code
- ❌ Commit secrets to version control
- ❌ Share API keys in chat, email, or documentation
- ❌ Store secrets in plain text files
- ❌ Log secrets in application logs

**ALWAYS**:
- ✅ Use environment variables for all secrets
- ✅ Validate `.gitignore` excludes `.env` files
- ✅ Use `python-dotenv` for local development
- ✅ Rotate API keys regularly (quarterly minimum)
- ✅ Log API key usage (without exposing keys)
- ✅ Use different keys for dev/staging/prod

### Implementation Pattern

```python
import os
from dotenv import load_dotenv

# Load environment variables (local development only)
load_dotenv()

# Access API keys via environment variables
api_key = os.environ.get("CFBD_API_KEY")
if not api_key:
    raise ValueError("CFBD_API_KEY environment variable not set")
```

### API Key Rotation

**Process**:
1. Generate new API key
2. Update environment variable in all environments
3. Verify application works with new key
4. Revoke old key after verification period
5. Document rotation in change log

**Monitoring**:
- Log authentication failures
- Alert on repeated failures
- Track API key usage patterns
- Monitor for unexpected access patterns

### Audit Logging

**What to Log**:
- API key usage (timestamp, action, success/failure)
- Authentication events (without exposing credentials)
- Security-related configuration changes
- Access to sensitive data

**What NOT to Log**:
- API key values
- Passwords or tokens
- Full request/response bodies with secrets
- Sensitive user data

**Implementation**:
```python
import logging
from datetime import datetime

logger = logging.getLogger("security")

def log_api_usage(action: str, success: bool, user_id: str = None):
    logger.info(
        "api_usage",
        extra={
            "action": action,
            "success": success,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

## Input Validation

### General Principles

**Always Validate**:
- ✅ All external inputs (user data, API responses, file contents)
- ✅ Type and format of input data
- ✅ Range and length constraints
- ✅ Required vs optional fields
- ✅ Encoding and character sets

### Validation Patterns

**Type Hints for Validation**:
```python
from typing import Optional
from pydantic import BaseModel, validator

class GameRequest(BaseModel):
    season: int
    week: int
    team: Optional[str] = None
    
    @validator('season')
    def validate_season(cls, v):
        if not 1869 <= v <= 2100:
            raise ValueError('Season must be between 1869 and 2100')
        return v
    
    @validator('week')
    def validate_week(cls, v):
        if not 1 <= v <= 25:
            raise ValueError('Week must be between 1 and 25')
        return v
```

**Manual Validation**:
```python
def validate_team_name(team: str) -> str:
    if not team:
        raise ValueError("Team name is required")
    if len(team) > 100:
        raise ValueError("Team name too long")
    if not team.replace(' ', '').isalnum():
        raise ValueError("Team name contains invalid characters")
    return team.strip()
```

### Sanitization

**For User-Provided Data**:
- Remove or escape special characters
- Normalize whitespace
- Limit string length
- Validate encoding

**Example**:
```python
import re

def sanitize_input(text: str, max_length: int = 1000) -> str:
    if not text:
        return ""
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    # Normalize whitespace
    text = ' '.join(text.split())
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    return text.strip()
```

### SQL Injection Prevention

**If Using Raw SQL** (avoid when possible):
- Use parameterized queries
- Never concatenate user input into SQL
- Validate input types before queries

**Preferred**: Use ORM or query builder with parameter binding

## Dependency Security

### Vulnerability Scanning

**Tools**:
- `pip-audit`: Official Python vulnerability scanner
- `safety`: Python dependency checker
- `dependabot`: Automated dependency updates (GitHub)

**Regular Scanning**:
```bash
# Install pip-audit
pip install pip-audit

# Scan dependencies
pip-audit

# Or use safety
pip install safety
safety check
```

**CI/CD Integration**:
```yaml
# .github/workflows/security.yml
- name: Scan dependencies
  run: |
    pip install pip-audit
    pip-audit --format json --output audit.json
```

### Dependency Updates

**Process**:
1. Review security advisories monthly
2. Test updates in development environment
3. Update patch versions immediately (security fixes)
4. Review minor versions quarterly
5. Review major versions annually

**Update Strategy**:
- **Patch versions**: Update immediately for security fixes
- **Minor versions**: Review quarterly, test thoroughly
- **Major versions**: Review annually, plan migration

### Minimizing Attack Surface

**Principles**:
- Only install required dependencies
- Avoid transitive dependencies when possible
- Review dependency tree regularly
- Remove unused dependencies

**Audit Dependencies**:
```bash
pip list --format=freeze > current_dependencies.txt
# Review and remove unused packages
```

## Data Encryption

### Encryption at Rest

**Sensitive Data**:
- Cache files with API responses
- Model pickle files
- Database files
- Configuration files with secrets

**Implementation**:
```python
from cryptography.fernet import Fernet
import os

def get_encryption_key() -> bytes:
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY not set")
    return key.encode()

def encrypt_data(data: bytes) -> bytes:
    key = get_encryption_key()
    fernet = Fernet(key)
    return fernet.encrypt(data)

def decrypt_data(encrypted_data: bytes) -> bytes:
    key = get_encryption_key()
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_data)
```

### SQLite Cache Encryption

**For Production**:
- Enable encryption for SQLite databases
- Use SQLCipher for encrypted SQLite
- Store encryption keys securely

**Local Development**:
- Encryption optional but recommended
- Use separate keys for dev/prod

### Pickle File Security

**Risks**:
- Pickle files can execute arbitrary code
- Deserialization vulnerabilities
- Unauthorized code execution

**Mitigations**:
- Only load pickle files from trusted sources
- Validate pickle file signatures
- Use `pickle.loads()` with caution
- Consider alternatives (joblib, JSON, HDF5)

**Safer Alternative**:
```python
import joblib
import hashlib

def verify_pickle_file(filepath: str, expected_hash: str) -> bool:
    with open(filepath, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    return file_hash == expected_hash

# Load verified model
if verify_pickle_file("model.pkl", expected_hash):
    model = joblib.load("model.pkl")
else:
    raise SecurityError("Model file verification failed")
```

## Authentication & Authorization

### API Key Management

**Storage**:
- Environment variables (recommended)
- Secret management services (AWS Secrets Manager, HashiCorp Vault)
- Configuration files (excluded from version control)

**Validation**:
- Verify API key format before use
- Check key expiration (if supported)
- Validate permissions for requested action

**Rate Limiting**:
- Implement per-key rate limiting
- Track usage per API key
- Alert on unusual patterns

### Permission Levels

**Agent Permission Model**:
- READ_ONLY: Read-only access
- READ_EXECUTE: Read and execute actions
- READ_EXECUTE_WRITE: Full access except system changes
- ADMIN: Full system access

**Implementation**:
```python
from agents.core.agent_framework import PermissionLevel

def check_permission(
    agent_permission: PermissionLevel,
    required_permission: PermissionLevel
) -> bool:
    permission_hierarchy = {
        PermissionLevel.READ_ONLY: 1,
        PermissionLevel.READ_EXECUTE: 2,
        PermissionLevel.READ_EXECUTE_WRITE: 3,
        PermissionLevel.ADMIN: 4
    }
    return (permission_hierarchy[agent_permission] >= 
            permission_hierarchy[required_permission])
```

## Network Security

### HTTPS Requirements

**Production**:
- ✅ Always use HTTPS
- ✅ Validate SSL certificates
- ✅ Use strong cipher suites
- ✅ Implement certificate pinning for critical APIs

**Development**:
- Use HTTPS even in local development when possible
- Disable SSL verification only for local testing
- Never disable SSL verification in production code

**Implementation**:
```python
import requests
import ssl

# Production: Strict SSL verification
session = requests.Session()
session.verify = True  # Default, validates certificates

# Development: Only if necessary
if os.environ.get("ENVIRONMENT") == "development":
    # Still preferred to use valid certificates
    pass
```

### Certificate Validation

**Best Practices**:
- Verify SSL certificates for all HTTPS requests
- Use system certificate store
- Implement certificate pinning for critical APIs
- Alert on certificate errors

**Certificate Pinning**:
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

class PinnedHTTPAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.load_verify_locations(cafile='path/to/cert.pem')
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

session = requests.Session()
session.mount('https://api.example.com', PinnedHTTPAdapter())
```

### Rate Limiting

**External API Rate Limits**:
- Respect CFBD API rate limits (6 req/sec)
- Implement exponential backoff for retries
- Queue requests to avoid rate limit violations

**Internal Rate Limiting**:
- Implement rate limiting on internal endpoints
- Protect against abuse
- Track and log rate limit violations

## Error Handling Security

### Error Message Guidelines

**DO**:
- ✅ Provide user-friendly error messages
- ✅ Log detailed errors server-side only
- ✅ Use error codes for client communication
- ✅ Implement error categorization

**DON'T**:
- ❌ Expose system internals in error messages
- ❌ Reveal file paths or system details
- ❌ Include stack traces in user-facing errors
- ❌ Leak information about authentication status

**Implementation**:
```python
class SecurityError(Exception):
    """Base class for security-related errors"""
    pass

class AuthenticationError(SecurityError):
    """Authentication failed"""
    user_message = "Authentication failed. Please check your credentials."
    
class AuthorizationError(SecurityError):
    """Authorization failed"""
    user_message = "You do not have permission to perform this action."

def handle_error(error: Exception) -> dict:
    if isinstance(error, SecurityError):
        # User-friendly message
        return {"error": error.user_message, "code": error.__class__.__name__}
    else:
        # Generic message for unexpected errors
        logger.exception("Unexpected error occurred")
        return {"error": "An error occurred. Please try again later.", "code": "INTERNAL_ERROR"}
```

### Error Categorization

**Error Types**:
- **Input Validation Errors**: User-provided data issues
- **Authentication Errors**: Authentication failures
- **Authorization Errors**: Permission issues
- **System Errors**: Internal system failures
- **External Service Errors**: Third-party service issues

**Response Strategy**:
- Input Validation: Return detailed feedback to user
- Authentication: Log failure, generic message to user
- Authorization: Log attempt, generic message to user
- System Errors: Log details, generic message to user
- External Service: Log details, retry if appropriate

## Security Checklist

### Before Deploying

- [ ] All secrets use environment variables
- [ ] No hardcoded credentials in code
- [ ] `.gitignore` excludes `.env` files
- [ ] Dependencies scanned for vulnerabilities
- [ ] Input validation implemented
- [ ] Error messages don't expose system internals
- [ ] HTTPS enabled in production
- [ ] SSL certificate validation enabled
- [ ] Rate limiting implemented
- [ ] Audit logging configured
- [ ] Sensitive data encrypted at rest
- [ ] API key rotation scheduled

### Regular Maintenance

- [ ] Monthly dependency vulnerability scan
- [ ] Quarterly API key rotation
- [ ] Quarterly security review
- [ ] Annual security audit
- [ ] Regular log review for security events
- [ ] Update security documentation

## Incident Response

### If a Security Issue is Detected

1. **Immediate Actions**:
   - Revoke compromised API keys
   - Isolate affected systems
   - Preserve logs for investigation

2. **Investigation**:
   - Review audit logs
   - Identify attack vector
   - Assess impact

3. **Remediation**:
   - Patch vulnerabilities
   - Update security measures
   - Rotate all affected credentials

4. **Documentation**:
   - Document incident
   - Update security procedures
   - Share lessons learned

## References

- **Main Documentation**: `AGENTS.md`
- **Architecture Guide**: `docs/ARCHITECTURE_IMPROVEMENTS.md`
- **Code Quality Guide**: `docs/CODE_QUALITY_GUIDELINES.md`
- **CFBD Integration**: `agents/cfbd_integration_agent.py`

