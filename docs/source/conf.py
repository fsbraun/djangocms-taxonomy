# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.abspath("../../"))

# -- Django setup (required for autodoc importing Django modules) ---------
# Default to the test settings which are self-contained for this repo.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

try:
    import django

    django.setup()
except Exception as exc:
    # Keep docs importable even when Django isn't available (e.g. readthedocs
    # misconfiguration). Autodoc pages that import Django code may fail.
    print(f"WARNING: Django could not be initialized for autodoc: {exc}")

from djangocms_taxonomy import __version__

# -- Project information -------------------------------------------------------
project = "django CMS Taxonomy"
copyright = "2026, Fabian Braun"
author = "Fabian Braun"
release = __version__

# -- General configuration -------------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output ---------------------------------------------------
html_theme = "furo"
html_static_path = ["_static"]
html_theme_options = {
    "sidebar_hide_name": False,
    "light_css_variables": {
        "color-brand-primary": "#0066cc",
        "color-brand-content": "#0066cc",
    },
}

# MyST configuration
myst_enable_extensions = [
    "colon_fence",
    "linkify",
]

# -- Autodoc configuration ----------------------------------------------------
autodoc_typehints = "description"
autodoc_member_order = "bysource"
