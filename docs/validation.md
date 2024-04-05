# BotsOnRails Validation Rules

To help ensure the integrity of your workflows, BotsOnRails enforces certain validation rules. This document outlines the key rules to be aware of.

## No Nested Cycles

BotsOnRails does not allow nested cycles in the workflow graph. A nested cycle means a cycle within a cycle. 

For example, this is not allowed:

```python
@step(next_step="node2")
def node1():
    pass

@step(next_step="node3")
def node2():
    pass

@step(next_step="node1")
def node3():
    pass
```

This creates a cycle `node1 -> node2 -> node3 -> node1`.

Cycles are detected when you call `compile()` on your `ExecutionTree`. A `ValueError` will be raised if a nested cycle is found.

## Return Type Consistency

The return type annotation of a node must match the input type annotation of any nodes it routes to.

For example, this is valid:

```python
@step(next_step="node2")
def node1() -> int:
    return 42

@step
def node2(x: int):
    print(x)
```

But this would raise an error:

```python
@step(next_step="node2")  
def node1() -> int:
    return 42

@step
def node2(x: str):
    print(x)
```

The return type of `node1` is `int` but `node2` expects a `str` input.

