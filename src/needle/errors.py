"""
needle.errors - Domain exceptions and error hierarchy for Yarns and Strands.
"""

from __future__ import annotations

from typing import Any

SAFE_EXCEPTIONS = (AttributeError, TypeError, ValueError, KeyError, OSError, RuntimeError, ImportError)


class NeedleError(Exception):
    """Base domain exception for Needle & Textile operations."""

    def __init__(
        self,
        message: str,
        hint: str | None = None,
        code: str = "ERR_NEEDLE",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        res: dict[str, Any] = {
            "status": "error",
            "code": self.code,
            "message": self.message,
        }
        if self.hint:
            res["hint"] = self.hint
        if self.details:
            res["details"] = self.details
        return res

    def __str__(self) -> str:
        base = f"[{self.code}] {self.message}"
        if self.hint:
            base += f" (Hint: {self.hint})"
        return base


class StrandError(NeedleError):
    """Base error for strand execution failure."""


class StrandOperationalError(StrandError):
    """Raised when a strand execution fails during underlying tool execution."""

    def __init__(self, strand_name: str, reason: str, original_error: Exception | None = None):
        super().__init__(
            message=reason,
            hint="Inspect operational details; tool execution failed.",
            code="ERR_STRAND_OPERATIONAL",
            details={"strand": strand_name, "original_error": str(original_error) if original_error else None},
        )


class StrandNotFoundError(StrandError):
    """Raised when a requested strand is not registered or active."""

    def __init__(self, strand_name: str, available_strands: list[str] | None = None):
        top_matches = sorted(available_strands[:5]) if available_strands else []
        hint_msg = (
            f"Did you mean one of: {', '.join(top_matches)}?"
            if top_matches
            else "Inspect available strands registered on this yarn."
        )
        super().__init__(
            message=f"Strand '{strand_name}' not found.",
            hint=hint_msg,
            code="ERR_STRAND_NOT_FOUND",
            details={"strand": strand_name},
        )


class YarnNotFoundError(NeedleError):
    """Raised when a requested yarn is not registered or active."""

    def __init__(self, yarn_name: str, available_yarns: list[str] | None = None):
        top_matches = sorted(available_yarns[:5]) if available_yarns else []
        hint_msg = f"Did you mean one of: {', '.join(top_matches)}?" if top_matches else "Inspect available yarns."
        super().__init__(
            message=f"Yarn '{yarn_name}' not found.",
            hint=hint_msg,
            code="ERR_YARN_NOT_FOUND",
            details={"yarn": yarn_name},
        )


class StrandCollisionError(NeedleError):
    """Raised when two Yarns register identical strand names without a capability contract."""

    def __init__(self, strand_name: str, existing_yarn: str, new_yarn: str):
        msg = (
            f"Strand collision detected: '{strand_name}' registered by both "
            f"'{existing_yarn}' and '{new_yarn}' without a capability contract."
        )
        super().__init__(
            message=msg,
            hint="Declare explicit 'capability' on both strands to allow layer-based overrides.",
            code="ERR_STRAND_COLLISION",
            details={"strand": strand_name, "existing_yarn": existing_yarn, "new_yarn": new_yarn},
        )


__all__ = [
    "SAFE_EXCEPTIONS",
    "NeedleError",
    "StrandCollisionError",
    "StrandError",
    "StrandNotFoundError",
    "StrandOperationalError",
    "YarnNotFoundError",
]
