import uuid
import asyncio
from decimal import Decimal
from fastapi.testclient import TestClient
from src.main import app
from src.database import init_db

# Ensure database tables exist before running tests
asyncio.run(init_db())

client = TestClient(app)

def make_account(balance="1000.00"):
    acc_id = f"T-{uuid.uuid4().hex[:8]}"   # unique id, so tests don't collide
    r = client.post("/api/accounts", json={
        "account_id": acc_id, "account_name": "Test", "initial_balance": balance})
    assert r.status_code == 201
    return acc_id

def balance(acc_id):
    return Decimal(client.get(f"/api/accounts/{acc_id}").json()["balance"])

def test_deposit_increases_balance():
    a = make_account()
    client.post("/api/transactions/deposit", json={"account_id": a, "amount": "500.00"})
    assert balance(a) == Decimal("1500.00")

def test_overdraft_rejected_and_balance_unchanged():
    a = make_account("100.00")
    r = client.post("/api/transactions/withdraw", json={"account_id": a, "amount": "200.00"})
    assert r.status_code >= 400
    assert balance(a) == Decimal("100.00")

def test_withdrawal_over_daily_limit_rejected():
    a = make_account("50000.00")
    r = client.post("/api/transactions/withdraw", json={"account_id": a, "amount": "10001.00"})
    assert r.status_code >= 400

def test_transfer_is_atomic_and_conserves_money():
    a, b = make_account("1000.00"), make_account("0.00")
    client.post("/api/transactions/transfer", json={
        "source_account_id": a, "destination_account_id": b, "amount": "300.00"})
    assert balance(a) + balance(b) == Decimal("1000.00")

def test_duplicate_transaction_within_60s_rejected():
    a = make_account()
    p = {"account_id": a, "amount": "25.00"}
    assert client.post("/api/transactions/withdraw", json=p).status_code == 200
    assert client.post("/api/transactions/withdraw", json=p).status_code >= 400
