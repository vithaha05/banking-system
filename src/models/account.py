"""
Account Model
Represents a bank account with balance and status
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import Column, String, Numeric, DateTime, CheckConstraint
from .base import Base


class AccountStatus(str, Enum):
    """Account status enumeration"""
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"


class Account(Base):
    """
    Account Entity
    
    Design Decisions:
    - Uses Decimal for precise financial calculations (no floating point errors)
    - Database-level CHECK constraint ensures balance >= 0
    - Status field prevents transactions on blocked accounts
    - Timestamps for audit trail
    """
    __tablename__ = "accounts"
    
    account_id = Column(String(50), primary_key=True)
    account_name = Column(String(255), nullable=False)
    balance = Column(Numeric(19, 2), nullable=False, default=Decimal("0.00"))
    status = Column(String(20), nullable=False, default=AccountStatus.ACTIVE.value)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("balance >= 0", name="check_balance_non_negative"),
        CheckConstraint("status IN ('ACTIVE', 'BLOCKED')", name="check_status_valid"),
    )
    
    def is_active(self) -> bool:
        """Check if account can perform transactions"""
        return self.status == AccountStatus.ACTIVE.value
    
    def has_sufficient_balance(self, amount: Decimal) -> bool:
        """Check if account has sufficient balance"""
        return self.balance >= amount
    
    def __repr__(self):
        return f"<Account(account_id={self.account_id}, balance={self.balance}, status={self.status})>"

