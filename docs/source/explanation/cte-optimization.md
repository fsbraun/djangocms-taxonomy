# CTE Optimization

Understanding how Common Table Expressions optimize category queries.

## What are CTEs?

Common Table Expressions (CTEs) are SQL constructs that create temporary result sets. For hierarchical data, CTEs enable **recursive queries**.

## Hierarchical Problem

Without CTEs, querying hierarchies requires:

### Adjacency List Model (Traditional)

Django's standard approach for trees:

```python
class Category(models.Model):
    parent = models.ForeignKey("self", null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
```

**Getting all descendants required:**

```python
# Bad: N+1 problem
category = Category.objects.get(slug="python")
all_descendants = []


def get_all_descendants(cat):
    children = cat.children.all()
    all_descendants.extend(children)
    for child in children:
        get_all_descendants(child)  # Recursive Python query


get_all_descendants(category)

# For a 5-level deep tree with 3 children each:
# Tree size: 363 categories
# Number of queries: 363 (one for each category)
```

### Nested Set Model (Complex)

Alternative approach that uses left/right values:

**Pros**:
- Single query to get subtree
- Efficient ancestor/descendant queries

**Cons**:
- Complex to maintain (recalculating on every insert/update)
- Difficult to implement correctly
- Poor write performance

## CTE Solution

Django CMS Taxonomy uses **recursive CTEs** via `django-cte`:

### Single Query Approach

```python
categories = Category.objects.with_tree_fields()

# Generates SQL like:
# WITH RECURSIVE tree AS (
#     SELECT id, parent_id, 0 as depth FROM category WHERE parent_id IS NULL
#     UNION ALL
#     SELECT c.id, c.parent_id, t.depth + 1
#     FROM category c
#     INNER JOIN tree t ON c.parent_id = t.id
# )
# SELECT * FROM tree;
```

**Results**:
- Single database query regardless of tree depth
- Returns all categories with depth information
- Same result as N+1 approach, but in milliseconds

### Performance Comparison

For a tree with 1000 categories:

```
Adjacency List (N+1):        1000 queries, ~1000ms
Nested Set (Complex):         1 query, ~10ms (but harder to maintain)
CTE (with_tree_fields):       1 query, ~10ms (easy to maintain)
```

## Key CTE Methods

### with_tree_fields()

Adds depth and path to every category:

```python
categories = Category.objects.with_tree_fields()

for cat in categories:
    print(f"{cat.name}: depth={cat.depth}, path={cat.path}")
    # Output:
    # Programming: depth=0, path=[1]
    # Python: depth=1, path=[1, 2]
    # Django: depth=2, path=[1, 2, 5]
```

### roots()

Get only root categories efficiently:

```python
roots = Category.objects.roots()
# Equivalent to: Category.objects.filter(parent__isnull=True)
```

### leaves()

Get only categories without children:

```python
leaves = Category.objects.leaves()
# Uses EXISTS subquery for efficiency
```

### get_children()

Get direct children of a category:

```python
category = Category.objects.get(slug="python")
children = category.get_children()
# Equivalent to: category.category_set.all()
```

### get_descendants()

Get all descendants (recursive):

```python
category = Category.objects.get(slug="programming")
all_descendants = category.get_descendants()

# Uses CTE for single query:
# WITH RECURSIVE descendants AS (
#     SELECT id, parent_id FROM category WHERE parent_id = <id>
#     UNION ALL
#     SELECT c.id, c.parent_id
#     FROM category c
#     INNER JOIN descendants d ON c.parent_id = d.id
# )
# SELECT * FROM descendants;
```

## Real-World Impact

### Blog with 50 Categories

```python
# Without CTE (Django standard):
categories = Category.objects.all()
for cat in categories:
    children = cat.children.all()  # 50 additional queries
print(f"Total queries: 51")

# With CTE:
categories = Category.objects.with_tree_fields().prefetch_related("children")
for cat in categories:
    children = cat.children.all()  # Prefetched, no query
print(f"Total queries: 1-2")
```

### Admin Hierarchical Display

Django CMS Taxonomy's CategoryAdmin uses CTEs:

```python
def get_queryset(self, request):
    # Efficient even with 10000 categories
    return super().get_queryset(request).with_tree_fields()
```

Admin stays responsive regardless of category count.

## Database Support

CTE support by database:

| Database | CTE Support | Recursive CTE |
|----------|-------------|---------------|
| PostgreSQL | 8.4+ | Yes |
| MySQL | 8.0+ | Yes |
| SQLite | 3.8.3+ | Yes |
| Oracle | 9.1+ | Yes |
| SQL Server | 2005+ | Yes |

Django CMS Taxonomy works with virtually all modern databases.

## Advanced: Custom CTE Queries

For complex scenarios, you can write custom CTEs:

```python
from django.db.models import Q, Prefetch

# Get categories at exactly depth 2
depth_2 = Category.objects.with_tree_fields().filter(depth=2)

# Get leaf categories ordered by tree path
leaves = Category.objects.leaves().order_by("path")

# Get all descendants of a category with specific name
root = Category.objects.get(name="Programming")
descendants = root.get_descendants().filter(name__icontains="Python")
```

## Limitations

CTEs work best for:
- Reading hierarchies
- Exporting category structures
- Building menus/navigation

CTEs are less ideal for:
- Frequent tree updates (need to recompute)
- Very deep trees (recursion depth limits)
- Moving nodes (requires updating all descendants)

For these cases, consider storing denormalized path data (which CTEs can provide).

## Summary

**CTEs provide the best of both worlds:**
- Single queries like Nested Set
- Simple maintenance like Adjacency List
- Scalability for large trees
- Modern database support

Django CMS Taxonomy leverages CTEs via `django-cte` for optimal performance.
