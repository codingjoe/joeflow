from joeflow.utils import NoDashDiGraph


class TestNoDashDiGraph:
    def test_node(self):
        graph = NoDashDiGraph()
        graph.node("foo", color="blue")
        assert list(graph) == [
            "digraph {\n",
            "\tfoo [color=blue]\n",
            "}\n",
        ]
        graph.node("foo", color="red")
        assert list(graph) == [
            "digraph {\n",
            "\tfoo [color=red]\n",
            "}\n",
        ]

    def test_edge(self):
        graph = NoDashDiGraph()
        graph.edge("foo", "bar", color="blue")
        assert list(graph) == [
            "digraph {\n",
            "\tfoo -> bar [color=blue]\n",
            "}\n",
        ]
        graph.edge("foo", "bar", color="red")
        assert list(graph) == [
            "digraph {\n",
            "\tfoo -> bar [color=red]\n",
            "}\n",
        ]

    def test_iter(self):
        graph = NoDashDiGraph(node_attr={"style": "filled"})
        graph.node("foo", color="red")
        graph.node("bar", color="green")
        graph.edge("foo", "bar", color="blue")
        graph.comment = "This is a comment."
        print(str(graph))
        assert list(graph.__iter__()) == [
            "// This is a comment.\n",
            "digraph {\n",
            "\tnode [style=filled]\n",
            "\tbar [color=green]\n",
            "\tfoo [color=red]\n",
            "\tfoo -> bar [color=blue]\n",
            "}\n",
        ]

    def test_iter__subgraph(self):
        graph = NoDashDiGraph(node_attr={"style": "filled"})
        graph.node("foo", color="red")
        graph.node("bar", color="green")
        graph.edge("foo", "bar", color="blue")
        graph.comment = "This is a comment."
        print(str(graph))
        assert list(graph.__iter__(subgraph=True)) == [
            "// This is a comment.\n",
            "{\n",
            "\tnode [style=filled]\n",
            "\tbar [color=green]\n",
            "\tfoo [color=red]\n",
            "\tfoo -> bar [color=blue]\n",
            "}\n",
        ]

    def test_quote(self):
        assert NoDashDiGraph._quote("foo_bar") == '"foo bar"'

    def test_quote_edge(self):
        assert NoDashDiGraph._quote_edge("foo_bar") == '"foo bar"'
