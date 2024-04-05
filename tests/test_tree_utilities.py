import unittest
from typing import NoReturn


from BotsOnRails.decorators import step_decorator_for_path
from BotsOnRails.nodes import BaseNode
from BotsOnRails.rails import ExecutionPath


class TestTreeUtilities(unittest.TestCase):

    def test_lookup_node_fail(self):
        """
        Make sure we can't specify an override return value for node typed to return NoReturn
        """

        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True)
        def do_nothing_node(**kwargs) -> NoReturn:
            print("I'm the laziest function you've ever seen!")

        self.assertIsNone(tree.get_node("Bob is your uncle"))
        self.assertIsInstance(tree.get_node("do_nothing_node"), BaseNode)
