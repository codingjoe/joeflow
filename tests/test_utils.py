from joeflow.utils import NoDashDiGraph


class TestNoDashDiGraph:
    def test_node(self):
        graph = NoDashDiGraph()
        graph.node("foo", color="blue")
        graph_str = str(graph)
        assert "graph LR" in graph_str
        assert "foo[foo]" in graph_str
        # Test that updating node works
        graph.node("foo", color="red")
        graph_str = str(graph)
        assert "graph LR" in graph_str
        assert "foo[foo]" in graph_str

    def test_edge(self):
        graph = NoDashDiGraph()
        graph.edge("foo", "bar", color="blue")
        graph_str = str(graph)
        assert "graph LR" in graph_str
        assert "foo --> bar" in graph_str
        # Test that updating edge works
        graph.edge("foo", "bar", color="red")
        graph_str = str(graph)
        assert "graph LR" in graph_str
        assert "foo --> bar" in graph_str

    def test_iter(self):
        graph = NoDashDiGraph(node_attr={"style": "filled"})
        graph.node("foo", color="red")
        graph.node("bar", color="green")
        graph.edge("foo", "bar", color="blue")
        graph.comment = "This is a comment."
        print(str(graph))
        graph_str = str(graph)
        assert "%% This is a comment." in graph_str
        assert "graph LR" in graph_str
        assert "bar[bar]" in graph_str
        assert "foo[foo]" in graph_str
        assert "foo --> bar" in graph_str

    def test_sanitize_id(self):
        assert NoDashDiGraph._sanitize_id("foo_bar") == "foo_bar"
        assert NoDashDiGraph._sanitize_id("foo bar") == "foo_bar"

    def test_format_label(self):
        assert NoDashDiGraph._format_label("foo_bar") == "foo bar"
