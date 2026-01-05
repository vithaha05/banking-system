"""
Pydantic Schemas for API Request/Response Validation
"""
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from src.models.account import AccountStatus
from src.models.transaction_log import TransactionType, TransactionStatus


class CreateAccountRequest(BaseModel):
    """Request schema for creating an account"""
    account_id: str = Field(..., min_length=1, max_length=50, description="Unique account identifier")
    account_name: str = Field(..., min_length=1, max_length=255, description="Account holder name")
    initial_balance: Decimal = Field(..., ge=0, description="Initial account balance (must be non-negative)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "ACC001",
                "account_name": "John Doe",
                "initial_balance": "1000.00"
            }
        }


class AccountResponse(BaseModel):
    """Response schema for account information"""
    account_id: str
    account_name: str
    balance: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DepositRequest(BaseModel):
    """Request schema for deposit transaction"""
    account_id: str = Field(..., description="Account ID to deposit into")
    amount: Decimal = Field(..., gt=0, description="Deposit amount (must be positive)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "ACC001",
                "amount": "500.00"
            }
        }


class WithdrawRequest(BaseModel):
    """Request schema for withdrawal transaction"""
    account_id: str = Field(..., description="Account ID to withdraw from")
    amount: Decimal = Field(..., gt=0, description="Withdrawal amount (must be positive)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "ACC001",
                "amount": "200.00"
            }
        }


class TransferRequest(BaseModel):
    """Request schema for transfer transaction"""
    source_account_id: str = Field(..., description="Source account ID")
    destination_account_id: str = Field(..., description="Destination account ID")
    amount: Decimal = Field(..., gt=0, description="Transfer amount (must be positive)")
    
    @field_validator('source_account_id', 'destination_account_id')
    @classmethod
    def accounts_must_differ(cls, v, info):
        if 'source_account_id' in info.data and 'destination_account_id' in info.data:
            if info.data['source_account_id'] == info.data['destination_account_id']:
                raise ValueError("Source and destination accounts cannot be the same")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_account_id": "ACC001",
                "destination_account_id": "ACC002",
                "amount": "300.00"
            }
        }


class TransactionResponse(BaseModel):
    """Response schema for transaction operations"""
    transaction_type: str
    status: str
    amount: str
    account_id: Optional[str] = None
    source_account_id: Optional[str] = None
    destination_account_id: Optional[str] = None
    new_balance: Optional[str] = None
    source_new_balance: Optional[str] = None
    destination_new_balance: Optional[str] = None


class TransactionHistoryResponse(BaseModel):
    """Response schema for transaction history"""
    transaction_id: int
    transaction_type: str
    source_account_id: Optional[str]
    destination_account_id: Optional[str]
    amount: str
    status: str
    error_message: Optional[str]
    created_at: str


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    detail: Optional[str] = None

