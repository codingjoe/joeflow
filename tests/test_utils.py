from joeflow.utils import NoDashDiGraph


class TestNoDashDiGraph:
    def test_node(self):
        graph = NoDashDiGraph()
        graph.node("foo", color="blue")
        assert list(graph) == [
            "digraph {",
            "\tfoo [color=blue]",
            "}",
        ]
        graph.node("foo", color="red")
        assert list(graph) == [
            "digraph {",
            "\tfoo [color=red]",
            "}",
        ]

    def test_edge(self):
        graph = NoDashDiGraph()
        graph.edge("foo", "bar", color="blue")
        assert list(graph) == [
            "digraph {",
            "\tfoo -> bar [color=blue]",
            "}",
        ]
        graph.edge("foo", "bar", color="red")
        assert list(graph) == [
            "digraph {",
            "\tfoo -> bar [color=red]",
            "}",
        ]

    def test_iter(self):
        graph = NoDashDiGraph(node_attr={"style": "filled"})
        graph.node("foo", color="red")
        graph.node("bar", color="green")
        graph.edge("foo", "bar", color="blue")
        graph.comment = "This is a comment."
        print(str(graph))
        assert list(graph.__iter__()) == [
            "// This is a comment.",
            "digraph {",
            "\tnode [style=filled]",
            "\tbar [color=green]",
            "\tfoo [color=red]",
            "\tfoo -> bar [color=blue]",
            "}",
        ]

    def test_iter__subgraph(self):
        graph = NoDashDiGraph(node_attr={"style": "filled"})
        graph.node("foo", color="red")
        graph.node("bar", color="green")
        graph.edge("foo", "bar", color="blue")
        graph.comment = "This is a comment."
        print(str(graph))
        assert list(graph.__iter__(subgraph=True)) == [
            "// This is a comment.",
            "{",
            "\tnode [style=filled]",
            "\tbar [color=green]",
            "\tfoo [color=red]",
            "\tfoo -> bar [color=blue]",
            "}",
        ]

    def test_quote(self):
        assert NoDashDiGraph._quote("foo_bar") == '"foo bar"'

    def test_quote_edge(self):
        assert NoDashDiGraph._quote_edge("foo_bar") == '"foo bar"'
