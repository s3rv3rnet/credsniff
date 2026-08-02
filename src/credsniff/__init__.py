"""credsniff — a fast, local, zero-cloud secret scanner.

Scans a codebase for likely secrets (API keys, tokens, private keys) using regex
rules and entropy heuristics. Runs entirely locally: this package never makes a
network call, and never prints a secret in full.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]


def main() -> None:
    """Print a placeholder message.

    Temporary entry point, replaced in Step 9 by the real Typer application
    (``credsniff.cli:app``).
    """
    print(f"credsniff {__version__} — not implemented yet")
