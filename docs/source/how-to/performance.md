# Optimize Performance

Best practices for optimal performance with Django CMS Taxonomy.

## Database Query Optimization

### Prefetch Related Categories

When working with multiple objects, prefetch their categories:

```python
from django.db.models import Prefetch
from djangocms_taxonomy.models import CategoryRelation
from blog.models import BlogPost

# Good: One query per object
posts = BlogPost.objects.all()
for post in posts:
    categories = post.categories.all()  # N queries

# Better: Prefetch all categories in 2 queries
posts = BlogPost.objects.prefetch_related("categoryrelation_set").all()
for post in posts:
    categories = post.categories.all()  # No additional queries

# Best: Custom prefetch with select_related
relations = CategoryRelation.objects.select_related("category")
posts = BlogPost.objects.prefetch_related(Prefetch("categoryrelation_set", queryset=relations)).all()
```

### Use only() and defer()

Limit fields retrieved from database:

```python
# Get only necessary fields
posts = BlogPost.objects.only("id", "title").all()

# Exclude large fields
posts = BlogPost.objects.defer("content").all()
```

## CTE Query Optimization

Django CMS Taxonomy uses CTEs for efficient tree queries:

```python
from djangocms_taxonomy.models import Category

# Efficient: Single CTE query to get tree structure
root = Category.objects.get(slug="programming")
children = root.get_children()  # Uses CTE
descendants = root.get_descendants()  # Uses CTE
```

## Caching

### Cache Category Hierarchy

```python
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from djangocms_taxonomy.models import Category


def get_category_tree():
    """Get category tree with caching."""
    cache_key = "category_tree"
    tree = cache.get(cache_key)

    if tree is None:
        tree = Category.objects.roots()
        cache.set(cache_key, tree, 3600)  # Cache for 1 hour

    return tree


@cache_page(60 * 15)  # Cache view for 15 minutes
def category_list(request):
    categories = get_category_tree()
    return render(request, "categories/list.html", {"categories": categories})
```

### Cache Category Filtering

```python
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType
from djangocms_taxonomy.models import CategoryRelation
from blog.models import BlogPost


def get_posts_by_category(category_id):
    """Get posts in category with caching."""
    cache_key = f"posts_category_{category_id}"
    posts = cache.get(cache_key)

    if posts is None:
        ct = ContentType.objects.get_for_model(BlogPost)
        post_ids = CategoryRelation.objects.filter(category_id=category_id, content_type=ct).values_list(
            "object_id", flat=True
        )

        posts = list(BlogPost.objects.filter(id__in=post_ids))
        cache.set(cache_key, posts, 3600)

    return posts
```

## Bulk Operations

### Use bulk_create for Multiple Categories

Django CMS Taxonomy's `CategoryFormMixin` already uses `bulk_create`:

```python
# Automatically optimized - creates all relations in one query
form.save()  # Uses bulk_create internally
```

If you need to create relations manually:

```python
from djangocms_taxonomy.models import CategoryRelation
from django.contrib.contenttypes.models import ContentType
from blog.models import BlogPost

post = BlogPost.objects.get(id=1)
ct = ContentType.objects.get_for_model(BlogPost)
categories = [1, 2, 3]  # Category IDs

relations = [
    CategoryRelation(category_id=cat_id, content_type=ct, object_id=post.id, order=i)
    for i, cat_id in enumerate(categories)
]

# Single query for all relations
CategoryRelation.objects.bulk_create(relations)
```

## Select Related Categories

```python
# Good for accessing category fields
posts = BlogPost.objects.all()
categories = Category.objects.all()  # Separate query

# Better: Select related when accessing category details
from django.db.models import Prefetch

relations = CategoryRelation.objects.select_related("category")
posts = BlogPost.objects.prefetch_related(Prefetch("categoryrelation_set", queryset=relations))

# Now accessing category.name doesn't trigger new query
for post in posts:
    for relation in post.categoryrelation_set.all():
        print(relation.category.name)  # No query
```

## Batch Delete Categories

```python
from django.contrib.contenttypes.models import ContentType
from djangocms_taxonomy.models import CategoryRelation
from blog.models import BlogPost

# Efficient deletion
ct = ContentType.objects.get_for_model(BlogPost)
CategoryRelation.objects.filter(content_type=ct, object_id__in=[1, 2, 3]).delete()  # Single query
```

## Monitoring Performance

Use Django Debug Toolbar to monitor queries:

```python
# settings/development.py

INSTALLED_APPS += ["debug_toolbar"]

MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

INTERNAL_IPS = ["127.0.0.1"]
```

Monitor query count when working with categories to identify N+1 problems.
