# Working with Models

Learn how to use `CategoryMixin` in your Django models.

## Basic Usage

Import and add `CategoryMixin` to your model:

```python
from django.db import models
from djangocms_taxonomy import CategoryMixin


class Article(CategoryMixin, models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
```

## Accessing Categories

The `CategoryMixin` provides a `categories` property that returns a QuerySet:

```python
article = Article.objects.get(id=1)

# Get all categories
all_categories = article.categories.all()

# Count categories
category_count = article.categories.count()

# Filter categories
tech_categories = article.categories.filter(name__icontains="tech")

# Order categories
sorted_categories = article.categories.order_by("name")
```

## Hierarchical Category Queries

Since categories are hierarchical, you can access parent-child relationships:

```python
article = Article.objects.get(id=1)

for category in article.categories.all():
    # Get parent category
    parent = category.parent

    # Get all children
    children = category.get_children()

    # Check if it's a root category
    is_root = category.parent is None

    # Get all descendants
    descendants = category.get_descendants()
```

## Category Ordering

Categories are saved in `CategoryRelation` with an `order` field. The order is preserved based on the selection order in the admin:

```python
# Get categories in their saved order
ordered_cats = article.categories.all()

# Access the order through the relation
from djangocms_taxonomy.models import CategoryRelation

relations = CategoryRelation.objects.filter(
    content_type=ContentType.objects.get_for_model(Article), object_id=article.id
).order_by("order")

for rel in relations:
    print(f"{rel.order}: {rel.category.name}")
```

## Multiple Models with Categories

You can add `CategoryMixin` to multiple models. The `Category` model uses generic foreign keys, so one category can be associated with different model types:

```python
class BlogPost(CategoryMixin, models.Model):
    title = models.CharField(max_length=255)


class NewsArticle(CategoryMixin, models.Model):
    title = models.CharField(max_length=255)
    source = models.CharField(max_length=255)


# Both can share the same categories
blog = BlogPost.objects.create(title="Django Tips")
news = NewsArticle.objects.create(title="Django 5.0 Released", source="Official")

# They use the same Category objects through different relations
from djangocms_taxonomy.models import Category

cat = Category.objects.create(name="Django")

CategoryRelation.objects.create(
    category=cat, content_type=ContentType.objects.get_for_model(BlogPost), object_id=blog.id
)
CategoryRelation.objects.create(
    category=cat, content_type=ContentType.objects.get_for_model(NewsArticle), object_id=news.id
)
```

## Performance Considerations

The `categories` property queries the database each time it's accessed. For optimal performance in loops, cache the queryset:

```python
# Good - single query
articles = Article.objects.all()
for article in articles:
    categories = article.categories.all()  # Query for each article

# Better - prefetch related
from django.db.models import Prefetch

articles = Article.objects.prefetch_related("categoryrelation_set").all()
```
