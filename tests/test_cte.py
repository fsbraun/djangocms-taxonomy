"""Tests for CTE-based tree queries."""
import pytest
from djangocms_taxonomy.models import Category


@pytest.mark.django_db
class TestCategoryTreeQueries:
    """Test CTE-based hierarchical queries."""

    def test_with_tree_fields_root_only(self):
        """Test tree fields annotation with root category."""
        root = Category.objects.create(slug="root")
        root.set_current_language("en")
        root.name = "Root"
        root.save()

        categories = Category.objects.with_tree_fields()

        assert categories.count() == 1
        cat = categories.first()
        assert cat.path == "Root"
        assert cat.depth == 0

    def test_with_tree_fields_hierarchy(self):
        """Test tree fields annotation with multi-level hierarchy."""
        root = Category.objects.create(slug="electronics")
        root.set_current_language("en")
        root.name = "Electronics"
        root.save()

        child1 = Category.objects.create(slug="computers", parent=root)
        child1.set_current_language("en")
        child1.name = "Computers"
        child1.save()

        child2 = Category.objects.create(slug="phones", parent=root)
        child2.set_current_language("en")
        child2.name = "Phones"
        child2.save()

        grandchild = Category.objects.create(slug="laptops", parent=child1)
        grandchild.set_current_language("en")
        grandchild.name = "Laptops"
        grandchild.save()

        categories = list(Category.objects.with_tree_fields())

        # Should be 4 categories
        assert len(categories) == 4

        # Check they are ordered by path (hierarchically)
        paths = [cat.path for cat in categories]
        assert paths == [
            "Electronics",
            "Electronics/computers",
            "Electronics/computers/laptops",
            "Electronics/phones",
        ]

        # Check depths
        depths = {cat.name: cat.depth for cat in categories}
        assert depths["Electronics"] == 0
        assert depths["Computers"] == 1
        assert depths["Phones"] == 1
        assert depths["Laptops"] == 2

    def test_with_tree_fields_multiple_roots(self):
        """Test tree fields with multiple root categories."""
        root1 = Category.objects.create(slug="books")
        root1.set_current_language("en")
        root1.name = "Books"
        root1.save()

        root2 = Category.objects.create(slug="movies")
        root2.set_current_language("en")
        root2.name = "Movies"
        root2.save()

        child1 = Category.objects.create(slug="fiction", parent=root1)
        child1.set_current_language("en")
        child1.name = "Fiction"
        child1.save()

        child2 = Category.objects.create(slug="action", parent=root2)
        child2.set_current_language("en")
        child2.name = "Action"
        child2.save()

        categories = list(Category.objects.with_tree_fields())

        assert len(categories) == 4

        # Verify ordering keeps children under parents
        paths = [cat.path for cat in categories]
        assert paths == [
            "Books",
            "Books/fiction",
            "Movies",
            "Movies/action",
        ]

    def test_with_tree_fields_filter_by_depth(self):
        """Test filtering annotated queryset by depth."""
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

        # Get only depth 1 categories
        depth_1 = Category.objects.with_tree_fields().filter(depth=1)

        assert depth_1.count() == 1
        assert depth_1.first().name == "Child"

    def test_with_tree_fields_order_by_path(self):
        """Test that results are ordered by path by default."""
        # Create in random order
        cat_b = Category.objects.create(slug="b")
        cat_b.set_current_language("en")
        cat_b.name = "B"
        cat_b.save()

        cat_a = Category.objects.create(slug="a")
        cat_a.set_current_language("en")
        cat_a.name = "A"
        cat_a.save()

        cat_c = Category.objects.create(slug="c")
        cat_c.set_current_language("en")
        cat_c.name = "C"
        cat_c.save()

        categories = list(Category.objects.with_tree_fields())
        names = [cat.name for cat in categories]

        # Should be alphabetically ordered by path (which equals name for roots)
        assert names == ["A", "B", "C"]

    def test_roots_queryset(self):
        """Test roots() queryset method."""
        root1 = Category.objects.create(slug="root1")
        root1.set_current_language("en")
        root1.name = "Root1"
        root1.save()

        root2 = Category.objects.create(slug="root2")
        root2.set_current_language("en")
        root2.name = "Root2"
        root2.save()

        child = Category.objects.create(slug="child", parent=root1)
        child.set_current_language("en")
        child.name = "Child"
        child.save()

        roots = Category.objects.roots()

        assert roots.count() == 2
        assert set(roots.values_list("translations__name", flat=True)) == {"Root1", "Root2"}

    def test_leaves_queryset(self):
        """Test leaves() queryset method."""
        root = Category.objects.create(slug="root")
        root.set_current_language("en")
        root.name = "Root"
        root.save()

        child1 = Category.objects.create(slug="child1", parent=root)
        child1.set_current_language("en")
        child1.name = "Child1"
        child1.save()

        child2 = Category.objects.create(slug="child2", parent=root)
        child2.set_current_language("en")
        child2.name = "Child2"
        child2.save()

        grandchild = Category.objects.create(slug="grandchild", parent=child1)
        grandchild.set_current_language("en")
        grandchild.name = "Grandchild"
        grandchild.save()

        leaves = Category.objects.leaves()

        # Child2 and Grandchild are leaves (no children)
        assert leaves.count() == 2
        assert set(leaves.values_list("translations__name", flat=True)) == {"Child2", "Grandchild"}

    def test_with_tree_fields_preserves_all_fields(self):
        """Test that with_tree_fields preserves all model fields."""
        root = Category.objects.create(slug="test")
        root.set_current_language("en")
        root.name = "Test"
        root.description = "Test description"
        root.save()

        cat = Category.objects.with_tree_fields().first()

        assert cat.name == "Test"
        assert cat.slug == "test"
        assert cat.description == "Test description"
        assert hasattr(cat, "path")
        assert hasattr(cat, "depth")

    def test_descendants_of_returns_all_descendants(self):
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

        descendants = Category.objects.descendants_of(root)
        assert set(descendants.values_list("slug", flat=True)) == {"child", "grandchild"}

    def test_descendants_of_include_self(self):
        root = Category.objects.create(slug="root")
        root.set_current_language("en")
        root.name = "Root"
        root.save()

        child = Category.objects.create(slug="child", parent=root)
        child.set_current_language("en")
        child.name = "Child"
        child.save()

        descendants = Category.objects.descendants_of(root, include_self=True)
        assert set(descendants.values_list("slug", flat=True)) == {"root", "child"}
