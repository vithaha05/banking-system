"""
Custom Exceptions for Banking System
"""


class BankingException(Exception):
    """Base exception for all banking-related errors"""
    pass


class InsufficientFundsException(BankingException):
    """Thrown when an account does not have sufficient balance for a transaction"""
    pass


class InvalidAccountException(BankingException):
    """Thrown when an account is invalid, not found, or blocked"""
    pass


class TransactionLimitException(BankingException):
    """Thrown when a transaction exceeds daily limits"""
    pass


class DuplicateTransactionException(BankingException):
    """Thrown when a duplicate transaction is detected"""
    pass

