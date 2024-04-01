import collections.abc
import logging
import uuid
from typing import Dict, Callable, Any, Optional, NoReturn, Literal, Tuple
from graphviz import Digraph

import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_pydot import graphviz_layout

from pydantic import BaseModel, Field, UUID4, ConfigDict

from BotsOnRails.nodes import BaseNode
from BotsOnRails.stores import StateStore, InMemoryStateStore
from BotsOnRails.types import OT, SpecialTypes
from BotsOnRails.utils import match_types, find_cycles_and_for_each_paths

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExecutionPath(BaseModel):
    """
        A flexible and lightweight tree-based execution orchestrator designed for managing
        complex natural language workflows with embedded human-in-the-loop decision points.

        Enables the creation, management, and execution of execution trees where nodes represent
        individual tasks or decision points, supporting seamless pausing and resuming based on
        human input or algorithmic conditions. Tailored for scenarios requiring iterative human
        feedback or approval within LLM-based processing flows.

        Attributes:
            id (str): A unique identifier for the execution tree instance.
            root_node_id (Optional[str]): The ID of the root node, setting the entry point of the workflows.
            nodes (Dict[str, BaseNode]): A dictionary mapping node names to their instances, forming the workflows structure.
            node_ids (Dict[str, str]): A mapping of node names to their UUIDs, facilitating node reference and management.
            node_names (Dict[str, str]): A reverse mapping of UUIDs to node names, aiding in node identification.
            output (Dict[str, Any]): Captures output data from nodes for access post-execution or during human review points.

        Methods:
            root: Retrieves the root node of the execution tree, if set.
            add_node: Adds a new node to the execution tree, optionally setting it as the root node.
            link_nodes: Establishes execution flow between nodes, supporting both sequential and conditional routing.
            get_node: Fetches a node instance by its name, facilitating dynamic interaction with the execution tree.
            run: Initiates the workflows execution from the root node, processing through the tree based on defined paths.
            run_from_step: Allows restarting or continuing execution from a specific node, useful for iterative review or modification.
            generate_graph: Constructs a graph representation of the execution tree, aiding in visualization and analysis.
            visualize: Displays a graphical representation of the workflows, optionally saving it to disk.
            print_graph_to_command_line: Outputs a text-based representation of the execution tree to the command line for quick inspection.

        This orchestrator stands out for its ability to integrate deep human insights directly into automated workflows,
        providing a unique blend of algorithmic efficiency and human intelligence.
        """

    id: str = Field(default_factory=uuid.uuid4().__str__)
    input: Optional[Any] = Field(default=None)
    root_node_id: Optional[UUID4] = Field(default=None)
    locked_at_step_name: Optional[str] = Field(default=None)
    nodes: Dict[str, BaseNode] = Field(default={})
    node_ids: Dict[str, UUID4] = Field(default={})
    node_names: Dict[UUID4, str] = Field(default={})
    output: Any = Field(default=SpecialTypes.NEVER_RAN)
    compiled: bool = Field(default=False)
    state_store: StateStore = Field(default_factory=InMemoryStateStore, exclude=True)
    allow_cycles: bool = Field(default=True)
    true_cycles: Optional[list[list[str]]] = Field(default=None)
    for_each_cycles: Optional[list[list[str]]] = Field(default=None)
    for_each_start_node_ids: list[str] = Field(default=[])
    for_each_end_node_ids: dict[str, str] = Field(default={})

    class Config:
        arbitrary_types_allowed = True  # Allow arbitrary types

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.debug(f"ExecutionTree state store address: {id(self.state_store)}")

    @property
    def root(self) -> Optional[BaseNode]:
        """
        Retrieves the root node of the execution tree, serving as the starting point for the workflows.

        Returns:
            Optional[BaseNode]: The root node instance if set, otherwise None.

        Raises:
            ValueError: If the root node ID does not correspond to a BaseNode instance.
        """
        if self.root_node_id is not None:
            return self.nodes[self.node_names[self.root_node_id]]
        return None

    @property
    def root_node_name(self) -> Optional[str]:
        if self.root_node_id in self.node_names:
            return self.node_names[self.root_node_id]
        else:
            return None

    def handle_output(self, *args):
        """
        Expects that positional args will be the output of a function, so should be array of length 1
        """
        if self.output not in [SpecialTypes.NEVER_FINISHED, SpecialTypes.NEVER_RAN, SpecialTypes.EXECUTION_HALTED]:
            raise ValueError("Already handled output for tree suggesting you had parallel execution pathways... The "
                             "initial version of NLX requires you take a single execution pathway through"
                             "your DAG.")
        self.output = args[0]
        print(f"Execution Tree final output: {self.output}")

    def add_node(self, name: str, node: BaseNode, root: bool = False) -> 'ExecutionPath':
        """
        Adds a node to the execution tree, optionally setting it as the root node.

        Parameters:
            name (str): The name of the node to register - this allows you to re-use same node instance at different
                        place in DAG.
            node (BaseNode): The node instance to add to the tree.
            root (bool, optional): If True, sets the added node as the root node. Defaults to False.

        Returns:
            ExecutionPath: The execution tree instance, allowing for method chaining.

        Raises:
            ValueError: If a node with the same name already exists in the tree.
        """
        logger.debug(f"Add node `{name}`: {node}")

        if not isinstance(node, BaseNode) and not issubclass(node.__class__, BaseNode):
            raise ValueError(f"Node has wrong type {type(node)}... cannot add")

        if self.root_node_id is not None and root:
            raise ValueError(f"Root node {self.root_node_id} is already registered!")

        if name in self.node_ids:
            raise ValueError("Names need to be unique in the TreeBuilder")

        self.nodes[name] = node
        logger.debug(f"\tResulting nodes dict: {self.nodes}")

        self.node_ids[name] = node.id
        logger.debug(f"\tResulting node id dict: {self.node_ids}")

        self.node_names[node.id] = name
        logger.debug(f"\tResulting node name dict: {self.node_names}")

        if root:
            self.root_node_id = node.id

        node.get_node = lambda x: self.get_node(x)
        node.handle_leaf_output = self.handle_output

        if node.route is not None:
            self.compiled = False  # If Node is added with a route, we have to re-compile edges

        return self

    def _add_static_route(self, source_node_name: str, routing: Dict[OT, str],
                          **kwargs):
        """
        Creates a routing node in the execution tree, capable of directing workflows based on dynamic conditions or
        outputs where `routing` dictionary maps specific output result to the name of the node that should
        handle that output condition. If you want to use a routing function, you should create that node separately and
        then add and link it to requisite nodes.

        Parameters:
            source_node_name (str): The name of the node we're routing from.
            routing (Union[Callable[[OT], str], Dict[OT, str]]): The routing logic or mapping to determine the next node based on output.

        Returns:
            ExecutionPath: The execution tree instance, allowing for method chaining.
        """
        logger.debug(f"_add_static_route() - route from `{source_node_name} / routing: {routing}`")
        source_node = self.nodes[source_node_name]
        source_node.route = routing

    def _add_for_each_route(
            self,
            source_node_name: str,
            routing: tuple[Literal['FOR_EACH'], str]
    ):
        logger.debug(f"_add_for_each_route - from `{source_node_name}` to `{routing[1]}`")

        if routing[0] != "FOR_EACH":
            raise ValueError("While attempting to add a FOR_EACH route, the provided route is not of form "
                             "tuple['FOR_EACH', <target_node_name>]")

        from_node_instance = self.nodes[source_node_name]
        to_node_instance = self.nodes[routing[1]]
        logger.debug(f"\tFrom `{from_node_instance.id}` to `{to_node_instance.id}`")
        from_node_instance.route = routing

    def _add_functional_route(
            self,
            source_node_name: str,
            routing: Callable[[OT], str],
            router_target_annotation: Optional[list[str]] = None
    ):
        logger.debug(f"add_functional_route() - route from `{source_node_name}` / ")
        source_node = self.nodes[source_node_name]
        source_node.route = routing
        source_node.func_router_possible_next_step_names = router_target_annotation

    def _add_direct_route(self, from_node: str, to_node: str):
        """
        Establishes an execution flow link between two nodes, defining the workflows path.

        Parameters:
            from_node (str): The name of the node from which the link originates.
            to_node (str): The name of the node to which the link goes.

        Returns:
            ExecutionPath: The execution tree instance, for method chaining.
        """
        logger.debug(f"add_direct_route - from `{from_node}` to `{to_node}`")
        from_node_instance = self.nodes[from_node]
        to_node_instance = self.nodes[to_node]
        logger.debug(f"\tFrom `{from_node_instance.id}` to `{to_node_instance.id}`")
        from_node_instance.route = to_node

    def compile(self, type_checking: bool = False):
        """
        Dynamically generates router nodes and edges by traversing the nodes list
        and applying appropriate routing logic based on each node's registered route attribute.
        """

        if self.root_node_id is None:
            raise ValueError("You need to register a root node. Use the path_start=True argument on root node "
                             "decorator")

        for node_name, node in self.nodes.items():

            logger.debug(f"Compile {node_name}")

            if not node.route:
                continue  # Skip nodes without routing

            if isinstance(node.route, dict):

                logger.debug(f"Appears we have static routing via a dict: {node.route}")

                # For dict-based routing, create conditional router nodes
                for condition_value, target_node_name in node.route.items():

                    if type_checking:
                        target_node = self.nodes[target_node_name]
                        match_types(
                            node.output_type,
                            target_node.execute_function,
                            unpack_output=node.unpack_output,
                            aggregator=node.aggregator
                        )

                    self._add_static_route(node_name, node.route)

            elif isinstance(node.route, tuple):
                logger.debug(
                    f"Compiling node with route {node.route}, which IS a tuple - output type {node.output_type}")
                if node.route[0] == 'FOR_EACH' and isinstance(node.route[1], str):
                    logger.debug("Meets for_each syntax requirements")
                    if type_checking:
                        logger.debug("Type checking is enabled for the for_each loop components...")
                        target_node = self.nodes[node.route[1]]
                        match_types(
                            node.output_type,
                            target_node.execute_function,
                            unpack_output=node.unpack_output,
                            for_each_loop=True,
                            aggregator=node.aggregator
                        )
                        logger.debug("Type checking passed!")
                    self._add_for_each_route(node_name, node.route)
                else:
                    raise ValueError(f"Unsupported special routing command {node.route[0]}.")

            elif callable(node.route):

                logger.debug(f'Appears we have dynamic routing via a function {node.route}')

                # For function-based routing, create a functional router node
                # Assuming we can extract or have predefined target annotations for dynamic functions
                if node.func_router_possible_next_step_names:

                    if type_checking:
                        for possible_node in node.func_router_possible_next_step_names:
                            target_node = self.nodes[possible_node]
                            match_types(
                                node.output_type,
                                target_node.execute_function,
                                unpack_output=node.unpack_output,
                                aggregator=node.aggregator
                            )

                    self._add_functional_route(node_name, node.route, node.func_router_possible_next_step_names)
                else:
                    raise ValueError(
                        f"Node {node_name} uses a routing function but does not have func_router_possible_next_step_names set.")

            elif isinstance(node.route, str):

                # For direct routing, simply add a direct route
                logger.debug(f'Appears we have direct routing to {node.route}')

                if type_checking:
                    target_node = self.nodes[node.route]
                    match_types(
                        node.output_type,
                        target_node.execute_function,
                        unpack_output=node.unpack_output,
                        aggregator=node.aggregator
                    )

                self._add_direct_route(node_name, node.route)

            else:
                logger.warning(f"Node {node_name} has an unrecognized route type: {type(node.route)}")

        # Check there are NO nested cycles and setup state store for FOR_EACH cycles.
        if self.allow_cycles:

            digraph = self.generate_nx_digraph(ignore_compile_flag=True)

            if self.true_cycles is None or self.for_each_cycles is None:
                cycles, for_each_cycles = find_cycles_and_for_each_paths(
                    digraph,
                    self.root_node_name
                )
                self.true_cycles = cycles
                self.for_each_cycles = for_each_cycles
                self.for_each_end_node_ids = {
                    cycle[0]: cycle[-1] for cycle in self.for_each_cycles
                }
                print(f"compile() - for_each_end_node_ids: {self.for_each_end_node_ids}")

        else:
            if self.has_cycle:
                raise ValueError("allow_cycles is set to False but the tree has cycles...")

        # Prep the state store.
        self._prep_state_store()

        self.compiled = True

    def _prep_state_store(self):
        """
        Sets up state store with state variables needed for loop control
        """
        # Populate state store with iteration counts.
        if self.for_each_cycles is None:
            raise ValueError(f"Tree not properly compiled... for_each_cycles is still None")

        for cycle in self.for_each_cycles:
            self.state_store.set_property_for_node(
                cycle[0],
                'expected',
                0
            )
            self.state_store.set_property_for_node(
                cycle[0],
                'actual',
                0
            )
            self.state_store.set_property_for_node(
                cycle[len(cycle) - 1],
                'actual',
                0
            )
            self.state_store.set_property_for_node(
                cycle[len(cycle) - 1],
                'expected',
                0
            )
            self.state_store.register_cycle(cycle)

    def get_node(self, name: str) -> Optional[BaseNode]:
        """
        Fetches a node instance by its name from the execution tree.

        Parameters:
            name (str): The name of the node to retrieve.

        Returns:
            BaseNode: The node instance corresponding to the provided name.
        """
        return self.nodes.get(name, None)

    def _clear_execution_state(self):

        print(f"Clear Execution State!")
        self.output = SpecialTypes.NEVER_RAN
        self.locked_at_step_name = None

        for n in self.nodes.values():
            n.clear_state()

    def run(
            self,
            *args,
            auto_approve: bool = False,
            runtime_args: Optional[Dict] = None
    ) -> Any:
        """
        Initiates the execution of the workflows from the root node, processing through the tree based on defined paths.

        Parameters:
            :param input_val: The initial input to be passed to the root node for processing.
            :param runtime_args:
            :param auto_approve:

        Returns:
            dict: A dictionary capturing the execution state and outputs of the workflows.

        """
        logger.debug(f"run() - with args {args}")

        if not self.compiled:
            logger.warning(
                f"You must call .compile() after adding the last node before you can use the Execution Tree. "
                f"Calling it for you!")
            self.compile()

        self.input = args

        if not isinstance(runtime_args, dict):
            runtime_args = {}
        runtime_args['input'] = args
        runtime_args['auto_approve'] = auto_approve

        if self.root:
            logger.debug(f"Root node exists... proceed to run with {args}")

            # First let's clear any residual state
            self._clear_execution_state()
            self.state_store.reset()

            # Setup loop tracking vars
            self._prep_state_store()

            self.root.run(
                *args,
                has_approval=auto_approve,
                runtime_args=runtime_args
            )

            for name, node in self.nodes.items():
                if node.waiting_for_approval:
                    if self.locked_at_step_name is not None:
                        raise ValueError(f"Your tree appears to have stopped at multiple execution points - node "
                                         f"{self.locked_at_step_name} and {name}. We don't support that (yet...)")
                    else:
                        self.locked_at_step_name = name
                        self.output = SpecialTypes.EXECUTION_HALTED

            # If we ran the tree but nothing came back, just flip output to NO_RETURN (TODO - change that)
            if self.output == SpecialTypes.NEVER_RAN:
                self.output = SpecialTypes.NEVER_FINISHED

            return self.output
        else:
            raise ValueError("No root node registered!")

    def _rehydrate_output(self, output: Any, node: BaseNode) -> Any:
        """
        If you try to run_from_step and pass in a prev_execution_state that was serialized, you will only be able to get
        primitives, dicts, tuples and list. Objects and other types of variables will not be able to be serialized and
        deserialized without custom tooling. This function is a place you can hook into the execution order and convert
        the output_data from your selected start node back into the type it was supposed to be. For now, we only support
        Pydantic BaseModel and child classes, but this could be extended or even made pluggable to support other things.
        """
        if (issubclass(node.output_type, BaseModel) or node.output_type is BaseModel) and isinstance(output, dict):
            return node.output_type(**output)
        else:
            return output

    def run_from_step(
            self,
            node_name: str,
            input_val: Any = SpecialTypes.NOT_PROVIDED,
            prev_execution_state: Optional[dict] = None,
            has_approval: bool = False,
            override_output: Optional[Any] = SpecialTypes.NO_RETURN,
            runtime_args: Optional[Dict] = None
    ) -> Any:
        """
        If we want to replay execution from after a specific node of the tree, such as instances where we
        have an approval node and want to pass its outputs on subsequent run (or potentially have a non-deterministic
        function), we can use this method to run execution from only specified node (anywhere in the tree)
        forward. At the moment, you have to have a previous execution state to do this which you pass in as
        prev_execution_state, so you have inputs to proceed with from your specified node.

        Parameters:
            node_name (str): The name of the node from which to restart or continue execution.
            prev_execution_state (dict): The previous execution state to use as a context for continuation.
            has_approval (bool, optional): If True, bypasses any user approval steps for the node being executed.
                Defaults to False.
            override_output (Any, optional): If this is not None use this as
            runtime_args (Dict, optional): Args to pass to function at runtime
            input_val (Any, optional): If prev_execution_state is None and we're starting from random spot, we need input

        Returns:
            dict: The updated execution state reflecting changes from the continued execution.
        """

        if input_val is SpecialTypes.NOT_PROVIDED and prev_execution_state is None and override_output is SpecialTypes.NO_RETURN:
            raise ValueError("You need to either provide a previous execution state of the tree, an input_val for "
                             "specified node or an override_output for the specified node.")

        if not self.compiled:
            logger.warning(
                f"You must call .compile() after adding the last node before you can use the Execution Tree. "
                f"Calling it for you!")
            self.compile()

        if runtime_args is None:
            runtime_args = {}

        # If you want to replay the entire tree for some reason, just grab initial inputs from previous run
        logger.debug(f"Tree {self.id} - run_from_step {node_name}")

        # Run tree from specified node. Not, if it's an approval node, you'll need to set skip_approval = True otherwise
        # you will just get stuck waiting for approval again.
        start_node = self.nodes[node_name]
        input_chain = {}

        # Clear any residual state from last run
        self._clear_execution_state()
        self.state_store.reset()

        # Setup state store for tracking vars
        self._prep_state_store()

        if prev_execution_state is not None:
            exec_state = {**prev_execution_state}
            self.input = exec_state['input']

            self.output = SpecialTypes(exec_state['output'])
            prev_execution_state_nodes = exec_state['nodes']
            start_after_node = prev_execution_state_nodes[node_name]
            logger.debug(f"run_from_step() - start after execution state {start_after_node}")

            for node_name, state in prev_execution_state_nodes.items():
                if state['executed']:
                    input_chain[node_name] = state['input_data']

            start_node_input_data = start_after_node['input_data']
            logger.debug(f"running next start node input data: {start_node_input_data}")
            start_node_output_data = start_after_node['output_data']
            logger.debug(f"Target type for output is: {start_node.output_type}")

            # This is a hook for something that could become more modular - if the output type is a pydantic model,
            # convert the now dict outputs to pydantic model. Could do other similar things in
            # self._rehydrate_output(...)
            start_node_output_data = self._rehydrate_output(start_node_output_data, start_node)
            # if issubclass(start_node.output_type, BaseModel) or start_node.output_type is BaseModel:
            #     start_node_output_data = start_node.output_type(**start_node_output_data)

            logger.debug(f"running next with output data {start_node_output_data}")
            logger.debug(f"run_from_step() - output_data: {start_node_output_data}")
            logger.debug(f"run_from_step() - input_data: {start_node_input_data}")

        else:
            print(f"prev_execution_state is None... reset inputs and states ")
            # First let's clear any residual state in the tree and nodes
            self.input = input_val
            start_node_input_data = input_val
            start_node_output_data = SpecialTypes.NEVER_RAN

        # If this is not None, we don't rerun the node, we start AFTER
        # the node and pass through the override_output.
        if override_output is not SpecialTypes.NO_RETURN:

            logger.debug(f"Override output for {start_node.name}: {override_output}")

            # Make sure type is compatible with node signature
            if start_node.output_type == NoReturn:
                raise ValueError("You are overriding the output of a node that has a NoReturn return signature. "
                                 "Can't do that. Future you will love current you. Trust us.")
            elif type(override_output) != start_node.output_type:
                raise ValueError(f"The override output you are providing has type {type(override_output)}, which "
                                 f"appears incompatible with node return type of {start_node.output_type}")

            logger.debug(f"Override_output is not None")
            start_node.run_next(
                start_node_input_data,
                override_output,
                runtime_args={
                    "input_chain": input_chain,
                    "input": self.input,
                    **runtime_args
                }
            )

        # If we have output in state from last time waiting approval
        elif start_node_output_data is not SpecialTypes.NEVER_FINISHED:
            logger.debug(f"Node {start_node.name} produced outputs: {start_node_output_data}, pass these through")
            start_node.run_next(
                start_node_input_data,
                start_node_output_data,
                runtime_args={
                    "input_chain": input_chain,
                    "input": self.input,
                    **(runtime_args if runtime_args is not None else {})
                }
            )

        # TODO - no test case is picking this up
        # Otherwise, the node never completed and we run the node AGAIN but do not pause execution
        else:
            if start_node_input_data == SpecialTypes.NOT_PROVIDED:
                start_node.run(
                    has_approval=has_approval,
                    runtime_args={
                        "input_chain": input_chain,
                        "input": self.input,
                        **(runtime_args if isinstance(runtime_args, dict) else {})
                    }
                )
            else:
                start_node.run(
                    start_node_input_data,
                    has_approval=has_approval,
                    runtime_args={
                        "input_chain": input_chain,
                        "input": self.input,
                        **runtime_args
                    }
                )

        # Figure out where we have a stopped node and get name
        # ATM we do NOT support having multiple breakpoints in parallel branches.
        for name, node in self.nodes.items():
            if node.waiting_for_approval:
                if self.locked_at_step_name is not None:
                    raise ValueError(f"Your tree appears to have stopped at multiple execution points - node "
                                     f"{self.locked_at_step_name} and {name}. We don't support that (yet...)")
                else:
                    self.locked_at_step_name = name

        if self.locked_at_step_name:
            return SpecialTypes.EXECUTION_HALTED

        if self.output == SpecialTypes.NEVER_RAN:
            self.output = SpecialTypes.NEVER_FINISHED

        return self.output

    @property
    def has_cycle(self):
        """
        Is there a cycle on the graph (convert to undirected, as we don't want circular flows, even if they're
        directional)
        :return:
        """
        # undirected_cycles = nx.cycle_basis(self.generate_nx_digraph(ignore_compile_flag=True).to_undirected())
        simple_cycles = list(nx.simple_cycles(self.generate_nx_digraph(ignore_compile_flag=True)))
        return len(simple_cycles) > 0

    def generate_nx_digraph(self, ignore_compile_flag: bool = False) -> nx.DiGraph:
        """
        Constructs a graph representation of the execution tree using networkx, aiding in visualization and analysis.

        Returns:
            nx.DiGraph: A directed graph representation of the execution tree.
        """

        logger.debug(f"generate_graph() - Generate graph for DAG {self.id}")

        if not ignore_compile_flag and not self.compiled:
            # We need to be able to ignore this as we rely on this function in self.compile, but generally we want
            # to only run this if we've compiled the tree (which creates the edges).
            logger.warning(
                f"You must call .compile() after adding the last node before you can visualize the Execution "
                f"Tree. Calling it for you!")
            self.compile()

        G = nx.DiGraph()
        for name, node in self.nodes.items():
            logger.debug(f"generate_graph() - Add node {name}")
            logger.debug(f"\t...to return to link route (type {type(node.route)}): {node.route}")
            G.add_node(name, for_each=node.for_each_start_node, aggregator=node.aggregator)

        for name, node in self.nodes.items():
            if isinstance(node.route, list):
                logger.debug(f"\t\tgenerate_graph() - For node {name} list of next nodes: {node.route}")
                for nxt in node.route:
                    logger.debug(f"\t\tgenerate_graph() - Link {name} to {nxt}")
                    G.add_edge(name, nxt)
            elif isinstance(node.route, dict):
                logger.debug(f"\t\tgenerate_graph() - For node {name} dict of next nodes: {node.route}")
                for nxt in node.route.values():
                    logger.debug(f"\t\tgenerate_graph() - Link {name} to {nxt}")
                    G.add_edge(name, nxt)
            elif isinstance(node.route, str):
                logger.debug(f"\t\tgenerate_graph() - Link {name} to {node.route}")
                G.add_edge(name, node.route)
            elif isinstance(node.route, (Callable, collections.abc.Callable)):
                if isinstance(node.func_router_possible_next_step_names, list):
                    for target_name in node.func_router_possible_next_step_names:
                        G.add_edge(name, target_name)
                else:
                    logger.warning(
                        f"Cannot show outputs of router function for {node.name} as func_router_possible_next_step_names is Null")
            elif isinstance(node.route, (tuple, Tuple)):
                logger.debug(f"Node {node.name} is a special command with a tuple.")
                if node.route[0] == 'FOR_EACH' and isinstance(node.route[1], str):
                    G.add_edge(name, node.route[1], special_command="FOR_EACH")
                else:
                    raise ValueError(f"Unsupported special routing command {node.route[0]}.")

            elif node.route is None:
                logger.debug(f"Node {node.name} is terminal. No next node.")
            else:
                logger.error(f"Node {node.name} unrecognized route type {type(node.route)}")
        return G

    def visualize_via_nx(self, save_to_disk: Optional[str] = None):
        """
        Visualizes the execution tree graphically using networkx and matplotlib, with an option to save the
        visualization to disk.

        Parameters:
            save_to_disk (Optional[str], optional): If provided, the path where the visualization should be saved as an
                         image file. Otherwise, displays the visualization. Defaults to None.
        """

        # TODO - tree.py:604: DeprecationWarning: nx.nx_pydot.graphviz_layout depends on
        #  the pydot package, which has known issues and is not actively maintained. Consider using
        #  nx.nx_agraph.graphviz_layout instead.

        if not self.compiled:
            logger.warning(
                f"You must call .compile() after adding the last node before you can visualize the Execution "
                f"Tree. Calling it for you!")
            self.compile()

        G = self.generate_nx_digraph()

        # Visualize the graph
        pos = graphviz_layout(G, prog="dot")
        my_dpi = 96
        plt.figure(3, figsize=(1024 / my_dpi, 1024 / my_dpi))
        nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=700, edge_color='k')

        if save_to_disk is not None:
            plt.savefig(save_to_disk)
            plt.close()
        else:
            plt.show()

    def generate_mermaid_diagram(self) -> Optional[str]:
        """
        Generates a Mermaid class diagram of executed nodes in a tree-based workflows,
        including their names, input, and output data as class properties.

        Returns:
            str: A string that represents the Mermaid diagram.
        """

        if not self.compiled:
            logger.warning(
                f"You must call .compile() after adding the last node before you can visualize the Execution "
                f"Tree. Calling it for you!")
            self.compile()

        state = self.model_dump()
        executed_nodes = {name: node for name, node in state["nodes"].items() if node["executed"]}

        if len(executed_nodes.items()) == 0:
            return None

        # Mermaid diagram initialization
        diagram = "classDiagram\n"

        relationships = []

        # Generate classes for each node
        for name, node in executed_nodes.items():
            # Define the class with name and properties
            class_name = name.replace("_", "")  # Simplify node name for class name
            input_data = node["input_data"] if node["input_data"] != "" else "None"
            output_data = node["output_data"]
            diagram += f'    class {class_name} {{\n'
            diagram += f'        +String name = "{name}"\n'
            diagram += f'        +InputData input = {input_data}\n'
            diagram += f'        +OutputData output = {output_data}\n'
            if node['waiting_for_approval']:
                diagram += '        ----- !! HALT !! -----'
            diagram += '    }\n'

            selected_route = node['selected_route']
            if selected_route:
                selected_route = selected_route.replace("_", "")
                relationships.append(f'    {name} --|> {selected_route} : routed')

        diagram += "\n".join(relationships)

        return diagram

    def visualize_via_graphviz(self, filename: Optional[str] = None) -> NoReturn | Digraph:
        """
        Generates a Graphviz visualization of this ExecutionTree.

        Parameters:
        - filename (Optional, str) - the filename to save the graphviz file to (default = None). If None, visualize it.

        Returns:
        - A Graphviz Digraph object representing the execution tree.
        """

        if not self.compiled:
            logger.warning(
                f"You must call .compile() after adding the last node before you can visualize the Execution "
                f"Tree. Calling it for you!")
            self.compile()

        dot = Digraph(comment='Execution Tree Visualization')

        # Add nodes
        for node_name, node in self.nodes.items():
            label = f"{node_name}\n({node.description})"
            dot.node(node_name, label, shape='box', style='filled', color='lightgrey')

        # Add edges
        for node_name, node in self.nodes.items():
            if node.route:
                if isinstance(node.route, dict):
                    # Conditional routing based on dict mapping
                    for output_condition, target_node_name in node.route.items():
                        label = f"if {output_condition}"
                        dot.edge(node_name, target_node_name, label=label, color='blue')
                elif callable(node.route):
                    # Functional routing (condition function)
                    # Assuming func_router_possible_next_step_names for target nodes visualization
                    for target_node_name in node.func_router_possible_next_step_names:
                        label = "func condition"
                        dot.edge(node_name, target_node_name, label=label, color='red')
                elif isinstance(node.route, str):
                    # Direct routing
                    dot.edge(node_name, node.route, color='black')
                elif isinstance(node.route, tuple):
                    label = "for_each output item -->"
                    dot.edge(node_name, node.route[1], label=label, color='blue')
                    print(self.for_each_end_node_ids)
                    dot.edge(self.for_each_end_node_ids[node_name], node_name, label, color='blue')
                else:
                    raise ValueError(f"Unsupported route type for node {node_name}")

        # Additional styling and layout options can be specified here
        if filename is not None:
            dot.render(filename, view=False)  # Saves and opens the visualization
        else:
            dot.view()

    def dump_json(self, hide_intermediate_results: bool = True) -> str:
        return self.model_dump_json(
            indent=4,
            exclude={
                'input_data': hide_intermediate_results,
                'output_data': hide_intermediate_results,
                'runtime_args': hide_intermediate_results,
            }
        )
