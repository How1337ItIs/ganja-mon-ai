# IoT Security Best Practices for Grok & Mon

Comprehensive security patterns for IoT cannabis cultivation systems, covering authentication, network security, and data protection.

## Overview

Grok & Mon is an IoT system controlling physical hardware (lights, fans, pumps, sensors) and processing sensitive cultivation data. Security is critical to prevent unauthorized access, data breaches, and physical damage to equipment.

---

## Security Layers

1. **Network Security** - Isolation, segmentation, VPN
2. **Authentication & Authorization** - API keys, JWT, MQTT auth
3. **Data Protection** - Encryption, secure storage
4. **Input Validation** - Sensor data, API requests
5. **Audit Logging** - Track all actions
6. **Rate Limiting** - Prevent abuse
7. **Secrets Management** - Secure credential storage

---

## 1. Network Security

### Network Segmentation

**Isolate IoT Devices:**
```
Internet
  │
  ├─ Main Network (Trusted)
  │   └─ Web Server, Database
  │
  └─ IoT Network (Isolated)
      ├─ Raspberry Pi (Control Server)
      ├─ Sensors (DHT22, SCD30, etc.)
      └─ Actuators (Lights, Fans, Pumps)
```

**Implementation:**
- Use separate VLAN for IoT devices
- Firewall rules: IoT network can only communicate with control server
- No direct internet access for sensors/actuators
- Control server acts as gateway

**Docker Network Isolation:**
```yaml
# docker-compose.yml
services:
  control-server:
    networks:
      - iot-network
      - api-network
  
  sensors:
    networks:
      - iot-network  # Only internal IoT network
  
  api:
    networks:
      - api-network  # Only API network
```

### VPN Access

**For Remote Monitoring:**
- Use WireGuard or OpenVPN
- Require VPN connection to access control interface
- MFA for VPN authentication
- Log all VPN connections

**WireGuard Setup:**
```bash
# Install WireGuard
sudo apt install wireguard

# Generate keys
wg genkey | tee privatekey | wg pubkey > publickey

# Server config (/etc/wireguard/wg0.conf)
[Interface]
PrivateKey = <server-private-key>
Address = 10.0.0.1/24
ListenPort = 51820

[Peer]
PublicKey = <client-public-key>
AllowedIPs = 10.0.0.2/32
```

---

## 2. Authentication & Authorization

### API Authentication

**Option 1: API Keys (Simple)**
```python
from fastapi import FastAPI, Security, HTTPException
from fastapi.security import APIKeyHeader
import secrets

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Store keys securely (use environment variables or secrets manager)
VALID_API_KEYS = {
    os.environ.get("API_KEY_1"),
    os.environ.get("API_KEY_2")
}

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.get("/api/sensors")
async def get_sensors(api_key: str = Security(verify_api_key)):
    return {"sensors": get_sensor_data()}
```

**Option 2: JWT Tokens (Recommended)**
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

@app.post("/api/login")
async def login(username: str, password: str):
    # Verify credentials
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/sensors")
async def get_sensors(token: str = Security(verify_token)):
    return {"sensors": get_sensor_data()}
```

### MQTT Authentication

**Mosquitto Setup with Username/Password:**
```bash
# Create password file
mosquitto_passwd -c /etc/mosquitto/passwd grokmon

# mosquitto.conf
allow_anonymous false
password_file /etc/mosquitto/passwd

# ACL (Access Control List)
acl_file /etc/mosquitto/acl

# acl file
user grokmon
topic readwrite sensors/#
topic readwrite actuators/#
topic readwrite control/#
```

**Python MQTT Client with Auth:**
```python
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.username_pw_set(
    username=os.environ.get("MQTT_USERNAME"),
    password=os.environ.get("MQTT_PASSWORD")
)
client.tls_set()  # Enable TLS
client.connect("mqtt.example.com", 8883, 60)
```

**MQTT Certificate-Based Auth (More Secure):**
```bash
# Generate CA certificate
openssl req -new -x509 -days 365 -extensions v3_ca \
    -keyout ca.key -out ca.crt

# Generate server certificate
openssl genrsa -out server.key 2048
openssl req -new -out server.csr -key server.key
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out server.crt -days 365

# mosquitto.conf
listener 8883
cafile /etc/mosquitto/ca.crt
certfile /etc/mosquitto/server.crt
keyfile /etc/mosquitto/server.key
require_certificate true
```

---

## 3. Data Protection

### Encryption at Rest

**Database Encryption:**
```python
# SQLite with encryption (using sqlcipher)
from pysqlcipher3 import dbapi2 as sqlite

conn = sqlite.connect('grokmon.db')
conn.execute("PRAGMA key='your-encryption-key'")
```

**Sensitive File Encryption:**
```python
from cryptography.fernet import Fernet

# Generate key (store securely)
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt sensitive data
encrypted = cipher.encrypt(b"sensitive data")

# Decrypt
decrypted = cipher.decrypt(encrypted)
```

### Encryption in Transit

**HTTPS/TLS:**
```python
# FastAPI with HTTPS
from fastapi import FastAPI
import uvicorn

app = FastAPI()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=443,
        ssl_keyfile="/path/to/key.pem",
        ssl_certfile="/path/to/cert.pem"
    )
```

**MQTT over TLS:**
```python
client = mqtt.Client()
client.tls_set(
    ca_certs="/path/to/ca.crt",
    certfile="/path/to/client.crt",
    keyfile="/path/to/client.key"
)
```

---

## 4. Input Validation

### Sensor Data Validation

```python
from pydantic import BaseModel, validator, Field
from typing import Optional

class SensorReading(BaseModel):
    temperature_f: float = Field(..., ge=55, le=95)  # 55-95°F range
    humidity_percent: float = Field(..., ge=20, le=90)  # 20-90% range
    vpd_kpa: float = Field(..., ge=0.0, le=3.0)
    co2_ppm: Optional[int] = Field(None, ge=300, le=2000)
    soil_moisture_percent: float = Field(..., ge=0, le=100)
    timestamp: datetime
    
    @validator('temperature_f')
    def validate_temp(cls, v):
        if v < 55 or v > 95:
            raise ValueError('Temperature outside safe range')
        return v
    
    @validator('humidity_percent')
    def validate_humidity(cls, v):
        if v < 20 or v > 90:
            raise ValueError('Humidity outside safe range')
        return v

@app.post("/api/sensors/reading")
async def submit_reading(reading: SensorReading):
    # Pydantic automatically validates
    store_reading(reading)
    return {"status": "accepted"}
```

### API Request Validation

```python
from fastapi import HTTPException

def validate_actuator_command(command: dict):
    """Validate actuator commands before execution."""
    
    allowed_actions = {
        "set_light_intensity": {"intensity_percent": (0, 100)},
        "trigger_irrigation": {"amount_ml": (0, 1000)},
        "set_fan_speed": {"speed_percent": (0, 100)},
    }
    
    action = command.get("action")
    if action not in allowed_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")
    
    params = command.get("parameters", {})
    validations = allowed_actions[action]
    
    for param, (min_val, max_val) in validations.items():
        value = params.get(param)
        if value is None:
            raise HTTPException(status_code=400, detail=f"Missing parameter: {param}")
        if not (min_val <= value <= max_val):
            raise HTTPException(
                status_code=400,
                detail=f"Parameter {param} out of range: {min_val}-{max_val}"
            )
    
    return True
```

---

## 5. Rate Limiting

### FastAPI Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/sensors")
@limiter.limit("10/minute")  # 10 requests per minute
async def get_sensors(request: Request):
    return {"sensors": get_sensor_data()}

@app.post("/api/control")
@limiter.limit("5/minute")  # Stricter limit for control endpoints
async def control_actuator(request: Request, command: dict):
    return execute_command(command)
```

### MQTT Rate Limiting

```python
from collections import defaultdict
from datetime import datetime, timedelta

class MQTTRateLimiter:
    def __init__(self, max_messages: int = 100, window_seconds: int = 60):
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self.message_counts = defaultdict(list)
    
    def check_rate_limit(self, client_id: str) -> bool:
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Remove old messages
        self.message_counts[client_id] = [
            ts for ts in self.message_counts[client_id]
            if ts > cutoff
        ]
        
        # Check limit
        if len(self.message_counts[client_id]) >= self.max_messages:
            return False
        
        # Add current message
        self.message_counts[client_id].append(now)
        return True

rate_limiter = MQTTRateLimiter(max_messages=100, window_seconds=60)

def on_message(client, userdata, msg):
    if not rate_limiter.check_rate_limit(client._client_id):
        print(f"Rate limit exceeded for {client._client_id}")
        return
    
    # Process message
    process_message(msg)
```

---

## 6. Secrets Management

### Environment Variables

**Best Practices:**
- Never commit secrets to git
- Use `.env` file (add to `.gitignore`)
- Load from environment in production

```python
# .env (not in git)
XAI_API_KEY=your-api-key
MQTT_PASSWORD=your-password
JWT_SECRET_KEY=your-secret-key
DATABASE_PASSWORD=your-db-password

# .gitignore
.env
*.key
*.pem
secrets/

# Load in code
from dotenv import load_dotenv
load_dotenv()

api_key = os.environ.get("XAI_API_KEY")
```

### Docker Secrets

```yaml
# docker-compose.yml
services:
  control-server:
    secrets:
      - xai_api_key
      - mqtt_password
    environment:
      - XAI_API_KEY_FILE=/run/secrets/xai_api_key
      - MQTT_PASSWORD_FILE=/run/secrets/mqtt_password

secrets:
  xai_api_key:
    file: ./secrets/xai_api_key.txt
  mqtt_password:
    file: ./secrets/mqtt_password.txt
```

**Access in code:**
```python
# Read from secret file
with open(os.environ.get("XAI_API_KEY_FILE"), "r") as f:
    api_key = f.read().strip()
```

### HashiCorp Vault (Enterprise)

```python
import hvac

client = hvac.Client(url='https://vault.example.com')
client.token = os.environ.get('VAULT_TOKEN')

# Read secret
secret = client.secrets.kv.v2.read_secret_version(path='grokmon/api-keys')
api_key = secret['data']['data']['xai_api_key']
```

---

## 7. Audit Logging

### Action Logging

```python
from datetime import datetime
import json

class AuditLogger:
    def __init__(self, log_file: str = "audit.log"):
        self.log_file = log_file
    
    def log_action(
        self,
        user: str,
        action: str,
        resource: str,
        success: bool,
        details: dict = None
    ):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "action": action,
            "resource": resource,
            "success": success,
            "details": details or {}
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def log_sensor_reading(self, sensor: str, value: float):
        self.log_action(
            user="system",
            action="sensor_reading",
            resource=sensor,
            success=True,
            details={"value": value}
        )
    
    def log_actuator_command(self, user: str, command: str, params: dict, success: bool):
        self.log_action(
            user=user,
            action="actuator_command",
            resource=command,
            success=success,
            details={"parameters": params}
        )

audit_logger = AuditLogger()

@app.post("/api/control/light")
async def control_light(command: dict, user: str = get_current_user()):
    try:
        result = execute_light_command(command)
        audit_logger.log_actuator_command(
            user=user,
            command="set_light_intensity",
            params=command,
            success=True
        )
        return result
    except Exception as e:
        audit_logger.log_actuator_command(
            user=user,
            command="set_light_intensity",
            params=command,
            success=False,
            details={"error": str(e)}
        )
        raise
```

### Security Event Logging

```python
def log_security_event(event_type: str, details: dict):
    """Log security-related events."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,  # "auth_failure", "rate_limit", "invalid_input", etc.
        "details": details
    }
    
    # Log to separate security log
    with open("security.log", "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    # Alert on critical events
    if event_type in ["unauthorized_access", "suspicious_activity"]:
        send_alert(entry)

# Usage
if failed_login_attempts > 5:
    log_security_event("auth_failure", {
        "username": username,
        "attempts": failed_login_attempts,
        "ip": request.client.host
    })
```

---

## 8. FastAPI Security Middleware

### Complete Security Setup

```python
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
import time

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://grokandmon.com"],  # Only allow specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Authentication
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

@app.get("/api/sensors", dependencies=[Depends(verify_token)])
@limiter.limit("10/minute")
async def get_sensors(request: Request):
    return {"sensors": get_sensor_data()}
```

---

## 9. Hardware Security

### Physical Security

- **Locked Enclosure:** Control server in locked cabinet
- **Tamper Detection:** Sensors for cabinet opening
- **Backup Power:** UPS for power outages
- **Fire Safety:** Smoke detectors, automatic shutdown

### Firmware Security

- **Signed Updates:** Verify firmware signatures
- **Secure Boot:** Prevent unauthorized firmware
- **Update Verification:** Check checksums before applying updates

```python
import hashlib

def verify_firmware_update(firmware_path: str, expected_hash: str) -> bool:
    """Verify firmware update before applying."""
    with open(firmware_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    return file_hash == expected_hash
```

---

## 10. Security Checklist

### Pre-Deployment

- [ ] All API endpoints require authentication
- [ ] HTTPS/TLS enabled for all connections
- [ ] MQTT uses TLS and authentication
- [ ] Secrets stored securely (not in code)
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] Audit logging configured
- [ ] Network segmentation implemented
- [ ] Firewall rules configured
- [ ] Backup and recovery plan

### Ongoing Maintenance

- [ ] Regular security updates
- [ ] Monitor audit logs
- [ ] Review access logs weekly
- [ ] Rotate API keys quarterly
- [ ] Update dependencies monthly
- [ ] Test backup/restore procedures
- [ ] Review firewall rules
- [ ] Check for suspicious activity

---

## Implementation for Grok & Mon

### Recommended Architecture

```
┌─────────────────────────────────────────┐
│         Internet (HTTPS Only)          │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────▼──────────┐
        │   Reverse Proxy    │
        │   (Nginx/Caddy)     │
        │   - TLS Termination │
        │   - Rate Limiting   │
        └─────────┬──────────┘
                  │
        ┌─────────▼──────────┐
        │   FastAPI Server   │
        │   - JWT Auth       │
        │   - Input Validation│
        │   - Audit Logging  │
        └─────────┬──────────┘
                  │
        ┌─────────▼──────────┐
        │   MQTT Broker      │
        │   (Mosquitto)      │
        │   - TLS            │
        │   - Auth           │
        └─────────┬──────────┘
                  │
        ┌─────────▼──────────┐
        │   IoT Devices      │
        │   (Sensors/Actuators)│
        └────────────────────┘
```

### Configuration Files

**`.env` (not in git):**
```bash
# API Keys
XAI_API_KEY=your-key-here
JWT_SECRET_KEY=your-secret-key-here

# MQTT
MQTT_BROKER=mqtt.local
MQTT_USERNAME=grokmon
MQTT_PASSWORD=your-password

# Database
DATABASE_URL=sqlite:///data/grokmon.db
DATABASE_ENCRYPTION_KEY=your-encryption-key

# Security
ALLOWED_ORIGINS=https://grokandmon.com
RATE_LIMIT_PER_MINUTE=10
```

**`docker-compose.yml` security:**
```yaml
services:
  api:
    environment:
      - JWT_SECRET_KEY_FILE=/run/secrets/jwt_secret
    secrets:
      - jwt_secret
      - xai_api_key
    networks:
      - api-network
  
  mqtt:
    volumes:
      - ./mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
      - ./mosquitto/passwd:/mosquitto/config/passwd:ro
    networks:
      - iot-network

secrets:
  jwt_secret:
    file: ./secrets/jwt_secret.txt
  xai_api_key:
    file: ./secrets/xai_api_key.txt

networks:
  api-network:
    internal: false
  iot-network:
    internal: true
```

---

## Sources & References

1. **OWASP IoT Security** - IoT security best practices
2. **FastAPI Security** - FastAPI security documentation
3. **Mosquitto Security** - MQTT broker security guide
4. **NIST IoT Security** - NIST guidelines for IoT security
5. **Docker Security** - Docker security best practices

---

*Last Updated: 2025-01-12*
*For use with Grok & Mon AI-autonomous cannabis cultivation system*
