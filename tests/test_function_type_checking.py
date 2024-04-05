import unittest
from typing import Tuple, Optional, List, Union, NoReturn, Dict, Callable

from BotsOnRails.decorators import step_decorator_for_path
from BotsOnRails.rails import ExecutionPath
from BotsOnRails.utils import check_union_or_optional_overlaps


class TestTypeChecking(unittest.TestCase):
    def test_simple_types(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> Tuple[int, str]: return 1, "test"

        @node()
        def b(x: int, y: str, **kwargs) -> str:
            return f"{x}{y}"

        tree.compile(type_checking=True)
        results = tree.run()
        assert results == '1test'

    def test_optional_types(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> Tuple[int, Optional[str]]: return 1, None

        @node()
        def b(x: int, y: Optional[str] = None, **kwargs) -> bool:
            return x == 1 and y is None

        tree.compile(type_checking=True)
        assert tree.run()

    def test_mismatched_types(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b')
        def a() -> Tuple[int, str]: return (1, "test")

        @node()
        def b(x: str, y: int) -> NoReturn: pass

        with self.assertRaises(ValueError):
            tree.compile(type_checking=True)

        # Not testing run because we can't run this tree

    def test_incorrect_argument_count(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b')
        def a() -> Tuple[int, str, float]: return (1, "test", 2.0)

        @node()
        def b(x: int, y: str) -> NoReturn: pass

        with self.assertRaises(ValueError):
            tree.compile(type_checking=True)

        # Not testing run because we can't run this tree

    def test_handling_list(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', unpack_output=False, path_start=True)
        def a(**kwargs) -> List[int]: return [1, 2, 3]

        @node()
        def b(x: List[int], **kwargs) -> int:
            return sum(x)

        tree.compile(type_checking=True)
        assert tree.run() == 6

    def test_handling_union(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> Union[int, str]: return "test"

        @node()
        def b(x: Union[int, str], **kwargs) -> str:
            return str(x)

        tree.compile(type_checking=True)
        assert tree.run() == 'test'

    def test_handling_optional_with_none(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> Optional[int]: return None

        @node()
        def b(x: Optional[int], **kwargs) -> NoReturn: pass

        tree.compile(type_checking=True)
        assert tree.run() is None

    def test_nested_tuples(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> Tuple[Tuple[int, str], bool]: return ((1, "nested"), True)

        @node()
        def b(x: Tuple[int, str], y: bool, **kwargs) -> str:
            return f"{x[0]}-{x[1]}-{y}"

        tree.compile(type_checking=True)
        assert tree.run() == '1-nested-True'

    def test_list_of_tuples(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True, unpack_output=False)
        def a(**kwargs) -> List[Tuple[int, str]]: return [(1, "one"), (2, "two")]

        @node(unpack_output=False)
        def b(x: List[Tuple[int, str]], **kwargs) -> int:
            return len(x)

        tree.compile(type_checking=True)
        assert tree.run() == 2

    def test_complex_union(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True, unpack_output=False)
        def a(**kwargs) -> Union[Tuple[int, str], List[str], str]: return ["hello", "world"]

        @node()
        def b(x: Union[Tuple[int, str], List[str], str], **kwargs) -> int:
            if isinstance(x, list):
                return len(x)
            return 0

        tree.compile(type_checking=True)
        assert tree.run() == 2

    def test_default_none_with_optional(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> Optional[str]: return None

        @node()
        def b(x: Optional[str] = "default", **kwargs) -> str:
            return x

        tree.compile(type_checking=True)
        print(f"test_default_none_with_optional: {tree.run()}")
        assert tree.run() is None

    def test_mixed_types_with_optional(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> Tuple[int, Optional[str], bool]: return (1, None, True)

        @node()
        def b(x: int, y: Optional[str], z: bool, **kwargs) -> bool:
            return x == 1 and y is None and z is True

        tree.compile(type_checking=True)
        assert tree.run()

    def test_dict_output_input(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> Dict[str, int]: return {"one": 1, "two": 2}

        @node()
        def b(x: Dict[str, int], **kwargs) -> int:
            return sum(x.values())

        tree.compile(type_checking=True)
        assert tree.run() == 3

    def test_multiple_optional_outputs(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> Tuple[Optional[int], Optional[str]]: return (None, "test")

        @node()
        def b(x: Optional[int], y: Optional[str], **kwargs) -> str:
            return y if x is None else "fail"

        tree.compile(type_checking=True)
        assert tree.run() == "test"

    def test_callable_as_input(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> Callable[[int], int]: return lambda x: x * 2

        @node()
        def b(x: Callable[[int], int], **kwargs) -> int:
            return x(10)

        tree.compile(type_checking=True)
        assert tree.run() == 20

    def test_nested_collections(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True, unpack_output=False)
        def a(**kwargs) -> List[Dict[str, Tuple[int, str]]]: return [{"key": (1, "value")}]

        @node(unpack_output=False)
        def b(x: List[Dict[str, Tuple[int, str]]], **kwargs) -> str:
            return x[0]["key"][1]

        tree.compile(type_checking=True)
        assert tree.run() == "value"

    def test_none_as_output_with_invalid_input(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> None: pass

        # This doesn't work because there's no positional arg for `None` return type.
        # Use typing.NoReturn if you intend function to return nothing
        @node()
        def b(**kwargs) -> str:
            return "success"

        # This is going to fail type checking for reasons mentioned above
        with self.assertRaises(ValueError):
            tree.compile(type_checking=True)

    ### Additional Union type checks
    def test_union_with_two_types(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> Union[int, str]: return 42

        @node()
        def b(x: Union[int, str], **kwargs) -> str:
            return f"Value: {x}"

        tree.compile(type_checking=True)
        assert tree.run() == "Value: 42"

    def test_union_with_none_type(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> Union[None, str]: return None

        @node()
        def b(x: Optional[str], **kwargs) -> str:
            return x or "No value"

        tree.compile(type_checking=True)
        assert tree.run() == "No value"

    def test_union_with_multiple_types(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> Union[int, str, bool]: return True

        @node()
        def b(x: Union[int, str, bool], **kwargs) -> str:
            return str(x)

        tree.compile(type_checking=True)
        assert tree.run() == "True"

    def test_union_returning_different_types(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True, unpack_output=False)
        def a(**kwargs) -> Union[str, int]:
            return "test" if kwargs.get('to_str', False) else 1

        @node(next_step='d')
        def b(x: str | int, **kwargs) -> str:
            return f"String: {x}"

        # @node(next_step='d')
        # def c(x: int, **kwargs) -> str:
        #     return f"Int: {x}"

        @node()
        def d(x: str, **kwargs) -> None:
            print(x)

        tree.compile(type_checking=True)
        # Assuming there's logic to choose the correct path based on 'a's output
        assert tree.run() is None  # This test assumes dynamic path selection based on output

    def test_union_with_callable(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> Union[Callable[[int], int], str]: return lambda x: x + 1

        @node()
        def b(x: Union[Callable[[int], int], str], **kwargs) -> int:
            if callable(x):
                return x(5)
            return 0

        tree.compile(type_checking=True)
        assert tree.run() == 6

    def test_union_with_collections(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True, unpack_output=False)
        def a(**kwargs) -> Union[List[int], Dict[str, int]]:
            return [1, 2, 3]

        @node()
        def b(x: Union[List[int], Dict[str, int]], **kwargs) -> int:
            if isinstance(x, list):
                return sum(x)
            elif isinstance(x, dict):
                return sum(x.values())
            return 0

        tree.compile(type_checking=True)
        assert tree.run() == 6

    def test_union_with_different_collections(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True, unpack_output=False)
        def a(**kwargs) -> Union[List[int], Tuple[int, ...]]: return (1, 2, 3)

        @node()
        def b(x: Union[List[int], Tuple[int, ...]], **kwargs) -> int:
            return len(x)

        tree.compile(type_checking=True)
        assert tree.run() == 3

    def test_union_with_none_as_explicit_option(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> Union[int, None]: return None

        @node()
        def b(x: Optional[int], **kwargs) -> str:
            return "None received" if x is None else "Int received"

        tree.compile(type_checking=True)
        assert tree.run() == "None received"

    def test_union_post_python_3_9_syntax(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True)
        def a(**kwargs) -> int | None: return None

        @node()
        def b(x: int | None, **kwargs) -> str:
            return "None" if x is None else str(x)

        tree.compile(type_checking=True)
        assert tree.run() == "None"

    def test_union_with_complex_nested_types(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(next_step='b', path_start=True, unpack_output=False)
        def a(**kwargs) -> Union[List[Tuple[int, str]], Dict[str, List[int]]]:
            return {"numbers": [1, 2, 3]}

        @node()
        def b(x: Union[List[Tuple[int, str]], Dict[str, List[int]]], **kwargs) -> int:
            if isinstance(x, dict):
                return sum(x["numbers"])
            return 0

        tree.compile(type_checking=True)
        assert tree.run() == 6

    def test_check_union_or_optional_overlaps(self):
        assert check_union_or_optional_overlaps(str, Optional[str]) == True
        assert check_union_or_optional_overlaps(int, Union[None, str, int]) == True
        assert check_union_or_optional_overlaps(float, Union[str, int]) == False
        assert check_union_or_optional_overlaps(Union[str, int], Union[int, float]) == True
        assert check_union_or_optional_overlaps(Optional[str], int) == False


if __name__ == '__main__':
    unittest.main()
