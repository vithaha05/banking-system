# API Request Examples

This document provides sample API requests for testing the Banking Transaction Processing System.

## Base URL
```
http://localhost:8080
```

## Account Management

### 1. Create Account

**Request:**
```bash
curl -X POST "http://localhost:8080/api/accounts" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "ACC001",
    "account_name": "John Doe",
    "initial_balance": "1000.00"
  }'
```

**Response (201 Created):**
```json
{
  "account_id": "ACC001",
  "account_name": "John Doe",
  "balance": "1000.00",
  "status": "ACTIVE",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### 2. Get Account Details

**Request:**
```bash
curl -X GET "http://localhost:8080/api/accounts/ACC001"
```

**Response (200 OK):**
```json
{
  "account_id": "ACC001",
  "account_name": "John Doe",
  "balance": "1000.00",
  "status": "ACTIVE",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### 3. Get All Accounts

**Request:**
```bash
curl -X GET "http://localhost:8080/api/accounts"
```

**Response (200 OK):**
```json
[
  {
    "account_id": "ACC001",
    "account_name": "John Doe",
    "balance": "1000.00",
    "status": "ACTIVE",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  },
  {
    "account_id": "ACC002",
    "account_name": "Jane Smith",
    "balance": "5000.00",
    "status": "ACTIVE",
    "created_at": "2024-01-15T10:35:00",
    "updated_at": "2024-01-15T10:35:00"
  }
]
```

### 4. Block Account

**Request:**
```bash
curl -X POST "http://localhost:8080/api/accounts/ACC001/block"
```

**Response (200 OK):**
```json
{
  "account_id": "ACC001",
  "account_name": "John Doe",
  "balance": "1000.00",
  "status": "BLOCKED",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T11:00:00"
}
```

### 5. Unblock Account

**Request:**
```bash
curl -X POST "http://localhost:8080/api/accounts/ACC001/unblock"
```

**Response (200 OK):**
```json
{
  "account_id": "ACC001",
  "account_name": "John Doe",
  "balance": "1000.00",
  "status": "ACTIVE",
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T11:05:00"
}
```

## Transactions

### 1. Deposit Money

**Request:**
```bash
curl -X POST "http://localhost:8080/api/transactions/deposit" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "ACC001",
    "amount": "500.00"
  }'
```

**Response (200 OK):**
```json
{
  "transaction_type": "DEPOSIT",
  "account_id": "ACC001",
  "amount": "500.00",
  "new_balance": "1500.00",
  "status": "SUCCESS"
}
```

### 2. Withdraw Money

**Request:**
```bash
curl -X POST "http://localhost:8080/api/transactions/withdraw" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "ACC001",
    "amount": "200.00"
  }'
```

**Response (200 OK):**
```json
{
  "transaction_type": "WITHDRAW",
  "account_id": "ACC001",
  "amount": "200.00",
  "new_balance": "1300.00",
  "status": "SUCCESS"
}
```

**Error Response - Insufficient Funds (402 Payment Required):**
```json
{
  "error": "InsufficientFundsException",
  "detail": "Insufficient funds. Available: 1000.00, Required: 2000.00"
}
```

**Error Response - Daily Limit Exceeded (429 Too Many Requests):**
```json
{
  "error": "TransactionLimitException",
  "detail": "Daily withdrawal limit exceeded. Limit: 10000.00, Today's total: 9500.00, Requested: 1000.00"
}
```

### 3. Transfer Money

**Request:**
```bash
curl -X POST "http://localhost:8080/api/transactions/transfer" \
  -H "Content-Type: application/json" \
  -d '{
    "source_account_id": "ACC001",
    "destination_account_id": "ACC002",
    "amount": "300.00"
  }'
```

**Response (200 OK):**
```json
{
  "transaction_type": "TRANSFER",
  "source_account_id": "ACC001",
  "destination_account_id": "ACC002",
  "amount": "300.00",
  "source_new_balance": "1000.00",
  "destination_new_balance": "5300.00",
  "status": "SUCCESS"
}
```

**Error Response - Same Account (400 Bad Request):**
```json
{
  "error": "ValueError",
  "detail": "Source and destination accounts cannot be the same"
}
```

### 4. Get Transaction History

**Request:**
```bash
curl -X GET "http://localhost:8080/api/transactions/history/ACC001?limit=10"
```

**Response (200 OK):**
```json
[
  {
    "transaction_id": 5,
    "transaction_type": "WITHDRAW",
    "source_account_id": "ACC001",
    "destination_account_id": null,
    "amount": "200.00",
    "status": "SUCCESS",
    "error_message": null,
    "created_at": "2024-01-15T11:20:00"
  },
  {
    "transaction_id": 4,
    "transaction_type": "DEPOSIT",
    "source_account_id": null,
    "destination_account_id": "ACC001",
    "amount": "500.00",
    "status": "SUCCESS",
    "error_message": null,
    "created_at": "2024-01-15T11:15:00"
  },
  {
    "transaction_id": 3,
    "transaction_type": "TRANSFER",
    "source_account_id": "ACC001",
    "destination_account_id": "ACC002",
    "amount": "300.00",
    "status": "SUCCESS",
    "error_message": null,
    "created_at": "2024-01-15T11:10:00"
  }
]
```

## Error Responses

### Account Not Found (404)
```json
{
  "error": "InvalidAccountException",
  "detail": "Account ACC999 not found"
}
```

### Account Blocked (403)
```json
{
  "error": "InvalidAccountException",
  "detail": "Account ACC001 is blocked and cannot perform withdrawals"
}
```

### Duplicate Transaction (409)
```json
{
  "error": "DuplicateTransactionException",
  "detail": "Duplicate withdrawal transaction detected"
}
```

## Complete Workflow Example

Here's a complete workflow demonstrating account creation and transactions:

```bash
# 1. Create two accounts
curl -X POST "http://localhost:8080/api/accounts" \
  -H "Content-Type: application/json" \
  -d '{"account_id": "ACC001", "account_name": "Alice", "initial_balance": "1000.00"}'

curl -X POST "http://localhost:8080/api/accounts" \
  -H "Content-Type: application/json" \
  -d '{"account_id": "ACC002", "account_name": "Bob", "initial_balance": "500.00"}'

# 2. Deposit money into ACC001
curl -X POST "http://localhost:8080/api/transactions/deposit" \
  -H "Content-Type: application/json" \
  -d '{"account_id": "ACC001", "amount": "500.00"}'

# 3. Transfer money from ACC001 to ACC002
curl -X POST "http://localhost:8080/api/transactions/transfer" \
  -H "Content-Type: application/json" \
  -d '{"source_account_id": "ACC001", "destination_account_id": "ACC002", "amount": "300.00"}'

# 4. Check account balances
curl -X GET "http://localhost:8080/api/accounts/ACC001"
curl -X GET "http://localhost:8080/api/accounts/ACC002"

# 5. Get transaction history for ACC001
curl -X GET "http://localhost:8080/api/transactions/history/ACC001"
```

## Using Python requests

```python
import requests

BASE_URL = "http://localhost:8080"

# Create account
response = requests.post(
    f"{BASE_URL}/api/accounts",
    json={
        "account_id": "ACC001",
        "account_name": "John Doe",
        "initial_balance": "1000.00"
    }
)
print(response.json())

# Deposit
response = requests.post(
    f"{BASE_URL}/api/transactions/deposit",
    json={
        "account_id": "ACC001",
        "amount": "500.00"
    }
)
print(response.json())

# Transfer
response = requests.post(
    f"{BASE_URL}/api/transactions/transfer",
    json={
        "source_account_id": "ACC001",
        "destination_account_id": "ACC002",
        "amount": "300.00"
    }
)
print(response.json())
```

## Testing Concurrency

To test concurrent transactions, you can use multiple terminal windows or a script:

```bash
# Terminal 1
for i in {1..10}; do
  curl -X POST "http://localhost:8080/api/transactions/deposit" \
    -H "Content-Type: application/json" \
    -d "{\"account_id\": \"ACC001\", \"amount\": \"100.00\"}" &
done
wait

# Terminal 2 (simultaneously)
for i in {1..10}; do
  curl -X POST "http://localhost:8080/api/transactions/withdraw" \
    -H "Content-Type: application/json" \
    -d "{\"account_id\": \"ACC001\", \"amount\": \"50.00\"}" &
done
wait

# Check final balance
curl -X GET "http://localhost:8080/api/accounts/ACC001"
```

The system will handle these concurrent requests safely using pessimistic locking.

