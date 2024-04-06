import unittest
from typing import List, Tuple

from BotsOnRails.decorators import step_decorator_for_path
from BotsOnRails.stores import StateStore, InMemoryStateStore
from BotsOnRails.rails import ExecutionPath


class TestForEachRouting(unittest.TestCase):
    def test_detect_nested_cycles(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True, next_step=('FOR_EACH', 'process_item'))
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        def router(item: int) -> str:
            if item == 4:
                return "nested_cycle"
            return "aggregate_results"

        @node(next_step=router, func_router_possible_next_step_names=['nested_cycles', 'aggregate_results'])
        def process_item(item: int, **kwargs) -> int:
            return item * 2

        @node(next_step='process_item')
        def nested_cycles(input: int) -> int:
            return input

        @node(aggregator=True)
        def aggregate_results(results: int, **kwargs) -> int:
            return results

        with self.assertRaises(ValueError) as cm:
            tree.compile(type_checking=True)
        self.assertEqual(str(cm.exception), "For_each node process_item is inside a cycle.")

    def test_set_up_state_store(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True, next_step=('FOR_EACH', 'process_item'))
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        @node(next_step='aggregate_results')
        def process_item(item: int, **kwargs) -> int:
            return item * 2

        @node(aggregator=True)
        def aggregate_results(results: int, **kwargs) -> int:
            return results

        tree.compile(type_checking=True)
        self.assertIsInstance(tree.state_store, StateStore)
        self.assertEqual(tree.state_store.get_property_for_node('start_node', 'expected'), 0)
        self.assertEqual(tree.state_store.get_property_for_node('start_node', 'actual'), 0)

    def test_update_state_store(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True, next_step=('FOR_EACH', 'process_item'))
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        @node(next_step='aggregate_results')
        def process_item(item: int, **kwargs) -> int:
            return item * 2

        @node(aggregator=True)
        def aggregate_results(results: int, **kwargs) -> int:
            return results

        tree.compile(type_checking=True)
        tree.run([1, 2, 3])
        self.assertEqual(tree.state_store.dump_store()['aggregate_results']['actual'], 3)

    def test_aggregate_results(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True, next_step=('FOR_EACH', 'process_item'))
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        @node(next_step='aggregate_results')
        def process_item(item: int, **kwargs) -> int:
            return item * 2

        @node(aggregator=True)
        def aggregate_results(results: int, **kwargs) -> int:
            return results

        tree.compile(type_checking=True)
        tree.run([1, 2, 3])
        self.assertEqual(tree.get_node('aggregate_results').output_data, [2, 4, 6])

    def test_provide_external_state_store(self):

        # TODO - not 100% sure why this is failing...

        state_store = InMemoryStateStore()
        tree = ExecutionPath(state_store=state_store)
        node = step_decorator_for_path(tree, state_store)

        @node(path_start=True, next_step=('FOR_EACH', 'process_item'))
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        @node(next_step='aggregate_results')
        def process_item(item: int, **kwargs) -> int:
            return item * 2

        @node(aggregator=True)
        def aggregate_results(results: int, **kwargs) -> int:
            return results

        tree.compile(type_checking=True)
        tree.state_store.set_property_for_node('start_node', 'expected', 5)
        tree.run([1, 2, 3])

    def test_for_each_type_checking(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True, next_step=('FOR_EACH', 'process_item'))
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        @node(next_step='aggregate_results')
        def process_item(item: str, **kwargs) -> str:
            return str(item)

        @node(aggregator=True)
        def aggregate_results(results: str, **kwargs) -> str:
            return results

        with self.assertRaises(ValueError) as cm:
            tree.compile(type_checking=True)
        self.assertIn("Mismatched input between output", str(cm.exception))

    def test_correct_typing_single_value(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True, next_step=('FOR_EACH', 'process_item'))
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        @node(next_step='aggregate_results')
        def process_item(item: int, **kwargs) -> int:
            return item * 2

        # TODO - this syntax looks weird because unpack you'd expect a list output but in fact here the function
        # returns a single int BUT since it's an aggregator, it's actually returning a list which is unpacked by default
        @node(aggregator=True, next_step='handle_results', unpack_output=False)
        def aggregate_results(result: int, **kwargs) -> int:
            return result

        @node()
        def handle_results(results: List[int], **kwargs) -> int:
            return sum(results)

        tree.compile(type_checking=True)
        result = tree.run([1, 2, 3])
        self.assertEqual(result, 12)

    def test_correct_typing_tuple(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True, next_step=('FOR_EACH', 'process_item'), unpack_output=False)
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        @node(next_step='aggregate_results', unpack_output=False)
        def process_item(item: int, **kwargs) -> Tuple[int, str]:
            return item * 2, str(item)

        @node(aggregator=True, next_step='handle_results', unpack_output=False)
        def aggregate_results(result: Tuple[int, str], **kwargs) -> Tuple[int, str]:
            return result

        @node()
        def handle_results(results: List[Tuple[int, str]], **kwargs) -> str:
            return ', '.join(str(x[0]) + ': ' + x[1] for x in results)

        tree.compile(type_checking=True)
        result = tree.run([1, 2, 3])
        self.assertEqual(result, '2: 1, 4: 2, 6: 3')

    def test_incorrect_typing_single_value(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True, next_step=('FOR_EACH', 'process_item'))
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        @node(next_step='aggregate_results')
        def process_item(item: int, **kwargs) -> int:
            return item * 2

        @node(aggregator=True, next_step='handle_results')
        def aggregate_results(result: int, **kwargs) -> int:
            return result

        @node()
        def handle_results(results: int, **kwargs) -> int:
            return results

        with self.assertRaises(ValueError):
            tree.compile(type_checking=True)

    def test_incorrect_typing_tuple(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True, next_step=('FOR_EACH', 'process_item'))
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        @node(next_step='aggregate_results')
        def process_item(item: int, **kwargs) -> Tuple[int, str]:
            return item * 2, str(item)

        @node(aggregator=True, next_step='handle_results')
        def aggregate_results(result: Tuple[int, str], **kwargs) -> Tuple[int, str]:
            return result

        @node()
        def handle_results(results: List[int], **kwargs) -> int:
            return sum(results)

        with self.assertRaises(ValueError):
            tree.compile(type_checking=True)

    def test_incorrect_typing_list(self):
        tree = ExecutionPath()
        node = step_decorator_for_path(tree)

        @node(path_start=True, next_step=('FOR_EACH', 'process_item'))
        def start_node(items: List[int], **kwargs) -> List[int]:
            return items

        @node(next_step='aggregate_results')
        def process_item(item: int, **kwargs) -> List[int]:
            return [item * 2]

        @node(aggregator=True, next_step='handle_results')
        def aggregate_results(result: List[int], **kwargs) -> List[int]:
            return result

        @node()
        def handle_results(results: List[List[int]], **kwargs) -> int:
            return sum(sum(x) for x in results)

        with self.assertRaises(ValueError):
            tree.compile(type_checking=True)


if __name__ == '__main__':
    unittest.main()