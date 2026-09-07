# Generic Relations

Understanding Django's generic relations and how Django CMS Taxonomy uses them.

## What are Generic Relations?

Generic relations allow a model to have foreign key relationships to **any** other model in your Django project, without knowing them in advance.

### Traditional Foreign Key

```python
class BlogPost(models.Model):
    title = models.CharField(max_length=255)


class Comment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE)
    text = models.TextField()
```

**Problem**: Comment can only link to BlogPost. What if you want comments on news, photos, etc.?

### Generic Foreign Key

```python
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class Comment(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    text = models.TextField()
```

**Solution**: Comment can now link to any model (BlogPost, NewsArticle, Photo, etc.)

## How CategoryRelation Uses Generic Relations

Django CMS Taxonomy's `CategoryRelation` model uses this pattern:

```python
from django.contrib.contenttypes.models import ContentType


class CategoryRelation(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Benefit**: Single Category model works with **any** Django model.

## Using Generic Relations

### Creating Relations

```python
from django.contrib.contenttypes.models import ContentType
from djangocms_taxonomy.models import Category, CategoryRelation
from blog.models import BlogPost

# Create a category
category = Category.objects.create(name="Django", slug="django")

# Create a blog post
post = BlogPost.objects.create(title="Django Tips")

# Link them
content_type = ContentType.objects.get_for_model(BlogPost)
relation = CategoryRelation.objects.create(category=category, content_type=content_type, object_id=post.id)
```

### Querying Relations

```python
# Get all relations for a category
relations = CategoryRelation.objects.filter(category=category)

# Access the related object
for rel in relations:
    print(f"Category linked to: {rel.object_id} ({rel.content_type})")

    # Get the actual object (if you need it)
    obj = rel.content_type.get_object_for_this_type(pk=rel.object_id)
    print(f"Title: {obj.title}")

# Get all categories for a blog post
content_type = ContentType.objects.get_for_model(BlogPost)
categories = CategoryRelation.objects.filter(content_type=content_type, object_id=post.id).values_list(
    "category", flat=True
)

post_categories = Category.objects.filter(id__in=categories)
```

## Why Generic Relations for Categories?

### Advantages

1. **Flexibility**: One Category model for all content types
2. **Scalability**: Add categories to new models without schema changes
3. **Simplicity**: No need for separate relation models

### Example: Multiple Content Types

```python
# Without generic relations:
# Create separate models:
class BlogPostCategory(models.Model):
    blog_post = models.ForeignKey(BlogPost, ...)
    category = models.ForeignKey(Category, ...)


class NewsArticleCategory(models.Model):
    news_article = models.ForeignKey(NewsArticle, ...)
    category = models.ForeignKey(Category, ...)


class PhotoCategory(models.Model):
    photo = models.ForeignKey(Photo, ...)
    category = models.ForeignKey(Category, ...)


# With generic relations:
class CategoryRelation(models.Model):
    category = models.ForeignKey(Category, ...)
    content_type = models.ForeignKey(ContentType, ...)
    object_id = models.PositiveIntegerField()
```

Single CategoryRelation table handles all relationships!

## ContentType Framework

The `ContentType` model stores information about Django models:

```python
from django.contrib.contenttypes.models import ContentType

# Get ContentType for a model
ct = ContentType.objects.get_for_model(BlogPost)
print(f"App label: {ct.app_label}")  # blog
print(f"Model: {ct.model}")  # blogpost
print(f"ID: {ct.id}")  # Unique identifier

# Reverse lookup
ct = ContentType.objects.get(app_label="blog", model="blogpost")
```

### Using ContentType in Queries

```python
# Find all categories linked to BlogPost objects
from django.contrib.contenttypes.models import ContentType
from djangocms_taxonomy.models import CategoryRelation

ct = ContentType.objects.get_for_model(BlogPost)
relations = CategoryRelation.objects.filter(content_type=ct)

# Works across models
ct_news = ContentType.objects.get_for_model(NewsArticle)
relations = CategoryRelation.objects.filter(content_type=ct_news)
```

## Performance Considerations

### Potential N+1 Problem

```python
# Bad: Each relation requires content_type lookup
relations = CategoryRelation.objects.all()
for rel in relations:
    print(rel.content_type)  # Query for each relation
```

### Optimized with select_related

```python
# Good: Fetch content_type in single query
relations = CategoryRelation.objects.select_related("content_type", "category")
for rel in relations:
    print(rel.content_type)  # Already loaded
    print(rel.category)  # Already loaded
```

## CategoryMixin Alternative

Django CMS Taxonomy provides `CategoryMixin` to avoid these queries:

```python
from djangocms_taxonomy import CategoryMixin


class BlogPost(CategoryMixin, models.Model):
    title = models.CharField(max_length=255)


# Simple access:
post = BlogPost.objects.get(id=1)
categories = post.categories.all()  # Handles ContentType lookup automatically
```

The mixin encapsulates the generic relation logic.

## Trade-offs

### Generic Relations Pros
- Single table for all relationships
- Flexible schema
- No schema changes needed for new models

### Generic Relations Cons
- Slightly more complex queries
- Require ContentType lookups
- No database-level referential integrity
- Can't use raw SQL as easily
- Potential for orphaned relations

### Mitigation
Django CMS Taxonomy handles most complexity:
- CategoryMixin provides clean API
- CategoryAdminMixin manages relations automatically
- Bulk operations for performance
- Pre-fetching support to avoid N+1

## Advanced: Custom Generic Relation

If you need custom behavior, you can work with CategoryRelation directly:

```python
from django.contrib.contenttypes.models import ContentType
from djangocms_taxonomy.models import Category, CategoryRelation


def categorize_object(obj, category_ids):
    """Assign categories to any object."""
    content_type = ContentType.objects.get_for_model(obj.__class__)

    # Clear existing
    CategoryRelation.objects.filter(content_type=content_type, object_id=obj.id).delete()

    # Create new
    relations = [
        CategoryRelation(category_id=cat_id, content_type=content_type, object_id=obj.id, order=i)
        for i, cat_id in enumerate(category_ids)
    ]
    CategoryRelation.objects.bulk_create(relations)


# Usage
post = BlogPost.objects.get(id=1)
categorize_object(post, [1, 2, 3])  # Assign categories 1, 2, 3
```

## Summary

Generic relations enable Django CMS Taxonomy to:
- Work with any Django model
- Use a single Category model for all relationships
- Scale from simple blogs to complex multi-model systems
- Maintain clean, flexible architecture

The trade-off of slightly more complex queries is worth the flexibility and maintainability benefits.
