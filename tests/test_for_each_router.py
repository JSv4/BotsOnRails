import unittest
from typing import List

from nlx.decorators import node_for_tree
from nlx.stores import StateStore, InMemoryStateStore
from nlx.tree import ExecutionTree


class TestForEachRouting(unittest.TestCase):
    def test_detect_nested_cycles(self):
        tree = ExecutionTree()
        node = node_for_tree(tree)

        @node(start_node=True, next_nodes=('FOR_EACH', 'process_item'))
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        @node(next_nodes='aggregate_results')
        def process_item(item: int, **kwargs) -> int:
            return item * 2

        @node(next_nodes=('FOR_EACH', 'process_item'), aggregator=True)
        def aggregate_results(results: List[int], **kwargs) -> List[int]:
            return results

        with self.assertRaises(ValueError) as cm:
            tree.compile(type_checking=True)
        self.assertEqual(str(cm.exception), "Nested cycles are not allowed.")

    def test_set_up_state_store(self):
        tree = ExecutionTree()
        node = node_for_tree(tree)

        @node(start_node=True, next_nodes=('FOR_EACH', 'process_item'))
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        @node(next_nodes='aggregate_results')
        def process_item(item: int, **kwargs) -> int:
            return item * 2

        @node(aggregator=True)
        def aggregate_results(results: List[int], **kwargs) -> List[int]:
            return results

        tree.compile(type_checking=True)
        self.assertIsInstance(tree.state_store, StateStore)
        self.assertEqual(tree.state_store.get_property_for_node('start_node', 'expected'), 0)
        self.assertEqual(tree.state_store.get_property_for_node('start_node', 'actual'), 0)

    def test_update_state_store(self):
        tree = ExecutionTree()
        node = node_for_tree(tree)

        @node(start_node=True, next_nodes=('FOR_EACH', 'process_item'))
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        @node(next_nodes='aggregate_results')
        def process_item(item: int, **kwargs) -> int:
            return item * 2

        @node(aggregator=True)
        def aggregate_results(results: List[int], **kwargs) -> List[int]:
            return results

        tree.compile(type_checking=True)
        tree.run([1, 2, 3])
        self.assertEqual(tree.state_store['start_node']['actual'], 3)

    def test_aggregate_results(self):
        tree = ExecutionTree()
        node = node_for_tree(tree)

        @node(start_node=True, next_nodes=('FOR_EACH', 'process_item'))
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        @node(next_nodes='aggregate_results')
        def process_item(item: int, **kwargs) -> int:
            return item * 2

        @node(aggregator=True)
        def aggregate_results(results: int, **kwargs) -> List[int]:
            return results

        tree.compile(type_checking=True)
        tree.run([1, 2, 3])
        self.assertEqual(tree.get_node('aggregate_results').output_data, [2, 4, 6])

    def test_iteration_mismatch(self):
        tree = ExecutionTree()
        state_store = InMemoryStateStore()
        node = node_for_tree(tree, state_store)

        @node(start_node=True, next_nodes=('FOR_EACH', 'process_item'))
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        @node(next_nodes='aggregate_results')
        def process_item(item: int, **kwargs) -> int:
            return item * 2

        @node(aggregator=True)
        def aggregate_results(results: List[int], **kwargs) -> List[int]:
            return results

        tree.compile(type_checking=True)
        tree.state_store['start_node']['expected'] = 5
        with self.assertRaises(ValueError) as cm:
            tree.run([1, 2, 3])
        self.assertIn("Mismatch in iterations for cycle starting with node start_node", str(cm.exception))

    def test_for_each_type_checking(self):
        tree = ExecutionTree()
        node = node_for_tree(tree)

        @node(start_node=True, next_nodes=('FOR_EACH', 'process_item'))
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        @node(next_nodes='aggregate_results')
        def process_item(item: str, **kwargs) -> str:
            return str(item)

        @node(aggregator=True)
        def aggregate_results(results: List[str], **kwargs) -> List[str]:
            return results

        with self.assertRaises(ValueError) as cm:
            tree.compile(type_checking=True)
        self.assertIn("Mismatched input between output", str(cm.exception))


if __name__ == '__main__':
    unittest.main()