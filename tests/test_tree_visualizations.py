import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Tuple, Optional, List, Union, NoReturn, Dict, Callable

import BotsOnRails

from BotsOnRails.decorators import step_decorator_for_path
from BotsOnRails.rails import ExecutionPath

fixture_dir = Path(__file__).parent / 'fixtures'
visualizations_dir = fixture_dir / "visualizations"
nx_filename = "test_nx_visualization.png"


class TestTreeValidations(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.tree = ExecutionPath()
        node = step_decorator_for_path(self.tree)

        @node(path_start=True, next_step="b")
        def a(**kwargs) -> str:
            return "Hello!"

        @node(next_step="c", wait_for_approval=True)
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

        with self.assertLogs(BotsOnRails.rails.__name__, level='WARNING') as cm:
            with tempfile.TemporaryDirectory() as tmpdirname:
                target_file_path = (Path(tmpdirname) / nx_filename).__str__()
                self.tree.visualize_via_nx(
                    save_to_disk=target_file_path
                )
                self.assertEqual(
                    open(target_file_path, "rb").read(),
                    open((visualizations_dir / nx_filename).__str__(), "rb").read()
                )
        self.assertEqual(cm.output, [f'WARNING:{BotsOnRails.rails.__name__}:You must call .compile() after adding the '
                                     f'last node before you can visualize the Execution Tree. Calling it for you!',
                                     ])

    def test_mermaid_diagram_without_compile(self):

        self.tree._clear_execution_state()
        self.tree.compiled = False

        with self.assertLogs(BotsOnRails.rails.__name__, level='WARNING') as cm:
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
        self.assertEqual(cm.output, [f'WARNING:{BotsOnRails.rails.__name__}:You must call .compile() after adding the '
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

    def test_tree_dump(self):

        output_with_ids = self.tree.dump_json()
        output_dict = json.loads(output_with_ids)
        output_dict.pop("id")
        output_dict.pop("root_node_id")
        output_dict.pop("node_names")
        output_dict.pop("node_ids")
        for name, obj in output_dict['nodes'].items():
            obj.pop("id")

        generated_output = json.dumps(output_dict, indent=4)
        expected_output = (visualizations_dir / "tree_dump.json").read_text()

        self.assertEqual(
            expected_output,
            generated_output
        )
