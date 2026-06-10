"""CLI: keygen produces correctly-prefixed keys."""

from __future__ import annotations

import argparse

from synthr_gateway import cli


def test_keygen_secret(capsys) -> None:
    cli.keygen(argparse.Namespace(public=False))
    out = capsys.readouterr().out.strip()
    assert out.startswith("sk_proj_") and len(out) > 20


def test_keygen_public(capsys) -> None:
    cli.keygen(argparse.Namespace(public=True))
    assert capsys.readouterr().out.strip().startswith("pk_proj_")


def test_parser_requires_command() -> None:
    import pytest

    with pytest.raises(SystemExit):
        cli.build_parser().parse_args([])
