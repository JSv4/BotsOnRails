import unittest
from typing import Tuple, Optional, List, Union, NoReturn, Dict, Callable

import BotsOnRails

from BotsOnRails.decorators import step_decorator_for_path
from BotsOnRails.rails import ExecutionPath


class TestTreeValidations(unittest.TestCase):
    def test_override_noreturn_type(self):
        """
        Make sure we can't specify an override return value for node typed to return NoReturn
        """

        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True)
        def do_nothing_node(**kwargs) -> NoReturn:
            print("I'm the laziest function you've ever seen!")

        tree.compile(type_checking=True)

        with self.assertRaises(ValueError):
            tree.run_from_step('do_nothing_node', override_output="I shouldn't have an output")

    def test_no_cycles(self):
        """
        Make sure we can't have a true cycle (circular pathways are OK, as long as they go one direction and stop)
        """

        tree = ExecutionPath(allow_cycles=False)
        node = step_decorator_for_path(tree)

        @node(path_start=True, next_step='eating')
        def snake(val: str) -> str:
            return val

        @node(next_step='tail')
        def eating(val: str) -> str:
            return val

        @node(next_step='snake')
        def tail(val: str) -> str:
            return val

        with self.assertRaises(ValueError) as e:
            tree.compile(type_checking=True)

        assert 'allow_cycles is set to False but the tree has cycles' in str(e.exception)

    def test_add_non_node_as_node(self):
        tree = ExecutionPath()

        with self.assertRaises(ValueError):
            tree.add_node("Yo", "A Node I am not", root=True)

    def test_register_multiple_results(self):
        tree = ExecutionPath()

        # Make sure we can't call handle_output twice in the tree
        tree.handle_output("Results")
        with self.assertRaises(ValueError):
            tree.handle_output("Second Result")

    def test_register_multiple_root_nodes(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True, next_step='b')
        def a(val: str) -> str:
            return val

        with self.assertRaises(ValueError):
            @node(path_start=True)
            def b(val: str) -> str:
                return val

    def test_non_unique_node_name(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True, next_step='b')
        def a(val: str) -> str:
            return val

        # Can't have the same name twice, though we could register same function twice if we specify a name="..." param
        # in decorator
        with self.assertRaises(ValueError):
            @node(path_start=True)
            def a(val: str) -> str:
                return val

    def test_run_without_compile(self):

        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True)
        def a(val: str, **kwargs) -> str:
            return val

        with self.assertLogs(BotsOnRails.rails.__name__, level='WARNING') as cm:
            tree.run("Hello")

        self.assertEqual(cm.output, [f'WARNING:{BotsOnRails.rails.__name__}:You must call .compile() after adding the last '
                                     f'node before you can use the Execution Tree. Calling it for you!',
                                     ])

    def test_run_from_step_without_compile(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True)
        def a(val: str, **kwargs) -> str:
            return val

        with self.assertLogs(BotsOnRails.rails.__name__, level='WARNING') as cm:
            result = tree.run_from_step("a", override_output="Goodbye")

        self.assertEqual(result, "Goodbye")
        self.assertEqual(cm.output, [f'WARNING:{BotsOnRails.rails.__name__}:You must call .compile() after adding the last '
                                     f'node before you can use the Execution Tree. Calling it for you!',
                                     ])

    def test_cant_override_output_for_noreturn_node(self):
        """
        Make sure if a node has a NoReturn type, you can't force a return type
        :return:
        """

        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True)
        def a(val: str, **kwargs) -> NoReturn:
            print("I am a waste of electrons!")

        tree.compile()

        with self.assertRaises(ValueError):
            tree.run_from_step("a", override_output="I shouldn't return anything tho!")

    def test_cant_override_output_with_wrong_type(self):
        """
        Make sure if a node has a return type other than NoReturn, you can only override it with same type.
        """

        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True)
        def a(**kwargs) -> float:
            return 1.01

        tree.compile()

        assert tree.run() == 1.01

        with self.assertRaises(ValueError):
            tree.run_from_step("a", override_output=bool)

    def test_required_vals_for_run_from_step(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True, next_step="b")
        def a(**kwargs) -> str:
            return "Hello!"

        @node(next_step="c", wait_for_approval=True)
        def b(arg1: str, **kwargs) -> str:
            return arg1

        @node()
        def c(arg1: str, **kwargs) -> str:
            return arg1

        with self.assertRaises(ValueError):
            tree.run_from_step("b")