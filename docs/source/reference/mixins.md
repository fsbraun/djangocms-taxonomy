# Mixins API

Reference documentation for Django CMS Taxonomy mixins.

## CategoryMixin

Model mixin that adds category support to any Django model.

```{autoclass} djangocms_taxonomy.mixins.CategoryMixin
:members:
:undoc-members:
```

### Properties

#### categories

Returns a QuerySet of all categories associated with this instance.

**Returns**: `QuerySet[Category]`

**Example**:
```python
post = BlogPost.objects.get(id=1)
categories = post.categories.all()
```

## CategoryFormMixin

Form mixin that adds category field to model forms.

```{autoclass} djangocms_taxonomy.mixins.CategoryFormMixin
:members:
:undoc-members:
```

### Methods

#### save_m2m()

Save category relations to the database.

Called automatically by Django when `form.save()` is invoked with `commit=True`.

**Returns**: `None`

## CategoryAdminMixin

Admin mixin that provides category management in Django admin.

```{autoclass} djangocms_taxonomy.mixins.CategoryAdminMixin
:members:
:undoc-members:
```

### Methods

#### get_form(request, obj=None, **kwargs)

Get the form class with category support.

**Parameters**:
- `request` (`HttpRequest`): The request object
- `obj` (`Model | None`): The model instance being edited
- `**kwargs`: Additional keyword arguments

**Returns**: `type[ModelForm]`

#### get_fieldsets(request, obj=None)

Get fieldsets including a collapsed categories section.

**Parameters**:
- `request` (`HttpRequest`): The request object
- `obj` (`Model | None`): The model instance being edited

**Returns**: `tuple`

#### get_readonly_fields(request, obj=None)

Get readonly fields (preserves parent implementation).

**Parameters**:
- `request` (`HttpRequest`): The request object
- `obj` (`Model | None`): The model instance being edited

**Returns**: `list[str]`

#### save_related(request, form, formsets, change)

Save category relations after the main form is saved.

**Parameters**:
- `request` (`HttpRequest`): The request object
- `form` (`ModelForm`): The form instance
- `formsets` (`list`): Inline formsets
- `change` (`bool`): Whether this is an edit (True) or creation (False)

**Returns**: `None`
