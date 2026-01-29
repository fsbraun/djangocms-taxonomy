from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import F, IntegerField, TextField, Value
from django.db.models.functions import Concat
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_cte import CTE, with_cte
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields


class CategoryQuerySet(TranslatableQuerySet):
    """
    Optimized queryset for Category model using CTEs.
    Inherits from TranslatableQuerySet for parler compatibility.
    """

    def with_tree_fields(self) -> models.QuerySet:
        """
        Annotate queryset with tree hierarchy fields using recursive CTE.

        Adds:
        - path: Full hierarchical path (e.g., "Parent / Child / Grandchild")
        - depth: Integer depth in the tree (root = 0)

        Returns:
            QuerySet annotated with path and depth, ordered hierarchically.
        """

        def make_cte(cte) -> models.QuerySet:
            # Non-recursive: get root nodes
            return (
                self.model.objects.filter(parent__isnull=True)
                .order_by()
                .values(  # Clear default ordering for UNION
                    "id",
                    "translations__name",
                    "slug",
                    "parent_id",
                    "translations__description",
                    "date_created",
                    "date_modified",
                    path=F("translations__name"),
                    depth=Value(0, output_field=IntegerField()),
                )
                .union(
                    # Recursive: get descendants
                    cte.join(self.model, parent_id=cte.col.id)
                    .order_by()
                    .values(  # Clear default ordering for UNION
                        "id",
                        "translations__name",
                        "slug",
                        "parent_id",
                        "translations__description",
                        "date_created",
                        "date_modified",
                        path=Concat(
                            cte.col.path,
                            Value("/"),
                            F("slug"),
                            output_field=TextField(),
                        ),
                        depth=cte.col.depth + Value(1, output_field=IntegerField()),
                    ),
                    all=True,
                )
            )

        cte = CTE.recursive(make_cte)

        return with_cte(
            cte,
            select=cte.join(self.model, id=cte.col.id)
            .annotate(
                path=cte.col.path,
                depth=cte.col.depth,
            )
            .order_by("path"),
        )

    def roots(self) -> "CategoryQuerySet":
        """
        Get all root categories (no parent).

        Returns:
            QuerySet of root categories.
        """
        return self.filter(parent__isnull=True)

    def leaves(self) -> "CategoryQuerySet":
        """
        Get all leaf categories (no children).

        Returns:
            QuerySet of leaf categories.
        """
        return self.filter(children__isnull=True)


class CategoryManager(models.Manager.from_queryset(CategoryQuerySet)):
    """Category manager exposing CategoryQuerySet helpers."""

    def descendants_of(self, category: "Category | int", *, include_self: bool = False) -> "CategoryQuerySet":
        """Return all descendants of a given category using a recursive CTE.

        Args:
            category: Category instance or primary key.
            include_self: Include the given category itself in the result.

        Returns:
            QuerySet of descendant Category objects.
        """

        category_id = category.pk if isinstance(category, Category) else int(category)

        def make_cte(cte) -> models.QuerySet:
            return (
                # Seed the CTE with the starting node to keep everything inside
                # a single WITH RECURSIVE expression.
                self.model.objects.filter(id=category_id)
                .order_by()
                .values("id", "parent_id")
                .union(
                    cte.join(self.model, parent_id=cte.col.id).order_by().values("id", "parent_id"),
                    all=True,
                )
            )

        cte = CTE.recursive(make_cte)
        qs = with_cte(cte, select=cte.join(self.model, id=cte.col.id)).distinct()
        if include_self:
            return qs
        return qs.exclude(pk=category_id)



class Category(TranslatableModel):
    """
    A hierarchical category model for taxonomy management.

    Categories are reusable across different content types and can be
    attached to any Django model via the CategoryRelation intermediary model.

    Features:
    - Hierarchical structure with parent-child relationships
    - Reusable across multiple content types
    - Translatable name and description using django-parler
    - Metadata like creation/modification dates
    - Optimized tree traversal to minimize database queries
    """

    # Hierarchical structure
    parent = models.ForeignKey(
        "self",
        verbose_name=_("parent"),
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
    )

    # Non-translatable core field
    slug = models.SlugField(
        _("slug"),
        max_length=255,
        unique=True,
        db_index=True,
    )

    # Translatable fields
    translations = TranslatedFields(
        name=models.CharField(
            _("name"),
            max_length=255,
        ),
        description=models.TextField(
            _("description"),
            blank=True,
        ),
    )

    # Timestamps
    date_created = models.DateTimeField(
        _("created at"),
        auto_now_add=True,
    )
    date_modified = models.DateTimeField(
        _("modified at"),
        auto_now=True,
    )

    # Custom manager with optimizations
    objects = CategoryManager()

    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")

        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["parent"]),
        ]

    def save(self, *args, **kwargs) -> None:
        """
        Auto-generate slug from name if not provided.

        Args:
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        if not self.slug and self.name:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """
        Return the string representation of the category.

        Returns:
            The category name.
        """
        return f"{self.name} ({self.parent.name})" if self.parent else self.name


class CategoryRelation(models.Model):
    """
    Intermediary model for generic many-to-many relationships between
    Category and any Django model.

    This allows:
    - Multiple categories to be attached to any object
    - Categories to be reused across different content types
    - Efficient querying and filtering
    """

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name=_("category"),
        related_name="relations",
    )

    # Generic foreign key to any model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("content type"),
    )
    object_id = models.PositiveIntegerField(
        _("object id"),
    )
    content_object = GenericForeignKey("content_type", "object_id")

    # Optional ordering within the relationship
    order = models.IntegerField(
        _("order"),
        default=0,
        help_text=_("Order of this category for the related object"),
    )

    class Meta:
        verbose_name = _("category relation")
        verbose_name_plural = _("category relations")
        ordering = ["order", "category__translations__name"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["category", "content_type"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["category", "content_type", "object_id"],
                name="unique_category_per_object",
            ),
        ]

    def __str__(self) -> str:
        """
        Return the string representation of the relation.

        Returns:
            A description of the category-object relationship.
        """
        return f"{self.category.name} -> {self.content_type.model}"
