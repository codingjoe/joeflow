import contextlib
import importlib
import inspect
import os
import sys
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.testapp.settings")
sys.path.insert(0, str(Path("..").resolve()))
django.setup()

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
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
    head = "main"

    if domain != "py" or not info["module"]:
        return None
    filename = info["module"].replace(".", "/")
    mod = importlib.import_module(info["module"])
    basename = Path(mod.__file__).with_suffix("")
    if str(basename).endswith("__init__"):
        filename += "/__init__"
    item = mod
    lineno = ""

    for piece in info["fullname"].split("."):
        with contextlib.suppress(AttributeError):
            item = getattr(item, piece)
        try:
            lines, first_line = inspect.getsourcelines(item)
            lineno = f"#L{first_line:d}-L{first_line + len(lines) - 1:d}"
        except TypeError, OSError:
            pass
    return (
        f"https://github.com/{github_user}/{project}/blob/{head}/{filename}.py{lineno}"
    )


# The master toctree document.
master_doc = "index"
project = "Joeflow"

html_theme = "furo"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": (
        "https://docs.djangoproject.com/en/stable/",
        "https://docs.djangoproject.com/en/stable/_objects/",
    ),
    "graphviz": ("https://graphviz.readthedocs.io/en/stable/", None),
}

spelling_word_list_filename = "spelling_wordlist.txt"
spelling_show_suggestions = True

graphviz_output_format = "svg"

inheritance_graph_attrs = {
    "rankdir": "TB",
    "size": '"6.0, 8.0"',
    "fontsize": 14,
    "ratio": "compress",
}
