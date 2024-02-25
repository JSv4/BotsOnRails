import os
import tempfile
import unittest
from pathlib import Path
from typing import Tuple, Optional, List, Union, NoReturn, Dict, Callable

import nlx

from nlx.decorators import node_for_tree
from nlx.tree import ExecutionTree

fixture_dir = Path(__file__).parent / 'fixtures'
visualizations_dir = fixture_dir / "visualizations"
nx_filename = "test_nx_visualization.png"


class TestTreeValidations(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
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

        with self.assertLogs(nlx.tree.__name__, level='WARNING') as cm:
            with tempfile.TemporaryDirectory() as tmpdirname:
                target_file_path = (Path(tmpdirname) / nx_filename).__str__()
                self.tree.visualize_via_nx(
                    save_to_disk=target_file_path
                )
                self.assertEqual(
                    open(target_file_path, "rb").read(),
                    open((visualizations_dir / nx_filename).__str__(), "rb").read()
                )
        self.assertEqual(cm.output, [f'WARNING:{nlx.tree.__name__}:You must call .compile() after adding the '
                                     f'last node before you can visualize the Execution Tree. Calling it for you!',
                                     ])

    def test_mermaid_diagram_without_compile(self):

        self.tree._clear_execution_state()
        self.tree.compiled = False

        with self.assertLogs(nlx.tree.__name__, level='WARNING') as cm:
            self.assertEqual(
                self.tree.generate_mermaid_diagram(),
                None
            )

            halted_execution_diagram = """classDiagram
    class a {
        +String name = "a"
        +InputData input = ()
        +OutputData output = Hello!
    }
    class b {
        +String name = "b"
        +InputData input = ('Hello!',)
        +OutputData output = Hello!
        ----- !! HALT !! -----    }
    a --|> b : routed"""

            self.tree.run()
            diagram = self.tree.generate_mermaid_diagram()
            print(diagram)
            self.assertEqual(
                diagram,
                halted_execution_diagram
            )
        self.assertEqual(cm.output, [f'WARNING:{nlx.tree.__name__}:You must call .compile() after adding the '
                                     f'last node before you can visualize the Execution Tree. Calling it for you!',
                                     ])

    def test_mermaid_results_propagation(self):

        self.tree._clear_execution_state()
        self.assertEqual(
            self.tree.generate_mermaid_diagram(),
            None
        )

        halted_execution_diagram = """classDiagram
    class a {
        +String name = "a"
        +InputData input = ()
        +OutputData output = Hello!
    }
    class b {
        +String name = "b"
        +InputData input = ('Hello!',)
        +OutputData output = Hello!
        ----- !! HALT !! -----    }
    a --|> b : routed"""

        self.tree.run()
        self.assertEqual(
            self.tree.generate_mermaid_diagram(),
            halted_execution_diagram
        )

        full_execution_diagram = """classDiagram
    class a {
        +String name = "a"
        +InputData input = ()
        +OutputData output = Hello!
    }
    class b {
        +String name = "b"
        +InputData input = ('Hello!',)
        +OutputData output = Hello!
    }
    class c {
        +String name = "c"
        +InputData input = ('Hello!',)
        +OutputData output = Hello!
    }
    a --|> b : routed
    b --|> c : routed"""

        # Re-run but don't stop for approvals
        self.tree.run(auto_approve=True)
        print(f"`{self.tree.generate_mermaid_diagram()}`")
        self.assertEqual(
            self.tree.generate_mermaid_diagram(),
            full_execution_diagram
        )

    def test_graphviz_visuals(self):

        with tempfile.TemporaryDirectory() as tmpdirname:
            graphviz_filename = "graphviz_visual.dot"
            target_file_path = (Path(tmpdirname) / graphviz_filename).__str__()
            self.tree.visualize_via_graphviz(target_file_path)
            self.assertEqual(
                open(target_file_path, "rb").read(),
                open((visualizations_dir / graphviz_filename).__str__(), "rb").read()
            )
