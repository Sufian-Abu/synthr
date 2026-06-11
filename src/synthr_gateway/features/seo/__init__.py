"""seo — content to title / description / keywords."""

from .models import SeoRequest
from .service import seo

__all__ = ["SeoRequest", "seo"]
