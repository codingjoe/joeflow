import importlib
import inspect
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.testapp.settings")
sys.path.insert(0, os.path.abspath(".."))
django.setup()

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.intersphinx",
    "sphinx.ext.githubpages",
    "sphinx.ext.linkcode",
]

try:
    import sphinxcontrib.spelling  # noqa
except ImportError:
    pass
else:
    extensions.append("sphinxcontrib.spelling")


def linkcode_resolve(domain, info):
    """Link source code to GitHub."""
    project = "joeflow"
    github_user = "codingjoe"
    head = "master"

    if domain != "py" or not info["module"]:
        return None
    filename = info["module"].replace(".", "/")
    mod = importlib.import_module(info["module"])
    basename = os.path.splitext(mod.__file__)[0]
    if basename.endswith("__init__"):
        filename += "/__init__"
    item = mod
    lineno = ""

    for piece in info["fullname"].split("."):
        try:
            item = getattr(item, piece)
        except AttributeError:
            pass
        try:
            lines, first_line = inspect.getsourcelines(item)
            lineno = "#L%d-L%s" % (first_line, first_line + len(lines) - 1)
        except (TypeError, IOError):
            pass
    return "https://github.com/%s/%s/blob/%s/%s.py%s" % (
        github_user,
        project,
        head,
        filename,
        lineno,
    )


# The master toctree document.
master_doc = "index"
project = "Joeflow"

html_theme = "alabaster"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": (
        "https://docs.djangoproject.com/en/stable/",
        "https://docs.djangoproject.com/en/stable/_objects/",
    ),
    "dramatiq": ("https://dramatiq.io/", None),
    "celery": ("https://docs.celeryproject.org/en/stable/", None),
    "graphviz": ("https://graphviz.readthedocs.io/en/stable/", None),
}

spelling_word_list_filename = "spelling_wordlist.txt"
spelling_show_suggestions = True

graphviz_output_format = "svg"

inheritance_graph_attrs = dict(
    rankdir="TB", size='"6.0, 8.0"', fontsize=14, ratio="compress"
)
