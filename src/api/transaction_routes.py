"""
Transaction API Routes
REST endpoints for transaction operations (deposit, withdraw, transfer)
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.services.transaction_service import TransactionService
from src.api.schemas import (
    DepositRequest,
    WithdrawRequest,
    TransferRequest,
    TransactionResponse,
    TransactionHistoryResponse,
    ErrorResponse
)
from src.exceptions import (
    InsufficientFundsException,
    InvalidAccountException,
    TransactionLimitException,
    DuplicateTransactionException
)

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.post(
    "/deposit",
    response_model=TransactionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Account not found"},
        403: {"model": ErrorResponse, "description": "Account is blocked"}
    },
    summary="Deposit money",
    description="Deposits money into an account. Account must be active."
)
async def deposit(
    request: DepositRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Deposit money into an account
    
    - **account_id**: Account to deposit into
    - **amount**: Amount to deposit (must be positive)
    """
    try:
        service = TransactionService(db)
        result = await service.deposit(request.account_id, request.amount)
        return TransactionResponse(**result)
    except InvalidAccountException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/withdraw",
    response_model=TransactionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request or insufficient funds"},
        404: {"model": ErrorResponse, "description": "Account not found"},
        403: {"model": ErrorResponse, "description": "Account is blocked"},
        402: {"model": ErrorResponse, "description": "Insufficient funds"},
        429: {"model": ErrorResponse, "description": "Daily transaction limit exceeded"},
        409: {"model": ErrorResponse, "description": "Duplicate transaction"}
    },
    summary="Withdraw money",
    description="Withdraws money from an account. Requires sufficient balance and must not exceed daily limits."
)
async def withdraw(
    request: WithdrawRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Withdraw money from an account
    
    - **account_id**: Account to withdraw from
    - **amount**: Amount to withdraw (must be positive)
    
    Business Rules:
    - Account must have sufficient balance
    - Must not exceed daily withdrawal limit ($10,000)
    - Account must be active
    """
    try:
        service = TransactionService(db)
        result = await service.withdraw(request.account_id, request.amount)
        return TransactionResponse(**result)
    except InsufficientFundsException as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(e)
        )
    except InvalidAccountException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except TransactionLimitException as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except DuplicateTransactionException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/transfer",
    response_model=TransactionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request or insufficient funds"},
        404: {"model": ErrorResponse, "description": "Account not found"},
        403: {"model": ErrorResponse, "description": "Account is blocked"},
        402: {"model": ErrorResponse, "description": "Insufficient funds"},
        429: {"model": ErrorResponse, "description": "Daily transaction limit exceeded"},
        409: {"model": ErrorResponse, "description": "Duplicate transaction"}
    },
    summary="Transfer money",
    description="Transfers money between two accounts. Atomic operation with ACID guarantees."
)
async def transfer(
    request: TransferRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Transfer money between accounts
    
    - **source_account_id**: Account to transfer from
    - **destination_account_id**: Account to transfer to
    - **amount**: Amount to transfer (must be positive)
    
    Business Rules:
    - Source account must have sufficient balance
    - Must not exceed daily transfer limit ($50,000)
    - Both accounts must be active
    - Transaction is atomic (all-or-nothing)
    """
    try:
        service = TransactionService(db)
        result = await service.transfer(
            request.source_account_id,
            request.destination_account_id,
            request.amount
        )
        return TransactionResponse(**result)
    except InsufficientFundsException as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(e)
        )
    except InvalidAccountException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND if "not found" in str(e).lower() else status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except TransactionLimitException as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e)
        )
    except DuplicateTransactionException as e:
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
    "/history/{account_id}",
    response_model=List[TransactionHistoryResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Account not found"}
    },
    summary="Get transaction history",
    description="Retrieves transaction history for an account"
)
async def get_transaction_history(
    account_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of transactions to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get transaction history for an account
    
    - **account_id**: Account ID to get history for
    - **limit**: Maximum number of transactions to return (1-1000, default: 100)
    """
    try:
        service = TransactionService(db)
        history = await service.get_transaction_history(account_id, limit)
        return [TransactionHistoryResponse(**item) for item in history]
    except InvalidAccountException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

