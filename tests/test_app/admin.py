from django.contrib import admin

from djangocms_taxonomy.mixins import CategoryAdminMixin

from .models import TestModel


@admin.register(TestModel)
class TestModelAdmin(CategoryAdminMixin, admin.ModelAdmin):
    list_display = ("title", "description")
    search_fields = ("title",)
