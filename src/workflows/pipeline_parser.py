from .types import Pipeline, PIPENINE_EXAMPLE, EdgesTypeEnum, Edge, NodeDependency


# This will not be used, will be developed later.
class PipelineParserAdvanced:
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline
        self._parallel_nodes = {}
        self._trace = {}

    def _identify_root_parallel_nodes(self):
        parallel_nodes = {}
        root_src = None

        for edge in self.pipeline.edges:
            if edge.type == EdgesTypeEnum.PARALLEL:
                if not root_src == edge.source:
                    root_src = edge.source

                if not root_src in parallel_nodes:
                    parallel_nodes.update({root_src: []})

                parallel_nodes[root_src].append(edge)

        self._parallel_nodes = parallel_nodes
        return parallel_nodes

    def trace_till_intersection(self):
        node_items: tuple[tuple[str, list[Edge]]] = self._parallel_nodes.items()
        trace = {}

        for k, v in node_items:
            for p_edge in v:
                for edge in self.pipeline.edges:

                    if not p_edge.target in trace:
                        trace.update({p_edge.target: []})

                    if not edge.source == p_edge.target:
                        continue

                    trace[p_edge.target].append(edge)

        self._trace = trace
        return trace

    def parse(self):
        pass


def parse_pipeline(pipeline: Pipeline) -> NodeDependency:
    """Gives 'on which nodes the single node is dependent upon', {"node": ["node1", "node2", ...]}'"""
    node_names = []
    data: dict[str, list[str]] = {}

    for node in pipeline.nodes:
        node_names.append(node.name)
    for node in pipeline.nodes:
        if not node.name in data:
            data.update({node.name: []})

        for n in node_names:
            for i_val in node.inputs.values():
                if n in i_val:
                    data[node.name].append(n)

    return NodeDependency(data=data)
