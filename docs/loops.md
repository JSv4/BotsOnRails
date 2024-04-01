# BotsOnRails For Each Loops 

A powerful feature of BotsOnRails is the ability to dynamically process each element of an iterable 
(only lists or tuples ATM) individually using a for each loop. This guide explains how to use this feature.

## Basic Syntax

To use a for each loop, a node must return an iterable output. Then, in the `next_step` routing specification, use the 
special tuple syntax `("FOR_EACH", "node_name")` to indicate that each element of the iterable should be processed 
individually by the specified next node.

Here's an example:

```python
@step(next_step=("FOR_EACH", "process_item"))
def get_items() -> List[str]:
    return ["foo", "bar", "baz"]

@step(next_step="aggregate_results")  
def process_item(item: str) -> str:
    return item.upper()

@step()
def aggregate_results(item: str) -> str:
    return item
```

In this example, `get_items` returns a list of strings. The `("FOR_EACH", "process_item")` routing spec indicates that 
each string should be passed individually to `process_item`. 

The `process_item` node receives a single string as input (note the type annotation) and processes it, in this case 
converting it to uppercase.

Finally, the results are passed one by one to the `aggregate_results` node (which would typically aggregate them in 
some way).

## Type Safety

For each loops in BotsOnRails are type safe. The return type annotation of the node that initiates the loop must be a 
`List` or `Tuple` (or other iterable) and the input type annotation of the processing node must match the element type 
of the iterable.

For example, this is valid:

```python
@step(next_step=("FOR_EACH", "process_item"))
def get_items() -> List[str]:
    return ["foo", "bar", "baz"]

@step
def process_item(item: str) -> str:
    return item.upper()
```

But this would raise a type error:

```python
@step(next_step=("FOR_EACH", "process_item"))
def get_items() -> List[str]:
    return ["foo", "bar", "baz"] 

@step
def process_item(item: int) -> int: 
    return item * 2
```

The processing node expects an `int` but the for each loop provides a `str`.

## Aggregation

After processing each element individually, you often want to aggregate the results back together. This is done in an 
aggregation node.

An aggregation node is indicated by the `aggregator=True` argument to the `@step` decorator. It must take a single
input of the same type outputted by the processing node. 

While you might expect an aggregator to return a list as a type signature, it *should not*. Remember, when your IDE is 
type checking and warning of mismatches, it's looking at the return signatures within the function. We're doing some 
backend magic to aggregate everything and storing a list of values from each loop during each execution of the 
`for_each` loop. The `@step(aggregator=True)` step is our best attempt (at the moment) to signal to our execution 
engine that the logic for the loop ends at the aggregator node and should be aggregated. Typically, you're not going
to want to do much (if anything) in the aggreagtor other than pass through the received value, which will be aggregated
by the `ExecutionPath`.

Here's an example that extends the previous one to aggregate the uppercased strings into a single string:

```python
@step(next_step="aggregate_results")
def process_item(item: str) -> str:
    return item.upper()

@step(next_step="print_list", aggregator=True)
def aggregate_results(items: str) -> str:
    return items

# Note this expects a list whereas the aggregator __function__ provides just a single string. This is due to how we 
# wrap the functions and perform the `for_each` logic.
@step()
def print_list(items: List[str]):
    print("Result: " + ", ".join(items))
```

The `aggregate_results` step has been marked as an aggregator via `aggregator=True`. It outputs a string for each list 
element.

The `print_list` node takes the `List[str]` assembled by the aggregator as input and combines them into a single result 
string. As discussed, the typing is not perfect here (and we're open to suggestions!). The aggreagtor __function__
only returns a single item. The following step's function, however, should expect a list of the types that the aggregator
outputs. 
