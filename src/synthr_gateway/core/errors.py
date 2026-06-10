"""Stable error model. Codes match SPEC.md §4 and are part of the public contract."""

from __future__ import annotations


class SynthrError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        http_status: int = 400,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.retry_after = retry_after


def invalid_key() -> SynthrError:
    return SynthrError("invalid_key", "Invalid or unknown project key.", 401)


def origin_not_allowed(origin: str | None) -> SynthrError:
    return SynthrError("origin_not_allowed", f"Origin {origin!r} is not allowed for this key.", 403)


def feature_not_allowed(feature: str) -> SynthrError:
    return SynthrError("feature_not_allowed", f"Feature {feature!r} is not allowed for this key type.", 403)


def invalid_input(message: str) -> SynthrError:
    return SynthrError("invalid_input", message, 422)


def guardrail_blocked(message: str) -> SynthrError:
    return SynthrError("guardrail_blocked", message, 400)


def rate_limited(retry_after: int) -> SynthrError:
    return SynthrError("rate_limited", "Rate limit exceeded.", 429, retry_after=retry_after)


def provider_error(message: str) -> SynthrError:
    return SynthrError("provider_error", message, 502)


def internal_error(message: str) -> SynthrError:
    return SynthrError("internal_error", message, 500)
