import types
from collections import defaultdict

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
    """
    Like `.graphviz.Digraph` but with unique nodes and edges.

    Nodes and edges are unique and their attributes will be overridden
    should the same node or edge be added twice. Nodes are unique by name
    and edges unique by head and tail.

    Underscores are replaced with whitespaces from identifiers.
    """

    def __init__(self, *args, **kwargs):
        self._nodes = defaultdict(dict)
        self._edges = defaultdict(dict)
        super().__init__(*args, **kwargs)

    def __iter__(self, subgraph=False):
        """Yield the DOT source code line by line (as graph or subgraph)."""
        if self.comment:
            yield self._comment(self.comment)

        if subgraph:
            if self.strict:
                raise ValueError("subgraphs cannot be strict")
            head = self._subgraph if self.name else self._subgraph_plain
        else:
            head = self._head_strict if self.strict else self._head
        yield head(self._quote(self.name) + " " if self.name else "")

        for kw in ("graph", "node", "edge"):
            attrs = getattr(self, "%s_attr" % kw)
            if attrs:
                yield self._attr(kw, self._attr_list(None, attrs))

        yield from self.body

        for name, attrs in sorted(self._nodes.items()):
            name = self._quote(name)
            label = attrs.pop("label", None)
            _attributes = attrs.pop("_attributes", None)
            attr_list = self._attr_list(label, attrs, _attributes)
            yield self._node(name, attr_list)

        for edge, attrs in sorted(self._edges.items()):
            tail_name, head_name = edge
            tail_name = self._quote_edge(tail_name)
            head_name = self._quote_edge(head_name)
            label = attrs.pop("label", None)
            _attributes = attrs.pop("_attributes", None)
            attr_list = self._attr_list(label, attrs, _attributes)
            yield self._edge(tail=tail_name, head=head_name, attr=attr_list)

        yield self._tail

    def node(self, name, **attrs):
        self._nodes[name] = attrs

    def edge(self, tail_name, head_name, **attrs):
        self._edges[(tail_name, head_name)] = attrs

    @staticmethod
    def _quote(identifier, *args, **kwargs):
        """Remove underscores from labels."""
        identifier = identifier.replace("_", " ")
        return gv.quoting.quote(identifier, *args, **kwargs)

    @staticmethod
    def _quote_edge(identifier):
        """Remove underscores from labels."""
        identifier = identifier.replace("_", " ")
        return gv.quoting.quote_edge(identifier)
