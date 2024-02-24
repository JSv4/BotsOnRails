import unittest
from typing import NoReturn


from nlx.decorators import node_for_tree
from nlx.nodes import BaseNode
from nlx.tree import ExecutionTree


class TestTreeUtilities(unittest.TestCase):

    def test_lookup_node_fail(self):
        """
        Make sure we can't specify an override return value for node typed to return NoReturn
        """

        tree = ExecutionTree()
        node = node_for_tree(tree)

        @node(start_node=True)
        def do_nothing_node(**kwargs) -> NoReturn:
            print("I'm the laziest function you've ever seen!")

        self.assertIsNone(tree.get_node("Bob is your uncle"))
        self.assertIsInstance(tree.get_node("do_nothing_node"), BaseNode)
