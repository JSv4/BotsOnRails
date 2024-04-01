# BotsOnRails: README / QUICKSTART

BotsOnRails is a Python library for orchestrating Large Language Models (LLMs) and other functions in a flexible, human-in-the-loop manner. It allows you to build execution trees where nodes represent individual tasks or decision points, with the ability to pause and resume execution based on human input or algorithmic conditions. This makes it ideal for scenarios where you need to integrate human insights and approvals into automated workflows.

# Key Features:

1. Tree-based orchestration: Define complex workflows as execution trees with nodes representing tasks or decisions.
2. Human-in-the-loop: Seamlessly integrate human input and approvals into automated workflows.
3. Dynamic routing: Route execution flow based on runtime data or conditions using functions or static mappings.
4. Type checking: Ensure type safety and compatibility between nodes for robust execution.
5. Visualization: Generate visual representations of your execution trees for analysis and debugging.
6. Resumable execution: Restart or continue execution from specific nodes for iterative review and modification.
7. Lightweight and flexible: Easy to integrate into existing projects and adapt to various use cases.

# Installation:

## Prerequisites 

You need to install graphviz, which has different installation methods depending on your system.

### Windows

We'd suggest using the .exe installer from the 
[official graphviz website](https://graphviz.org/doc/winbuild.html).

### Linux

If you're using Ubuntu or another Debian derivative, try using apt like so:

```requirements
sudo apt install graphviz 
```

### MacOS

There are a number of ways to install graphviz on Mac. For example, you can use homebrew:

```requirements
brew install graphviz
```

## Install BotsOnRails

You can install the package directly from PyPi using pip:

```commandline
pip install BotsOnRails
```

# Quickstart:

## Steps:

1. Define your functions: Write the functions that will be executed as nodes in your tree. Annotate them with type hints for inputs and outputs.

2. Create an ExecutionTree: Instantiate an ExecutionTree object to manage your workflow.

3. Register nodes: Use the node_for_tree decorator factory to register your functions as nodes in the tree. You can specify node names, approval requirements, and routing logic within the decorator.

4. Compile the tree: Call the compile method on the ExecutionTree to generate the necessary routing logic and ensure type compatibility.

5. Run the tree: Call the run method on the ExecutionTree to initiate execution. You can provide initial input data and control auto-approval behavior.

6. Visualize and analyze: Use the visualization methods like visualize_via_graphviz and generate_mermaid_diagram to understand your workflow structure and execution flow.

## Example:

```
from BotsOnRails import ExecutionTree, node_for_tree

tree = ExecutionTree()
node = node_for_tree(tree)

@node(path_start=True, next_nodes="process_data")
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

# Documentation:

For detailed documentation and API reference, please refer to the docstrings within the code or visit the project's GitHub repository.

# Contributing:

Contributions are welcome! Please see the contributing guidelines in the GitHub repository.

# License:

BotsOnRails is licensed under the MIT License.