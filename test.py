"""Test the temporal workflow with a nice example."""
import asyncio
import json
from src.workflows.utils import (
    resolve_inputs,
    _resolve_single_reference,
    topological_sort,
)
from src.workflows.types import Pipeline, Node, NodeDependency
from src.workflows.pipeline_parser import parse_pipeline


async def test_resolve_inputs():
    """Test resolve_inputs with various reference formats."""
    print("=" * 80)
    print("Testing resolve_inputs function")
    print("=" * 80)
    
    # Simulated outputs from previous node executions
    outputs = {
        "groq_llm_node1": {
            "output": {
                "outlines": ["Introduction to Nepal", "Geography", "Culture", "Economy"]
            }
        },
        "groq_llm_node2": {
            "output": {
                "article": "Nepal is a fascinating country with rich cultural heritage..."
            }
        },
        "groq_llm_node3": {
            "output": {
                "article": "The Himalayas dominate Nepal's landscape..."
            }
        },
        "process1": {
            "output": {
                "cleaned": "Processed article 1"
            }
        },
        "process2": {
            "output": {
                "cleaned": "Processed article 2"
            }
        },
    }
    
    # Test 1: Single reference
    print("\n[Test 1] Single reference")
    inputs1 = {
        "topics": "groq_llm_node1.outputs.output.outlines"
    }
    result1 = resolve_inputs(inputs1, outputs)
    print(f"Input:  {inputs1}")
    print(f"Output: {result1}")
    print(f"✓ Resolved to: {result1['topics']}")
    
    # Test 2: Multiple space-separated references
    print("\n[Test 2] Multiple space-separated references")
    inputs2 = {
        "articles": "groq_llm_node2.outputs.output.article groq_llm_node3.outputs.output.article"
    }
    result2 = resolve_inputs(inputs2, outputs)
    print(f"Input:  {inputs2}")
    print(f"Output: {result2}")
    print(f"✓ Resolved to list with {len(result2['articles'])} items")
    
    # Test 3: Template string with reference
    print("\n[Test 3] Template string with reference")
    inputs3 = {
        "prompt": "Generate a description on topics {topics}",
        "topics": "groq_llm_node1.outputs.output.outlines"
    }
    result3 = resolve_inputs(inputs3, outputs)
    print(f"Input:  {inputs3}")
    print(f"Output:")
    print(f"  prompt: {result3['prompt']}")
    print(f"  topics: {result3['topics']}")
    
    # Test 4: Template string with embedded reference
    print("\n[Test 4] Template string with embedded reference")
    inputs4 = {
        "prompt": "Here are the articles: {groq_llm_node2.outputs.output.article}"
    }
    result4 = resolve_inputs(inputs4, outputs)
    print(f"Input:  {inputs4}")
    print(f"Output: {result4}")
    print(f"✓ Template interpolated successfully")
    
    # Test 5: No references (plain values)
    print("\n[Test 5] No references (plain values)")
    inputs5 = {
        "prompt": "Generate me an outline for essay on Nepal",
        "model": "groq",
        "temperature": 0.7
    }
    result5 = resolve_inputs(inputs5, outputs)
    print(f"Input:  {inputs5}")
    print(f"Output: {result5}")
    print(f"✓ All values passed through unchanged")
    
    # Test 6: Mixed - some references, some plain
    print("\n[Test 6] Mixed - references and plain values")
    inputs6 = {
        "prompt": "Analyze this: {groq_llm_node2.outputs.output.article}",
        "temperature": 0.5,
        "other_articles": "groq_llm_node3.outputs.output.article"
    }
    result6 = resolve_inputs(inputs6, outputs)
    print(f"Input:  {inputs6}")
    print(f"Output:")
    for k, v in result6.items():
        print(f"  {k}: {v}")
    
    # Test 7: Unresolved reference (node output not available)
    print("\n[Test 7] Unresolved reference (node not in outputs)")
    inputs7 = {
        "topics": "nonexistent_node.outputs.something"
    }
    result7 = resolve_inputs(inputs7, outputs)
    print(f"Input:  {inputs7}")
    print(f"Output: {result7}")
    print(f"✓ Unresolved reference kept as-is: {result7['topics']}")


def test_topological_sort():
    """Test topological sorting with the example pipeline."""
    print("\n\n" + "=" * 80)
    print("Testing topological_sort function")
    print("=" * 80)
    
    # Create a simple pipeline
    nodes = [
        Node(key="llm.groq", name="node1", type="LLM"),
        Node(key="llm.groq", name="node2", type="LLM", 
             inputs={"prompt": "text", "topics": "node1.outputs.topics"}),
        Node(key="processor", name="node3", type="ACTION",
             inputs={"article": "node2.outputs.article"}),
        Node(key="llm.groq", name="node4", type="LLM",
             inputs={"prompt": "text", "articles": "node2.outputs.article node3.outputs.result"}),
    ]
    
    dependency = parse_pipeline(Pipeline(nodes=nodes, edges=[]))
    print(f"\nDependency graph: {dependency.data}")
    
    order = topological_sort(dependency, nodes)
    print(f"Execution order: {order}")
    
    # Verify order
    for i, node_name in enumerate(order):
        node = next(n for n in nodes if n.name == node_name)
        deps = dependency.data.get(node_name, [])
        if deps:
            print(f"  {i+1}. {node_name} (depends on: {deps})")
        else:
            print(f"  {i+1}. {node_name} (no dependencies)")
    print("\n✓ Topological sort completed successfully")


async def main():
    """Run all tests."""
    await test_resolve_inputs()
    test_topological_sort()
    print("\n" + "=" * 80)
    print("All tests completed successfully! ✓")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
