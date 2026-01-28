"""Django CMS Taxonomy: A flexible taxonomy system for django CMS."""

__version__ = "1.0.0"

__all__ = [
    "CategoryAdminMixin",
    "CategoryFormMixin",
]


def __getattr__(name: str):
    """Lazily import admin mixins to avoid app registry issues."""
    if name == "CategoryAdminMixin":
        from .admin_mixins import CategoryAdminMixin

        return CategoryAdminMixin
    elif name == "CategoryFormMixin":
        from .admin_mixins import CategoryFormMixin

        return CategoryFormMixin
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
