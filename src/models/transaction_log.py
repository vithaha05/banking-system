"""
Transaction Log Model
Immutable audit trail of all transactions
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, CheckConstraint
from .base import Base


class TransactionType(str, Enum):
    """Transaction type enumeration"""
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    TRANSFER = "TRANSFER"


class TransactionStatus(str, Enum):
    """Transaction status enumeration"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"


class TransactionLog(Base):
    """
    Transaction Log Entity
    
    Design Decisions:
    - Immutable: Once created, transaction logs are never updated
    - All transactions (successful and failed) are logged for audit
    - Used for compliance, debugging, and transaction history
    - Foreign keys ensure referential integrity
    """
    __tablename__ = "transaction_logs"
    
    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_type = Column(String(20), nullable=False)
    source_account_id = Column(String(50), ForeignKey("accounts.account_id"), nullable=True)
    destination_account_id = Column(String(50), ForeignKey("accounts.account_id"), nullable=True)
    amount = Column(Numeric(19, 2), nullable=False)
    status = Column(String(20), nullable=False)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("transaction_type IN ('DEPOSIT', 'WITHDRAW', 'TRANSFER')", name="check_transaction_type"),
        CheckConstraint("status IN ('SUCCESS', 'FAILED', 'PENDING')", name="check_transaction_status"),
        CheckConstraint("amount > 0", name="check_amount_positive"),
    )
    
    def __repr__(self):
        return f"<TransactionLog(id={self.transaction_id}, type={self.transaction_type}, amount={self.amount}, status={self.status})>"

