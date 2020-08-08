import types

import graphviz as gv


def get_workflows() -> types.GeneratorType:
    """Return all registered workflows."""
    from django.apps import apps

    from .models import Workflow

    apps.check_models_ready()
    for model in apps.get_models():
        if issubclass(model, Workflow) and model is not Workflow and model.edges:
            yield model


def get_workflow(name):
    for workflow_cls in get_workflows():
        if (
            name.lower()
            == f"{workflow_cls._meta.app_label}.{workflow_cls.__name__}".lower()
        ):
            return workflow_cls


class NoDashDiGraph(gv.Digraph):
    """Like `.graphviz.Digraph` but removes underscores from labels."""

    def __init__(self, *args, **kwargs):
        self._edges = []
        super().__init__(*args, **kwargs)

    def edge(self, tail_name, head_name, label=None, _attributes=None, **attrs):
        if not (tail_name, head_name) in self._edges:
            self._edges.append((tail_name, head_name))
            super().edge(
                tail_name, head_name, label=label, _attributes=_attributes, **attrs
            )

    @staticmethod
    def _quote(identifier, *args, **kwargs):
        """Remove underscores from labels."""
        identifier = identifier.replace("_", " ")
        return gv.lang.quote(identifier, *args, **kwargs)

    @staticmethod
    def _quote_edge(identifier):
        """Remove underscores from labels."""
        identifier = identifier.replace("_", " ")
        return gv.lang.quote_edge(identifier)
