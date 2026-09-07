# Admin Configuration

Configure the Django admin to manage categories for your models.

## Basic Admin Setup

Use `CategoryAdminMixin` to add category management to your model admin:

```python
from django.contrib import admin
from djangocms_taxonomy import CategoryAdminMixin
from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(CategoryAdminMixin, admin.ModelAdmin):
    list_display = ("title", "created_at")
    search_fields = ("title", "content")
```

## What the Mixin Provides

`CategoryAdminMixin` automatically:

- **Adds a "Categories" fieldset** (collapsed by default for cleaner UI)
- **Provides FilteredSelectMultiple widget** for easy category selection with search
- **Manages CategoryRelation objects** on save (create, update, delete)
- **Populates initial categories** when editing existing objects
- **Uses bulk_create** for efficient batch category relation creation

## Customizing the Fieldsets

You can override `get_fieldsets()` to customize the category fieldset position or appearance:

```python
@admin.register(BlogPost)
class BlogPostAdmin(CategoryAdminMixin, admin.ModelAdmin):
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        # Customize fieldsets here if needed
        return fieldsets
```

## Combining with Other Mixins

`CategoryAdminMixin` works well with other Django admin mixins:

```python
from django.contrib import admin
from djangocms_taxonomy import CategoryAdminMixin
from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(CategoryAdminMixin, admin.ModelAdmin):
    list_display = ("title", "author", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
```

## Category Management Admin

Django CMS Taxonomy includes a built-in admin for the `Category` model:

```python
# This is automatically registered by the app
# But you can customize it by creating your own

from django.contrib import admin
from djangocms_taxonomy.models import Category
from djangocms_taxonomy.admin import CategoryAdmin

# The default CategoryAdmin is already registered,
# but you can override it if needed
```

The Category admin features:

- Hierarchical display with indentation based on depth
- CTE-based tree queries for efficiency
- Multilingual field support via django-parler
- Search by name and slug
- Ordering by path for hierarchical display

## Filtering Objects by Category

You can filter model instances by category in the admin:

```python
@admin.register(BlogPost)
class BlogPostAdmin(CategoryAdminMixin, admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Filter by category if requested
        category_id = request.GET.get("category")
        if category_id:
            from djangocms_taxonomy.models import CategoryRelation

            related = CategoryRelation.objects.filter(category_id=category_id).values_list("object_id", flat=True)
            from django.contrib.contenttypes.models import ContentType

            ct = ContentType.objects.get_for_model(BlogPost)
            related = CategoryRelation.objects.filter(category_id=category_id, content_type=ct).values_list(
                "object_id", flat=True
            )
            qs = qs.filter(id__in=related)

        return qs
```
