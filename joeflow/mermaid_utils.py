"""Utilities for generating Mermaid diagrams."""
from collections import defaultdict

# Color constants
COLOR_BLACK = "#000"
COLOR_GRAY = "#888888"
COLOR_WHITE = "white"

# Style constants
STROKE_DASHARRAY = "5 5"


class MermaidDiagram:
    """
    Generate Mermaid diagram syntax for workflow visualization.

    Similar to graphviz.Digraph but generates Mermaid markup instead.
    Nodes and edges are unique and their attributes will be overridden
    should the same node or edge be added twice.

    Underscores are replaced with whitespaces from identifiers.
    """

    def __init__(self, name="", comment=None, **kwargs):
        self.name = name
        self.comment = comment
        self.graph_attr = {}
        self.node_attr = {}
        self.edge_attr = {}
        self._nodes = defaultdict(dict)
        self._edges = defaultdict(dict)
        self.body = []

    def attr(self, kw, **kwargs):
        """Set graph, node, or edge attributes."""
        if kw == "graph":
            self.graph_attr.update(kwargs)
        elif kw == "node":
            self.node_attr.update(kwargs)
        elif kw == "edge":
            self.edge_attr.update(kwargs)

    def node(self, name, **attrs):
        """Add or update a node."""
        self._nodes[name] = attrs

    def edge(self, tail_name, head_name, **attrs):
        """Add or update an edge between two nodes."""
        self._edges[(tail_name, head_name)] = attrs

    @staticmethod
    def _sanitize_id(name):
        """Convert name to valid Mermaid node ID."""
        # Replace spaces and special chars with underscores
        sanitized = name.replace(" ", "_").replace("-", "_")
        return sanitized

    @staticmethod
    def _format_label(name):
        """Format label for display (replace underscores with spaces)."""
        return name.replace("_", " ")

    def _get_node_shape(self, attrs):
        """Determine Mermaid node shape based on attributes."""
        style = attrs.get("style", "")

        # Check for rounded style (human tasks)
        if "rounded" in style:
            # Rounded rectangle: (text)
            return "(", ")"
        else:
            # Rectangle: [text]
            return "[", "]"

    def _generate_node_styles(self):
        """Generate style definitions for nodes."""
        styles = []
        node_styles = {}

        for name, attrs in sorted(self._nodes.items()):
            node_id = self._sanitize_id(name)
            style_attrs = []

            color = attrs.get("color", "black")
            fontcolor = attrs.get("fontcolor", "black")
            fillcolor = attrs.get("fillcolor", "white")
            style = attrs.get("style", "")

            # Map colors
            if color == COLOR_GRAY:
                stroke_color = COLOR_GRAY
            else:
                stroke_color = COLOR_BLACK

            if fontcolor == COLOR_GRAY:
                text_color = COLOR_GRAY
            else:
                text_color = COLOR_BLACK

            # Determine stroke width based on bold
            if "bold" in style:
                stroke_width = "3px"
            else:
                stroke_width = "2px"

            # Determine stroke style based on dashed
            if "dashed" in style:
                stroke_style = f"stroke-dasharray: {STROKE_DASHARRAY}"
            else:
                stroke_style = ""

            # Build style
            style_parts = [
                f"fill:{fillcolor}",
                f"stroke:{stroke_color}",
                f"stroke-width:{stroke_width}",
                f"color:{text_color}",
            ]
            if stroke_style:
                style_parts.append(stroke_style)

            node_styles[node_id] = ",".join(style_parts)

        # Generate style commands
        for node_id, style_str in node_styles.items():
            styles.append(f"    style {node_id} {style_str}")

        return styles

    def _generate_edge_styles(self):
        """Generate style definitions for edges."""
        styles = []
        edge_styles = {}

        for idx, ((tail, head), attrs) in enumerate(sorted(self._edges.items())):
            style = attrs.get("style", "")
            color = attrs.get("color", "black")

            # Determine link style based on attributes
            if "dashed" in style:
                # Mermaid uses linkStyle to style edges
                if color == COLOR_GRAY:
                    edge_styles[idx] = f"stroke:{COLOR_GRAY},stroke-dasharray: {STROKE_DASHARRAY}"
                else:
                    edge_styles[idx] = f"stroke:{COLOR_BLACK},stroke-dasharray: {STROKE_DASHARRAY}"
            elif color == COLOR_GRAY:
                edge_styles[idx] = f"stroke:{COLOR_GRAY}"
            # else: default black stroke

        # Generate linkStyle commands
        for idx, style_str in edge_styles.items():
            styles.append(f"    linkStyle {idx} {style_str}")

        return styles

    def __iter__(self):
        """Yield the Mermaid source code line by line."""
        lines = []

        # Comment
        if self.comment:
            lines.append(f"%% {self.comment}")

        # Graph declaration
        rankdir = self.graph_attr.get("rankdir", "LR")
        lines.append(f"graph {rankdir}")

        # Nodes
        for name, attrs in sorted(self._nodes.items()):
            node_id = self._sanitize_id(name)
            label = self._format_label(name)

            # Determine shape
            left, right = self._get_node_shape(attrs)

            # Add href if present
            href = attrs.get("href", "")
            if href:
                lines.append(f"    {node_id}{left}{label}{right}")
                lines.append(f'    click {node_id} "{href}"')
            else:
                lines.append(f"    {node_id}{left}{label}{right}")

        # Edges
        for tail_name, head_name in sorted(self._edges.keys()):
            tail_id = self._sanitize_id(tail_name)
            head_id = self._sanitize_id(head_name)
            lines.append(f"    {tail_id} --> {head_id}")

        # Styles
        node_styles = self._generate_node_styles()
        lines.extend(node_styles)

        edge_styles = self._generate_edge_styles()
        lines.extend(edge_styles)

        for line in lines:
            yield line

    def __str__(self):
        """Return the complete Mermaid diagram as a string."""
        return "\n".join(self)

    def source(self):
        """Return the Mermaid diagram source."""
        return str(self)

    def pipe(self, format="svg", encoding="utf-8"):
        """
        Return the diagram in the specified format.

        For Mermaid, we return the source wrapped in appropriate HTML.
        This is meant for compatibility with the graphviz API.
        """
        source = self.source()
        if format == "svg":
            # Return raw mermaid source - rendering happens client-side
            return source
        elif format == "png" or format == "pdf":
            # For file formats, return the source as-is
            # The management command will handle file writing
            return source
        return source

    def render(self, filename, directory=None, format="svg", cleanup=False):
        """
        Save the Mermaid diagram to a file.

        Args:
            filename: Base filename (without extension)
            directory: Output directory
            format: Output format (svg, png, pdf) - for compatibility
            cleanup: Cleanup intermediate files (not used for Mermaid)
        """
        import os

        if directory:
            filepath = os.path.join(directory, f"{filename}.mmd")
        else:
            filepath = f"{filename}.mmd"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.source())

        return filepath
