"""Tests for CategoryAdminMixin."""

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory

from djangocms_taxonomy.admin_mixins import CategoryAdminMixin
from djangocms_taxonomy.models import Category, CategoryRelation
from tests.test_app.models import TestModel


User = get_user_model()


@pytest.mark.django_db
class TestCategoryAdminMixin:
    """Test CategoryAdminMixin functionality."""

    def setup_method(self) -> None:
        """Set up test data."""
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="password",
        )

        # Create test categories
        self.cat1 = Category.objects.create(slug="cat1")
        self.cat1.set_current_language("en")
        self.cat1.name = "Category 1"
        self.cat1.save()

        self.cat2 = Category.objects.create(slug="cat2")
        self.cat2.set_current_language("en")
        self.cat2.name = "Category 2"
        self.cat2.save()

    def test_mixin_adds_fieldsets(self) -> None:
        """Test that mixin provides get_fieldsets method."""
        from tests.test_app.admin import TestModelAdmin

        admin_instance = TestModelAdmin(TestModel, AdminSite())

        # Check that the mixin is applied
        assert isinstance(admin_instance, CategoryAdminMixin)

        # Check that it has the get_fieldsets method from the mixin
        assert hasattr(admin_instance, "get_fieldsets")
        assert callable(admin_instance.get_fieldsets)

    def test_mixin_saves_categories_via_relation(self) -> None:
        """Test that categories can be saved via CategoryRelation."""
        # Create a test object
        obj = TestModel.objects.create(title="Test")

        # Create category relations
        content_type = ContentType.objects.get_for_model(TestModel)
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

        # Verify relations were created
        relations = CategoryRelation.objects.filter(
            content_type=content_type,
            object_id=obj.pk,
        ).order_by("order")

        assert relations.count() == 2
        assert relations[0].category_id == self.cat1.id
        assert relations[1].category_id == self.cat2.id

    def test_mixin_updates_categories_via_relation(self) -> None:
        """Test that category relations can be updated."""
        # Create a test object with categories
        obj = TestModel.objects.create(title="Test")
        content_type = ContentType.objects.get_for_model(TestModel)

        # Create initial relation
        CategoryRelation.objects.create(
            category=self.cat1,
            content_type=content_type,
            object_id=obj.pk,
            order=0,
        )

        # Update to cat2
        relation = CategoryRelation.objects.get(
            content_type=content_type,
            object_id=obj.pk,
        )
        relation.category = self.cat2
        relation.save()

        # Verify update
        updated_relation = CategoryRelation.objects.get(
            content_type=content_type,
            object_id=obj.pk,
        )
        assert updated_relation.category_id == self.cat2.id

    def test_mixin_clears_categories_via_relation(self) -> None:
        """Test that category relations can be cleared."""
        # Create a test object with categories
        obj = TestModel.objects.create(title="Test")
        content_type = ContentType.objects.get_for_model(TestModel)

        CategoryRelation.objects.create(
            category=self.cat1,
            content_type=content_type,
            object_id=obj.pk,
            order=0,
        )

        # Delete relations
        CategoryRelation.objects.filter(
            content_type=content_type,
            object_id=obj.pk,
        ).delete()

        # Verify all relations were removed
        relations = CategoryRelation.objects.filter(
            content_type=content_type,
            object_id=obj.pk,
        )

        assert relations.count() == 0

    def test_queryset_with_tree_fields_for_category_selection(self) -> None:
        """Test that categories can be queried with tree fields for selection."""
        # Create hierarchical categories
        parent = Category.objects.create(slug="parent")
        parent.set_current_language("en")
        parent.name = "Parent"
        parent.save()

        child = Category.objects.create(slug="child", parent=parent)
        child.set_current_language("en")
        child.name = "Child"
        child.save()

        # Query with tree fields
        qs = Category.objects.all().with_tree_fields()

        assert qs.count() >= 2
        assert all(hasattr(obj, "depth") for obj in qs)
        assert all(hasattr(obj, "path") for obj in qs)
