# Banking Transaction Processing System

A production-quality, banking-style transaction processing system designed for a global investment bank. This system ensures correctness, consistency, fault tolerance, and auditability of financial transactions.

## Technology Choice: Python

**Why Python?**
- **Rapid Development**: Faster to implement and iterate
- **Rich Ecosystem**: Excellent libraries (FastAPI, SQLAlchemy) for building production systems
- **Async Support**: Native async/await for handling concurrent requests efficiently
- **Type Safety**: Pydantic for request/response validation
- **Maintainability**: Clean, readable code that's easier to understand and maintain
- **Testing**: Excellent testing frameworks (pytest)
- **Industry Adoption**: Widely used in fintech and banking systems

## Architecture

### Layered Architecture

```
┌─────────────────────────────────────┐
│         API Layer (FastAPI)         │  ← REST endpoints, request validation
├─────────────────────────────────────┤
│      Service Layer (Business)       │  ← Business logic, transaction orchestration
├─────────────────────────────────────┤
│   Repository Layer (Data Access)    │  ← Database operations, queries
├─────────────────────────────────────┤
│      Database (SQLite/PostgreSQL)    │  ← Data persistence
└─────────────────────────────────────┘
```

### Key Components

1. **API Layer** (`src/api/`)
   - REST endpoints using FastAPI
   - Request/response validation with Pydantic
   - Error handling and HTTP status codes

2. **Service Layer** (`src/services/`)
   - Business logic and rules enforcement
   - Transaction orchestration
   - Concurrency control

3. **Repository Layer** (`src/repository/`)
   - Data access abstraction
   - Database queries
   - Pessimistic locking for concurrency

4. **Models** (`src/models/`)
   - Database entities
   - Business domain objects

## Core Features

### 1. Account Management
- Create accounts with unique IDs
- Store account name, balance, and status (ACTIVE/BLOCKED)
- Prevent negative balances (database-level constraint)
- Block/unblock accounts

### 2. Transaction Processing
- **Deposit**: Add money to an account
- **Withdraw**: Remove money from an account (with balance check)
- **Transfer**: Move money between accounts (atomic operation)

### 3. Consistency & Concurrency
- **Pessimistic Locking**: Uses `SELECT FOR UPDATE` to prevent race conditions
- **Database Transactions**: All operations are atomic (ACID guarantees)
- **Optimistic Concurrency**: Version field prevents lost updates
- **Isolation**: Proper transaction isolation levels

### 4. Failure Handling
- **Automatic Rollback**: Failed transactions are rolled back automatically
- **Error Logging**: All failures are logged in transaction_logs
- **Graceful Degradation**: Invalid operations return proper error responses

### 5. Audit Logging
- **Immutable Logs**: All transactions are logged (successful and failed)
- **Complete History**: Timestamp, accounts, amount, status, error messages
- **Compliance Ready**: Suitable for regulatory requirements

### 6. Business Rules
- **Balance Validation**: Cannot withdraw/transfer more than available
- **Account Status**: Blocked accounts cannot perform transactions
- **Daily Limits**: 
  - Withdrawal limit: $10,000 per day
  - Transfer limit: $50,000 per day
- **Duplicate Prevention**: Detects duplicate transactions within 60 seconds

## Database Schema

### Accounts Table
```sql
CREATE TABLE accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    account_name VARCHAR(255) NOT NULL,
    balance DECIMAL(19, 2) NOT NULL DEFAULT 0.00,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (balance >= 0),
    CHECK (status IN ('ACTIVE', 'BLOCKED'))
);
```

### Transaction Logs Table
```sql
CREATE TABLE transaction_logs (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_type VARCHAR(20) NOT NULL,
    source_account_id VARCHAR(50),
    destination_account_id VARCHAR(50),
    amount DECIMAL(19, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (transaction_type IN ('DEPOSIT', 'WITHDRAW', 'TRANSFER')),
    CHECK (status IN ('SUCCESS', 'FAILED', 'PENDING')),
    CHECK (amount > 0)
);
```

## Concurrency Handling

### Problem: Race Conditions
When multiple transactions access the same account simultaneously, race conditions can occur:
- Two withdrawals reading the same balance
- Both succeeding when only one should

### Solution: Pessimistic Locking
```python
# Lock account row during transaction
account = await account_repo.find_by_id(account_id, lock=True)  # SELECT FOR UPDATE
```

**How it works:**
1. When a transaction starts, it locks the account row
2. Other transactions wait until the lock is released
3. Ensures sequential access to account balance
4. Prevents lost updates and race conditions

### Transaction Isolation
- All operations use database transactions
- Automatic rollback on failure
- ACID guarantees (Atomicity, Consistency, Isolation, Durability)

## Failure Scenarios

### 1. Insufficient Funds
- **Scenario**: Withdraw/transfer exceeds balance
- **Handling**: Exception raised, transaction rolled back, logged as FAILED
- **Response**: HTTP 402 with error message

### 2. Account Not Found
- **Scenario**: Invalid account ID
- **Handling**: Exception raised, transaction rolled back, logged as FAILED
- **Response**: HTTP 404 with error message

### 3. Blocked Account
- **Scenario**: Transaction on blocked account
- **Handling**: Exception raised, transaction rolled back, logged as FAILED
- **Response**: HTTP 403 with error message

### 4. Daily Limit Exceeded
- **Scenario**: Transaction exceeds daily limit
- **Handling**: Exception raised, transaction rolled back, logged as FAILED
- **Response**: HTTP 429 with error message

### 5. Database Failure
- **Scenario**: Database connection lost or constraint violation
- **Handling**: Automatic rollback, exception propagated
- **Response**: HTTP 500 with error message

### 6. Duplicate Transaction
- **Scenario**: Same transaction submitted twice within 60 seconds
- **Handling**: Exception raised, transaction rejected
- **Response**: HTTP 409 with error message

## Banking Assumptions

1. **Precision**: All monetary values use `Decimal` type (no floating-point errors)
2. **Immutability**: Transaction logs are never updated (audit trail)
3. **Atomicity**: All multi-step operations are atomic (all-or-nothing)
4. **Consistency**: Database constraints enforce business rules
5. **Auditability**: All transactions (successful and failed) are logged
6. **Idempotency**: Duplicate transactions are detected and rejected
7. **Limits**: Daily transaction limits prevent fraud and errors
8. **Status Management**: Accounts can be blocked/unblocked for security

## Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Setup

1. **Clone/Navigate to project directory**
```bash
cd banking-system
```

2. **Create virtual environment (recommended)**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the application**
```bash
python -m src.main
```

Or using uvicorn directly:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

5. **Access API Documentation**
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## API Endpoints

### Account Management

- `POST /api/accounts` - Create account
- `GET /api/accounts/{account_id}` - Get account details
- `GET /api/accounts` - Get all accounts
- `POST /api/accounts/{account_id}/block` - Block account
- `POST /api/accounts/{account_id}/unblock` - Unblock account

### Transactions

- `POST /api/transactions/deposit` - Deposit money
- `POST /api/transactions/withdraw` - Withdraw money
- `POST /api/transactions/transfer` - Transfer money
- `GET /api/transactions/history/{account_id}` - Get transaction history

## Testing

### Manual Testing with curl

See `API_EXAMPLES.md` for detailed API request examples.

### Automated Testing (pytest)

The system is covered by automated pytest tests verifying core transaction endpoints, business rules, limits, and ACID guarantees:

```bash
# Run all tests
pytest tests/ -v
```

**Test Coverage:**
- `test_deposit_increases_balance`: Verifies deposits correctly increase account balance.
- `test_overdraft_rejected_and_balance_unchanged`: Verifies overdraft requests are rejected and account balance remains unchanged.
- `test_withdrawal_over_daily_limit_rejected`: Enforces daily withdrawal limits ($10,000 max per day) with 429/4xx rejection.
- `test_transfer_is_atomic_and_conserves_money`: Verifies atomic multi-account transfers conserve total money.
- `test_duplicate_transaction_within_60s_rejected`: Verifies immediate duplicate transactions within the 60-second window are rejected.


## Migration to PostgreSQL

To migrate from SQLite to PostgreSQL:

1. Update `DATABASE_URL` in environment:
```bash
export DATABASE_URL="postgresql+asyncpg://user:password@localhost/banking_db"
```

2. Install PostgreSQL driver:
```bash
pip install asyncpg
```

3. Update `requirements.txt` to include `asyncpg`

4. The schema is compatible - no code changes needed!

## Production Considerations

1. **Database**: Use PostgreSQL for production (better concurrency, ACID guarantees)
2. **Connection Pooling**: Configure appropriate pool size
3. **Logging**: Implement structured logging (e.g., with structlog)
4. **Monitoring**: Add metrics and health checks
5. **Security**: 
   - Add authentication/authorization
   - Use HTTPS
   - Implement rate limiting
   - Input sanitization (already handled by Pydantic)
6. **Backup**: Regular database backups
7. **Scaling**: Consider read replicas for transaction history queries

## Project Structure

```
banking-system/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── database.py             # Database configuration
│   ├── exceptions.py           # Custom exceptions
│   ├── api/                    # API layer
│   │   ├── __init__.py
│   │   ├── schemas.py          # Pydantic schemas
│   │   ├── account_routes.py   # Account endpoints
│   │   └── transaction_routes.py # Transaction endpoints
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── account_service.py
│   │   └── transaction_service.py
│   ├── repository/             # Data access layer
│   │   ├── __init__.py
│   │   ├── account_repository.py
│   │   └── transaction_repository.py
│   └── models/                 # Database models
│       ├── __init__.py
│       ├── base.py
│       ├── account.py
│       └── transaction_log.py
├── tests/
│   ├── __init__.py
│   └── test_transactions.py    # Automated API tests
├── requirements.txt
├── .gitignore
└── README.md
```

## License

This is a demonstration project for educational purposes.

## Author

Built as a production-quality banking transaction processing system demonstrating:
- Clean architecture
- ACID transaction guarantees
- Concurrency control
- Error handling
- Audit logging
- Business rule enforcement

