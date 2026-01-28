"""Tests for CategoryMixin model mixin."""

import pytest
from django.contrib.contenttypes.models import ContentType

from djangocms_taxonomy.models import Category, CategoryRelation
from tests.test_app.models import TestModel


@pytest.mark.django_db
class TestCategoryMixin:
    """Test CategoryMixin functionality."""

    def setup_method(self) -> None:
        """Set up test data."""
        # Create test categories
        self.cat1 = Category.objects.create(slug="cat1")
        self.cat1.set_current_language("en")
        self.cat1.name = "Category 1"
        self.cat1.save()

        self.cat2 = Category.objects.create(slug="cat2")
        self.cat2.set_current_language("en")
        self.cat2.name = "Category 2"
        self.cat2.save()

        self.cat3 = Category.objects.create(slug="cat3")
        self.cat3.set_current_language("en")
        self.cat3.name = "Category 3"
        self.cat3.save()

    def test_categories_property_returns_queryset(self) -> None:
        """Test that categories property returns a QuerySet."""
        obj = TestModel.objects.create(title="Test")

        # Verify it returns a QuerySet
        assert hasattr(obj, "categories")
        categories = obj.categories
        assert hasattr(categories, "all")
        assert hasattr(categories, "filter")

    def test_categories_property_empty_when_no_relations(self) -> None:
        """Test that categories returns empty queryset when no relations exist."""
        obj = TestModel.objects.create(title="Test")

        categories = obj.categories.all()
        assert categories.count() == 0

    def test_categories_property_returns_related_categories(self) -> None:
        """Test that categories property returns related categories."""
        obj = TestModel.objects.create(title="Test")
        content_type = ContentType.objects.get_for_model(TestModel)

        # Create relations
        CategoryRelation.objects.create(
            category=self.cat1,
            content_type=content_type,
            object_id=obj.pk,
            order=0,
        )
        CategoryRelation.objects.create(
            category=self.cat2,
            content_type=content_type,
            object_id=obj.pk,
            order=1,
        )

        # Get categories
        categories = obj.categories.all()

        assert categories.count() == 2
        assert self.cat1 in categories
        assert self.cat2 in categories
        assert self.cat3 not in categories

    def test_categories_property_multiple_objects(self) -> None:
        """Test that categories are correctly isolated between objects."""
        obj1 = TestModel.objects.create(title="Test 1")
        obj2 = TestModel.objects.create(title="Test 2")
        content_type = ContentType.objects.get_for_model(TestModel)

        # Create relations for obj1
        CategoryRelation.objects.create(
            category=self.cat1,
            content_type=content_type,
            object_id=obj1.pk,
            order=0,
        )

        # Create relations for obj2
        CategoryRelation.objects.create(
            category=self.cat2,
            content_type=content_type,
            object_id=obj2.pk,
            order=0,
        )
        CategoryRelation.objects.create(
            category=self.cat3,
            content_type=content_type,
            object_id=obj2.pk,
            order=1,
        )

        # Verify obj1 has only cat1
        categories1 = obj1.categories.all()
        assert categories1.count() == 1
        assert self.cat1 in categories1

        # Verify obj2 has cat2 and cat3
        categories2 = obj2.categories.all()
        assert categories2.count() == 2
        assert self.cat2 in categories2
        assert self.cat3 in categories2

    def test_categories_property_before_save(self) -> None:
        """Test that categories returns empty queryset for unsaved objects."""
        obj = TestModel(title="Test")

        # Should return empty queryset for unsaved object
        categories = obj.categories.all()
        assert categories.count() == 0

    def test_categories_property_queryset_methods(self) -> None:
        """Test that returned queryset supports standard QuerySet methods."""
        obj = TestModel.objects.create(title="Test")
        content_type = ContentType.objects.get_for_model(TestModel)

        # Create relations
        CategoryRelation.objects.create(
            category=self.cat1,
            content_type=content_type,
            object_id=obj.pk,
            order=0,
        )
        CategoryRelation.objects.create(
            category=self.cat2,
            content_type=content_type,
            object_id=obj.pk,
            order=1,
        )

        # Test filter
        filtered = obj.categories.filter(slug="cat1")
        assert filtered.count() == 1
        assert filtered.first() == self.cat1

        # Test values
        names = list(obj.categories.values_list("slug", flat=True))
        assert "cat1" in names
        assert "cat2" in names

        # Test exists
        assert obj.categories.exists()

    def test_categories_property_with_hierarchical_categories(self) -> None:
        """Test categories property with hierarchical category structure."""
        # Create parent category
        parent = Category.objects.create(slug="parent")
        parent.set_current_language("en")
        parent.name = "Parent"
        parent.save()

        # Create child category
        child = Category.objects.create(slug="child", parent=parent)
        child.set_current_language("en")
        child.name = "Child"
        child.save()

        obj = TestModel.objects.create(title="Test")
        content_type = ContentType.objects.get_for_model(TestModel)

        # Relate to child category
        CategoryRelation.objects.create(
            category=child,
            content_type=content_type,
            object_id=obj.pk,
            order=0,
        )

        # Get categories
        categories = obj.categories.all()

        assert categories.count() == 1
        assert child in categories
        assert parent not in categories
