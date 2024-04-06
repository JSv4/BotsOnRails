import unittest

from BotsOnRails.decorators import step_decorator_for_path
from BotsOnRails.rails import ExecutionPath
from BotsOnRails.types import SpecialTypes


class TestTreeExecution(unittest.TestCase):

    def test_resume_execution_dont_override(self):
        """
        Make sure we can't specify an override return value for node typed to return NoReturn
        """

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

        result = tree.run()

        # Tree return should indicate execution halted
        self.assertEqual(result, SpecialTypes.EXECUTION_HALTED)
        self.assertEqual(tree.get_node("b").input_data[0], "Hello!")

        # Get execution state - TODO - rename this
        exec_state = tree.model_dump()

        # IF we don't override the output of "b" - we'll just get its original output passed along the chain
        result_2 = tree.run_from_step(
            "b",
            prev_execution_state=exec_state
        )
        self.assertEqual(result_2, "Hello!")
        self.assertEqual(tree.get_node("b").input_data[0], "Hello!")

        # IF we DO override the output of "B" - we'll see that propagate further (here's where you could introduce
        # a corrected or approved value from a user or external function
        result_3 = tree.run_from_step(
            "b",
            override_output="Goodbye!"
        )
        self.assertEqual(result_3, "Goodbye!")

        # In this case, however, the input value is not set
        self.assertEqual(tree.get_node("b").input_data, SpecialTypes.NOT_PROVIDED)




