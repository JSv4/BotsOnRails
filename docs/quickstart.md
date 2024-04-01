# BotsOnRails Quickstart

This guide will walk you through the key steps and concepts for building a workflow using BotsOnRails.

## Defining Nodes

The key building block in BotsOnRails is a node, which represents a single task or decision point in your workflow. Nodes are defined using normal Python functions, with a few key additions:

1. Use the `@node` decorator to indicate that a function is a workflow node. At least one node must have `path_start=True` 
2. Add type annotations to the function indicating the expected input and output types
3. Optionally specify a `next_step` argument indicating which node(s) to execute next

Here's an example node definition:

```python
# Compile the execution tree
from BotsOnRails import ExecutionPath, step_decorator_for_path

path = ExecutionPath()
step = step_decorator_for_path(path)


@step(next_nodes="process_text", path_start=True)
def get_user_input() -> str:
    return input("Please enter some text: ")


@step()
def process_text(text: str) -> str:
    return text.upper()


path.compile(type_checking=True)
path.visualize_via_graphviz()
```

## Building a Workflow

To build a complete workflow, define an `ExecutionPath` and add your node functions to it:

```python
from BotsOnRails import ExecutionPath, step_decorator_for_path

path = ExecutionPath()
step = step_decorator_for_path(path)

@step(path_start=True, next_step="process_text")
def get_user_input() -> str:
    return input("Please enter some text: ")

@step()
def process_text(text: str) -> str:
    return text.upper()
```

Use the `path_start=True` argument to indicate which step is the entry point for the path.

## Executing a Workflow 

To run the workflow, first compile it (you only have to do this once), then call the `run` method:

```python
path.compile()
path.run()
```

This will execute the workflow starting from the designated start node.

## Next Steps

That covers the basic concepts! For more advanced topics, check out:

- The [Node Syntax Guide](node_syntax.md) to learn more techniques for defining nodes and routing 
- The [For Each Guide](loops.md) to understand BotsOnRails' looping functionality
- The [Validation Rules](validation.md) to understand the guardrails BotsOnRails provides

Happy bot building!



for_each_loops.md


validation.md

Let me know if you have any other questions!