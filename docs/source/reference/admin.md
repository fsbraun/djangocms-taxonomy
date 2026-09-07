# Admin API

Reference documentation for Django CMS Taxonomy admin classes.

## CategoryAdmin

Built-in admin for the Category model.

```{autoclass} djangocms_taxonomy.admin.CategoryAdmin
:members:
:undoc-members:
```

### Features

- **Hierarchical Display**: Categories shown with indentation based on tree depth
- **CTE Optimization**: Uses efficient CTE queries for tree traversal
- **List Display**: Shows indented names, slugs, and timestamps
- **Search**: Search by name and slug
- **Ordering**: Ordered by tree path for hierarchical display
- **Prepopulated Fields**: Slug auto-populated from name
- **Localized**: Translatable name and description fields via django-parler

### List Display Columns

- **indented_name**: Name with indentation showing hierarchy
- **slug**: URL-friendly slug
- **created_at**: Creation date
- **updated_at**: Last modification date

### Search Fields

- **name**: Category name (translatable)
- **slug**: Category slug

### Actions

Standard Django admin actions available:
- Delete selected categories (with cascade to relations)

## Integration with Your Models

Use `CategoryAdminMixin` in your admin classes:

```python
from django.contrib import admin
from djangocms_taxonomy import CategoryAdminMixin
from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(CategoryAdminMixin, admin.ModelAdmin):
    pass
```

The mixin automatically:
1. Adds categories field to the form
2. Creates a collapsed "Categories" fieldset
3. Provides FilteredSelectMultiple widget
4. Manages CategoryRelation objects on save
