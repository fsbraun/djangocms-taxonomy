"""Model and admin mixins for category integration with Django models."""

from typing import TYPE_CHECKING, Any, Iterable

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Model, QuerySet
from django.utils.translation import gettext_lazy as _

from .models import Category, CategoryRelation

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager


class CategoryManager:
    """
    M2M-like manager for categories that provides add/remove/set/clear methods.

    This wraps the GenericRelation to provide a more intuitive API for managing
    categories on model instances.
    """

    def __init__(self, instance: Model):
        self.instance = instance
        self._content_type: ContentType | None = None

    @property
    def content_type(self) -> ContentType:
        if self._content_type is None:
            self._content_type = ContentType.objects.get_for_model(self.instance)
        return self._content_type

    def all(self) -> QuerySet[Category]:
        """Return all categories for this instance."""
        if not self.instance.pk:
            return Category.objects.none()
        category_ids = CategoryRelation.objects.filter(
            content_type=self.content_type,
            object_id=self.instance.pk,
        ).values_list("category_id", flat=True)
        return Category.objects.filter(pk__in=category_ids)

    def add(self, *categories: Category) -> None:
        """Add one or more categories to this instance."""
        if not self.instance.pk:
            raise ValueError("Cannot add categories to unsaved instance")
        existing = set(
            CategoryRelation.objects.filter(
                content_type=self.content_type,
                object_id=self.instance.pk,
                category__in=categories,
            ).values_list("category_id", flat=True)
        )
        max_order = (
            CategoryRelation.objects.filter(
                content_type=self.content_type,
                object_id=self.instance.pk,
            ).aggregate(max_order=models.Max("order"))["max_order"]
            or 0
        )
        new_relations = [
            CategoryRelation(
                category=cat,
                content_type=self.content_type,
                object_id=self.instance.pk,
                order=max_order + i + 1,
            )
            for i, cat in enumerate(categories)
            if cat.pk not in existing
        ]
        if new_relations:
            CategoryRelation.objects.bulk_create(new_relations)

    def remove(self, *categories: Category) -> None:
        """Remove one or more categories from this instance."""
        if not self.instance.pk:
            return
        CategoryRelation.objects.filter(
            content_type=self.content_type,
            object_id=self.instance.pk,
            category__in=categories,
        ).delete()

    def clear(self) -> None:
        """Remove all categories from this instance."""
        if not self.instance.pk:
            return
        CategoryRelation.objects.filter(
            content_type=self.content_type,
            object_id=self.instance.pk,
        ).delete()

    def set(self, categories: Iterable[Category]) -> None:
        """Replace all categories with the given ones."""
        self.clear()
        self.add(*categories)

    def __iter__(self):
        return iter(self.all())

    def __bool__(self):
        return self.all().exists()

    def count(self) -> int:
        return self.all().count()

    def __getattr__(self, name: str):
        # Provide qs methods
        return getattr(self.all(), name)


class CategoryDescriptor:
    """Descriptor that returns a CategoryManager for each instance."""

    def __get__(self, instance: Model | None, owner: type) -> "CategoryManager | RelatedManager[Category]":
        if instance is None:
            raise AttributeError("Cannot access categories from class, only from instances")
        return CategoryManager(instance)


class CategoryMixin(models.Model):
    """
    Model mixin that adds M2M-like category management.

    Provides a `categories` attribute with add/remove/set/clear methods.

    Usage:
        class MyModel(CategoryMixin, models.Model):
            title = models.CharField(max_length=255)

        obj = MyModel.objects.get(pk=1)
        obj.categories.add(category1, category2)
        obj.categories.remove(category1)
        obj.categories.set([category3])
        obj.categories.clear()
        for cat in obj.categories.all():
            print(cat.name)
    """

    class Meta:
        abstract = True

    categories = CategoryDescriptor()


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

    class CategoryRelationListFilter(admin.SimpleListFilter):
        title = _("Category")
        parameter_name = "category"
        template = "admin/djangocms_taxonomy/category_autocomplete_filter.html"

        def __init__(self, request: Any, params: Any, model: type[Model], model_admin: admin.ModelAdmin) -> None:
            super().__init__(request, params, model, model_admin)
            self._selected_category: Category | None = None
            value = self.value()
            if value and value != "__none__" and str(value).isdigit():
                self._selected_category = Category.objects.filter(pk=int(value)).first()

        @property
        def selected_category(self) -> Category | None:
            return self._selected_category

        @property
        def selected_category_label(self) -> str:
            if not self._selected_category:
                return ""
            return (
                self._selected_category.safe_translation_getter("name", any_language=True)
                or getattr(self._selected_category, "slug", None)
                or str(self._selected_category.pk)
            )

        def lookups(self, request: Any, model_admin: admin.ModelAdmin):
            # Kept for API compatibility; the custom template renders an
            # autocomplete widget instead of a long list.
            return [("__none__", str(_("No category")))]

        def queryset(self, request: Any, queryset: QuerySet):
            value = self.value()
            if not value:
                return queryset

            content_type = ContentType.objects.get_for_model(queryset.model)
            relations = CategoryRelation.objects.filter(content_type=content_type)

            if value == "__none__":
                related_object_ids = relations.values_list("object_id", flat=True)
                return queryset.exclude(pk__in=related_object_ids)

            related_object_ids = relations.filter(category_id=value).values_list("object_id", flat=True)
            return queryset.filter(pk__in=related_object_ids)

    def get_list_filter(self, request: Any):
        list_filter = list(super().get_list_filter(request))  # type: ignore
        if self.CategoryRelationListFilter not in list_filter:
            list_filter.append(self.CategoryRelationListFilter)
        return list_filter

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

    def save_related(self, request: Any, form: forms.ModelForm, formsets: Any, change: bool) -> None:
        """Save related objects including category relations."""
        # Call parent save_related
        super().save_related(request, form, formsets, change)  # type: ignore

        # Save category relations from the form
        if form.instance.pk and hasattr(form, "cleaned_data"):
            content_type = ContentType.objects.get_for_model(form.instance)

            # Clear existing relations
            CategoryRelation.objects.filter(
                content_type=content_type,
                object_id=form.instance.pk,
            ).delete()

            # Create new relations for selected categories
            categories = form.cleaned_data.get("categories", [])
            relations = [
                CategoryRelation(
                    category=category,
                    content_type=content_type,
                    object_id=form.instance.pk,
                    order=order,
                )
                for order, category in enumerate(categories)
            ]
            if relations:
                CategoryRelation.objects.bulk_create(relations)
