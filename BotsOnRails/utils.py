import inspect
import itertools
import json
import logging
import uuid
import networkx as nx
from typing import Any, Callable, get_type_hints, NoReturn, List, get_origin, Union, get_args, Tuple, _GenericAlias

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
        aggregator: bool = False,
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
    print(f"Input parameters for next func {next_function.__name__}: {input_params}")
    input_signature_params = inspect.signature(next_function).parameters

    # We don't want return type on the input annotation hint
    if 'return' in input_params:
        input_params.pop('return')
    annot = get_origin(previous_func_output)

    if aggregator:
        input_param_type = list(input_params.values())
        if len(input_param_type) != 1:
           raise ValueError(f"Function {next_function.__name__} following an aggregator node expects multiple inputs"
                            f"but we only support 1 - a list.")
        elif isinstance(input_param_type[0], _GenericAlias):
                if input_param_type[0].__origin__ not in (list, tuple):
                    raise ValueError(
                        f"Function following an aggregator should expect a single input tuple or list, not "
                        f"{input_param_type}")
        elif not isinstance(input_param_type[0], (tuple, list, Tuple, List)):
            raise ValueError(f"Function following an aggregator should expect a single input tuple or list, not "
                             f"{type(input_param_type[0])}")

        elif previous_func_output != unpack_annotation(input_param_type[0])[0]:
            raise ValueError(f"Function following an aggregator should expect a single list or tuple with inner type "
                             f"composed the type output signature of the aggregator function - e.g. if aggregator "
                             f"returns int, next function should expect list[int] or tuple[int]. Your aggregator "
                             f"returns {previous_func_output} and next function expects"
                             f" {unpack_annotation(input_param_type[0])[0]}")
        else:
            pass

    elif not unpackable_annotation(get_origin(previous_func_output)):
        if previous_func_output == NoReturn:
            if input_params == {}:
                pass  # no actual inputs
            elif len(input_params.values()) != 0:
                raise ValueError(
                    f"Function preceding {next_function.__name__} has return type of NoReturn yet function "
                    f"expects inputs of {type(input_params)}")
        elif 'args' in input_signature_params:
            # If we have *args in next function, we're cool with any positional arguments.
            pass
        elif len(input_params.values()) == 1:
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

        contents_of_iterable = unpack_annotation(previous_func_output)

        if len(input_params.items()) == 1:
            if contents_of_iterable[0] != list(input_params.values())[0]:
                raise ValueError(f"for_each_loop - Mismatched input between output ({previous_func_output} and next input "
                                 f"({list(input_params.values())[0]}). YOU ARE USING FLAG unpack_output.")
        else:
            raise ValueError(f"Return type to {next_function.__name__} is an iterable, and you want to loop over each "
                             f"of its constituent elements. We check that the constituent parts of the list or tuple "
                             f"are what's expected as an input for the next function, but it expects multiple inputs.")

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
        next_func_input_types = list(input_params.values())
        prev_f_unpacked_annot = unpack_annotation(previous_func_output)

        # 1) If previous function has MORE annotations than what's expected in next function...
        if len(prev_f_unpacked_annot) > len(next_func_input_types) and 'args' not in input_signature_params:
            raise ValueError(
                f"Function {next_function.__name__} is going to receive too many positional arguments: "
                f"{prev_f_unpacked_annot}")

        # 2) OR, if output iterable has exactly same # of constituent members as inputs, we need to check
        # annotations at same index position are the same.
        elif len(prev_f_unpacked_annot) == len(next_func_input_types):
            for index, (out_type, b_arg_type) in enumerate(zip(prev_f_unpacked_annot, next_func_input_types)):
                if out_type != b_arg_type:
                    raise ValueError(
                        f"Mismatch in input iterable @ pos {index} to {next_function.__name__} - output "
                        f"type {out_type} != {b_arg_type} ")

        # 3) OR, if we have an output iterable with fewer constituent members than input, this CAN be valid IF
        # we have a) more than enough values for non-optional values and b) any remaining values have same type as
        # what's expected for corresponding optional values
        elif len(prev_f_unpacked_annot) < len(next_func_input_types):
            logger.debug(F"b_arg_types: {next_func_input_types}")
            raise ValueError(
                f"Function {next_function.__name__} has at least {len(next_func_input_types)} required positional "
                f"args, yet output value of preceding function only has {len(prev_f_unpacked_annot)} members")

            print(f"Optional inputs for {next_function.__name__}: {next_func_input_types}")
            print(f"Outputs from previous f annot: {prev_f_unpacked_annot}")
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


def find_cycles_and_for_each_paths(graph, root_node_id: Any) -> tuple[list[str], list[str]]:
    cycles = list(nx.simple_cycles(graph))

    logger.debug(f"Checking for nested cycles in {cycles}")
    for i in range(len(cycles)):
        for j in range(i + 1, len(cycles)):
            logger.debug(f"Comparing cycle {cycles[i]} with cycle {cycles[j]}")
            if set(cycles[i]).issubset(cycles[j]) or set(cycles[j]).issubset(cycles[i]):
                logger.error("Nested cycles are not allowed.")
                raise ValueError("Nested cycles are not allowed.")

    cycle_nodes = list(itertools.chain.from_iterable(cycles))
    for_each_paths = []

    def dfs(node_id, path, for_each_start_id, visited):

        if node_id in visited:
            return
        visited.add(node_id)

        path.append(node_id)

        if graph.nodes[node_id].get('for_each', False):
            for_each_start_id = node_id

        if node_id in cycle_nodes and for_each_start_id is not None:
            raise ValueError(f"For_each node {node_id} is inside a cycle.")

        if graph.nodes[node_id].get('aggregator', False) and for_each_start_id is not None:
            print(f"Finished for_each cycle path: {path}")
            cycle_start_index = path.index(for_each_start_id)
            print(f"Cycle start index: {cycle_start_index}")
            cycle_end_index = path.index(node_id)
            print(f"Cycle end index: {cycle_end_index}")
            total_cycle = path[cycle_start_index:cycle_end_index+1]
            print(f"Total cycle: {total_cycle}")
            for_each_paths.append(total_cycle)
            for_each_start_id = None

        if graph.out_degree(node_id) > 1 and for_each_start_id is not None:
            raise ValueError(f"Encountered a branch at node {node_id} while traversing from for_each node starting at {node_id}")

        successor_nodes = list(graph.successors(node_id))
        if len(successor_nodes) == 0 and for_each_start_id is not None:
            raise ValueError(f"No aggregator node found for for_each branch starting at {for_each_start_id}")
        else:
            for neighbor in graph.successors(node_id):
                dfs(neighbor, path, for_each_start_id, visited)

        path.pop()

    visited = set()
    dfs(root_node_id, [], None, visited)

    cycle_tuples = [(cycle[0], cycle[-1]) for cycle in cycles]
    return cycle_tuples, for_each_paths


from typing import Union, Optional, get_args, get_origin


def is_union_type(target_type) -> bool:
    origin = get_origin(target_type)
    return origin is Union

def is_optional_type(target_type) -> bool:
    origin = get_origin(target_type)
    return origin is Optional

def check_union_or_optional_overlaps(input_type, output_type):
    """
    Check if two typing annotations (input and output) are potentially compatible.

    This function considers Union types and Optional types. If either the input or output
    is a Union type, it checks for any overlap between the allowed types. If either is an
    Optional type, it checks compatibility with the non-None type.

    Args:
        input_type: The input typing annotation.
        output_type: The output typing annotation.

    Returns:
        bool: True if the input and output types are potentially compatible, False otherwise.

    Examples:
        >>> check_union_or_optional_overlaps(str, Optional[str])
        True
        >>> check_union_or_optional_overlaps(int, Union[None, str, int])
        True
        >>> check_union_or_optional_overlaps(float, Union[str, int])
        False
        >>> check_union_or_optional_overlaps(Union[str, int], Union[int, float])
        True
        >>> check_union_or_optional_overlaps(Optional[str], int)
        False
    """
    # Check if either input or output is a Union type
    input_origin = get_origin(input_type)
    output_origin = get_origin(output_type)

    if input_origin is Union or output_origin is Union:
        # If both are Union types, check if there's any overlap
        if input_origin is Union and output_origin is Union:
            input_args = get_args(input_type)
            output_args = get_args(output_type)
            return any(arg in output_args for arg in input_args)

        # If only one is a Union type, check if the other is in the Union
        if input_origin is Union:
            return output_type in get_args(input_type)
        else:
            return input_type in get_args(output_type)

    # Check if either input or output is an Optional type
    if input_origin is Union and type(None) in get_args(input_type):
        return check_union_or_optional_overlaps(get_args(input_type)[0], output_type)

    if output_origin is Union and type(None) in get_args(output_type):
        return check_union_or_optional_overlaps(input_type, get_args(output_type)[0])

    # If neither is a Union or Optional, check for equality
    return input_type == output_type