import collections.abc
import json
import uuid
from typing import Any, Callable, get_type_hints, NoReturn, List, get_origin, Union, get_args, Tuple


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
    print(f"Is annotation {annotation} (type {type(annotation)}) optional?")
    print(f"Origin is {get_origin(annotation)}")
    print(f"Args: {get_args(annotation)}")
    return get_origin(annotation) is Union and type(None) in get_args(annotation)

def type_allowed_under_optional_annot(type_annot, annotation) -> bool:
    for arg in get_args(annotation):
        if type_annot == arg:
            return True
    return False

def match_types(
        previous_func_output: Any,
        next_function: Callable,
        unpack_output: bool = True
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
    input_params.pop('return')  # We don't want return type on the input annotation hint
    print("Match types")
    print(input_params)
    print(previous_func_output)
    print(get_origin(previous_func_output))
    print(isinstance(get_origin(previous_func_output), (Callable, collections.abc.Callable)))
    print(isinstance(get_origin(previous_func_output), (tuple, Tuple)))
    print(get_origin(previous_func_output) == tuple)
    annot = get_origin(previous_func_output)
    print("is_tuple_annotation: " + str(is_tuple_annotation(annot)))
    print("is_list_annotation: " + str(is_list_annotation(annot)))
    print("is_str_or_bytes_str: " + str(is_not_str_or_bytes_str(annot)))
    print("is_complex_iterable_annot: " + str(unpackable_annotation(annot)))

    if not unpackable_annotation(get_origin(previous_func_output)):
        print(f"input_params: ({type(input_params)}) {input_params}")
        print(f"input_params.items: {input_params.items()}")
        if previous_func_output == NoReturn:
            if input_params == {}:
                pass  # no actual inputs
            elif len(input_params.items()) != 0:
                raise ValueError(f"Function preceding {next_function.__name__} has return type of NoReturn yet function "
                                 f"expects inputs of {type(input_params)}")
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
    elif not unpack_output:
        if len(input_params.items()) == 1:
            if previous_func_output != list(input_params.values())[0]:
                raise ValueError(f"Mismatched input between output ({previous_func_output} and next input "
                                 f"({list(input_params.values())[0]}). YOU ARE USING FLAG unpack_output.")
        else:
            raise ValueError(f"Return type is an iterable, but you explicitly instructed us not to unpack it (with "
                             f"unpack_output=False), yet next function expects"
                             f"multiple positional args - {input_params.values()}. Did you mean to set "
                             f"unpack_output=True?")
    else:
        print(f"Output of preceding function is a complex type that can iterate: {previous_func_output}")
        next_func_input_types = list(input_params.values())
        print(f"Function {next_function.__name__} expects input of {next_func_input_types}")
        prev_f_unpacked_annot = unpack_annotation(previous_func_output)

        # We have a couple different cases to handle here
        # 1) We have an output iterable with more constituent members than positional args in next function (that's an
        # error)
        if len(prev_f_unpacked_annot) > len(next_func_input_types):
            raise ValueError(f"Function {next_function.__name__} is going to receive too many positional arguments: "
                             f"{prev_f_unpacked_annot}")

        # 2) The output iterable has exactly same # of constituent members as inputs, in which case we need to check
        # annotations are same.
        if len(prev_f_unpacked_annot) == len(next_func_input_types):
            for index, (out_type, b_arg_type) in enumerate(zip(prev_f_unpacked_annot, next_func_input_types)):
                if out_type != b_arg_type:
                    raise ValueError(f"Mismatch in input iterable @ pos {index} to {next_function.__name__} - output "
                                     f"type {out_type} != {b_arg_type} ")

        # 3) We have an output iterable with fewer constituent members than input, in which case this CAN be valid IF
        # we have a) more than enough values for non-optional values and b) any remaining values have same type as
        # what's expected for corresponding optional values
        print(F"b_arg_types: {next_func_input_types}")

        # TODO - need to handle Union rather than Optional here because Optional is just alias for Union with None.

        if len(prev_f_unpacked_annot) < len(next_func_input_types):
            raise ValueError(f"Function {next_function.__name__} has at least {len(next_func_input_types)} required positional "
                             f"args, yet output value of preceding function only has {len(prev_f_unpacked_annot)} members")

        print(f"Optional inputs for {next_function.__name__}: {prev_f_unpacked_annot}")
        for index, opt_inp in enumerate(prev_f_unpacked_annot):
            if is_optional_annotation(next_func_input_types[index]):
                if next_func_input_types[index] == opt_inp:
                    pass
                elif not type_allowed_under_optional_annot(opt_inp, next_func_input_types[index]):
                    raise ValueError(f"Positional argument # {index} for function {next_function.__name__} is Union "
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
