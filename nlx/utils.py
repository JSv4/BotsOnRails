import inspect
import itertools
import json
import logging
import uuid
import networkx as nx
from typing import Any, Callable, get_type_hints, NoReturn, List, get_origin, Union, get_args, Tuple

logger = logging.getLogger(__name__)


class UUIDEncoder(json.JSONEncoder):
    """
    A custom JSONEncoder subclass that knows how to encode UUID objects.

    Example usage:
    >>> my_uuid = uuid.uuid4()
    >>> json.dumps({'my_uuid': my_uuid}, cls=UUIDEncoder)
    """

    def encode(self, obj: Any) -> str:
        """
        Overridden method that serializes objects, specifically handling
        dictionaries with UUID keys.

        Args:
            obj (Any): The object to serialize.

        Returns:
            str: A JSON string representation of the object.
        """
        if isinstance(obj, dict):
            # Convert UUID keys and values to strings
            obj = {str(k): v if not isinstance(v, uuid.UUID) else str(v) for k, v in obj.items()}
        return super().encode(obj)

    def default(self, obj: Any) -> Any:
        """
        Overridden method that serializes UUID objects as strings.
        If the object to serialize is not a UUID, it defers to the superclass method.

        Args:
            obj (Any): The object to serialize.

        Returns:
            Any: A serializable object representation or raises TypeError.
        """
        if isinstance(obj, uuid.UUID):
            # Convert UUID to string
            return str(obj)
        # For any other object, the super class method is called.
        return super().default(obj)


def convert_uuids(obj: Any) -> Any:
    """
    Recursively convert all UUID objects in a data structure (including keys and values in dictionaries)
    to their string representation.

    Args:
        obj (Any): The input object, which can be a dictionary, a list, or any other data type.

    Returns:
        Any: The modified object with all UUIDs converted to strings.
    """
    if isinstance(obj, uuid.UUID):
        # Convert UUID to string
        return str(obj)
    elif isinstance(obj, dict):
        # Recursively apply to dictionary keys and values
        return {convert_uuids(k): convert_uuids(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        # Recursively apply to elements in a list
        return [convert_uuids(elem) for elem in obj]
    elif isinstance(obj, tuple):
        # Recursively apply to elements in a tuple, converting it to a tuple again
        return tuple(convert_uuids(elem) for elem in obj)
    elif isinstance(obj, set):
        # Recursively apply to elements in a set, converting it to a set again
        # Note: All elements in the set must be hashable; converting UUIDs to strings maintains this property.
        return {convert_uuids(elem) for elem in obj}
    else:
        # Return the object unchanged if it's not one of the above types
        return obj


def is_iterable(obj: Any) -> bool:
    """Check if the object is iterable."""
    try:
        iter(obj)
        return True
    except TypeError:
        return False


def is_complex_iterable_annot(annot: Any) -> bool:
    return hasattr(annot, '__args__') and annot.__args__ is not None


def unpack_annotation(annotation: Any) -> List[Any]:
    """
    Unpacks a complex type annotation into a list of its component annotations.

    Args:
        annotation: The complex type annotation to be unpacked.

    Returns:
        A list of component annotations if the input is a complex type annotation,
        otherwise, a list containing the annotation itself.
    """
    # Check if the annotation is a complex type with sub-annotations
    if is_complex_iterable_annot(annotation):
        return list(annotation.__args__)

    # Return the annotation itself wrapped in a list if it's not a complex type
    return [annotation]


def is_optional_annotation(annotation) -> bool:
    """
    Determines if a type annotation is an Optional type.

    Args:
        annotation: The type annotation to check.

    Returns:
        True if the annotation is Optional, False otherwise.
    """
    logger.debug(f"Is annotation {annotation} (type {type(annotation)}) optional?")
    logger.debug(f"Origin is {get_origin(annotation)}")
    logger.debug(f"Args: {get_args(annotation)}")
    return get_origin(annotation) is Union and type(None) in get_args(annotation)


def type_allowed_under_optional_annot(type_annot, annotation) -> bool:
    for arg in get_args(annotation):
        if type_annot == arg:
            return True
    return False


def match_types(
        previous_func_output: Any,
        next_function: Callable,
        unpack_output: bool = True,
        for_each_loop: bool = False,
):
    """
    Checks if the output of a function A is iterable, has the same count as the number of positional
    arguments of function B, and if each item in the output has the same type as the expected type of
    the corresponding positional argument in function B.
    """

    def is_tuple_annotation(annotation):
        return annotation == tuple or isinstance(annotation, (tuple, Tuple))

    def is_list_annotation(annotation):
        return annotation == list or isinstance(annotation, (list, List))

    def is_not_str_or_bytes_str(annotation):
        return (
                annotation != str and
                annotation != bytes and
                annotation != bytearray and
                not isinstance(annotation, (str, bytes, bytearray))
        )

    def unpackable_annotation(annotation):
        return ((is_tuple_annotation(annotation) or is_list_annotation(annotation))
                and is_not_str_or_bytes_str(annotation))

    # Extract argument types for function B
    input_params = get_type_hints(next_function)
    input_signature_params = inspect.signature(next_function).parameters
    input_params.pop('return')  # We don't want return type on the input annotation hint
    annot = get_origin(previous_func_output)
    print(f"Previous function annot origin: {annot}")
    print(f"This is unpackable: {unpackable_annotation(get_origin(previous_func_output))}")

    if not unpackable_annotation(get_origin(previous_func_output)):
        if previous_func_output == NoReturn:
            if input_params == {}:
                pass  # no actual inputs
            elif len(input_params.items()) != 0:
                raise ValueError(
                    f"Function preceding {next_function.__name__} has return type of NoReturn yet function "
                    f"expects inputs of {type(input_params)}")
        elif 'args' in input_signature_params:
            # If we have *args in next function, we're cool with any positional arguments.
            pass
        elif len(input_params.items()) == 1:
            if previous_func_output != list(input_params.values())[0]:
                raise ValueError(f"Mismatched input between output ({previous_func_output}) and next input "
                                 f"({list(input_params.values())[0]})")
        else:
            if input_params == {}:
                raise ValueError("No positional arguments are expected for target function, but preceding function"
                                 " has a return type...")
            else:
                raise ValueError(f"Return type is not an iterable (and single, unpackable value), yet next function "
                                 f"expects multiple positional args - {input_params} {input_params.values()}")
    elif for_each_loop:

        print("This is a for_each loop!")
        contents_of_iterable = unpack_annotation(previous_func_output)

        if len(input_params.items()) == 1:
            if contents_of_iterable[0] != list(input_params.values())[0]:
                raise ValueError(f"for_each_loop - Mismatched input between output ({previous_func_output} and next input "
                                 f"({list(input_params.values())[0]}). YOU ARE USING FLAG unpack_output.")
        else:
            raise ValueError(f"Return type is an iterable, and you want to loop over each of its constituent elements."
                             f"We check that the constituent parts of the list or tuple are what's expected as an input"
                             f"for the next function, but it expects multiple inputs.")

        print(f"For_each loop typing works! Each {contents_of_iterable[0]} in list can be passed as input to function "
              f"expecting {list(input_params.values())[0]}")

    elif not unpack_output:

        if len(input_params.items()) == 1:
            if previous_func_output != list(input_params.values())[0]:
                raise ValueError(f"Mismatched input between output ({previous_func_output} and next input "
                                 f"({list(input_params.values())[0]}). YOU ARE NOT USING FLAG unpack_output.")
        else:
            raise ValueError(f"Return type is an iterable, but you explicitly instructed us not to unpack it (with "
                             f"unpack_output=False), yet next function expects"
                             f"multiple positional args - {input_params.values()}. Did you mean to set "
                             f"unpack_output=True?")
    else:
        logger.debug(f"Output of preceding function is a complex type that can iterate: {previous_func_output}")
        next_func_input_types = list(input_params.values())
        logger.debug(f"Function {next_function.__name__} expects input of {next_func_input_types}")
        prev_f_unpacked_annot = unpack_annotation(previous_func_output)

        if len(prev_f_unpacked_annot) > len(next_func_input_types) and 'args' not in input_signature_params:
            raise ValueError(
                f"Function {next_function.__name__} is going to receive too many positional arguments: "
                f"{prev_f_unpacked_annot}")

        # 2) The output iterable has exactly same # of constituent members as inputs, in which case we need to check
        # annotations are same.
        if len(prev_f_unpacked_annot) == len(next_func_input_types):
            for index, (out_type, b_arg_type) in enumerate(zip(prev_f_unpacked_annot, next_func_input_types)):
                if out_type != b_arg_type:
                    raise ValueError(
                        f"Mismatch in input iterable @ pos {index} to {next_function.__name__} - output "
                        f"type {out_type} != {b_arg_type} ")

        # 3) We have an output iterable with fewer constituent members than input, in which case this CAN be valid IF
        # we have a) more than enough values for non-optional values and b) any remaining values have same type as
        # what's expected for corresponding optional values
        logger.debug(F"b_arg_types: {next_func_input_types}")
        if len(prev_f_unpacked_annot) < len(next_func_input_types):
            raise ValueError(
                f"Function {next_function.__name__} has at least {len(next_func_input_types)} required positional "
                f"args, yet output value of preceding function only has {len(prev_f_unpacked_annot)} members")

        logger.debug(f"Optional inputs for {next_function.__name__}: {prev_f_unpacked_annot}")
        for index, opt_inp in enumerate(prev_f_unpacked_annot):
            if is_optional_annotation(next_func_input_types[index]):
                if next_func_input_types[index] == opt_inp:
                    pass
                elif not type_allowed_under_optional_annot(opt_inp, next_func_input_types[index]):
                    raise ValueError(
                        f"Positional argument # {index} for function {next_function.__name__} is Union "
                        f"({next_func_input_types[index]}) but doesn't allow type {opt_inp}")


def is_iterable_of_primitives(value: Any) -> bool:
    """Check if the value is an iterable of primitives (excluding strings/bytes).

    Args:
        value (Any): The value to check.

    Returns:
        bool: True if the value is an iterable of primitives, False otherwise.
    """
    # Check if the value is an iterable but not a string/bytes/bytearray
    return isinstance(value, (tuple, list)) and not isinstance(value, (str, bytes, bytearray))


def find_cycles_and_for_each_paths(graph, root_node_id: Any):
    cycles = list(nx.simple_cycles(graph))
    cycle_nodes = list(itertools.chain.from_iterable(cycles))
    print(f"* find_cycles_and_for_each_paths - cycles: {cycles}")
    print(f"** Cycle nodes: {cycle_nodes}")
    for_each_paths = []

    # def dfs(node, path, visited):
    #     print(f"dfs - node {node} / path {path} / visited {visited}")
    #     if node in visited:
    #         return
    #     visited.add(node)
    #     path.append(node)
    #
    #     for_each_nodes = graph.nodes[node].get('for_each', False)
    #     print(f"\tIs for_each nodes: {for_each_nodes}")
    #
    #     if graph.nodes[node].get('for_each', False):
    #         if node in cycle_nodes:
    #             raise ValueError(f"For_each node {node} is inside a cycle.")
    #         for neighbor in graph.successors(node):
    #             is_aggregator = graph.nodes[neighbor].get('aggregator', False)
    #             print(f"\tProcess neighbor: {neighbor} - is_aggregator: {is_aggregator}")
    #             if is_aggregator:
    #                 for_each_paths.append((node, neighbor))
    #                 return
    #             elif graph.out_degree(neighbor) > 1:
    #                 raise ValueError(f"Encountered a branch at node {neighbor} while traversing from for_each node {node}.")
    #             else:
    #                 dfs(neighbor, path, visited)
    #         raise ValueError(f"No aggregator node found for for_each node {node}.")
    #
    #     for neighbor in graph.successors(node):
    #         dfs(neighbor, path, visited)

    # visited = set()
    # # Look for for_each nodes
    # for node in graph.nodes:
    #     print(f"Process node {node} in graph.nodes")
    #     if graph.in_degree(node) == 0:  # Start traversal from root nodes
    #         dfs(node, [], visited)

    def dfs(node_id, path, is_for_each):

        print(f"Analyze node {node_id} with path {path} for each {is_for_each}")
        path.append(node_id)

        if graph.nodes[node_id].get('for_each', False):
            is_for_each = True

        if node_id in cycle_nodes:
            raise ValueError(f"For_each node {node_id} is inside a cycle.")

        if graph.nodes[node_id].get('aggregator', False) and is_for_each:
            for_each_paths.append(tuple(path.copy()))
            is_for_each = False

        if graph.out_degree(node_id) > 1 and is_for_each:
            raise ValueError(f"Encountered a branch at node {node_id} while traversing from a for_each node.")

        for neighbor in graph.successors(node_id):
            dfs(neighbor, path, is_for_each)

        path.pop()

    dfs(root_node_id, [], False)

    cycle_tuples = [(cycle[0], cycle[-1]) for cycle in cycles]
    print(f"*** Cycle tuples: {cycle_tuples}")
    return cycle_tuples, for_each_paths
