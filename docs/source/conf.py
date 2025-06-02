# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('../../'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'thinFTP'
copyright = '2025, M.V. Harish Kumar'
author = 'M.V. Harish Kumar'
release = '0.1.0'
version = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx_autodoc_typehints',
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = []

# -- Autodoc configuration --------------------------------------------------
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

autosummary_generate = True

# -- Napoleon settings -------------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# -- Intersphinx mapping ----------------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
}

# -- MyST configuration -----------------------------------------------------
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_image",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']

# -- PyData theme configuration ---------------------------------------------
html_theme_options = {
    "logo": {
        "text": "thinFTP",
    },
    "use_edit_page_button": True,
    "show_toc_level": 1,
    "navbar_align": "left",
    "navbar_center": ["navbar-nav"],
    "navbar_persistent": ["search-button"],
    "footer_start": ["copyright"],
    "footer_end": ["sphinx-version"],
    "pygments_light_style": "default",
    "pygments_dark_style": "github-dark",
    # Hide the left sidebar to avoid redundancy with right sidebar TOC
    "show_prev_next": False,
    "primary_sidebar_end": [],
    "secondary_sidebar_items": ["page-toc", "edit-this-page"],
}

html_context = {
    "github_user": "harishtpj",  # Update with your GitHub username
    "github_repo": "thinftp",   # Update with your repo name
    "github_version": "main",
    "doc_path": "docs/source",
}

# The master toctree document.
master_doc = 'index'

# Custom CSS files
html_css_files = [
    'custom.css',
]
