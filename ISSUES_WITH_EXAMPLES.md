# Key Issues with Code Examples

## CRITICAL ISSUES

### 1. Default SECRET_KEY Vulnerability

**File**: `src/config.py:16`

```python
# CURRENT (INSECURE)
class Settings(BaseSettings):
    secret_key: SecretStr = "secret"  # ❌ CRITICAL ISSUE
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
```

**Problem**: Anyone can forge JWT tokens using the known key "secret"

**Impact**: Complete authentication bypass

**Fix**:
```python
from pydantic import Field, SecretStr
from functools import lru_cache

class Settings(BaseSettings):
    secret_key: SecretStr = Field(
        ...,  # Make it required
        description="JWT secret key. MUST be changed in production!"
    )
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: SecretStr) -> SecretStr:
        if v.get_secret_value() == "secret":
            raise ValueError(
                "SECRET_KEY cannot be 'secret'. "
                "Set SECRET_KEY environment variable to a strong random value."
            )
        return v
```

---

### 2. Public Reservations Endpoint (Privacy Breach)

**File**: `src/routers/reservations.py:11`

```python
# CURRENT (NO AUTHENTICATION)
@router.get("/", name="List of all reservations", response_model=list[ReservationResponse])
async def get_all_reservations_ep(session: session_type):  # ❌ Anyone can access
    return await get_all_reservations(session)
```

**Problem**: Anyone can access full list of reservations including user emails and schedules

**Fix**:
```python
from src.security import JWTBearer

@router.get("/", name="List of all reservations", response_model=list[ReservationResponse])
async def get_all_reservations_ep(
    session: session_type, 
    user_id: int = Depends(JWTBearer())  # ✓ Add authentication
):
    # Optional: only return reservations for the current user
    return await get_all_user_reservations(user_id, session)
```

---

### 3. Zero Test Coverage

**File**: Entire project

**Problem**: No tests exist for:
- Authentication (token generation, validation, expiration)
- User creation (duplicate username/email, password hashing)
- Availability creation (constraints, race conditions)
- Reservation creation (4+ user logic)
- Error handling (invalid inputs, database failures)

**Example Missing Tests**:
```python
# tests/test_users.py (DOES NOT EXIST)
import pytest
from src.schemas.users import UserCreate
from src.controllers.users import create_user

@pytest.mark.asyncio
async def test_create_user_success(session):
    """Test successful user creation"""
    user = await create_user("john", "john@example.com", "password", session)
    assert user.username == "john"
    assert user.email == "john@example.com"
    assert user.check_password("password")

@pytest.mark.asyncio
async def test_duplicate_username_fails(session):
    """Test that duplicate username is rejected"""
    await create_user("john", "john@example.com", "password", session)
    result = await create_user("john", "john2@example.com", "password", session)
    assert result is None  # Should fail

@pytest.mark.asyncio
async def test_jwt_token_expiration(settings):
    """Test that expired tokens are rejected"""
    # ... test code
    
# tests/test_availabilities.py (DOES NOT EXIST)
@pytest.mark.asyncio
async def test_availability_race_condition(session):
    """Test race condition when multiple users create availability simultaneously"""
    # This test would catch the race condition bug
    # ... test code
```

---

## HIGH PRIORITY ISSUES

### 4. Race Condition in Availability Creation

**File**: `src/routers/availabilities.py:32-65`

```python
# CURRENT (VULNERABLE TO RACE CONDITIONS)
async def create_availability_ep(
    payload: AvailabilityCreate,
    session: session_type,
    bg_tasks: BackgroundTasks,
    user_id: int = Depends(JWTBearer()),
):
    start_datetime = datetime.combine(payload.date, time(payload.slot_start_hour))
    end_datetime = start_datetime + timedelta(hours=1)

    # ❌ CHECK-THEN-ACT PATTERN (RACE CONDITION)
    # Multiple concurrent requests could read the same count
    a_exists = await get_availability(start_datetime, end_datetime, session)
    exists_user_ids = [a.user_id for a in a_exists]
    
    if user_id in exists_user_ids:
        raise HTTPException(status_code=400, detail="Slot is already booked")

    # Between this check and the create, another user could create availability
    a = await create_availability(user_id, start_datetime, end_datetime, session)
    exists_user_ids.append(user_id)
    a_exists.append(a)

    # Race condition: multiple requests reach here with count=4
    if len(a_exists) >= 4:  # ❌ Both could be true!
        try:
            reservation = await create_reservation(start_datetime, end_datetime, session)
            # ...
```

**Scenario**:
```
Time    Thread A                    Thread B                    Thread C
0       Check count=3              -                           -
1       -                          Check count=3               -
2       -                          -                           Check count=3
3       Create availability        -                           -
4       -                          Create availability         -
5       -                          -                           Create availability
6       Count=4? YES, create res   Count=4? YES, create res    Count=4? YES, create res
        ↓                          ↓                           ↓
        FAILS (unique constraint)  FAILS (unique constraint)   SUCCEEDS
```

**Fix**:
```python
from sqlalchemy import select, func

async def create_availability_ep(...):
    # Option 1: Use database-level uniqueness check
    try:
        a = await create_availability(user_id, start_datetime, end_datetime, session)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="Slot is already booked")
    
    # Option 2: Use COUNT(*) with HAVING
    count = session.query(func.count(Availability.id)).filter(
        Availability.start == start_datetime,
        Availability.end == end_datetime
    ).scalar()
    
    if count >= 4:
        # Use SELECT FOR UPDATE to prevent other threads from modifying
        # (Note: SQLite doesn't support FOR UPDATE, but PostgreSQL does)
```

---

### 5. Generic Exception Handling

**File**: `src/routers/availabilities.py:49-56`

```python
# CURRENT (HIDES ACTUAL ERRORS)
try:
    reservation = await create_reservation(start_datetime, end_datetime, session)
    for a in a_exists:
        await create_reservation_relation(a.user_id, reservation.id, session)
except Exception as e:  # ❌ Catches EVERYTHING
    logging.error(f"sql error: {e}")
    session.rollback()
    raise HTTPException(status_code=400, detail="Error creating reservation")
```

**Problems**:
- Catches all exceptions, not just SQL errors
- Client gets generic error message
- Debugging is impossible
- Hides programming errors

**What could be caught**:
```
- IntegrityError (duplicate key)  → 409 Conflict
- OperationalError (DB connection) → 503 Service Unavailable
- ValueError (invalid input)      → 400 Bad Request
- Timeout                         → 504 Gateway Timeout
- Programming error               → 500 Internal Server Error
```

**Fix**:
```python
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

try:
    reservation = await create_reservation(start_datetime, end_datetime, session)
    for a in a_exists:
        await create_reservation_relation(a.user_id, reservation.id, session)
except IntegrityError as e:
    session.rollback()
    logging.error(f"Reservation already exists for this time slot: {e}")
    raise HTTPException(
        status_code=409,
        detail="A reservation already exists for this time slot"
    )
except OperationalError as e:
    session.rollback()
    logging.error(f"Database connection error: {e}")
    raise HTTPException(
        status_code=503,
        detail="Database service unavailable. Please try again later."
    )
except SQLAlchemyError as e:
    session.rollback()
    logging.error(f"Database error: {e}")
    raise HTTPException(
        status_code=500,
        detail="Internal server error"
    )
except Exception as e:
    session.rollback()
    logging.exception(f"Unexpected error: {e}")  # Use exception() to include traceback
    raise HTTPException(
        status_code=500,
        detail="Internal server error"
    )
```

---

### 6. No Docstrings

**File**: All Python files

```python
# CURRENT (NO DOCUMENTATION)
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, unique=True)
    # ... no docstring explaining what this model represents

@property
def password_setter(self):  # ❌ Name is confusing, no docstring
    raise AttributeError("Password can't be read")

@password_setter.setter
def password_setter(self, password: str) -> None:
    self.password = pwd_context.hash(password)

def check_password(self, plane_password: str) -> bool:
    # ❌ Typo: "plane_password" should be "plain_password"
    # ❌ No docstring explaining what this returns
    return pwd_context.verify(plane_password, self.password)
```

**Fix**:
```python
class User(Base):
    """User account model.
    
    Stores user authentication information and relationships to
    availabilities and reservations.
    """
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    """Unique user identifier"""
    
    username: Mapped[str] = mapped_column(Text, unique=True)
    """Unique username for login"""
    
    email: Mapped[str] = mapped_column(Text, unique=True)
    """Unique email address for notifications"""

    @property
    def password_setter(self):
        """Password cannot be read directly (write-only property)."""
        raise AttributeError("Password can't be read")

    @password_setter.setter
    def password_setter(self, password: str) -> None:
        """Hash and store the password.
        
        Args:
            password: Plain text password to hash
        """
        self.password = pwd_context.hash(password)

    def check_password(self, plain_password: str) -> bool:
        """Verify a password against the stored hash.
        
        Args:
            plain_password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, self.password)
```

---

## MEDIUM PRIORITY ISSUES

### 7. No Rate Limiting

**File**: `src/routers/users.py:19`

```python
# CURRENT (NO RATE LIMITING)
@router.post("/login", response_model=UserJWT)
async def user_login(payload: UserLogin, session: session_type):
    # ❌ No rate limiting - can be brute forced
    user = await get_user_by_username(payload.username, session)
    if not user or not user.check_password(payload.password):
        raise HTTPException(status_code=401, detail="Wrong user or password")
    return sign_jwt(user.id)
```

**Attack**: 10,000 login attempts per second with no limit

**Fix**:
```python
# Install: pip install slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login", response_model=UserJWT)
@limiter.limit("5/minute")  # 5 attempts per minute per IP
async def user_login(payload: UserLogin, session: session_type):
    user = await get_user_by_username(payload.username, session)
    if not user or not user.check_password(payload.password):
        raise HTTPException(status_code=401, detail="Wrong user or password")
    return sign_jwt(user.id)
```

---

### 8. Hardcoded Database URL

**File**: `src/controllers/db.py:8`

```python
# CURRENT (HARDCODED)
SQLALCHEMY_DATABASE_URL = "sqlite:///./padel_app.db"  # ❌ Not configurable

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
```

**Problems**:
- Can't use PostgreSQL in production
- Can't use MySQL for testing
- Can't change location without code change
- Not suitable for multi-server deployment

**Fix**:
```python
# src/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./padel_app.db"  # Configurable

# src/controllers/db.py
from src.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)
```

---

### 9. Typo in Filename

**File**: `src/controllers/availabilites.py` (should be `availabilities.py`)

```
# Current: availabilites.py (WRONG - missing 'i')
# Should: availabilities.py (CORRECT)
```

This causes:
- Confusion for developers
- Search failures ("availabilities" won't find "availabilites")
- Spelling mistake in codebase
- Inconsistent with other files

---

## SMALL IMPROVEMENTS

### 10. Missing Logging Configuration

**Current**: Ad-hoc logging with no configuration
```python
logging.error(e)  # ❌ No configuration
```

**Fix**:
```python
# src/logging_config.py
import logging
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "src": {
            "handlers": ["default"],
            "level": "INFO",
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
```

---

### 11. Missing .env.example

**File**: Should exist but doesn't

```bash
# .env.example
SECRET_KEY=your-secret-key-here-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
SERVICE_PORT=8000
NOTIFICATIONS_URL=http://notifications-service:7777/v1/email_service
DATABASE_URL=sqlite:///./padel_app.db
```

---

## Summary Table

| Issue | Severity | Lines | File |
|-------|----------|-------|------|
| Default SECRET_KEY | CRITICAL | 1 | config.py:16 |
| Public /reservations | CRITICAL | 3 | routers/reservations.py:11 |
| No tests | CRITICAL | 0 | - |
| Race condition | HIGH | 30 | routers/availabilities.py:22-65 |
| Generic exceptions | HIGH | 8 | routers/availabilities.py:49-56 |
| No docstrings | HIGH | 490 | All files |
| No rate limiting | MEDIUM | - | routers/users.py:19 |
| Hardcoded DB URL | MEDIUM | 1 | controllers/db.py:8 |
| Typo in filename | MEDIUM | 1 | availabilites.py |
| No logging config | MEDIUM | 5 | Throughout |
| No .env.example | LOW | - | - |

---

For complete analysis, see: `CODEBASE_ANALYSIS.txt`
