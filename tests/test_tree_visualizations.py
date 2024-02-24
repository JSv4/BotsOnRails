import tempfile
import unittest
from pathlib import Path
from typing import Tuple, Optional, List, Union, NoReturn, Dict, Callable

from nlx.decorators import node_for_tree
from nlx.tree import ExecutionTree

fixture_dir = Path(__file__).parent / 'fixtures'
visualizations_dir = fixture_dir / "visualizations"
nx_filename = "test_nx_visualization.png"


class TestTreeValidations(unittest.TestCase):

    def setUp(self):
        self.tree = ExecutionTree()
        node = node_for_tree(self.tree)

        @node(start_node=True, next_nodes="b")
        def a(**kwargs) -> str:
            return "Hello!"

        @node(next_nodes="c", wait_for_approval=True)
        def b(arg1: str, **kwargs) -> str:
            return arg1

        @node()
        def c(arg1: str, **kwargs) -> str:
            return arg1

    def test_nx_visualization(self):
        with tempfile.TemporaryDirectory() as tmpdirname:

            target_file_path = (Path(tmpdirname) / nx_filename).__str__()
            self.tree.visualize_via_nx(
                save_to_disk=target_file_path
            )
            self.assertEqual(
                open(target_file_path, "rb").read(),
                open((visualizations_dir / nx_filename).__str__(), "rb").read()
            )

    def test_nx_visualization_no_compile(self):

        self.tree.compiled = False

        with tempfile.TemporaryDirectory() as tmpdirname:
            target_file_path = (Path(tmpdirname) / nx_filename).__str__()
            self.tree.visualize_via_nx(
                save_to_disk=target_file_path
            )
            self.assertEqual(
                open(target_file_path, "rb").read(),
                open((visualizations_dir / nx_filename).__str__(), "rb").read()
            )
