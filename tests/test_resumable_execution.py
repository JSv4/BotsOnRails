import unittest
from typing import NoReturn

from BotsOnRails.decorators import node_for_tree
from BotsOnRails.tree import ExecutionTree
from BotsOnRails.types import SpecialTypes


class TestResumeExecution(unittest.TestCase):

    def test_resume_after_approve(self):

        tree = ExecutionTree()
        node = node_for_tree(tree)

        @node(next_nodes={'open': 'open', 'turn_back': 'turn_back'}, start_node=True)
        def explore_the_cave(route: int, **kwargs) -> NoReturn:
            print("You have been exploring the cave system for hours when you stumble across a an ancient-looking "
                  "metal door flecked with veins of a strange, glowing green mineral. A symbol that looks vaguely like "
                  "a human skull with a more oblong back can just be made out, barely raised from the ancient surface.")
            print("Which what do you do?[turn back] or [open] the door?")
            decision = 'open' if route == 1 else 'turn_back'
            return decision

        @node()
        def turn_back(*args, **kwargs) -> str:
            print("Like a scared, meek little kitten you turn back for higher ground. A sinkhole opens up and swallows "
                  "your cautious self. As you sink into the depths, you think, 'I shoulda stayed on the bus like Ms. "
                  "Haltleson told me to.' No snack time for you.")
            return "You are dead. And lame."

        @node(wait_for_approval=True, next_nodes={"yes": "press_the_button", "no": "turn_back"})
        def open(*args, **kwargs) -> str:
            print("Behind the door is a polished rock face of deepest ebony. Those strange green mineral veins"
                  "cris-cross the surface and seem to gather size and intensity as they flow toward a large round"
                  "raised gem at the center. It looks like a button.")
            print(f"Are you sure you want to press it? [yes] or [no]?")
            return "no"  # default return

        @node()
        def press_the_button(*args, **kwargs) -> str:
            print(f"Woah... the earth starts to shake. You look around and think, 'yah, we're doing this!' If only you "
                  f"knew what it was you had unleashed. And yet... you find yourself lacking all curiosity. Why "
                  f"shouldn't they all suffer. They made you miss snack time.")
            return "Everyone is dead."

        tree.compile(type_checking=True)
        results = tree.run(1)
        assert results == SpecialTypes.EXECUTION_HALTED

        halted_state = tree.model_dump()
        destroy_the_world = tree.run_from_node(
            'open',
            prev_execution_state=halted_state,
            override_output='yes'
        )
        assert destroy_the_world == "Everyone is dead."


if __name__ == '__main__':
    unittest.main()
