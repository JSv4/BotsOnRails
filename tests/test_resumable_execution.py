import unittest
from typing import NoReturn

from nlx.decorators import node_for_tree
from nlx.tree import ExecutionTree


class TestResumeExecution(unittest.TestCase):

    def test_resume_after_approve(self):

        tree = ExecutionTree()
        node = node_for_tree(tree)

        @node(next_nodes={'open': 'open', 'turn_back': 'turn_back'}, start_node=True)
        def explore_the_cave(*args, **kwargs) -> str:
            print("You have been exploring the cave system for hours when you stumble across a an ancient-looking "
                  "metal door flecked with veins of a strange, glowing green mineral. A symbol that looks vaguely like "
                  "a human skull with a more oblong back can just be made out, barely raised from the ancient surface.")
            decision = input("Which what do you do?[turn back] or [open] the door?")
            return decision

        @node()
        def turn_back(*args, **kwargs):
            print("Like a scared, meek little kitten you turn back for higher ground. A sinkhole opens up and swallows "
                  "your cautious self. As you fall into the depths, you think, 'I shoulda stayed on the bus like Ms. "
                  "Haltleson told me to.'")

        @node(wait_for_approval=True, next_nodes={"yes": "press_the_button", "no": "turn_back"})
        def open(*args, **kwargs):
            print("Behind the door is a polished rock face of deepest ebony. Those strange green mineral veins"
                  "cris-cross the surface and seem to gather size and intensity as they flow toward a large round"
                  "raised gem at the center. It looks like a button.")
            decision = input("Do you [press it] or [turn back]?")
            print(f"Are you sure you want to {decision}? [yes] or [no]?")
            return

        def press_the_button()
            print(f"Woah... the earth starts to shake. You look around and think, 'yah, we're doing this!' If only you "
                  f"knew what it was you had unleashed.")

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
