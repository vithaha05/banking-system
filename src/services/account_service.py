"""
Account Service
Business logic layer for Account operations
"""
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.account import Account, AccountStatus
from src.repository.account_repository import AccountRepository
from src.exceptions import InvalidAccountException


class AccountService:
    """
    Service for Account business logic
    
    Design Decisions:
    - Encapsulates business rules and validation
    - Coordinates between repositories
    - All operations are transactional
    """
    
    def __init__(self, session: AsyncSession):
        self.account_repo = AccountRepository(session)
    
    async def create_account(
        self,
        account_id: str,
        account_name: str,
        initial_balance: Decimal
    ) -> Account:
        """
        Create a new account
        
        Business Rules:
        - Account ID must be unique
        - Initial balance must be non-negative
        """
        # Check if account already exists
        existing = await self.account_repo.find_by_id(account_id)
        if existing:
            raise InvalidAccountException(f"Account {account_id} already exists")
        
        # Validate initial balance
        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative")
        
        return await self.account_repo.create(account_id, account_name, initial_balance)
    
    async def get_account(self, account_id: str) -> Account:
        """Get account by ID"""
        return await self.account_repo.find_by_id_or_raise(account_id)
    
    async def get_all_accounts(self) -> list[Account]:
        """Get all accounts"""
        return await self.account_repo.get_all_accounts()
    
    async def block_account(self, account_id: str) -> Account:
        """Block an account (prevent transactions)"""
        account = await self.account_repo.find_by_id_or_raise(account_id)
        if account.status == AccountStatus.BLOCKED.value:
            raise InvalidAccountException(f"Account {account_id} is already blocked")
        return await self.account_repo.block_account(account_id)
    
    async def unblock_account(self, account_id: str) -> Account:
        """Unblock an account (allow transactions)"""
        account = await self.account_repo.find_by_id_or_raise(account_id)
        if account.status == AccountStatus.ACTIVE.value:
            raise InvalidAccountException(f"Account {account_id} is already active")
        return await self.account_repo.unblock_account(account_id)

