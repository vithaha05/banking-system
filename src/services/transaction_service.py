"""
Transaction Service
Business logic layer for Transaction operations
Handles deposits, withdrawals, and transfers with ACID guarantees
"""
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.account import AccountStatus
from src.models.transaction_log import TransactionType, TransactionStatus
from src.repository.account_repository import AccountRepository
from src.repository.transaction_repository import TransactionRepository
from src.exceptions import (
    InsufficientFundsException,
    InvalidAccountException,
    TransactionLimitException,
    DuplicateTransactionException
)


class TransactionService:
    """
    Service for Transaction business logic
    
    Design Decisions:
    - All transactions are atomic (all-or-nothing)
    - Uses pessimistic locking (SELECT FOR UPDATE) to prevent race conditions
    - Enforces business rules (sufficient funds, account status, daily limits)
    - Maintains immutable audit log
    - Handles rollback on failure
    """
    
    # Business Rules - Daily Transaction Limits
    DAILY_WITHDRAWAL_LIMIT = Decimal("10000.00")  # $10,000 per day
    DAILY_TRANSFER_LIMIT = Decimal("50000.00")    # $50,000 per day
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.account_repo = AccountRepository(session)
        self.transaction_repo = TransactionRepository(session)
    
    async def deposit(self, account_id: str, amount: Decimal) -> dict:
        """
        Deposit money into an account
        
        Business Rules:
        - Account must exist and be active
        - Amount must be positive
        - Transaction is logged
        """
        # Validate amount
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        # Get account with lock to prevent concurrent modifications
        account = await self.account_repo.find_by_id_or_raise(account_id, lock=True)
        
        # Validate account status
        if not account.is_active():
            error_msg = f"Account {account_id} is blocked and cannot receive deposits"
            await self._log_transaction(
                TransactionType.DEPOSIT,
                amount,
                TransactionStatus.FAILED,
                destination_account_id=account_id,
                error_message=error_msg
            )
            raise InvalidAccountException(error_msg)
        
        try:
            # Update balance
            new_balance = account.balance + amount
            account.balance = new_balance
            await self.session.flush()
            
            # Log successful transaction
            await self._log_transaction(
                TransactionType.DEPOSIT,
                amount,
                TransactionStatus.SUCCESS,
                destination_account_id=account_id
            )
            
            return {
                "transaction_type": "DEPOSIT",
                "account_id": account_id,
                "amount": str(amount),
                "new_balance": str(new_balance),
                "status": "SUCCESS"
            }
        except Exception as e:
            # Log failed transaction
            await self._log_transaction(
                TransactionType.DEPOSIT,
                amount,
                TransactionStatus.FAILED,
                destination_account_id=account_id,
                error_message=str(e)
            )
            raise
    
    async def withdraw(self, account_id: str, amount: Decimal) -> dict:
        """
        Withdraw money from an account
        
        Business Rules:
        - Account must exist and be active
        - Account must have sufficient balance
        - Amount must be positive
        - Must not exceed daily withdrawal limit
        - Transaction is logged
        """
        # Validate amount
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        
        # Check for duplicate transaction (within 60 seconds)
        if await self.transaction_repo.check_duplicate_transaction(
            TransactionType.WITHDRAW,
            account_id,
            None,
            amount
        ):
            raise DuplicateTransactionException("Duplicate withdrawal transaction detected")
        
        # Get account with lock
        account = await self.account_repo.find_by_id_or_raise(account_id, lock=True)
        
        # Validate account status
        if not account.is_active():
            error_msg = f"Account {account_id} is blocked and cannot perform withdrawals"
            await self._log_transaction(
                TransactionType.WITHDRAW,
                amount,
                TransactionStatus.FAILED,
                source_account_id=account_id,
                error_message=error_msg
            )
            raise InvalidAccountException(error_msg)
        
        # Check sufficient balance
        if not account.has_sufficient_balance(amount):
            error_msg = f"Insufficient funds. Available: {account.balance}, Required: {amount}"
            await self._log_transaction(
                TransactionType.WITHDRAW,
                amount,
                TransactionStatus.FAILED,
                source_account_id=account_id,
                error_message=error_msg
            )
            raise InsufficientFundsException(error_msg)
        
        # Check daily withdrawal limit
        today = date.today()
        daily_total = await self.transaction_repo.get_daily_transaction_total(
            account_id,
            today,
            [TransactionType.WITHDRAW]
        )
        
        if daily_total + amount > self.DAILY_WITHDRAWAL_LIMIT:
            error_msg = f"Daily withdrawal limit exceeded. Limit: {self.DAILY_WITHDRAWAL_LIMIT}, Today's total: {daily_total}, Requested: {amount}"
            await self._log_transaction(
                TransactionType.WITHDRAW,
                amount,
                TransactionStatus.FAILED,
                source_account_id=account_id,
                error_message=error_msg
            )
            raise TransactionLimitException(error_msg)
        
        try:
            # Update balance
            new_balance = account.balance - amount
            account.balance = new_balance
            await self.session.flush()
            
            # Log successful transaction
            await self._log_transaction(
                TransactionType.WITHDRAW,
                amount,
                TransactionStatus.SUCCESS,
                source_account_id=account_id
            )
            
            return {
                "transaction_type": "WITHDRAW",
                "account_id": account_id,
                "amount": str(amount),
                "new_balance": str(new_balance),
                "status": "SUCCESS"
            }
        except Exception as e:
            # Log failed transaction
            await self._log_transaction(
                TransactionType.WITHDRAW,
                amount,
                TransactionStatus.FAILED,
                source_account_id=account_id,
                error_message=str(e)
            )
            raise
    
    async def transfer(
        self,
        source_account_id: str,
        destination_account_id: str,
        amount: Decimal
    ) -> dict:
        """
        Transfer money between accounts
        
        Business Rules:
        - Both accounts must exist and be active
        - Source account must have sufficient balance
        - Amount must be positive
        - Must not exceed daily transfer limit
        - Transaction is atomic (all-or-nothing)
        - Transaction is logged
        """
        # Validate amount
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        
        # Validate accounts are different
        if source_account_id == destination_account_id:
            raise ValueError("Source and destination accounts cannot be the same")
        
        # Check for duplicate transaction
        if await self.transaction_repo.check_duplicate_transaction(
            TransactionType.TRANSFER,
            source_account_id,
            destination_account_id,
            amount
        ):
            raise DuplicateTransactionException("Duplicate transfer transaction detected")
        
        # Get both accounts with locks (order by ID to prevent deadlock)
        account_ids = sorted([source_account_id, destination_account_id])
        source_account = await self.account_repo.find_by_id_or_raise(account_ids[0], lock=True)
        dest_account = await self.account_repo.find_by_id_or_raise(account_ids[1], lock=True)
        
        # Ensure we have the right accounts
        if source_account.account_id != source_account_id:
            source_account, dest_account = dest_account, source_account
        
        # Validate source account status
        if not source_account.is_active():
            error_msg = f"Source account {source_account_id} is blocked"
            await self._log_transaction(
                TransactionType.TRANSFER,
                amount,
                TransactionStatus.FAILED,
                source_account_id=source_account_id,
                destination_account_id=destination_account_id,
                error_message=error_msg
            )
            raise InvalidAccountException(error_msg)
        
        # Validate destination account status
        if not dest_account.is_active():
            error_msg = f"Destination account {destination_account_id} is blocked"
            await self._log_transaction(
                TransactionType.TRANSFER,
                amount,
                TransactionStatus.FAILED,
                source_account_id=source_account_id,
                destination_account_id=destination_account_id,
                error_message=error_msg
            )
            raise InvalidAccountException(error_msg)
        
        # Check sufficient balance
        if not source_account.has_sufficient_balance(amount):
            error_msg = f"Insufficient funds. Available: {source_account.balance}, Required: {amount}"
            await self._log_transaction(
                TransactionType.TRANSFER,
                amount,
                TransactionStatus.FAILED,
                source_account_id=source_account_id,
                destination_account_id=destination_account_id,
                error_message=error_msg
            )
            raise InsufficientFundsException(error_msg)
        
        # Check daily transfer limit
        today = date.today()
        daily_total = await self.transaction_repo.get_daily_transaction_total(
            source_account_id,
            today,
            [TransactionType.TRANSFER]
        )
        
        if daily_total + amount > self.DAILY_TRANSFER_LIMIT:
            error_msg = f"Daily transfer limit exceeded. Limit: {self.DAILY_TRANSFER_LIMIT}, Today's total: {daily_total}, Requested: {amount}"
            await self._log_transaction(
                TransactionType.TRANSFER,
                amount,
                TransactionStatus.FAILED,
                source_account_id=source_account_id,
                destination_account_id=destination_account_id,
                error_message=error_msg
            )
            raise TransactionLimitException(error_msg)
        
        try:
            # Atomic transfer: update both balances
            source_account.balance -= amount
            dest_account.balance += amount
            await self.session.flush()
            
            # Log successful transaction
            await self._log_transaction(
                TransactionType.TRANSFER,
                amount,
                TransactionStatus.SUCCESS,
                source_account_id=source_account_id,
                destination_account_id=destination_account_id
            )
            
            return {
                "transaction_type": "TRANSFER",
                "source_account_id": source_account_id,
                "destination_account_id": destination_account_id,
                "amount": str(amount),
                "source_new_balance": str(source_account.balance),
                "destination_new_balance": str(dest_account.balance),
                "status": "SUCCESS"
            }
        except Exception as e:
            # Log failed transaction
            await self._log_transaction(
                TransactionType.TRANSFER,
                amount,
                TransactionStatus.FAILED,
                source_account_id=source_account_id,
                destination_account_id=destination_account_id,
                error_message=str(e)
            )
            raise
    
    async def get_transaction_history(self, account_id: str, limit: int = 100) -> list:
        """Get transaction history for an account"""
        await self.account_repo.find_by_id_or_raise(account_id)  # Validate account exists
        logs = await self.transaction_repo.get_transaction_history(account_id, limit)
        return [
            {
                "transaction_id": log.transaction_id,
                "transaction_type": log.transaction_type,
                "source_account_id": log.source_account_id,
                "destination_account_id": log.destination_account_id,
                "amount": str(log.amount),
                "status": log.status,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    
    async def _log_transaction(
        self,
        transaction_type: TransactionType,
        amount: Decimal,
        status: TransactionStatus,
        source_account_id: str = None,
        destination_account_id: str = None,
        error_message: str = None
    ):
        """Helper method to log transactions"""
        await self.transaction_repo.create_log(
            transaction_type=transaction_type,
            amount=amount,
            status=status,
            source_account_id=source_account_id,
            destination_account_id=destination_account_id,
            error_message=error_message
        )

