#!/usr/bin/env python
"""Summary representation of a graph."""

from igraph.statistics import median
from math import ceil
from textwrap import TextWrapper

__all__ = ["GraphSummary"]

class GraphSummary(object):
    """Summary representation of a graph.

    The summary representation includes a header line and the list of
    edges. The header line consists of C{IGRAPH}, followed by a
    four-character long code, the number of vertices, the number of
    edges, two dashes (C{--}) and the name of the graph (i.e.
    the contents of the C{name} attribute, if any). For instance,
    a header line may look like this:

        IGRAPH U--- 4 5 --

    The four-character code describes some basic properties of the
    graph. The first character is C{U} if the graph is undirected,
    C{D} if it is directed. The second letter is C{N} if the graph
    has a vertex attribute called C{name}, or a dash otherwise. The
    third letter is C{W} if the graph is weighted (i.e. it has an
    edge attribute called C{weight}), or a dash otherwise. The
    fourth letter is C{B} if the graph has a vertex attribute called
    C{type}; this is usually used for bipartite graphs.

    Edges may be presented as an ordinary edge list or an adjacency
    list. By default, this depends on the number of edges; however,
    you can control it with the appropriate constructor arguments.
    """


    def __init__(self, graph, verbosity=0, width=78,
            edge_list_format="auto",
            print_graph_attributes=True,
            print_vertex_attributes=True,
            print_edge_attributes=True):
        """Constructs a summary representation of a graph.

        @param verbosity: the verbosity of the summary. If zero, only
          the header line will be returned. If one, the header line
          and the list of edges will both be returned.
        @param width: the maximal width of each line in the summary.
          C{None} means that no limit will be enforced.
        @param edge_list_format: format of the edge list in the summary.
          Supported formats are: C{compressed}, C{adjlist}, C{edgelist},
          C{auto}, which selects automatically from the other three based
          on some simple criteria.
        @param print_graph_attributes: whether to print graph attributes
          if there are any.
        @param print_vertex_attributes: whether to print vertex attributes
          if there are any.
        @param print_edge_attributes: whether to print edge attributes
          if there are any.
        """
        self._graph = graph
        self.edge_list_format = edge_list_format.lower()
        self.print_graph_attributes = print_graph_attributes
        self.print_vertex_attributes = print_vertex_attributes
        self.print_edge_attributes = print_edge_attributes
        self.verbosity = verbosity
        self.width = width
        if self.width is None:
            class FakeWrapper(object):
                def wrap(text):
                    return [text]
                def fill(text):
                    return [text]
            self.wrapper = FakeWrapper()
        else:
            self.wrapper = TextWrapper(width=self.width)
        self.wrapper.break_on_hyphens = False

        if self._graph.is_named():
            self._edges_header = "+ edges (vertex names):"
        else:
            self._edges_header = "+ edges:"
        self._arrow = ["--", "->"][self._graph.is_directed()]
        self._arrow_format = "%%s%s%%s" % self._arrow

    def _construct_edgelist_adjlist(self):
        """Constructs the part in the summary that prints the edge list in an
        adjacency list format."""
        result = [self._edges_header]
        arrow = self._arrow_format

        if self._graph.vcount() == 0:
            return

        if self._graph.is_named():
            names = self._graph.vs["name"]
            maxlen = max(len(name) for name in names)
            format_str = "%%%ds %s %%s" % (maxlen, self._arrow)
            for v1, name in enumerate(names):
                neis = self._graph.successors(v1)
                neis = ", ".join(str(names[v2]) for v2 in neis)
                result.append(format_str % (name, neis))
        else:
            maxlen = len(str(self._graph.vcount()))
            num_format = "%%%dd" % maxlen
            format_str = "%s %s %%s" % (num_format, self._arrow)
            for v1 in xrange(self._graph.vcount()):
                neis = self._graph.successors(v1)
                neis = " ".join(num_format % v2 for v2 in neis)
                result.append(format_str % (v1, neis))

        # Try to wrap into multiple columns if that works with the given width
        if self.width is not None:
            maxlen = max(len(line) for line in result[1:])
            colcount = int(self.width + 3) / int(maxlen + 3)
            if colcount > 1:
                # Rewrap to multiple columns
                nrows = len(result) - 1
                colheight = int(ceil(nrows / float(colcount)))
                newrows = [[] for _ in xrange(colheight)]
                for i, row in enumerate(result[1:]):
                    newrows[i % colheight].append(row.ljust(maxlen))
                result[1:] = ["   ".join(row) for row in newrows]

        return result

    def _construct_edgelist_compressed(self):
        """Constructs the part in the summary that prints the edge list in a
        compressed format suitable for graphs with mostly small degrees."""
        result = [self._edges_header]
        arrow = self._arrow_format

        if self._graph.is_named():
            names = self._graph.vs["name"]
            edges = ", ".join(arrow % (names[edge.source], names[edge.target])
                for edge in self._graph.es)
        else:
            edges = " ".join(arrow % edge.tuple for edge in self._graph.es)

        result.append(edges)
        return result

    def _construct_edgelist_edgelist(self):
        """Constructs the part in the summary that prints the edge list in a
        full edge list format."""
        result = [self._edges_header]
        arrow = self._arrow_format

        # TODO
        return result

    def _construct_graph_attributes(self):
        """Constructs the part in the summary that lists the graph attributes."""
        attrs = self._graph.attributes()
        if not attrs:
            return []
        
        result = ["+ graph attributes:"]
        attrs.sort()
        for attr in attrs:
            result.append("[[%s]]" % attr)
            result.append(str(self._graph[attr]))
        return result

    def _construct_vertex_attributes(self):
        """Constructs the part in the summary that lists the vertex attributes."""
        attrs = set(self._graph.vertex_attributes())
        attrs.discard("name")
        if not attrs:
            return []

        result = ["+ vertex attributes:"]

        # TODO
        return result

    def _construct_header(self):
        """Constructs the header part of the summary."""
        graph = self._graph
        params = dict(
                directed="UD"[graph.is_directed()],
                named="-N"[graph.is_named()],
                weighted="-W"[graph.is_weighted()],
                typed="-T"["type" in graph.vertex_attributes()],
                vcount=graph.vcount(),
                ecount=graph.ecount(),
        )
        if "name" in graph.attributes():
            params["name"] = graph["name"]
        else:
            params["name"] = ""
        result = ["IGRAPH %(directed)s%(named)s%(weighted)s%(typed)s "\
                  "%(vcount)d %(ecount)d -- %(name)s" % params]

        attrs = ["%s (g)" % name for name in graph.attributes()]
        attrs.extend("%s (v)" % name for name in graph.vertex_attributes())
        attrs.extend("%s (e)" % name for name in graph.edge_attributes())
        if attrs:
            result.append("+ attr: %s" % ", ".join(attrs))
            if self.wrapper is not None:
                self.wrapper.subsequent_indent = '  '
                result[-1:] = self.wrapper.wrap(result[-1])
                self.wrapper.subsequent_indent = ''

        return result

    def __str__(self):
        """Returns the summary representation as a string."""
        output = self._construct_header()
        if self.verbosity <= 0:
            return "\n".join(output)

        if self.print_graph_attributes:
            output.extend(self._construct_graph_attributes())
        if self.print_vertex_attributes:
            output.extend(self._construct_vertex_attributes())

        if self._graph.ecount() > 0:
            # Add the edge list
            if self.edge_list_format == "auto":
                # Select the appropriate edge list format
                if (self.print_edge_attributes and self._graph.edge_attributes()):
                    format = "edgelist"
                elif median(self._graph.degree(type="out")) < 3:
                    format = "compressed"
                else:
                    format = "adjlist"
            else:
                format = self.edge_list_format

            method_name = "_construct_edgelist_%s" % format
            if hasattr(self, method_name):
                output.extend(getattr(self, method_name)())

        if self.wrapper is not None:
            return "\n".join("\n".join(self.wrapper.wrap(line)) for line in output)

        return "\n".join(output)
