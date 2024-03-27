import pytest
import networkx as nx

from nlx.utils import find_cycles_and_for_each_paths


def test_simple_cycle():
    graph = nx.DiGraph()
    graph.add_nodes_from([1, 2, 3])
    graph.add_edges_from([(1, 2), (2, 3), (3, 1)])
    cycles, for_each_paths = find_cycles_and_for_each_paths(graph)
    assert cycles == [(1, 3)]
    assert for_each_paths == []


def test_for_each_path_only():
    graph = nx.DiGraph()
    graph.add_nodes_from([1], for_each=True)
    graph.add_nodes_from([2, 3])
    graph.add_nodes_from([4], aggregator=True)
    graph.add_edges_from([(1, 2), (2, 3), (3, 4)])
    cycle_analysis = find_cycles_and_for_each_paths(graph)
    cycles, for_each_paths = cycle_analysis
    assert cycles == []
    assert for_each_paths[0] == (1, 2, 3, 4)


def test_cycle_with_for_each_node():
    graph = nx.DiGraph()
    graph.add_nodes_from([1], for_each=True)
    graph.add_nodes_from([2,3])
    graph.add_edges_from([(1,2), (2,3), (3,1)])
    cycle_analysis = find_cycles_and_for_each_paths(graph, 1)
    cycles, for_each_paths = cycle_analysis
    print(f"cycles: {cycles}")
    print(f"for_each_paths: {for_each_paths}")
    with pytest.raises(ValueError, match="For_each node 2 is inside a cycle."):
        find_cycles_and_for_each_paths(graph)


def test_for_each_path_with_branch():
    graph = nx.DiGraph()
    graph.add_nodes_from([1, 2, 3], for_each=True)
    graph.add_nodes_from([4, 5], aggregator=True)
    graph.add_edges_from([(1, 2), (2, 3), (3, 4), (3, 5)])
    with pytest.raises(ValueError, match="Encountered a branch at node 3 while traversing from for_each node 1."):
        find_cycles_and_for_each_paths(graph)


def test_for_each_path_without_aggregator():
    graph = nx.DiGraph()
    graph.add_nodes_from([1, 2, 3], for_each=True)
    graph.add_edges_from([(1, 2), (2, 3)])
    with pytest.raises(ValueError, match="No aggregator node found for for_each node 1."):
        find_cycles_and_for_each_paths(graph)


def test_multiple_cycles_and_for_each_paths():
    graph = nx.DiGraph()
    graph.add_cycle([1, 2, 3])
    graph.add_cycle([4, 5, 6])
    graph.add_nodes_from([7, 8, 9], for_each=True)
    graph.add_nodes_from([10], aggregator=True)
    graph.add_edges_from([(7, 8), (8, 9), (9, 10)])
    cycles, for_each_paths = find_cycles_and_for_each_paths(graph)
    assert cycles == [(1, 3), (4, 6)]
    assert for_each_paths == [(7, 10), (8, 10), (9, 10)]


def test_no_cycles_or_for_each_paths():
    graph = nx.DiGraph()
    graph.add_edges_from([(1, 2), (2, 3), (3, 4)])
    cycles, for_each_paths = find_cycles_and_for_each_paths(graph)
    assert cycles == []
    assert for_each_paths == []
