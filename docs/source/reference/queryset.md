# QuerySet API

Reference documentation for QuerySet methods.

## CategoryQuerySet Methods

### with_tree_fields()

Annotate queryset with CTE-based tree structure fields.

**Returns**: `QuerySet[Category]`

**Annotations Added**:
- **depth**: Integer representing distance from root (0 = root)
- **path**: String array representing ancestor IDs

**Example**:
```python
categories = Category.objects.with_tree_fields()

for cat in categories:
    print(f"{cat.name} (depth: {cat.depth})")
```

### roots()

Return only root categories (those without a parent).

**Returns**: `QuerySet[Category]`

**Example**:
```python
root_categories = Category.objects.roots()

# Equivalent to:
# Category.objects.filter(parent__isnull=True)
```

### leaves()

Return only leaf categories (those without children).

**Returns**: `QuerySet[Category]`

**Example**:
```python
leaf_categories = Category.objects.leaves()

# Get all categories that have no subcategories
```

## Related QuerySet Methods

### get_children()

Get direct child categories.

**Returns**: `QuerySet[Category]`

**Example**:
```python
category = Category.objects.get(slug="programming")
children = category.get_children()

# Returns only direct children, not grandchildren
```

### get_descendants()

Get all descendant categories (children, grandchildren, etc.).

**Returns**: `QuerySet[Category]`

**Example**:
```python
category = Category.objects.get(slug="programming")
descendants = category.get_descendants()

# Returns all categories under this one in the tree
```

## Chaining

QuerySet methods can be chained:

```python
# Get root categories with tree fields
roots = Category.objects.with_tree_fields().roots()

# Get leaf categories ordered by name
leaves = Category.objects.leaves().order_by("name")

# Get descendants of a category with depth
parent = Category.objects.get(slug="python")
descendants = parent.get_descendants().with_tree_fields()
```

## Filtering

Filter on annotated fields:

```python
# Get categories at depth 2 (grandchildren of root)
categories = Category.objects.with_tree_fields().filter(depth=2)

# Get categories with certain slug patterns
technical = Category.objects.filter(slug__in=["python", "javascript", "golang"])

# Combine filters
root_tech = Category.objects.roots().filter(slug__startswith="tech-")
```

## Performance

The CTE-based methods are optimized for performance:

- **with_tree_fields()**: Single query with CTE
- **roots()**: Simple filter on parent field
- **leaves()**: Uses EXISTS subquery
- **get_children()**: Direct parent filter
- **get_descendants()**: CTE-based recursive query

Avoid N+1 problems by prefetching relations:

```python
# Good: Prefetch all tree fields in one query
categories = Category.objects.with_tree_fields().prefetch_related("children")

# Use in views
for cat in categories:
    print(cat.depth)  # No additional query
    for child in cat.children.all():  # Prefetched, no query
        print(child.name)
```
