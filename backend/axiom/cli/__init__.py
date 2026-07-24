"""CLI package — command-line interface for Axiom OS.

Access the Typer app via `get_app()` or `from axiom.cli import app`.
Import from `main` is deferred to avoid RuntimeWarning when running via
`python -m axiom.cli.main`.
"""


def get_app():
    """Return the Typer CLI app (lazy import)."""
    from axiom.cli.main import app  # noqa: deferred import
    return app


# Module-level accessor — app is resolved lazily on first access.
# When this module is loaded via `python -m axiom.cli.main`, the __init__.py
# does NOT eagerly import from main, so runpy does not warn.
#
#   from axiom.cli import get_app; typer_app = get_app()
#   from axiom.cli import app           — also works (lazy descriptor)
#

class _LazyApp:
    def __repr__(self):
        return "<lazy CLI app — resolved on first use>"

    def __getattr__(self, name):
        return getattr(get_app(), name)


app = _LazyApp()

__all__ = ["app", "get_app"]