"""Admin mixins for category integration with Django models."""

from typing import Any

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.forms.widgets import CheckboxSelectMultiple
from django.utils.translation import gettext_lazy as _

from .models import Category, CategoryRelation


class CategoryFormMixin(forms.ModelForm):
    """Form mixin that adds category selection field to any model form."""

    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all().with_tree_fields(),
        widget=CheckboxSelectMultiple,
        required=False,
        label=_("Categories"),
        help_text=_("Select categories for this object"),
    )

    class Meta:
        fields = "__all__"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize form and populate categories field with existing relations."""
        super().__init__(*args, **kwargs)

        # If editing an existing object, populate categories from relations
        if self.instance and self.instance.pk:
            related_categories = CategoryRelation.objects.filter(
                content_type=ContentType.objects.get_for_model(self.instance),
                object_id=self.instance.pk,
            ).values_list("category_id", flat=True)
            self.fields["categories"].initial = related_categories

    def save(self, commit: bool = True) -> Model:
        """Save the form and update category relations."""
        instance = super().save(commit=commit)

        if commit and self.instance.pk:
            # Get content type for this model
            content_type = ContentType.objects.get_for_model(instance)

            # Clear existing relations
            CategoryRelation.objects.filter(
                content_type=content_type,
                object_id=instance.pk,
            ).delete()

            # Create new relations for selected categories
            categories = self.cleaned_data.get("categories", [])
            for order, category in enumerate(categories):
                CategoryRelation.objects.create(
                    category=category,
                    content_type=content_type,
                    object_id=instance.pk,
                    order=order,
                )

        return instance


class CategoryAdminMixin:
    """Admin mixin that provides category selection for any model admin."""

    form: type[forms.ModelForm] = CategoryFormMixin

    def get_form(self, request: Any, obj: Model | None = None, **kwargs: Any) -> type[forms.ModelForm]:
        """Get the form class with category support."""
        form_class = super().get_form(request, obj, **kwargs)  # type: ignore

        # Create a new form class that combines the original form with category support
        class CombinedForm(CategoryFormMixin, form_class):  # type: ignore
            pass

        return CombinedForm

    def get_readonly_fields(self, request: Any, obj: Model | None = None) -> list[str]:
        """Get readonly fields, preserving parent class readonly fields."""
        readonly = list(super().get_readonly_fields(request, obj))  # type: ignore
        return readonly

    fieldsets: tuple[Any, ...] | None = None

    def get_fieldsets(self, request: Any, obj: Model | None = None):
        """Add categories fieldset to the form."""
        fieldsets = super().get_fieldsets(request, obj)  # type: ignore

        if not fieldsets:
            return fieldsets

        # Convert to mutable list of lists
        fieldsets_list = [list(fs) for fs in fieldsets]

        # Add categories fieldset at the end
        fieldsets_list.append(
            [
                _("Taxonomy"),
                {
                    "fields": ("categories",),
                    "classes": ("collapse",),
                },
            ]
        )

        return fieldsets_list
