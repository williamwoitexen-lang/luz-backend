# Security & Access Control Guide

**Versão**: 2.0 | **Última Atualização**: 2026-01-15 | **Status**: Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication (MSAL + Entra ID)](#authentication-msal--entra-id)
3. [Authorization (RBAC)](#authorization-rbac)
4. [Data Protection](#data-protection)
5. [API Security](#api-security)
6. [Network Security](#network-security)
7. [Secrets Management](#secrets-management)
8. [Compliance & Audit](#compliance--audit)
9. [Common Vulnerabilities](#common-vulnerabilities)
10. [Security Checklist](#security-checklist)

---

## Overview

### Security Layers

```
┌─────────────────────────────────────────────────────────┐
│ Layer 5: Data Classification                           │
│ (Public, Confidential, Sensitive PII)                  │
├─────────────────────────────────────────────────────────┤
│ Layer 4: Encryption at Rest & Transit                  │
│ (TLS 1.2+, SQL encryption, Blob encryption)            │
├─────────────────────────────────────────────────────────┤
│ Layer 3: Authorization (RBAC)                          │
│ (Role-based access, attribute filtering)               │
├─────────────────────────────────────────────────────────┤
│ Layer 2: Authentication (JWT + HTTPOnly Cookies)       │
│ (MSAL + Azure Entra ID)                                │
├─────────────────────────────────────────────────────────┤
│ Layer 1: Network Security                              │
│ (TLS, API Gateway, Firewall)                           │
└─────────────────────────────────────────────────────────┘
```

### Threat Model

| Threat | Risk | Mitigation |
|--------|------|-----------|
| Unauthorized access | HIGH | JWT + MSAL + RBAC |
| Data breach | HIGH | Encryption + access control |
| SQL injection | MEDIUM | Pydantic validation |
| XSS/CSRF | MEDIUM | HTTPOnly cookies + CORS |
| DDoS | MEDIUM | Rate limiting + Azure DDoS |
| Credential leakage | MEDIUM | KeyVault + .env.example |

---

## Authentication (MSAL + Entra ID)

### What is MSAL?

**MSAL** (Microsoft Authentication Library) = OAuth 2.0 + OpenID Connect implementation by Microsoft

Flow:
```
1. User clicks "Login"
2. Redirected to: https://login.microsoftonline.com/...
3. User authenticates in Azure AD
4. Azure redirects back with auth code
5. Backend exchanges code for JWT token
6. JWT stored in HTTPOnly cookie
7. Subsequent requests include JWT in cookie
```

### Configuration

```env
# .env
ENTRA_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
ENTRA_CLIENT_ID=yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
ENTRA_CLIENT_SECRET=your-secret-key (>=32 chars)
ENTRA_REDIRECT_URI=http://localhost:3000/auth/callback

# Production
ENTRA_REDIRECT_URI=https://yourdomain.com/auth/callback
```

### Implementation (Backend)

```python
# app/core/auth.py
from msal import ConfidentialClientApplication
from fastapi import Cookie, HTTPException
import jwt

class AuthService:
    
    def __init__(self):
        self.msal_app = ConfidentialClientApplication(
            client_id=env("ENTRA_CLIENT_ID"),
            client_credential=env("ENTRA_CLIENT_SECRET"),
            authority=f"https://login.microsoftonline.com/{env('ENTRA_TENANT_ID')}",
        )
        self.jwt_secret = env("JWT_SECRET")
        self.jwt_algorithm = "HS256"
    
    def get_auth_url(self) -> str:
        """Generate Azure AD login URL"""
        auth_url = self.msal_app.get_authorization_request_url(
            scopes=["user.read"],
            redirect_uri=env("ENTRA_REDIRECT_URI"),
        )
        return auth_url
    
    def get_token_by_auth_code(self, auth_code: str) -> str:
        """Exchange auth code for JWT (callback endpoint)"""
        
        try:
            result = self.msal_app.acquire_token_by_authorization_code(
                code=auth_code,
                scopes=["user.read"],
                redirect_uri=env("ENTRA_REDIRECT_URI"),
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Auth failed: {e}")
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error_description"])
        
        # Extract user info from token
        user_info = result.get("id_token_claims", {})
        user_email = user_info.get("email")
        
        # Create JWT token (our own, not MSAL's)
        jwt_token = jwt.encode(
            {
                "sub": user_email,
                "email": user_email,
                "name": user_info.get("name"),
                "exp": datetime.utcnow() + timedelta(hours=24),
            },
            key=self.jwt_secret,
            algorithm=self.jwt_algorithm,
        )
        
        return jwt_token
    
    def verify_jwt(self, token: str) -> dict:
        """Verify JWT token and return payload"""
        
        try:
            payload = jwt.decode(
                token,
                key=self.jwt_secret,
                algorithms=[self.jwt_algorithm],
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidSignatureError:
            raise HTTPException(status_code=401, detail="Invalid token")
```

### Implementation (Frontend)

```javascript
// frontend/src/auth.js

// Step 1: Redirect to login
function login() {
  const redirectUri = window.location.origin + "/auth/callback";
  
  const params = new URLSearchParams({
    client_id: ENTRA_CLIENT_ID,
    response_type: "code",
    scope: "user.read",
    redirect_uri: redirectUri,
    response_mode: "query",
  });
  
  window.location.href = `https://login.microsoftonline.com/${ENTRA_TENANT_ID}/oauth2/v2.0/authorize?${params}`;
}

// Step 2: Callback page extracts code and exchanges it
function handleCallback() {
  const code = new URLSearchParams(window.location.search).get("code");
  
  // Send to backend
  fetch("/api/v1/getatoken?code=" + code)
    .then(res => res.json())
    .then(data => {
      // JWT is now in cookie (HTTPOnly), no action needed
      window.location.href = "/dashboard";
    });
}

// Step 3: All subsequent requests include JWT automatically
// (Cookies are sent by browser by default)
fetch("/api/v1/documents", {
  method: "GET",
  credentials: "include",  // Important: send cookies
})
```

### JWT in HTTPOnly Cookie

**Why HTTPOnly?**
- 🔒 JavaScript can't access (prevents XSS theft)
- 🔒 Automatically sent in requests (no manual header needed)
- 🔒 HTTPS-only in production (prevents man-in-the-middle)

```python
# app/routers/auth.py
from fastapi.responses import JSONResponse

@router.get("/getatoken")
async def get_token(code: str):
    """Exchange auth code for JWT in HTTPOnly cookie"""
    
    jwt_token = auth_service.get_token_by_auth_code(code)
    
    response = JSONResponse({"message": "Authenticated"})
    response.set_cookie(
        key="jwt",
        value=jwt_token,
        httponly=True,  # ← Prevents JavaScript access
        secure=True,    # ← HTTPS-only in production
        samesite="Lax", # ← CSRF protection
        max_age=86400,  # ← 24 hours
    )
    
    return response

@router.get("/logout")
async def logout():
    """Clear JWT cookie"""
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie(
        key="jwt",
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    return response
```

---

## Authorization (RBAC)

### Role Hierarchy

```
ADMIN
├── Can manage admins, view all documents
└── Can view all conversations

MANAGER
├── Can manage team members
├── Can access team documents + personal
└── Can access team conversations + personal

EMPLOYEE
└── Can access own documents + shared
└── Can access own conversations

VIEWER
└── Read-only access to documents
└── Can ask questions
```

### Attribute-Based Access Control (ABAC)

Beyond roles, we filter by attributes:

```python
# app/core/rbac.py

class UserContext:
    """User authentication + authorization context"""
    
    def __init__(self, email: str, name: str, roles: List[str], 
                 country: str, city: str, department: str):
        self.email = email
        self.name = name
        self.roles = roles  # e.g., ["Employee", "Manager"]
        self.country = country  # e.g., "Brazil"
        self.city = city  # e.g., "São Paulo"
        self.department = department  # e.g., "HR"

class DocumentAccessControl:
    """Check if user can access document"""
    
    def can_access_document(self, user: UserContext, document: Document) -> bool:
        """
        Return True if user can read this document
        
        Access granted if:
        1. User is ADMIN
        2. User's country is in document.allowed_countries
        3. AND User's city is in document.allowed_cities (if restricted)
        """
        
        # ADMIN bypass
        if "ADMIN" in user.roles:
            return True
        
        # Check country (required)
        if document.allowed_countries and user.country not in document.allowed_countries:
            return False
        
        # Check city (if specified in document)
        if document.allowed_cities and user.city not in document.allowed_cities:
            return False
        
        # Check role-based access
        if document.required_roles and not any(role in document.required_roles for role in user.roles):
            return False
        
        return True

    def filter_documents(self, user: UserContext, documents: List[Document]) -> List[Document]:
        """Return only documents user can access"""
        return [doc for doc in documents if self.can_access_document(user, doc)]
```

### Using in Routers

```python
# app/routers/documents.py
from fastapi import Depends

async def get_current_user(request: Request) -> UserContext:
    """Dependency: Extract user from JWT cookie"""
    
    token = request.cookies.get("jwt")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    payload = auth_service.verify_jwt(token)
    
    # Get user details from database/AD
    user = await user_repository.get_by_email(payload["email"])
    
    return UserContext(
        email=user.email,
        name=user.name,
        roles=user.roles,
        country=user.country,
        city=user.city,
        department=user.department,
    )

@router.get("/documents")
async def list_documents(user: UserContext = Depends(get_current_user)):
    """List documents user can access"""
    
    all_docs = await document_repository.get_all()
    
    # Filter by user's access rights
    accessible_docs = access_control.filter_documents(user, all_docs)
    
    return accessible_docs
```

### Role Permissions Matrix

```python
# app/core/permissions.py

PERMISSIONS = {
    "admin": {
        "documents:create": True,
        "documents:read": True,
        "documents:update": True,
        "documents:delete": True,
        "admin:manage_users": True,
        "admin:view_audit_logs": True,
    },
    "manager": {
        "documents:create": True,
        "documents:read": True,
        "documents:update": True,  # Own + team
        "documents:delete": False,
        "admin:manage_users": False,
        "admin:view_audit_logs": False,
    },
    "employee": {
        "documents:create": False,
        "documents:read": True,    # Accessible docs
        "documents:update": False,
        "documents:delete": False,
        "admin:manage_users": False,
        "admin:view_audit_logs": False,
    },
}

def has_permission(user: UserContext, permission: str) -> bool:
    """Check if user has permission"""
    
    for role in user.roles:
        if PERMISSIONS.get(role, {}).get(permission, False):
            return True
    
    return False

# Usage in route
@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, user: UserContext = Depends(get_current_user)):
    """Delete document (admin only)"""
    
    if not has_permission(user, "documents:delete"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    await document_repository.delete(doc_id)
```

---

## Data Protection

### Encryption at Rest

**Where**:
- SQL Server: Transparent Data Encryption (TDE)
- Azure Blob Storage: Service-Side Encryption
- Redis: Encrypted at rest option

**Configuration** (SQL Server):

```sql
-- Enable TDE
ALTER DATABASE [luz_db] SET ENCRYPTION ON;

-- Verify
SELECT name, is_encrypted FROM sys.databases WHERE name = 'luz_db';
-- Output: luz_db, 1 (encrypted)
```

**Configuration** (Blob Storage):

```python
# Storage account automatically encrypts with Microsoft-managed keys
# To use customer-managed keys:
connection_string = env("AZURE_STORAGE_CONNECTION_STRING")
client = BlobServiceClient.from_connection_string(connection_string)

# Check encryption status
properties = client.get_account_properties()
print(properties.encryption)  # Shows encryption key provider
```

### Encryption in Transit

**All communications must use TLS 1.2+**

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS: only allow trusted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",  # ← HTTPS only!
        "https://app.yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Force HTTPS redirect (in production)
@app.middleware("http")
async def force_https(request: Request, call_next):
    if request.url.scheme == "http":
        url = request.url.replace(scheme="https")
        return RedirectResponse(url=url)
    return await call_next(request)
```

**Verify TLS**:
```bash
# Check certificate
openssl s_client -connect yourdomain.com:443 -tls1_2

# Recommended: TLS 1.2 or 1.3 only
```

### Field-Level Encryption (Sensitive Data)

```python
# app/models/document.py
from cryptography.fernet import Fernet

class Document(Base):
    __tablename__ = "documents"
    
    id: str = Column(String, primary_key=True)
    title: str = Column(String)  # Plain text (searchable)
    content: str = Column(LargeBinary)  # ENCRYPTED
    
    @property
    def decrypted_content(self) -> str:
        """Decrypt content (only when needed)"""
        cipher = Fernet(env("ENCRYPTION_KEY"))
        return cipher.decrypt(self.content).decode()

# On save (encrypt)
doc = Document(
    id="123",
    title="Benefits Guide",
    content=Fernet(env("ENCRYPTION_KEY")).encrypt(full_text.encode()),
)
db.add(doc)
db.commit()

# On read (decrypt when needed)
doc = db.query(Document).filter(Document.id == "123").first()
if can_access(user, doc):
    print(doc.decrypted_content)  # Only decrypt if authorized
```

---

## API Security

### Rate Limiting

Prevent brute force / DoS:

```python
# app/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# In app/main.py
app.state.limiter = limiter

# Apply to routes
@router.get("/documents")
@limiter.limit("100/minute")
async def list_documents(request: Request):
    return []

@router.post("/login")
@limiter.limit("5/minute")  # Stricter for auth
async def login(request: Request):
    return {}
```

### Input Validation

Prevent injection attacks:

```python
# app/models/chat.py
from pydantic import BaseModel, Field, validator

class ChatRequest(BaseModel):
    """Validated input model"""
    
    question: str = Field(
        ..., 
        min_length=1,
        max_length=5000,
        description="User's question"
    )
    
    user_id: EmailStr  # Auto-validates email format
    
    @validator("question")
    def question_no_sql_injection(cls, v):
        """Prevent SQL injection in question"""
        # Even though we use parameterized queries,
        # this adds defense-in-depth
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "--", "/*"]
        for keyword in dangerous_keywords:
            if keyword in v.upper():
                raise ValueError(f"Invalid query: contains '{keyword}'")
        return v

# ✅ Safe: Pydantic validates before reaching database
request = ChatRequest(
    question="Quais benefícios?",
    user_id="alice@company.com"
)

# ❌ Blocked: Pydantic rejects
request = ChatRequest(
    question="'; DROP TABLE documents; --",  # SQL injection attempt
    user_id="alice@company.com"
)
# → ValidationError: Invalid query: contains 'DROP'
```

### SQL Parameterization

Already done with SQLAlchemy ORM:

```python
# ✅ SAFE: Using ORM (parameterized)
documents = db.query(Document).filter(
    Document.title.ilike(f"%{user_input}%")
).all()

# ✅ SAFE: Using raw SQL with parameters
result = db.execute(
    "SELECT * FROM documents WHERE title LIKE ?",
    (f"%{user_input}%",)  # Parameters separate from query
)

# ❌ UNSAFE: String interpolation
result = db.execute(
    f"SELECT * FROM documents WHERE title LIKE '%{user_input}%'"
)
# If user_input = "'; DROP TABLE documents; --"
# → Query becomes: SELECT * FROM documents WHERE title LIKE ''; DROP TABLE documents; --'%
```

### CORS Security

```python
# ✅ Restrictive CORS (recommended)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.yourdomain.com",
        "https://admin.yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
    expose_headers=["X-Total-Count"],
    max_age=600,  # Preflight cache
)

# ❌ DANGEROUS: Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Opens to CSRF attacks
    allow_credentials=True,  # Even worse with credentials
)
```

---

## Network Security

### Azure Network Security

```
┌─────────────────────────────────────┐
│ Internet                            │
└──────────────┬──────────────────────┘
               │
       ┌───────▼────────┐
       │ Azure Firewall │
       │ (DDoS, WAF)    │
       └───────┬────────┘
               │
    ┌──────────▼──────────┐
    │ App Gateway / Load  │
    │ Balancer (TLS term) │
    └──────────┬──────────┘
               │
       ┌───────▼────────┐
       │ Web App / VM   │
       │ (FastAPI app)  │
       └───────┬────────┘
               │
    ┌──────────▼──────────┐
    │ Azure Private Link  │
    │ (Database, Storage) │
    └─────────────────────┘
```

### NSG (Network Security Group) Rules

```python
# Restrict inbound traffic
allowed_ips = [
    "203.0.113.0/24",  # Office network
    "198.51.100.0/24", # Backup office
]

# Only allow these IPs + Azure services
inbound_rules = [
    {
        "name": "Allow-Office",
        "protocol": "Tcp",
        "sourcePortRange": "*",
        "destinationPortRange": "443",
        "sourceAddressPrefix": allowed_ips,
        "destinationAddressPrefix": "*",
        "access": "Allow",
        "priority": 100,
    },
    {
        "name": "Deny-All",  # Default deny
        "protocol": "*",
        "sourcePortRange": "*",
        "destinationPortRange": "*",
        "sourceAddressPrefix": "*",
        "destinationAddressPrefix": "*",
        "access": "Deny",
        "priority": 4096,
    },
]
```

---

## Secrets Management

### Azure KeyVault

Store all secrets in KeyVault, NOT in `.env`:

```python
# app/core/keyvault.py
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class KeyVaultConfig:
    """Load secrets from Azure KeyVault"""
    
    def __init__(self):
        credential = DefaultAzureCredential()
        kv_url = env("KEYVAULT_URL")  # e.g., https://my-vault.vault.azure.net/
        self.client = SecretClient(vault_url=kv_url, credential=credential)
    
    def get_secret(self, name: str) -> str:
        """Retrieve secret from KeyVault"""
        secret = self.client.get_secret(name)
        return secret.value

kv = KeyVaultConfig()

# Usage
db_password = kv.get_secret("db-password")
api_key = kv.get_secret("api-key")
```

### Local Development (`.env.example` only)

```bash
# ✅ SAFE: Example file with dummy values
# .env.example
ENTRA_CLIENT_ID=dummy-client-id-change-this
ENTRA_CLIENT_SECRET=dummy-secret-change-this
LLM_API_KEY=dummy-key-change-this

# ✅ SAFE: Real .env in .gitignore (never committed)
# .env
ENTRA_CLIENT_ID=12345678-abcd-efgh-ijkl-mnopqrstuvwx
ENTRA_CLIENT_SECRET=abc123xyz...
LLM_API_KEY=sk-proj-...

# ✅ SAFE: .gitignore prevents accident
# .gitignore
.env
.env.*.local
secrets/
*.pem
```

### Secret Rotation

```python
# app/core/secret_rotation.py
from datetime import datetime, timedelta
import asyncio

class SecretRotation:
    """Monitor and rotate secrets"""
    
    def __init__(self, keyvault_client):
        self.kv = keyvault_client
        self.check_interval_hours = 24
    
    async def start_monitoring(self):
        """Periodically check for expiring secrets"""
        
        while True:
            await asyncio.sleep(self.check_interval_hours * 3600)
            await self.check_secret_expiration()
    
    async def check_secret_expiration(self):
        """Alert if secrets will expire soon"""
        
        secrets_to_check = [
            "db-connection-string",
            "api-key",
            "jwt-secret",
        ]
        
        for secret_name in secrets_to_check:
            secret = self.kv.get_secret(secret_name)
            
            if secret.properties.expires_on:
                days_until_expiry = (
                    secret.properties.expires_on - datetime.utcnow()
                ).days
                
                if days_until_expiry < 30:
                    alert(f"⚠️  Secret '{secret_name}' expires in {days_until_expiry} days")
```

---

## Compliance & Audit

### Audit Logging

Log all sensitive operations:

```python
# app/models/audit.py
from sqlalchemy import Column, String, DateTime, JSON
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: str = Column(String, primary_key=True)
    timestamp: datetime = Column(DateTime, default=datetime.utcnow)
    user_email: str = Column(String)
    action: str = Column(String)  # e.g., "document_deleted", "user_created"
    resource_type: str = Column(String)  # e.g., "document", "user"
    resource_id: str = Column(String)
    details: dict = Column(JSON)
    ip_address: str = Column(String)
    status: str = Column(String)  # "success" or "failed"

# Usage in routes
@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    user: UserContext = Depends(get_current_user),
    request: Request
):
    """Delete document with audit logging"""
    
    try:
        document = await document_repository.get(doc_id)
        
        # Check authorization
        if not access_control.can_access_document(user, document):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Perform action
        await document_repository.delete(doc_id)
        
        # Audit log success
        await audit_service.log(
            user_email=user.email,
            action="document_deleted",
            resource_type="document",
            resource_id=doc_id,
            details={"title": document.title},
            ip_address=request.client.host,
            status="success",
        )
        
    except Exception as e:
        # Audit log failure
        await audit_service.log(
            user_email=user.email,
            action="document_delete_failed",
            resource_type="document",
            resource_id=doc_id,
            details={"error": str(e)},
            ip_address=request.client.host,
            status="failed",
        )
        raise
```

### Compliance Standards

| Standard | Requirement | Implementation |
|----------|-------------|-----------------|
| GDPR | Data minimization | Collect only necessary data |
| | Right to deletion | Delete endpoint + cascade |
| | Encryption | TLS + at-rest encryption |
| LGPD | Data processing agreements | DPA signed with providers |
| | Security measures | 2FA, encryption, audits |
| SOC 2 | Access controls | RBAC + least privilege |
| | Change management | Version control + approvals |
| | Monitoring | Audit logs + alerts |

---

## Common Vulnerabilities

### 1. Insecure Direct Object Reference (IDOR)

**Vulnerable**:
```python
# ❌ User can access ANY document by changing ID
@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    return doc  # No authorization check!
```

**Secure**:
```python
# ✅ User can only access documents they have access to
@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: str,
    user: UserContext = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    
    if not access_control.can_access_document(user, doc):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return doc
```

### 2. Broken Authentication

**Vulnerable**:
```python
# ❌ Store password as plain text
user.password = request.password
db.add(user)
db.commit()
```

**Secure**:
```python
# ✅ Hash password with bcrypt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

user.password_hash = pwd_context.hash(request.password)  # Hash
db.add(user)
db.commit()

# On login, verify
if not pwd_context.verify(request.password, user.password_hash):
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

### 3. Sensitive Data Exposure

**Vulnerable**:
```python
# ❌ Return user's password/API keys in response
return {
    "email": user.email,
    "password": user.password,  # DON'T EXPOSE
    "api_key": user.api_key,    # DON'T EXPOSE
}
```

**Secure**:
```python
# ✅ Return only safe fields
from pydantic import BaseModel

class UserResponse(BaseModel):
    email: str
    name: str
    roles: List[str]
    # password and api_key NOT included

return UserResponse(**user.dict())
```

### 4. XML External Entity (XXE) Attacks

**Vulnerable**:
```python
# ❌ Parse XML without disabling external entities
import xml.etree.ElementTree as ET

tree = ET.parse(user_uploaded_file)  # Can read system files!
```

**Secure**:
```python
# ✅ Disable external entities
from defusedxml import ElementTree

tree = ElementTree.parse(user_uploaded_file)  # Safe!
```

---

## Security Checklist

### Pre-Production

- [ ] All secrets moved to KeyVault (no `.env` in Git)
- [ ] HTTPS/TLS enabled on all endpoints
- [ ] Authentication (MSAL) configured with production tenant
- [ ] RBAC policies defined and tested
- [ ] Database encryption enabled (TDE)
- [ ] Backup encryption configured
- [ ] Audit logging enabled and monitored
- [ ] Rate limiting configured
- [ ] CORS restricted to known origins
- [ ] Security headers added (CSP, HSTS, etc.)
- [ ] Input validation on all endpoints
- [ ] Secrets rotation scheduled
- [ ] Security team review completed
- [ ] Penetration testing completed

### Post-Production

- [ ] Monitor audit logs weekly
- [ ] Review authentication failures daily
- [ ] Update dependencies monthly
- [ ] Rotate secrets every 90 days
- [ ] Backup tested monthly
- [ ] Disaster recovery plan updated
- [ ] Security training for team members
- [ ] Incident response plan in place

---

## Security Headers

```python
# app/main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*.yourdomain.com"])

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response
```

---

## Related Documentation

- [CONFIG_KEYS.md](CONFIG_KEYS.md) - Security-related configuration
- [RUN_LOCAL_COMPLETE_GUIDE.md](RUN_LOCAL_COMPLETE_GUIDE.md) - Development setup
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - General troubleshooting
- [LLM_TROUBLESHOOTING.md](LLM_TROUBLESHOOTING.md) - Data sensitivity in logs

---

**Questions?**

- Authentication: #backend-auth-support
- Security: #backend-security-support
- Compliance: compliance@company.com
