import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

project = "Contact_app"
copyright = "2023, Olexandr"
author = "Olexandr"
release = "0.1"


extensions = ["sphinx.ext.autodoc"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


html_theme = "sphinxdoc"
html_static_path = ["_static"]
