"""Tests for admin interface."""
import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from djangocms_taxonomy.admin import CategoryAdmin
from djangocms_taxonomy.models import Category


User = get_user_model()


@pytest.mark.django_db
class TestCategoryAdmin:
    """Test CategoryAdmin interface."""

    def setup_method(self):
        """Set up test data."""
        self.site = AdminSite()
        self.admin = CategoryAdmin(Category, self.site)
        self.factory = RequestFactory()

        # Create test user
        self.user = User.objects.create_superuser(username="admin", email="admin@test.com", password="password")

    def test_admin_registered(self):
        """Test that CategoryAdmin is properly registered."""
        assert isinstance(self.admin, CategoryAdmin)
        assert self.admin.model == Category

    def test_list_display(self):
        """Test list_display configuration."""
        expected = ["indented_name", "slug", "parent", "date_created"]
        assert self.admin.list_display == expected

    def test_search_fields(self):
        """Test search_fields configuration."""
        assert "translations__name" in self.admin.search_fields
        assert "slug" in self.admin.search_fields

    def test_get_queryset_adds_tree_fields(self):
        """Test that get_queryset adds CTE annotations."""
        # Create hierarchical categories
        root = Category.objects.create(slug="root")
        root.set_current_language("en")
        root.name = "Root"
        root.save()

        child = Category.objects.create(slug="child", parent=root)
        child.set_current_language("en")
        child.name = "Child"
        child.save()

        # Get queryset through admin
        request = self.factory.get("/admin/djangocms_taxonomy/category/")
        request.user = self.user

        qs = self.admin.get_queryset(request)

        # Should have tree fields annotations
        first_obj = qs.first()
        assert hasattr(first_obj, "path")
        assert hasattr(first_obj, "depth")

    def test_indented_name_root_category(self):
        """Test indented_name for root category (depth 0)."""
        root = Category.objects.create(slug="root")
        root.set_current_language("en")
        root.name = "Root Category"
        root.save()

        # Fetch with tree fields
        request = self.factory.get("/admin/djangocms_taxonomy/category/")
        request.user = self.user
        qs = self.admin.get_queryset(request)
        obj = qs.get(slug="root")

        result = self.admin.indented_name(obj)
        # Root should have no indentation
        assert "Root Category" in result
        assert obj.depth == 0

    def test_indented_name_child_category(self):
        """Test indented_name for child category (depth 1)."""
        root = Category.objects.create(slug="root")
        root.set_current_language("en")
        root.name = "Root"
        root.save()

        child = Category.objects.create(slug="child", parent=root)
        child.set_current_language("en")
        child.name = "Child Category"
        child.save()

        # Fetch with tree fields
        request = self.factory.get("/admin/djangocms_taxonomy/category/")
        request.user = self.user
        qs = self.admin.get_queryset(request)
        obj = qs.get(slug="child")

        result = self.admin.indented_name(obj)
        # Child should have indentation (4 non-breaking spaces per level)
        assert "Child Category" in result
        assert "&nbsp;" in result
        assert obj.depth == 1

    def test_indented_name_grandchild_category(self):
        """Test indented_name for grandchild category (depth 2)."""
        root = Category.objects.create(slug="root")
        root.set_current_language("en")
        root.name = "Root"
        root.save()

        child = Category.objects.create(slug="child", parent=root)
        child.set_current_language("en")
        child.name = "Child"
        child.save()

        grandchild = Category.objects.create(slug="grandchild", parent=child)
        grandchild.set_current_language("en")
        grandchild.name = "Grandchild"
        grandchild.save()

        # Fetch with tree fields
        request = self.factory.get("/admin/djangocms_taxonomy/category/")
        request.user = self.user
        qs = self.admin.get_queryset(request)
        obj = qs.get(slug="grandchild")

        result = self.admin.indented_name(obj)
        # Grandchild should have double indentation
        assert "Grandchild" in result
        assert obj.depth == 2

    def test_queryset_ordering(self):
        """Test that queryset is ordered hierarchically by path."""
        # Create categories in random order
        child_b = Category.objects.create(slug="b-child")
        child_b.set_current_language("en")
        child_b.name = "B Child"
        child_b.save()

        root_a = Category.objects.create(slug="a-root")
        root_a.set_current_language("en")
        root_a.name = "A Root"
        root_a.save()

        child_a = Category.objects.create(slug="a-child", parent=root_a)
        child_a.set_current_language("en")
        child_a.name = "A Child"
        child_a.save()

        root_b = Category.objects.create(slug="b-root")
        root_b.set_current_language("en")
        root_b.name = "B Root"
        root_b.save()

        child_b.parent = root_b
        child_b.save()

        # Get queryset through admin
        request = self.factory.get("/admin/djangocms_taxonomy/category/")
        request.user = self.user
        qs = self.admin.get_queryset(request)

        names = [obj.name for obj in qs]

        # Should be ordered: A Root, A Child, B Root, B Child
        assert names == ["A Root", "A Child", "B Root", "B Child"]

    def test_prepopulated_fields(self):
        """Test that slug is prepopulated from name."""
        assert "slug" in self.admin.prepopulated_fields
        assert self.admin.prepopulated_fields["slug"] == ("name",)

    def test_parent_field_excludes_self_and_descendants(self):
        """Parent selection must not allow cycles (self/descendants)."""
        root = Category.objects.create(slug="root")
        root.set_current_language("en")
        root.name = "Root"
        root.save()

        child = Category.objects.create(slug="child", parent=root)
        child.set_current_language("en")
        child.name = "Child"
        child.save()

        grandchild = Category.objects.create(slug="grandchild", parent=child)
        grandchild.set_current_language("en")
        grandchild.name = "Grandchild"
        grandchild.save()

        other_root = Category.objects.create(slug="other")
        other_root.set_current_language("en")
        other_root.name = "Other"
        other_root.save()

        request = self.factory.get(f"/admin/djangocms_taxonomy/category/{child.pk}/change/")
        request.user = self.user

        form_class = self.admin.get_form(request, obj=child)
        form = form_class(instance=child)

        parent_qs = form.fields["parent"].queryset
        assert root in parent_qs
        assert other_root in parent_qs
        assert child not in parent_qs
        assert grandchild not in parent_qs

    def test_parent_autocomplete_search_excludes_self_and_descendants(self):
        root = Category.objects.create(slug="root")
        root.set_current_language("en")
        root.name = "Root"
        root.save()

        child = Category.objects.create(slug="child", parent=root)
        child.set_current_language("en")
        child.name = "Child"
        child.save()

        grandchild = Category.objects.create(slug="grandchild", parent=child)
        grandchild.set_current_language("en")
        grandchild.name = "Grandchild"
        grandchild.save()

        other_root = Category.objects.create(slug="other")
        other_root.set_current_language("en")
        other_root.name = "Other"
        other_root.save()

        request = self.factory.get(
            "/admin/autocomplete/",
            {
                "app_label": "djangocms_taxonomy",
                "model_name": "category",
                "field_name": "parent",
                "term": "",
            },
        )
        request.user = self.user
        request.META["HTTP_REFERER"] = f"/admin/djangocms_taxonomy/category/{child.pk}/change/"

        qs, _use_distinct = self.admin.get_search_results(request, Category.objects.all(), "")
        assert child not in qs
        assert grandchild not in qs
        assert root in qs
        assert other_root in qs
