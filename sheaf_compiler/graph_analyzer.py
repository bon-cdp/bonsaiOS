"""
PyTorch Graph Analyzer using torch.fx

This module traces PyTorch models and analyzes their computation graph
to identify algebraic structure (routing, experts, patches).

The goal: map a PyTorch model to a sheaf structure automatically.
"""

import torch
import torch.fx as fx
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import networkx as nx


@dataclass
class GraphPatch:
    """
    Represents a "patch" in the sheaf-theoretic sense.

    A patch is a connected subgraph that operates independently
    (conditioned on the router's decision).
    """
    patch_id: int
    name: str
    nodes: Set[str]  # fx.Node names in this patch
    input_nodes: Set[str]  # Entry points to the patch
    output_nodes: Set[str]  # Exit points from the patch
    conditioning_value: Optional[int] = None  # Which expert/route


@dataclass
class SheafStructure:
    """
    Complete sheaf structure of a model.

    patches: The local systems
    router_node: The conditioning function
    gluing_constraints: How patches connect
    """
    patches: List[GraphPatch]
    router_node: Optional[str]
    graph: fx.GraphModule
    node_to_patch: Dict[str, int]  # Maps node name to patch_id


class GraphAnalyzer:
    """
    Analyzes PyTorch computation graphs using torch.fx.

    Workflow:
      1. Trace model to fx.GraphModule
      2. Identify router (conditioning function)
      3. Partition graph into patches based on routing
      4. Build sheaf structure
    """

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.graph_module: Optional[fx.GraphModule] = None
        self.sheaf_structure: Optional[SheafStructure] = None

    def trace(self, model: torch.nn.Module, example_input: torch.Tensor) -> fx.GraphModule:
        """
        Trace a PyTorch model using torch.fx.

        Args:
            model: The PyTorch model to trace
            example_input: Example input for tracing

        Returns:
            fx.GraphModule containing the traced graph
        """
        if self.verbose:
            print("="*70)
            print("Tracing PyTorch Model with torch.fx")
            print("="*70)

        try:
            self.graph_module = fx.symbolic_trace(model)

            if self.verbose:
                print(f"\n✓ Successfully traced model")
                print(f"  - Total nodes: {len(list(self.graph_module.graph.nodes))}")
                print(f"\nGraph IR:")
                print("-"*70)
                print(self.graph_module.graph)

            return self.graph_module

        except Exception as e:
            print(f"\n✗ Failed to trace model: {e}")
            raise

    def identify_router(self) -> Optional[str]:
        """
        Identify the routing operation in the graph.

        For MoE models, this is typically:
          - A softmax operation (soft routing)
          - An argmax operation (hard routing)
          - Any operation that outputs expert selection weights

        Returns:
            Name of the router node, or None if not found
        """
        if self.graph_module is None:
            raise ValueError("Must call trace() first")

        if self.verbose:
            print("\n" + "="*70)
            print("Identifying Router (Conditioning Function)")
            print("="*70)

        # Look for common routing patterns
        routing_ops = ['softmax', 'argmax', 'gumbel_softmax']

        for node in self.graph_module.graph.nodes:
            # Check if node is a call to a routing function
            if node.op == 'call_function':
                func_name = node.target.__name__ if hasattr(node.target, '__name__') else str(node.target)
                if any(routing_op in func_name.lower() for routing_op in routing_ops):
                    if self.verbose:
                        print(f"\n✓ Found router: {node.name}")
                        print(f"  - Operation: {func_name}")
                        print(f"  - Target: {node.target}")
                        print(f"  - Args: {node.args}")

                    return node.name

            # Check if node is a call to a method (e.g., tensor.softmax())
            if node.op == 'call_method':
                if any(routing_op in node.target for routing_op in routing_ops):
                    if self.verbose:
                        print(f"\n✓ Found router: {node.name}")
                        print(f"  - Method: {node.target}")
                        print(f"  - Args: {node.args}")

                    return node.name

        if self.verbose:
            print("\n✗ No explicit router found")
            print("   (Model may not have MoE structure)")

        return None

    def partition_graph(self, router_node_name: Optional[str] = None) -> List[GraphPatch]:
        """
        Partition the computation graph into patches.

        Strategy:
          1. If router exists: trace data flow to identify expert branches
          2. Each branch becomes a patch
          3. Shared nodes go into a "common" patch

        Args:
            router_node_name: Name of the router node (auto-detected if None)

        Returns:
            List of GraphPatch objects
        """
        if self.graph_module is None:
            raise ValueError("Must call trace() first")

        if router_node_name is None:
            router_node_name = self.identify_router()

        if self.verbose:
            print("\n" + "="*70)
            print("Partitioning Graph into Patches")
            print("="*70)

        patches: List[GraphPatch] = []
        node_to_patch: Dict[str, int] = {}

        # For now, simple heuristic: nodes after router are separate patches
        # More sophisticated: analyze data dependencies

        # Get all nodes
        nodes = list(self.graph_module.graph.nodes)
        node_names = [n.name for n in nodes]

        if router_node_name:
            router_idx = node_names.index(router_node_name)

            # Nodes before router = patch 0 (common/input processing)
            pre_router_nodes = set(node_names[:router_idx + 1])
            patch_0 = GraphPatch(
                patch_id=0,
                name="input_and_router",
                nodes=pre_router_nodes,
                input_nodes={node_names[0]},  # Input node
                output_nodes={router_node_name}
            )
            patches.append(patch_0)

            for node_name in pre_router_nodes:
                node_to_patch[node_name] = 0

            # Nodes after router = patch 1 (for now, single expert patch)
            # TODO: Implement proper expert identification
            post_router_nodes = set(node_names[router_idx + 1:])
            patch_1 = GraphPatch(
                patch_id=1,
                name="expert_processing",
                nodes=post_router_nodes,
                input_nodes={router_node_name},
                output_nodes={node_names[-1]}  # Output node
            )
            patches.append(patch_1)

            for node_name in post_router_nodes:
                node_to_patch[node_name] = 1

        else:
            # No router: treat entire graph as single patch
            all_nodes = set(node_names)
            patch_0 = GraphPatch(
                patch_id=0,
                name="monolithic",
                nodes=all_nodes,
                input_nodes={node_names[0]},
                output_nodes={node_names[-1]}
            )
            patches.append(patch_0)

            for node_name in node_names:
                node_to_patch[node_name] = 0

        if self.verbose:
            print(f"\n✓ Identified {len(patches)} patches:")
            for patch in patches:
                print(f"\n  Patch {patch.patch_id}: '{patch.name}'")
                print(f"    - Nodes: {len(patch.nodes)}")
                print(f"    - Inputs: {patch.input_nodes}")
                print(f"    - Outputs: {patch.output_nodes}")

        return patches, node_to_patch

    def analyze(self, model: torch.nn.Module, example_input: torch.Tensor) -> SheafStructure:
        """
        Full analysis pipeline: trace → identify router → partition.

        Args:
            model: PyTorch model
            example_input: Example input for tracing

        Returns:
            SheafStructure describing the model's algebraic decomposition
        """
        # Step 1: Trace
        self.trace(model, example_input)

        # Step 2: Identify router
        router_node = self.identify_router()

        # Step 3: Partition
        patches, node_to_patch = self.partition_graph(router_node)

        # Step 4: Build sheaf structure
        self.sheaf_structure = SheafStructure(
            patches=patches,
            router_node=router_node,
            graph=self.graph_module,
            node_to_patch=node_to_patch
        )

        if self.verbose:
            print("\n" + "="*70)
            print("✅ Sheaf Structure Analysis Complete!")
            print("="*70)
            print(f"\nSummary:")
            print(f"  - Total patches: {len(patches)}")
            print(f"  - Router node: {router_node or 'None'}")
            print(f"  - Graph nodes: {len(node_to_patch)}")

        return self.sheaf_structure

    def visualize_graph(self, output_path: str = "graph_visualization.png"):
        """
        Visualize the computation graph with patches colored.

        Requires: graphviz, networkx, matplotlib
        """
        if self.graph_module is None:
            raise ValueError("Must call trace() first")

        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches

            # Build NetworkX graph
            G = nx.DiGraph()

            for node in self.graph_module.graph.nodes:
                G.add_node(node.name, op=node.op, target=str(node.target))

                for arg in node.args:
                    if isinstance(arg, fx.Node):
                        G.add_edge(arg.name, node.name)

            # Color nodes by patch
            if self.sheaf_structure:
                node_colors = []
                color_map = {0: 'lightblue', 1: 'lightgreen', 2: 'lightcoral', 3: 'lightyellow'}

                for node in G.nodes():
                    patch_id = self.sheaf_structure.node_to_patch.get(node, 0)
                    node_colors.append(color_map.get(patch_id, 'lightgray'))
            else:
                node_colors = ['lightgray'] * len(G.nodes())

            # Draw
            plt.figure(figsize=(14, 10))
            pos = nx.spring_layout(G, k=1.5, iterations=50)
            nx.draw(G, pos, with_labels=True, node_color=node_colors,
                   node_size=1500, font_size=8, font_weight='bold',
                   arrows=True, edge_color='gray', alpha=0.7)

            # Add legend
            if self.sheaf_structure:
                legend_elements = [
                    mpatches.Patch(color='lightblue', label='Patch 0: Input/Router'),
                    mpatches.Patch(color='lightgreen', label='Patch 1: Expert Processing')
                ]
                plt.legend(handles=legend_elements, loc='upper left')

            plt.title("Computation Graph with Sheaf Patches", fontsize=16, fontweight='bold')
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"\n✓ Saved graph visualization to {output_path}")

        except ImportError as e:
            print(f"\n✗ Cannot visualize: missing dependencies ({e})")


def test_graph_analyzer():
    """Test the GraphAnalyzer on our SimpleMoE model."""
    from simple_moe_model import SimpleMoE, HardMoE

    print("\n" + "="*70)
    print("Testing Graph Analyzer on MoE Models")
    print("="*70)

    # Create model and example input
    # Note: Using SimpleMoE because HardMoE has control flow that torch.fx can't trace
    model = SimpleMoE(input_dim=4, hidden_dim=8, output_dim=2, num_experts=3)
    example_input = torch.randn(2, 4)

    # Analyze
    analyzer = GraphAnalyzer(verbose=True)
    sheaf_structure = analyzer.analyze(model, example_input)

    # Print summary
    print("\n" + "="*70)
    print("Sheaf Structure Summary")
    print("="*70)
    print(f"\nPatches: {len(sheaf_structure.patches)}")
    for patch in sheaf_structure.patches:
        print(f"\n  {patch.name}:")
        print(f"    - ID: {patch.patch_id}")
        print(f"    - Nodes: {len(patch.nodes)}")
        print(f"    - Sample nodes: {list(patch.nodes)[:5]}")

    print("\n" + "="*70)
    print("✅ Graph analysis complete!")
    print("="*70)


if __name__ == "__main__":
    test_graph_analyzer()
