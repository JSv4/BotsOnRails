import unittest
from typing import NoReturn

from nlx.decorators import node_for_tree
from nlx.tree import ExecutionTree


class TestNodeRouting(unittest.TestCase):
    def test_dict_router(self):
        tree = ExecutionTree()
        node = node_for_tree(tree)

        @node(next_nodes={"valid": "handle_valid", "invalid": "handle_invalid"}, start_node=True)
        def wrapped_dict_routing(input_str: str, **kwargs) -> str:
            return input_str

        @node()
        def handle_valid(input: str, **kwargs):
            return "Congrats!"

        @node()
        def handle_invalid(input: str, **kwargs):
            return "Aww, too bad"

        tree.compile()

        print("Result:")
        print(tree.run('valid'))

        assert tree.run('valid') == "Congrats!"
        assert tree.run('invalid') == "Aww, too bad"

    def test_functional_router(self):

        tree = ExecutionTree()
        node = node_for_tree(tree)

        def route_function(input: int) -> str:
            if input % 3 == 0:
                return 'comedy_comes_in_threes'
            return 'boring_boring'

        @node(
            start_node=True,
            next_nodes=route_function,
            func_router_possible_node_annot=[
                'boring_boring',
                'comedy_comes_in_threes'
            ]
        )
        def start_node(input: int, **kwargs) -> int:
            """
            Where we just want an initial router, we can pass through the input value to the output. You could
            also process the input here too, of course.
            """
            return input

        @node()
        def boring_boring(input: int, **kwargs) -> str:
            return "Have I told you about the benefits of a high fiber diet?"

        @node()
        def comedy_comes_in_threes(value: int, **kwargs) -> NoReturn:
            return f"Did I tell you the one about the {value} that walked into a bar?"

        tree.compile(type_checking=True)
        assert tree.run(4) == 'Have I told you about the benefits of a high fiber diet?'
        assert tree.run(3) == 'Did I tell you the one about the 3 that walked into a bar?'

    def test_functional_routing_with_no_annot(self):
        """
        Where we use a functional router, we require you provide a list of possible outputs so we can
        produce a visualization showing the possible execution pathway.
        """
        tree = ExecutionTree()
        node = node_for_tree(tree)

        def route_function(input: int) -> str:
            if input % 3 == 0:
                return 'comedy_comes_in_threes'
            return 'boring_boring'

        # Leave off the func_router_possible_node_annot
        @node(
            start_node=True,
            next_nodes=route_function
        )
        def start_node(input: int, **kwargs) -> int:
            return input

        @node()
        def boring_boring(input: int, **kwargs) -> str:
            return "Have I told you about the benefits of a high fiber diet?"

        @node()
        def comedy_comes_in_threes(value: int, **kwargs) -> NoReturn:
            return f"Did I tell you the one about the {value} that walked into a bar?"

        with self.assertRaises(ValueError):
            tree.compile(type_checking=True)


if __name__ == '__main__':
    unittest.main()
