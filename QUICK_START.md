# Quick Start Guide

## Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

## Installation & Run

### Option 1: Using the run script (Recommended)
```bash
./run.sh
```

### Option 2: Manual setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

## Access the API

Once the server is running:

- **API Documentation (Swagger UI)**: http://localhost:8080/docs
- **Alternative Documentation (ReDoc)**: http://localhost:8080/redoc
- **Health Check**: http://localhost:8080/health

## Quick Test

### 1. Create an account
```bash
curl -X POST "http://localhost:8080/api/accounts" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "ACC001",
    "account_name": "John Doe",
    "initial_balance": "1000.00"
  }'
```

### 2. Deposit money
```bash
curl -X POST "http://localhost:8080/api/transactions/deposit" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "ACC001",
    "amount": "500.00"
  }'
```

### 3. Check account balance
```bash
curl -X GET "http://localhost:8080/api/accounts/ACC001"
```

## Next Steps

- See `API_EXAMPLES.md` for comprehensive API usage examples
- See `README.md` for detailed system documentation

