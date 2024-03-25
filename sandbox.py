import networkx as nx
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_graph():
    logger.debug("Entering create_graph function")
    G = nx.DiGraph()
    logger.debug("Created an empty directed graph")

    logger.debug("Adding nodes with custom attributes")
    G.add_node('A', for_each=True, aggregate=False)
    logger.debug("Added node 'A' with for_each=True and aggregate=False")
    G.add_node('B', for_each=False, aggregate=False)
    logger.debug("Added node 'B' with for_each=False and aggregate=False")
    G.add_node('C', for_each=False, aggregate=False)
    logger.debug("Added node 'C' with for_each=False and aggregate=False")
    G.add_node('D', for_each=False, aggregate=True)
    logger.debug("Added node 'D' with for_each=False and aggregate=True")
    G.add_node('E', for_each=True, aggregate=True)
    logger.debug("Added node 'E' with for_each=True and aggregate=False")
    G.add_node('F', for_each=True, aggregate=True)
    logger.debug("Added node 'F' with for_each=False and aggregate=False")
    G.add_node('G', for_each=False, aggregate=True)
    logger.debug("Added node 'G' with for_each=False and aggregate=True")

    logger.debug("Adding edges")
    G.add_edge('A', 'B')
    logger.debug("Added edge from 'A' to 'B'")
    G.add_edge('B', 'C')
    logger.debug("Added edge from 'B' to 'C'")
    G.add_edge('C', 'D')
    logger.debug("Added edge from 'C' to 'D'")
    G.add_edge('D', 'A')
    logger.debug("Added edge from 'D' to 'A'")
    G.add_edge('E', 'F')
    logger.debug("Added edge from 'E' to 'F'")
    G.add_edge('F', 'G')
    logger.debug("Added edge from 'F' to 'G'")
    G.add_edge('G', 'E')
    logger.debug("Added edge from 'G' to 'E'")

    logger.debug("Adding additional nested cycles")
    G.add_edge('E', 'F')
    logger.debug("Added edge from 'E' to 'F' (nested cycle)")
    G.add_edge('F', 'E')
    logger.debug("Added edge from 'F' to 'E' (nested cycle)")
    G.add_edge('F', 'D')
    logger.debug("Added edge from 'F' to 'D' (nested cycle)")
    G.add_edge('D', 'A')
    logger.debug("Added edge from 'D' to 'A' (nested cycle)")
    G.add_edge("A", "B")
    G.add_edge("B", "A")

    logger.debug("Leaving create_graph function")
    return G


def validate_cycles(nx_digraph: nx.DiGraph) -> list[list[str]]:
    """
    Returns list of valid for_each cycles (as lists of node ids) in digraph or throws error.
    Will fail if for_each doesn't end with aggregate or
    """
    logger.debug("Entering detect_cycles function")
    cycles = list(nx.simple_cycles(nx_digraph))
    logger.debug(f"Found {len(cycles)} cycles: {cycles}")
    for_each_cycles = []

    logger.debug("Iterating over cycles")
    for cycle in cycles:
        logger.debug(f"Processing cycle: {cycle}")
        start_node = nx_digraph.nodes[cycle[0]]
        logger.debug(f"Start node: {cycle[0]} with attributes: {start_node}")
        end_node = nx_digraph.nodes[cycle[-1]]
        logger.debug(f"End node: {cycle[-1]} with attributes: {end_node}")

        if start_node['for_each'] and end_node['aggregate']:
            logger.debug(f"Found a valid FOR_EACH cycle: {cycle}")
            for_each_cycles.append(cycle)
        elif start_node['for_each'] and not end_node['aggregate']:
            logger.error(f"For-each cycle starting with node {cycle[0]} does not end with an aggregation node.")
            raise ValueError(f"For-each cycle starting with node {cycle[0]} does not end with an aggregation node.")
        else:
            # We'll want to have other types of cycle validations, probably, for other types of cycles.
            pass

    logger.debug(f"Checking for nested cycles in {cycles}")
    for i in range(len(cycles)):
        for j in range(i + 1, len(cycles)):
            logger.debug(f"Comparing cycle {cycles[i]} with cycle {cycles[j]}")
            if set(cycles[i]).issubset(cycles[j]) or set(cycles[j]).issubset(cycles[i]):
                logger.error("Nested cycles are not allowed.")
                raise ValueError("Nested cycles are not allowed.")

    logger.debug("Leaving detect_cycles function")
    return for_each_cycles


# Create the graph
logger.debug("Creating the graph")
G = create_graph()

# Detect cycles
logger.debug("Detecting cycles")
try:
    for_each_cycles = validate_cycles(G)
    logger.debug("FOR_EACH cycles:")
    for cycle in for_each_cycles:
        logger.debug(cycle)
except ValueError as e:
    logger.error(f"Error: {str(e)}")
