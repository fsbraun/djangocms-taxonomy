"""Model and admin mixins for category integration with Django models."""

from typing import Any

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Model, QuerySet
from django.utils.translation import gettext_lazy as _

from .models import Category, CategoryRelation


class CategoryMixin(models.Model):
    """
    Model mixin that adds a reverse relation to categories.

    Provides a `categories` property that returns all categories
    associated with this model instance through CategoryRelation.

    Usage:
        class MyModel(CategoryMixin, models.Model):
            title = models.CharField(max_length=255)

        # Access categories
        obj = MyModel.objects.get(pk=1)
        categories = obj.categories.all()
    """

    class Meta:
        abstract = True

    @property
    def categories(self) -> QuerySet[Category]:
        """
        Get all categories associated with this object.

        Returns:
            QuerySet of Category objects related to this instance.
        """
        if not self.pk:
            return Category.objects.none()

        content_type = ContentType.objects.get_for_model(self.__class__)
        category_ids = CategoryRelation.objects.filter(
            content_type=content_type,
            object_id=self.pk,
        ).values_list("category_id", flat=True)

        return Category.objects.filter(pk__in=category_ids)


class CategoryFormMixin(forms.BaseModelForm):
    """Form mixin that adds category selection field to any model form."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize form and populate categories field with existing relations."""
        super().__init__(*args, **kwargs)

        # Add categories field lazily to avoid app registry issues
        if "categories" not in self.fields:
            self.fields["categories"] = forms.ModelMultipleChoiceField(
                queryset=Category.objects.all().with_tree_fields(),
                widget=FilteredSelectMultiple(
                    verbose_name=_("categories"),
                    is_stacked=False,
                ),
                required=False,
                label=_("Categories"),
                help_text=_("Select categories for this object"),
            )

        # If editing an existing object, populate categories from relations
        if self.instance and self.instance.pk:
            # Use the categories property if available (from CategoryMixin)
            if hasattr(self.instance, "categories") and hasattr(self.instance.categories, "all"):
                self.fields["categories"].initial = list(self.instance.categories.all())
            else:
                # Fallback to direct query if CategoryMixin is not used
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
    """
    Admin mixin that provides category selection for any model admin.

    Works seamlessly with models that use CategoryMixin, but can also
    be used with any Django model to manage CategoryRelation objects.

    Usage:
        @admin.register(MyModel)
        class MyModelAdmin(CategoryAdminMixin, admin.ModelAdmin):
            list_display = ('title',)
    """

    def get_form(self, request: Any, obj: Model | None = None, **kwargs: Any) -> type[forms.ModelForm]:
        """Get the form class with category support."""
        # Remove 'categories' from fields list to prevent validation error
        # It will be added back by CategoryFormMixin
        if "fields" not in kwargs:
            # Get the default fields but exclude 'categories' (it's in the fieldset)
            default_fields = super().get_fields(request, obj)  # type: ignore
            kwargs["fields"] = [f for f in default_fields if f != "categories"]
        elif kwargs.get("fields"):
            fields = [f for f in kwargs["fields"] if f != "categories"]
            kwargs["fields"] = fields if fields else None

        form_class = super().get_form(request, obj, **kwargs)  # type: ignore

        # Create new form class that combines CategoryFormMixin with the base form
        # Preserve the Meta class from the original form
        class CombinedForm(CategoryFormMixin, form_class):  # type: ignore
            pass

        return CombinedForm

    def get_fieldsets(self, request: Any, obj: Model | None = None):
        """Add categories fieldset to the form, collapsed by default."""
        fieldsets = super().get_fieldsets(request, obj)  # type: ignore

        if not fieldsets:
            return fieldsets

        # Convert to mutable list
        fieldsets_list = list(fieldsets)

        # Add categories fieldset at the end, collapsed by default
        fieldsets_list.append(
            (
                _("Categories"),
                {
                    "fields": ("categories",),
                    "classes": ("collapse",),
                },
            )
        )

        return fieldsets_list

    def get_readonly_fields(self, request: Any, obj: Model | None = None) -> list[str]:
        """Get readonly fields, preserving parent class readonly fields."""
        readonly = list(super().get_readonly_fields(request, obj))  # type: ignore
        return readonly
