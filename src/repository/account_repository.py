"""
Account Repository
Data access layer for Account operations
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal

from src.models.account import Account, AccountStatus
from src.exceptions import InvalidAccountException


class AccountRepository:
    """
    Repository for Account operations
    
    Design Decisions:
    - Uses async/await for non-blocking database operations
    - Implements pessimistic locking for balance updates (SELECT FOR UPDATE)
    - All database operations are within transactions
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, account_id: str, account_name: str, initial_balance: Decimal) -> Account:
        """Create a new account"""
        account = Account(
            account_id=account_id,
            account_name=account_name,
            balance=initial_balance,
            status=AccountStatus.ACTIVE.value
        )
        self.session.add(account)
        await self.session.flush()
        return account
    
    async def find_by_id(self, account_id: str, lock: bool = False) -> Optional[Account]:
        """
        Find account by ID
        
        Args:
            account_id: Account identifier
            lock: If True, locks the row for update (pessimistic locking)
        """
        query = select(Account).where(Account.account_id == account_id)
        
        if lock:
            # Use SELECT FOR UPDATE for pessimistic locking
            # This prevents concurrent modifications
            query = query.with_for_update()
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def find_by_id_or_raise(self, account_id: str, lock: bool = False) -> Account:
        """Find account by ID or raise exception if not found"""
        account = await self.find_by_id(account_id, lock)
        if not account:
            raise InvalidAccountException(f"Account {account_id} not found")
        return account
    
    async def update_balance(self, account_id: str, new_balance: Decimal) -> Account:
        """
        Update account balance
        
        Note: Should be called within a transaction with locked account
        """
        account = await self.find_by_id_or_raise(account_id, lock=True)
        account.balance = new_balance
        await self.session.flush()
        return account
    
    async def block_account(self, account_id: str) -> Account:
        """Block an account"""
        account = await self.find_by_id_or_raise(account_id)
        account.status = AccountStatus.BLOCKED.value
        await self.session.flush()
        return account
    
    async def unblock_account(self, account_id: str) -> Account:
        """Unblock an account"""
        account = await self.find_by_id_or_raise(account_id)
        account.status = AccountStatus.ACTIVE.value
        await self.session.flush()
        return account
    
    async def get_all_accounts(self) -> list[Account]:
        """Get all accounts (for admin/testing purposes)"""
        result = await self.session.execute(select(Account))
        return list(result.scalars().all())

