"""Lossless prompt compression: trims redundant whitespace before sending to a provider.

Conservative on purpose — collapses repeated spaces/tabs and blank lines and trims edges,
never changing wording. Saves tokens with zero quality loss.
"""

from __future__ import annotations

import re

_SPACES = re.compile(r"[ \t]{2,}")
_BLANK_LINES = re.compile(r"\n{3,}")


def compress(text: str) -> str:
    if not text:
        return text
    lines = (_SPACES.sub(" ", line).rstrip() for line in text.split("\n"))
    collapsed = _BLANK_LINES.sub("\n\n", "\n".join(lines))
    return collapsed.strip()
