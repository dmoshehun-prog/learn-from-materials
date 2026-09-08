from __future__ import annotations
class ExtractionError(Exception):
    """Raised when a single file cannot be extracted (non-fatal in batch mode)."""
