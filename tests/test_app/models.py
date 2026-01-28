from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from djangocms_taxonomy.mixins import CategoryMixin


class TestModel(CategoryMixin, models.Model):
    """
    A test model to verify generic foreign key functionality with Category.
    """

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Generic foreign key for testing
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        app_label = "test_app"

    def __str__(self):
        return self.title
