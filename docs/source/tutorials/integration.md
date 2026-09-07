# Complete Integration Example

A complete, working example of integrating Django CMS Taxonomy.

## Project Setup

```python
# settings.py

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Required dependencies
    "parler",
    "django_cte",
    # Django CMS Taxonomy
    "djangocms_taxonomy",
    # Your apps
    "blog",
]

LANGUAGES = [
    ("en", "English"),
    ("de", "German"),
]

LANGUAGE_CODE = "en"
```

## Models

```python
# blog/models.py

from django.db import models
from django.urls import reverse
from djangocms_taxonomy import CategoryMixin


class BlogPost(CategoryMixin, models.Model):
    """Blog post with category support."""

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    excerpt = models.CharField(max_length=500, blank=True)
    author = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=[("draft", "Draft"), ("published", "Published")], default="draft")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:post-detail", args=[self.slug])
```

## Admin Configuration

```python
# blog/admin.py

from django.contrib import admin
from djangocms_taxonomy import CategoryAdminMixin
from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(CategoryAdminMixin, admin.ModelAdmin):
    list_display = ("title", "author", "status", "created_at", "category_list")
    list_filter = ("status", "created_at", "author")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Basic Info", {"fields": ("title", "slug", "author", "status")}),
        ("Content", {"fields": ("excerpt", "content")}),
        ("Meta", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def category_list(self, obj):
        """Display categories in list view."""
        return ", ".join([cat.name for cat in obj.categories.all()])

    category_list.short_description = "Categories"
```

## Views

```python
# blog/views.py

from django.views.generic import ListView, DetailView
from .models import BlogPost


class BlogPostListView(ListView):
    model = BlogPost
    paginate_by = 10
    queryset = BlogPost.objects.filter(status="published")
    context_object_name = "posts"
    template_name = "blog/post_list.html"


class BlogPostDetailView(DetailView):
    model = BlogPost
    slug_field = "slug"
    queryset = BlogPost.objects.filter(status="published")
    context_object_name = "post"
    template_name = "blog/post_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add related posts from same categories
        categories = self.object.categories.all()
        context["related_posts"] = (
            BlogPost.objects.filter(status="published", categoryrelation__category__in=categories)
            .exclude(id=self.object.id)
            .distinct()[:5]
        )
        return context
```

## Templates

```html
{# blog/post_list.html #}
{% extends "base.html" %}

{% block content %}
<div class="blog-posts">
    {% for post in posts %}
    <article class="post-card">
        <h2><a href="{{ post.get_absolute_url }}">{{ post.title }}</a></h2>
        <div class="meta">
            <span class="author">By {{ post.author }}</span>
            <span class="date">{{ post.created_at|date:"SHORT_DATE_FORMAT" }}</span>
        </div>

        {% if post.categories.all %}
        <div class="categories">
            {% for category in post.categories.all %}
                <a href="#" class="category-tag">{{ category.name }}</a>
            {% endfor %}
        </div>
        {% endif %}

        <p>{{ post.excerpt }}</p>
        <a href="{{ post.get_absolute_url }}" class="read-more">Read More →</a>
    </article>
    {% endfor %}
</div>
{% endblock %}
```

```html
{# blog/post_detail.html #}
{% extends "base.html" %}

{% block content %}
<article class="post-detail">
    <h1>{{ post.title }}</h1>

    <div class="meta">
        <span class="author">By {{ post.author }}</span>
        <span class="date">{{ post.created_at|date:"DATETIME_FORMAT" }}</span>
    </div>

    {% if post.categories.all %}
    <div class="categories">
        <h4>Categories</h4>
        <ul>
        {% for category in post.categories.all %}
            <li><a href="#">{{ category.name }}</a></li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}

    <div class="content">
        {{ post.content|safe }}
    </div>

    {% if related_posts %}
    <section class="related-posts">
        <h3>Related Posts</h3>
        <ul>
        {% for related in related_posts %}
            <li><a href="{{ related.get_absolute_url }}">{{ related.title }}</a></li>
        {% endfor %}
        </ul>
    </section>
    {% endif %}
</article>
{% endblock %}
```

## URLs

```python
# blog/urls.py

from django.urls import path
from .views import BlogPostListView, BlogPostDetailView

app_name = "blog"

urlpatterns = [
    path("", BlogPostListView.as_view(), name="post-list"),
    path("<slug:slug>/", BlogPostDetailView.as_view(), name="post-detail"),
]
```

This example demonstrates:
- Model setup with `CategoryMixin`
- Admin integration with `CategoryAdminMixin`
- Using categories in views
- Displaying categories in templates
