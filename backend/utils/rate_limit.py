"""
Rate Limiter (Token-Bucket) für Phase 2 Runbook.
Optional, klein & lokal.
"""
import os
import time
import logging

logger = logging.getLogger(__name__)


class TokenBucket:
    """
    Token-Bucket für Rate-Limiting.
    
    Standard: 10 Requests/Sekunde, Burst: 10
    """
    
    def __init__(self, rate_per_sec: float = 10.0, burst: int = 10):
        """
        Initialisiert Token-Bucket.
        
        Args:
            rate_per_sec: Rate in Requests pro Sekunde (Standard: 10)
            burst: Maximale Burst-Größe (Standard: 10)
        """
        self.rate = rate_per_sec
        self.burst = burst
        self.tokens = float(burst)
        self.ts = time.time()
    
    def allow(self) -> bool:
        """
        Prüft ob Request erlaubt ist.
        
        Returns:
            True wenn Request erlaubt, False wenn limitiert
        """
        now = time.time()
        
        # Füge Tokens basierend auf vergangener Zeit hinzu
        elapsed = now - self.ts
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.ts = now
        
        # Verbrauche Token wenn verfügbar
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        
        return False
    
    def wait_time(self) -> float:
        """
        Berechnet Wartezeit bis nächster Request erlaubt ist.
        
        Returns:
            Wartezeit in Sekunden
        """
        if self.tokens >= 1.0:
            return 0.0
        
        # Berechne wie lange wir warten müssen
        needed = 1.0 - self.tokens
        return needed / self.rate


# Globale Instanz für OSRM (konfigurierbar über ENV)
_rate_limit_enabled = os.getenv("OSRM_RATE_LIMIT_ENABLED", "false").lower() == "true"
_rate_limit_rate = float(os.getenv("OSRM_RATE_LIMIT_RATE", "10.0"))
_rate_limit_burst = int(os.getenv("OSRM_RATE_LIMIT_BURST", "10"))

rate_limiter_osrm = TokenBucket(
    rate_per_sec=_rate_limit_rate,
    burst=_rate_limit_burst
) if _rate_limit_enabled else None

