"""Integration tests for CategoryMixin and CategoryAdminMixin working together."""

import pytest
from django.contrib.contenttypes.models import ContentType

from djangocms_taxonomy.models import Category, CategoryRelation
from tests.test_app.models import TestModel


@pytest.mark.django_db
class TestMixinIntegration:
    """Test CategoryMixin and CategoryAdminMixin working together."""

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

    def test_model_mixin_provides_categories_property(self) -> None:
        """Test that CategoryMixin provides categories property."""
        obj = TestModel.objects.create(title="Test")

        # Verify it has the categories property
        assert hasattr(obj, "categories")
        assert hasattr(obj.categories, "all")

    def test_categories_accessible_via_mixin_after_relation_creation(self) -> None:
        """Test that categories are accessible via mixin after creating relations."""
        # Create object
        obj = TestModel.objects.create(title="Test")
        content_type = ContentType.objects.get_for_model(TestModel)

        # Create relations manually (as admin would)
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

        # Verify accessible via mixin property
        categories = obj.categories.all()
        assert categories.count() == 2
        assert self.cat1 in categories
        assert self.cat2 in categories

    def test_mixin_reflects_relation_updates(self) -> None:
        """Test that mixin property reflects relation updates."""
        obj = TestModel.objects.create(title="Test")
        content_type = ContentType.objects.get_for_model(TestModel)

        # Create initial relation
        CategoryRelation.objects.create(
            category=self.cat1,
            content_type=content_type,
            object_id=obj.pk,
            order=0,
        )

        # Verify initial state
        assert obj.categories.count() == 1
        assert self.cat1 in obj.categories.all()

        # Update relations (clear and add new)
        CategoryRelation.objects.filter(
            content_type=content_type,
            object_id=obj.pk,
        ).delete()

        CategoryRelation.objects.create(
            category=self.cat2,
            content_type=content_type,
            object_id=obj.pk,
            order=0,
        )
        CategoryRelation.objects.create(
            category=self.cat3,
            content_type=content_type,
            object_id=obj.pk,
            order=1,
        )

        # Verify updated state via mixin
        categories = obj.categories.all()
        assert categories.count() == 2
        assert self.cat2 in categories
        assert self.cat3 in categories
        assert self.cat1 not in categories

    def test_mixin_with_no_relations(self) -> None:
        """Test that mixin returns empty queryset when no relations exist."""
        obj = TestModel.objects.create(title="Test")

        categories = obj.categories.all()
        assert categories.count() == 0
        assert not categories.exists()

    def test_mixin_with_unsaved_object(self) -> None:
        """Test that mixin handles unsaved objects gracefully."""
        obj = TestModel(title="Test")

        # Should return empty queryset for unsaved object
        categories = obj.categories.all()
        assert categories.count() == 0
