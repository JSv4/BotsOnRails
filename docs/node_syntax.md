# BotsOnRails Node Syntax

This guide dives deeper into the options available when defining workflow nodes in BotsOnRails.

## Basic Definition

As covered in the quickstart, the basic syntax for defining a step first uses the `step_decorator_for_path` to create
a decroator - we typically call it a `@step` decorator - which can then be used on a Python function:

```python
from BotsOnRails import ExecutionPath, step_decorator_for_path

path = ExecutionPath()
step = step_decorator_for_path(path)

@step(next_step="process_data")
def get_data() -> str:
    return "Some data"
```

The `@step` decorator takes several optional arguments:

- `path_start`: Boolean indicating if this is the entry point node for the workflow
- `next_step`: Specifies which node(s) to execute after this one (more on this below)
- `wait_for_approval`: Boolean indicating if workflow execution should pause after this node for human approval 
  before proceeding. More on this in the guide on [resumable workflows](resumable_workflows.md). 

## Routing Options

The `next_step` argument provides several options for controlling the flow of execution:

### Static Routing

You can route to a single node by providing the name of the node function as a string:

```python
@step(next_step="node2")
def node1():
    pass
```

### Conditional Routing

To conditionally route based on the output of a node, provide a dictionary mapping output values to node names:

```python
@step(next_step={"foo": "handle_foo", "bar": "handle_bar"})
def router() -> str:
    return "foo"
```

### Dynamic Routing

For even more flexibility, you can provide a function that takes the node output as input and returns the name of the next node:

```python
def router_func(output):
    if output > 10:
        return "handle_high"
    else:
        return "handle_low"

@step(next_step=router_func)
def dynamic_router() -> int:
    return 42
```

**To make full use of functions like type checking and flow visualization** be sure to provide a list of all the possible
resulting next step names as a list to the `func_router_possible_next_step_names` argument of the decorator like so:

```python
def router_func(output):
    if output > 10:
        return "handle_high"
    else:
        return "handle_low"

@step(next_step=router_func, func_router_possible_next_step_names=['handle_high', 'handle_low'])
def dynamic_router() -> int:
    return 42
```

### Looping

To process each element of an iterable output individually, use the special `("FOR_EACH", "node_name")` syntax:

```python
@step(next_step=("FOR_EACH", "process_item"))
def get_items() -> List[str]:
    return ["foo", "bar", "baz"]
```

See the [For Each Guide](loops.md) for more details.

## Type Annotations 

BotsOnRails uses Python type annotations to validate the input and output types of nodes. This helps catch type 
mismatches and ensures the integrity of data flowing through your workflow.

Nodes should have type annotations on their input arguments and return value:

```python
@step
def process_text(text: str) -> str:
    return text.upper()
```

When possible, use specific types like `str`, `int`, `List`, `Dict`, etc. rather than the generic `Any` type. This 
enables better type checking. Use `NoReturn` or leave off a return signature where nothing is returned.
