"""
Simple Mixture-of-Experts (MoE) PyTorch Model

This is our "patient" - a model with explicit routing structure that perfectly
demonstrates the sheaf-theoretic decomposition:
  - Router = conditioning function
  - Experts = patches
  - Final aggregation = gluing constraint

The model is intentionally simple to make the algebraic structure clear.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class ExpertNetwork(nn.Module):
    """A single expert in the MoE. Simple linear layer."""

    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.fc = nn.Linear(input_dim, output_dim)

    def forward(self, x):
        return self.fc(x)


class SimpleMoE(nn.Module):
    """
    Simple Mixture of Experts Model

    Architecture:
        input → router (selects expert) → expert_0, expert_1, expert_2 → output

    This structure maps perfectly to sheaf theory:
        - router() is the conditioning_function
        - Each expert is a "patch" (local system)
        - The gating mechanism enforces consistency (gluing)

    Args:
        input_dim: Dimension of input features
        hidden_dim: Dimension of expert outputs
        output_dim: Final output dimension
        num_experts: Number of expert networks
    """

    def __init__(self, input_dim: int = 4, hidden_dim: int = 8,
                 output_dim: int = 2, num_experts: int = 3):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.num_experts = num_experts

        # Router: maps input to expert selection logits
        self.router = nn.Linear(input_dim, num_experts)

        # Experts: independent local networks
        self.experts = nn.ModuleList([
            ExpertNetwork(input_dim, hidden_dim)
            for _ in range(num_experts)
        ])

        # Final projection
        self.output_proj = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        """
        Forward pass with explicit routing

        Args:
            x: Input tensor [batch_size, input_dim]

        Returns:
            output: [batch_size, output_dim]
            routing_weights: [batch_size, num_experts] (for analysis)
        """
        batch_size = x.shape[0]

        # 1. Router: decide which expert(s) to use
        routing_logits = self.router(x)  # [batch, num_experts]
        routing_weights = F.softmax(routing_logits, dim=-1)  # [batch, num_experts]

        # 2. Experts: compute outputs for all experts
        expert_outputs = []
        for expert in self.experts:
            expert_out = expert(x)  # [batch, hidden_dim]
            expert_outputs.append(expert_out)

        expert_outputs = torch.stack(expert_outputs, dim=1)  # [batch, num_experts, hidden_dim]

        # 3. Aggregate: weighted combination based on routing
        # routing_weights: [batch, num_experts, 1]
        # expert_outputs: [batch, num_experts, hidden_dim]
        weighted_experts = routing_weights.unsqueeze(-1) * expert_outputs  # [batch, num_experts, hidden_dim]
        combined = weighted_experts.sum(dim=1)  # [batch, hidden_dim]

        # 4. Final projection
        output = self.output_proj(combined)  # [batch, output_dim]

        return output, routing_weights


class HardMoE(nn.Module):
    """
    Hard-routed MoE (selects single expert via argmax)

    This is easier to analyze for patch discovery since routing is deterministic.
    """

    def __init__(self, input_dim: int = 4, hidden_dim: int = 8,
                 output_dim: int = 2, num_experts: int = 3):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.num_experts = num_experts

        self.router = nn.Linear(input_dim, num_experts)
        self.experts = nn.ModuleList([
            ExpertNetwork(input_dim, hidden_dim)
            for _ in range(num_experts)
        ])
        self.output_proj = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        """Hard routing: select single expert via argmax."""
        batch_size = x.shape[0]

        # Router
        routing_logits = self.router(x)
        expert_indices = torch.argmax(routing_logits, dim=-1)  # [batch]

        # Select expert outputs (non-differentiable, but good for analysis)
        outputs = []
        for i in range(batch_size):
            expert_idx = expert_indices[i].item()
            expert_out = self.experts[expert_idx](x[i:i+1])
            outputs.append(expert_out)

        combined = torch.cat(outputs, dim=0)  # [batch, hidden_dim]
        output = self.output_proj(combined)

        # Create one-hot routing weights for compatibility
        routing_weights = F.one_hot(expert_indices, num_classes=self.num_experts).float()

        return output, routing_weights


def test_moe_models():
    """Test both MoE models to verify they work."""
    print("="*70)
    print("Testing Mixture-of-Experts Models")
    print("="*70)

    # Create dummy data
    batch_size = 4
    input_dim = 4
    x = torch.randn(batch_size, input_dim)

    print(f"\nInput shape: {x.shape}")

    # Test SimpleMoE (soft routing)
    print("\n1. SimpleMoE (soft routing via softmax)")
    print("-"*70)

    model = SimpleMoE(input_dim=input_dim, hidden_dim=8, output_dim=2, num_experts=3)
    output, routing_weights = model(x)

    print(f"Output shape: {output.shape}")
    print(f"Routing weights shape: {routing_weights.shape}")
    print(f"Routing weights:\n{routing_weights}")
    print(f"Routing weights sum per sample: {routing_weights.sum(dim=1)}")

    # Test HardMoE (hard routing)
    print("\n2. HardMoE (hard routing via argmax)")
    print("-"*70)

    hard_model = HardMoE(input_dim=input_dim, hidden_dim=8, output_dim=2, num_experts=3)
    output_hard, routing_hard = hard_model(x)

    print(f"Output shape: {output_hard.shape}")
    print(f"Routing weights (one-hot):\n{routing_hard}")
    print(f"Selected experts: {torch.argmax(routing_hard, dim=1)}")

    print("\n" + "="*70)
    print("✅ Both MoE models work correctly!")
    print("="*70)
    print("\nKey observations:")
    print("  • Router creates the conditioning function")
    print("  • Each expert is an independent patch")
    print("  • Hard routing makes patch assignment explicit")
    print("  • This structure is PERFECT for sheaf-theoretic analysis!")


if __name__ == "__main__":
    test_moe_models()
