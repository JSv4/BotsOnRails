import unittest
from typing import Tuple, Optional, List, Union, NoReturn, Dict, Callable

from nlx.decorators import node_for_tree
from nlx.tree import ExecutionTree


class TestTypeChecking(unittest.TestCase):
    def test_override_noreturn_type(self):
        """
        Make sure we can't specify an override return value for node typed to return NoReturn
        """

        tree = ExecutionTree()
        node = node_for_tree(tree)

        @node(start_node=True)
        def do_nothing_node(**kwargs) -> NoReturn:
            print("I'm the laziest function you've ever seen!")

        tree.compile(type_checking=True)

        with self.assertRaises(ValueError):
            tree.run_from_node('do_nothing_node', override_output="I shouldn't have an output")

    def test_no_cycles(self):
        """
        Make sure we can't have a true cycle (circular pathways are OK, as long as they go one direction and stop)
        """

        tree = ExecutionTree()
        node = node_for_tree(tree)

        @node(start_node=True, next_nodes='eating')
        def snake(val: str) -> str:
            return val

        @node(next_nodes='tail')
        def eating(val: str) -> str:
            return val

        @node(next_nodes='snake')
        def tail(val: str) -> str:
            return val

        with self.assertRaises(ValueError) as e:
            tree.compile(type_checking=True)

        assert 'we don\'t support circular flows' in str(e.exception)

