# Design Decisions

Key architectural decisions and their rationale.

## Generic Relations vs Foreign Keys

**Decision**: Use ContentType + object_id (generic relations) instead of model-specific foreign keys.

**Rationale**:
- One Category model works with any Django model
- No need to modify Category model when adding category support to new models
- Supports polymorphic relationships (categories with different model types)

**Trade-offs**:
- Slightly more complex queries (need ContentType lookups)
- Less database-level referential integrity
- Performance concerns mitigated with proper indexing and caching

**Alternative Considered**: Create separate relation models for each model type
- Would require model per model type (BlogPostCategory, NewsCategory, etc.)
- More complex schema, harder to maintain
- Decided against due to flexibility needs

## Mixin-based Design

**Decision**: Use three separate mixins (CategoryMixin, CategoryFormMixin, CategoryAdminMixin) instead of a single all-in-one mixin.

**Rationale**:
- Each mixin has a single responsibility
- Can be used independently or combined
- Doesn't force inheritance of unnecessary functionality
- Flexible composition with other mixins

**Example**:
```python
# You don't have to use all three
class MyModel(CategoryMixin, models.Model):
    pass  # Model support only


# Or combine them
@admin.register(MyModel)
class MyAdmin(CategoryAdminMixin, admin.ModelAdmin):
    pass  # Admin support
```

## Bulk Create for Relations

**Decision**: Use `bulk_create()` instead of individual `.create()` calls when saving categories.

**Rationale**:
- Significantly faster (single database round-trip)
- Scales better with many categories
- Follows Django ORM best practices

**Trade-offs**:
- Does not trigger model signals
- Does not set `id` or `pk` on returned objects
- Usually acceptable since CategoryRelation has minimal business logic

**Alternative**: Use `bulk_update()` for updates
- Considered but not implemented (typically fewer relations updated)
- Could be added if performance becomes concern

## CTE for Tree Queries

**Decision**: Use Common Table Expressions via django-cte for hierarchical queries.

**Rationale**:
- Single query retrieves entire subtree
- Better than recursive Python loops
- Native to most modern databases (PostgreSQL, MySQL 8+, SQLite 3.8.3+)
- Significantly better performance than adjacency list model

**Example Trade-off**: Nested Set Model
- More complex to maintain
- Easier to query left/right boundaries
- Harder to update (requires recalculating boundaries)
- Decided against due to CTE advantages

## FilteredSelectMultiple Widget

**Decision**: Use Django's FilteredSelectMultiple widget for category selection.

**Rationale**:
- Better UX than CheckboxSelectMultiple (search capability)
- Works great for many categories
- Built-in to Django contrib.admin

**Alternative Considered**: Custom hierarchical widget
- Would show categories with indentation
- Decided against: Added complexity vs benefit
- FilteredSelectMultiple sufficient for most use cases

## Collapsed Fieldset

**Decision**: Show categories in a collapsed fieldset by default.

**Rationale**:
- Keeps admin cleaner
- Categories are often optional
- User can expand when needed
- Follows Django admin conventions for optional fields

**Alternative**: Show in main fieldset
- Decided against: Clutters interface
- Collapsed approach preferred for cleaner admin

## save_related() vs save()

**Decision**: Save category relations in `save_related()` instead of `save()`.

**Rationale**:
- `save_related()` is Django's standard hook for related object saving
- Called automatically after instance save
- Follows Django ModelAdmin patterns
- Allows for other related objects to be saved first

**Flow**:
```
1. Form validated
2. Model instance saved → save()
3. Relations saved → save_related()
4. Inlines saved
5. Admin redirects
```

## Lazy Field Addition

**Decision**: Add categories field in form's `__init__()` instead of defining in form class.

**Rationale**:
- Avoids app registry issues
- Works with any model without special form definition
- Field is added dynamically when form is instantiated
- Allows for flexible widget customization

**Example**:
```python
# No need for special form class
class MyAdmin(CategoryAdminMixin, admin.ModelAdmin):
    pass  # Field added automatically
```

## Multilingual Support

**Decision**: Use django-parler instead of custom translation system.

**Rationale**:
- Proven, battle-tested package
- Standard in Django ecosystem
- Community support
- Flexible translation management

**Alternative**: Separate Name/Description per language
- Decided against: More schema tables, harder to query
- django-parler handles this elegantly

## No Admin M2M Widget Override

**Decision**: Keep using FilteredSelectMultiple instead of RelatedFieldWidgetWrapper for inline creation.

**Rationale**:
- Categories should be managed separately
- Simpler, cleaner interface
- Avoids complexity of inline category creation
- Users can create categories in Category admin first

**Note**: Could be enhanced in future if needed, but current approach keeps UI clean and predictable.
