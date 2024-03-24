BotsOnRails: README / QUICKSTART

BotsOnRails is a Python library for orchestrating Large Language Models (LLMs) and other functions in a flexible, human-in-the-loop manner. It allows you to build execution trees where nodes represent individual tasks or decision points, with the ability to pause and resume execution based on human input or algorithmic conditions. This makes it ideal for scenarios where you need to integrate human insights and approvals into automated workflows.
Key Features:

    Tree-based orchestration: Define complex workflows as execution trees with nodes representing tasks or decisions.

    Human-in-the-loop: Seamlessly integrate human input and approvals into automated workflows.

    Dynamic routing: Route execution flow based on runtime data or conditions using functions or static mappings.

    Type checking: Ensure type safety and compatibility between nodes for robust execution.

    Visualization: Generate visual representations of your execution trees for analysis and debugging.

    Resumable execution: Restart or continue execution from specific nodes for iterative review and modification.

    Lightweight and flexible: Easy to integrate into existing projects and adapt to various use cases.

Installation:

      
pip install BotsOnRails

    

Use code with caution.Bash
Quickstart:

    Define your functions: Write the functions that will be executed as nodes in your tree. Annotate them with type hints for inputs and outputs.

    Create an ExecutionTree: Instantiate an ExecutionTree object to manage your workflow.

    Register nodes: Use the node_for_tree decorator factory to register your functions as nodes in the tree. You can specify node names, approval requirements, and routing logic within the decorator.

    Compile the tree: Call the compile method on the ExecutionTree to generate the necessary routing logic and ensure type compatibility.

    Run the tree: Call the run method on the ExecutionTree to initiate execution. You can provide initial input data and control auto-approval behavior.

    Visualize and analyze: Use the visualization methods like visualize_via_graphviz and generate_mermaid_diagram to understand your workflow structure and execution flow.

Example:

```
from BotsOnRails import ExecutionTree, node_for_tree

tree = ExecutionTree()
node = node_for_tree(tree)

@node(start_node=True, next_nodes="process_data")
def get_data(**kwargs) -> str:
    # Logic to fetch data
    return data

@node(wait_for_approval=True)
def process_data(data: str, **kwargs) -> str:
    # Logic to process data
    return processed_data

@node()
def send_results(processed_data: str, **kwargs):
    # Logic to send results
    pass

tree.compile(type_checking=True)
tree.run()  # Initiates execution
```

This example demonstrates a simple workflow where data is fetched, processed with human approval, and then sent. You can build much more complex workflows with conditional routing, loops, and various node types.
Documentation:

For detailed documentation and API reference, please refer to the docstrings within the code or visit the project's GitHub repository.
Contributing:

Contributions are welcome! Please see the contributing guidelines in the GitHub repository.
License:

BotsOnRails is licensed under the MIT License.