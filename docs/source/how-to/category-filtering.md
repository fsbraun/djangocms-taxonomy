# Filter Objects by Category

Learn how to query and filter your models by category.

## Basic Filtering

### Filter by a Single Category

```python
from blog.models import BlogPost
from djangocms_taxonomy.models import Category, CategoryRelation
from django.contrib.contenttypes.models import ContentType

# Get all posts in a specific category
category = Category.objects.get(slug="django")
ct = ContentType.objects.get_for_model(BlogPost)

post_ids = CategoryRelation.objects.filter(category=category, content_type=ct).values_list("object_id", flat=True)

posts = BlogPost.objects.filter(id__in=post_ids)
```

### Filter by Multiple Categories (OR)

```python
# Get posts that are in ANY of these categories
categories = Category.objects.filter(slug__in=["django", "python"])
ct = ContentType.objects.get_for_model(BlogPost)

post_ids = CategoryRelation.objects.filter(category__in=categories, content_type=ct).values_list(
    "object_id", flat=True
)

posts = BlogPost.objects.filter(id__in=post_ids).distinct()
```

### Filter by Multiple Categories (AND)

```python
# Get posts that are in ALL of these categories
category_slugs = ["django", "tutorial"]

for slug in category_slugs:
    category = Category.objects.get(slug=slug)
    ct = ContentType.objects.get_for_model(BlogPost)

    post_ids = CategoryRelation.objects.filter(category=category, content_type=ct).values_list("object_id", flat=True)

    posts = posts.filter(id__in=post_ids)
```

## Exclude Categories

```python
# Get posts NOT in a specific category
exclude_category = Category.objects.get(slug="deprecated")
ct = ContentType.objects.get_for_model(BlogPost)

exclude_ids = CategoryRelation.objects.filter(category=exclude_category, content_type=ct).values_list(
    "object_id", flat=True
)

posts = BlogPost.objects.exclude(id__in=exclude_ids)
```

## Count by Category

```python
from django.db.models import Count

# Count how many posts are in each category
categories = Category.objects.all()

for category in categories:
    ct = ContentType.objects.get_for_model(BlogPost)
    count = CategoryRelation.objects.filter(category=category, content_type=ct).count()
    print(f"{category.name}: {count} posts")
```

## Django ORM Helper

Create a helper method on your model for convenience:

```python
# blog/models.py

from django.db import models
from djangocms_taxonomy import CategoryMixin


class BlogPost(CategoryMixin, models.Model):
    title = models.CharField(max_length=255)
    # ... other fields

    @classmethod
    def by_category(cls, category):
        """Get all posts in a category."""
        from djangocms_taxonomy.models import CategoryRelation
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get_for_model(cls)
        post_ids = CategoryRelation.objects.filter(category=category, content_type=ct).values_list(
            "object_id", flat=True
        )

        return cls.objects.filter(id__in=post_ids)


# Usage
django_posts = BlogPost.by_category(django_category)
```

## Template Filtering

In your Django templates, you can filter using the categories property:

```html
{# Display all posts with a specific category #}
{% for post in posts %}
    {% if 'django'|slugify in post.categories.values_list 'slug' %}
        <p>{{ post.title }} - Django related</p>
    {% endif %}
{% endfor %}
```

Or better, do the filtering in views:

```python
# views.py
class BlogPostListView(ListView):
    def get_queryset(self):
        category_slug = self.kwargs.get("category_slug")
        qs = BlogPost.objects.filter(status="published")

        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            return BlogPost.by_category(category)

        return qs
```
