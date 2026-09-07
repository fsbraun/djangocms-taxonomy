# Customize the Admin Interface

Extend and customize the Django admin for your categories.

## Custom CategoryAdminMixin

Create your own admin mixin extending `CategoryAdminMixin`:

```python
from django.contrib import admin
from djangocms_taxonomy import CategoryAdminMixin
from .models import BlogPost


class CustomCategoryAdminMixin(CategoryAdminMixin):
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        # Customize fieldsets further
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        readonly = super().get_readonly_fields(request, obj)
        # Add custom readonly fields
        if obj:  # Only for editing
            readonly.append("created_at")
        return readonly


@admin.register(BlogPost)
class BlogPostAdmin(CustomCategoryAdminMixin, admin.ModelAdmin):
    list_display = ("title", "author", "status")
```

## Display Categories in List View

```python
from django.contrib import admin
from djangocms_taxonomy import CategoryAdminMixin
from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(CategoryAdminMixin, admin.ModelAdmin):
    list_display = ("title", "author", "category_list")

    def category_list(self, obj):
        """Display categories as comma-separated list."""
        categories = obj.categories.all()
        return ", ".join([cat.name for cat in categories])

    category_list.short_description = "Categories"
    category_list.admin_order_field = None  # Can't order by computed field
```

## Filter by Category in List View

```python
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from djangocms_taxonomy import CategoryAdminMixin
from djangocms_taxonomy.models import CategoryRelation
from .models import BlogPost


class CategoryFilter(admin.SimpleListFilter):
    title = "Category"
    parameter_name = "category"

    def lookups(self, request, model_admin):
        categories = Category.objects.all()
        return [(cat.id, cat.name) for cat in categories]

    def queryset(self, request, queryset):
        if self.value():
            category_id = self.value()
            ct = ContentType.objects.get_for_model(BlogPost)
            post_ids = CategoryRelation.objects.filter(category_id=category_id, content_type=ct).values_list(
                "object_id", flat=True
            )
            return queryset.filter(id__in=post_ids)
        return queryset


@admin.register(BlogPost)
class BlogPostAdmin(CategoryAdminMixin, admin.ModelAdmin):
    list_display = ("title", "author", "status")
    list_filter = (CategoryFilter, "status", "created_at")
```

## Custom Category Widget

Create a custom widget for category selection:

```python
from django.forms.widgets import CheckboxSelectMultiple
from django.contrib import admin
from djangocms_taxonomy import CategoryAdminMixin, CategoryFormMixin
from .models import BlogPost


class HierarchicalCategoryWidget(CheckboxSelectMultiple):
    """Display categories with hierarchy."""

    def render(self, name, value, attrs=None, renderer=None):
        # Custom rendering logic
        return super().render(name, value, attrs, renderer)


class CustomCategoryFormMixin(CategoryFormMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use custom widget
        if "categories" in self.fields:
            self.fields["categories"].widget = HierarchicalCategoryWidget()


class CustomCategoryAdminMixin(CategoryAdminMixin):
    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)

        # Override with custom form mixin
        class CombinedForm(CustomCategoryFormMixin, form_class):
            pass

        return CombinedForm


@admin.register(BlogPost)
class BlogPostAdmin(CustomCategoryAdminMixin, admin.ModelAdmin):
    pass
```

## Inline Categories

If you want to manage categories as inlines (not recommended, but possible):

```python
from django.contrib import admin
from djangocms_taxonomy.models import CategoryRelation


class CategoryInline(admin.TabularInline):
    model = CategoryRelation
    extra = 1
    raw_id_fields = ("category",)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    inlines = [CategoryInline]
    # Note: You may need to hide the categories field
    # to avoid duplication with the mixin
```

## Restrict Categories by User

Create a custom mixin that restricts category choices based on permissions:

```python
from django.contrib import admin
from djangocms_taxonomy import CategoryAdminMixin
from djangocms_taxonomy.models import Category
from .models import BlogPost


class RestrictedCategoryAdminMixin(CategoryAdminMixin):
    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)

        class RestrictedForm(form_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                # Restrict categories based on user permissions
                if "categories" in self.fields:
                    if request.user.is_superuser:
                        queryset = Category.objects.all()
                    else:
                        # Only show categories in certain parent categories
                        queryset = Category.objects.filter(
                            parent__in=[1, 2, 3]  # Specific parent IDs
                        )

                    self.fields["categories"].queryset = queryset

        return RestrictedForm


@admin.register(BlogPost)
class BlogPostAdmin(RestrictedCategoryAdminMixin, admin.ModelAdmin):
    pass
```
