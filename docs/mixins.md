# Category Mixins Usage Guide

## CategoryMixin (Model Mixin)

Adds a `categories` property to any Django model that provides reverse relation access to associated categories.

### Usage

```python
from django.db import models
from djangocms_taxonomy import CategoryMixin

class Article(CategoryMixin, models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
```

### Accessing Categories

```python
# Get an article
article = Article.objects.get(pk=1)

# Access categories as a QuerySet
categories = article.categories.all()

# Filter categories
featured_cats = article.categories.filter(slug__contains="featured")

# Count categories
num_categories = article.categories.count()

# Check if has categories
has_cats = article.categories.exists()

# Get category names
names = list(article.categories.values_list("name", flat=True))
```

### Creating Category Relations

```python
from django.contrib.contenttypes.models import ContentType
from djangocms_taxonomy.models import Category, CategoryRelation

# Get or create a category
category = Category.objects.create(slug="news")
category.set_current_language("en")
category.name = "News"
category.save()

# Create the relation
content_type = ContentType.objects.get_for_model(Article)
CategoryRelation.objects.create(
    category=category,
    content_type=content_type,
    object_id=article.pk,
    order=0,
)

# Now accessible via the mixin
assert category in article.categories.all()
```

## CategoryAdminMixin (Admin Mixin)

Adds category selection to Django admin for any model.

### Usage

```python
from django.contrib import admin
from djangocms_taxonomy import CategoryAdminMixin
from myapp.models import Article

@admin.register(Article)
class ArticleAdmin(CategoryAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'created')
    search_fields = ('title',)
```

This automatically adds:
- Multi-select categories field with hierarchical display
- Automatic CategoryRelation management
- Collapsible "Taxonomy" fieldset in admin

## Combined Usage

For complete integration, use both mixins:

```python
# models.py
from django.db import models
from djangocms_taxonomy import CategoryMixin

class Article(CategoryMixin, models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()

# admin.py
from django.contrib import admin
from djangocms_taxonomy import CategoryAdminMixin
from .models import Article

@admin.register(Article)
class ArticleAdmin(CategoryAdminMixin, admin.ModelAdmin):
    list_display = ('title',)
```

Now you can:
1. Select categories in Django admin
2. Access categories programmatically via `article.categories`
3. Query articles by category relationships
