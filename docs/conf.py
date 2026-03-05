# Configuration file for the Sphinx documentation builder.

project = "python-package-copier-template"
copyright = "2026, Martín Gaitán"
author = "Martín Gaitán"

extensions = [
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_book_theme"
html_static_path = ["_static"]

myst_url_schemes = {
    "http": None,
    "https": None,
    "gh": {
        "url": "https://github.com/mgaitan/python-package-copier-template/blob/main/{path}#{fragment}",
        "title": "",
        "classes": ["github"],
    },
}
