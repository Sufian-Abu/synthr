"""Authentication and the dual-key (secret/public) access model."""

from .auth import AuthContext, authenticate, authorize_feature

__all__ = ["AuthContext", "authenticate", "authorize_feature"]
