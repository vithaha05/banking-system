"""
Transaction Repository
Data access layer for Transaction Log operations
"""
from datetime import datetime, date, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from decimal import Decimal

from src.models.transaction_log import TransactionLog, TransactionType, TransactionStatus


class TransactionRepository:
    """
    Repository for Transaction Log operations
    
    Design Decisions:
    - Transaction logs are immutable (insert-only)
    - Used for audit trail and compliance
    - Supports querying for daily limits and transaction history
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_log(
        self,
        transaction_type: TransactionType,
        amount: Decimal,
        status: TransactionStatus,
        source_account_id: Optional[str] = None,
        destination_account_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> TransactionLog:
        """Create a new transaction log entry"""
        log = TransactionLog(
            transaction_type=transaction_type.value,
            source_account_id=source_account_id,
            destination_account_id=destination_account_id,
            amount=amount,
            status=status.value,
            error_message=error_message
        )
        self.session.add(log)
        await self.session.flush()
        return log
    
    async def get_daily_transaction_total(
        self,
        account_id: str,
        transaction_date: date,
        transaction_types: List[TransactionType]
    ) -> Decimal:
        """
        Get total amount of transactions for an account on a specific date
        
        Used for enforcing daily transaction limits
        """
        type_values = [t.value for t in transaction_types]
        
        query = select(func.sum(TransactionLog.amount)).where(
            and_(
                TransactionLog.source_account_id == account_id,
                TransactionLog.status == TransactionStatus.SUCCESS.value,
                func.date(TransactionLog.created_at) == transaction_date,
                TransactionLog.transaction_type.in_(type_values)
            )
        )
        
        result = await self.session.execute(query)
        total = result.scalar()
        return Decimal(total) if total else Decimal("0.00")
    
    async def get_transaction_history(
        self,
        account_id: str,
        limit: int = 100
    ) -> List[TransactionLog]:
        """Get transaction history for an account"""
        query = select(TransactionLog).where(
            (TransactionLog.source_account_id == account_id) |
            (TransactionLog.destination_account_id == account_id)
        ).order_by(TransactionLog.created_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def check_duplicate_transaction(
        self,
        transaction_type: TransactionType,
        source_account_id: Optional[str],
        destination_account_id: Optional[str],
        amount: Decimal,
        time_window_seconds: int = 60
    ) -> bool:
        """
        Check if a duplicate transaction exists within a time window
        
        Prevents accidental duplicate submissions
        """
        cutoff_time = datetime.utcnow() - timedelta(seconds=time_window_seconds)
        
        conditions = [
            TransactionLog.transaction_type == transaction_type.value,
            TransactionLog.amount == amount,
            TransactionLog.status == TransactionStatus.SUCCESS.value,
            TransactionLog.created_at >= cutoff_time
        ]
        
        if source_account_id:
            conditions.append(TransactionLog.source_account_id == source_account_id)
        if destination_account_id:
            conditions.append(TransactionLog.destination_account_id == destination_account_id)
        
        query = select(TransactionLog).where(and_(*conditions))
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

