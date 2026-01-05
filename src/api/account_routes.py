"""
Account API Routes
REST endpoints for account management
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.services.account_service import AccountService
from src.api.schemas import (
    CreateAccountRequest,
    AccountResponse,
    ErrorResponse
)
from src.exceptions import InvalidAccountException

router = APIRouter(prefix="/api/accounts", tags=["Accounts"])


@router.post(
    "",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        409: {"model": ErrorResponse, "description": "Account already exists"}
    },
    summary="Create a new account",
    description="Creates a new bank account with the specified account ID, name, and initial balance"
)
async def create_account(
    request: CreateAccountRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new account
    
    - **account_id**: Unique identifier for the account
    - **account_name**: Name of the account holder
    - **initial_balance**: Initial balance (must be non-negative)
    """
    try:
        service = AccountService(db)
        account = await service.create_account(
            account_id=request.account_id,
            account_name=request.account_name,
            initial_balance=request.initial_balance
        )
        return AccountResponse(
            account_id=account.account_id,
            account_name=account.account_name,
            balance=str(account.balance),
            status=account.status,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
    except InvalidAccountException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{account_id}",
    response_model=AccountResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Account not found"}
    },
    summary="Get account by ID",
    description="Retrieves account information by account ID"
)
async def get_account(
    account_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get account details by account ID"""
    try:
        service = AccountService(db)
        account = await service.get_account(account_id)
        return AccountResponse(
            account_id=account.account_id,
            account_name=account.account_name,
            balance=str(account.balance),
            status=account.status,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
    except InvalidAccountException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "",
    response_model=List[AccountResponse],
    summary="Get all accounts",
    description="Retrieves all accounts in the system (for admin/testing purposes)"
)
async def get_all_accounts(db: AsyncSession = Depends(get_db)):
    """Get all accounts"""
    service = AccountService(db)
    accounts = await service.get_all_accounts()
    return [
        AccountResponse(
            account_id=acc.account_id,
            account_name=acc.account_name,
            balance=str(acc.balance),
            status=acc.status,
            created_at=acc.created_at,
            updated_at=acc.updated_at
        )
        for acc in accounts
    ]


@router.post(
    "/{account_id}/block",
    response_model=AccountResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Account not found"},
        400: {"model": ErrorResponse, "description": "Account already blocked"}
    },
    summary="Block an account",
    description="Blocks an account, preventing all transactions"
)
async def block_account(
    account_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Block an account"""
    try:
        service = AccountService(db)
        account = await service.block_account(account_id)
        return AccountResponse(
            account_id=account.account_id,
            account_name=account.account_name,
            balance=str(account.balance),
            status=account.status,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
    except InvalidAccountException as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )


@router.post(
    "/{account_id}/unblock",
    response_model=AccountResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Account not found"},
        400: {"model": ErrorResponse, "description": "Account already active"}
    },
    summary="Unblock an account",
    description="Unblocks an account, allowing transactions"
)
async def unblock_account(
    account_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Unblock an account"""
    try:
        service = AccountService(db)
        account = await service.unblock_account(account_id)
        return AccountResponse(
            account_id=account.account_id,
            account_name=account.account_name,
            balance=str(account.balance),
            status=account.status,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
    except InvalidAccountException as e:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )

