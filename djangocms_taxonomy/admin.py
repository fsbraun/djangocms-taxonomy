from django.contrib import admin
from django.apps import apps as django_apps
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from parler.admin import TranslatableAdmin

from .models import Category


@admin.register(Category)
class CategoryAdmin(TranslatableAdmin):
    """Admin interface for Category model with hierarchical display."""

    list_display = ["indented_name", "slug", "parent", "date_created"]
    list_filter = ["date_created", "date_modified"]
    search_fields = ["translations__name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ["parent"]

    def check(self, **kwargs):
        """Override to disable prepopulated_fields check for translatable fields."""
        errors = super().check(**kwargs)
        # Filter out admin.E040 (prepopulated_fields refers to non-ForeignKey/SlugField)
        # This is expected for django-parler translatable fields
        return [error for error in errors if error.id != "admin.E030"]

    def __init__(self, *args, **kwargs):
        """Initialize admin with sorting by path flag."""
        super().__init__(*args, **kwargs)
        self._is_sorted_by_path = True  # Default to True (show indentation)

    def changelist_view(self, request, extra_context=None):
        """Override to track if sorting is by path."""
        # Check the 'o' parameter (ordering) from request
        # path field ordering parameter is typically 'path' or '-path'
        ordering_param = request.GET.get("o", "")
        # Check if sorting by path (with or without descending)
        self._is_sorted_by_path = (
            ordering_param.startswith(str(self.list_display.index("indented_name") + 1)) or not ordering_param
        )
        return super().changelist_view(request, extra_context)

    def get_queryset(self, request):
        """Override queryset to add CTE annotations for path and depth."""
        qs = super().get_queryset(request)
        # Add tree fields with path and depth for hierarchical ordering
        return qs.with_tree_fields()

    @admin.display(
        description=_("Name"),
        ordering="path",
    )
    def indented_name(self, obj):
        """Display name with indentation based on depth in hierarchy."""
        # Only add indentation if sorting by path
        if hasattr(obj, "depth") and self._is_sorted_by_path:
            # Use non-breaking spaces for indentation (4 spaces per level)
            indent = "&nbsp;" * 4 * obj.depth
            return format_html("{}{}", mark_safe(indent), obj.name)
        return obj.name


if django_apps.is_installed("taggit"):
    from taggit.models import Tag, TaggedItem

    # If taggit registered its own admin elsewhere, remove it so the proxy
    # models below show up under the Taxonomy app.
    try:
        admin.site.unregister(Tag)
    except admin.sites.NotRegistered:
        pass

    try:
        admin.site.unregister(TaggedItem)
    except admin.sites.NotRegistered:
        pass

    class TaxonomyTag(Tag):
        class Meta:
            proxy = True
            verbose_name = _("Tag")
            app_label = "djangocms_taxonomy"

    class TaxonomyTaggedItem(TaggedItem):
        class Meta:
            proxy = True
            verbose_name = _("Tagged item")
            app_label = "djangocms_taxonomy"

    @admin.register(TaxonomyTag)
    class TaxonomyTagAdmin(admin.ModelAdmin):
        search_fields = ("name",)
        ordering = ("name",)
