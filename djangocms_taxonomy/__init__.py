"""Django CMS Taxonomy: A flexible taxonomy system for django CMS."""

__version__ = "1.0.0"

__all__ = [
    "CategoryMixin",
    "CategoryAdminMixin",
    "CategoryFormMixin",
]


def __getattr__(name: str):
    """Lazily import mixins to avoid app registry issues."""
    if name == "CategoryMixin":
        from .mixins import CategoryMixin

        return CategoryMixin
    elif name == "CategoryAdminMixin":
        from .mixins import CategoryAdminMixin

        return CategoryAdminMixin
    elif name == "CategoryFormMixin":
        from .mixins import CategoryFormMixin

        return CategoryFormMixin
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
