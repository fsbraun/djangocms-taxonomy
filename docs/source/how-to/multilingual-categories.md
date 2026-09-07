# Work with Multilingual Categories

Manage categories in multiple languages using django-parler.

## Setup

Ensure django-parler is installed and configured:

```python
# settings.py

INSTALLED_APPS = [
    "parler",
    "djangocms_taxonomy",
]

LANGUAGES = [
    ("en", "English"),
    ("de", "Deutsch"),
    ("fr", "Français"),
]

PARLER_LANGUAGES = {
    None: (
        {"code": "en"},
        {"code": "de"},
        {"code": "fr"},
    ),
    "default": {
        "fallback": "en",
        "hide_untranslated": False,
    },
}
```

## Creating Translations

### In Python Code

```python
from djangocms_taxonomy.models import Category

# Create a category with English name
category = Category.objects.create(name="Django", slug="django")

# Add translations
category.translations.create(
    language_code="de",
    name="Django",  # German translation
)

category.translations.create(
    language_code="fr",
    name="Django",  # French translation
)
```

### In Django Admin

The Category admin automatically includes translation fields:

1. Go to Categories admin
2. Select a category to edit
3. Scroll to the "Translations" section
4. Click "Add translation" to add a new language
5. Enter the translated name and description

## Accessing Translations

### Get Current Language Translation

```python
from django.utils.translation import get_language

category = Category.objects.get(slug="django")

# Get name in current language
current_name = category.name  # Uses current language

# Access specific language
de_name = category.safe_translation_getter("name", language_code="de")
```

### List All Translations

```python
category = Category.objects.get(slug="django")

for translation in category.translations.all():
    print(f"{translation.language_code}: {translation.name}")
```

### Filter by Translated Field

```python
# Find categories with a specific name in a language
from parler.utils.context import switch_language

categories = Category.objects.language("de").filter(name="Python")
```

## Templates with Translations

```html
{# Auto-detect current language #}
<h3>{{ category.name }}</h3>
<p>{{ category.description }}</p>

{# Explicitly set language #}
{% load i18n %}
<ul>
    {% for lang_code, lang_name in LANGUAGES %}
        <li>
            <a href="?lang={{ lang_code }}">
                {{ lang_name }}
                {% if lang_code == LANGUAGE_CODE %}(current){% endif %}
            </a>
        </li>
    {% endfor %}
</ul>

{% for category in categories %}
    <div class="category">
        <h4>{{ category.name }}</h4>
        <p>{{ category.description }}</p>
    </div>
{% endfor %}
```

## Language Switching in Views

```python
from django.views.generic import DetailView
from django.utils.translation import activate
from parler.utils.context import switch_language
from djangocms_taxonomy.models import Category


class CategoryDetailView(DetailView):
    model = Category
    slug_field = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Ensure translations are available for all languages
        category = self.get_object()
        context["translations"] = {}

        for lang_code, lang_name in self.request.LANGUAGES:
            with switch_language(category, lang_code):
                context["translations"][lang_code] = {
                    "name": category.name,
                    "description": category.description,
                }

        return context
```

## Fallback Languages

Configure fallback behavior in settings:

```python
PARLER_LANGUAGES = {
    None: (
        {"code": "en"},
        {"code": "de"},
        {"code": "fr"},
    ),
    "default": {
        "fallback": "en",  # Fall back to English if translation missing
        "hide_untranslated": False,  # Show categories even if untranslated
    },
}
```

This ensures that if a category doesn't have a German translation, it will show the English name instead.
