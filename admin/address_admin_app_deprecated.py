"""Deprecated entry point kept for backward compatibility.

The new admin surface lives in ``admin.address_admin_app_fixed``.
Importing this module raises an informative error message so that
legacy scripts are guided to the updated implementation without
causing silent failures.
"""

raise ImportError(
    "admin.address_admin_app_deprecated wurde entfernt. "
    "Bitte admin.address_admin_app_fixed verwenden."
)

