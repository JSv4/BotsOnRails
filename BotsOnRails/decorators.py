import logging
from functools import wraps
from typing import Optional, Callable, Dict, get_type_hints, List, NoReturn, Type, Literal, Tuple

from BotsOnRails.nodes import BaseNode
from BotsOnRails.stores import InMemoryStateStore, StateStore
from BotsOnRails.types import OT

logger = logging.getLogger(__name__)


def node_for_tree(execution_tree, state_store: Optional[StateStore] = None):
    """
    A decorator factory that creates a decorator for registering functions as nodes in a specified execution tree.

    This approach allows for the dynamic association of function logic with nodes in an execution tree, facilitating
    the construction of complex execution flows within a modular and manageable framework. Each node in the tree
    represents a unit of work or decision-making logic that can be executed as part of the tree's overall workflows.

    Parameters:
    - execution_tree (ExecutionTree): An instance of an ExecutionTree to which the nodes created by this decorator
      will be added. This allows for the separation of concerns and the ability to manage multiple distinct execution
      trees within the same application or module.

    Returns:
    - A decorator function that takes a function and registers it as a node within the execution tree. This decorator
      can be customized with node-specific parameters such as `name`, `wait_for_approval`, and `next_nodes` to define
      the node's behavior within the tree. If you pass a tuple with a special operator (currently only for_each) and
      the target node, you can create a loop over outputs of node.

    Usage:

    1. Initialize an execution tree instance:
       ```
       tree1 = ExecutionTree()
       ```

    2. Create a specific decorator using the factory, bound to the execution tree instance:
       ```
       node_for_tree1 = node_for_tree(tree1)
       ```

    3. Use the decorator to register functions as nodes in the tree:
       ```
       @node_for_tree1(name="example_node", wait_for_approval=True)
       def some_function(input_data):
           # Function logic
           return some_result
       ```

    The decorator can be used to annotate multiple functions, each of which will be registered as a separate node
    in the execution tree. The `name` parameter allows for the specification of a custom node name, which
    allows for the registration of the same function for use as more than one node. If not provided,
    the function's name will be used. The `wait_for_approval` parameter indicates whether the node's execution should
    pause, waiting for external approval before proceeding. The `next_nodes` parameter allows for the definition of
    dynamic or conditional routing logic, directing the flow from the current node to subsequent nodes based on runtime
    data or conditions.
    """

    # If we didn't purposefully overrride the state store (for whatever reason), use the same instance that's registered
    # for the tree.
    if state_store is None:
        state_store = execution_tree.state_store

    def node_decorator(
            name: Optional[str] = None,
            start_node: bool = False,
            wait_for_approval: bool = False,
            next_nodes: Optional[Callable[[OT], str] | Dict[OT, str] | str | tuple[Literal['FOR_EACH'], str]] = None,
            func_router_possible_node_annot: Optional[List[str]] = None,
            unpack_output: bool = True,
            aggregator: bool = False,
    ):
        def decorator(func):
            nonlocal name
            if name is None:
                name = func.__name__

            # Determine input and output types from annotations
            input_type, output_type = None, None
            type_hints = get_type_hints(func)
            logger.debug(F"Type_hints: {type_hints}")
            if 'return' in type_hints:
                output_type = type_hints.pop('return', None)
                if isinstance(output_type, (list, tuple, List, Tuple)) and isinstance(next_nodes, (tuple, Tuple)):
                    raise ValueError("You can only use special iteration commands in next_nodes where output "
                                     "type is a list or tuple!")
            else:
                if isinstance(next_nodes, tuple):
                    raise ValueError("You can only use the for_each next node command where output type is annotated")

            if len(type_hints) > 0:
                input_type = type_hints

            # Create the node instance
            node_instance = BaseNode(
                name=name,
                description=func.__doc__ if func.__doc__ is not None else "Function call in DAG",
                wait_for_approval=wait_for_approval,
                execute_function=func,
                route=next_nodes,
                func_router_possible_node_annot=func_router_possible_node_annot,
                unpack_output=unpack_output,
                aggregator=aggregator,
                state_store=state_store
            )

            if output_type is not None:
                node_instance.output_type = output_type
            if input_type is not None:
                node_instance.input_type = input_type

            # Add the node to the execution tree
            execution_tree.add_node(name, node_instance, root=start_node)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    return node_decorator
