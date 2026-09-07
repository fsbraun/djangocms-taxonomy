# Getting Started

Welcome to Django CMS Taxonomy! This tutorial will walk you through the basic setup and usage.

## Installation

Install Django CMS Taxonomy using pip:

```bash
pip install djangocms-taxonomy
```

## Configuration

Add `djangocms_taxonomy` to your Django `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... other apps
    "parler",  # Required for multilingual support
    "django_cte",  # Required for efficient tree queries
    "djangocms_taxonomy",
]
```

## Your First Category Model

The `Category` model is provided by Django CMS Taxonomy. It includes:

- Hierarchical parent-child relationships
- Multilingual name and description fields
- CTE-based tree traversal for efficient queries
- Slug field for URL-friendly names

You don't need to create a Category model yourself—it's already provided and ready to use!

## Adding Categories to Your Models

Use `CategoryMixin` to add category support to any Django model:

```python
from django.db import models
from djangocms_taxonomy import CategoryMixin


class BlogPost(CategoryMixin, models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()

    def __str__(self):
        return self.title
```

## Accessing Categories

Once your model uses `CategoryMixin`, you can access related categories:

```python
post = BlogPost.objects.first()
categories = post.categories.all()

# Use category relationships
for category in categories:
    print(f"{post.title} is in {category.name}")
```

## Admin Integration

Add category selection to your model's admin using `CategoryAdminMixin`:

```python
from django.contrib import admin
from djangocms_taxonomy import CategoryAdminMixin
from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(CategoryAdminMixin, admin.ModelAdmin):
    list_display = ("title", "created_at")
    search_fields = ("title", "content")
```

The mixin automatically:
- Adds a "Categories" fieldset (collapsed by default)
- Provides a filtered select multiple widget
- Manages category relations on save
- Handles both creation and editing

## Next Steps

- Learn more about [Creating Category Models](models.md)
- Explore [Admin Configuration](admin.md)
- See [Complete Integration Example](integration.md)
