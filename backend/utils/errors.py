"""
Custom Exceptions für Phase 2 Runbook.
"""
from typing import Optional


class TransientError(Exception):
    """
    Transient-Fehler (vorübergehend, retry möglich).
    Z.B. OSRM down, Timeout, 502/503/504.
    """
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class QuotaError(Exception):
    """
    Quota-Fehler (402/429).
    Retry nach Backoff.
    """
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after

