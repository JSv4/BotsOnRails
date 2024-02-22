import logging
import uuid
from typing import Type, Optional, List, Callable, Dict, NoReturn, Any

from pydantic import BaseModel, UUID4, Field, field_validator, field_serializer
from pydantic_core.core_schema import FieldValidationInfo

from nlx.types import IT, OT
from nlx.utils import is_iterable_of_primitives

logger = logging.getLogger(__name__)


class BaseNode(BaseModel):
    """
    Represents a node in a natural language program execution tree.
    """

    id: UUID4 = Field(default_factory=uuid.uuid4)
    name: str
    executed: bool = Field(default=False)
    wait_for_approval: bool = Field(default=False)
    waiting_for_approval: bool = Field(default=False, init=False)
    description: str = Field(default="NLX natural language program node")
    output_type: Type[OT] = Field(default=Type[str])
    output_data: Optional[OT | list[OT]] = Field(default=None)
    runtime_args: Dict[str, Any] = Field(default={}, exclude=True)
    input_data: Optional[IT] = Field(default=None)
    input_type: Dict[str, Type] = Field(default={})
    selected_route: Optional[List[str] | str] = Field(default=None)
    route: Optional[Callable[[OT], str]] | Dict[OT, str] | str = Field(default=None, exclude=True)
    func_router_possible_node_annot: Optional[List[str]] = Field(exclude=True, default=None)
    get_node: Optional[Callable[[str], 'BaseNode']] = Field(exclude=True, default=None)
    execute_function: Optional[Callable] = Field(default=None, exclude=True)
    unpack_output: bool = Field(default=True, description='If decorated function output is iterable like List or '
                                                          'Tuple, do we unpack and pass the positional args '
                                                          'separately or pass iterable output as a single positional '
                                                          'arg')
    handle_output: Optional[Callable[[Any], NoReturn]] = Field(default=None)

    def clear_state(self):
        self.executed = False
        self.input_data = None
        self.output_data = None
        self.waiting_for_approval = False
        self.runtime_args = {}
        self.selected_route = None

    @field_serializer('output_type')
    def serialize_dt(self, ot, _info):
        return str(ot)

    @field_serializer('input_type')
    def serialize_it(self, it, _info):
        return str(it)


    class Config:
        arbitrary_types_allowed = True  # Allow arbitrary types

    @field_validator('output_type')
    @classmethod
    def validate_output_type(cls, v, info: FieldValidationInfo) -> str:
        # Implement custom logic to handle special types if necessary
        # For example, convert typing.NoReturn to a string representation
        print(f"Validating output type val {v} with info {info}")
        if v == NoReturn:
            return 'NoReturn'
        return v

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Optionally, check if a custom handle_output function is provided
        if 'custom_handle_output' in kwargs:
            self.handle_output = kwargs['custom_handle_output']

    def _execute(self, *args, runtime_args: Optional[Dict] = None, **kwargs) -> OT:

        """
        """
        print(f"FunctionNode.{self.name} - _Execute with input: {args}")
        self.runtime_args = runtime_args
        output_data = self.execute_function(*args, runtime_args=runtime_args)
        logger.debug(f"FunctionNode.{self.name} - _execute output: {output_data}")
        return output_data

    def pre_process_input(self, *args):
        logger.debug(f"{self.name} pre_process_input(...) - for node {self.name} with input {args}")
        self.input_data = args
        print(f"{self.name} pre_process_input(...) - stored {self.input_data}")
        return args

    def post_process_output(self, node_output: OT):
        logger.debug(f"{self.name} post_process_output(...) - for node {self.name} with input {node_output}")
        self.executed = True
        self.output_data = node_output
        logger.debug(f"{self.name} post_process_output(...) - stored {self.output_data}")
        return node_output

    def route_output(self, original_output: Any, runtime_args: Optional[Dict]):
        # If we passed in a routing function, run it with output to get target node
        # We DO NOT unpack function outputs for the router.

        if self.get_node is not None:
            if isinstance(self.route, Callable):
                print(f"Node {self.name} has functional routing... proceed")
                self.selected_route = self.route(original_output)
                print(f"Node {self.name} - selected route is {self.selected_route}")
                if self.unpack_output:
                    if is_iterable_of_primitives(original_output):
                        self.get_node(
                            self.selected_route
                        ).run(
                            *original_output,
                            runtime_args=runtime_args
                        )
                    else:
                        self.get_node(
                            self.selected_route
                        ).run(
                            original_output,
                            runtime_args=runtime_args
                        )
                else:
                    self.get_node(
                        self.selected_route
                    ).run(
                        original_output,
                        runtime_args=runtime_args
                    )
            # If we passed in routing dictionary mapping outputs (preferably primitives) to
            # next id, fetch next id
            elif isinstance(self.route, dict):

                print(f"Node {self.name} - has static routing... proceed")
                self.selected_route = self.route.get(original_output, None)
                print(f"Node {self.name} - selected route is {self.selected_route}")

                # We want ability to select none of the provided routes, in which case this is just a conditional link
                if self.selected_route is None:
                    return

                if self.unpack_output:
                    if is_iterable_of_primitives(original_output):
                        self.get_node(
                            self.selected_route
                        ).run(
                            *original_output,
                            runtime_args=runtime_args
                        )
                    else:
                        self.get_node(
                            self.selected_route
                        ).run(
                            original_output,
                            runtime_args=runtime_args
                        )
                else:
                    self.get_node(
                        self.selected_route
                    ).run(
                        original_output,
                        runtime_args=runtime_args
                    )
            # Finally, if it's a single uuid, run it.
            elif isinstance(self.route, str):
                print(f"Node {self.name} - has linked list routing... proceed")
                print(f"\t--> to function `{self.route}` with inputs {original_output}")
                self.selected_route = self.route

                if self.unpack_output:
                    if is_iterable_of_primitives(original_output):
                        print(f"Original output {original_output} is iterable of primitives")
                        self.get_node(
                            self.route
                        ).run(
                            *original_output,
                            runtime_args=runtime_args
                        )
                    else:
                        self.get_node(
                            self.route
                        ).run(
                            original_output,
                            runtime_args=runtime_args
                        )
                else:
                    self.get_node(
                        self.route
                    ).run(
                        original_output,
                        runtime_args=runtime_args
                    )

            elif self.route is None:
                print(f"Execution stopped at node {self.name}")
                if self.handle_output:
                    print(f"Output handler registered!")
                    self.handle_output(original_output)
            else:
                raise ValueError(f"Unexpected value for `route`: {type(self.route)}")
        else:
            logger.warning(
                f"Node {self.name} (type {type(self)}) with id {self.id} has not get_node() function and execution will "
                f"not proceed. This is ok if you don't intend for execution to continue.")

    def run(self, *args, has_approval: bool = False, runtime_args: Optional[Dict] = None, **kwargs):

        print(f"Node {self.name} - run with approval {has_approval} and runtime_args: {runtime_args}")
        print(f"\tReceived input {args}")
        if runtime_args:
            input_chain = runtime_args.get("input_chain", None)
            if isinstance(input_chain, dict):
                runtime_args['input_chain'][self.name] = args
            else:
                runtime_args['input_chain'] = {
                    self.name: args
                }
        else:
            runtime_args = {
                'input_chain': {
                    self.name: args
                }
            }
        self.runtime_args = runtime_args

        processed_input = self.pre_process_input(*args)
        print(f"Processed input: {processed_input}")
        output_data = self._execute(
            *processed_input,
            runtime_args=runtime_args)
        processed_output = self.post_process_output(output_data)

        if self.wait_for_approval and not has_approval:
            logger.debug(f"Node {self.name} is waiting for approval")
            self.waiting_for_approval = True
        else:
            print(f"Node {self.name} is proceeding to router with results {processed_output}")
            self.route_output(processed_output, runtime_args=runtime_args)

    def run_next(self, input_data: IT, output_data: OT, runtime_args: Optional[Dict] = None):
        """
        Take static inputs & outputs for this node and just run the router.

        :param input_data:
        :param output_data:
        :param runtime_args:
        :return:
        """
        print(f"Node {self.name} - run_next with input `{input_data}` and output `{output_data}`")
        self.input_data = input_data
        self.output_data = output_data
        self.executed = True
        self.route_output(*output_data, runtime_args=runtime_args)
