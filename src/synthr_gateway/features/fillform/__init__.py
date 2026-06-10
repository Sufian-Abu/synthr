"""fillForm — schema-constrained form autofill (SPEC.md §6.1)."""

from .models import FillFormRequest, FormField
from .service import fill_form

__all__ = ["FillFormRequest", "FormField", "fill_form"]
