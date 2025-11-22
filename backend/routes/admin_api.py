"""
Zentraler Admin-API-Router.
Bündelt alle Admin-Endpoints unter /api/admin/* für konsistente Struktur (AR-02).

WICHTIG: Backward Compatibility - Alte URLs bleiben funktional!
- Alt: /api/tourplan/batch-geocode ✅
- Neu: /api/admin/tourplan/batch-geocode ✅
"""
from fastapi import APIRouter, Depends
from backend.routes.auth_api import require_admin

# Zentraler Admin-Router mit globalem Prefix und Auth
admin_router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)]  # Alle Admin-Endpoints benötigen Auth
)

# Importiere alle Admin-Router (werden als Sub-Router registriert)
from backend.routes.db_management_api import router as db_management_router
from backend.routes.db_schema_api import router as db_schema_router
from backend.routes.system_rules_api import router as system_rules_router
from backend.routes.backup_api import router as backup_router
from backend.routes.upload_csv import router as upload_csv_router
from backend.routes.tour_filter_api import router as tour_filter_router

# Registriere Sub-Router
# WICHTIG: Router haben bereits eigene Prefixes (/api/tourplan, /api/db, etc.)
# Diese werden unter /api/admin zusätzlich registriert
# Beispiel: /api/tourplan/batch-geocode bleibt, zusätzlich /api/admin/tourplan/batch-geocode
admin_router.include_router(db_management_router)
admin_router.include_router(db_schema_router)
admin_router.include_router(system_rules_router)
admin_router.include_router(backup_router)
admin_router.include_router(upload_csv_router)
admin_router.include_router(tour_filter_router)

# Exportiere den zentralen Admin-Router
__all__ = ["admin_router"]

