"""Token optimizer: lossless whitespace compression."""

from __future__ import annotations

from synthr_gateway.optimizer import compress


def test_collapses_spaces_and_blank_lines() -> None:
    out = compress("hello    world\n\n\n\nfoo   \n   ")
    assert out == "hello world\n\nfoo"


def test_empty_is_safe() -> None:
    assert compress("") == ""
